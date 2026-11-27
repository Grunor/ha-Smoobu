"""Lexware Office – optionales Modul (BETA, ab v1.20.0, Wunsch Betreiber 22.11.2026, Roadmap #22).

Aktiv nur mit Schalter `lexware_enabled` UND API-Key (Public API ab Tarif XL) oder Testmodus.

Funktionen
- Rechnungsentwurf per Button in den Buchungsdetails nach dem Regelwerk (lexware_regeln.py), mit Vorschau,
  Kontaktsuche (lexware_kontakt.py) und Bestätigung. Lexware bekommt immer nur einen Entwurf.
- Zahlungsstand je Buchung (lexware_zahlung.py): Abgleich per Webhook (Event-Subscription
  `invoice.status.changed`, `payment.changed`) und stündlichem Abruf offener Rechnungen.
  Der Webhook dient nur als Anstoß: HA liest danach immer selbst bei Lexware nach und vertraut dem
  Inhalt des Aufrufs nicht (die RSA-Signatur von Lexware wird deshalb nicht benötigt).
- Haken „bezahlt“/„Anzahlung“ in Smoobu je nach Einstellung „Bedeutung bezahlt“ (nur Lexware → Smoobu).
- Aufgaben für „Wartet auf dich“ (Kategorie „Rechnungen“) und Pushes (Push-Art „lexware“).

Speicher: Store `smoobu_lexware_<entry_id>` {"rechnungen": {Buchungs-ID: {...}}, "aktiv_seit", "artikel", "webhook"}.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Any, Callable

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from . import lexware_kontakt as kontakt
from . import lexware_regeln as regeln
from . import lexware_zahlung as zahlung
from .const import DOMAIN
from .lexware_client import LexwareClient, LexwareError, MockLexware, deeplink
from .models import is_blocked

_LOGGER = logging.getLogger(__name__)

CONF_LEX_ENABLED = "lexware_enabled"
CONF_LEX_KEY = "lexware_api_key"
CONF_LEX_MOCK = "lexware_mock"
CONF_LEX_RULES = "lexware_rules"                  # {"direkt": [...], "portal": [...]}
CONF_LEX_TAX_COMPANY = "lexware_tax_company"      # net | gross
CONF_LEX_TAX_PRIVATE = "lexware_tax_private"
CONF_LEX_INVOICE_DATE = "lexware_invoice_date"    # erstellung | anreise
CONF_LEX_PAYMENT_TEXT = "lexware_payment_text"    # {"direkt": "...", "portal": "..."}
CONF_LEX_DEPOSIT_PCT = "lexware_deposit_pct"
CONF_LEX_DEPOSIT_DAYS = "lexware_deposit_days"
CONF_LEX_DRAFT_DAYS = "lexware_draft_days"
CONF_LEX_MISSING_DAYS = "lexware_missing_days"    # „Rechnung fehlt“ ab n Tagen vor Anreise
CONF_LEX_SEARCH = "lexware_contact_search"        # name | email | beide
CONF_LEX_COUNTRY = "lexware_default_country"
CONF_LEX_WEBHOOK = "lexware_webhook"
CONF_LEX_SYNC = "lexware_sync_smoobu"             # Haken in Smoobu schreiben (gemäß Bedeutung)
CONF_PAID_MEANING = "paid_meaning"                # {"direkt": ..., "portal": ...} – gilt auch ohne Lexware

DEFAULTS: dict[str, Any] = {
    CONF_LEX_ENABLED: False, CONF_LEX_MOCK: False, CONF_LEX_TAX_COMPANY: "net", CONF_LEX_TAX_PRIVATE: "gross",
    CONF_LEX_INVOICE_DATE: "erstellung", CONF_LEX_DEPOSIT_PCT: 50.0, CONF_LEX_DEPOSIT_DAYS: 7, CONF_LEX_DRAFT_DAYS: 2,
    CONF_LEX_MISSING_DAYS: 14, CONF_LEX_SEARCH: "name", CONF_LEX_COUNTRY: "DE", CONF_LEX_WEBHOOK: True, CONF_LEX_SYNC: True,
}
POLL_EVERY = timedelta(hours=1)
WEBHOOK_EVENTS = ("invoice.status.changed", "payment.changed")
BACK_DAYS = 60   # „Rechnung fehlt“ höchstens so weit zurück (Abreise)
KEEP_DAYS = 400


def opt(o: dict[str, Any], key: str) -> Any:
    return o.get(key, DEFAULTS.get(key))


def paid_meaning(o: dict[str, Any], group: str) -> str:
    on = bool(opt(o, CONF_LEX_ENABLED)) and (bool(o.get(CONF_LEX_KEY)) or bool(opt(o, CONF_LEX_MOCK)))
    return zahlung.effective_meaning((o.get(CONF_PAID_MEANING) or {}).get(group), group, on)


class LexwareModule:
    """Lexware-Anbindung eines Smoobu-Kontos."""

    def __init__(self, hass: HomeAssistant, coordinator: Any) -> None:
        self.hass = hass
        self.c = coordinator
        self.store: Store = Store(hass, 1, f"{DOMAIN}_lexware_{coordinator.config_entry.entry_id}")
        self.data: dict[str, Any] = {"rechnungen": {}, "aktiv_seit": None, "artikel": [], "webhook": {}}
        self.client: Any = None
        self.status: dict[str, Any] = {"verbunden": None, "fehler": None, "stand": None}
        self._unsubs: list[Callable[[], None]] = []
        self._lock = asyncio.Lock()
        self._loaded = False
        self._mock: MockLexware | None = None

    # --- Grundlagen -------------------------------------------------------
    @property
    def opts(self) -> dict[str, Any]:
        return dict(self.c.config_entry.options)

    @property
    def enabled(self) -> bool:
        o = self.opts
        return bool(opt(o, CONF_LEX_ENABLED)) and (bool(o.get(CONF_LEX_KEY)) or bool(opt(o, CONF_LEX_MOCK)))

    @property
    def mock(self) -> bool:
        return bool(opt(self.opts, CONF_LEX_MOCK))

    def _make_client(self) -> Any:
        if self.mock:
            # Testmodus: ein Beispiel-Lexware je Konto, bleibt bis zum Neustart erhalten
            self._mock = self._mock or MockLexware()
            return self._mock
        return LexwareClient(async_get_clientsession(self.hass), str(self.opts.get(CONF_LEX_KEY) or ""))

    async def async_setup(self) -> None:
        stored = await self.store.async_load() or {}
        self.data.update({k: stored.get(k, v) for k, v in self.data.items()})
        self._loaded = True
        if not self.enabled:
            return
        self.client = self._make_client()
        if not self.data.get("aktiv_seit"):
            self.data["aktiv_seit"] = dt_util.now().date().isoformat()
            await self._save()
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, POLL_EVERY))
        self.hass.async_create_task(self._start())

    async def _start(self) -> None:
        await self.refresh_articles()
        await self.async_poll()
        if opt(self.opts, CONF_LEX_WEBHOOK) and not self.mock:
            await self._setup_webhook()

    async def async_unload(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()
        if (wid := (self.data.get("webhook") or {}).get("id")):
            from homeassistant.components import webhook  # noqa: PLC0415

            webhook.async_unregister(self.hass, wid)
        if self._loaded:
            await self._save()

    async def _save(self) -> None:
        await self.store.async_save(self.data)

    async def _tick(self, _now: Any) -> None:
        await self.async_poll()

    def _err(self, err: Exception) -> None:
        self.status.update({"verbunden": False, "fehler": str(err), "stand": dt_util.now().isoformat()})

    async def test_connection(self) -> dict[str, Any]:
        if not self.client:
            return {"ok": False, "fehler": "Lexware ist aus oder es fehlt der API-Key"}
        try:
            p = await self.client.profile()
        except LexwareError as err:
            self._err(err)
            return {"ok": False, "fehler": err.message, "status": err.status}
        self.status.update({"verbunden": True, "fehler": None, "stand": dt_util.now().isoformat()})
        return {"ok": True, "firma": (p or {}).get("companyName"), "testmodus": self.mock}

    async def refresh_articles(self) -> list[dict[str, Any]]:
        if not self.client:
            return self.data.get("artikel") or []
        try:
            arts = await self.client.articles()
        except LexwareError as err:
            self._err(err)
            _LOGGER.warning("Lexware: Artikel konnten nicht geladen werden: %s", err)
            return self.data.get("artikel") or []
        self.data["artikel"] = [a for a in arts if not a.get("archived")]
        self.status.update({"verbunden": True, "fehler": None, "stand": dt_util.now().isoformat()})
        await self._save()
        return self.data["artikel"]

    @property
    def articles(self) -> dict[str, dict[str, Any]]:
        return {a["id"]: a for a in self.data.get("artikel") or [] if a.get("id")}

    def articles_choice(self) -> list[dict[str, Any]]:
        """Auswahl für die Einstellungskarte (Bezeichnung, Einheit, Preis, Steuersatz)."""
        out = []
        for a in self.data.get("artikel") or []:
            i = regeln.article_info(a)
            out.append({"id": i["id"], "name": i["name"], "einheit": i["einheit"], "brutto": i["brutto"], "steuersatz": i["steuersatz"]})
        return sorted(out, key=lambda x: x["name"].casefold())

    # --- Buchungen --------------------------------------------------------
    def _booking(self, booking_id: int) -> dict[str, Any] | None:
        data = self.c.data
        for items in (data.bookings.values() if data else []):
            for b in items:
                if b.get("id") == booking_id:
                    return b
        return None

    async def _booking_raw(self, booking_id: int) -> dict[str, Any]:
        b = self._booking(booking_id)
        if b:
            return b
        try:
            return await self.c.client.get_reservation(booking_id)
        except Exception as err:  # noqa: BLE001 – Smoobu-Fehler als ValueError weiterreichen
            raise ValueError(f"Buchung {booking_id} nicht gefunden: {err}") from err

    def _group(self, booking: dict[str, Any]) -> str:
        return "direkt" if self.c.costs(booking).get("kanal_gruppe") == "Direkt" else "portal"

    def _record(self, booking_id: int) -> dict[str, Any] | None:
        for r in self.c.records_all():
            if r.get("id") == booking_id:
                return r
        return None

    # --- Vorschau und Erstellen ------------------------------------------
    async def preview(self, booking_id: int, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.enabled or not self.client:
            raise ValueError("Lexware ist aus")
        ov = dict(overrides or {})
        b = await self._booking_raw(booking_id)
        if is_blocked(b):
            raise ValueError("Sperrzeiten bekommen keine Rechnung")
        o = self.opts
        if not self.articles:
            await self.refresh_articles()
        ov.setdefault("gruppe", self._group(b))
        company = str(ov.get("firma") or "").strip()
        total = float(b.get("price") or 0)
        deposit = zahlung.soll_anzahlung(total, float(b.get("prepayment") or 0), float(opt(o, CONF_LEX_DEPOSIT_PCT)))
        out = regeln.build(
            b, o.get(CONF_LEX_RULES) or {}, self.articles, today=dt_util.now().date(), portal_channels=[],
            company=bool(company), tax_company=opt(o, CONF_LEX_TAX_COMPANY), tax_private=opt(o, CONF_LEX_TAX_PRIVATE),
            invoice_date=opt(o, CONF_LEX_INVOICE_DATE), payment_text=o.get(CONF_LEX_PAYMENT_TEXT), deposit=deposit,
            overrides=ov, tz_suffix=dt_util.now().strftime("%z")[:3] + ":" + dt_util.now().strftime("%z")[3:],
        )
        g = kontakt.guest(b)
        out["gast"] = {k: g[k] for k in ("vorname", "nachname", "name", "strasse", "plz", "ort", "land")}
        out["anrede"] = ov.get("anrede") or ""
        out["kontakt"] = await self._contact_candidates(g, company)
        if company == "" and ov.get("firma") is not None and str(ov.get("firma")).strip() == "" and ov.get("ist_firma"):
            out["fehler"] = sorted({*out["fehler"], "firmenname_fehlt"})
        if ov.get("ist_firma") and not company:
            out["fehler"] = sorted({*out["fehler"], "firmenname_fehlt"})
        out["vorhanden"] = self.data["rechnungen"].get(str(booking_id))
        out["soll_anzahlung"] = deposit
        out["testmodus"] = self.mock
        out.pop("payload", None)
        return out

    async def _contact_candidates(self, g: dict[str, str], company: str) -> dict[str, Any]:
        mode = opt(self.opts, CONF_LEX_SEARCH)
        name = company or g["name"]
        if len(name) < 3 and mode == "name":
            return {"modus": "neu", "treffer": []}
        try:
            found = await self.client.contacts(name=name if mode in ("name", "beide") and len(name) >= 3 else None,
                                               email=g["email"] if mode in ("email", "beide") and g["email"] else None)
        except LexwareError as err:
            return {"modus": "fehler", "treffer": [], "fehler": err.message}
        hits = kontakt.matches(found, name=name, email=g["email"], mode=mode, company=bool(company))
        return {"modus": "vorhanden" if len(hits) == 1 else ("auswahl" if hits else "neu"),
                "treffer": [kontakt.summary(c) for c in hits[:10]]}

    async def create(self, booking_id: int, overrides: dict[str, Any] | None = None, contact_id: str | None = None) -> dict[str, Any]:
        """Rechnungsentwurf in Lexware anlegen. Fehler als ValueError (Text für die Karte)."""
        async with self._lock:
            key = str(booking_id)
            old = self.data["rechnungen"].get(key)
            if old and old.get("status") != "voided" and not (overrides or {}).get("neu"):
                raise ValueError("Für diese Buchung gibt es schon eine Rechnung")
            ov = dict(overrides or {})
            b = await self._booking_raw(booking_id)
            ov.setdefault("gruppe", self._group(b))
            company = str(ov.get("firma") or "").strip()
            if ov.get("ist_firma") and not company:
                raise ValueError("Firmenname fehlt")
            o = self.opts
            total = float(b.get("price") or 0)
            deposit = zahlung.soll_anzahlung(total, float(b.get("prepayment") or 0), float(opt(o, CONF_LEX_DEPOSIT_PCT)))
            now = dt_util.now()
            out = regeln.build(
                b, o.get(CONF_LEX_RULES) or {}, self.articles, today=now.date(), portal_channels=[], company=bool(company),
                tax_company=opt(o, CONF_LEX_TAX_COMPANY), tax_private=opt(o, CONF_LEX_TAX_PRIVATE),
                invoice_date=opt(o, CONF_LEX_INVOICE_DATE), payment_text=o.get(CONF_LEX_PAYMENT_TEXT), deposit=deposit,
                overrides=ov, tz_suffix=now.strftime("%z")[:3] + ":" + now.strftime("%z")[3:],
            )
            if out["fehler"]:
                raise ValueError("Rechnung nicht möglich: " + ", ".join(out["fehler"]))
            g = kontakt.guest(b)
            salutation = str(ov.get("anrede") or "")
            try:
                cid, note = await self._ensure_contact(g, company, contact_id, salutation)
                payload = {**out["payload"], "address": kontakt.invoice_address(cid, None, g, company=bool(company), salutation=salutation)}
                res = await self.client.create_invoice_draft(payload)
            except LexwareError as err:
                self._err(err)
                raise ValueError(f"Lexware: {err.message}") from err
            iid = res["id"]
            if self.mock:
                self._mock.invoices_data[iid]["_total"] = out["summen"]["brutto"]  # type: ignore[union-attr]
            self.data["rechnungen"][key] = {
                "rechnung_id": iid, "status": "draft", "erstellt": now.date().isoformat(), "summe": out["summen"]["brutto"],
                "faellig": out["faellig"], "gruppe": out["gruppe"], "kontakt_id": cid, "firma": company or None,
                "nummer": None, "gemeldet": [],
            }
            await self._save()
            self.c.async_update_listeners()
            return {"id": iid, "link": deeplink("invoices", iid, "edit"), "hinweis": note, "summe": out["summen"]["brutto"]}

    async def _ensure_contact(self, g: dict[str, str], company: str, contact_id: str | None, salutation: str) -> tuple[str, str | None]:
        """Kontakt-ID für die Rechnung; legt bei Bedarf an bzw. trägt den Gast als Ansprechpartner nach."""
        if not contact_id:
            cand = await self._contact_candidates(g, company)
            if cand["modus"] == "auswahl":
                raise ValueError("Mehrere passende Kontakte – bitte in der Vorschau auswählen")
            if cand["modus"] == "vorhanden":
                contact_id = cand["treffer"][0]["id"]
        if not contact_id:
            res = await self.client.create_contact(kontakt.new_contact(g, company=company, salutation=salutation,
                                                                       default_country=str(opt(self.opts, CONF_LEX_COUNTRY))))
            return res["id"], None
        if company:
            c = await self.client.contact(contact_id)
            upd = kontakt.with_contact_person(c, g, salutation)
            if upd is None and kontakt.multi_entries(c):
                return contact_id, "Ansprechpartner nicht im Kontakt ergänzt (Lexware erlaubt keine Änderung) – steht nur auf der Rechnung"
            if upd is not None:
                try:
                    await self.client.update_contact(contact_id, upd)
                except LexwareError as err:
                    return contact_id, f"Ansprechpartner nicht ergänzt: {err.message} – steht nur auf der Rechnung"
        return contact_id, None

    # --- Zahlungsstand ----------------------------------------------------
    async def async_poll(self, only: str | None = None) -> None:
        """Rechnungsstand und Zahlungen offener Rechnungen nachlesen (ohne bezahlte/stornierte, außer `only`)."""
        if not self.enabled or not self.client:
            return
        changed = False
        today = dt_util.now().date()
        for key, rec in list(self.data["rechnungen"].items()):
            if only and rec.get("rechnung_id") != only and key != only:
                continue
            if not only and rec.get("status") in ("voided",) or (not only and rec.get("bezahlt_seit")
                                                                   and rec["bezahlt_seit"] < (today - timedelta(days=3)).isoformat()):
                continue
            try:
                inv = await self.client.invoice(rec["rechnung_id"])
                pay = await self.client.payments(rec["rechnung_id"]) if inv.get("voucherStatus") != "draft" else None
            except LexwareError as err:
                if err.status == 404:  # in Lexware gelöscht (nur Entwürfe lassen sich löschen)
                    self.data["rechnungen"].pop(key, None)
                    changed = True
                    continue
                self._err(err)
                return
            before = (rec.get("status"), rec.get("offen"))
            rec["status"] = str(inv.get("voucherStatus") or rec.get("status"))
            rec["nummer"] = inv.get("voucherNumber") or rec.get("nummer")
            gross = ((inv.get("totalPrice") or {}).get("totalGrossAmount"))
            if gross is not None:
                rec["summe"] = float(gross)
            if pay is not None:
                rec["offen"] = round(float(pay.get("openAmount") or 0), 2)
                rec["zahlung_status"] = pay.get("voucherStatus")
                rec["zahlungen"] = [{"betrag": p.get("amount"), "datum": str(p.get("postingDate") or "")[:10], "art": p.get("paymentItemType")}
                                    for p in pay.get("paymentItems") or []]
                if pay.get("voucherStatus") in ("paid", "paidoff") and not rec.get("bezahlt_seit"):
                    rec["bezahlt_seit"] = today.isoformat()
            if (rec.get("status"), rec.get("offen")) != before:
                changed = True
                await self._after_change(int(key), rec, before)
        await self.async_check(today)
        self.status.update({"verbunden": True, "fehler": None, "stand": dt_util.now().isoformat()})
        if changed:
            await self._save()
            self.c.async_update_listeners()

    def evaluate(self, booking_id: int, today: date | None = None) -> dict[str, Any]:
        rec = self.data["rechnungen"].get(str(booking_id))
        r = self._record(booking_id) or {}
        group = (rec or {}).get("gruppe") or ("direkt" if r.get("gruppe") == "Direkt" else "portal")
        pay = None
        if rec and rec.get("zahlung_status"):
            pay = {"openAmount": rec.get("offen", rec.get("summe")), "voucherStatus": rec.get("zahlung_status")}
        arrival = date.fromisoformat(r["anreise"]) if r.get("anreise") else None
        o = self.opts
        ev = zahlung.evaluate(rec, pay, group=group, total=float(r.get("brutto") or 0),
                              smoobu_prepayment=float(r.get("anzahlung") or 0), arrival=arrival,
                              today=today or dt_util.now().date(), deposit_pct=float(opt(o, CONF_LEX_DEPOSIT_PCT)),
                              deposit_days=int(opt(o, CONF_LEX_DEPOSIT_DAYS)), draft_days=int(opt(o, CONF_LEX_DRAFT_DAYS)))
        ev["gruppe"] = group
        ev["bedeutung"] = paid_meaning(o, group)
        if rec:
            ev["link"] = deeplink("invoices", rec["rechnung_id"], "edit" if rec.get("status") == "draft" else "view")
            ev["rechnung_id"] = rec["rechnung_id"]
            ev["erstellt"] = rec.get("erstellt")
            ev["firma"] = rec.get("firma")
            ev["zahlungen"] = rec.get("zahlungen") or []
        return ev

    async def _after_change(self, booking_id: int, rec: dict[str, Any], before: tuple[Any, Any]) -> None:
        """Smoobu-Haken nachziehen und Zahlungseingang melden."""
        ev = self.evaluate(booking_id)
        if opt(self.opts, CONF_LEX_SYNC):
            await self._sync_smoobu(booking_id, ev)
        old_open = before[1]
        if rec.get("offen") is not None and old_open is not None and rec["offen"] < old_open - 0.005:
            got = round(old_open - rec["offen"], 2)
            what = "komplett bezahlt" if ev["status"] == "bezahlt" else ("Anzahlung eingegangen" if ev["status"] == "anzahlung" else "Teilzahlung eingegangen")
            await self._push(booking_id, f"💶 {what}: {self._guest(booking_id)}",
                             f"{regeln.euro(got)} eingegangen, offen {regeln.euro(rec['offen'])}.", tag=f"lexware_{booking_id}")

    async def _sync_smoobu(self, booking_id: int, ev: dict[str, Any]) -> None:
        want = zahlung.smoobu_flags(ev["bedeutung"], ev)
        if not want:
            return
        r = self._record(booking_id) or {}
        body = {}
        if "price_paid" in want and bool(r.get("bezahlt")) != want["price_paid"]:
            body["priceStatus"] = 1 if want["price_paid"] else 0
        if "prepayment_paid" in want and bool(r.get("anzahlung_bezahlt")) != want["prepayment_paid"] and float(r.get("anzahlung") or 0) > 0:
            body["prepaymentStatus"] = 1 if want["prepayment_paid"] else 0
        if not body:
            return
        try:
            await self.c.client.update_reservation(booking_id, body)
            self.c.force_revenue_refresh = True
            await self.c.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Lexware → Smoobu: Zahlungsstatus von Buchung %s nicht gesetzt: %s", booking_id, err)

    def _guest(self, booking_id: int) -> str:
        r = self._record(booking_id) or {}
        return str(r.get("gast") or r.get("gastname") or f"Buchung {booking_id}")

    async def _push(self, booking_id: int, title: str, text: str, tag: str) -> None:
        notifier = getattr(self.c, "notifier", None)
        if notifier:
            await notifier.send("lexware", title, text, {"tag": tag, "group": "smoobu_lexware"})

    async def async_check(self, today: date) -> None:
        """Hinweise (Anzahlung fehlt, Rest offen) je Rechnung einmal melden."""
        for key, rec in self.data["rechnungen"].items():
            ev = self.evaluate(int(key), today)
            done = set(rec.get("gemeldet") or [])
            for h in ev["hinweise"]:
                if h in done or h == "entwurf_offen":
                    continue
                if h == "anzahlung_fehlt":
                    await self._push(int(key), f"⚠️ Anzahlung fehlt: {self._guest(int(key))}",
                                     f"Seit {opt(self.opts, CONF_LEX_DEPOSIT_DAYS)} Tagen keine (vollständige) Anzahlung "
                                     f"({regeln.euro(ev['soll_anzahlung'])}) – Storno möglich.", tag=f"lexware_{key}")
                elif h == "rest_offen":
                    await self._push(int(key), f"💶 Restzahlung offen: {self._guest(int(key))}",
                                     f"Heute Anreise, offen {regeln.euro(ev['offen'])}.", tag=f"lexware_{key}")
                done.add(h)
            if done != set(rec.get("gemeldet") or []):
                rec["gemeldet"] = sorted(done)
                await self._save()

    # --- Aufgaben für „Wartet auf dich“ -----------------------------------
    def tasks(self, today: date | None = None, apartment_ids: set[int] | None = None) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        today = today or dt_util.now().date()
        since = date.fromisoformat(self.data.get("aktiv_seit") or today.isoformat())
        ahead = int(opt(self.opts, CONF_LEX_MISSING_DAYS))
        out = []
        for r in self.c.records_all():
            if r.get("storniert") or r.get("blockiert") or not r.get("anreise"):
                continue
            if apartment_ids and r.get("wohnung_id") not in apartment_ids:
                continue
            arr, dep = date.fromisoformat(r["anreise"]), date.fromisoformat(r["abreise"])
            if dep < today - timedelta(days=BACK_DAYS):
                continue
            base = {"buchung_id": r["id"], "gast": r.get("gast"), "anreise": r["anreise"], "kanal": r.get("kanal"),
                    "wohnung_id": r.get("wohnung_id"), "brutto": r.get("brutto")}
            rec = self.data["rechnungen"].get(str(r["id"]))
            if not rec:
                if arr >= since and arr <= today + timedelta(days=ahead):
                    out.append({**base, "art": "rechnung_fehlt"})
                continue
            ev = self.evaluate(r["id"], today)
            for h in ev["hinweise"]:
                out.append({**base, "art": h, "offen": ev["offen"], "soll_anzahlung": ev["soll_anzahlung"],
                            "gezahlt": ev["gezahlt"], "link": ev.get("link")})
        return sorted(out, key=lambda x: x["anreise"])

    # --- Webhook ----------------------------------------------------------
    async def _setup_webhook(self) -> None:
        from homeassistant.components import webhook  # noqa: PLC0415

        hook = self.data.setdefault("webhook", {})
        wid = hook.get("id") or webhook.async_generate_id()
        try:
            webhook.async_register(self.hass, DOMAIN, f"Smoobu Lexware ({self.c.config_entry.title})", wid,
                                   self._handle_webhook, allowed_methods=["POST"])
        except ValueError:
            pass  # schon registriert (Neuladen)
        hook["id"] = wid
        if not hook.get("url"):
            from . import _async_public_url  # noqa: PLC0415

            hook["url"] = await _async_public_url(self.hass, wid)
        if not hook.get("url"):
            _LOGGER.info("Lexware: keine öffentliche HTTPS-URL – nur stündlicher Abruf")
            await self._save()
            return
        try:
            subs = await self.client.subscriptions()
            have = {(s.get("eventType"), s.get("callbackUrl")) for s in subs}
            for ev in WEBHOOK_EVENTS:
                if (ev, hook["url"]) not in have:
                    await self.client.subscribe(ev, hook["url"])
        except LexwareError as err:
            _LOGGER.warning("Lexware-Webhook konnte nicht eingerichtet werden (nur stündlicher Abruf): %s", err)
        await self._save()

    async def _handle_webhook(self, hass: HomeAssistant, webhook_id: str, request: Any) -> Any:
        """Lexware meldet eine Änderung → kurz quittieren, dann selbst nachlesen (Inhalt wird nicht vertraut)."""
        from aiohttp import web  # noqa: PLC0415

        try:
            body = await request.json()
        except ValueError:
            body = {}
        rid = str((body or {}).get("resourceId") or "")
        known = {rec.get("rechnung_id") for rec in self.data["rechnungen"].values()}
        if rid and rid in known:
            hass.async_create_task(self.async_poll(only=rid))
        return web.Response(status=200)

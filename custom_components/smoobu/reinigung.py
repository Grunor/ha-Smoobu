"""Reinigungsboard (ab v1.19.0, Wunsch Betreiber 20.11.2026).

Je Abreise eines Gastes entsteht eine Reinigung. Sie zeigt, was die Reinigungskraft wissen muss:
Abreisetag und Check-out-Zeit, die nächste Anreise (Check-in-Zeit, Personen, Hund) und ob es ein
Gästewechsel am selben Tag ist. Vom Gast nur der Vorname (bzw. gar nichts ohne „belegung_sehen“).

Zuweisung (Entscheidungen Betreiber 20.11.2026):
- Recht „reinigung“: offene Reinigungen sehen, sich selbst eintragen/austragen, eigene (oder noch
  nicht zugewiesene) als erledigt markieren.
- Recht „reinigung_zuweisen“: jede Reinigung einem Benutzer mit Recht „reinigung“ zuweisen,
  Zuweisung entfernen, jeden Status setzen.
- Nicht zugewiesene Reinigungen sind für alle mit Recht „reinigung“ sichtbar (zum Übernehmen).
- Push an die zugewiesene Person: bei Zuweisung/Änderung und am Vorabend (Uhrzeit einstellbar,
  Standard 18:00). Handy je HA-Benutzer in den Einstellungen (Option `cleaning_phones`).
  Die Pushes halten die Ruhezeit ein (werden gesammelt) – wie die übrigen Smoobu-Pushes.

Dauer (v1.19.0, Wunsch Betreiber 20.11.2026): je Reinigung buchbar (Aktion „dauer“, Minuten), ohne
Eintrag gilt die Standard-Reinigungszeit (Option `cost_cleaning_minutes`, Standard 60). Kosten der
Reinigung = Dauer × Stundenlohn der Person (Deckungsbeitrag der Buchung und Statistik).

Schlüssel einer Reinigung: `<buchungs_id>:<abreise>` – verschiebt sich die Abreise, entsteht eine
neue Reinigung (alte Zuweisung passt dann nicht mehr sicher zum Tag). Gespeichert im Store
`smoobu_reinigung_<entry_id>`. Offene Einträge fallen nach 60 Tagen weg, erledigte bleiben dauerhaft
für die Statistik (Wunsch Betreiber 20.11.2026: wer hat wann welche Wohnung gereinigt; v1.19.1b2:
ohne Ablauf statt 3 Jahre, damit nachgetragene Reinigungen ab 2020 erhalten bleiben).
Datenschutz (v1.19.1b3, Speicherbegrenzung Art. 5 DSGVO): Nach `cleaning_keep_years` Jahren
(Standard 10, steuerliche Aufbewahrung) wird die Person anonymisiert – „gereinigt von“ wird
„Unbekannt“, wer abgehakt hat wird entfernt. Tag, Wohnung, Dauer und Kosten bleiben für die Statistik.
Geprüft beim Laden und täglich mit der Vorabend-Erinnerung.

Nachtragen (v1.19.1): vergangene Reinigungen nachträglich erfassen, einzeln (Aktion „nachtragen“) oder
gesammelt (`async_bulk`: alle offenen bis zu einem Datum). Als Person geht auch „Unbekannt“
(`UNKNOWN`) – für Altfälle, bei denen niemand mehr weiß, wer gereinigt hat. Stundenlohn für
„Unbekannt“: Eintrag `unbekannt` in `cleaning_wages`, sonst 0 €/h (Wunsch Betreiber 21.11.2026). Beim
Erledigen wird ein Schnappschuss der Reinigung gespeichert (Tag, Wohnung, Gästewechsel, Hund,
Personen, Nächte, Check-out), damit die Statistik auch nach Änderungen/Stornos stimmt.
Die Statistik beginnt mit dem Update auf v1.19.0 – frühere Reinigungen kennt die Integration nicht.

Reinigung planen (v1.20.0, Wunsch/Entscheidungen Betreiber 27.11.2026):
- Aktion „planen“ (nur Recht „reinigung_zuweisen“): Reinigungstag frei wählbar vom Abreisetag bis höchstens zur
  nächsten Belegung der Wohnung (Gast ODER bestehende Sperre – vermeidet überlappende Sperren). Ohne Folgebelegung
  höchstens DAYS_AHEAD Tage nach der Abreise. Geprüft im Backend (`plan_range`), die Karte zeigt nur die Grenzen.
- Liegt der Tag nach der Abreise, sperrt die Integration die Nächte ab Abreise (frühestens heute) bis zum Vortag
  der Reinigung in Smoobu (Sperr-Kanal, Hinweis „Reinigung geplant (HA)“). Am Reinigungstag ist eine Anreise
  möglich – wie beim Gästewechsel. Die Sperre wird im Store gemerkt (`sperre_id`), nur diese eigenen Sperren
  ändert/löscht die Integration.
- Verschieben = alte Sperre löschen, neue anlegen (Smoobu ändert Daten einer Sperre nicht zuverlässig per API).
  Zurück auf den Abreisetag = Sperre freigeben.
- Früher erledigt: die restliche Sperre wird ab dem Folgetag freigegeben (Entscheidung Betreiber).
- Aufräumen (`async_reconcile`, nach jeder Aktualisierung): Buchung storniert oder Abreise verschoben (Reinigung
  existiert nicht mehr) → eigene Sperre löschen; Sperre in Smoobu von Hand gelöscht → Planung zurück auf Abreise.
- Die eigene Sperre zählt bei der Reinigung nicht als „nächste Belegung“ (sonst wäre sie ihre eigene Grenze).
- Board, Vorabend-Erinnerung und Push richten sich nach dem geplanten Tag (`tag`); `datum` bleibt der Abreisetag
  (Schlüssel, Statistik).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from . import rechte
from .analytics import block_channel_id
from .api import SmoobuError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_CLEANING_PHONES = "cleaning_phones"        # {HA-Benutzer-ID: "notify.mobile_app_…"}
CONF_CLEANING_NOTIFY = "cleaning_notify"        # Pushes an/aus (Standard an)
CONF_CLEANING_REMIND_TIME = "cleaning_remind_time"  # Vorabend-Erinnerung, HH:MM
DEFAULT_CLEANING_REMIND_TIME = "18:00"
DAYS_BACK = 7      # erledigte/vergessene der letzten Woche bleiben sichtbar
DAYS_AHEAD = 60
KEEP_DAYS = 60          # offene/zugewiesene Einträge
WIDE_BACK = 40 * 366    # „ohne Zeitfenster“ zurück (Nachtragen, Buchungsdetails) – Historie reicht bis 2020
UNKNOWN = "unbekannt"   # v1.19.1b2: Pseudo-Person „Unbekannt“ (nur Nachtragen, nie zuweisbar)
UNKNOWN_NAME = "Unbekannt"
CONF_CLEANING_KEEP_YEARS = "cleaning_keep_years"  # v1.19.1b3: Person nach N Jahren anonymisieren
DEFAULT_CLEANING_KEEP_YEARS = 10
CONF_CLEANING_MINUTES_BY_USER = "cleaning_minutes_by_user"  # v1.19.1b4: {HA-Benutzer-ID: Standard-Minuten}
_PERSON_KEYS = ("erledigt_von", "erledigt_von_id")
ACTIONS = ("uebernehmen", "abgeben", "zuweisen", "erledigt", "offen", "dauer", "nachtragen", "planen")
BLOCK_NOTICE = "Reinigung geplant (HA)"   # v1.20.0: Hinweis an der automatischen Sperre in Smoobu
BLOCK_GRACE = timedelta(minutes=15)       # frisch angelegte Sperre fehlt evtl. noch in den Daten → nicht als gelöscht werten
_BLOCK_KEYS = ("sperre_id", "sperre_von", "sperre_bis", "sperre_seit")
# v1.19.1: Diese Aktionen gehen (nur mit „Reinigung zuweisen“) auch für Abreisen außerhalb des Board-Fensters
# (älter als DAYS_BACK) – zum Nachtragen vergangener Reinigungen und zum Korrigieren nachgetragener.
PAST_ACTIONS = ("nachtragen", "offen", "dauer")
MAX_MINUTES = 600


class CleaningError(Exception):
    """Aktion nicht erlaubt oder ungültig (Code für die Karte in `code`)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _time(value: Any, fallback: str) -> str:
    return str(value or fallback or "")[:5]


def build(records: list[dict[str, Any]], opts: dict[str, Any], today: date,
          days_back: int = DAYS_BACK, days_ahead: int = DAYS_AHEAD, ignore: set[Any] | None = None) -> list[dict[str, Any]]:
    """Reinigungen aus den Buchungsdatensätzen (ohne Zuweisung/Status), nach Tag sortiert.

    v1.20.0: `ignore` = IDs der eigenen Reinigungs-Sperren – sie zählen nicht als nächste Belegung."""
    ignore = ignore or set()
    start, end = (today - timedelta(days=days_back)).isoformat(), (today + timedelta(days=days_ahead)).isoformat()
    guests = sorted((r for r in records if not r.get("blockiert") and not r.get("storniert")),
                    key=lambda r: (r["anreise"], r["id"]))
    occupied = sorted((r for r in records if not r.get("storniert") and r["id"] not in ignore),
                      key=lambda r: (r["anreise"], r["id"]))
    out = []
    for r in guests:
        if not (start <= r["abreise"] <= end):
            continue
        # Nächste Belegung derselben Wohnung (Gast oder Sperre) ab dem Abreisetag
        nxt = next((n for n in occupied if n["wohnung_id"] == r["wohnung_id"] and n["id"] != r["id"]
                    and n["anreise"] >= r["abreise"]), None)
        out.append({
            "key": f"{r['id']}:{r['abreise']}",
            "buchung_id": r["id"],
            "wohnung_id": r["wohnung_id"],
            "datum": r["abreise"],
            "check_out": _time(r.get("check_out"), opts.get("default_checkout", "11:00")),
            "vorname": r.get("vorname"),
            "gast": r.get("gast"),  # voller Name – nur für Benutzer mit Recht „gaeste“ (siehe items)
            "personen": r.get("personen"),
            "hund": bool(r.get("hund")),
            "naechte": r.get("naechte"),
            # Gästewechsel am selben Tag = enges Zeitfenster zwischen Check-out und Check-in
            "wechsel": bool(nxt and not nxt.get("blockiert") and nxt["anreise"] == r["abreise"]),
            "naechste": None if nxt is None else {
                "datum": nxt["anreise"],
                "sperre": bool(nxt.get("blockiert")),
                "check_in": None if nxt.get("blockiert") else _time(nxt.get("check_in"), opts.get("default_checkin", "16:00")),
                "vorname": None if nxt.get("blockiert") else nxt.get("vorname"),
                "gast": None if nxt.get("blockiert") else nxt.get("gast"),
                "personen": None if nxt.get("blockiert") else nxt.get("personen"),
                "hund": bool(nxt.get("hund")),
                "naechte": nxt.get("naechte"),
            },
        })
    out.sort(key=lambda x: (x["datum"], x["check_out"] or "", x["key"]))
    return out


def plan_range(item: dict[str, Any], today: date) -> tuple[str, str]:
    """v1.20.0: erlaubter Reinigungstag (frühestens, spätestens) – ab Abreise (in der Vergangenheit: ab heute),
    höchstens bis zur nächsten Belegung (Gast oder Sperre), ohne Folgebelegung DAYS_AHEAD Tage nach der Abreise."""
    dep = date.fromisoformat(item["datum"])
    nxt = item.get("naechste")
    latest = nxt["datum"] if nxt else (dep + timedelta(days=DAYS_AHEAD)).isoformat()
    return max(dep, today).isoformat(), latest


def block_range(item: dict[str, Any], planned: str | None, today: date) -> tuple[str, str] | None:
    """v1.20.0: zu sperrender Zeitraum (Anreise, Abreise im Smoobu-Sinn) – Nächte ab Abreise (frühestens heute)
    bis zum Vortag der Reinigung; None = keine Sperre nötig."""
    if not planned:
        return None
    start = max(item["datum"], today.isoformat())
    return (start, planned) if planned > start else None


class CleaningBoard:
    """Zuweisungen und Status der Reinigungen eines Kontos (hängt am Coordinator)."""

    def __init__(self, hass: HomeAssistant, coordinator: Any) -> None:
        self.hass = hass
        self.c = coordinator
        self.store: Store = Store(hass, 1, f"{DOMAIN}_reinigung_{coordinator.config_entry.entry_id}")
        self.state: dict[str, dict[str, Any]] | None = None
        self._unsubs: list[Callable[[], None]] = []
        self._lock = asyncio.Lock()  # v1.20.0: Sperren nie parallel anlegen/löschen

    @property
    def opts(self) -> dict[str, Any]:
        return dict(self.c.config_entry.options)

    # --- Lebenszyklus ----------------------------------------------------
    async def async_setup(self) -> None:
        await self._load()
        hh, mm = (_time(self.opts.get(CONF_CLEANING_REMIND_TIME), DEFAULT_CLEANING_REMIND_TIME).split(":") + ["0"])[:2]
        try:
            self._unsubs.append(async_track_time_change(self.hass, self._remind, hour=int(hh), minute=int(mm), second=0))
        except ValueError:
            pass
        # v1.20.0: nach jeder Aktualisierung eigene Reinigungs-Sperren prüfen (Storno, verschobene Abreise)
        self._unsubs.append(self.c.async_add_listener(self._on_update))

    def _on_update(self) -> None:
        if self.state and any(v.get("sperre_id") for v in self.state.values()) and not self._lock.locked():
            self.hass.async_create_task(self.async_reconcile(), "smoobu_reinigung_sperren")

    def own_blocks(self) -> set[Any]:
        """IDs der eigenen Reinigungs-Sperren (v1.20.0)."""
        return {v["sperre_id"] for v in (self.state or {}).values() if v.get("sperre_id")}

    def _build(self, today: date, **kw: Any) -> list[dict[str, Any]]:
        """build() mit eigenen Sperren als „ignorieren“; Fenster zurück so weit, dass noch geplante (nicht erledigte)
        Reinigungen mit älterer Abreise sichtbar bleiben."""
        back = kw.pop("days_back", DAYS_BACK)
        for key, v in (self.state or {}).items():
            if v.get("geplant") and v.get("status") != "erledigt" and v["geplant"] >= (today - timedelta(days=DAYS_BACK)).isoformat():
                try:
                    back = max(back, (today - date.fromisoformat(key.split(":")[-1])).days)
                except ValueError:
                    pass
        return build(self.c.records_all(), self.opts, today, days_back=back, ignore=self.own_blocks(), **kw)

    async def async_unload(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()
        if self.state is not None:
            await self.store.async_save(self.state)

    async def _load(self) -> dict[str, dict[str, Any]]:
        if self.state is None:
            self.state = dict(await self.store.async_load() or {})
            today = dt_util.now().date()
            cutoff = (today - timedelta(days=KEEP_DAYS)).isoformat()
            for key, v in list(self.state.items()):
                # v1.19.1b2: erledigte bleiben dauerhaft (Statistik); nur offene/zugewiesene laufen ab
                if v.get("status") != "erledigt" and key.split(":")[-1] < cutoff:
                    self.state.pop(key, None)
            if self._anonymize(self.state):
                await self.store.async_save(self.state)
        return self.state

    def _anonymize(self, state: dict[str, dict[str, Any]]) -> int:
        """v1.19.1b3: erledigte Reinigungen älter als die Aufbewahrungsfrist → Person „Unbekannt“.

        Ändert `state` direkt, liefert die Anzahl geänderter Einträge (Speichern macht der Aufrufer)."""
        years = int(self.opts.get(CONF_CLEANING_KEEP_YEARS, DEFAULT_CLEANING_KEEP_YEARS) or DEFAULT_CLEANING_KEEP_YEARS)
        today = dt_util.now().date()
        try:
            limit = today.replace(year=today.year - years).isoformat()
        except ValueError:  # 29.02.
            limit = (today - timedelta(days=1)).replace(year=today.year - years).isoformat()
        n = 0
        for key, v in state.items():
            if v.get("status") != "erledigt" or key.split(":")[-1] >= limit:
                continue
            if v.get("gereinigt_von") == UNKNOWN and v.get("zugewiesen") is None and not any(v.get(k) for k in _PERSON_KEYS):
                continue
            v.update({"gereinigt_von": UNKNOWN, "gereinigt_name": UNKNOWN_NAME, "zugewiesen": None,
                      "erledigt_von": None, "erledigt_von_id": None, "anonymisiert": True})
            n += 1
        return n

    # --- Lesen -----------------------------------------------------------
    async def items(self, apartments: list[Any] | None, user: Any, booking_id: int | None = None) -> list[dict[str, Any]]:
        """Reinigungen mit Zuweisung/Status, gefiltert nach Wohnungen und den Rechten des Benutzers.

        v1.19.1: mit `booking_id` nur die Reinigung nach dieser Buchung – ohne Zeitfenster, damit die
        Buchungsdetails auch vergangene Aufenthalte zeigen (Reinigung nachtragen)."""
        state = await self._load()
        opts = self.opts
        rights = rechte.rights_of(user, opts)
        names = await self._user_names()
        by_user = minutes_by_user(opts)
        out = []
        today = dt_util.now().date()
        window = {"days_back": WIDE_BACK, "days_ahead": 2 * 366} if booking_id is not None else {}
        for item in self._build(today, **window):
            if apartments is not None and item["wohnung_id"] not in apartments:
                continue
            if booking_id is not None and item["buchung_id"] != booking_id:
                continue
            s = state.get(item["key"], {})
            frm, latest = plan_range(item, today)
            item = {**item, "zugewiesen": s.get("zugewiesen"),
                    # v1.20.0: geplanter Reinigungstag (None = Abreisetag), Grenzen fürs Verschieben, eigene Sperre
                    "geplant": s.get("geplant"), "tag": s.get("geplant") or item["datum"],
                    "planbar_von": frm, "planbar_bis": latest, "gesperrt_bis": s.get("sperre_bis") if s.get("sperre_id") else None, "zugewiesen_name": names.get(s.get("zugewiesen")),
                    "minuten": s.get("minuten"),
                    # v1.19.1b4: Standardzeit der zugewiesenen/reinigenden Person (None = allgemeiner Standard)
                    "standard_minuten_person": by_user.get(s.get("gereinigt_von") or s.get("zugewiesen") or ""),
                    "status": s.get("status", "offen"), "erledigt_von": s.get("erledigt_von"), "erledigt_um": s.get("erledigt_um"),
                    # v1.19.1: nachgetragen (Zeitpunkt des Nachtragens) + wer gereinigt hat
                    "nachgetragen": s.get("nachgetragen"), "gereinigt_name": names.get(s.get("gereinigt_von")) or s.get("gereinigt_name")}
            # Korrektur 21.11.2026 (Wunsch Betreiber): voller Gastname für alle mit „Gästedaten sehen“
            # (alle Rollen außer „Reinigung“), sonst nur der Vorname; ohne „Kalender sehen“ gar kein Name.
            full = "gaeste" in rights
            item["name_voll"] = full
            if item["naechste"]:
                item["naechste"] = dict(item["naechste"])
            for part in (item, item["naechste"]):
                if not part:
                    continue
                full_name = part.pop("gast", None)
                name = (full_name or part.get("vorname")) if full else part.get("vorname")
                part["vorname"] = name if "belegung_sehen" in rights else None
            out.append(item)
        out.sort(key=lambda x: (x["tag"], x["check_out"] or "", x["key"]))
        return out

    async def async_stats(self, apartments: list[Any] | None, start: str, end: str, codes: dict[Any, str]) -> dict[str, Any]:
        state = await self._load()
        pending = []
        today = dt_util.now().date()
        for item in self._build(today, days_back=400, days_ahead=0):
            s = state.get(item["key"], {})
            pending.append({**item, "zugewiesen": s.get("zugewiesen"), "status": s.get("status", "offen")})
        o = self.opts
        wages = {str(k): float(v) for k, v in (o.get("cleaning_wages") or {}).items() if v not in (None, "")}  # 0 €/h erlaubt (z. B. Inhaber)
        default = float(o.get("cost_cleaning", 17.0))
        return stats(state, pending, start, end, set(apartments) if apartments is not None else None,
                     await self._user_names(), codes, today.isoformat(),
                     wage=lambda uid: wage_of(wages, uid, default), minutes=float(o.get("cost_cleaning_minutes", 60)),
                     minutes_for=lambda uid, std=minutes_by_user(o): std.get(uid or ""))

    async def _user_names(self) -> dict[str, str]:
        return {u.id: (u.name or u.id) for u in await self.hass.auth.async_get_users() if not u.system_generated}

    async def cleaners(self) -> list[dict[str, Any]]:
        """HA-Benutzer, denen Reinigungen zugewiesen werden können (Recht „reinigung“, inkl. Admins)."""
        opts = self.opts
        return [{"id": u.id, "name": u.name or u.id, "admin": u.is_admin,
                 "handy": (opts.get(CONF_CLEANING_PHONES) or {}).get(u.id)}
                for u in await self.hass.auth.async_get_users()
                if u.is_active and not u.system_generated and rechte.allowed(u, opts, "reinigung")]

    # --- Ändern ----------------------------------------------------------
    async def async_set(self, key: str, action: str, user: Any, target: str | None = None,
                        minutes: int | None = None, day: str | None = None) -> dict[str, Any]:
        """Aktion ausführen (Rechte siehe Modul-Doku). Rückgabe: neuer Zustand der Reinigung."""
        if action not in ACTIONS:
            raise CleaningError("invalid_action")
        opts = self.opts
        rights = rechte.rights_of(user, opts)
        can_assign = "reinigung_zuweisen" in rights
        if "reinigung" not in rights and not can_assign:
            raise CleaningError("unauthorized")
        today = dt_util.now().date()
        await self._load()
        item = next((x for x in self._build(today) if x["key"] == key), None)
        if item is None and can_assign and action in PAST_ACTIONS:
            # v1.19.1: ältere Abreise (außerhalb des Board-Fensters) – nur Zuweisende, nur Nachtragen/Korrigieren
            item = next((x for x in self._build(today, days_back=WIDE_BACK, days_ahead=0)
                         if x["key"] == key), None)
        if item is None:
            raise CleaningError("not_found")
        state = await self._load()
        cur = dict(state.get(key, {}))
        me = getattr(user, "id", None)
        before = cur.get("zugewiesen")
        moved = False
        if action == "planen":
            # v1.20.0: Reinigungstag planen/verschieben – nur „Reinigung zuweisen“ (Entscheidung Betreiber 27.11.2026)
            if not can_assign:
                raise CleaningError("unauthorized")
            if cur.get("status") == "erledigt":
                raise CleaningError("already_done")
            frm, latest = plan_range(item, today)
            target_day = day or item["datum"]
            try:
                date.fromisoformat(target_day)
            except (TypeError, ValueError) as err:
                raise CleaningError("invalid_date") from err
            if target_day != item["datum"] and not frm <= target_day <= latest:
                raise CleaningError("out_of_range")
            new = None if target_day == item["datum"] else target_day
            moved = new != cur.get("geplant")
            await self._block_or_save(state, key, cur, item, block_range(item, new, today))
            if new:
                cur["geplant"] = new
            else:
                cur.pop("geplant", None)
        elif action == "uebernehmen":
            if "reinigung" not in rights:
                raise CleaningError("unauthorized")
            if before and before != me and not can_assign:
                raise CleaningError("already_assigned")
            cur["zugewiesen"] = me
        elif action == "abgeben":
            if before != me and not can_assign:
                raise CleaningError("not_yours")
            cur["zugewiesen"] = None
        elif action == "zuweisen":
            if not can_assign:
                raise CleaningError("unauthorized")
            if target:
                tu = await self.hass.auth.async_get_user(target)
                if tu is None or not tu.is_active or not rechte.allowed(tu, opts, "reinigung"):
                    raise CleaningError("invalid_user")
            cur["zugewiesen"] = target or None
        elif action == "nachtragen":
            # v1.19.1: vergangene Reinigung in einem Schritt erfassen – „gereinigt von <Person>“ + erledigt.
            # Bewusst ohne Push (die Person hat längst gereinigt) und ohne Abhak-Zeitpunkt: erledigt_um bleibt
            # leer, damit die Auswertung „Ø Minuten bis zum Abhaken“ nicht verfälscht wird.
            if not can_assign:
                raise CleaningError("unauthorized")
            if (cur.get("geplant") or item["datum"]) > today.isoformat():  # v1.20.0: geplanter Tag zählt
                raise CleaningError("not_past")
            if target == UNKNOWN:
                who_name = UNKNOWN_NAME
            else:
                tu = await self.hass.auth.async_get_user(target) if target else None
                if tu is None or not rechte.allowed(tu, opts, "reinigung"):
                    raise CleaningError("invalid_user")
                who_name = tu.name or target
            if minutes is not None:
                if not 1 <= int(minutes) <= MAX_MINUTES:
                    raise CleaningError("invalid_minutes")
                cur["minuten"] = int(minutes)
            cur.update({
                "zugewiesen": None if target == UNKNOWN else target, "status": "erledigt", "erledigt_von": getattr(user, "name", None),
                "erledigt_von_id": me, "erledigt_um": None, "gereinigt_von": target,
                "gereinigt_name": who_name, "nachgetragen": dt_util.now().isoformat(timespec="minutes"),
                "snapshot": {k: item[k] for k in ("datum", "wohnung_id", "check_out", "wechsel", "hund", "personen", "naechte")},
            })
        elif action == "dauer":  # tatsächliche Reinigungszeit buchen (leer = Standard)
            if not can_assign and before not in (None, me):
                raise CleaningError("not_yours")
            if minutes is None:
                cur.pop("minuten", None)
            elif not 1 <= int(minutes) <= MAX_MINUTES:
                raise CleaningError("invalid_minutes")
            else:
                cur["minuten"] = int(minutes)
        else:  # erledigt / offen
            if not can_assign and before not in (None, me):
                raise CleaningError("not_yours")
            cur["status"] = action
            if action == "erledigt":
                cur["erledigt_von"] = getattr(user, "name", None)
                cur["erledigt_von_id"] = me
                cur["erledigt_um"] = dt_util.now().isoformat(timespec="minutes")
                # Wer hat gereinigt: die zugewiesene Person, sonst wer abhakt (Name zusätzlich gemerkt,
                # falls der HA-Benutzer später gelöscht wird)
                who = cur.get("zugewiesen") or me
                cur["gereinigt_von"] = who
                cur["gereinigt_name"] = (await self._user_names()).get(who) if who else None
                cur["snapshot"] = {k: item[k] for k in ("datum", "wohnung_id", "check_out", "wechsel", "hund", "personen", "naechte")}
                if cur.get("geplant"):
                    cur["snapshot"]["geplant"] = cur["geplant"]
                # v1.20.0: früher erledigt → restliche Sperre ab dem Folgetag freigeben (Entscheidung Betreiber)
                tomorrow = (today + timedelta(days=1)).isoformat()
                if cur.get("sperre_id") and cur.get("sperre_bis", "") > tomorrow:
                    want = (cur["sperre_von"], tomorrow) if cur["sperre_von"] < tomorrow else None
                    await self._block_or_save(state, key, cur, item, want)
            else:
                for k in ("erledigt_von", "erledigt_von_id", "erledigt_um", "gereinigt_von", "gereinigt_name", "snapshot",
                          "nachgetragen"):
                    cur.pop(k, None)
        cur["geaendert"] = dt_util.now().isoformat(timespec="seconds")
        state[key] = cur
        await self.store.async_save(state)
        after = cur.get("zugewiesen")
        if after != before and action != "nachtragen":  # v1.19.1: Nachtragen ohne Push
            if after and after != me:  # sich selbst eintragen braucht keinen Push
                await self._push(after, item, "zugewiesen")
            if before and before != me:
                await self._push(before, item, "entfernt")
        elif moved and after and after != me:  # v1.20.0: Termin verschoben → Push an die zugewiesene Person
            await self._push(after, {**item, "tag": cur.get("geplant") or item["datum"]}, "verschoben")
        self.c.async_update_listeners()  # Karten laden neu (Datenabo)
        return cur

    # --- Sperren (v1.20.0) -------------------------------------------------
    async def _block_or_save(self, state: dict[str, Any], key: str, cur: dict[str, Any], item: dict[str, Any],
                             want: tuple[str, str] | None) -> None:
        """Sperre anpassen; schlägt das fehl, den tatsächlichen Sperr-Stand trotzdem speichern und Fehler weitergeben."""
        async with self._lock:
            try:
                await self._apply_block(cur, item, want)
            except CleaningError:
                old = dict(state.get(key, {}))
                for k in _BLOCK_KEYS:
                    old.pop(k, None)
                    if k in cur:
                        old[k] = cur[k]
                # Ohne Sperre gilt keine spätere Planung (sonst wäre die Wohnung ungeschützt buchbar)
                if not old.get("sperre_id") and block_range(item, old.get("geplant"), dt_util.now().date()):
                    old.pop("geplant", None)
                state[key] = old
                await self.store.async_save(state)
                raise

    async def _apply_block(self, cur: dict[str, Any], item: dict[str, Any], want: tuple[str, str] | None) -> None:
        """Eigene Sperre in Smoobu auf `want` bringen (None = keine). Ändert `cur` (Speichern macht der Aufrufer).

        Reihenfolge: alte löschen, neue anlegen (überlappende Sperren lehnt Smoobu ab). Scheitert das Anlegen,
        wird die alte Sperre wiederhergestellt und `block_failed` gemeldet – die Planung bleibt dann unverändert."""
        have = (cur["sperre_von"], cur["sperre_bis"]) if cur.get("sperre_id") else None
        if have == want:
            return
        client = self.c.client
        if have:
            try:
                await client.delete_reservation(cur["sperre_id"])
            except SmoobuError as err:
                if "404" not in str(err):
                    raise CleaningError("block_failed") from err
            for k in _BLOCK_KEYS:
                cur.pop(k, None)
        if want is None:
            await self._refresh()
            return
        channel_id = block_channel_id(self.c.records(item["wohnung_id"]))
        if channel_id is None:
            raise CleaningError("no_block_channel")
        async def create(rng: tuple[str, str]) -> Any:
            res = await client.create_block({"arrivalDate": rng[0], "departureDate": rng[1], "apartmentId": item["wohnung_id"],
                                             "channelId": channel_id, "notice": f"{BLOCK_NOTICE} · {item['key']}"})
            return (res or {}).get("id")
        try:
            rid = await create(want)
        except SmoobuError as err:
            _LOGGER.warning("Smoobu: Reinigungs-Sperre %s nicht angelegt: %s", want, err)
            if have:
                try:
                    old = await create(have)
                    cur.update({"sperre_id": old, "sperre_von": have[0], "sperre_bis": have[1],
                                "sperre_seit": dt_util.now().isoformat(timespec="seconds")})
                except SmoobuError:
                    pass
            await self._refresh()
            raise CleaningError("block_failed") from err
        cur.update({"sperre_id": rid, "sperre_von": want[0], "sperre_bis": want[1],
                    "sperre_seit": dt_util.now().isoformat(timespec="seconds")})
        await self._refresh()

    async def _refresh(self) -> None:
        self.c.force_revenue_refresh = True
        await self.c.async_request_refresh()

    async def async_reconcile(self) -> int:
        """Eigene Sperren aufräumen: Reinigung gibt es nicht mehr (Storno/Abreise verschoben) → Sperre löschen;
        Sperre in Smoobu von Hand gelöscht → Planung zurück auf den Abreisetag. Rückgabe: Anzahl Änderungen."""
        state = await self._load()
        if not any(v.get("sperre_id") for v in state.values()):
            return 0
        async with self._lock:
            today = dt_util.now().date()
            items = {x["key"] for x in self._build(today, days_back=WIDE_BACK, days_ahead=2 * 366)}
            ids = {r["id"] for r in self.c.records_all() if not r.get("storniert")}
            now = dt_util.now()
            n = tidy = 0
            for key, v in state.items():
                if not v.get("sperre_id"):
                    continue
                if v.get("sperre_bis", "") < today.isoformat():
                    # Sperre ist vorbei → nur noch die Verknüpfung vergessen (spart die Prüfung bei jeder Aktualisierung)
                    for k in _BLOCK_KEYS:
                        v.pop(k, None)
                    tidy += 1
                    continue
                fresh = (now - dt_util.parse_datetime(v.get("sperre_seit") or "1970-01-01T00:00:00+00:00")) < BLOCK_GRACE
                if key not in items:
                    if v["sperre_id"] in ids:
                        try:
                            await self.c.client.delete_reservation(v["sperre_id"])
                        except SmoobuError as err:
                            _LOGGER.warning("Smoobu: Reinigungs-Sperre %s nicht gelöscht: %s", v["sperre_id"], err)
                            continue
                    _LOGGER.info("Smoobu: Reinigung %s entfällt – eigene Sperre %s freigegeben", key, v["sperre_id"])
                elif v["sperre_id"] in ids or fresh:
                    continue  # Sperre vorhanden (oder gerade erst angelegt)
                else:
                    _LOGGER.info("Smoobu: Reinigungs-Sperre %s fehlt in Smoobu – Planung %s zurück auf Abreise", v["sperre_id"], key)
                    v.pop("geplant", None)
                for k in _BLOCK_KEYS:
                    v.pop(k, None)
                n += 1
            if n or tidy:
                await self.store.async_save(state)
        if n:
            await self._refresh()
        return n

    async def async_bulk(self, user: Any, target: str, until: str, since: str | None = None,
                         replace: str | None = None) -> dict[str, int]:
        """v1.19.1b2: alle vergangenen, nicht erledigten Reinigungen mit Abreise in [since, until] nachtragen.

        `replace` (optional): zusätzlich bereits erledigte, die von dieser Person gereinigt wurden, auf
        `target` umschreiben (Korrektur einer früheren Sammelaktion). Ohne Push, ein Speichern am Ende.
        Rechte und Person wie bei der Einzelaktion „nachtragen“."""
        opts = self.opts
        if "reinigung_zuweisen" not in rechte.rights_of(user, opts):
            raise CleaningError("unauthorized")
        today = dt_util.now().date().isoformat()
        until = min(until, today)
        if target == UNKNOWN:
            who_name = UNKNOWN_NAME
        else:
            tu = await self.hass.auth.async_get_user(target) if target else None
            if tu is None or not rechte.allowed(tu, opts, "reinigung"):
                raise CleaningError("invalid_user")
            who_name = tu.name or target
        state = await self._load()
        now = dt_util.now().isoformat(timespec="minutes")
        me = getattr(user, "id", None)
        done = replaced = 0
        for item in self._build(dt_util.now().date(), days_back=WIDE_BACK, days_ahead=0):
            if item["datum"] > until or (since and item["datum"] < since):
                continue
            cur = dict(state.get(item["key"], {}))
            if cur.get("status") == "erledigt":
                if not replace or cur.get("gereinigt_von") != replace:
                    continue
                replaced += 1
            else:
                done += 1
            cur.update({
                "zugewiesen": None if target == UNKNOWN else target, "status": "erledigt",
                "erledigt_von": getattr(user, "name", None), "erledigt_von_id": me, "erledigt_um": None,
                "gereinigt_von": target, "gereinigt_name": who_name, "nachgetragen": now, "geaendert": now,
                "snapshot": {k: item[k] for k in ("datum", "wohnung_id", "check_out", "wechsel", "hund", "personen", "naechte")},
            })
            state[item["key"]] = cur
        if done or replaced:
            await self.store.async_save(state)
            self.c.async_update_listeners()
        return {"nachgetragen": done, "ersetzt": replaced}

    # --- Pushes ----------------------------------------------------------
    def _phone(self, user_id: str) -> str | None:
        return (self.opts.get(CONF_CLEANING_PHONES) or {}).get(user_id)

    def _text(self, item: dict[str, Any]) -> str:
        d = date.fromisoformat(item.get("tag") or item["datum"])
        if d.isoformat() == item["datum"]:
            parts = [f"{_DOW[d.weekday()]} {d.strftime('%d.%m.')} ab {item['check_out']} Uhr"]
        else:  # v1.20.0: später geplant – Abreisetag zur Orientierung
            parts = [f"{_DOW[d.weekday()]} {d.strftime('%d.%m.')} (Abreise {date.fromisoformat(item['datum']).strftime('%d.%m.')})"]
        if len(self.c.data.apartments if self.c.data else {}) > 1:
            parts.append(self.c.apartment_code(item["wohnung_id"]))
        n = item.get("naechste")
        if item["wechsel"]:
            parts.append(f"Gästewechsel – Anreise {n['check_in']} Uhr, {n['personen']} Pers.{' 🐕' if n['hund'] else ''}")
        elif n and not n["sperre"]:
            nd = date.fromisoformat(n["datum"])
            parts.append(f"nächste Anreise {nd.strftime('%d.%m.')}")
        if item["hund"]:
            parts.append("Gast mit Hund 🐕")
        return " · ".join(p for p in parts if p)

    async def _push(self, user_id: str, item: dict[str, Any], why: str) -> None:
        if not self.opts.get(CONF_CLEANING_NOTIFY, True) or not rechte.module_on(self.opts, "reinigung"):
            return  # v1.19.0b10: auch bei ausgeschaltetem Modul keine Pushes
        phone = self._phone(user_id)
        notifier = getattr(self.c, "notifier", None)
        if not phone or notifier is None:
            return
        title = {"zugewiesen": "🧹 Reinigung für dich", "entfernt": "🧹 Reinigung abgegeben",
                 "erinnerung": "🧹 Morgen Reinigung", "verschoben": "🧹 Reinigung verschoben"}[why]
        await notifier.send("reinigung", title, self._text(item),
                            {"tag": f"smoobu_reinigung_{item['key']}", "url": self._path()},
                            check_enabled=False, to=[phone])

    def _path(self) -> str:
        """Ziel beim Antippen: Ansicht `smoobu-reinigung` im Dashboard des Assistent-Pfads (z. B.
        /mein-dashboard/smoobu-nachrichten → /mein-dashboard/smoobu-reinigung), sonst /lovelace/…"""
        parts = [p for p in str(self.opts.get("assist_path") or "/lovelace").split("/") if p]
        return f"/{parts[0] if parts else 'lovelace'}/smoobu-reinigung"

    async def _remind(self, _now: datetime | None) -> None:
        """Vorabend: zugewiesene, offene Reinigungen von morgen an die jeweilige Person."""
        state = await self._load()
        if self._anonymize(state):  # v1.19.1b3: täglich Aufbewahrungsfrist prüfen
            await self.store.async_save(state)
        tomorrow = (dt_util.now().date() + timedelta(days=1)).isoformat()
        for item in self._build(dt_util.now().date(), days_ahead=DAYS_AHEAD):
            s = state.get(item["key"], {})
            item = {**item, "tag": s.get("geplant") or item["datum"]}  # v1.20.0: nach dem geplanten Tag
            if item["tag"] == tomorrow and s.get("zugewiesen") and s.get("status", "offen") == "offen":
                await self._push(s["zugewiesen"], item, "erinnerung")


_DOW = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def minutes_by_user(opts: dict[str, Any]) -> dict[str, float]:
    """v1.19.1b4: eigene Standard-Reinigungszeit je Person (Minuten); leer = allgemeiner Standard."""
    return {str(k): float(v) for k, v in (opts.get(CONF_CLEANING_MINUTES_BY_USER) or {}).items() if v not in (None, "")}


def minutes_of(by_user: dict[str, float], uid: str | None, default: float) -> float:
    """Standardzeit der Person (falls eingetragen), sonst allgemeiner Standard."""
    return by_user.get(uid or "", default)


def wage_of(wages: dict[str, float], uid: str | None, default: float) -> float:
    """Stundenlohn einer Person; „Unbekannt“ ohne eigenen Eintrag = 0 €/h (v1.19.1b2)."""
    if uid == UNKNOWN:
        return wages.get(UNKNOWN, 0.0)
    return wages.get(uid or "", default)


def _delay_minutes(snap: dict[str, Any], done: str | None) -> int | None:
    """Minuten vom Check-out bis zum Abhaken (negativ = vorher abgehakt; None = unbekannt/anderer Tag > 2 Tage)."""
    if snap.get("geplant") and snap["geplant"] != snap.get("datum"):
        return None  # v1.20.0: bewusst später geplant – kein „Verzug“ ab Check-out
    try:
        co = datetime.fromisoformat(f"{snap['datum']}T{snap.get('check_out') or '11:00'}")
        d = datetime.fromisoformat(done or "")
    except (TypeError, ValueError, KeyError):
        return None
    minutes = int((d.replace(tzinfo=None) - co).total_seconds() // 60)
    return minutes if abs(minutes) <= 2 * 24 * 60 else None


def stats(state: dict[str, dict[str, Any]], pending: list[dict[str, Any]], start: str, end: str,
          apartments: set[Any] | None, names: dict[str, str], codes: dict[Any, str], today: str,
          wage: Callable[[str | None], float] | None = None, minutes: float = 60.0,
          minutes_for: Callable[[str | None], float | None] | None = None) -> dict[str, Any]:
    """Auswertung „Wer hat wann welche Wohnung gereinigt“ für [start, end).

    `pending` = aktuelle Reinigungen mit Zuweisung/Status (für vergangene, nicht abgehakte).
    Je Person: Anzahl, Gästewechsel, mit Hund, Personen und Nächte der abgereisten Gäste (Aufwand),
    Ø Minuten vom Check-out bis zum Abhaken. Dazu Monat × Person, Wohnung × Person und eine Liste.
    v1.19.0: Kosten je Reinigung = Standardzeit × Stundenlohn der Person (`wage`, sonst Standardlohn).
    """
    done = []
    for key, v in state.items():
        snap = v.get("snapshot")
        if v.get("status") != "erledigt" or not snap or not (start <= snap["datum"] < end):
            continue
        if apartments is not None and snap["wohnung_id"] not in apartments:
            continue
        who = v.get("gereinigt_von")
        # v1.19.1b4: gebuchte Dauer > Standardzeit der Person > allgemeiner Standard
        mins = v.get("minuten") or (minutes_for(who) if minutes_for else None) or minutes
        done.append({**snap, "key": key, "person_id": who,
                     "person": names.get(who) or v.get("gereinigt_name") or v.get("erledigt_von") or "?",
                     "erledigt_um": v.get("erledigt_um"), "abgehakt_von": v.get("erledigt_von"),
                     "nachgetragen": v.get("nachgetragen"),  # v1.19.1
                     "verzug_min": _delay_minutes(snap, v.get("erledigt_um")),
                     "minuten": mins, "minuten_gebucht": v.get("minuten") is not None,
                     "kosten": round((wage(who) if wage else 0.0) * mins / 60, 2),
                     "kuerzel": codes.get(snap["wohnung_id"], "")})
    done.sort(key=lambda x: (x["datum"], x["key"]), reverse=True)
    people: dict[str, dict[str, Any]] = {}
    months: dict[str, dict[str, int]] = {}
    flats: dict[str, dict[str, int]] = {}
    for x in done:
        p = people.setdefault(x["person"], {"person": x["person"], "anzahl": 0, "wechsel": 0, "hund": 0, "personen": 0,
                                            "naechte": 0, "_delay": [], "letzte": None, "erste": None, "kosten": 0.0,
                                            "stundenlohn": wage(x["person_id"]) if wage else None, "minuten": 0})
        p["anzahl"] += 1
        p["minuten"] += x["minuten"]
        p["kosten"] = round(p["kosten"] + x["kosten"], 2)
        p["wechsel"] += int(bool(x["wechsel"]))
        p["hund"] += int(bool(x["hund"]))
        p["personen"] += int(x.get("personen") or 0)
        p["naechte"] += int(x.get("naechte") or 0)
        if x["verzug_min"] is not None:
            p["_delay"].append(x["verzug_min"])
        p["letzte"] = max(p["letzte"] or x["datum"], x["datum"])
        p["erste"] = min(p["erste"] or x["datum"], x["datum"])
        months.setdefault(x["datum"][:7], {}).setdefault(x["person"], 0)
        months[x["datum"][:7]][x["person"]] += 1
        flat = x["kuerzel"] or str(x["wohnung_id"])
        flats.setdefault(flat, {}).setdefault(x["person"], 0)
        flats[flat][x["person"]] += 1
    total = len(done)
    persons = []
    for p in sorted(people.values(), key=lambda p: -p["anzahl"]):
        delays = sorted(p.pop("_delay"))
        p["anteil_prozent"] = round(p["anzahl"] / total * 100) if total else 0
        p["verzug_median_min"] = delays[len(delays) // 2] if delays else None
        p["personen_je_reinigung"] = round(p["personen"] / p["anzahl"], 1) if p["anzahl"] else None
        p["minuten_je_reinigung"] = round(p["minuten"] / p["anzahl"]) if p["anzahl"] else None
        persons.append(p)
    # Vergangene Reinigungen im Zeitraum, die (noch) nicht abgehakt sind – erst ab dem ersten Eintrag im
    # Reinigungsboard (vorher gab es nichts abzuhaken; sonst stünden alle Abreisen vor dem Update hier)
    first = min((k.split(":")[-1] for k in state), default=None)
    missed = [x for x in pending if first and max(start, first) <= x["datum"] < min(end, today) and x["status"] != "erledigt"
              and (apartments is None or x["wohnung_id"] in apartments)]
    return {
        "anzahl": total,
        "kosten": round(sum(x["kosten"] for x in done), 2),
        "minuten": minutes,  # Standard-Reinigungszeit
        "minuten_summe": sum(x["minuten"] for x in done),
        "minuten_gebucht": sum(1 for x in done if x["minuten_gebucht"]),
        "wechsel": sum(1 for x in done if x["wechsel"]),
        "hund": sum(1 for x in done if x["hund"]),
        "nicht_abgehakt": len(missed),
        "nicht_abgehakt_ohne_zuweisung": sum(1 for x in missed if not x.get("zugewiesen")),
        "personen": persons,
        "monate": [{"monat": m, "je_person": v, "summe": sum(v.values())} for m, v in sorted(months.items())],
        "wohnungen": [{"wohnung": f, "je_person": v, "summe": sum(v.values())} for f, v in sorted(flats.items())],
        "liste": done[:100],
        "seit": min((k.split(":")[-1] for k, v in state.items() if v.get("status") == "erledigt"), default=None),
    }


def merge_stats(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """Statistik mehrerer Smoobu-Konten zusammenführen (Ansicht „Alle Wohnungen“ über Konten)."""
    out: dict[str, Any] = {"kosten": 0.0, "minuten": parts[0].get("minuten", 60) if parts else 60, "anzahl": 0, "wechsel": 0, "hund": 0, "nicht_abgehakt": 0, "nicht_abgehakt_ohne_zuweisung": 0,
                           "personen": [], "monate": [], "wohnungen": [], "liste": [], "seit": None}
    people: dict[str, dict[str, Any]] = {}
    months: dict[str, dict[str, int]] = {}
    for p in parts:
        for k in ("anzahl", "wechsel", "hund", "nicht_abgehakt", "nicht_abgehakt_ohne_zuweisung"):
            out[k] += p[k]
        out["kosten"] = round(out["kosten"] + p.get("kosten", 0.0), 2)
        out["minuten_summe"] = out.get("minuten_summe", 0) + p.get("minuten_summe", 0)
        out["minuten_gebucht"] = out.get("minuten_gebucht", 0) + p.get("minuten_gebucht", 0)
        for x in p["personen"]:
            q = people.setdefault(x["person"], {**x, "anzahl": 0, "wechsel": 0, "hund": 0, "personen": 0, "naechte": 0, "kosten": 0.0, "minuten": 0})
            for k in ("anzahl", "wechsel", "hund", "personen", "naechte", "kosten", "minuten"):
                q[k] += x[k]
            q["letzte"] = max(q.get("letzte") or "", x.get("letzte") or "") or None
        for m in p["monate"]:
            dst = months.setdefault(m["monat"], {})
            for who, n in m["je_person"].items():
                dst[who] = dst.get(who, 0) + n
        out["wohnungen"] += p["wohnungen"]
        out["liste"] += p["liste"]
        if p["seit"] and (out["seit"] is None or p["seit"] < out["seit"]):
            out["seit"] = p["seit"]
    total = out["anzahl"]
    for q in people.values():
        q["anteil_prozent"] = round(q["anzahl"] / total * 100) if total else 0
        q["personen_je_reinigung"] = round(q["personen"] / q["anzahl"], 1) if q["anzahl"] else None
        q["minuten_je_reinigung"] = round(q["minuten"] / q["anzahl"]) if q["anzahl"] else None
    out["personen"] = sorted(people.values(), key=lambda q: -q["anzahl"])
    out["monate"] = [{"monat": m, "je_person": v, "summe": sum(v.values())} for m, v in sorted(months.items())]
    out["liste"] = sorted(out["liste"], key=lambda x: (x["datum"], x["key"]), reverse=True)[:100]
    return out

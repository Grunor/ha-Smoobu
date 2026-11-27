"""Benachrichtigungen (v1.17.0): welche Pushes an wen und wann.

Push-Arten (je an/aus und eigene Empfänger, Optionsschritt „Benachrichtigungen“):

- buchung    Neue Buchung (aus dem Datenabgleich, nicht aus Sperrzeiten)
- storno     Storno oder Änderung (Personen, Ankunftszeit, Preis), Vorher → Nachher
- umbuchung  v1.18.0: Zeitraum oder Unterkunft geändert (eigene Push-Art; ohne eigene Einstellung wie „storno“)
- nachricht  Neue Gästenachricht (auch ohne KI; mit KI-Vorschlag kommt stattdessen der Vorschlag)
- vorschlag  KI-Antwortvorschlag mit Buttons (bisheriges Verhalten)
- zahlung    Zahlungserinnerung X Tage vor Anreise (ohne Kanäle mit Zahlung über das Portal)
- briefing   Tagesbriefing zur festen Uhrzeit
- luecken    Nicht buchbare Lücken (Mindestaufenthalt) zur festen Uhrzeit
- lexware    v1.20.0 (BETA): Zahlungseingang, Anzahlung fehlt, Restzahlung am Anreisetag offen (Lexware Office)

Ruhezeit: Nicht dringende Pushes werden in der Ruhezeit gesammelt und zum Ende
zugestellt (je Tag/Thema nur der neueste Stand). Sofort kommen weiterhin:
dringende KI-Vorschläge, Bestätigungen auf eigene Aktionen und – wenn so
eingestellt (Standard) – Gästenachrichten.

Rückwärtskompatibel: Fehlen die neuen Optionen, gelten die bisherigen
(Empfänger „assist_recipients“, Tagesbriefing/Lücken des Assistenten).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ASSIST_BRIEFING,
    CONF_ASSIST_BRIEFING_TIME,
    CONF_ASSIST_GAPS,
    CONF_ASSIST_PATH,
    CONF_ASSIST_RECIPIENTS,
    CONF_NOTIFY_GAPS_TIME,
    CONF_NOTIFY_PAYMENT_DAYS,
    CONF_NOTIFY_PAYMENT_TIME,
    CONF_NOTIFY_QUIET,
    CONF_NOTIFY_QUIET_FROM,
    CONF_NOTIFY_QUIET_MESSAGES,
    CONF_NOTIFY_QUIET_TO,
    NOTIFY_QUIET_DEFAULT,
    DEFAULT_NOTIFY_GAPS_TIME,
    DEFAULT_NOTIFY_PAYMENT_DAYS,
    DEFAULT_NOTIFY_PAYMENT_TIME,
    DEFAULT_NOTIFY_QUIET_FROM,
    DEFAULT_NOTIFY_QUIET_TO,
    DOMAIN,
    NOTIFY_TYPES,
)

if TYPE_CHECKING:
    from .coordinator import SmoobuCoordinator

_LOGGER = logging.getLogger(__name__)
STORE_VERSION = 1

# Felder, deren Änderung als „Änderung“ gemeldet wird (Datensatz-Schlüssel → Anzeige)
CHANGE_FIELDS = {"anreise": "Anreise", "abreise": "Abreise", "wohnung_id": "Unterkunft", "personen": "Personen",
                 "check_in": "Ankunft", "brutto": "Preis"}
# v1.18.0: diese Felder machen aus einer Änderung eine „Umbuchung“ (eigene Push-Art)
MOVE_FIELDS = ("anreise", "abreise", "wohnung_id")


def opt_enabled(opts: dict[str, Any], kind: str) -> bool:
    """Push-Art an? Ohne neue Option: bisheriges Verhalten (Vorschlag an, Briefing/Lücken wie Assistent)."""
    key = f"notify_{kind}"
    if key in opts:
        return bool(opts[key])
    if kind == "vorschlag":
        return True
    if kind == "umbuchung":  # v1.18.0: neue Push-Art erbt ohne eigene Einstellung „Storno & Änderung“
        return opt_enabled(opts, "storno")
    if kind == "briefing":
        return bool(opts.get(CONF_ASSIST_BRIEFING))
    if kind == "luecken":
        return bool(opts.get(CONF_ASSIST_GAPS))
    if kind == "lexware":  # v1.20.0: ohne eigene Einstellung an, sobald das Lexware-Modul an ist
        return bool(opts.get("lexware_enabled"))
    return False


def opt_quiet(opts: dict[str, Any], kind: str) -> bool:
    """v1.18.0: Hält diese Push-Art die Ruhezeit ein (wird gesammelt)? Ohne eigene Option: bisheriges Verhalten."""
    key = f"notify_{kind}_quiet"
    if key in opts:
        return bool(opts[key])
    if kind == "umbuchung" and "notify_storno_quiet" in opts:
        return bool(opts["notify_storno_quiet"])  # v1.18.0: wie „Storno & Änderung“, bis eigens eingestellt
    if kind == "nachricht":
        # Altwert „Gästenachrichten sofort“ (Standard an) → hält die Ruhezeit nicht ein
        return not opts.get(CONF_NOTIFY_QUIET_MESSAGES, True)
    return NOTIFY_QUIET_DEFAULT.get(kind, True)


def opt_recipients(opts: dict[str, Any], kind: str) -> list[str]:
    """Empfänger je Push-Art; ohne eigene Auswahl die bisherigen Assistent-Empfänger."""
    own = opts.get(f"notify_{kind}_to")
    if not own and kind == "umbuchung" and "notify_umbuchung" not in opts:
        own = opts.get("notify_storno_to")  # v1.18.0: Empfänger wie „Storno & Änderung“, bis eigene gewählt sind
    return list(own) if own else list(opts.get(CONF_ASSIST_RECIPIENTS) or [])


def _hm(value: str | None, fallback: str) -> time:
    try:
        hh, mm = (value or fallback)[:5].split(":")
        return time(int(hh), int(mm))
    except ValueError:
        hh, mm = fallback.split(":")
        return time(int(hh), int(mm))


def in_quiet(now: time, start: time, end: time) -> bool:
    """Liegt `now` in der Ruhezeit [start, end)? Über Mitternacht (21:00–07:00) wird unterstützt."""
    if start == end:
        return False
    if start < end:
        return start <= now < end
    return now >= start or now < end


def _money(v: float | None) -> str:
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".") if v else "–"


def _d(iso: str | None) -> str:
    try:
        return date.fromisoformat(iso).strftime("%d.%m.")
    except (TypeError, ValueError):
        return iso or "?"


class SmoobuNotifier:
    """Zustellung aller Smoobu-Pushes eines Kontos (hängt am Coordinator)."""

    def __init__(self, hass: HomeAssistant, coordinator: SmoobuCoordinator) -> None:
        self.hass = hass
        self.c = coordinator
        self.store: Store = Store(hass, STORE_VERSION, f"{DOMAIN}_notify_{coordinator.config_entry.entry_id}")
        # warteschlange: in der Ruhezeit gesammelte Pushes; gemeldet: bereits erinnerte Zahlungen
        self.data: dict[str, Any] = {"warteschlange": [], "gemeldet": []}
        self._snapshot: dict[int, dict[str, Any]] | None = None
        self._unsubs: list[Callable[[], None]] = []

    @property
    def opts(self) -> dict[str, Any]:
        return dict(self.c.config_entry.options)

    def enabled(self, kind: str) -> bool:
        return opt_enabled(self.opts, kind)

    # --- Lebenszyklus ----------------------------------------------------
    async def async_setup(self) -> None:
        stored = await self.store.async_load()
        if stored:
            self.data.update(stored)
        o = self.opts
        if o.get(CONF_NOTIFY_QUIET):
            end = _hm(o.get(CONF_NOTIFY_QUIET_TO), DEFAULT_NOTIFY_QUIET_TO)
            self._unsubs.append(async_track_time_change(self.hass, self._flush, hour=end.hour, minute=end.minute, second=0))
        if self.enabled("zahlung"):
            t = _hm(o.get(CONF_NOTIFY_PAYMENT_TIME), DEFAULT_NOTIFY_PAYMENT_TIME)
            self._unsubs.append(async_track_time_change(self.hass, self._payments, hour=t.hour, minute=t.minute, second=0))
        self._unsubs.append(self.c.async_add_listener(self._on_data))
        self._on_data()  # Ausgangsstand merken (keine Pushes für bestehende Buchungen)
        # Nach Neustart außerhalb der Ruhezeit: Liegengebliebenes zustellen
        if not self.quiet_now():
            await self._flush(None)

    async def async_unload(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()
        await self.store.async_save(self.data)

    def _save(self) -> None:
        self.store.async_delay_save(lambda: self.data, 2)

    # --- Zustellung ------------------------------------------------------
    def quiet_now(self) -> bool:
        o = self.opts
        if not o.get(CONF_NOTIFY_QUIET):
            return False
        return in_quiet(
            dt_util.now().time(),
            _hm(o.get(CONF_NOTIFY_QUIET_FROM), DEFAULT_NOTIFY_QUIET_FROM),
            _hm(o.get(CONF_NOTIFY_QUIET_TO), DEFAULT_NOTIFY_QUIET_TO),
        )

    async def send(
        self, kind: str, title: str | None, message: str, data: dict[str, Any] | None = None,
        *, urgent: bool = False, check_enabled: bool = True, to: list[str] | None = None,
    ) -> bool:
        """Push einer Art an deren Empfänger; in der Ruhezeit (nicht dringend) gesammelt.

        `check_enabled=False` für Bestätigungen/Fehler und das Entfernen von Pushes,
        die immer an die Empfänger der Art gehen. Rückgabe: zugestellt oder gesammelt.
        """
        if check_enabled and not self.enabled(kind):
            return False
        data = dict(data or {})
        if message == "clear_notification":
            # Gesammelten Push gleicher Kennung verwerfen, dann (falls schon zugestellt) entfernen
            self._drop(data.get("tag"))
            await self._deliver(kind, None, message, data, **({"to": to} if to else {}))
            return True
        # v1.18.0: je Push-Art einstellbar, ob sie die Ruhezeit einhält. Dringende Vorschläge und
        # Bestätigungen/Fehler (urgent) kommen immer sofort.
        hold = not urgent and self.quiet_now() and opt_quiet(self.opts, kind)
        if hold:
            self._drop(data.get("tag"))  # je Thema nur der neueste Stand
            self.data["warteschlange"].append({"art": kind, "titel": title, "text": message, "daten": data,
                                               "zeit": dt_util.now().isoformat(), **({"an": to} if to else {})})
            self.data["warteschlange"] = self.data["warteschlange"][-50:]
            self._save()
            return True
        await self._deliver(kind, title, message, data, **({"to": to} if to else {}))
        return True

    def _drop(self, tag: str | None) -> None:
        if not tag:
            return
        before = len(self.data["warteschlange"])
        self.data["warteschlange"] = [q for q in self.data["warteschlange"] if (q.get("daten") or {}).get("tag") != tag]
        if len(self.data["warteschlange"]) != before:
            self._save()

    async def _deliver(self, kind: str, title: str | None, message: str, data: dict[str, Any],
                       to: list[str] | None = None) -> None:
        for svc in to or opt_recipients(self.opts, kind):
            name = svc.removeprefix("notify.")
            payload: dict[str, Any] = {"message": message, "data": data}
            if title:
                payload["title"] = title
            try:
                await self.hass.services.async_call("notify", name, payload, blocking=False)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Push an %s fehlgeschlagen: %s", name, err)

    async def _flush(self, _now: datetime | None) -> None:
        """Ende der Ruhezeit: gesammelte Pushes zustellen (älteste zuerst)."""
        queue, self.data["warteschlange"] = list(self.data["warteschlange"]), []
        if queue:
            self._save()
        for q in queue:
            await self._deliver(q["art"], q.get("titel"), q["text"], q.get("daten") or {}, **({"to": q["an"]} if q.get("an") else {}))

    # --- Buchung / Storno / Änderung aus dem Datenabgleich ----------------
    @callback
    def _on_data(self) -> None:
        """Nach jeder Aktualisierung: neue, stornierte und geänderte Buchungen erkennen."""
        snap = {
            int(r["id"]): {**{k: r.get(k) for k in CHANGE_FIELDS}, "storniert": r["storniert"], "rec": r}
            for r in self.c.records_all() if r.get("id") and not r["blockiert"]
        }
        prev, self._snapshot = self._snapshot, snap
        if prev is None:
            return  # erster Stand nach Start: nur merken
        today = dt_util.now().date()
        for rid, cur in snap.items():
            old = prev.get(rid)
            rec = cur["rec"]
            if old is None:
                # Neu im Datenbestand. Nur wirklich neue Buchungen melden (angelegt ≤ 2 Tage) –
                # nicht solche, die durch das wandernde Zeitfenster neu hereinkommen.
                created = (rec.get("erstellt") or "")[:10]
                if not cur["storniert"] and created and (today - date.fromisoformat(created)).days <= 2:
                    self.hass.async_create_task(self.send("buchung", *self._booking_text(rec)))
                continue
            # Vergangene Aufenthalte nicht melden (Datenquelle wechselt, wenn sie aus dem Zeitfenster fallen)
            if rec["abreise"] < today.isoformat():
                continue
            if cur["storniert"] and not old["storniert"]:
                self.hass.async_create_task(self.send("storno", *self._cancel_text(rec)))
                continue
            if cur["storniert"]:
                continue
            changes = [(k, label, old[k], cur[k]) for k, label in CHANGE_FIELDS.items() if old[k] != cur[k]]
            if not changes:
                continue
            # v1.18.0: Zeitraum/Unterkunft geändert → eigene Push „Umbuchung“ (inkl. weiterer Änderungen);
            # ist sie ausgeschaltet, kommt die Änderung wie bisher unter „Storno & Änderung“
            if any(k in MOVE_FIELDS for k, *_ in changes) and self.enabled("umbuchung"):
                self.hass.async_create_task(self.send("umbuchung", *self._move_text(rec, old, changes)))
            else:
                self.hass.async_create_task(self.send("storno", *self._change_text(rec, [c[1:] for c in changes])))

    def _path(self) -> str:
        return self.opts.get(CONF_ASSIST_PATH) or "/lovelace"

    def _apt(self, rec: dict[str, Any]) -> str:
        """Wohnungskürzel voranstellen, wenn das Konto mehr als eine Wohnung hat."""
        if self.c.data and len(self.c.data.apartments) > 1:
            return f"[{self.c.apartment_code(rec.get('wohnung_id'))}] "
        return ""

    def _booking_text(self, r: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
        body = (f"{_d(r['anreise'])} – {_d(r['abreise'])} · {r['naechte']} N. · {r['personen']} P."
                f"{' · 🐕' if r.get('hund') else ''}\n{r.get('kanal')} · {_money(r.get('brutto'))}"
                + (f" · offen {_money(r['offen'])}" if r.get("offen") else ""))
        return (f"🆕 {self._apt(r)}Neue Buchung: {r.get('gast')}", body,
                {"tag": f"smoobu_buchung_{r['id']}", "url": self._path(), "group": "smoobu_buchungen"})

    def _cancel_text(self, r: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
        body = f"{_d(r['anreise'])} – {_d(r['abreise'])} · {r['naechte']} N. · {r.get('kanal')} · {_money(r.get('brutto'))}"
        return (f"❌ {self._apt(r)}Storniert: {r.get('gast')}", body,
                {"tag": f"smoobu_buchung_{r['id']}", "url": self._path(), "group": "smoobu_buchungen"})

    def _apt_name(self, apt_id: Any) -> str:
        """Name der Wohnung (mit Kürzel bei mehreren Wohnungen)."""
        apts = self.c.data.apartments if self.c.data else {}
        name = (apts.get(apt_id) or {}).get("name") or str(apt_id)
        return f"[{self.c.apartment_code(apt_id)}] {name}" if len(apts) > 1 else name

    def _move_text(self, r: dict[str, Any], old: dict[str, Any], changes: list[tuple[str, str, Any, Any]]) -> tuple[str, str, dict[str, Any]]:
        """v1.18.0: Umbuchung – Zeitraum (mit Nächten) und Unterkunft Vorher → Nachher, dann weitere Änderungen."""
        keys = {k for k, *_ in changes}
        lines = []
        if keys & {"anreise", "abreise"}:
            n_old = (date.fromisoformat(old["abreise"]) - date.fromisoformat(old["anreise"])).days
            lines.append(f"Zeitraum: {_d(old['anreise'])} – {_d(old['abreise'])} ({n_old} N.)\n"
                         f"→ {_d(r['anreise'])} – {_d(r['abreise'])} ({r['naechte']} N.)")
        if "wohnung_id" in keys:
            lines.append(f"Unterkunft: {self._apt_name(old['wohnung_id'])} → {self._apt_name(r.get('wohnung_id'))}")
        rest = [c[1:] for c in changes if c[0] not in MOVE_FIELDS]
        if rest:
            lines.append(self._change_text(r, rest)[1])
        what = "Unterkunft gewechselt" if keys == {"wohnung_id"} else "Umgebucht"
        icon = "🏠" if keys == {"wohnung_id"} else "📅"
        return (f"{icon} {self._apt(r)}{what}: {r.get('gast')}", "\n".join(lines),
                {"tag": f"smoobu_buchung_{r['id']}", "url": self._path(), "group": "smoobu_buchungen"})

    def _change_text(self, r: dict[str, Any], changes: list[tuple[str, Any, Any]]) -> tuple[str, str, dict[str, Any]]:
        def fmt(label: str, v: Any) -> str:
            if label in ("Anreise", "Abreise"):
                return _d(v)
            if label == "Unterkunft":
                return self._apt_name(v)
            if label == "Preis":
                return _money(v)
            return str(v) if v not in (None, "") else "–"
        lines = [f"{label}: {fmt(label, a)} → {fmt(label, b)}" for label, a, b in changes]
        return (f"✏️ {self._apt(r)}Geändert: {r.get('gast')}", "\n".join(lines),
                {"tag": f"smoobu_buchung_{r['id']}", "url": self._path(), "group": "smoobu_buchungen"})

    # --- Zahlungserinnerung ----------------------------------------------
    async def _payments(self, _now: datetime | None) -> None:
        """Täglich: offene Zahlungen von Buchungen mit Anreise in genau X Tagen (bzw. überfällig heute)."""
        days = int(self.opts.get(CONF_NOTIFY_PAYMENT_DAYS, DEFAULT_NOTIFY_PAYMENT_DAYS))
        today = dt_util.now().date()
        due = []
        for r in self.c.records_all():
            if r["blockiert"] or r["storniert"] or not (r.get("offen") or 0) > 0:
                continue
            left = (date.fromisoformat(r["anreise"]) - today).days
            key = f"zahlung:{r['id']}:{'heute' if left == 0 else days}"
            if left in (days, 0) and key not in self.data["gemeldet"]:
                due.append((r, left, key))
        for r, left, key in due:
            when = "heute" if left == 0 else f"in {left} Tagen"
            await self.send("zahlung", f"💶 {self._apt(r)}Zahlung offen: {r.get('gast')}",
                            f"Anreise {when} ({_d(r['anreise'])}) · offen {_money(r['offen'])} von {_money(r.get('brutto'))} · {r.get('kanal')}",
                            {"tag": f"smoobu_zahlung_{r['id']}", "url": self._path()})
            self.data["gemeldet"] = (self.data["gemeldet"] + [key])[-300:]
        if due:
            self._save()

    def gaps_time(self) -> time:
        return _hm(self.opts.get(CONF_NOTIFY_GAPS_TIME), DEFAULT_NOTIFY_GAPS_TIME)

    def briefing_time(self) -> time:
        return _hm(self.opts.get(CONF_ASSIST_BRIEFING_TIME), "07:30")


__all__ = ["NOTIFY_TYPES", "SmoobuNotifier", "in_quiet", "opt_enabled", "opt_quiet", "opt_recipients"]

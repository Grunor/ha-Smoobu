"""Türzugangscodes je Buchung (ab v1.19.0, Wunsch Betreiber 21.11.2026).

Entscheidungen Betreiber (21.11.2026):
- Zufallscode bei neuer Buchung automatisch (Sperrzeiten bekommen keinen), Stellenzahl in den
  Optionen (`door_code_digits`, Standard 6, 4–10).
- Gültig ab Check-in − 2 h bis Check-out + 1 h (Optionen `door_code_before_h`, `door_code_after_h`).
  Ändern sich An-/Abreise, wandert die Gültigkeit mit; der Code bleibt.
- Der Code steht als eigene Zeile in der Smoobu-Notiz der Buchung („Türcode: … (gültig …)“), wird
  bei Änderung ersetzt; der Rest der Notiz bleibt unberührt.
- Schloss-Adapter je Wohnung (Option `door_locks`): kein Schloss, Matter, Z-Wave JS, ZHA,
  Zigbee2MQTT oder eigenes Skript. Gesetzt wird der Code kurz vor Gültigkeitsbeginn in einen freien
  Code-Platz des eingestellten Bereichs, gelöscht nach Gültigkeitsende bzw. bei Storno.

Statischer Code (ab v1.19.0b2, Wunsch Betreiber 21.11.2026, z. B. Schlüsseltresor):
- Modus je Wohnung in `door_locks[<Wohnung>]`: „modus“ = „zufall“ (Standard) oder „statisch“ mit „code“
  (4–12 Ziffern/Buchstaben). Jede Buchung bekommt dann diesen Code – gleiche Ausgabe wie beim
  Zufallscode (Smoobu-Notiz, Entität, Platzhalter {{ turcode }}), aber kein „Neu erzeugen“.
- Wird der statische Code geändert oder der Modus gewechselt, bekommen alle noch nicht abgelaufenen
  Buchungen den neuen Code (Notiz wird ersetzt, ein Schloss neu programmiert). Keine Wechsel-Erinnerung
  (Entscheidung Betreiber).

Statischer Code mit Gültigkeit (v1.20.0, Wunsch/Entscheidungen Betreiber 27.11.2026):
- Je Wohnung zusätzlich „gültig ab/bis“ (ganze Tage, ab 00:00, beide optional = unbegrenzt) und ein
  „nächster Code“ mit „gültig ab“ (Pflicht) und optional „bis“ (`ab`, `bis`, `naechster_code`, `naechster_ab`,
  `naechster_bis` in `door_locks[<Wohnung>]`). Der nächste Code gilt ab seinem Starttag – auch wenn der aktuelle
  kein „bis“ hat.
- Maßgeblich ist der Code am **Anreisetag** (Schlüsseltresor: Gast holt den Schlüssel bei Anreise). Ist der Gast
  schon angereist und für seinen Anreisetag kein Code mehr eingetragen (z. B. nach dem Nachrücken), behält er seinen.
- Gilt für eine Buchung kein Code (abgelaufen, kein nächster): kein Code (Status „fehlt“, Notizzeile entfällt,
  Platzhalter „(Code folgt)“), Aufgabe im Board „Wartet auf dich“ + Push (Push-Art „tuercode“).
- Erinnerung `door_code_static_remind_days` (Standard 14) Tage vor Ablauf des aktuellen Codes, solange kein
  nächster eingetragen ist (Aufgabe + einmal Push).
- Am Starttag rückt der nächste Code in den aktuellen nach (Optionen werden ohne Neuladen umgeschrieben),
  das Feld „nächster Code“ ist danach wieder frei.

Sicherheit:
- Zufall aus `secrets` (kryptografisch). Abgelehnt werden triviale Codes (alle Ziffern gleich, auf-/
  absteigende Folgen, kurze Muster wie 1212/123123) und Codes, die eine andere Buchung derselben
  Wohnung mit überschneidender Gültigkeit hat bzw. die in den letzten 50 Codes vorkamen.
- Codes gelten als Gästedaten: sichtbar nur mit Recht „gaeste“; neu erzeugen mit „belegung“.
- Die Sensor-Entitäten zeigen den Code als Zustand – den sieht jeder HA-Benutzer, der die Entität
  sehen kann (README-Hinweis).
- Der Code geht nie an die KI: Antwortvorschläge enthalten nur den Platzhalter {{ turcode }}, der
  erst beim Senden lokal ersetzt wird.

Speicher: Store `smoobu_tuercodes_<entry_id>` {Buchungs-ID: {...}}; Einträge > 60 Tage nach Ende fallen weg.
"""

from __future__ import annotations

import asyncio
import logging
import re
import secrets
from datetime import date, datetime, time, timedelta
from typing import Any, Callable

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_DOOR_CODE_ENABLED = "door_code_enabled"
CONF_DOOR_CODE_DIGITS = "door_code_digits"
CONF_DOOR_CODE_BEFORE = "door_code_before_h"
CONF_DOOR_CODE_AFTER = "door_code_after_h"
CONF_DOOR_CODE_NOTE = "door_code_note"
CONF_DOOR_LOCKS = "door_locks"   # {Wohnungs-ID: {"typ", "entitaet", "slot_von", "slot_bis"}}
DEFAULT_DIGITS = 6
DEFAULT_BEFORE_H = 2.0
DEFAULT_AFTER_H = 1.0
LOCK_TYPES = ("kein", "matter", "zwave_js", "zha", "z2m", "skript")
MODES = ("zufall", "statisch")
STATIC_RE = re.compile(r"[0-9A-Za-z]{4,12}")
PLACEHOLDER_RE = re.compile(r"\{\{\s*t(?:ü|ue|u)rcode\s*\}\}", re.IGNORECASE)
NOTE_RE = re.compile(r"^T(?:ü|ue)rcode:.*$\n?", re.MULTILINE)
SET_LEAD = timedelta(minutes=10)   # so lange vor Gültigkeitsbeginn ins Schloss schreiben
CHECK_EVERY = timedelta(minutes=5)
CONF_DOOR_CODE_REMIND = "door_code_static_remind_days"  # v1.20.0
DEFAULT_REMIND_DAYS = 14
KEEP_DAYS = 60
RECENT = 50


# ---------------------------------------------------------------------------
# Reine Logik
# ---------------------------------------------------------------------------
def trivial(code: str) -> bool:
    """Leicht zu erratende Codes: alle gleich, Folgen (…1234…, …9876…), Muster mit Periode ≤ 3."""
    if len(set(code)) == 1:
        return True
    diffs = {(int(b) - int(a)) % 10 for a, b in zip(code, code[1:])}
    if diffs in ({1}, {9}):
        return True
    for period in (1, 2, 3):
        if len(code) > period and all(code[i] == code[i % period] for i in range(len(code))):
            return True
    return False


def new_code(digits: int, taken: set[str], rand: Callable[[int], int] = secrets.randbelow) -> str:
    """Zufälliger, nicht trivialer Code, der nicht in `taken` vorkommt (führende Nullen erlaubt)."""
    digits = max(4, min(int(digits), 10))
    for _ in range(1000):
        code = "".join(str(rand(10)) for _ in range(digits))
        if not trivial(code) and code not in taken:
            return code
    raise RuntimeError("Kein freier Türcode gefunden")


def window(rec: dict[str, Any], checkin: time, checkout: time, before_h: float, after_h: float) -> tuple[datetime, datetime]:
    """Gültigkeit: Check-in − before_h bis Check-out + after_h (lokale Zeit, als aware datetime)."""
    tz = dt_util.get_default_time_zone()

    def t(value: Any, fallback: time) -> time:
        try:
            hh, mm = str(value)[:5].split(":")
            return time(int(hh), int(mm))
        except (TypeError, ValueError):
            return fallback

    start = datetime.combine(date.fromisoformat(rec["anreise"]), t(rec.get("check_in"), checkin), tz) - timedelta(hours=before_h)
    end = datetime.combine(date.fromisoformat(rec["abreise"]), t(rec.get("check_out"), checkout), tz) + timedelta(hours=after_h)
    return start, end


def static_for(cfg: dict[str, Any], day: str) -> str | None:
    """v1.20.0: statischer Code, der am Tag `day` (JJJJ-MM-TT, Anreisetag) gilt – None = keiner."""
    nxt, nab, nbis = str(cfg.get("naechster_code") or ""), cfg.get("naechster_ab"), cfg.get("naechster_bis")
    if nxt and nab and day >= nab:
        return nxt if not nbis or day <= nbis else None
    code, ab, bis = str(cfg.get("code") or ""), cfg.get("ab"), cfg.get("bis")
    if code and (not ab or day >= ab) and (not bis or day <= bis):
        return code
    return None


def static_end(cfg: dict[str, Any]) -> str | None:
    """v1.20.0: letzter Tag, für den ein statischer Code eingetragen ist (None = unbegrenzt)."""
    if cfg.get("naechster_code") and cfg.get("naechster_ab"):
        return cfg.get("naechster_bis") or None
    return cfg.get("bis") or None


def static_rollover(cfg: dict[str, Any], today: str) -> dict[str, Any] | None:
    """v1.20.0: ab dem Starttag rückt der nächste Code nach – neue Konfiguration oder None (nichts zu tun)."""
    if not (cfg.get("naechster_code") and cfg.get("naechster_ab") and today >= cfg["naechster_ab"]):
        return None
    out = {k: v for k, v in cfg.items() if k not in ("code", "ab", "bis", "naechster_code", "naechster_ab", "naechster_bis")}
    out.update({"code": cfg["naechster_code"], "ab": cfg["naechster_ab"]})
    if cfg.get("naechster_bis"):
        out["bis"] = cfg["naechster_bis"]
    return out


def note_line(code: str, start: datetime, end: datetime) -> str:
    fmt = lambda d: dt_util.as_local(d).strftime("%d.%m. %H:%M")  # noqa: E731
    return f"Türcode: {code} (gültig {fmt(start)} – {fmt(end)})"


def merge_note(notice: str | None, line: str | None) -> str:
    """Türcode-Zeile in die Notiz setzen bzw. ersetzen (line=None entfernt sie); Rest bleibt."""
    rest = NOTE_RE.sub("", notice or "").strip("\n")
    if not line:
        return rest
    return f"{line}\n{rest}" if rest else line


def fill(text: str, code: str | None) -> str:
    """Platzhalter {{ turcode }} durch den Code ersetzen (lokal, erst beim Senden)."""
    return PLACEHOLDER_RE.sub(code or "(Code folgt)", text or "")


# ---------------------------------------------------------------------------
# Schloss-Adapter: (Domain, Aktion, Daten) für setzen und löschen
# ---------------------------------------------------------------------------
def lock_calls(lock: dict[str, Any], action: str, slot: int | None, code: str, item: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    typ, ent = lock.get("typ", "kein"), lock.get("entitaet") or ""
    if typ == "kein":
        return []
    if typ == "matter":
        if action == "setzen":
            return [("matter", "set_lock_credential", {"entity_id": ent, "credential_type": "pin", "credential_data": code,
                                                       "credential_index": slot})]
        return [("matter", "clear_lock_credential", {"entity_id": ent, "credential_type": "pin", "credential_index": slot})]
    if typ == "zwave_js":
        if action == "setzen":
            return [("zwave_js", "set_lock_usercode", {"entity_id": ent, "code_slot": slot, "usercode": code})]
        return [("zwave_js", "clear_lock_usercode", {"entity_id": ent, "code_slot": slot})]
    if typ == "zha":
        if action == "setzen":
            return [("zha", "set_lock_user_code", {"entity_id": ent, "code_slot": slot, "user_code": code})]
        return [("zha", "clear_lock_user_code", {"entity_id": ent, "code_slot": slot})]
    if typ == "z2m":  # entitaet = Gerätename in Zigbee2MQTT (Topic zigbee2mqtt/<name>/set)
        topic = ent if "/" in ent else f"zigbee2mqtt/{ent}/set"
        pin = {"user": slot, "user_type": "unrestricted", "user_enabled": action == "setzen",
               "pin_code": code if action == "setzen" else None}
        import json
        return [("mqtt", "publish", {"topic": topic, "payload": json.dumps({"pin_code": pin})})]
    if typ == "skript":
        return [("script", "turn_on", {"entity_id": ent, "variables": {
            "aktion": action, "code": code, "slot": slot, "gueltig_von": item.get("von"), "gueltig_bis": item.get("bis"),
            "buchung_id": item.get("buchung_id"), "wohnung_id": item.get("wohnung_id")}})]
    return []


class DoorCodes:
    """Türcodes eines Kontos: erzeugen, an Buchungsänderungen anpassen, Notiz, Schloss, Entitäten."""

    def __init__(self, hass: HomeAssistant, coordinator: Any) -> None:
        self.hass = hass
        self.c = coordinator
        self.store: Store = Store(hass, 1, f"{DOMAIN}_tuercodes_{coordinator.config_entry.entry_id}")
        self.codes: dict[str, dict[str, Any]] = {}
        self.recent: dict[str, list[str]] = {}
        self.pushed: list[str] = []  # v1.20.0: Hinweise, zu denen schon ein Push ging
        self._unsubs: list[Callable[[], None]] = []
        self._lock = asyncio.Lock()
        self._loaded = False

    @property
    def opts(self) -> dict[str, Any]:
        return dict(self.c.config_entry.options)

    @property
    def enabled(self) -> bool:
        return bool(self.opts.get(CONF_DOOR_CODE_ENABLED))

    async def async_setup(self) -> None:
        data = await self.store.async_load() or {}
        self.codes, self.recent = dict(data.get("codes") or {}), dict(data.get("zuletzt") or {})
        self.pushed = list(data.get("gemeldet") or [])
        self._loaded = True
        if not self.enabled:
            return
        self._unsubs.append(self.c.async_add_listener(self._on_data))
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, CHECK_EVERY))
        self.hass.async_create_task(self.async_sync())

    async def async_unload(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()
        if self._loaded:
            await self._save()

    async def _save(self) -> None:
        await self.store.async_save({"codes": self.codes, "zuletzt": self.recent, "gemeldet": self.pushed})

    @callback
    def _on_data(self) -> None:
        self.hass.async_create_task(self.async_sync())

    async def _tick(self, _now: Any) -> None:
        await self.async_sync()

    # --- Abgleich mit den Buchungen ---------------------------------------
    def _window(self, rec: dict[str, Any]) -> tuple[datetime, datetime]:
        o = self.opts
        return window(rec, self.c.default_checkin, self.c.default_checkout,
                      float(o.get(CONF_DOOR_CODE_BEFORE, DEFAULT_BEFORE_H)), float(o.get(CONF_DOOR_CODE_AFTER, DEFAULT_AFTER_H)))

    def _taken(self, apt: Any, start: datetime, end: datetime, skip: str | None = None) -> set[str]:
        out = set(self.recent.get(str(apt), []))
        for bid, it in self.codes.items():
            if bid == skip or it.get("wohnung_id") != apt or it.get("status") == "geloescht":
                continue
            if datetime.fromisoformat(it["von"]) < end and start < datetime.fromisoformat(it["bis"]):
                out.add(it["code"])
        return out

    async def async_sync(self) -> None:
        """Neue Buchungen → Code; geänderte Zeiten → Gültigkeit; Storno → löschen; Schloss je Zeitpunkt."""
        if not self.enabled or not self.c.data:
            return
        async with self._lock:
            now = dt_util.now()
            digits = int(self.opts.get(CONF_DOOR_CODE_DIGITS, DEFAULT_DIGITS))
            changed = False
            recs = {str(r["id"]): r for r in self.c.records_all() if not r.get("blockiert")}
            for bid, r in recs.items():
                start, end = self._window(r)
                it = self.codes.get(bid)
                if r.get("storniert"):
                    if it and it.get("status") != "geloescht":
                        await self._clear_lock(it)
                        it.update({"status": "geloescht", "grund": "storniert"})
                        await self._write_note(r, None)
                        changed = True
                    continue
                if end < now:
                    continue  # vergangen: keinen Code mehr erzeugen
                # v1.20.0: statischer Modus → Code, der am Anreisetag gilt (None = keiner eingetragen → „fehlt“)
                is_static = self.static_mode(r["wohnung_id"])
                static = self.static_code(r["wohnung_id"], r["anreise"]) if is_static else None
                if is_static and static is None and it and it.get("code") and r["anreise"] < now.date().isoformat():
                    static = it["code"]  # Gast ist schon da: kein Code mehr eingetragen für seinen Anreisetag → seinen behalten
                if it is None:
                    code = static if is_static else new_code(digits, self._taken(r["wohnung_id"], start, end))
                    it = self.codes[bid] = {"buchung_id": r["id"], "wohnung_id": r["wohnung_id"], "code": code,
                                            "art": "statisch" if is_static else "zufall",
                                            "von": start.isoformat(), "bis": end.isoformat(), "status": "geplant" if code else "fehlt",
                                            "erstellt": now.isoformat(timespec="seconds"), "slot": None, "fehler": None}
                    if not is_static:  # statische Codes nicht in die Zufalls-Historie
                        self.recent.setdefault(str(r["wohnung_id"]), []).append(code)
                        self.recent[str(r["wohnung_id"])] = self.recent[str(r["wohnung_id"])][-RECENT:]
                    changed = True
                elif it.get("status") not in ("geloescht", "abgelaufen") and (
                        (is_static and it.get("code") != static) or (not is_static and it.get("art") == "statisch")):
                    # Statischer Code geändert (auch: Gültigkeit/nächster Code) bzw. Modus gewechselt → Code tauschen
                    # (Schloss neu, Notiz unten); v1.20.0: static None = für diese Anreise kein Code → „fehlt“
                    await self._swap(it, static if is_static else new_code(digits, self._taken(r["wohnung_id"], start, end, skip=bid)),
                                     "statisch" if is_static else "zufall")
                    changed = True
                elif (it["von"], it["bis"]) != (start.isoformat(), end.isoformat()) and it.get("status") != "geloescht":
                    it.update({"von": start.isoformat(), "bis": end.isoformat()})
                    changed = True
                if it.get("status") != "geloescht" and self.opts.get(CONF_DOOR_CODE_NOTE, True):
                    line = note_line(it["code"], start, end) if it.get("code") else None  # v1.20.0: ohne Code keine Zeile
                    want = merge_note(r.get("notiz"), line)
                    if (r.get("notiz") or "").strip() != want.strip():
                        await self._write_note(r, line)
            # Schloss: setzen kurz vor Beginn, löschen nach Ende
            for bid, it in self.codes.items():
                if it.get("status") in ("geloescht", "abgelaufen"):
                    continue
                von, bis = datetime.fromisoformat(it["von"]), datetime.fromisoformat(it["bis"])
                if it.get("status") == "fehlt":  # v1.20.0: kein Code → nichts ins Schloss; nach Ende abgelaufen
                    if now >= bis:
                        it["status"] = "abgelaufen"
                        changed = True
                    continue
                if now >= bis:
                    await self._clear_lock(it)
                    it["status"] = "abgelaufen"
                    changed = True
                elif now >= von - SET_LEAD and it.get("status") in ("geplant", "fehler"):
                    await self._set_lock(it)
                    changed = True
            # alte Einträge aufräumen
            cutoff = (now - timedelta(days=KEEP_DAYS)).isoformat()
            for bid in [b for b, it in self.codes.items() if it["bis"] < cutoff]:
                self.codes.pop(bid)
                changed = True
            changed |= await self._static_checks(now)
            if changed:
                await self._save()
                self.c.async_update_listeners()

    # --- Statischer Code: Nachrücken, fehlende Codes, Erinnerung (v1.20.0) -----------------
    def _rollover(self, today: str) -> bool:
        """Nächsten Code in den aktuellen nachrücken lassen – Optionen ohne Neuladen umschreiben."""
        locks = dict(self.opts.get(CONF_DOOR_LOCKS) or {})
        new = {apt: static_rollover(cfg, today) for apt, cfg in locks.items() if isinstance(cfg, dict) and cfg.get("modus") == "statisch"}
        new = {apt: cfg for apt, cfg in new.items() if cfg}
        if not new:
            return False
        from . import SKIP_RELOAD  # noqa: PLC0415  (Kreisimport vermeiden)

        entry = self.c.config_entry
        self.hass.data.setdefault(SKIP_RELOAD, set()).add(entry.entry_id)
        self.hass.config_entries.async_update_entry(entry, options={**entry.options, CONF_DOOR_LOCKS: {**locks, **new}})
        _LOGGER.info("Smoobu: nächster statischer Türcode ist jetzt aktuell (Wohnungen %s)", list(new))
        return True

    def hints(self) -> list[dict[str, Any]]:
        """Aufgaben „Wartet auf dich“: Buchungen ohne gültigen statischen Code, Code läuft bald ab ohne nächsten."""
        if not self.enabled:
            return []
        today = dt_util.now().date()
        lead = int(self.opts.get(CONF_DOOR_CODE_REMIND, DEFAULT_REMIND_DAYS))
        out: list[dict[str, Any]] = []
        for it in self.codes.values():
            if it.get("status") == "fehlt":
                out.append({"art": "code_fehlt", "buchung_id": it["buchung_id"], "wohnung_id": it["wohnung_id"],
                            "anreise": it["von"][:10], "key": f"tuercode:fehlt:{it['buchung_id']}"})
        for apt, cfg in (self.opts.get(CONF_DOOR_LOCKS) or {}).items():
            if not isinstance(cfg, dict) or cfg.get("modus") != "statisch" or cfg.get("naechster_code") or not cfg.get("bis"):
                continue
            if lead and today.isoformat() >= (date.fromisoformat(cfg["bis"]) - timedelta(days=lead)).isoformat():
                out.append({"art": "code_laeuft_ab", "wohnung_id": int(apt) if str(apt).isdigit() else apt, "bis": cfg["bis"],
                            "key": f"tuercode:ablauf:{apt}:{cfg['bis']}"})
        out.sort(key=lambda x: x.get("anreise") or x.get("bis") or "")
        return out

    async def _static_checks(self, now: datetime) -> bool:
        """Nachrücken und je Hinweis einmal Push (Push-Art „tuercode“). Rückgabe: gespeicherte Daten geändert."""
        changed = self._rollover(now.date().isoformat())
        notifier = getattr(self.c, "notifier", None)
        hints = self.hints()
        sent = self.pushed
        live = {h["key"] for h in hints}
        for h in hints:
            if h["key"] in sent:
                continue
            sent.append(h["key"])
            changed = True
            if notifier is None:
                continue
            if h["art"] == "code_fehlt":
                rec = next((r for r in self.c.records_all() if r["id"] == h["buchung_id"]), {})
                text = (f"Für {rec.get('vorname') or 'die Buchung'} (Anreise {date.fromisoformat(h['anreise']).strftime('%d.%m.')}) "
                        "gilt kein Türcode – bitte in den Einstellungen den nächsten Code eintragen.")
            else:
                text = (f"Der Türcode gilt nur bis {date.fromisoformat(h['bis']).strftime('%d.%m.%Y')} – "
                        "bitte den nächsten Code in den Einstellungen eintragen.")
            await notifier.send("tuercode", "🔑 Türcode", text, {"tag": f"smoobu_{h['key'].replace(':', '_')}"})
        # erledigte Hinweise vergessen (z. B. Code eingetragen) – so kommt ein späterer Fall wieder
        keep = [k for k in sent if k in live]
        if keep != sent:
            self.pushed[:] = keep
            changed = True
        return changed

    async def _swap(self, it: dict[str, Any], code: str | None, art: str) -> None:
        """Code einer laufenden/künftigen Buchung tauschen: alten aus dem Schloss, neuer wird im
        nächsten Schritt von async_sync gesetzt (Status zurück auf „geplant“; ohne Code „fehlt“)."""
        await self._clear_lock(it)
        it.update({"code": code, "art": art, "status": "geplant" if code else "fehlt", "slot": None, "fehler": None})

    def static_mode(self, apt: Any) -> bool:
        """v1.20.0: Wohnung im Modus „statisch“ (unabhängig davon, ob gerade ein Code gilt)."""
        return self._lock_cfg(apt).get("modus") == "statisch"

    def static_code(self, apt: Any, day: str | None = None) -> str | None:
        """Statischer Code der Wohnung am Tag `day` (Standard heute), sonst None (kein statischer Modus / keiner gültig)."""
        cfg = self._lock_cfg(apt)
        if cfg.get("modus") != "statisch":
            return None
        code = static_for(cfg, day or dt_util.now().date().isoformat())
        return code if code and STATIC_RE.fullmatch(code) else None

    def known_codes(self) -> set[str]:
        """Alle Codes, die nie an die KI dürfen: je Buchung plus statische aus den Optionen."""
        out = {it["code"] for it in self.codes.values() if it.get("code")}
        for cfg in (self.opts.get(CONF_DOOR_LOCKS) or {}).values():
            if isinstance(cfg, dict) and cfg.get("modus") == "statisch":
                out |= {str(cfg[k]) for k in ("code", "naechster_code") if cfg.get(k)}  # v1.20.0: auch der nächste
        return out

    async def renew(self, booking_id: int) -> dict[str, Any]:
        """Neuen Code für eine Buchung (alten im Schloss löschen, neuen setzen falls schon aktiv)."""
        async with self._lock:
            r = next((x for x in self.c.records_all() if x["id"] == booking_id and not x.get("blockiert")), None)
            if r is None:
                raise ValueError("not_found")
            if self.static_mode(r["wohnung_id"]):
                raise ValueError("statisch")  # statischer Code: in den Einstellungen ändern
            start, end = self._window(r)
            old = self.codes.get(str(booking_id))
            if old:
                await self._clear_lock(old)
            code = new_code(int(self.opts.get(CONF_DOOR_CODE_DIGITS, DEFAULT_DIGITS)),
                            self._taken(r["wohnung_id"], start, end, skip=str(booking_id)) | ({old["code"]} if old else set()))
            it = self.codes[str(booking_id)] = {"buchung_id": booking_id, "wohnung_id": r["wohnung_id"], "code": code, "art": "zufall",
                                                "von": start.isoformat(), "bis": end.isoformat(), "status": "geplant",
                                                "erstellt": dt_util.now().isoformat(timespec="seconds"), "slot": None, "fehler": None}
            self.recent.setdefault(str(r["wohnung_id"]), []).append(code)
            if dt_util.now() >= start - SET_LEAD:
                await self._set_lock(it)
            if self.opts.get(CONF_DOOR_CODE_NOTE, True):
                await self._write_note(r, note_line(code, start, end))
            await self._save()
        self.c.async_update_listeners()
        return it

    # --- Smoobu-Notiz -----------------------------------------------------
    async def _write_note(self, rec: dict[str, Any], line: str | None) -> None:
        text = merge_note(rec.get("notiz"), line)
        if text.strip() == (rec.get("notiz") or "").strip():
            return
        try:
            await self.c.client.update_reservation(rec["id"], {"notice": text})
            rec["notiz"] = text  # lokal nachziehen, damit der nächste Abgleich nicht erneut schreibt
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Smoobu: Türcode-Notiz für Buchung %s nicht geschrieben: %s", rec["id"], err)

    # --- Schloss ------------------------------------------------------------
    def _lock_cfg(self, apt: Any) -> dict[str, Any]:
        locks = self.opts.get(CONF_DOOR_LOCKS) or {}
        return locks.get(str(apt)) or locks.get(apt) or {"typ": "kein"}

    def _free_slot(self, apt: Any, lock: dict[str, Any]) -> int | None:
        lo, hi = int(lock.get("slot_von") or 1), int(lock.get("slot_bis") or lock.get("slot_von") or 1)
        used = {it.get("slot") for it in self.codes.values() if it.get("wohnung_id") == apt and it.get("status") == "gesetzt"}
        return next((s for s in range(lo, hi + 1) if s not in used), None)

    async def _call(self, calls: list[tuple[str, str, dict[str, Any]]]) -> None:
        for domain, service, data in calls:
            await self.hass.services.async_call(domain, service, data, blocking=True)

    async def _set_lock(self, it: dict[str, Any]) -> None:
        lock = self._lock_cfg(it["wohnung_id"])
        if lock.get("typ", "kein") == "kein":
            it["status"] = "aktiv"  # kein Schloss: Code gilt nur als Information
            return
        slot = it.get("slot") or self._free_slot(it["wohnung_id"], lock)
        if slot is None:
            it.update({"status": "fehler", "fehler": "Kein freier Code-Platz im eingestellten Bereich"})
            return
        try:
            await self._call(lock_calls(lock, "setzen", slot, it["code"], it))
            it.update({"status": "gesetzt", "slot": slot, "fehler": None, "gesetzt_um": dt_util.now().isoformat(timespec="seconds")})
        except Exception as err:  # noqa: BLE001
            it.update({"status": "fehler", "fehler": str(err)})
            self._notify(it, f"Türcode konnte nicht ins Schloss geschrieben werden: {err}")

    async def _clear_lock(self, it: dict[str, Any]) -> None:
        if it.get("status") != "gesetzt" or not it.get("slot"):
            return
        lock = self._lock_cfg(it["wohnung_id"])
        try:
            await self._call(lock_calls(lock, "loeschen", it["slot"], it["code"], it))
            it["slot_frei"] = True
        except Exception as err:  # noqa: BLE001
            it["fehler"] = f"Löschen fehlgeschlagen: {err}"
            self._notify(it, f"Türcode konnte nicht aus dem Schloss gelöscht werden: {err}")

    def _notify(self, it: dict[str, Any], text: str) -> None:
        from homeassistant.components import persistent_notification

        persistent_notification.async_create(self.hass, f"{text} (Buchung {it['buchung_id']})", "Smoobu Türcode",
                                             f"smoobu_tuercode_{it['buchung_id']}")

    # --- Lesen ------------------------------------------------------------
    def for_booking(self, booking_id: Any) -> dict[str, Any] | None:
        it = self.codes.get(str(booking_id))
        return dict(it) if it else None

    def current_next(self, apt: Any) -> dict[str, dict[str, Any] | None]:
        """Code des aktuellen und des nächsten Gastes einer Wohnung (nach Gültigkeit)."""
        now = dt_util.now()
        items = sorted((it for it in self.codes.values() if it.get("wohnung_id") == apt and it.get("status") not in ("geloescht",)),
                       key=lambda x: x["von"])
        cur = next((it for it in items if datetime.fromisoformat(it["von"]) <= now < datetime.fromisoformat(it["bis"])), None)
        nxt = next((it for it in items if datetime.fromisoformat(it["von"]) > now and it is not cur), None)
        return {"aktuell": cur, "naechster": nxt}

    def code_for_send(self, booking_id: Any) -> str | None:
        it = self.codes.get(str(booking_id))
        return it["code"] if it and it.get("status") != "geloescht" and it.get("code") else None

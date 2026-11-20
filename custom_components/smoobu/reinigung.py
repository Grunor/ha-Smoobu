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
`smoobu_reinigung_<entry_id>`. Offene Einträge fallen nach 60 Tagen weg, erledigte bleiben 3 Jahre
für die Statistik (Wunsch Betreiber 20.11.2026: wer hat wann welche Wohnung gereinigt). Beim
Erledigen wird ein Schnappschuss der Reinigung gespeichert (Tag, Wohnung, Gästewechsel, Hund,
Personen, Nächte, Check-out), damit die Statistik auch nach Änderungen/Stornos stimmt.
Die Statistik beginnt mit dem Update auf v1.19.0 – frühere Reinigungen kennt die Integration nicht.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from . import rechte
from .const import DOMAIN

CONF_CLEANING_PHONES = "cleaning_phones"        # {HA-Benutzer-ID: "notify.mobile_app_…"}
CONF_CLEANING_NOTIFY = "cleaning_notify"        # Pushes an/aus (Standard an)
CONF_CLEANING_REMIND_TIME = "cleaning_remind_time"  # Vorabend-Erinnerung, HH:MM
DEFAULT_CLEANING_REMIND_TIME = "18:00"
DAYS_BACK = 7      # erledigte/vergessene der letzten Woche bleiben sichtbar
DAYS_AHEAD = 60
KEEP_DAYS = 60          # offene/zugewiesene Einträge
KEEP_DONE_DAYS = 3 * 366  # erledigte (Statistik)
ACTIONS = ("uebernehmen", "abgeben", "zuweisen", "erledigt", "offen", "dauer")
MAX_MINUTES = 600


class CleaningError(Exception):
    """Aktion nicht erlaubt oder ungültig (Code für die Karte in `code`)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _time(value: Any, fallback: str) -> str:
    return str(value or fallback or "")[:5]


def build(records: list[dict[str, Any]], opts: dict[str, Any], today: date,
          days_back: int = DAYS_BACK, days_ahead: int = DAYS_AHEAD) -> list[dict[str, Any]]:
    """Reinigungen aus den Buchungsdatensätzen (ohne Zuweisung/Status), nach Tag sortiert."""
    start, end = (today - timedelta(days=days_back)).isoformat(), (today + timedelta(days=days_ahead)).isoformat()
    guests = sorted((r for r in records if not r.get("blockiert") and not r.get("storniert")),
                    key=lambda r: (r["anreise"], r["id"]))
    occupied = sorted((r for r in records if not r.get("storniert")), key=lambda r: (r["anreise"], r["id"]))
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
                "personen": None if nxt.get("blockiert") else nxt.get("personen"),
                "hund": bool(nxt.get("hund")),
                "naechte": nxt.get("naechte"),
            },
        })
    out.sort(key=lambda x: (x["datum"], x["check_out"] or "", x["key"]))
    return out


class CleaningBoard:
    """Zuweisungen und Status der Reinigungen eines Kontos (hängt am Coordinator)."""

    def __init__(self, hass: HomeAssistant, coordinator: Any) -> None:
        self.hass = hass
        self.c = coordinator
        self.store: Store = Store(hass, 1, f"{DOMAIN}_reinigung_{coordinator.config_entry.entry_id}")
        self.state: dict[str, dict[str, Any]] | None = None
        self._unsubs: list[Callable[[], None]] = []

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
            cutoff_done = (today - timedelta(days=KEEP_DONE_DAYS)).isoformat()
            for key, v in list(self.state.items()):
                day = key.split(":")[-1]
                if day < (cutoff_done if v.get("status") == "erledigt" else cutoff):
                    self.state.pop(key, None)
        return self.state

    # --- Lesen -----------------------------------------------------------
    async def items(self, apartments: list[Any] | None, user: Any) -> list[dict[str, Any]]:
        """Reinigungen mit Zuweisung/Status, gefiltert nach Wohnungen und den Rechten des Benutzers."""
        state = await self._load()
        opts = self.opts
        rights = rechte.rights_of(user, opts)
        records = [r for r in self.c.records_all() if apartments is None or r["wohnung_id"] in apartments]
        names = await self._user_names()
        out = []
        for item in build(records, opts, dt_util.now().date()):
            s = state.get(item["key"], {})
            item = {**item, "zugewiesen": s.get("zugewiesen"), "zugewiesen_name": names.get(s.get("zugewiesen")),
                    "minuten": s.get("minuten"),
                    "status": s.get("status", "offen"), "erledigt_von": s.get("erledigt_von"), "erledigt_um": s.get("erledigt_um")}
            if "belegung_sehen" not in rights:  # Recht „Reinigung“ ohne Belegung: auch keine Vornamen
                item["vorname"] = None
                if item["naechste"]:
                    item["naechste"] = {**item["naechste"], "vorname": None}
            out.append(item)
        return out

    async def async_stats(self, apartments: list[Any] | None, start: str, end: str, codes: dict[Any, str]) -> dict[str, Any]:
        state = await self._load()
        pending = []
        today = dt_util.now().date()
        for item in build(self.c.records_all(), self.opts, today, days_back=400, days_ahead=0):
            s = state.get(item["key"], {})
            pending.append({**item, "zugewiesen": s.get("zugewiesen"), "status": s.get("status", "offen")})
        o = self.opts
        wages = {str(k): float(v) for k, v in (o.get("cleaning_wages") or {}).items() if v}
        default = float(o.get("cost_cleaning", 17.0))
        return stats(state, pending, start, end, set(apartments) if apartments is not None else None,
                     await self._user_names(), codes, today.isoformat(),
                     wage=lambda uid: wages.get(uid or "", default), minutes=float(o.get("cost_cleaning_minutes", 60)))

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
                        minutes: int | None = None) -> dict[str, Any]:
        """Aktion ausführen (Rechte siehe Modul-Doku). Rückgabe: neuer Zustand der Reinigung."""
        if action not in ACTIONS:
            raise CleaningError("invalid_action")
        opts = self.opts
        rights = rechte.rights_of(user, opts)
        can_assign = "reinigung_zuweisen" in rights
        if "reinigung" not in rights and not can_assign:
            raise CleaningError("unauthorized")
        item = next((x for x in build(self.c.records_all(), opts, dt_util.now().date()) if x["key"] == key), None)
        if item is None:
            raise CleaningError("not_found")
        state = await self._load()
        cur = dict(state.get(key, {}))
        me = getattr(user, "id", None)
        before = cur.get("zugewiesen")
        if action == "uebernehmen":
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
            else:
                for k in ("erledigt_von", "erledigt_von_id", "erledigt_um", "gereinigt_von", "gereinigt_name", "snapshot"):
                    cur.pop(k, None)
        cur["geaendert"] = dt_util.now().isoformat(timespec="seconds")
        state[key] = cur
        await self.store.async_save(state)
        after = cur.get("zugewiesen")
        if after != before:
            if after and after != me:  # sich selbst eintragen braucht keinen Push
                await self._push(after, item, "zugewiesen")
            if before and before != me:
                await self._push(before, item, "entfernt")
        self.c.async_update_listeners()  # Karten laden neu (Datenabo)
        return cur

    # --- Pushes ----------------------------------------------------------
    def _phone(self, user_id: str) -> str | None:
        return (self.opts.get(CONF_CLEANING_PHONES) or {}).get(user_id)

    def _text(self, item: dict[str, Any]) -> str:
        d = date.fromisoformat(item["datum"])
        parts = [f"{_DOW[d.weekday()]} {d.strftime('%d.%m.')} ab {item['check_out']} Uhr"]
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
        if not self.opts.get(CONF_CLEANING_NOTIFY, True):
            return
        phone = self._phone(user_id)
        notifier = getattr(self.c, "notifier", None)
        if not phone or notifier is None:
            return
        title = {"zugewiesen": "🧹 Reinigung für dich", "entfernt": "🧹 Reinigung abgegeben",
                 "erinnerung": "🧹 Morgen Reinigung"}[why]
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
        tomorrow = (dt_util.now().date() + timedelta(days=1)).isoformat()
        for item in build(self.c.records_all(), self.opts, dt_util.now().date(), 0, 2):
            s = state.get(item["key"], {})
            if item["datum"] == tomorrow and s.get("zugewiesen") and s.get("status", "offen") == "offen":
                await self._push(s["zugewiesen"], item, "erinnerung")


_DOW = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _delay_minutes(snap: dict[str, Any], done: str | None) -> int | None:
    """Minuten vom Check-out bis zum Abhaken (negativ = vorher abgehakt; None = unbekannt/anderer Tag > 2 Tage)."""
    try:
        co = datetime.fromisoformat(f"{snap['datum']}T{snap.get('check_out') or '11:00'}")
        d = datetime.fromisoformat(done or "")
    except (TypeError, ValueError, KeyError):
        return None
    minutes = int((d.replace(tzinfo=None) - co).total_seconds() // 60)
    return minutes if abs(minutes) <= 2 * 24 * 60 else None


def stats(state: dict[str, dict[str, Any]], pending: list[dict[str, Any]], start: str, end: str,
          apartments: set[Any] | None, names: dict[str, str], codes: dict[Any, str], today: str,
          wage: Callable[[str | None], float] | None = None, minutes: float = 60.0) -> dict[str, Any]:
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
        done.append({**snap, "key": key, "person_id": who,
                     "person": names.get(who) or v.get("gereinigt_name") or v.get("erledigt_von") or "?",
                     "erledigt_um": v.get("erledigt_um"), "abgehakt_von": v.get("erledigt_von"),
                     "verzug_min": _delay_minutes(snap, v.get("erledigt_um")),
                     "minuten": v.get("minuten") or minutes, "minuten_gebucht": v.get("minuten") is not None,
                     "kosten": round((wage(who) if wage else 0.0) * (v.get("minuten") or minutes) / 60, 2),
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

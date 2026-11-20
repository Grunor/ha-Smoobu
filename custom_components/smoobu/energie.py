"""Stromkosten aus Messwerten (ab v1.19.0, Wunsch Betreiber 20.11.2026).

Zwei Wege, umschaltbar in den Einstellungen (Option `cost_power_source`):
- „konstant“ (Standard, Verhalten bis v1.18): feste kWh je Nacht × Mischpreis aus festem
  Netzpreis, PV-Wert und 12 festen Monatswerten für den Netzanteil (deckungsbeitrag.py).
- „zaehler“: echter Verbrauch je Buchung aus der stündlichen HA-Langzeitstatistik eines
  Energiezählers je Wohnung (Option `cost_power_entities`), optional mit Strompreis-Entität
  (`cost_price_entity`) und stündlich gemessenem Netzanteil aus dem Energie-Dashboard
  (`cost_grid_share_auto`).

Messlogik „zaehler“ (Entscheidungen Betreiber 20.11.2026):
- Eine Buchung beginnt mit dem Vorheizen: gemessener Vorheizstart aus einer optionalen
  Zeitstempel-Entität (`cost_preheat_entities`, nur soweit der Recorder ihn noch kennt), sonst
  Check-in − `cost_preheat_hours` (Standard 4 h). Ende = Check-out. Stundengenau (Statistik).
- Verbrauch außerhalb aller Buchungen (Leerstand: Frostschutz, Kühlschrank, Router), Option
  `cost_vacancy_mode`: „separat“ (Standard, Entscheidung Betreiber 20.11.2026) = Fixkosten, eigene
  Zeile in Statistik/Einstellungen, nicht im Deckungsbeitrag; „anteilig“ = je Monat nach
  Gästenächten auf die Buchungen verteilt (Monate ohne Gästenacht behalten ihren Leerstand).
- Preis je Stunde = Netzanteil × Netzpreis + (1 − Netzanteil) × Wert PV-Strom (wie bisher).
  Netzanteil je Stunde = Netzbezug ÷ Hausverbrauch (Netzbezug + PV + Speicher-Entladung
  − Einspeisung − Speicher-Ladung); ohne Daten der feste Monatswert.
- Strompreis-Entität: Verlauf aus dem Recorder (Zustände, so weit vorhanden), davor der feste
  Netzpreis. Einheit: „ct/kWh“ → ct, „€/kWh“/„EUR/kWh“ → ×100, ohne Einheit < 5 → €/kWh.
- Buchungen außerhalb des Messzeitraums (vor Zählerstart, Zukunft) bleiben geschätzt
  (konstante Werte); jede Buchung trägt `strom_quelle` = „gemessen“ bzw. „geschätzt“.

Reine Rechenfunktionen (`allocate`, `hour_shares`) ohne HA – testbar; `EnergyData` holt die
Daten aus Recorder und Energie-Dashboard und hält sie im Speicher (inkrementell nachgeladen).
"""

from __future__ import annotations

import logging
from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

CONF_COST_POWER_SOURCE = "cost_power_source"       # "konstant" | "zaehler"
CONF_COST_POWER_ENTITIES = "cost_power_entities"   # {Wohnungs-ID: sensor.… (Energie, kWh/Wh)}
CONF_COST_PRICE_ENTITY = "cost_price_entity"       # input_number/number/sensor (€/kWh oder ct/kWh)
CONF_COST_GRID_SHARE_AUTO = "cost_grid_share_auto"  # Netzanteil stündlich aus dem Energie-Dashboard
CONF_COST_PREHEAT_ENTITIES = "cost_preheat_entities"  # {Wohnungs-ID: sensor.… (Zeitstempel Vorheizstart)}
CONF_COST_PREHEAT_HOURS = "cost_preheat_hours"     # Stunden vor Check-in, wenn kein Vorheizstart bekannt
CONF_COST_VACANCY_MODE = "cost_vacancy_mode"       # Leerstand-Strom: "separat" (Fixkosten) | "anteilig" (auf Buchungen)
DEFAULT_COST_VACANCY_MODE = "separat"
# v1.19.0 (Wunsch Betreiber 20.11.2026): dasselbe für Wasser und Heizung – konstant (Standard) oder aus Zähler
CONF_COST_WATER_SOURCE = "cost_water_source"        # "konstant" | "zaehler"
CONF_COST_WATER_ENTITIES = "cost_water_entities"    # {Wohnungs-ID: sensor.… (Volumen, m³ oder L)}
CONF_COST_WATER_PRICE = "cost_water_price"          # € je m³ Frisch- + Abwasser
CONF_COST_WATER_PRICE_ENTITY = "cost_water_price_entity"
CONF_COST_HEAT_SOURCE = "cost_heat_source"          # "konstant" | "zaehler"
CONF_COST_HEAT_ENTITIES = "cost_heat_entities"      # {Wohnungs-ID: sensor.… (Wärme kWh, Gas m³, Öl L …)}
CONF_COST_HEAT_PRICE = "cost_heat_price"            # € je Einheit des Zählers
CONF_COST_HEAT_PRICE_ENTITY = "cost_heat_price_entity"
CONF_COST_HEAT_INCL_HOT_WATER = "cost_heat_incl_hot_water"  # Zähler misst auch das Warmwasser
DEFAULT_COST_WATER_PRICE = 0.0
DEFAULT_COST_HEAT_PRICE = 0.0
# Art → (Quelle, Zähler, fester Preis, Preis-Entität, Einheiten-Umrechnung für die Statistik)
METER_KINDS: dict[str, tuple[str, str, str, str, dict[str, str] | None]] = {
    "wasser": (CONF_COST_WATER_SOURCE, CONF_COST_WATER_ENTITIES, CONF_COST_WATER_PRICE, CONF_COST_WATER_PRICE_ENTITY, {"volume": "m³"}),
    "heizung": (CONF_COST_HEAT_SOURCE, CONF_COST_HEAT_ENTITIES, CONF_COST_HEAT_PRICE, CONF_COST_HEAT_PRICE_ENTITY, None),
}
VACANCY_MODES = ("separat", "anteilig")
DEFAULT_COST_POWER_SOURCE = "konstant"
DEFAULT_COST_PREHEAT_HOURS = 4
POWER_SOURCES = ("konstant", "zaehler")
HOUR = 3600


# ---------------------------------------------------------------------------
# Reine Rechenlogik
# ---------------------------------------------------------------------------
def price_ct(value: Any, unit: str | None) -> float | None:
    """Strompreis in ct/kWh aus Zustand + Einheit (None = unbrauchbar)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    u = (unit or "").casefold()
    if "ct" in u or "cent" in u:
        return v
    if "€" in u or "eur" in u:
        return v * 100
    return v * 100 if v < 5 else v


def unit_price_ct(value: Any, unit: str | None) -> float | None:
    """Preis je Einheit (Wasser/Heizung) in ct: „ct/…“ → ct, sonst Euro → ×100."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if "ct" in (unit or "").casefold() or "cent" in (unit or "").casefold() else v * 100


def hour_shares(stats: dict[str, dict[int, float]], grid_from: list[str], grid_to: list[str],
                solar: list[str], bat_from: list[str], bat_to: list[str]) -> dict[int, float]:
    """Netzanteil (0–1) je Stunde = Netzbezug ÷ Hausverbrauch. Stunden ohne Hausverbrauch fehlen."""
    hours = set()
    for sid in grid_from:
        hours |= set(stats.get(sid, {}))
    out = {}
    get = lambda ids, h: sum(stats.get(i, {}).get(h, 0.0) or 0.0 for i in ids)  # noqa: E731
    for h in hours:
        imp = max(get(grid_from, h), 0.0)
        house = imp + get(solar, h) + get(bat_from, h) - get(grid_to, h) - get(bat_to, h)
        if house > 0.001:
            out[h] = min(max(imp / house, 0.0), 1.0)
    return out


@dataclass
class Prices:
    """Preis je Stunde: Netzanteil × Netzpreis + Rest × PV-Wert (ct/kWh)."""

    grid_price: float                 # fester Netzpreis (ct/kWh), auch vor dem ersten Preis-Messwert
    pv_value: float                   # ct/kWh
    month_share: tuple[float, ...]    # 12 feste Monatswerte in %
    shares: dict[int, float] = field(default_factory=dict)  # gemessen je Stunde (0–1)
    price_points: list[tuple[int, float]] = field(default_factory=list)  # (ts, ct) aufsteigend

    def grid(self, ts: int) -> float:
        if not self.price_points:
            return self.grid_price
        i = bisect_right([p[0] for p in self.price_points], ts) - 1
        return self.price_points[i][1] if i >= 0 else self.grid_price

    def share(self, ts: int, month: int) -> float:
        s = self.shares.get(ts)
        return s if s is not None else max(min(float(self.month_share[month - 1]), 100.0), 0.0) / 100

    def mixed(self, ts: int, month: int) -> float:
        s = self.share(ts, month)
        return s * self.grid(ts) + (1 - s) * self.pv_value


def _local(d: date, t: time) -> int:
    return int(dt_util.as_utc(datetime.combine(d, t, tzinfo=dt_util.get_default_time_zone())).timestamp())


def _parse_time(value: Any, fallback: time) -> time:
    try:
        hh, mm = str(value)[:5].split(":")
        return time(int(hh), int(mm))
    except (TypeError, ValueError):
        return fallback


def allocate(records: list[dict[str, Any]], hourly: dict[int, float], prices: Prices, checkin: time,
             checkout: time, preheat_hours: float, preheat: dict[Any, int] | None = None,
             distribute_vacancy: bool = False) -> dict[str, Any]:
    """Stromverbrauch und -kosten je Buchung (Aufenthalt + anteiliger Leerstand) und je Monat.

    hourly: {Stundenbeginn (Unix-s, UTC): kWh}. preheat: {Buchungs-ID: Vorheizstart (Unix-s)}.
    Ergebnis: {"buchungen": {id: {...}}, "monate": {"YYYY-MM": {...}}, "von": ts, "bis": ts}.
    """
    out: dict[str, Any] = {"buchungen": {}, "monate": {}, "von": None, "bis": None}
    if not hourly:
        return out
    first, last = min(hourly), max(hourly) + HOUR
    out["von"], out["bis"] = first, last
    tz = dt_util.get_default_time_zone()
    month_of = lambda ts: datetime.fromtimestamp(ts, tz).strftime("%Y-%m")  # noqa: E731
    guests = sorted((r for r in records if not r.get("blockiert") and not r.get("storniert") and r.get("naechte")),
                    key=lambda r: (r["anreise"], r["id"]))
    in_stay: set[int] = set()
    stays: dict[Any, dict[str, Any]] = {}
    for r in guests:
        arr, dep = date.fromisoformat(r["anreise"]), date.fromisoformat(r["abreise"])
        ci = _local(arr, _parse_time(r.get("check_in"), checkin))
        co = _local(dep, _parse_time(r.get("check_out"), checkout))
        start = (preheat or {}).get(r["id"])
        if not start or not (ci - 12 * HOUR <= start <= ci):
            start = ci - int(preheat_hours * HOUR)
        h0, h1 = start - start % HOUR, co + (-co % HOUR)
        if h0 < first or h1 > last:
            continue  # nicht vollständig gemessen → bleibt geschätzt
        kwh = cost = 0.0
        for h in range(h0, h1, HOUR):
            if h in in_stay:
                continue  # Stunde gehört schon zum Vorgänger (Gästewechsel) – nicht doppelt zählen
            in_stay.add(h)
            k = hourly.get(h, 0.0) or 0.0
            m = int(month_of(h)[5:])
            kwh += k
            cost += k * prices.mixed(h, m) / 100
        stays[r["id"]] = {"kwh": kwh, "kosten": cost, "nights": [arr + timedelta(days=i) for i in range(r["naechte"])],
                          "von": h0, "bis": h1}
    # Leerstand je Monat (gemessene Stunden außerhalb aller Aufenthalte)
    months: dict[str, dict[str, float]] = {}
    for h, k in hourly.items():
        mk = month_of(h)
        mo = months.setdefault(mk, {"kwh": 0.0, "kwh_aufenthalt": 0.0, "kwh_leerstand": 0.0, "kosten": 0.0,
                                    "kosten_leerstand": 0.0, "netz_kwh": 0.0, "naechte": 0, "stunden": 0})
        k = k or 0.0
        c = k * prices.mixed(h, int(mk[5:])) / 100
        mo["kwh"] += k
        mo["kosten"] += c
        mo["netz_kwh"] += k * prices.share(h, int(mk[5:]))
        mo["stunden"] += 1
        if h in in_stay:
            mo["kwh_aufenthalt"] += k
        else:
            mo["kwh_leerstand"] += k
            mo["kosten_leerstand"] += c
    for s in stays.values():
        for n in s["nights"]:
            if n.strftime("%Y-%m") in months:
                months[n.strftime("%Y-%m")]["naechte"] += 1
    for bid, s in stays.items():
        per_night_stay = s["kosten"] / len(s["nights"])
        nights = []
        vac = 0.0
        for n in s["nights"]:
            mo = months.get(n.strftime("%Y-%m"))
            share = mo["kosten_leerstand"] / mo["naechte"] if distribute_vacancy and mo and mo["naechte"] else 0.0
            vac += share
            nights.append(round(per_night_stay + share, 4))
        out["buchungen"][bid] = {"kwh": round(s["kwh"], 2), "kosten_aufenthalt": round(s["kosten"], 2),
                                 "kosten_leerstand": round(vac, 2), "kosten": round(s["kosten"] + vac, 2),
                                 "naechte_kosten": nights}
    for mk, mo in months.items():
        out["monate"][mk] = {
            "kwh": round(mo["kwh"], 2), "kwh_aufenthalt": round(mo["kwh_aufenthalt"], 2),
            "kwh_leerstand": round(mo["kwh_leerstand"], 2), "kosten": round(mo["kosten"], 2),
            "kosten_leerstand": round(mo["kosten_leerstand"], 2),
            "leerstand_verteilt": bool(distribute_vacancy and mo["naechte"]), "naechte": mo["naechte"],
            "netzanteil_prozent": round(mo["netz_kwh"] / mo["kwh"] * 100, 1) if mo["kwh"] else None,
            "vollstaendig": mo["stunden"] >= 24 * 27,
        }
    return out


# ---------------------------------------------------------------------------
# Daten aus Home Assistant (Recorder-Statistik, Energie-Dashboard, Zustandsverlauf)
# ---------------------------------------------------------------------------
class EnergyData:
    """Stundenwerte je Statistik im Speicher; bei jedem Abruf nur die neuen Stunden nachladen."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.hourly: dict[str, dict[int, float]] = {}  # statistic_id → {ts: kWh}
        self.fetched_until: dict[str, int] = {}
        self.error: str | None = None

    async def energy_sources(self) -> dict[str, list[str]]:
        """Statistik-IDs aus dem Energie-Dashboard (Netz, PV, Speicher)."""
        try:
            from homeassistant.components.energy.data import async_get_manager

            manager = await async_get_manager(self.hass)
            prefs = manager.data or {}
        except Exception:  # noqa: BLE001  (Energie-Integration nicht geladen)
            return {}
        out: dict[str, list[str]] = {"grid_from": [], "grid_to": [], "solar": [], "bat_from": [], "bat_to": []}
        for src in prefs.get("energy_sources", []):
            t = src.get("type")
            if t == "grid":
                for f in src.get("flow_from", []) or []:  # ältere Struktur
                    out["grid_from"].append(f.get("stat_energy_from"))
                for f in src.get("flow_to", []) or []:
                    out["grid_to"].append(f.get("stat_energy_to"))
                if src.get("stat_energy_from"):
                    out["grid_from"].append(src["stat_energy_from"])
                if src.get("stat_energy_to"):
                    out["grid_to"].append(src["stat_energy_to"])
            elif t == "solar" and src.get("stat_energy_from"):
                out["solar"].append(src["stat_energy_from"])
            elif t == "battery":
                if src.get("stat_energy_from"):
                    out["bat_from"].append(src["stat_energy_from"])
                if src.get("stat_energy_to"):
                    out["bat_to"].append(src["stat_energy_to"])
        return {k: [x for x in v if x] for k, v in out.items()}

    async def load(self, statistic_ids: list[str], since: datetime, units: dict[str, str] | None = None) -> None:
        """Stündliche Änderungen (kWh) laden – erstmals ab `since`, danach ab der letzten Stunde."""
        try:
            from homeassistant.components.recorder import get_instance
            from homeassistant.components.recorder.statistics import statistics_during_period
        except ImportError:
            self.error = "recorder"
            return
        now = dt_util.utcnow()
        todo: dict[int, set[str]] = {}
        for sid in statistic_ids:
            start = self.fetched_until.get(sid)
            start_ts = (start - 2 * HOUR) if start else int(since.timestamp())
            todo.setdefault(start_ts, set()).add(sid)
        try:
            instance = get_instance(self.hass)
        except (KeyError, RuntimeError):
            self.error = "recorder"
            return
        for start_ts, ids in todo.items():
            start_dt = datetime.fromtimestamp(start_ts, dt_util.UTC)
            try:
                rows = await instance.async_add_executor_job(
                    statistics_during_period, self.hass, start_dt, now, ids, "hour", units or {"energy": "kWh"}, {"change"})
            except Exception as err:  # noqa: BLE001
                self.error = str(err)
                _LOGGER.warning("Smoobu: Energiestatistik nicht lesbar: %s", err)
                return
            for sid in ids:
                dst = self.hourly.setdefault(sid, {})
                for row in rows.get(sid, []):
                    ts = int(row["start"] if isinstance(row["start"], (int, float)) else row["start"].timestamp())
                    if row.get("change") is not None:
                        dst[ts] = float(row["change"])
                self.fetched_until[sid] = max(dst) + HOUR if dst else start_ts
        self.error = None

    async def unit(self, statistic_id: str) -> str | None:
        """Einheit einer Statistik (Recorder-Metadaten), z. B. „kWh“, „m³“, „L“."""
        try:
            from homeassistant.components.recorder import get_instance
            from homeassistant.components.recorder.statistics import get_metadata

            meta = await get_instance(self.hass).async_add_executor_job(
                lambda: get_metadata(self.hass, statistic_ids={statistic_id}))
            return (meta.get(statistic_id) or (None, {}))[1].get("unit_of_measurement")
        except Exception:  # noqa: BLE001
            return None

    async def states(self, entity_id: str, since: datetime) -> list[tuple[int, Any, dict[str, Any]]]:
        """Zustandsverlauf (so weit der Recorder ihn hält): [(ts, Zustand, Attribute)]."""
        try:
            from homeassistant.components.recorder import get_instance
            from homeassistant.components.recorder.history import get_significant_states

            instance = get_instance(self.hass)
            res = await instance.async_add_executor_job(
                get_significant_states, self.hass, since, None, [entity_id], None, True, False)
        except Exception:  # noqa: BLE001
            res = {}
        out = []
        for st in res.get(entity_id, []):
            if hasattr(st, "state"):
                out.append((int(st.last_changed.timestamp()), st.state, dict(st.attributes)))
        cur = self.hass.states.get(entity_id)
        if cur is not None and (not out or out[-1][1] != cur.state):
            out.append((int(cur.last_changed.timestamp()), cur.state, dict(cur.attributes)))
        return out


async def _preheat(data: EnergyData, options: dict[str, Any], apt: int, records: list, checkin: time) -> dict[Any, int]:
    """Gemessener Vorheizstart je Buchung (Zeitstempel-Entität, so weit der Recorder ihn kennt)."""
    preheat: dict[Any, int] = {}
    ents = options.get(CONF_COST_PREHEAT_ENTITIES) or {}
    pent = ents.get(str(apt)) or ents.get(apt)
    if not pent:
        return preheat
    values = []
    for _ts, val, _a in await data.states(pent, dt_util.utcnow() - timedelta(days=30)):
        parsed = dt_util.parse_datetime(str(val))
        if parsed:
            values.append(int(parsed.timestamp()))
    for r in records:
        if r.get("blockiert") or r.get("storniert"):
            continue
        ci = _local(date.fromisoformat(r["anreise"]), _parse_time(r.get("check_in"), checkin))
        cands = [v for v in values if ci - 12 * HOUR <= v <= ci]
        if cands:
            preheat[r["id"]] = max(cands)
    return preheat


async def measure_all(hass: HomeAssistant, data: EnergyData, options: dict[str, Any], records_by_apt: dict[int, list],
                      cfg: Any, checkin: time, checkout: time) -> dict[int, dict[str, Any]]:
    """Messergebnisse je Wohnung und Art: {Wohnung: {"strom": …, "wasser": …, "heizung": …}} (nur Arten im Modus „zaehler“)."""
    out: dict[int, dict[str, Any]] = {}
    for apt, res in (await measure(hass, data, options, records_by_apt, cfg, checkin, checkout)).items():
        out.setdefault(apt, {})["strom"] = res
    for kind in METER_KINDS:
        for apt, res in (await measure_meter(data, kind, options, records_by_apt, checkin, checkout)).items():
            out.setdefault(apt, {})[kind] = res
    return out


async def measure_meter(data: EnergyData, kind: str, options: dict[str, Any], records_by_apt: dict[int, list],
                        checkin: time, checkout: time) -> dict[int, dict[str, Any]]:
    """Wasser oder Heizung aus Zähler: Menge je Stunde × Preis je Einheit (fest oder aus Entität)."""
    src_key, ent_key, price_key, price_ent_key, units = METER_KINDS[kind]
    if options.get(src_key, "konstant") != "zaehler":
        return {}
    meters = {int(k): v for k, v in (options.get(ent_key) or {}).items() if v and int(k) in records_by_apt}
    if not meters:
        return {}
    since = datetime(2000, 1, 1, tzinfo=dt_util.UTC)
    await data.load(list(meters.values()), since, units)
    points: list[tuple[int, float]] = []
    if pe := options.get(price_ent_key):
        for ts, val, attrs in await data.states(pe, since):
            ct = unit_price_ct(val, attrs.get("unit_of_measurement"))
            if ct is not None and ct > 0:
                points.append((ts, ct))
        points.sort()
    fixed = float(options.get(price_key) or 0) * 100  # € → ct je Einheit
    prices = Prices(fixed, 0.0, tuple([100.0] * 12), {}, points)
    hours = float(options.get(CONF_COST_PREHEAT_HOURS, DEFAULT_COST_PREHEAT_HOURS))
    mode = options.get(CONF_COST_VACANCY_MODE, DEFAULT_COST_VACANCY_MODE)
    out: dict[int, dict[str, Any]] = {}
    for apt, ent in meters.items():
        preheat = await _preheat(data, options, apt, records_by_apt[apt], checkin)
        res = allocate(records_by_apt[apt], data.hourly.get(ent, {}), prices, checkin, checkout, hours, preheat, mode == "anteilig")
        res.update({"leerstand_modus": mode, "entitaet": ent, "preis_entitaet": options.get(price_ent_key) if points else None,
                    "einheit": "m³" if kind == "wasser" else (await data.unit(ent) or ""), "fehler": data.error,
                    "inkl_warmwasser": bool(options.get(CONF_COST_HEAT_INCL_HOT_WATER)) if kind == "heizung" else None})
        out[apt] = res
    return out


async def measure(hass: HomeAssistant, data: EnergyData, options: dict[str, Any], records_by_apt: dict[int, list],
                  cfg: Any, checkin: time, checkout: time) -> dict[int, dict[str, Any]]:
    """Messergebnis je Wohnung für Modus „zaehler“ ({} bei „konstant“ oder ohne Zähler)."""
    if options.get(CONF_COST_POWER_SOURCE, DEFAULT_COST_POWER_SOURCE) != "zaehler":
        return {}
    meters = {int(k): v for k, v in (options.get(CONF_COST_POWER_ENTITIES) or {}).items() if v}
    meters = {a: e for a, e in meters.items() if a in records_by_apt}
    if not meters:
        return {}
    since = datetime(2000, 1, 1, tzinfo=dt_util.UTC)
    sources = await data.energy_sources() if options.get(CONF_COST_GRID_SHARE_AUTO, True) else {}
    share_ids = [i for v in sources.values() for i in v]
    await data.load(list(meters.values()) + share_ids, since)
    shares = hour_shares(data.hourly, sources.get("grid_from", []), sources.get("grid_to", []),
                         sources.get("solar", []), sources.get("bat_from", []), sources.get("bat_to", [])) if sources.get("grid_from") else {}
    points: list[tuple[int, float]] = []
    if pe := options.get(CONF_COST_PRICE_ENTITY):
        for ts, val, attrs in await data.states(pe, since):
            ct = price_ct(val, attrs.get("unit_of_measurement"))
            if ct is not None and 0 < ct < 500:
                points.append((ts, ct))
        points.sort()
    prices = Prices(cfg.grid_price, cfg.pv_value, tuple(cfg.grid_share), shares, points)
    hours = float(options.get(CONF_COST_PREHEAT_HOURS, DEFAULT_COST_PREHEAT_HOURS))
    out: dict[int, dict[str, Any]] = {}
    for apt, ent in meters.items():
        preheat = await _preheat(data, options, apt, records_by_apt[apt], checkin)
        res = allocate(records_by_apt[apt], data.hourly.get(ent, {}), prices, checkin, checkout, hours, preheat,
                       options.get(CONF_COST_VACANCY_MODE, DEFAULT_COST_VACANCY_MODE) == "anteilig")
        res["leerstand_modus"] = options.get(CONF_COST_VACANCY_MODE, DEFAULT_COST_VACANCY_MODE)
        res["entitaet"] = ent
        res["netzanteil_gemessen"] = bool(shares)
        res["preis_entitaet"] = options.get(CONF_COST_PRICE_ENTITY) if points else None
        res["fehler"] = data.error
        res["einheit"] = "kWh"
        out[apt] = res
    return out


def average_kwh_per_night(result: dict[str, Any], today: date, months: int = 12) -> float | None:
    """Ø kWh je Gästenacht der letzten `months` vollständigen Monate inkl. Leerstand (Vorschlag „konstant“)."""
    cutoff = (today.replace(day=1) - timedelta(days=months * 31)).strftime("%Y-%m")
    cur = today.strftime("%Y-%m")
    sel = [m for k, m in result.get("monate", {}).items() if cutoff <= k < cur and m["vollstaendig"]]
    nights = sum(m["naechte"] for m in sel)
    return round(sum(m["kwh"] for m in sel) / nights, 1) if nights else None


def vacancy_costs(result: dict[str, Any], start: date, end: date) -> dict[str, float]:
    """Leerstand-Strom im Zeitraum [start, end) – Monate anteilig nach Tagen (für Statistik/Finanzen)."""
    from calendar import monthrange

    kwh = cost = 0.0
    for k, m in result.get("monate", {}).items():
        y, mo = int(k[:4]), int(k[5:])
        first, days = date(y, mo, 1), monthrange(y, mo)[1]
        last = first + timedelta(days=days)
        overlap = (min(end, last) - max(start, first)).days
        if overlap > 0:
            f = overlap / days
            kwh += m["kwh_leerstand"] * f
            cost += m["kosten_leerstand"] * f
    return {"kwh": round(kwh, 1), "kosten": round(cost, 2)}

"""Variable Kosten und Deckungsbeitrag je Buchung (ab v1.18.0).

Reine Python-Logik ohne HA (testbar). Grundlage: Entscheidungen Betreiber 17.11.2026.

Was zählt als variable Kosten?
- Nur Kosten, die durch einen Aufenthalt bzw. eine belegte Nacht ZUSÄTZLICH entstehen:
  je Aufenthalt Reinigung + Wäsche, je Nacht Heizung, Warmwasser, Wasser, Strom.
- Fixkosten (Grundsteuer, Versicherungen, Internet, Streaming …) bleiben draußen – sie
  ändern sich durch eine Buchung nicht. Deckungsbeitrag = Netto − variable Kosten.

Heizung und Warmwasser (Jahreskosten aus der Nebenkostenabrechnung):
- Verteilung auf die Monate nach der Gradtagszahlen-Tabelle (Promille je Monat, wie sie
  die Heizkostenverordnung §9b für Abrechnungen bei Nutzerwechsel vorsieht): Januar 170 ‰
  … Juli 13 ‰. Je Tag gerechnet (Promille ÷ Tage des Monats), damit Februar nicht
  billiger wirkt, nur weil er kürzer ist.
- Skalierung auf die echten Gästenächte des Abrechnungsjahres: Summe über alle Nächte
  des Bezugsjahres (Nächte × Tagesgewicht × k) = Jahreskosten. So stimmt die Summe mit der
  Abrechnung überein, und jede Nacht im Januar kostet rund 12× so viel wie eine im Juli.
- Warmwasser nutzt dieselbe Verteilung: im Sommer deckt die Solarthermie den Großteil,
  im Winter heizt der Kessel nach – die Kurve hat dieselbe Form.
- Alternative verworfen: feste Winter/Sommer-Werte. Zu grob (Oktober ≠ Januar, Wunsch Betreiber).

Strom: kWh je Nacht × Mischpreis des Monats. Mischpreis = Netzanteil × Netzpreis +
(1 − Netzanteil) × Wert des PV-Stroms. PV-Strom ist nicht kostenlos: ohne den Gast wäre er
eingespeist worden → bewertet mit der Einspeisevergütung (wie in der Speicher-Amortisation).
"""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from .const import (
    CONF_COST_CLEANING, CONF_COST_CLEANING_MINUTES, DEFAULT_COST_CLEANING_MINUTES, CONF_COST_GRID_PRICE, CONF_COST_GRID_SHARE, CONF_COST_HEATING_YEAR,
    CONF_COST_HOT_WATER_YEAR, CONF_COST_LAUNDRY, CONF_COST_POWER_KWH, CONF_COST_PV_VALUE,
    CONF_COST_REF_YEAR, CONF_COST_WATER_NIGHT, DEFAULT_COST_CLEANING, DEFAULT_COST_GRID_PRICE,
    DEFAULT_COST_GRID_SHARE, DEFAULT_COST_HEATING_YEAR, DEFAULT_COST_HOT_WATER_YEAR,
    DEFAULT_COST_LAUNDRY, DEFAULT_COST_POWER_KWH, DEFAULT_COST_PV_VALUE, DEFAULT_COST_REF_YEAR,
    DEFAULT_COST_WATER_NIGHT,
)

# Gradtagszahlen in Promille je Monat (Jan … Dez), Summe 1000
HEAT_PROMILLE = (170, 150, 130, 80, 40, 13.33, 13.33, 13.34, 30, 80, 120, 160)

# Standardwerte (Betreiber 17.11.2026, Nebenkostenabrechnung FeWo 2025)
DEFAULT_GRID_SHARE = (72, 55, 15, 11, 7, 10, 5, 26, 20, 47, 67, 80)  # % Netzbezug je Monat, HA-Statistik 2025


@dataclass
class CostConfig:
    """Variable Kosten aus den Optionen (Beträge in €, Preise in ct/kWh, Anteile in %)."""

    cleaning: float = 17.0          # € je Aufenthalt (= Reinigungszeit × Standard-Stundenlohn, v1.19.0)
    laundry: float = 5.0            # je Aufenthalt
    heating_year: float = 473.31    # € Heizung im Bezugsjahr
    hot_water_year: float = 161.53  # € Warmwasser im Bezugsjahr
    ref_year: int = 2025            # Abrechnungsjahr der beiden Jahreswerte
    water_night: float = 0.47       # € Wasser/Abwasser je Nacht
    power_kwh: float = 4.6          # kWh Strom je Nacht
    grid_price: float = 30.54       # ct/kWh Netzstrom
    pv_value: float = 8.2           # ct/kWh PV-Strom (entgangene Einspeisevergütung)
    grid_share: tuple[float, ...] = field(default=DEFAULT_GRID_SHARE)
    cleaning_minutes: float = 60.0  # v1.19.0: Standard-Reinigungszeit (min)
    cleaning_wage: float = 17.0     # v1.19.0: Standard-Stundenlohn (€/h)

    @property
    def per_stay(self) -> float:
        return self.cleaning + self.laundry

    @property
    def active(self) -> bool:
        """Sind überhaupt Kosten hinterlegt? (sonst kein Deckungsbeitrag anzeigen)"""
        return any((self.per_stay, self.heating_year, self.hot_water_year, self.water_night, self.power_kwh))


def config_from_options(options: Any) -> CostConfig:
    """CostConfig aus den Optionen des Eintrags (fehlende Werte = Standard)."""

    o = options or {}
    share = list(o.get(CONF_COST_GRID_SHARE) or DEFAULT_COST_GRID_SHARE)
    if len(share) != 12:
        share = list(DEFAULT_COST_GRID_SHARE)
    return CostConfig(
        # v1.19.0 (Wunsch Betreiber 20.11.2026): Reinigung = Zeit × Stundenlohn. Die alte Option „€ je Aufenthalt“
        # ist jetzt der Standard-Stundenlohn – bei Standardzeit 60 min bleibt der Betrag gleich (17 € = 17 €/h × 1 h).
        cleaning=float(o.get(CONF_COST_CLEANING, DEFAULT_COST_CLEANING)) * float(o.get(CONF_COST_CLEANING_MINUTES, DEFAULT_COST_CLEANING_MINUTES)) / 60,
        cleaning_minutes=float(o.get(CONF_COST_CLEANING_MINUTES, DEFAULT_COST_CLEANING_MINUTES)),
        cleaning_wage=float(o.get(CONF_COST_CLEANING, DEFAULT_COST_CLEANING)),
        laundry=float(o.get(CONF_COST_LAUNDRY, DEFAULT_COST_LAUNDRY)),
        heating_year=float(o.get(CONF_COST_HEATING_YEAR, DEFAULT_COST_HEATING_YEAR)),
        hot_water_year=float(o.get(CONF_COST_HOT_WATER_YEAR, DEFAULT_COST_HOT_WATER_YEAR)),
        ref_year=int(o.get(CONF_COST_REF_YEAR, DEFAULT_COST_REF_YEAR)),
        water_night=float(o.get(CONF_COST_WATER_NIGHT, DEFAULT_COST_WATER_NIGHT)),
        power_kwh=float(o.get(CONF_COST_POWER_KWH, DEFAULT_COST_POWER_KWH)),
        grid_price=float(o.get(CONF_COST_GRID_PRICE, DEFAULT_COST_GRID_PRICE)),
        pv_value=float(o.get(CONF_COST_PV_VALUE, DEFAULT_COST_PV_VALUE)),
        grid_share=tuple(float(x) for x in share),
    )


def parse_grid_share(value: Any) -> list[float]:
    """Netzanteil je Monat: Liste oder Text „72, 55, …“ → 12 Werte 0–100 (sonst ValueError)."""
    items = value if isinstance(value, list) else str(value or "").replace(";", ",").split(",")
    out = [float(str(x).strip().replace("%", "").replace(" ", "") or "x") for x in items if str(x).strip()]
    if len(out) != 12 or any(not 0 <= x <= 100 for x in out):
        raise ValueError("12 Werte zwischen 0 und 100 erwartet")
    return [round(x, 1) for x in out]


def parse_markups(value: Any) -> dict[str, float]:
    """Aufschläge je Kanal: dict oder Text „Airbnb=33; Booking.com=45“ → {Kanal: %} (0–300)."""
    if isinstance(value, dict):
        pairs = list(value.items())
    else:
        pairs = []
        for part in filter(None, (p.strip() for p in str(value or "").replace("\n", ";").split(";"))):
            name, sep, pct = part.partition("=")
            if not sep or not name.strip():
                raise ValueError(part)
            pairs.append((name, pct))
    out: dict[str, float] = {}
    for name, pct in pairs:
        number = float(str(pct).strip().replace(",", ".").replace("%", ""))
        if not -50 <= number <= 300:
            raise ValueError(name)
        if str(name).strip():
            out[str(name).strip()] = round(number, 2)
    return out


def _day_weight(month: int, year: int) -> float:
    return HEAT_PROMILLE[month - 1] / monthrange(year, month)[1]


def ref_nights_by_month(records: list[dict[str, Any]], year: int) -> dict[int, int]:
    """Gästenächte je Monat im Bezugsjahr (ohne Stornos und Sperrzeiten)."""
    out = {m: 0 for m in range(1, 13)}
    start, end = date(year, 1, 1), date(year + 1, 1, 1)
    for r in records:
        if r["blockiert"] or r["storniert"] or not r["naechte"]:
            continue
        day = max(date.fromisoformat(r["anreise"]), start)
        last = min(date.fromisoformat(r["abreise"]), end)
        while day < last:
            out[day.month] += 1
            day += timedelta(days=1)
    return out


def heat_factor(year_cost: float, nights: dict[int, int], year: int) -> float:
    """k so, dass Σ Nächte × Tagesgewicht × k = Jahreskosten.

    Ohne Gästenächte im Bezugsjahr: Verteilung über alle Kalendertage (Rückfall, damit
    die Kosten nicht verschwinden).
    """
    weighted = sum(nights.get(m, 0) * _day_weight(m, year) for m in range(1, 13))
    if weighted <= 0:
        weighted = sum(HEAT_PROMILLE)  # = Σ Tage × Promille/Tage
    return year_cost / weighted if weighted else 0.0


@dataclass
class CostTable:
    """Kosten je Nacht und Monat (1–12) – einmal je Wohnung berechnet."""

    cfg: CostConfig
    heat_k: float
    water_k: float

    def night(self, day: date) -> dict[str, float]:
        """Variable Kosten einer belegten Nacht (ohne Anteil Reinigung/Wäsche)."""
        m = day.month
        w = _day_weight(m, day.year)
        share = max(min(float(self.cfg.grid_share[m - 1]), 100.0), 0.0) / 100
        price = share * self.cfg.grid_price + (1 - share) * self.cfg.pv_value  # ct/kWh
        parts = {
            "heizung": self.heat_k * w,
            "warmwasser": self.water_k * w,
            "wasser": self.cfg.water_night,
            "strom": self.cfg.power_kwh * price / 100,
        }
        parts["summe"] = sum(parts.values())
        return parts

    def month(self, month: int, year: int) -> dict[str, float]:
        """Kosten je Nacht in einem Monat (Mitte des Monats als Stichtag) – für Anzeige/Tabelle."""
        return {k: round(v, 2) for k, v in self.night(date(year, month, 15)).items()}

    def stay(self, arrival: date, nights: int) -> float:
        """Variable Kosten eines Aufenthalts (Reinigung + Wäsche + alle Nächte)."""
        if nights <= 0:
            return 0.0
        return self.cfg.per_stay + sum(self.night(arrival + timedelta(days=i))["summe"] for i in range(nights))


def build_table(records: list[dict[str, Any]], cfg: CostConfig) -> CostTable:
    nights = ref_nights_by_month(records, cfg.ref_year)
    return CostTable(cfg, heat_factor(cfg.heating_year, nights, cfg.ref_year),
                     heat_factor(cfg.hot_water_year, nights, cfg.ref_year))


def apply(records: list[dict[str, Any]], table: CostTable, measured: dict[str, Any] | None = None,
          cleaning: dict[Any, float] | None = None) -> None:
    """Je Gästebuchung variable Kosten und Deckungsbeitrag ergänzen (in place).

    `var_naechte` = Kosten je Nacht inkl. anteiliger Reinigung/Wäsche (Aufenthaltskosten
    gleichmäßig auf die Nächte verteilt) – die Statistik verbucht so je Nacht wie beim Umsatz.
    v1.19.0: `measured` = gemessene Kosten je Art aus energie.measure_all einer Wohnung
    ({"strom": {"buchungen": …}, "wasser": …, "heizung": …}). Gemessene Arten ersetzen den
    geschätzten Anteil je Nacht; misst der Heizungszähler auch das Warmwasser, entfällt dessen
    Schätzung. Je Buchung `strom_quelle`, `wasser_quelle`, `heizung_quelle` = gemessen/geschätzt.
    Rückwärtskompatibel: ein flaches {Buchungs-ID: …} gilt als Strom.
    v1.19.0: `cleaning` = Reinigungskosten je Buchung (Stundenlohn der Person aus dem Reinigungsboard);
    ohne Eintrag gilt der Standard (Reinigungszeit × Standard-Stundenlohn).
    """
    if measured and not set(measured) <= {"strom", "wasser", "heizung"}:
        measured = {"strom": {"buchungen": measured}}
    kinds = {k: ((measured or {}).get(k) or {}) for k in ("strom", "wasser", "heizung")}
    hw_in_heat = bool(kinds["heizung"].get("inkl_warmwasser"))
    for r in records:
        if r["blockiert"] or r["storniert"] or not r["naechte"]:
            r["var_kosten"], r["db"], r["var_naechte"] = 0.0, 0.0, []
            continue
        arrival = date.fromisoformat(r["anreise"])
        clean = (cleaning or {}).get(r["id"], table.cfg.cleaning)
        r["reinigung_kosten"] = round(clean, 2)
        stay_part = (clean + table.cfg.laundry) / r["naechte"]
        nights = [dict(table.night(arrival + timedelta(days=i))) for i in range(r["naechte"])]
        for kind in ("strom", "wasser", "heizung"):
            m = (kinds[kind].get("buchungen") or {}).get(r["id"])
            if m and len(m["naechte_kosten"]) == r["naechte"]:
                for n, mk in zip(nights, m["naechte_kosten"]):
                    n[kind] = mk
                    if kind == "heizung" and hw_in_heat:
                        n["warmwasser"] = 0.0
                r[f"{kind}_quelle"] = "gemessen"
                r[f"{kind}_kosten"] = m["kosten"]
                r[f"{kind}_menge"] = m["kwh"]
            else:
                r[f"{kind}_quelle"] = "geschätzt"
                r[f"{kind}_kosten"] = round(sum(n[kind] for n in nights), 2)
        r["strom_kwh"] = r.get("strom_menge") if r["strom_quelle"] == "gemessen" else round(table.cfg.power_kwh * r["naechte"], 2)
        per_night = [round(n["heizung"] + n["warmwasser"] + n["wasser"] + n["strom"] + stay_part, 4) for n in nights]
        r["var_naechte"] = per_night
        r["var_kosten"] = round(sum(per_night), 2)
        r["db"] = round(r["netto"] - r["var_kosten"], 2)

"""Sensoren je Wohnung (Gäste, Termine, Statistik) und fürs Konto (Diagnose).

Alle Werte werden aus dem Coordinator-Datenstand berechnet. Zeitabhängige
Werte (z. B. „aktueller Gast“ wechselt um 16:00) werden zusätzlich jede
Minute neu ausgewertet, damit sie nicht bis zur nächsten API-Abfrage
hinterherhängen. HA schreibt dabei nur echte Änderungen in die Historie.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from . import SmoobuConfigEntry
from .channels import monthly, summarize
from .booking_fields import FIELDS, SCOPES, BookingField, is_enabled
from .const import CONF_CLOUDHOOK_URL, CONF_SMOOBU_WEBHOOK_ID, STATS_DAYS
from .coordinator import SmoobuCoordinator
from .entity import SmoobuEntity
from .sensor_analytics import (
    SELECTION_SENSORS,
    SmoobuForecastSensor,
    SmoobuSelectionSensor,
    channel_entity_adder,
)
from .models import (
    booking_attributes,
    booking_end,
    booking_start,
    first_name,
    guest_count,
    guest_name,
    is_blocked,
    is_yes,
    nights,
    open_amount,
    parse_date,
    days_in_month,
    free_gaps,
    pet_hint,
    price_breakdown,
    stay_overlap_nights,
    window,
)

C = SmoobuCoordinator


# ---------------------------------------------------------------------------
# Hilfsfunktionen für die Beschreibungen
# ---------------------------------------------------------------------------
def _current(c: C, apt: int) -> dict[str, Any] | None:
    return c.current_booking(apt)


def _next(c: C, apt: int) -> dict[str, Any] | None:
    return c.next_booking(apt)


def _attrs(booking: dict[str, Any] | None, c: C) -> dict[str, Any]:
    return booking_attributes(booking, c.default_checkin, c.default_checkout, c.checkout_buffer)


def _next_departure(c: C, apt: int) -> datetime | None:
    """Freigabe (Abreise + Puffer) der laufenden Buchung, sonst der nächsten."""
    booking = _current(c, apt) or _next(c, apt)
    return c.release(booking) if booking else None


def _upcoming_in_window(c: C, apt: int) -> list[dict[str, Any]]:
    """Gästebuchungen mit Anreise in den nächsten STATS_DAYS Tagen."""
    start, end = window(STATS_DAYS)
    result = []
    for b in c.bookings_for(apt):
        arrival = parse_date(b.get("arrival"))
        if not is_blocked(b) and arrival and start <= arrival < end:
            result.append(b)
    return result


def _short(b: dict[str, Any]) -> dict[str, Any]:
    """Kompakte Buchungszeile für Listen-Attribute."""
    return {
        "id": b.get("id"),
        "gast": guest_name(b),
        "anreise": b.get("arrival"),
        "abreise": b.get("departure"),
        "personen": guest_count(b),
        "kanal": (b.get("channel") or {}).get("name"),
        "preis": b.get("price"),
        "bezahlt": is_yes(b.get("price-paid")),
        "hund": pet_hint(b) is not None,
    }


def _occupancy(c: C, apt: int) -> float:
    """Anteil belegter Nächte (inkl. Blockierungen) in den nächsten 30 Tagen."""
    start, end = window(STATS_DAYS)
    booked = sum(stay_overlap_nights(b, start, end) for b in c.bookings_for(apt))
    return round(min(booked, STATS_DAYS) / STATS_DAYS * 100, 1)


def _revenue(c: C, apt: int) -> float:
    return round(sum(float(b.get("price") or 0) for b in _upcoming_in_window(c, apt)), 2)


def _unpaid(c: C, apt: int) -> list[dict[str, Any]]:
    """Laufende/kommende Gästebuchungen mit offenem Betrag.

    Offen = Preis − bezahlte Anzahlung, sofern nicht als bezahlt markiert.
    Portal-Kanäle (Option, Standard Airbnb + Booking.com) zählen nicht,
    weil dort das Portal kassiert und Smoobu trotzdem „unbezahlt“ meldet.
    """
    result = []
    for b in c.bookings_for(apt):
        if is_blocked(b):
            continue
        end = booking_end(b, c.default_checkout)
        if end is None or end < dt_util.now():
            continue
        if open_amount(b, c.payment_excluded_channels) > 0:
            result.append(b)
    return result


def _unpaid_short(c: C, apt: int) -> list[dict[str, Any]]:
    return [
        {**_short(b), "offen": open_amount(b, c.payment_excluded_channels)}
        for b in _unpaid(c, apt)
    ]


def _currency(c: C, apt: int) -> str:
    return (c.data.apartments.get(apt, {}) if c.data else {}).get("currency") or "EUR"


def _price(b: dict[str, Any] | None) -> float | None:
    return round(float(b.get("price")), 2) if b and b.get("price") is not None else None


def _price_attrs(c: C, b: dict[str, Any] | None) -> dict[str, Any]:
    """Preisdetails: Aufschlüsselung, Preis pro Nacht, Zahlungsstand."""
    if not b:
        return {}
    n = nights(b) or 0
    price = float(b.get("price") or 0)
    return {
        "gastname": guest_name(b),
        "kanal": (b.get("channel") or {}).get("name"),
        "anreise": b.get("arrival"),
        "abreise": b.get("departure"),
        "naechte": n,
        "preis_pro_nacht": round(price / n, 2) if n else None,
        "aufschluesselung": price_breakdown(b),
        "anzahlung": b.get("prepayment"),
        "anzahlung_bezahlt": is_yes(b.get("prepayment-paid")),
        "preis_bezahlt": is_yes(b.get("price-paid")),
        "offen": open_amount(b, c.payment_excluded_channels),
        "kurtaxe": b.get("city-tax"),
    }


def _rev(c: C, apt: int, earned: bool = False) -> dict[str, float]:
    if not c.data:
        return {}
    source = c.data.revenue_earned if earned else c.data.revenue
    return source.get(apt, {})


def _month_key(d) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _sum_year(rev: dict[str, float], year: int) -> float:
    return round(sum(v for k, v in rev.items() if k.startswith(f"{year:04d}-")), 2)


def _revenue_month(c: C, apt: int) -> float:
    return round(_rev(c, apt).get(_month_key(dt_util.now()), 0.0), 2)


def _revenue_month_attrs(c: C, apt: int) -> dict[str, Any]:
    now = dt_util.now()
    prev = (now.replace(day=1) - timedelta(days=1))
    last_year = now.replace(year=now.year - 1, day=1)
    current = round(_rev(c, apt).get(_month_key(now), 0.0), 2)
    vormonat = round(_rev(c, apt).get(_month_key(prev), 0.0), 2)
    vorjahr = round(_rev(c, apt).get(_month_key(last_year), 0.0), 2)
    return {
        "monat": _month_key(now),
        "davon_bis_heute": round(_rev(c, apt, True).get(_month_key(now), 0.0), 2),
        "vormonat": vormonat,
        "folgemonat": round(_rev(c, apt).get(_shift_month(_month_key(now), 1), 0.0), 2),
        "vorjahresmonat": vorjahr,
        "veraenderung_vormonat_prozent": _pct_change(current, vormonat),
        "veraenderung_vorjahr_prozent": _pct_change(current, vorjahr),
        "berechnung": "Buchungspreis anteilig nach Nächten, ohne Sperrzeiten/Stornos",
    }


def _shift_month(key: str, months: int) -> str:
    """'2026-11', +1 → '2026-12'; −12 → '2025-11'."""
    year, month = int(key[:4]), int(key[5:7])
    total = year * 12 + (month - 1) + months
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _pct_change(new: float, old: float) -> float | None:
    return round((new - old) / old * 100, 1) if old else None


def _occ(c: C, apt: int, key: str) -> float:
    """Auslastung eines Monats in % (nur Gäste-Nächte)."""
    nights_ = (c.data.guest_nights.get(apt, {}) if c.data else {}).get(key, 0)
    return round(min(nights_, days_in_month(key)) / days_in_month(key) * 100, 1)


def _month_compare(c: C, apt: int, offset: int) -> dict[str, Any]:
    """Vergleichsdaten für Monat (heute + offset) gegen Vorjahresmonat."""
    key = _shift_month(_month_key(dt_util.now()), offset)
    prev_year = _shift_month(key, -12)
    rev = _rev(c, apt)
    value = round(rev.get(key, 0.0), 2)
    last = round(rev.get(prev_year, 0.0), 2)
    return {
        "monat": key,
        "umsatz": value,
        "vorjahresmonat": last,
        "veraenderung_vorjahr_prozent": _pct_change(value, last),
        "auslastung": _occ(c, apt, key),
        "auslastung_vorjahr": _occ(c, apt, prev_year),
        "gaeste_naechte": (c.data.guest_nights.get(apt, {}) if c.data else {}).get(key, 0),
        "gesperrt_naechte": (c.data.blocked_nights.get(apt, {}) if c.data else {}).get(key, 0),
    }


def _occupancy_month_attrs(c: C, apt: int) -> dict[str, Any]:
    now = dt_util.now()
    key = _month_key(now)
    year = now.year
    return {
        "monat": key,
        "vormonat": _occ(c, apt, _shift_month(key, -1)),
        "folgemonat": _occ(c, apt, _shift_month(key, 1)),
        "vorjahresmonat": _occ(c, apt, _shift_month(key, -12)),
        "gaeste_naechte": (c.data.guest_nights.get(apt, {}) if c.data else {}).get(key, 0),
        "gesperrt_naechte": (c.data.blocked_nights.get(apt, {}) if c.data else {}).get(key, 0),
        "monate": {f"{year:04d}-{i:02d}": _occ(c, apt, f"{year:04d}-{i:02d}") for i in range(1, 13)},
        "monate_vorjahr": {f"{year - 1:04d}-{i:02d}": _occ(c, apt, f"{year - 1:04d}-{i:02d}") for i in range(1, 13)},
        "berechnung": "Gäste-Nächte ÷ Tage im Monat, Sperrzeiten zählen nicht",
    }


def _blocked(c: C, apt: int, key: str) -> int:
    """Vom Gastgeber gesperrte Nächte eines Monats."""
    return (c.data.blocked_nights.get(apt, {}) if c.data else {}).get(key, 0)


def _blocked_month_attrs(c: C, apt: int) -> dict[str, Any]:
    now = dt_util.now()
    key = _month_key(now)
    year = now.year
    months = [f"{year:04d}-{i:02d}" for i in range(1, 13)]
    months_prev = [f"{year - 1:04d}-{i:02d}" for i in range(1, 13)]
    return {
        "monat": key,
        "prozent": round(_blocked(c, apt, key) / days_in_month(key) * 100, 1),
        "vormonat": _blocked(c, apt, _shift_month(key, -1)),
        "folgemonat": _blocked(c, apt, _shift_month(key, 1)),
        "vorjahresmonat": _blocked(c, apt, _shift_month(key, -12)),
        "jahr_gesamt": sum(_blocked(c, apt, m) for m in months),
        "vorjahr_gesamt": sum(_blocked(c, apt, m) for m in months_prev),
        "monate": {m: _blocked(c, apt, m) for m in months},
        "monate_vorjahr": {m: _blocked(c, apt, m) for m in months_prev},
        "monate_prozent": {m: round(_blocked(c, apt, m) / days_in_month(m) * 100, 1) for m in months},
        "monate_vorjahr_prozent": {
            m: round(_blocked(c, apt, m) / days_in_month(m) * 100, 1) for m in months_prev
        },
        "berechnung": "Gesperrte Nächte (Blockierungen in Smoobu), getrennt von der Auslastung",
    }


def _revenue_year(c: C, apt: int) -> float:
    return _sum_year(_rev(c, apt), dt_util.now().year)


def _revenue_year_attrs(c: C, apt: int) -> dict[str, Any]:
    now = dt_util.now()
    year = now.year
    rev = _rev(c, apt)
    # Vorjahr bis zum gleichen Tag: Nächte vor (heute − 1 Jahr) – anteilig über den laufenden Monat
    earned = _rev(c, apt, True)
    return {
        "jahr": year,
        "davon_bis_heute": _sum_year(earned, year),
        "gebucht_ab_heute": round(_sum_year(rev, year) - _sum_year(earned, year), 2),
        "vorjahr_gesamt": _sum_year(rev, year - 1),
        "monate": {k: v for k, v in rev.items() if k.startswith(f"{year:04d}-")},
        "monate_vorjahr": {k: v for k, v in rev.items() if k.startswith(f"{year - 1:04d}-")},
        "berechnung": "Buchungspreis anteilig nach Nächten, ohne Sperrzeiten/Stornos",
    }


def _revenue_prev_year(c: C, apt: int) -> float:
    return _sum_year(_rev(c, apt), dt_util.now().year - 1)


def _rates(c: C, apt: int) -> dict[str, dict[str, Any]]:
    return (c.data.rates.get(apt, {}) if c.data else {}) or {}


def _rate_on(c: C, apt: int, offset: int) -> dict[str, Any]:
    day = (dt_util.now().date() + timedelta(days=offset)).isoformat()
    return _rates(c, apt).get(day) or {}


def _rate_price(c: C, apt: int, offset: int) -> float | None:
    price = _rate_on(c, apt, offset).get("price")
    return round(float(price), 2) if price is not None else None


def _is_available(entry: dict[str, Any]) -> bool:
    return str(entry.get("available")) in ("1", "True", "true")


def _next_free_day(c: C, apt: int):
    """Erster Tag ab heute, der laut Smoobu buchbar ist."""
    for day, entry in sorted(_rates(c, apt).items()):
        if day >= dt_util.now().date().isoformat() and _is_available(entry):
            return date_from_iso(day)
    return None


def date_from_iso(value: str) -> date:
    return date.fromisoformat(value)


def _free_nights_30(c: C, apt: int) -> int:
    today = dt_util.now().date()
    days = {(today + timedelta(days=i)).isoformat() for i in range(STATS_DAYS)}
    return sum(1 for d, e in _rates(c, apt).items() if d in days and _is_available(e))


def _gaps(c: C, apt: int) -> list[dict[str, Any]]:
    gaps = free_gaps(c.bookings_for(apt), dt_util.now().date(), 60)
    for gap in gaps:
        entry = _rates(c, apt).get(gap["von"]) or {}
        min_stay = entry.get("min_length_of_stay")
        gap["mindestaufenthalt"] = min_stay
        gap["buchbar"] = min_stay is None or gap["naechte"] >= int(min_stay)
    return gaps


def _next_gap(c: C, apt: int):
    gaps = _gaps(c, apt)
    return date_from_iso(gaps[0]["von"]) if gaps else None


def _next_gap_attrs(c: C, apt: int) -> dict[str, Any]:
    gaps = _gaps(c, apt)
    first = gaps[0] if gaps else {}
    return {
        "bis": first.get("bis"),
        "naechte": first.get("naechte"),
        "mindestaufenthalt": first.get("mindestaufenthalt"),
        "buchbar": first.get("buchbar"),
        "alle_luecken_60_tage": gaps,
        "berechnung": "Freie Nächte zwischen zwei Belegungen (Gäste oder Sperrzeit)",
    }


def _price_today_attrs(c: C, apt: int) -> dict[str, Any]:
    today = _rate_on(c, apt, 0)
    return {
        "mindestaufenthalt": today.get("min_length_of_stay"),
        "verfuegbar": _is_available(today) if today else None,
        "preise_60_tage": {d: e.get("price") for d, e in sorted(_rates(c, apt).items())},
        "mindestaufenthalt_60_tage": {
            d: e.get("min_length_of_stay") for d, e in sorted(_rates(c, apt).items())
        },
    }


# ---------------------------------------------------------------------------
# Direktvermarktung vs. Portale (Basis: channels.night_rows)
# ---------------------------------------------------------------------------
def _rows(c: C, apt: int) -> list:
    return (c.data.night_rows.get(apt, []) if c.data else []) or []


def _year_range(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year + 1, 1, 1)


def _prev_year_day(day: date) -> date:
    """Gleicher Tag im Vorjahr (29.02. → 28.02.)."""
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)


def _ch(c: C, apt: int) -> dict[str, Any]:
    """Jahr, Jahr bis heute, Vorjahr, Vorjahr bis heute – einmal berechnet."""
    today = dt_util.now().date()
    y = today.year
    rows = _rows(c, apt)
    return {
        "jahr": summarize(rows, *_year_range(y)),
        "bis_heute": summarize(rows, date(y, 1, 1), today),
        "vorjahr": summarize(rows, *_year_range(y - 1)),
        "vorjahr_bis_heute": summarize(rows, date(y - 1, 1, 1), _prev_year_day(today)),
    }


def _month_start(key: str) -> date:
    return date(int(key[:4]), int(key[5:7]), 1)


def _ch_month(c: C, apt: int, offset: int = 0, years_back: int = 0) -> dict[str, Any]:
    """Summen eines Monats relativ zum laufenden (offset) bzw. im Vorjahr (years_back)."""
    today = dt_util.now().date()
    key = _shift_month(f"{today.year:04d}-{today.month:02d}", offset - 12 * years_back)
    return summarize(_rows(c, apt), _month_start(key), _month_start(_shift_month(key, 1)))


def _group_attrs(c: C, apt: int, group: str) -> dict[str, Any]:
    """Attribute für Umsatz Direkt/Portale: Netto, Vorjahr, bis heute, Monate."""
    d = _ch(c, apt)
    y = dt_util.now().year
    cur, ytd = d["jahr"][group], d["bis_heute"][group]
    prev, prev_ytd = d["vorjahr"][group], d["vorjahr_bis_heute"][group]
    return {
        "netto": cur["netto"],
        "kosten": cur["kosten"],
        "kostenquote_prozent": cur["kostenquote_prozent"],
        "buchungen": cur["buchungen"],
        "naechte": cur["naechte"],
        "netto_pro_nacht": cur["netto_pro_nacht"],
        "anteil_prozent": (
            round(cur["brutto"] / d["jahr"]["gesamt"]["brutto"] * 100, 1)
            if d["jahr"]["gesamt"]["brutto"] else None
        ),
        "bis_heute": ytd["brutto"],
        "bis_heute_netto": ytd["netto"],
        "vorjahr": prev["brutto"],
        "vorjahr_netto": prev["netto"],
        "vorjahr_bis_heute": prev_ytd["brutto"],
        "vorjahr_bis_heute_netto": prev_ytd["netto"],
        "veraenderung_vorjahr_bis_heute_prozent": _pct_change(ytd["brutto"], prev_ytd["brutto"]),
        "veraenderung_vorjahr_prozent": _pct_change(cur["brutto"], prev["brutto"]),
        "monate": monthly(_rows(c, apt), y, group, "brutto"),
        "monate_vorjahr": monthly(_rows(c, apt), y - 1, group, "brutto"),
        "monate_netto": monthly(_rows(c, apt), y, group, "netto"),
    }


def _savings(stats: dict[str, Any]) -> float | None:
    """Gesparte Kosten der Direktbuchungen, gerechnet mit der Kostenquote der Portale."""
    quote = stats["portale"]["kostenquote_prozent"]
    return round(stats["direkt"]["brutto"] * quote / 100, 2) if quote else None


def _share_attrs(c: C, apt: int) -> dict[str, Any]:
    d = _ch(c, apt)
    cur, prev = d["jahr"], d["vorjahr"]
    ytd, prev_ytd = d["bis_heute"], d["vorjahr_bis_heute"]
    share = cur["direktanteil_prozent"]
    return {
        "anteil_naechte_prozent": cur["direktanteil_naechte_prozent"],
        "bis_heute_prozent": ytd["direktanteil_prozent"],
        "vorjahr_prozent": prev["direktanteil_prozent"],
        "vorjahr_bis_heute_prozent": prev_ytd["direktanteil_prozent"],
        "veraenderung_prozentpunkte": (
            round(share - prev["direktanteil_prozent"], 1)
            if share is not None and prev["direktanteil_prozent"] is not None else None
        ),
        "ersparnis_direkt": _savings(cur),
        "ersparnis_direkt_vorjahr": _savings(prev),
        "kanaele": cur["kanaele"],
        "kanaele_bis_heute": ytd["kanaele"],
        "kanaele_vorjahr": prev["kanaele"],
        "kanaele_vorjahr_bis_heute": prev_ytd["kanaele"],
        "berechnung": "Anteil am Bruttoumsatz (anteilig nach Nächten); Direktkanäle laut Optionen",
    }


def _net_year_attrs(c: C, apt: int) -> dict[str, Any]:
    d = _ch(c, apt)
    y = dt_util.now().year
    cur, ytd = d["jahr"]["gesamt"], d["bis_heute"]["gesamt"]
    prev, prev_ytd = d["vorjahr"]["gesamt"], d["vorjahr_bis_heute"]["gesamt"]
    return {
        "brutto": cur["brutto"],
        "provision": cur["provision"],
        "zahlungsgebuehren": cur["zahlungsgebuehren"],
        "kostenquote_prozent": cur["kostenquote_prozent"],
        "davon_bis_heute": ytd["netto"],
        "vorjahr_gesamt": prev["netto"],
        "vorjahr_bis_heute": prev_ytd["netto"],
        "veraenderung_vorjahr_bis_heute_prozent": _pct_change(ytd["netto"], prev_ytd["netto"]),
        "veraenderung_vorjahr_prozent": _pct_change(cur["netto"], prev["netto"]),
        "monate": monthly(_rows(c, apt), y),
        "monate_vorjahr": monthly(_rows(c, apt), y - 1),
    }


def _net_month_attrs(c: C, apt: int) -> dict[str, Any]:
    cur = _ch_month(c, apt)["gesamt"]
    prev_year = _ch_month(c, apt, years_back=1)["gesamt"]
    return {
        "brutto": cur["brutto"],
        "provision": cur["provision"],
        "zahlungsgebuehren": cur["zahlungsgebuehren"],
        "kostenquote_prozent": cur["kostenquote_prozent"],
        "vormonat": _ch_month(c, apt, -1)["gesamt"]["netto"],
        "folgemonat": _ch_month(c, apt, 1)["gesamt"]["netto"],
        "vorjahresmonat": prev_year["netto"],
        "veraenderung_vorjahr_prozent": _pct_change(cur["netto"], prev_year["netto"]),
        "kanaele": _ch_month(c, apt)["kanaele"],
    }


def _costs_attrs(c: C, apt: int) -> dict[str, Any]:
    d = _ch(c, apt)
    cur, prev = d["jahr"], d["vorjahr"]
    return {
        "provision": cur["gesamt"]["provision"],
        "zahlungsgebuehren": cur["gesamt"]["zahlungsgebuehren"],
        "kostenquote_prozent": cur["gesamt"]["kostenquote_prozent"],
        "bis_heute": d["bis_heute"]["gesamt"]["kosten"],
        "vorjahr": prev["gesamt"]["kosten"],
        "vorjahr_bis_heute": d["vorjahr_bis_heute"]["gesamt"]["kosten"],
        "vorjahr_kostenquote_prozent": prev["gesamt"]["kostenquote_prozent"],
        "je_kanal": {k: v["kosten"] for k, v in cur["kanaele"].items()},
        "je_kanal_vorjahr": {k: v["kosten"] for k, v in prev["kanaele"].items()},
        "provisionen_konfiguration": c.commissions,
        "provision_sonstige_portale": c.commission_other,
        "direktkanaele": c.direct_channels,
    }


def _price_costs(c: C, b: dict[str, Any] | None) -> dict[str, Any]:
    """Kanalgruppe/Provision/Netto für Preis-Sensoren aktueller/nächster Gast."""
    if not b:
        return {}
    costs = c.costs(b)
    costs.pop("brutto", None)
    costs.pop("kanal", None)
    return costs


# ---------------------------------------------------------------------------
# Beschreibungen
# ---------------------------------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class SmoobuSensorDescription(SensorEntityDescription):
    value_fn: Callable[[C, int], Any]
    attrs_fn: Callable[[C, int], dict[str, Any]] | None = None
    time_dependent: bool = True
    # "month"/"year": Umsatz-Sensor, last_reset am Monats-/Jahresanfang
    reset: str | None = None


APARTMENT_SENSORS: tuple[SmoobuSensorDescription, ...] = (
    SmoobuSensorDescription(
        key="aktueller_gast",
        icon="mdi:account",
        value_fn=lambda c, a: guest_name(b) if (b := _current(c, a)) else None,
        attrs_fn=lambda c, a: _attrs(_current(c, a), c),
    ),
    SmoobuSensorDescription(
        key="aktueller_vorname",
        icon="mdi:account-outline",
        value_fn=lambda c, a: first_name(b) or None if (b := _current(c, a)) else None,
    ),
    SmoobuSensorDescription(
        key="aktuelle_personen",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c, a: guest_count(b) if (b := _current(c, a)) else 0,
    ),
    SmoobuSensorDescription(
        key="naechster_gast",
        icon="mdi:account-arrow-right",
        value_fn=lambda c, a: guest_name(b) if (b := _next(c, a)) else None,
        attrs_fn=lambda c, a: _attrs(_next(c, a), c),
    ),
    SmoobuSensorDescription(
        key="naechster_vorname",
        icon="mdi:account-arrow-right-outline",
        value_fn=lambda c, a: first_name(b) or None if (b := _next(c, a)) else None,
    ),
    SmoobuSensorDescription(
        key="naechste_personen",
        icon="mdi:account-group-outline",
        value_fn=lambda c, a: guest_count(b) if (b := _next(c, a)) else None,
    ),
    SmoobuSensorDescription(
        key="naechste_anreise",
        icon="mdi:calendar-arrow-right",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda c, a: booking_start(b, c.default_checkin) if (b := _next(c, a)) else None,
    ),
    SmoobuSensorDescription(
        key="naechste_abreise",
        icon="mdi:calendar-arrow-left",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_next_departure,
    ),
    SmoobuSensorDescription(
        key="buchungen_30_tage",
        icon="mdi:calendar-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c, a: len(_upcoming_in_window(c, a)),
        attrs_fn=lambda c, a: {"buchungen": [_short(b) for b in _upcoming_in_window(c, a)]},
    ),
    SmoobuSensorDescription(
        key="auslastung_30_tage",
        icon="mdi:chart-donut",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_occupancy,
    ),
    SmoobuSensorDescription(
        key="umsatz_30_tage",
        icon="mdi:cash-multiple",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=_revenue,
    ),
    SmoobuSensorDescription(
        key="preis_aktueller_gast",
        icon="mdi:cash",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=lambda c, a: _price(_current(c, a)),
        attrs_fn=lambda c, a: {**_price_attrs(c, _current(c, a)), **_price_costs(c, _current(c, a))},
    ),
    SmoobuSensorDescription(
        key="preis_naechster_gast",
        icon="mdi:cash-fast",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=lambda c, a: _price(_next(c, a)),
        attrs_fn=lambda c, a: {**_price_attrs(c, _next(c, a)), **_price_costs(c, _next(c, a))},
    ),
    SmoobuSensorDescription(
        key="umsatz_monat",
        icon="mdi:calendar-month",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        reset="month",
        value_fn=_revenue_month,
        attrs_fn=_revenue_month_attrs,
    ),
    SmoobuSensorDescription(
        key="umsatz_jahr",
        icon="mdi:calendar-blank-multiple",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        reset="year",
        value_fn=_revenue_year,
        attrs_fn=_revenue_year_attrs,
    ),
    SmoobuSensorDescription(
        key="umsatz_vormonat",
        icon="mdi:calendar-arrow-left",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=lambda c, a: _month_compare(c, a, -1)["umsatz"],
        attrs_fn=lambda c, a: _month_compare(c, a, -1),
    ),
    SmoobuSensorDescription(
        key="umsatz_folgemonat",
        icon="mdi:calendar-arrow-right",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=lambda c, a: _month_compare(c, a, 1)["umsatz"],
        attrs_fn=lambda c, a: _month_compare(c, a, 1),
    ),
    SmoobuSensorDescription(
        key="auslastung_monat",
        icon="mdi:chart-donut-variant",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c, a: _occ(c, a, _month_key(dt_util.now())),
        attrs_fn=_occupancy_month_attrs,
    ),
    SmoobuSensorDescription(
        key="gesperrte_naechte_monat",
        icon="mdi:calendar-lock",
        native_unit_of_measurement="Nächte",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c, a: _blocked(c, a, _month_key(dt_util.now())),
        attrs_fn=_blocked_month_attrs,
    ),
    SmoobuSensorDescription(
        key="netto_umsatz_monat",
        icon="mdi:cash-check",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        reset="month",
        time_dependent=False,
        value_fn=lambda c, a: _ch_month(c, a)["gesamt"]["netto"],
        attrs_fn=_net_month_attrs,
    ),
    SmoobuSensorDescription(
        key="netto_umsatz_jahr",
        icon="mdi:cash-multiple",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        reset="year",
        time_dependent=False,
        value_fn=lambda c, a: _ch(c, a)["jahr"]["gesamt"]["netto"],
        attrs_fn=_net_year_attrs,
    ),
    SmoobuSensorDescription(
        key="provision_jahr",
        icon="mdi:hand-coin",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        time_dependent=False,
        value_fn=lambda c, a: _ch(c, a)["jahr"]["gesamt"]["kosten"],
        attrs_fn=_costs_attrs,
    ),
    SmoobuSensorDescription(
        key="umsatz_direkt_jahr",
        icon="mdi:home-heart",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        time_dependent=False,
        value_fn=lambda c, a: _ch(c, a)["jahr"]["direkt"]["brutto"],
        attrs_fn=lambda c, a: _group_attrs(c, a, "direkt"),
    ),
    SmoobuSensorDescription(
        key="umsatz_portale_jahr",
        icon="mdi:web",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        time_dependent=False,
        value_fn=lambda c, a: _ch(c, a)["jahr"]["portale"]["brutto"],
        attrs_fn=lambda c, a: _group_attrs(c, a, "portale"),
    ),
    SmoobuSensorDescription(
        key="direktanteil_jahr",
        icon="mdi:chart-donut",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        time_dependent=False,
        value_fn=lambda c, a: _ch(c, a)["jahr"]["direktanteil_prozent"],
        attrs_fn=_share_attrs,
    ),
    SmoobuSensorDescription(
        key="preis_heute",
        icon="mdi:tag",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=lambda c, a: _rate_price(c, a, 0),
        attrs_fn=_price_today_attrs,
    ),
    SmoobuSensorDescription(
        key="preis_morgen",
        icon="mdi:tag-arrow-right",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=lambda c, a: _rate_price(c, a, 1),
    ),
    SmoobuSensorDescription(
        key="mindestaufenthalt_heute",
        icon="mdi:calendar-range",
        native_unit_of_measurement="Nächte",
        value_fn=lambda c, a: _rate_on(c, a, 0).get("min_length_of_stay"),
    ),
    SmoobuSensorDescription(
        key="naechster_freier_tag",
        icon="mdi:calendar-check",
        device_class=SensorDeviceClass.DATE,
        value_fn=_next_free_day,
    ),
    SmoobuSensorDescription(
        key="freie_naechte_30_tage",
        icon="mdi:calendar-blank",
        native_unit_of_measurement="Nächte",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_free_nights_30,
    ),
    SmoobuSensorDescription(
        key="naechste_luecke",
        icon="mdi:calendar-expand-horizontal",
        device_class=SensorDeviceClass.DATE,
        value_fn=_next_gap,
        attrs_fn=_next_gap_attrs,
    ),
    SmoobuSensorDescription(
        key="umsatz_vorjahr",
        icon="mdi:calendar-clock",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=_revenue_prev_year,
    ),
    SmoobuSensorDescription(
        key="offene_zahlungen",
        icon="mdi:cash-clock",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c, a: len(_unpaid(c, a)),
        attrs_fn=lambda c, a: {
            "buchungen": _unpaid_short(c, a),
            "offener_betrag": round(sum(x["offen"] for x in _unpaid_short(c, a)), 2),
            "ausgenommene_kanaele": c.payment_excluded_channels,
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmoobuConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        SmoobuApartmentSensor(coordinator, apt_id, desc)
        for apt_id in coordinator.data.apartments
        for desc in APARTMENT_SENSORS
    ]
    entities += [
        SmoobuBookingFieldSensor(coordinator, apt_id, scope, field)
        for apt_id in coordinator.data.apartments
        for scope in SCOPES
        for field in FIELDS
        if not field.binary
    ]
    entities += [
        SmoobuLastMessageSensor(coordinator),
        SmoobuLastUpdateSensor(coordinator),
        SmoobuLastEventSensor(coordinator),
        SmoobuWebhookSensor(coordinator),
    ]
    # v1.7.0: Auswertung nach Auswahl + Prognose je Wohnung
    entities += [
        SmoobuSelectionSensor(coordinator, apt_id, desc, _currency(coordinator, apt_id))
        for apt_id in coordinator.data.apartments
        for desc in SELECTION_SENSORS
    ]
    entities += [
        SmoobuForecastSensor(coordinator, apt_id, _currency(coordinator, apt_id))
        for apt_id in coordinator.data.apartments
    ]
    async_add_entities(entities)
    # Kanal-Sensoren: einer je Kanal, neue Kanäle kommen zur Laufzeit dazu
    entry.async_on_unload(
        channel_entity_adder(
            coordinator, async_add_entities, lambda apt: _currency(coordinator, apt)
        )
    )


class SmoobuApartmentSensor(SmoobuEntity, SensorEntity):
    """Wohnungssensor auf Basis einer Beschreibung."""

    entity_description: SmoobuSensorDescription

    def __init__(self, coordinator: C, apartment_id: int, description: SmoobuSensorDescription) -> None:
        super().__init__(coordinator, apartment_id, description.key)
        self.entity_description = description
        if description.device_class == SensorDeviceClass.MONETARY:
            self._attr_native_unit_of_measurement = _currency(coordinator, apartment_id)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.entity_description.time_dependent:
            # Minütlich neu auswerten (Check-in/Check-out-Grenzen).
            self.async_on_remove(
                async_track_time_interval(self.hass, self._tick, timedelta(minutes=1))
            )

    @callback
    def _tick(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator, self.apartment_id)

    @property
    def last_reset(self) -> datetime | None:
        """Monats-/Jahresanfang für Umsatz-Sensoren (state_class total)."""
        reset = self.entity_description.reset
        if reset is None:
            return None
        start = dt_util.start_of_local_day().replace(day=1)
        return start.replace(month=1) if reset == "year" else start

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator, self.apartment_id)


# ---------------------------------------------------------------------------
# Konto-Sensoren (Diagnose)
# ---------------------------------------------------------------------------
class SmoobuLastUpdateSensor(SmoobuEntity, SensorEntity):
    """Zeitpunkt der letzten erfolgreichen API-Abfrage."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: C) -> None:
        super().__init__(coordinator, None, "letzte_aktualisierung")

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.last_update if self.coordinator.data else None


class SmoobuLastEventSensor(SmoobuEntity, SensorEntity):
    """Letztes per Webhook empfangenes Smoobu-Ereignis (action)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:webhook"

    def __init__(self, coordinator: C) -> None:
        super().__init__(coordinator, None, "letztes_ereignis")

    @property
    def native_value(self) -> str | None:
        event = self.coordinator.data.last_event if self.coordinator.data else None
        return event.get("action") if event else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        event = self.coordinator.data.last_event if self.coordinator.data else None
        if not event:
            return None
        return {
            "empfangen": event.get("received"),
            "buchungs_id": event.get("reservation_id"),
            "gast": event.get("guest_name"),
            "anreise": event.get("arrival"),
            "abreise": event.get("departure"),
        }


class SmoobuWebhookSensor(SmoobuEntity, SensorEntity):
    """Status des Echtzeit-Webhooks (aktiv bei Smoobu registriert / manuell / aus)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:webhook"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["registriert", "manuell", "aus"]

    def __init__(self, coordinator: C) -> None:
        super().__init__(coordinator, None, "webhook")

    @property
    def native_value(self) -> str:
        data = self.coordinator.config_entry.data
        if not data.get(CONF_CLOUDHOOK_URL):
            return "aus"
        return "registriert" if data.get(CONF_SMOOBU_WEBHOOK_ID) else "manuell"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        # URL wird gebraucht, falls sie in Smoobu manuell eingetragen werden muss.
        return {"url": self.coordinator.config_entry.data.get(CONF_CLOUDHOOK_URL)}


# ---------------------------------------------------------------------------
# Einzelne Buchungsfelder (aktueller / nächster Gast)
# ---------------------------------------------------------------------------
class SmoobuBookingFieldSensor(SmoobuEntity, SensorEntity):
    """Ein Feld der laufenden bzw. nächsten Buchung als eigene Entität."""

    def __init__(self, coordinator: C, apartment_id: int, scope: str, field: BookingField) -> None:
        super().__init__(coordinator, apartment_id, f"{scope}_{field.key}")
        self._scope = scope
        self._field = field
        self._attr_icon = field.icon
        self._attr_entity_registry_enabled_default = is_enabled(field, scope)
        if field.monetary:
            self._attr_device_class = SensorDeviceClass.MONETARY
            self._attr_native_unit_of_measurement = _currency(coordinator, apartment_id)
            self._attr_suggested_display_precision = 2
        elif field.device_class:
            self._attr_device_class = field.device_class
        if field.unit:
            self._attr_native_unit_of_measurement = field.unit

    def _booking(self) -> dict[str, Any] | None:
        method = SCOPES[self._scope][2]
        return getattr(self.coordinator, method)(self.apartment_id)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Wechsel aktueller/nächster Gast hängt an der Uhrzeit → minütlich prüfen
        self.async_on_remove(
            async_track_time_interval(self.hass, self._tick, timedelta(minutes=1))
        )

    @callback
    def _tick(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        booking = self._booking()
        return self._field.value(self.coordinator, booking) if booking else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        # Lange Texte: Zustand ist auf 255 Zeichen gekürzt, voller Text im Attribut
        if self._field.key in ("notiz", "assistent_notiz"):
            booking = self._booking() or {}
            raw = booking.get("notice" if self._field.key == "notiz" else "assistant-notice")
            return {"text": raw} if raw else None
        return None


class SmoobuLastMessageSensor(SmoobuEntity, RestoreSensor):
    """Letzte Gästenachricht (per Webhook „newMessage“), übersteht Neustarts."""

    _attr_icon = "mdi:message-text"

    def __init__(self, coordinator: C) -> None:
        super().__init__(coordinator, None, "letzte_gastnachricht")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Nach Neustart letzten Stand wiederherstellen (Smoobu wird nicht abgefragt)
        if self.coordinator.data and self.coordinator.data.last_message is None:
            last = await self.async_get_last_state()
            if last is not None and last.attributes.get("text"):
                self.coordinator.data.last_message = {
                    k: v for k, v in last.attributes.items() if k not in ("icon", "friendly_name")
                }

    @property
    def _msg(self) -> dict[str, Any]:
        return (self.coordinator.data.last_message if self.coordinator.data else None) or {}

    @property
    def native_value(self) -> str | None:
        text = self._msg.get("text")
        if not text:
            return None
        text = " ".join(str(text).split())
        return text if len(text) <= 255 else text[:252] + "…"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return dict(self._msg) or None

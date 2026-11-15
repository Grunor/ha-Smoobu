"""Sensoren je Wohnung (Gäste, Termine, Statistik) und fürs Konto (Diagnose).

Alle Werte werden aus dem Coordinator-Datenstand berechnet. Zeitabhängige
Werte (z. B. „aktueller Gast“ wechselt um 16:00) werden zusätzlich jede
Minute neu ausgewertet, damit sie nicht bis zur nächsten API-Abfrage
hinterherhängen. HA schreibt dabei nur echte Änderungen in die Historie.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
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
from .const import CONF_CLOUDHOOK_URL, CONF_SMOOBU_WEBHOOK_ID, STATS_DAYS
from .coordinator import SmoobuCoordinator
from .entity import SmoobuEntity
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
    return {
        "monat": _month_key(now),
        "davon_bis_heute": round(_rev(c, apt, True).get(_month_key(now), 0.0), 2),
        "vormonat": round(_rev(c, apt).get(_month_key(prev), 0.0), 2),
        "vorjahresmonat": round(_rev(c, apt).get(_month_key(last_year), 0.0), 2),
        "berechnung": "Buchungspreis anteilig nach Nächten, ohne Sperrzeiten/Stornos",
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
        attrs_fn=lambda c, a: _price_attrs(c, _current(c, a)),
    ),
    SmoobuSensorDescription(
        key="preis_naechster_gast",
        icon="mdi:cash-fast",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=lambda c, a: _price(_next(c, a)),
        attrs_fn=lambda c, a: _price_attrs(c, _next(c, a)),
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
        SmoobuLastUpdateSensor(coordinator),
        SmoobuLastEventSensor(coordinator),
        SmoobuWebhookSensor(coordinator),
    ]
    async_add_entities(entities)


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

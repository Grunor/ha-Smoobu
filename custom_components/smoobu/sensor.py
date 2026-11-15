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
    parse_date,
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
    }


def _occupancy(c: C, apt: int) -> float:
    """Anteil belegter Nächte (inkl. Blockierungen) in den nächsten 30 Tagen."""
    start, end = window(STATS_DAYS)
    booked = sum(stay_overlap_nights(b, start, end) for b in c.bookings_for(apt))
    return round(min(booked, STATS_DAYS) / STATS_DAYS * 100, 1)


def _revenue(c: C, apt: int) -> float:
    return round(sum(float(b.get("price") or 0) for b in _upcoming_in_window(c, apt)), 2)


def _unpaid(c: C, apt: int) -> list[dict[str, Any]]:
    """Laufende/kommende Gästebuchungen, die noch nicht voll bezahlt sind."""
    now_bookings = []
    for b in c.bookings_for(apt):
        if is_blocked(b):
            continue
        end = booking_end(b, c.default_checkout)
        if end is None or end < dt_util.now():
            continue
        if not is_yes(b.get("price-paid")):
            now_bookings.append(b)
    return now_bookings


def _currency(c: C, apt: int) -> str:
    return (c.data.apartments.get(apt, {}) if c.data else {}).get("currency") or "EUR"


# ---------------------------------------------------------------------------
# Beschreibungen
# ---------------------------------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class SmoobuSensorDescription(SensorEntityDescription):
    value_fn: Callable[[C, int], Any]
    attrs_fn: Callable[[C, int], dict[str, Any]] | None = None
    time_dependent: bool = True


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
        key="offene_zahlungen",
        icon="mdi:cash-clock",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c, a: len(_unpaid(c, a)),
        attrs_fn=lambda c, a: {
            "buchungen": [_short(b) for b in _unpaid(c, a)],
            "offener_betrag": round(sum(float(b.get("price") or 0) for b in _unpaid(c, a)), 2),
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

"""Binärsensoren je Wohnung: belegt, Anreise/Abreise/Gästewechsel heute.

Plus Diagnose fürs Konto: Liefert Smoobu Gästedaten (PII)?
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from . import SmoobuConfigEntry
from .booking_fields import FIELDS, SCOPES, BookingField, is_enabled
from .coordinator import SmoobuCoordinator
from .entity import SmoobuEntity
from .models import booking_attributes, guest_name, is_blocked, parse_date, pet_hint

C = SmoobuCoordinator


def _guest_bookings_on(c: C, apt: int, field: str, days: int = 0) -> list[dict[str, Any]]:
    """Gästebuchungen, deren arrival bzw. departure heute (days=0) bzw. in `days` Tagen ist."""
    day = dt_util.now().date() + timedelta(days=days)
    return [
        b
        for b in c.bookings_for(apt)
        if not is_blocked(b) and parse_date(b.get(field)) == day
    ]


def _pet_attrs(booking: dict[str, Any] | None) -> dict[str, Any]:
    """Gast, Anreise und Fundstelle zum Hunde-Hinweis."""
    if not booking:
        return {}
    return {
        "gastname": guest_name(booking),
        "anreise": booking.get("arrival"),
        "abreise": booking.get("departure"),
        "hund_hinweis": pet_hint(booking),
    }


@dataclass(frozen=True, kw_only=True)
class SmoobuBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[C, int], bool]
    attrs_fn: Callable[[C, int], dict[str, Any]] | None = None


APARTMENT_BINARY: tuple[SmoobuBinaryDescription, ...] = (
    SmoobuBinaryDescription(
        # an zwischen Check-in-Zeit und Check-out-Zeit einer Gästebuchung
        key="belegt",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        value_fn=lambda c, a: c.current_booking(a) is not None,
        attrs_fn=lambda c, a: booking_attributes(
            c.current_booking(a), c.default_checkin, c.default_checkout, c.checkout_buffer
        ),
    ),
    SmoobuBinaryDescription(
        key="anreise_heute",
        icon="mdi:calendar-import",
        value_fn=lambda c, a: bool(_guest_bookings_on(c, a, "arrival")),
        attrs_fn=lambda c, a: booking_attributes(
            next(iter(_guest_bookings_on(c, a, "arrival")), None),
            c.default_checkin,
            c.default_checkout,
            c.checkout_buffer,
        ),
    ),
    SmoobuBinaryDescription(
        # Morgen reist ein Gast an (Vorbereitung am Vorabend: Hund, Vorheizen, Reinigung)
        key="anreise_morgen",
        icon="mdi:calendar-arrow-right",
        value_fn=lambda c, a: bool(_guest_bookings_on(c, a, "arrival", 1)),
        attrs_fn=lambda c, a: booking_attributes(
            next(iter(_guest_bookings_on(c, a, "arrival", 1)), None),
            c.default_checkin,
            c.default_checkout,
            c.checkout_buffer,
        ),
    ),
    SmoobuBinaryDescription(
        key="abreise_heute",
        icon="mdi:calendar-export",
        value_fn=lambda c, a: bool(_guest_bookings_on(c, a, "departure")),
        attrs_fn=lambda c, a: booking_attributes(
            next(iter(_guest_bookings_on(c, a, "departure")), None),
            c.default_checkin,
            c.default_checkout,
            c.checkout_buffer,
        ),
    ),
    SmoobuBinaryDescription(
        # Laufende Buchung mit Hund/Haustier (Preiselement oder Notiz)
        key="hund_aktueller_gast",
        icon="mdi:dog",
        value_fn=lambda c, a: pet_hint(c.current_booking(a)) is not None,
        attrs_fn=lambda c, a: _pet_attrs(c.current_booking(a)),
    ),
    SmoobuBinaryDescription(
        # Nächste Buchung mit Hund/Haustier → z. B. Hundedecke/Napf bereitlegen
        key="hund_naechster_gast",
        icon="mdi:dog-side",
        value_fn=lambda c, a: pet_hint(c.next_booking(a)) is not None,
        attrs_fn=lambda c, a: _pet_attrs(c.next_booking(a)),
    ),
    SmoobuBinaryDescription(
        # Abreise und Anreise am selben Tag → Reinigung zwischen 11 und 16 Uhr
        key="gaestewechsel_heute",
        icon="mdi:swap-horizontal",
        value_fn=lambda c, a: bool(_guest_bookings_on(c, a, "arrival"))
        and bool(_guest_bookings_on(c, a, "departure")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmoobuConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        SmoobuApartmentBinary(coordinator, apt_id, desc)
        for apt_id in coordinator.data.apartments
        for desc in APARTMENT_BINARY
    ]
    entities += [
        SmoobuBookingFieldBinary(coordinator, apt_id, scope, field)
        for apt_id in coordinator.data.apartments
        for scope in SCOPES
        for field in FIELDS
        if field.binary
    ]
    entities.append(SmoobuPiiBinary(coordinator))
    async_add_entities(entities)


class SmoobuApartmentBinary(SmoobuEntity, BinarySensorEntity):
    entity_description: SmoobuBinaryDescription

    def __init__(self, coordinator: C, apartment_id: int, description: SmoobuBinaryDescription) -> None:
        super().__init__(coordinator, apartment_id, description.key)
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Minütlich neu auswerten, damit „belegt“ pünktlich zur Check-in-Zeit wechselt.
        self.async_on_remove(
            async_track_time_interval(self.hass, self._tick, timedelta(minutes=1))
        )

    @callback
    def _tick(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator, self.apartment_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator, self.apartment_id)


class SmoobuPiiBinary(SmoobuEntity, BinarySensorEntity):
    """Problem-Sensor: an, wenn Smoobu keine Gastnamen liefert (PII-Recht fehlt)."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: C) -> None:
        super().__init__(coordinator, None, "gastdaten_fehlen")

    @property
    def is_on(self) -> bool | None:
        pii = self.coordinator.data.pii_available if self.coordinator.data else None
        return None if pii is None else not pii


class SmoobuBookingFieldBinary(SmoobuEntity, BinarySensorEntity):
    """Zahlungsstatus der laufenden bzw. nächsten Buchung."""

    def __init__(self, coordinator: C, apartment_id: int, scope: str, field: BookingField) -> None:
        super().__init__(coordinator, apartment_id, f"{scope}_{field.key}")
        self._scope = scope
        self._field = field
        self._attr_icon = field.icon
        self._attr_entity_registry_enabled_default = is_enabled(field, scope)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_interval(self.hass, self._tick, timedelta(minutes=1))
        )

    @callback
    def _tick(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        booking = getattr(self.coordinator, SCOPES[self._scope][2])(self.apartment_id)
        return self._field.value(self.coordinator, booking) if booking else None

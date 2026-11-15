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
from .coordinator import SmoobuCoordinator
from .entity import SmoobuEntity
from .models import booking_attributes, is_blocked, parse_date

C = SmoobuCoordinator


def _guest_bookings_on(c: C, apt: int, field: str) -> list[dict[str, Any]]:
    """Gästebuchungen, deren arrival bzw. departure heute ist."""
    today = dt_util.now().date()
    return [
        b
        for b in c.bookings_for(apt)
        if not is_blocked(b) and parse_date(b.get(field)) == today
    ]


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

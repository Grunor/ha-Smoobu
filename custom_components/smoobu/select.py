"""Auswahl-Entitäten für die Auswertung in Lovelace (ab v1.7.0).

Drei Auswahlen je Wohnung – Kanal, Zeitraum, Vergleich. Sie speichern ihren
Stand im Coordinator; die Auswertungs-Sensoren (sensor_analytics.py) lesen
ihn und zeigen sofort die passenden Werte. So entsteht ein Filter im
Dashboard ohne Helfer und ohne Templates. Der Stand übersteht Neustarts.
"""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import SmoobuConfigEntry
from .analytics import COMPARES, PERIODS, SEL_ALL, SEL_DIRECT, SEL_PORTAL, channels_of
from .coordinator import SmoobuCoordinator
from .entity import SmoobuEntity
from .sensor_analytics import DEFAULT_SELECTION


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmoobuConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        SmoobuSelectionSelect(coordinator, apt, field)
        for apt in coordinator.data.apartments
        for field in ("kanal", "zeitraum", "vergleich")
    )


class SmoobuSelectionSelect(SmoobuEntity, SelectEntity, RestoreEntity):
    """Auswahl Kanal / Zeitraum / Vergleich für die Auswertungs-Sensoren."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: SmoobuCoordinator, apartment_id: int, field: str) -> None:
        super().__init__(coordinator, apartment_id, f"auswertung_{field}")
        self._field = field
        self._attr_icon = {
            "kanal": "mdi:filter-variant",
            "zeitraum": "mdi:calendar-range",
            "vergleich": "mdi:compare-horizontal",
        }[field]

    @property
    def options(self) -> list[str]:
        if self._field == "zeitraum":
            return PERIODS
        if self._field == "vergleich":
            return COMPARES
        # Kanäle aus den Buchungen; neue Kanäle erscheinen automatisch
        names = [ch["name"] for ch in channels_of(self.coordinator.records(self.apartment_id))]
        return [SEL_ALL, SEL_DIRECT, SEL_PORTAL, *names]

    @property
    def current_option(self) -> str:
        sel = self.coordinator.selection.get(self.apartment_id, {})
        return sel.get(self._field, DEFAULT_SELECTION[self._field])

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        # Gespeicherte Auswahl übernehmen (Kanal auch, wenn er gerade nicht vorkommt)
        if last is not None and last.state not in ("unknown", "unavailable", None):
            if self._field != "kanal" and last.state not in self.options:
                return
            self.coordinator.selection.setdefault(self.apartment_id, {})[self._field] = last.state
            self.coordinator.async_update_listeners()

    async def async_select_option(self, option: str) -> None:
        self.coordinator.selection.setdefault(self.apartment_id, {})[self._field] = option
        # Alle Entitäten neu schreiben → Auswertungs-Sensoren zeigen die neue Auswahl
        self.coordinator.async_update_listeners()

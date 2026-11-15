"""Gemeinsame Basisklasse: ein Gerät je Smoobu-Wohnung bzw. ein Kontogerät."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmoobuCoordinator


class SmoobuEntity(CoordinatorEntity[SmoobuCoordinator]):
    """Entität, die zu einer Wohnung (apartment_id) oder zum Konto (None) gehört."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SmoobuCoordinator, apartment_id: int | None, key: str
    ) -> None:
        super().__init__(coordinator)
        self.apartment_id = apartment_id
        entry_id = coordinator.config_entry.entry_id
        # unique_id stabil über Konto + Wohnung + Schlüssel → Umbenennen in HA bleibt erhalten.
        scope = apartment_id if apartment_id is not None else "account"
        self._attr_unique_id = f"{entry_id}_{scope}_{key}"
        self._attr_translation_key = key

        if apartment_id is None:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{entry_id}_account")},
                name="Smoobu",
                manufacturer="Smoobu",
                model="Konto",
                entry_type=DeviceEntryType.SERVICE,
                configuration_url="https://login.smoobu.com/",
            )
        else:
            apt = coordinator.data.apartments.get(apartment_id, {}) if coordinator.data else {}
            apt_type = apt.get("type")
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{entry_id}_{apartment_id}")},
                # Präfix „Smoobu“ im Gerätenamen → Entitäts-IDs werden zu
                # <domain>.smoobu_<wohnung>_<entität> (eindeutig, gut suchbar,
                # keine Kollision mit anderen Geräten derselben Wohnung).
                name=f"Smoobu {apt.get('name') or apartment_id}",
                manufacturer="Smoobu",
                model=apt_type.get("name") if isinstance(apt_type, dict) else "Wohnung",
                model_id=str(apartment_id),
                entry_type=DeviceEntryType.SERVICE,
                configuration_url="https://login.smoobu.com/",
            )

"""v1.19.0b8: neue HA-Benutzer erkennen und melden."""
from pytest_homeassistant_custom_component.common import async_mock_service

from homeassistant.components import persistent_notification

from custom_components.smoobu.const import DOMAIN

from .test_smoobu import setup  # noqa: F401  (Fixture)


async def test_neuer_benutzer_meldung(hass, setup, hass_storage):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    pushes = async_mock_service(hass, "notify", "mobile_app_test")
    hass.config_entries.async_update_entry(entry, options={**entry.options, "assist_recipients": ["notify.mobile_app_test"]})
    await hass.async_block_till_done()
    # Start-Abgleich beim ersten Lauf: Bestand still übernommen
    assert "bekannt" in hass_storage[f"{DOMAIN}_benutzer"]["data"]
    assert not persistent_notification._async_get_or_create_notifications(hass)  # noqa: SLF001
    # neuer Benutzer im laufenden Betrieb → HA-Meldung + Push
    user = await hass.auth.async_create_user("Neue Kraft")
    await hass.async_block_till_done()
    notes = persistent_notification._async_get_or_create_notifications(hass)  # noqa: SLF001
    note = notes.get(f"smoobu_neuer_benutzer_{user.id}")
    assert note and "Neue Kraft" in note["title"] and "dringend" in note["message"]
    assert pushes and "Neue Kraft" in pushes[-1].data["title"]
    assert user.id in hass_storage[f"{DOMAIN}_benutzer"]["data"]["bekannt"]
    # Systembenutzer werden ignoriert
    n = len(pushes)
    await hass.auth.async_create_system_user("App")
    await hass.async_block_till_done()
    assert len(pushes) == n

"""Einstellungen im Dashboard (v1.18.0): smoobu/settings/get + set, Berechtigung, Prüfung."""

from homeassistant.config_entries import ConfigEntryState

from custom_components.smoobu.const import DOMAIN

from .test_smoobu import setup  # noqa: F401  (Fixture)


async def _call(ws, msg_id, **msg):
    await ws.send_json({"id": msg_id, **msg})
    return await ws.receive_json()


async def test_settings_admin(hass, setup, hass_ws_client):  # noqa: F811
    ws = await hass_ws_client(hass)
    res = (await _call(ws, 1, type="smoobu/settings/get"))["result"]
    assert res["erlaubt"] is True and res["entry_id"] == setup.entry_id
    werte, meta = res["werte"], res["meta"]
    # Standardwerte wie im Options-Dialog
    assert werte["scan_interval"] == 10 and werte["default_checkin"] == "16:00"
    assert werte["commissions"]["Airbnb"] == 15.5 and werte["notify_vorschlag"] is True
    assert meta["admin"] is True and "Airbnb" in meta["kanaele"]
    assert meta["wohnungen"][0]["id"] == "123" and meta["benutzer"]

    # Ungültige Werte → Fehler je Feld, nichts gespeichert
    res = (await _call(ws, 2, type="smoobu/settings/set", changes={
        "scan_interval": 0, "notify_quiet_from": "25:00", "ai_enabled": True,
        "apartment_codes": {"123": "#!"}, "commissions": {"Airbnb": 70}, "bogus": 1}))["result"]
    assert res["ok"] is False
    assert res["fehler"] == {
        "scan_interval": "invalid", "notify_quiet_from": "invalid_time", "ai_entity": "ai_entity_required",
        "apartment_codes.123": "invalid_code", "commissions": "invalid_percent", "bogus": "unknown_field"}
    assert "scan_interval" not in setup.options

    # Gültige Änderung → gespeichert, Integration neu geladen
    res = (await _call(ws, 3, type="smoobu/settings/set", changes={
        "scan_interval": 15, "notify_buchung": True, "notify_buchung_to": ["notify.mobile_app_test"],
        "notify_quiet": True, "notify_quiet_from": "22:00", "commissions": {"Airbnb": 20, "Expedia": "18,5"},
        "apartment_codes": {"123": "fw1x"}, "history_since": "2020-01-01", "notify_briefing": True}))["result"]
    await hass.async_block_till_done()
    assert res["ok"] is True and res["geaendert"] is True
    o = setup.options
    assert o["scan_interval"] == 15 and o["notify_buchung_to"] == ["notify.mobile_app_test"]
    assert o["commissions"]["Expedia"] == 18.5 and o["apartment_codes"] == {"123": "FW1X"}
    assert o["history_since"] == "2020-01-01" and o["assist_briefing"] is True  # alter Schalter mitgeführt
    assert "ai_entity" not in o
    entry = hass.config_entries.async_get_entry(setup.entry_id)
    assert entry.state is ConfigEntryState.LOADED and entry.runtime_data is not None

    # Leeren von „Daten abrufen seit“ entfernt den Schlüssel
    res = (await _call(ws, 4, type="smoobu/settings/set", changes={"history_since": None}))["result"]
    await hass.async_block_till_done()
    assert res["ok"] is True and "history_since" not in setup.options


async def test_settings_permissions(hass, setup, hass_ws_client, hass_read_only_access_token, hass_read_only_user):  # noqa: F811
    guest = await hass_ws_client(hass, hass_read_only_access_token)
    res = (await _call(guest, 1, type="smoobu/settings/get"))["result"]
    assert res == {"erlaubt": False}
    res = await _call(guest, 2, type="smoobu/settings/set", changes={"scan_interval": 5})
    assert res["success"] is False and res["error"]["code"] == "unauthorized"

    # Freigabe durch einen Admin
    hass.config_entries.async_update_entry(setup, options={**setup.options, "settings_users": [hass_read_only_user.id]})
    await hass.async_block_till_done()
    res = (await _call(guest, 3, type="smoobu/settings/get"))["result"]
    assert res["erlaubt"] is True and res["meta"]["admin"] is False and res["meta"]["benutzer"] == []
    # Nicht-Admin darf ändern, aber nicht die Liste der Berechtigten
    res = (await _call(guest, 4, type="smoobu/settings/set", changes={"settings_users": []}))["result"]
    assert res["fehler"] == {"settings_users": "admin_only"}
    res = (await _call(guest, 5, type="smoobu/settings/set", changes={"enrich_count": 2}))["result"]
    await hass.async_block_till_done()
    assert res["ok"] is True
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.options["enrich_count"] == 2 and entry.options["settings_users"] == [hass_read_only_user.id]


async def test_options_notify_sections_have_inner_defaults(hass, setup):  # noqa: F811
    """1.17.1: Abschnitte ohne eigenen Default – sonst überschreibt {} die Feld-Defaults (OK-Button gesperrt)."""
    import voluptuous_serialize
    from homeassistant.helpers import config_validation as cv

    flow = await hass.config_entries.options.async_init(setup.entry_id)
    for _ in range(3):  # init → provisionen → assistent → benachrichtigungen (Standardwerte übernehmen)
        schema = flow["data_schema"]
        data = {str(k): k.default() for k in schema.schema if callable(getattr(k, "default", None))}
        flow = await hass.config_entries.options.async_configure(flow["flow_id"], data)
    assert flow["step_id"] == "benachrichtigungen"
    fields = voluptuous_serialize.convert(flow["data_schema"], custom_serializer=cv.custom_serializer)
    for field in fields:
        assert "default" not in field, field["name"]
        assert any("default" in sub for sub in field["schema"])

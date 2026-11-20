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
    # v1.18.0: Kanal-Dropdown – drei Gruppen, Katalog enthält z. B. HomeToGo
    auswahl = meta["kanal_auswahl"]
    assert set(auswahl) == {"buchungen", "eingestellt", "katalog", "alle"}
    assert "HomeToGo" in auswahl["alle"] and "Airbnb" in auswahl["alle"]
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
    for _ in range(4):  # init → provisionen → kosten → assistent → benachrichtigungen (Standardwerte übernehmen)
        schema = flow["data_schema"]
        data = {str(k): k.default() for k in schema.schema if callable(getattr(k, "default", None))}
        flow = await hass.config_entries.options.async_configure(flow["flow_id"], data)
    assert flow["step_id"] == "benachrichtigungen"
    fields = voluptuous_serialize.convert(flow["data_schema"], custom_serializer=cv.custom_serializer)
    for field in fields:
        assert "default" not in field, field["name"]
        assert any("default" in sub for sub in field["schema"])


async def test_settings_kosten(hass, setup, hass_ws_client):  # noqa: F811
    """v1.18.0: Kosten & Preise in der Einstellungskarte – Standardwerte, Prüfung, Speichern."""
    ws = await hass_ws_client(hass)
    werte = (await _call(ws, 1, type="smoobu/settings/get"))["result"]["werte"]
    assert werte["cost_cleaning"] == 17.0 and werte["cost_ref_year"] == 2025 and len(werte["cost_grid_share"]) == 12
    assert werte["channel_markups"]["Booking.com"] == 45.0 and werte["genius_share"] == 100.0
    res = (await _call(ws, 2, type="smoobu/settings/set", changes={
        "cost_grid_share": [1, 2, 3], "genius_discount": 80, "cost_cleaning": "abc"}))["result"]
    assert res["fehler"] == {"cost_grid_share": "invalid_grid_share", "genius_discount": "invalid_number",
                             "cost_cleaning": "invalid_number"}
    res = (await _call(ws, 3, type="smoobu/settings/set", changes={
        "cost_cleaning": "19,5", "cost_grid_share": [60] * 12, "channel_markups": {"Airbnb": 30, "Expedia": "20"}}))["result"]
    await hass.async_block_till_done()
    assert res["ok"] is True
    o = setup.options
    assert o["cost_cleaning"] == 19.5 and o["cost_grid_share"] == [60.0] * 12
    assert o["channel_markups"] == {"Airbnb": 30.0, "Expedia": 20.0}


def test_provision_herkunft():
    """v1.18.0: je Kanal markieren, ob Smoobu eine gültige Provision mitliefert."""
    from datetime import date

    from custom_components.smoobu.analytics import build_records
    from custom_components.smoobu.settings import commission_sources
    from tests.test_analytics import bk, costs

    recs = build_records([
        bk(1, "2026-03-01", "2026-03-03", "Booking.com", 200, **{"commission-included": 30}),
        bk(2, "2026-04-01", "2026-04-03", "Booking.com", 200, **{"commission-included": 30}),
        bk(3, "2026-05-01", "2026-05-03", "Airbnb", 200),
        bk(4, "2026-05-10", "2026-05-12", "Airbnb", 200, **{"commission-included": 29}),
        bk(5, "2026-06-01", "2026-06-03", "Expedia", 200, **{"commission-included": 150}),  # 75 % → unplausibel
    ], costs, [], date(2026, 11, 17))
    src = commission_sources(recs, date(2026, 11, 17))
    assert src["Booking.com"]["status"] == "smoobu" and src["Booking.com"]["prozent_schnitt"] == 15.0
    assert src["Airbnb"]["status"] == "teilweise" and src["Airbnb"]["mit_provision"] == 1
    assert src["Expedia"]["status"] == "option" and src["Expedia"]["ungueltig"] == 1


def test_genius_check():
    from datetime import date

    from custom_components.smoobu.analytics import build_records
    from custom_components.smoobu.settings import genius_check
    from tests.test_analytics import bk, costs

    recs = build_records([
        bk(1, "2026-08-04", "2026-08-06", "Booking.com", 188, notice="Weitere Angaben: booker_is_genius"),
        bk(2, "2026-09-04", "2026-09-06", "Booking.com", 188, notice="Payment charge is EUR 2.63"),
        bk(3, "2026-09-10", "2026-09-12", "Airbnb", 188, notice="booker_is_genius"),
    ], costs, [], date(2026, 11, 17))
    g = genius_check(recs, date(2026, 11, 17))
    assert g == {"buchungen": 2, "genius": 1, "anteil": 50, "letzte": "2026-09-04"}

"""Preise übernehmen / rückgängig (preisaktion.py + smoobu/rates/apply|undo|changes)."""
from datetime import date

import pytest

from custom_components.smoobu.const import DOMAIN
from custom_components.smoobu.preisaktion import base_price, days_of, operations, plan, verify

from .test_smoobu import BASE, setup  # noqa: F401  (Fixture)

TODAY = date(2026, 12, 20)
RATES = {f"2026-12-{d:02d}": {"price": 62, "min_length_of_stay": 1} for d in range(20, 32)}
RATES["2026-12-27"] = {"price": 90, "min_length_of_stay": 2}  # eigener Preis


def _body(call):
    import json  # noqa: PLC0415
    data = call[2]
    return json.loads(data) if isinstance(data, (bytes, str)) else data


async def _call(ws, msg_id, **msg):
    await ws.send_json({"id": msg_id, **msg})
    return await ws.receive_json()


def test_plan_senken_mit_filtern():
    spec = {"von": "2026-12-18", "bis": "2026-12-31", "prozent": -10, "ohne_feiertage": True, "nur_basispreis": True}
    res = plan(spec, RATES, TODAY)
    assert res["basispreis"] == 62
    tage = {t["datum"]: t for t in res["tage"]}
    skipped = {s["datum"]: s["grund"] for s in res["uebersprungen"]}
    assert "2026-12-18" not in tage and "2026-12-18" not in skipped  # Vergangenheit fällt weg
    assert skipped["2026-12-24"] == "Feiertag" and skipped["2026-12-23"] == "Feiertag"  # Nacht vor Heiligabend
    assert skipped["2026-12-31"] == "Feiertag" and skipped["2026-12-27"] == "eigener Preis"
    assert tage["2026-12-21"]["preis_neu"] == 56.0 and tage["2026-12-21"]["preis_alt"] == 62


def test_plan_fester_preis_wochentage_und_mindestaufenthalt():
    res = plan({"von": "2026-12-20", "bis": "2026-12-31", "preis": 70, "wochentage": [4, 5], "mindestaufenthalt": 2}, RATES, TODAY)
    assert [t["datum"] for t in res["tage"]] == ["2026-12-25", "2026-12-26"]  # Fr/Sa
    assert res["tage"][0]["min_neu"] == 2
    with pytest.raises(ValueError):
        plan({"von": "2026-12-20", "bis": "2026-12-21"}, RATES, TODAY)
    assert base_price({}, days_of({"von": "2026-12-20", "bis": "2026-12-21"}, TODAY)) is None


def test_operationen_und_pruefung():
    res = plan({"von": "2026-12-20", "bis": "2026-12-26", "preis": 70, "ohne_feiertage": True}, RATES, TODAY)
    ops = operations(res["tage"])
    assert ops == [{"dates": ["2026-12-20:2026-12-22", "2026-12-26:2026-12-26"], "daily_price": 70.0}]
    back = operations(res["tage"], restore=True)
    assert back == [{"dates": ["2026-12-20:2026-12-22", "2026-12-26:2026-12-26"], "daily_price": 62.0}]
    assert verify(res["tage"], RATES)[0] == {"datum": "2026-12-20", "soll": 70.0, "ist": 62}
    assert verify(res["tage"], RATES, restore=True) == []


async def test_websocket_uebernehmen_und_rueckgaengig(hass, setup, hass_ws_client, aioclient_mock, hass_read_only_access_token,  # noqa: F811
                                                      hass_read_only_user):
    aioclient_mock.post(f"{BASE}/api/rates", json={"success": True})
    ws = await hass_ws_client(hass)
    spec = {"von": "2026-11-20", "bis": "2026-11-22", "preis": 70, "label": "Test"}
    prev = (await _call(ws, 1, type="smoobu/rates/apply", vorgabe=spec, dry_run=True))["result"]
    assert prev["gespeichert"] is False and len(prev["tage"]) == 3
    posts = [c for c in aioclient_mock.mock_calls if c[0] == "POST" and str(c[1]).endswith("/api/rates")]
    assert not posts
    res = (await _call(ws, 2, type="smoobu/rates/apply", vorgabe=spec))["result"]
    assert res["gespeichert"] is True and res["aenderung_id"]
    posts = [c for c in aioclient_mock.mock_calls if c[0] == "POST" and str(c[1]).endswith("/api/rates")]
    assert _body(posts[-1])["operations"] == [{"dates": ["2026-11-20:2026-11-22"], "daily_price": 70.0}]
    lst = (await _call(ws, 3, type="smoobu/rates/changes"))["result"]
    assert lst["aenderungen"][0]["label"] == "Test" and lst["darf_aendern"] is True
    undo = (await _call(ws, 4, type="smoobu/rates/undo", aenderung_id=res["aenderung_id"]))["result"]
    assert undo["tage"] == 3
    posts = [c for c in aioclient_mock.mock_calls if c[0] == "POST" and str(c[1]).endswith("/api/rates")]
    # alte Preise sind je Tag verschieden (Mock: 80 + Tag) → je Tag eine Operation mit dem alten Wert
    ops = _body(posts[-1])["operations"]
    assert sorted(d for o in ops for d in o["dates"]) == ["2026-11-20:2026-11-20", "2026-11-21:2026-11-21", "2026-11-22:2026-11-22"]
    assert {o["daily_price"] for o in ops} == {85.0, 86.0, 87.0}
    again = await _call(ws, 5, type="smoobu/rates/undo", aenderung_id=res["aenderung_id"])
    assert again["success"] is False

    # Rolle ohne „preise“ darf nicht übernehmen
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    hass.config_entries.async_update_entry(entry, options={**entry.options, "user_roles": {hass_read_only_user.id: "mitarbeiter"}})
    await hass.async_block_till_done()
    guest = await hass_ws_client(hass, hass_read_only_access_token)
    res = await _call(guest, 6, type="smoobu/rates/apply", vorgabe=spec)
    assert res["error"]["code"] == "unauthorized"

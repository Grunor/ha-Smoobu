"""v1.19.0: Türcodes – Zufall ohne triviale Codes, Gültigkeit, Smoobu-Notiz, Schloss-Adapter, Entitäten, Platzhalter."""
from datetime import datetime, time

from pytest_homeassistant_custom_component.common import async_mock_service

from homeassistant.util import dt as dt_util

from custom_components.smoobu.const import DOMAIN
from custom_components.smoobu.tuercode import fill, lock_calls, merge_note, new_code, note_line, trivial, window

from .test_smoobu import BASE, setup  # noqa: F401  (Fixture)


def test_trivial_und_zufall():
    for bad in ("1111", "1234", "9876", "121212", "123123", "890123", "000000"):
        assert trivial(bad), bad
    for ok in ("482913", "5019", "730284"):
        assert not trivial(ok), ok
    seq = iter([1, 1, 1, 1, 1, 1, 4, 8, 2, 9, 1, 3, 4, 8, 2, 9, 1, 3, 7, 3, 0, 2, 8, 4])
    # erst „111111“ (trivial), dann „482913“ (vergeben), dann „730284“
    assert new_code(6, {"482913"}, rand=lambda _n: next(seq)) == "730284"
    assert len(new_code(4, set())) == 4 and len(new_code(20, set())) == 10  # Grenzen 4–10


def test_gueltigkeit_notiz_platzhalter():
    dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Berlin"))
    a, b = window({"anreise": "2026-11-22", "abreise": "2026-11-26", "check_in": "17:00", "check_out": None}, time(16), time(11), 2, 1)
    assert (a.hour, a.day, b.hour, b.day) == (15, 22, 12, 26)
    line = note_line("482913", a, b)
    assert line == "Türcode: 482913 (gültig 22.11. 15:00 – 26.11. 12:00)"
    assert merge_note("Hund: Leo", line) == f"{line}\nHund: Leo"
    assert merge_note(f"Türcode: 111 (alt)\nHund: Leo", line) == f"{line}\nHund: Leo"
    assert merge_note(f"{line}\nHund: Leo", None) == "Hund: Leo"
    assert fill("Code: {{ turcode }} / {{türcode}}", "4829") == "Code: 4829 / 4829"


def test_schloss_adapter():
    it = {"von": "a", "bis": "b", "buchung_id": 1, "wohnung_id": 2}
    assert lock_calls({"typ": "kein"}, "setzen", 1, "4829", it) == []
    assert lock_calls({"typ": "zwave_js", "entitaet": "lock.t"}, "setzen", 5, "4829", it) == [
        ("zwave_js", "set_lock_usercode", {"entity_id": "lock.t", "code_slot": 5, "usercode": "4829"})]
    assert lock_calls({"typ": "zha", "entitaet": "lock.t"}, "loeschen", 5, "4829", it)[0][1] == "clear_lock_user_code"
    assert lock_calls({"typ": "matter", "entitaet": "lock.t"}, "setzen", 5, "4829", it)[0][2]["credential_type"] == "pin"
    z2m = lock_calls({"typ": "z2m", "entitaet": "Haustuer"}, "setzen", 5, "4829", it)[0]
    assert z2m[0:2] == ("mqtt", "publish") and z2m[2]["topic"] == "zigbee2mqtt/Haustuer/set" and '"pin_code": "4829"' in z2m[2]["payload"]
    sk = lock_calls({"typ": "skript", "entitaet": "script.tuer"}, "loeschen", 5, "4829", it)[0]
    assert sk[2]["variables"]["aktion"] == "loeschen" and sk[2]["variables"]["code"] == "4829"


async def _call(ws, msg_id, **msg):
    await ws.send_json({"id": msg_id, **msg})
    return await ws.receive_json()


async def test_ablauf_mit_zwave(hass, setup, aioclient_mock, hass_ws_client, hass_read_only_access_token, hass_read_only_user):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    sets = async_mock_service(hass, "zwave_js", "set_lock_usercode")
    clears = async_mock_service(hass, "zwave_js", "clear_lock_usercode")
    aioclient_mock.put(f"{BASE}/api/reservations/1", json={})
    aioclient_mock.put(f"{BASE}/api/reservations/2", json={})
    hass.config_entries.async_update_entry(entry, options={**entry.options, "door_code_enabled": True, "door_code_digits": 6,
                                                          "door_locks": {"123": {"typ": "zwave_js", "entitaet": "lock.haustuer", "slot_von": 10, "slot_bis": 12}}})
    await hass.async_block_till_done()
    doors = entry.runtime_data.doorcodes
    await doors.async_sync()
    c1, c2 = doors.for_booking(1), doors.for_booking(2)
    # laufender Gast: sofort ins Schloss (Platz 10); nächster Gast: geplant
    assert c1["status"] == "gesetzt" and c1["slot"] == 10 and len(c1["code"]) == 6 and not trivial(c1["code"])
    assert c2["status"] == "geplant" and c2["code"] != c1["code"]
    assert sets[0].data == {"entity_id": "lock.haustuer", "code_slot": 10, "usercode": c1["code"]}
    # Smoobu-Notiz geschrieben (PUT mit Türcode-Zeile)
    puts = [r for r in aioclient_mock.mock_calls if r[0] == "PUT"]
    assert any(f"Türcode: {c1['code']} (gültig 13.11. 14:00" in r[2].decode() for r in puts)
    # Entitäten
    await hass.async_block_till_done()
    cur = [s for s in hass.states.async_all("sensor") if s.entity_id.endswith("turcode_aktueller_gast")][0]
    nxt = [s for s in hass.states.async_all("sensor") if s.entity_id.endswith("turcode_nachster_gast")][0]
    assert cur.state == c1["code"] and nxt.state == c2["code"] and cur.attributes["code_platz"] == 10
    # Neu erzeugen: alter Code raus, neuer rein (Recht „belegung“)
    ws = await hass_ws_client(hass)
    res = (await _call(ws, 1, type="smoobu/doorcode/renew", reservation_id=1))["result"]["code"]
    assert res["code"] != c1["code"] and clears[0].data == {"entity_id": "lock.haustuer", "code_slot": 10} and res["status"] == "gesetzt"
    got = (await _call(ws, 2, type="smoobu/doorcode/get", reservation_id=1))["result"]
    assert got["aktiv"] and got["code"]["code"] == res["code"] and got["schloss"] == "zwave_js"
    # Rolle Reinigung sieht keine Codes
    hass.config_entries.async_update_entry(entry, options={**entry.options, "user_roles": {hass_read_only_user.id: "reinigung"}})
    await hass.async_block_till_done()
    guest = await hass_ws_client(hass, hass_read_only_access_token)
    assert (await _call(guest, 1, type="smoobu/doorcode/get", reservation_id=1))["error"]["code"] == "unauthorized"
    # Platzhalter beim Senden lokal ersetzt
    doors = entry.runtime_data.doorcodes
    code = doors.for_booking(2)["code"]
    aioclient_mock.post(f"{BASE}/api/reservations/2/messages/send-message-to-host", status=201, text="")
    await hass.services.async_call(DOMAIN, "send_message", {"reservation_id": 2, "message": "Euer Code: {{ turcode }}",
                                                             "subject": "x"}, blocking=True)
    sent = [r for r in aioclient_mock.mock_calls if r[0] == "POST" and "messages" in str(r[1])][-1]
    assert f"Euer Code: {code}" in (sent[2].decode() if isinstance(sent[2], bytes) else str(sent[2]))


async def test_storno_und_ablauf(hass, setup, aioclient_mock, freezer):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    sets = async_mock_service(hass, "script", "turn_on")
    aioclient_mock.put(f"{BASE}/api/reservations/1", json={})
    aioclient_mock.put(f"{BASE}/api/reservations/2", json={})
    hass.config_entries.async_update_entry(entry, options={**entry.options, "door_code_enabled": True, "door_code_note": False,
                                                          "door_locks": {"123": {"typ": "skript", "entitaet": "script.tuer", "slot_von": 1, "slot_bis": 3}}})
    await hass.async_block_till_done()
    doors = entry.runtime_data.doorcodes
    await doors.async_sync()
    assert doors.for_booking(1)["status"] == "gesetzt" and sets[-1].data["variables"]["aktion"] == "setzen"
    assert not [r for r in aioclient_mock.mock_calls if r[0] == "PUT"]  # Notiz aus
    # nach Gültigkeitsende (Abreise + 1 h) → im Schloss gelöscht
    freezer.move_to(datetime.fromisoformat(doors.for_booking(1)["bis"]) + __import__("datetime").timedelta(minutes=1))
    await doors.async_sync()
    assert doors.for_booking(1)["status"] == "abgelaufen" and sets[-1].data["variables"]["aktion"] == "loeschen"

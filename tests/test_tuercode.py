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


async def test_statischer_code(hass, setup, aioclient_mock, hass_ws_client):  # noqa: F811
    """v1.19.0b2: statischer Code je Wohnung (Schlüsseltresor) – alle Buchungen gleich, kein „Neu erzeugen“,
    Änderung tauscht den Code bei laufenden/kommenden Buchungen, Wechsel zurück → Zufall."""
    from custom_components.smoobu import settings

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    aioclient_mock.put(f"{BASE}/api/reservations/1", json={})
    aioclient_mock.put(f"{BASE}/api/reservations/2", json={})
    # Prüfung in den Einstellungen
    _vals, err = settings.validate(hass, entry, {"door_locks": {"123": {"typ": "kein", "modus": "statisch", "code": "12"}}}, None)
    assert err["door_locks"] == "invalid_static_code"
    vals, err = settings.validate(hass, entry, {"door_locks": {"123": {"typ": "kein", "modus": "statisch", "code": " 4711 "}}}, None)
    assert not err and vals["door_locks"]["123"] == {"typ": "kein", "modus": "statisch", "code": "4711"}
    vals, _ = settings.validate(hass, entry, {"door_locks": {"123": {"typ": "kein", "modus": "zufall", "code": "4711"}}}, None)
    assert vals["door_locks"]["123"] == {"typ": "kein"}

    hass.config_entries.async_update_entry(entry, options={**entry.options, "door_code_enabled": True,
                                                          "door_locks": {"123": {"typ": "kein", "modus": "statisch", "code": "4711"}}})
    await hass.async_block_till_done()
    doors = entry.runtime_data.doorcodes
    await doors.async_sync()
    c1, c2 = doors.for_booking(1), doors.for_booking(2)
    assert c1["code"] == c2["code"] == "4711" and c1["art"] == "statisch" and c1["status"] == "aktiv"
    puts = [r for r in aioclient_mock.mock_calls if r[0] == "PUT"]
    assert any("Türcode: 4711 (gültig" in r[2].decode() for r in puts)
    assert "4711" in doors.known_codes()
    ws = await hass_ws_client(hass)
    assert (await _call(ws, 1, type="smoobu/doorcode/renew", reservation_id=1))["error"]["code"] == "static_code"
    assert (await _call(ws, 2, type="smoobu/doorcode/get", reservation_id=1))["result"]["statisch"] is True
    # Code geändert → beide Buchungen bekommen den neuen
    hass.config_entries.async_update_entry(entry, options={**entry.options, "door_locks": {"123": {"typ": "kein", "modus": "statisch", "code": "A2B9"}}})
    await hass.async_block_till_done()
    doors = entry.runtime_data.doorcodes
    await doors.async_sync()
    assert doors.for_booking(1)["code"] == doors.for_booking(2)["code"] == "A2B9" and doors.for_booking(1)["status"] == "aktiv"
    # zurück auf Zufall → eigene Zufallscodes
    hass.config_entries.async_update_entry(entry, options={**entry.options, "door_locks": {"123": {"typ": "kein"}}})
    await hass.async_block_till_done()
    doors = entry.runtime_data.doorcodes
    await doors.async_sync()
    r1, r2 = doors.for_booking(1), doors.for_booking(2)
    assert r1["art"] == r2["art"] == "zufall" and r1["code"] != r2["code"] and len(r1["code"]) == 6


async def test_entitaeten_vorschlaege(hass, setup):  # noqa: F811
    """Korrektur 21.11.2026: Dropdown-Vorschläge vorgefiltert – passende zuerst, Preise nur mit Währung."""
    from custom_components.smoobu.settings import energy_meta

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    tot = {"device_class": "energy", "state_class": "total_increasing", "unit_of_measurement": "kWh"}
    hass.states.async_set("sensor.strom_ferienwohnung", "10", {**tot, "friendly_name": "Strom Ferienwohnung"})
    hass.states.async_set("sensor.hausverbrauch", "10", {**tot, "friendly_name": "Hausverbrauch"})
    hass.states.async_set("sensor.co2", "300", {"unit_of_measurement": "gCO2eq/kWh"})
    hass.states.async_set("input_number.strompreis", "0.3", {"unit_of_measurement": "€/kWh", "friendly_name": "Strompreis"})
    hass.states.async_set("sensor.fewo_vorheizstart", "2026-11-21T10:00:00+00:00", {"device_class": "timestamp"})
    m = energy_meta(hass, entry.runtime_data)
    assert m["energie_zaehler"][0]["entity_id"] == "sensor.strom_ferienwohnung" and m["energie_zaehler"][0]["passend"]
    assert not next(e for e in m["energie_zaehler"] if e["entity_id"] == "sensor.hausverbrauch")["passend"]
    assert [e["entity_id"] for e in m["energie_preise"]] == ["input_number.strompreis"] and m["energie_preise"][0]["passend"]
    assert m["energie_zeitstempel"][0]["entity_id"] == "sensor.fewo_vorheizstart" and m["energie_zeitstempel"][0]["passend"]


def test_statisch_gueltigkeit_logik():
    """v1.20.0: Code am Anreisetag, nächster Code ab Starttag, Nachrücken."""
    from custom_components.smoobu.tuercode import static_end, static_for, static_rollover

    cfg = {"modus": "statisch", "code": "4711", "ab": "2026-01-01", "bis": "2026-11-30"}
    assert static_for(cfg, "2025-12-31") is None and static_for(cfg, "2026-11-30") == "4711" and static_for(cfg, "2026-12-01") is None
    assert static_end(cfg) == "2026-11-30"
    cfg2 = {"modus": "statisch", "code": "4711", "naechster_code": "9876", "naechster_ab": "2026-12-01"}  # aktueller ohne „bis“
    assert static_for(cfg2, "2026-11-30") == "4711" and static_for(cfg2, "2027-05-01") == "9876" and static_end(cfg2) is None
    assert static_rollover(cfg2, "2026-11-30") is None
    assert static_rollover({**cfg2, "typ": "kein", "naechster_bis": "2027-03-31"}, "2026-12-01") == \
        {"typ": "kein", "modus": "statisch", "code": "9876", "ab": "2026-12-01", "bis": "2027-03-31"}


async def test_statisch_gueltig_und_naechster(hass, setup, aioclient_mock, hass_ws_client):  # noqa: F811
    """v1.20.0: statischer Code mit Gültigkeit + nächster Code; Buchung ohne gültigen Code → „fehlt“ + Hinweis;
    Erinnerung vor Ablauf; Nachrücken am Starttag ohne Neuladen; Prüfung in den Einstellungen."""
    from custom_components.smoobu import settings

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    aioclient_mock.put(f"{BASE}/api/reservations/1", json={})
    aioclient_mock.put(f"{BASE}/api/reservations/2", json={})

    def check(cfg):
        return settings.validate(hass, entry, {"door_locks": {"123": {"typ": "kein", "modus": "statisch", "code": "4711", **cfg}}}, None)

    assert check({"ab": "2026-12-01", "bis": "2026-11-01"})[1]["door_locks"] == "invalid_static_dates"
    assert check({"bis": "2026-11-30", "naechster_code": "9876", "naechster_ab": "2026-11-30"})[1]["door_locks"] == "invalid_static_dates"
    assert check({"naechster_code": "9876"})[1]["door_locks"] == "invalid_static_dates"  # „ab“ Pflicht
    assert check({"naechster_code": "98", "naechster_ab": "2026-12-01"})[1]["door_locks"] == "invalid_static_code"
    vals, err = check({"ab": "", "bis": "2026-11-17", "naechster_code": " 9876 ", "naechster_ab": "2026-11-18", "naechster_bis": ""})
    assert not err and vals["door_locks"]["123"] == {"typ": "kein", "modus": "statisch", "code": "4711", "bis": "2026-11-17",
                                                     "naechster_code": "9876", "naechster_ab": "2026-11-18"}

    # Buchung 1 reist 13.11. an (alter Code), Buchung 2 am 18.11. (nächster Code)
    hass.config_entries.async_update_entry(entry, options={**entry.options, "door_code_enabled": True, "door_locks": vals["door_locks"]})
    await hass.async_block_till_done()
    doors = entry.runtime_data.doorcodes
    await doors.async_sync()
    assert doors.for_booking(1)["code"] == "4711" and doors.for_booking(2)["code"] == "9876" and doors.hints() == []
    assert "9876" in doors.known_codes()

    # Kein nächster Code → Buchung 2 ohne Code („fehlt“, Notizzeile weg, Platzhalter „Code folgt“) + Erinnerung
    hass.config_entries.async_update_entry(entry, options={**entry.options, "door_locks": {"123": {"typ": "kein", "modus": "statisch",
                                                                                                    "code": "4711", "bis": "2026-11-17"}}})
    await hass.async_block_till_done()
    doors = entry.runtime_data.doorcodes
    await doors.async_sync()
    b2 = doors.for_booking(2)
    assert b2["status"] == "fehlt" and b2["code"] is None and doors.code_for_send(2) is None
    arts = sorted(h["art"] for h in doors.hints())
    assert arts == ["code_fehlt", "code_laeuft_ab"] and len(doors.pushed) == 2
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/doorcode/tasks", "apartment_id": "alle"})
    res = await ws.receive_json()
    assert {a["art"] for a in res["result"]["aufgaben"]} == {"code_fehlt", "code_laeuft_ab"}
    await doors.async_sync()
    assert len(doors.pushed) == 2  # je Hinweis nur einmal

    # Nächster Code ab heute → rückt nach, ohne Neuladen; Buchung 2 bekommt ihn, Hinweise weg
    hass.config_entries.async_update_entry(entry, options={**entry.options, "door_locks": {"123": {
        "typ": "kein", "modus": "statisch", "code": "4711", "bis": "2026-11-14", "naechster_code": "5308", "naechster_ab": "2026-11-15"}}})
    await hass.async_block_till_done()
    doors = entry.runtime_data.doorcodes
    await doors.async_sync()
    await hass.async_block_till_done()
    assert entry.runtime_data.doorcodes is doors  # kein Neuladen
    assert entry.options["door_locks"]["123"] == {"typ": "kein", "modus": "statisch", "code": "5308", "ab": "2026-11-15"}
    await doors.async_sync()
    # Buchung 2 bekommt den neuen Code; Buchung 1 ist schon da (Anreise 13.11.) und behält ihren
    assert doors.for_booking(2)["code"] == "5308" and doors.for_booking(1)["code"] == "4711"
    assert doors.hints() == [] and doors.pushed == []

"""v1.19.0: Rollenkonfigurator, Rolle „Reinigung“ (nur Vorname) und Reinigungsboard mit Zuweisung und Statistik."""
from datetime import date
from types import SimpleNamespace

from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.smoobu import rechte
from custom_components.smoobu.const import DOMAIN
from custom_components.smoobu.reinigung import build

from .test_smoobu import setup  # noqa: F401  (Fixture)


async def _call(ws, msg_id, **msg):
    await ws.send_json({"id": msg_id, **msg})
    return await ws.receive_json()


def _rec(rid, an, ab, **kw):
    return {"id": rid, "wohnung_id": 1, "anreise": an, "abreise": ab, "blockiert": False, "storniert": False,
            "vorname": f"G{rid}", "personen": 2, "hund": False, "naechte": 2, "check_in": None, "check_out": None, **kw}


def test_build_wechsel_und_naechste():
    recs = [_rec(1, "2026-11-10", "2026-11-12", check_out="10:00"), _rec(2, "2026-11-12", "2026-11-14", hund=True, check_in="15:00"),
            _rec(3, "2026-11-20", "2026-11-22", blockiert=True), _rec(4, "2026-11-13", "2026-11-14", storniert=True)]
    items = build(recs, {"default_checkout": "11:00"}, date(2026, 11, 11))
    assert [x["key"] for x in items] == ["1:2026-11-12", "2:2026-11-14"]  # Sperre und Storno ohne Reinigung
    a, b = items
    assert a["wechsel"] and a["check_out"] == "10:00" and a["naechste"]["check_in"] == "15:00" and a["naechste"]["hund"]
    assert not b["wechsel"] and b["naechste"]["sperre"] and b["naechste"]["vorname"] is None


def test_rollen_konfigurierbar():
    u = SimpleNamespace(id="u", is_admin=False)
    # Standard unverändert; „gaeste“ schließt „belegung_sehen“ ein
    assert rechte.rights_of(u, {"user_roles": {"u": "lesen"}}) == rechte.ROLES["lesen"][1]
    opts = {"user_roles": {"u": "lesen"}, "role_rights": {"lesen": ["gaeste"], "kein": ["finanzen"]}}
    assert rechte.rights_of(u, opts) == {"gaeste", "belegung_sehen"}
    assert rechte.roles(opts)["kein"]["rechte"] == frozenset()  # fest
    # Eigene Rolle; gelöschte/unbekannte Rolle → Standardrolle
    opts = {"user_roles": {"u": "eigen_x"}, "custom_roles": {"eigen_x": {"name": "Hausmeister", "rechte": ["reinigung", "foo"]}}}
    assert rechte.rights_of(u, opts) == {"reinigung"} and rechte.describe(u, opts)["rolle_name"] == "Hausmeister"
    assert rechte.role_of(u, {"user_roles": {"u": "eigen_weg"}}) == "betrieb"
    assert rechte.hints(["preise", "finanzen"]) == [{"recht": "preise", "fehlt": ["belegung_sehen"]}]


def test_strip_nur_vorname():
    item = {"id": 1, "gast": "Anna Beispiel", "vorname": "Anna", "email": "a@b", "telefon": "1", "notiz": "x", "brutto": 9, "hund": True}
    assert rechte.strip(item, rechte.ROLES["reinigung"][1]) == {"id": 1, "gast": "Anna", "vorname": "Anna", "hund": True}


async def test_rollen_speichern(hass, setup, hass_ws_client, hass_read_only_user, hass_read_only_access_token):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    ws = await hass_ws_client(hass)
    meta = (await _call(ws, 1, type="smoobu/settings/get"))["result"]
    werte = meta["werte"]
    assert "reinigung" in werte["role_rights"] and "kein" not in werte["role_rights"]
    # Eigene Rolle anlegen, Standardrolle anpassen, Benutzer zuweisen
    rr = {**werte["role_rights"], "lesen": ["belegung_sehen"], "betrieb": werte["role_rights"]["betrieb"]}
    res = (await _call(ws, 2, type="smoobu/settings/set", changes={
        "role_rights": rr, "custom_roles": {"eigen_abc": {"name": "Hausmeister", "rechte": ["reinigung", "belegung_sehen"]}},
        "user_roles": {hass_read_only_user.id: "eigen_abc"}}))["result"]
    await hass.async_block_till_done()
    assert res["ok"] is True, res
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.options["role_rights"] == {"lesen": ["belegung_sehen"]}  # nur Abweichungen gespeichert
    assert entry.options["user_roles"] == {hass_read_only_user.id: "eigen_abc"}
    # Doppelter Name abgelehnt
    res = (await _call(ws, 3, type="smoobu/settings/set", changes={"custom_roles": {"eigen_abc": {"name": "Verwalter", "rechte": []}}}))["result"]
    assert res["fehler"] == {"custom_roles": "duplicate_role_name"}
    # Eigene Rolle ist Standardrolle → Löschen abgelehnt
    await _call(ws, 4, type="smoobu/settings/set", changes={"default_role": "eigen_abc"})
    await hass.async_block_till_done()
    res = (await _call(ws, 5, type="smoobu/settings/set", changes={"custom_roles": {}}))["result"]
    assert res["fehler"] == {"default_role": "role_is_default"}
    # Löschen mit anderer Standardrolle: Benutzer fällt auf die Standardrolle zurück
    res = (await _call(ws, 6, type="smoobu/settings/set", changes={"custom_roles": {}, "default_role": "reinigung"}))["result"]
    await hass.async_block_till_done()
    assert res["ok"] is True
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert "custom_roles" not in entry.options and entry.options.get("user_roles") == {}
    # Nicht-Admin (Verwalter) darf Rollen nicht einstellen
    hass.config_entries.async_update_entry(entry, options={**entry.options, "user_roles": {hass_read_only_user.id: "verwalter"}})
    await hass.async_block_till_done()
    guest = await hass_ws_client(hass, hass_read_only_access_token)
    res = (await _call(guest, 1, type="smoobu/settings/set", changes={"role_rights": {**werte["role_rights"], "lesen": []}}))["result"]
    assert res["fehler"] == {"role_rights": "admin_only"}


async def test_rolle_reinigung_und_board(hass, setup, hass_ws_client, hass_read_only_user, hass_read_only_access_token):  # noqa: F811
    pushes = async_mock_service(hass, "notify", "mobile_app_putz")
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    hass.config_entries.async_update_entry(entry, options={**entry.options, "user_roles": {hass_read_only_user.id: "reinigung"},
                                                          "cleaning_phones": {hass_read_only_user.id: "notify.mobile_app_putz"}})
    await hass.async_block_till_done()
    cleaner = await hass_ws_client(hass, hass_read_only_access_token)
    admin = await hass_ws_client(hass)

    # Rolle Reinigung: Kalender/Übersicht mit Vorname, ohne Kontakt und Preise; Finanzen/Nachrichten gesperrt
    b = (await _call(cleaner, 1, type="smoobu/bookings"))["result"]["buchungen"]
    anna = next(x for x in b if x["id"] == 1)
    assert anna["gast"] == "Anna" and "email" not in anna and "brutto" not in anna
    assert (await _call(cleaner, 2, type="smoobu/booking", reservation_id=1))["result"]["smoobu"] == {}
    assert (await _call(cleaner, 3, type="smoobu/analytics"))["error"]["code"] == "unauthorized"
    assert (await _call(cleaner, 4, type="smoobu/message_status", reservation_ids=[1]))["error"]["code"] == "unauthorized"
    assert (await _call(cleaner, 5, type="smoobu/rates"))["success"] is True

    # Board: zwei Reinigungen (Abreise 16.11. und 21.11.), Reinigung darf nicht zuweisen
    r = (await _call(cleaner, 6, type="smoobu/cleaning/get"))["result"]
    keys = [x["key"] for x in r["reinigungen"]]
    assert keys == ["1:2026-11-16", "2:2026-11-21"] and r["darf_uebernehmen"] and not r["darf_zuweisen"] and r["benutzer"] == []
    assert r["reinigungen"][0]["vorname"] == "Anna"
    eid = entry.entry_id
    res = await _call(cleaner, 7, type="smoobu/cleaning/set", entry_id=eid, key=keys[0], aktion="zuweisen", benutzer_id="x")
    assert res["error"]["code"] == "unauthorized"
    # Admin weist zu → Push an das Handy der Reinigungskraft
    users = (await _call(admin, 8, type="smoobu/cleaning/get"))["result"]["benutzer"]
    assert hass_read_only_user.id in {u["id"] for u in users}
    res = await _call(admin, 9, type="smoobu/cleaning/set", entry_id=eid, key=keys[0], aktion="zuweisen", benutzer_id=hass_read_only_user.id)
    assert res["success"] is True
    await hass.async_block_till_done()
    assert len(pushes) == 1 and "Reinigung" in pushes[0].data["title"] and pushes[0].data["data"]["tag"] == f"smoobu_reinigung_{keys[0]}"
    # Reinigungskraft übernimmt die zweite selbst (kein Push), hakt die erste ab
    assert (await _call(cleaner, 10, type="smoobu/cleaning/set", entry_id=eid, key=keys[1], aktion="uebernehmen"))["success"]
    assert (await _call(cleaner, 11, type="smoobu/cleaning/set", entry_id=eid, key=keys[0], aktion="erledigt"))["success"]
    await hass.async_block_till_done()
    assert len(pushes) == 1
    r = (await _call(cleaner, 12, type="smoobu/cleaning/get"))["result"]["reinigungen"]
    assert r[0]["status"] == "erledigt" and r[1]["zugewiesen"] == hass_read_only_user.id
    # Ungültige Zuweisung (Benutzer ohne Recht „reinigung“): Admins haben es, unbekannte IDs nicht
    res = await _call(admin, 13, type="smoobu/cleaning/set", entry_id=eid, key=keys[1], aktion="zuweisen", benutzer_id="gibtsnicht")
    assert res["error"]["code"] == "invalid_user"

    # Statistik: Reinigung sieht sie nicht, Admin schon
    assert (await _call(cleaner, 14, type="smoobu/cleaning/stats", start="2026-11-01", end="2026-12-01"))["error"]["code"] == "unauthorized"
    st = (await _call(admin, 15, type="smoobu/cleaning/stats", start="2026-11-01", end="2026-12-01"))["result"]
    assert st["anzahl"] == 1 and st["personen"][0]["anzahl"] == 1 and st["personen"][0]["naechte"] == 3
    assert st["liste"][0]["datum"] == "2026-11-16" and st["monate"][0]["summe"] == 1

    # Vorabend-Erinnerung: offene, zugewiesene Reinigung von morgen → Push
    assert (await _call(admin, 16, type="smoobu/cleaning/set", entry_id=eid, key=keys[0], aktion="offen"))["success"]
    await entry.runtime_data.cleaning._remind(None)
    await hass.async_block_till_done()
    assert len(pushes) == 2 and "Morgen" in pushes[1].data["title"]

    # v1.19.0: Reinigungskosten = Standardzeit × Stundenlohn der Person (Board), sonst Standardlohn
    assert (await _call(cleaner, 17, type="smoobu/cleaning/set", entry_id=eid, key=keys[0], aktion="erledigt"))["success"]
    hass.config_entries.async_update_entry(entry, options={**entry.options, "cleaning_wages": {hass_read_only_user.id: 20.0},
                                                          "cost_cleaning": 17.0, "cost_cleaning_minutes": 90})
    await hass.async_block_till_done()
    c = entry.runtime_data
    await c.async_refresh()
    recs = {r["id"]: r for r in c.records_all()}
    assert recs[1]["reinigung_kosten"] == 30.0          # 90 min × 20 €/h (Person aus dem Board)
    assert recs[2]["reinigung_kosten"] == 30.0          # zugewiesen (noch offen) zählt ebenfalls
    await _call(admin2 := await hass_ws_client(hass), 2, type="smoobu/cleaning/set", entry_id=eid, key=keys[1], aktion="zuweisen", benutzer_id=None)
    await c.async_refresh()
    assert {r["id"]: r for r in c.records_all()}[2]["reinigung_kosten"] == 25.5  # 90 min × 17 €/h (Standard)
    st = (await _call(admin2, 3, type="smoobu/cleaning/stats", start="2026-11-01", end="2026-12-01"))["result"]
    assert st["kosten"] == 30.0 and st["personen"][0]["stundenlohn"] == 20.0

    # v1.19.0: tatsächliche Dauer je Reinigung buchen (statt Standard 90 min) → 75 min × 20 €/h = 25 €
    cleaner2 = await hass_ws_client(hass, hass_read_only_access_token)
    res = await _call(cleaner2, 1, type="smoobu/cleaning/set", entry_id=eid, key=keys[0], aktion="dauer", minuten=75)
    assert res["success"] and res["result"]["zustand"]["minuten"] == 75
    assert (await _call(cleaner2, 2, type="smoobu/cleaning/get"))["result"]["standard_minuten"] == 90
    await c.async_refresh()
    assert {r["id"]: r for r in c.records_all()}[1]["reinigung_kosten"] == 25.0
    st = (await _call(admin2, 4, type="smoobu/cleaning/stats", start="2026-11-01", end="2026-12-01"))["result"]
    assert st["kosten"] == 25.0 and st["minuten_gebucht"] == 1 and st["personen"][0]["minuten"] == 75
    # ungültig und Zurücksetzen auf Standard
    assert (await _call(cleaner2, 3, type="smoobu/cleaning/set", entry_id=eid, key=keys[0], aktion="dauer", minuten=0))["success"] is False
    res = await _call(cleaner2, 4, type="smoobu/cleaning/set", entry_id=eid, key=keys[0], aktion="dauer", minuten=None)
    assert "minuten" not in res["result"]["zustand"]
    # Korrektur 21.11.2026: Stundenlohn 0 €/h (z. B. Inhaber) gilt – nicht der Standardlohn
    hass.config_entries.async_update_entry(entry, options={**entry.options, "cleaning_wages": {hass_read_only_user.id: 0.0}})
    await hass.async_block_till_done()
    c = entry.runtime_data
    await c.async_refresh()
    assert {r["id"]: r for r in c.records_all()}[1]["reinigung_kosten"] == 0.0
    st = (await _call(admin2, 5, type="smoobu/cleaning/stats", start="2026-11-01", end="2026-12-01"))["result"]
    assert st["kosten"] == 0.0

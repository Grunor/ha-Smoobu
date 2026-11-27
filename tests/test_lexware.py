"""v1.20.0 (BETA): Lexware-Modul Ende zu Ende im Testmodus (Beispiel-Lexware, kein Netzverkehr)."""

from homeassistant.core import HomeAssistant

from custom_components.smoobu.const import DOMAIN

from .test_smoobu import BASE, setup  # noqa: F401  (Fixture)

RULES = {
    "direkt": [
        {"artikel": "demo-uebernachtung", "menge": "nacht", "preis": "rest"},
        {"artikel": "demo-person", "menge": "zusatzperson_nacht", "ab": 2, "preis": "artikel"},
        {"artikel": "demo-hund", "menge": "hund", "max": 2, "preis": "artikel"},
        {"artikel": "demo-kurz", "menge": "pauschal", "bedingung": "naechte_max", "wert": 14, "preis": "artikel"},
    ],
    "portal": [{"artikel": "demo-portal", "menge": "pauschal", "preis": "rest"}],
}


async def _call(ws, msg_id, **msg):
    await ws.send_json({"id": msg_id, **msg})
    return await ws.receive_json()


async def test_lexware_ablauf(hass: HomeAssistant, setup, aioclient_mock, hass_ws_client):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    ws = await hass_ws_client(hass)
    # Ohne Lexware: Status inaktiv
    res = await _call(ws, 1, type="smoobu/lexware/status", reservation_id=2)
    assert res["success"] and res["result"]["aktiv"] is False

    # Einschalten ohne Key und ohne Testmodus → Fehler; mit Testmodus ok
    res = await _call(ws, 2, type="smoobu/settings/set", entry_id=entry.entry_id, changes={"lexware_enabled": True})
    assert res["result"]["ok"] is False and res["result"]["fehler"]["lexware_api_key"] == "lexware_key_required"
    res = await _call(ws, 3, type="smoobu/settings/set", entry_id=entry.entry_id,
                      changes={"lexware_enabled": True, "lexware_mock": True, "lexware_rules": RULES})
    assert res["result"]["ok"] is True, res
    assert res["result"]["werte"]["lexware_api_key"] == "" and res["result"]["werte"]["lexware_api_key_gesetzt"] is False
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    lex = entry.runtime_data.lexware
    assert lex.enabled and lex.mock and len(lex.articles) == 7

    # Vorschau Direktbuchung (2 Erwachsene, 3 Nächte, Hund über Zusatzleistung, 450,50 €)
    res = await _call(ws, 4, type="smoobu/lexware/preview", entry_id=entry.entry_id, reservation_id=2)
    assert res["success"], res
    p = res["result"]
    assert p["gruppe"] == "direkt" and p["fehler"] == [] and p["summen"]["brutto"] == 450.5
    assert [x["menge"] for x in p["positionen"]] == [3, 3, 1, 1]
    assert p["kontakt"]["modus"] == "neu" and p["soll_anzahlung"] == 100.0  # Smoobu-Anzahlung hat Vorrang
    assert "payload" not in p

    # Firma ohne Namen → Fehler
    res = await _call(ws, 5, type="smoobu/lexware/preview", entry_id=entry.entry_id, reservation_id=2, overrides={"ist_firma": True})
    assert "firmenname_fehlt" in res["result"]["fehler"]

    # Entwurf erstellen
    res = await _call(ws, 6, type="smoobu/lexware/create", entry_id=entry.entry_id, reservation_id=2)
    assert res["success"], res
    iid = res["result"]["id"]
    assert res["result"]["link"].endswith(f"/permalink/invoices/edit/{iid}")
    inv = lex.client.invoices_data[iid]
    assert inv["voucherStatus"] == "draft" and inv["taxConditions"]["taxType"] == "gross"
    assert inv["address"]["contactId"] in lex.client.contacts_data
    # Doppelt verhindern
    res = await _call(ws, 7, type="smoobu/lexware/create", entry_id=entry.entry_id, reservation_id=2)
    assert not res["success"] and "schon eine Rechnung" in res["error"]["message"]

    # In Lexware finalisiert + Anzahlung zugeordnet → Status „anzahlung“, keine Änderung in Smoobu nötig
    aioclient_mock.put(f"{BASE}/api/reservations/2", json={})
    lex.client.finalize(iid, 450.5)
    lex.client.pay(iid, 225.25)
    res = await _call(ws, 8, type="smoobu/lexware/refresh", entry_id=entry.entry_id, reservation_id=2)
    assert res["result"]["stand"]["status"] == "anzahlung" and res["result"]["stand"]["offen"] == 225.25
    assert not [c for c in aioclient_mock.mock_calls if c[0] == "PUT"]

    # Rest bezahlt → Haken „bezahlt“ in Smoobu (Bedeutung Direkt = Zahlung laut Lexware)
    lex.client.pay(iid, 225.25)
    res = await _call(ws, 9, type="smoobu/lexware/refresh", entry_id=entry.entry_id, reservation_id=2)
    assert res["result"]["stand"]["status"] == "bezahlt"
    puts = [c for c in aioclient_mock.mock_calls if c[0] == "PUT"]
    assert puts and puts[-1][2] == b'{"priceStatus":1}'

    # Aufgaben: nur Buchungen mit Anreise ab Aktivierung (keine Altlasten) …
    res = await _call(ws, 10, type="smoobu/lexware/tasks", entry_id=entry.entry_id)
    assert res["result"]["aufgaben"] == []
    # … Buchung 1 (Airbnb, läuft) ohne Rechnung → „rechnung_fehlt“, sobald sie nach der Aktivierung anreist
    lex.data["aktiv_seit"] = "2026-11-01"
    res = await _call(ws, 11, type="smoobu/lexware/tasks", entry_id=entry.entry_id)
    arten = {(t["buchung_id"], t["art"]) for t in res["result"]["aufgaben"]}
    assert (1, "rechnung_fehlt") in arten and not any(b == 2 for b, _a in arten)

    # Verbindungstest im Testmodus
    res = await _call(ws, 12, type="smoobu/lexware/test", entry_id=entry.entry_id)
    assert res["result"]["ok"] and res["result"]["testmodus"] and len(res["result"]["artikel"]) == 7

"""v1.18.0: Umbuchen (Zeitraum/Unterkunft) – Prüfung, Konflikte, Preisvorschlag, Abgleich mit Smoobu."""
from datetime import date

from custom_components.smoobu import umbuchung as u

from .test_smoobu import setup  # noqa: F401  (Fixture)

TODAY = date(2026, 11, 20)


def rec(i, a, b, apt=1, **kw):
    return {"id": i, "anreise": a, "abreise": b, "wohnung_id": apt, "naechte": (date.fromisoformat(b) - date.fromisoformat(a)).days,
            "gruppe": "Direkt", "blockiert": False, "storniert": False, "brutto": 300.0, "gast": "Max", **kw}


def test_check_rules():
    r = rec(1, "2026-12-01", "2026-12-04")
    assert u.check(r, [], "2026-12-02", "2026-12-05", 1, TODAY) == []
    assert "portal" in u.check({**r, "gruppe": "Portal"}, [], "2026-12-02", "2026-12-05", 1, TODAY)
    assert "zeitraum" in u.check(r, [], "2026-12-05", "2026-12-05", 1, TODAY)
    assert "anreise_vergangen" in u.check(r, [], "2026-11-10", "2026-11-12", 1, TODAY)
    # laufender Aufenthalt: Anreise bleibt, Verlängerung erlaubt
    run = rec(2, "2026-11-18", "2026-11-21")
    assert u.check(run, [], "2026-11-18", "2026-11-24", 1, TODAY) == []
    assert "vergangen" in u.check(rec(3, "2026-11-01", "2026-11-03"), [], "2026-12-01", "2026-12-03", 1, TODAY)


def test_conflicts_exclude_self_and_cancelled():
    r = rec(1, "2026-12-01", "2026-12-04")
    others = [r, rec(2, "2026-12-04", "2026-12-06"), rec(3, "2026-12-05", "2026-12-08", blockiert=True),
              rec(4, "2026-12-05", "2026-12-07", storniert=True)]
    assert u.conflicts(r, others, "2026-12-02", "2026-12-04") == []           # Abreise = Anreise der nächsten: ok
    hit = u.conflicts(r, others, "2026-12-03", "2026-12-06")
    assert [h["id"] for h in hit] == [2, 3] and hit[1]["blockiert"] and hit[1]["gast"] is None


def test_price_suggestion():
    r = rec(1, "2026-12-01", "2026-12-04")  # 3 Nächte, 300 € (inkl. Reinigung)
    old = {d: {"price": 80} for d in ("2026-12-01", "2026-12-02", "2026-12-03")}
    new = {d: {"price": 90} for d in ("2026-12-10", "2026-12-11", "2026-12-12", "2026-12-13")}
    s = u.price_suggestion(r, "2026-12-10", "2026-12-14", 1, old, new)
    assert s["basis"] == "tagespreise" and s["preis_vorschlag"] == 300 + 360 - 240
    # alte Tagespreise fehlen → anteilig
    s2 = u.price_suggestion(r, "2026-12-10", "2026-12-14", 1, {}, new)
    assert s2["basis"] == "anteilig" and s2["preis_vorschlag"] == 400.0
    assert u.price_suggestion(r, "2026-12-01", "2026-12-04", 1, old, old)["preis_vorschlag"] is None
    assert u.min_stay_hint({"2026-12-10": {"min_length_of_stay": 5}}, "2026-12-10", "2026-12-14") == 5


def test_verify():
    raw = {"arrival": "2026-12-10", "departure": "2026-12-14", "apartment": {"id": 2}}
    assert u.verify(raw, "2026-12-10", "2026-12-14", 2)["ok"]
    bad = u.verify({**raw, "arrival": "2026-12-01"}, "2026-12-10", "2026-12-14", 2)
    assert not bad["ok"] and bad["smoobu"]["anreise"] == "2026-12-01"


async def test_websocket_umbuchen(hass, setup, hass_ws_client, aioclient_mock):  # noqa: F811
    """Probelauf, Umbuchen mit Kontrolle, Smoobu ignoriert die Änderung → klare Meldung, kein Preis."""
    import re  # noqa: PLC0415

    from homeassistant.util import dt as dt_util  # noqa: PLC0415

    from .test_smoobu import BASE  # noqa: PLC0415

    c = hass.config_entries.async_get_entry(setup.entry_id).runtime_data
    today = dt_util.now().date().isoformat()
    r = next(x for x in c.records_all() if x["gruppe"] == "Direkt" and not x["blockiert"] and not x["storniert"] and x["anreise"] > today)
    apt = r["wohnung_id"]
    # freien Zeitraum in derselben Wohnung finden (2 Nächte)
    from datetime import date as d_, timedelta  # noqa: PLC0415
    busy = [(x["anreise"], x["abreise"]) for x in c.records(apt) if not x["storniert"] and x["id"] != r["id"]]
    a = d_.fromisoformat(r["anreise"]) + timedelta(days=1)
    while any(s < (a + timedelta(days=2)).isoformat() and e > a.isoformat() for s, e in busy):
        a += timedelta(days=1)
    arr, dep = a.isoformat(), (a + timedelta(days=2)).isoformat()
    aioclient_mock.clear_requests()  # Mocks der Grundeinrichtung würden die Buchungsabfrage zuerst beantworten
    aioclient_mock.get(re.compile(rf"{re.escape(BASE)}/api/rates.*"), json={"data": {}})
    aioclient_mock.put(f"{BASE}/api/reservations/{r['id']}", json={"id": r["id"]})
    aioclient_mock.get(f"{BASE}/api/reservations/{r['id']}", json={"id": r["id"], "arrival": arr, "departure": dep, "apartment": {"id": apt}})
    c.async_request_refresh = lambda: __import__("asyncio").sleep(0)  # kein Voll-Abgleich gegen die Mocks
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/booking/move", "reservation_id": r["id"], "anreise": arr, "abreise": dep})
    msg = await ws.receive_json()
    dry = msg.get("result")
    assert dry and dry["moeglich"], msg
    assert dry["naechte"] == 2 and dry["gespeichert"] is False and dry["preis_vorschlag"] is not None
    assert not [x for x in aioclient_mock.mock_calls if x[0] == "PUT"]
    await ws.send_json({"id": 2, "type": "smoobu/booking/move", "reservation_id": r["id"], "anreise": arr, "abreise": dep,
                        "dry_run": False, "preis": 199})
    res = (await ws.receive_json())["result"]
    puts = [x for x in aioclient_mock.mock_calls if x[0] == "PUT"]
    assert res["gespeichert"] and res["preis_gespeichert"] and len(puts) == 2, (res, puts)
    import json  # noqa: PLC0415
    body = lambda x: json.loads(x[2]) if isinstance(x[2], (bytes, str)) else x[2]  # noqa: E731
    assert body(puts[0]) == {"arrivalDate": arr, "departureDate": dep} and body(puts[1]) == {"price": 199.0}
    # Smoobu ignoriert die Änderung → nicht übernommen, Preis wird NICHT gesendet
    aioclient_mock.clear_requests()
    aioclient_mock.get(re.compile(rf"{re.escape(BASE)}/api/rates.*"), json={"data": {}})
    aioclient_mock.put(f"{BASE}/api/reservations/{r['id']}", json={"id": r["id"]})
    aioclient_mock.get(f"{BASE}/api/reservations/{r['id']}", json={"id": r["id"], "arrival": r["anreise"], "departure": r["abreise"], "apartment": {"id": apt}})
    await ws.send_json({"id": 3, "type": "smoobu/booking/move", "reservation_id": r["id"], "anreise": arr, "abreise": dep,
                        "dry_run": False, "preis": 250})
    res = (await ws.receive_json())["result"]
    assert res["nicht_uebernommen"] and not res["gespeichert"] and res["smoobu"]["anreise"] == r["anreise"]
    assert len([x for x in aioclient_mock.mock_calls if x[0] == "PUT"]) == 1

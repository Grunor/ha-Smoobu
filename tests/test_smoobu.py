"""End-to-End-Test der Smoobu-Integration mit gemockter API."""
import re
from datetime import date, timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from custom_components.smoobu.const import DOMAIN

BASE = "https://login.smoobu.com"
TODAY = date(2026, 11, 15)


def d(days):
    return (TODAY + timedelta(days=days)).isoformat()


BOOKINGS = [
    {  # laufend, keine Check-in-Zeit → 16:00 / 11:00
        "id": 1, "reference-id": "HMX1", "type": "reservation", "arrival": d(-2), "departure": d(1),
        "apartment": {"id": 123, "name": "Ferienwohnung"}, "channel": {"id": 1, "name": "Airbnb"},
        "guest-name": "Anna Beispiel", "email": "a@b.de", "phone": "+49", "adults": 2, "children": 1,
        "check-in": None, "check-out": None, "price": 300, "price-paid": "Yes",
        "is-blocked-booking": False, "modifiedAt": "2026-11-01 10:00",
    },
    {  # nächste, mit Check-in 20:00, unbezahlt
        "id": 2, "arrival": d(3), "departure": d(6), "apartment": {"id": 123, "name": "Ferienwohnung"},
        "channel": {"id": 2, "name": "Direct booking"}, "guest-name": "Max Mustermann", "adults": 2,
        "children": 0, "check-in": "20:00", "check-out": "10:00", "price": 450.5, "price-paid": "No",
        "prepayment": 100, "prepayment-paid": "Yes",
        "priceElements": [{"id": 9, "type": "addon", "name": "Endreinigung 1 Hund", "amount": 15}],
        "is-blocked-booking": False, "modifiedAt": "2026-11-02 10:00",
    },
    {  # blockiert
        "id": 3, "arrival": d(10), "departure": d(12), "apartment": {"id": 123, "name": "Ferienwohnung"},
        "channel": {"id": 3, "name": "Blocked"}, "guest-name": "", "adults": 0, "children": 0,
        "is-blocked-booking": True, "modifiedAt": "2026-11-03 10:00",
    },
]


def mock_api(aioclient_mock):
    aioclient_mock.get(f"{BASE}/api/me", json={"id": 999, "firstName": "Max", "lastName": "Host", "email": "x@y"})
    aioclient_mock.get(f"{BASE}/api/apartments", json={"apartments": [{"id": 123, "name": "Ferienwohnung"}]})
    aioclient_mock.get(f"{BASE}/api/apartments/123", json={"id": 123, "currency": "EUR", "rooms": {"maxOccupancy": 4}})
    aioclient_mock.get(f"{BASE}/api/reservations/1", json={**BOOKINGS[0], "firstname": "Anna", "lastname": "Beispiel", "city-tax": 7.5})
    aioclient_mock.get(f"{BASE}/api/reservations/2", json={**BOOKINGS[1], "firstname": "Max", "lastname": "Mustermann"})
    aioclient_mock.get(f"{BASE}/api/reservations", json={"page_count": 1, "page_size": 100, "total_items": 3, "page": 1, "bookings": BOOKINGS})
    aioclient_mock.get(f"{BASE}/api/users/webhooks", json={"webhooks": []})
    aioclient_mock.post(f"{BASE}/api/users/webhooks", json={"id": 77, "webhookUrl": "x"}, status=201)
    aioclient_mock.get(f"{BASE}/api/reservations/2/messages", json={"page_count": 1, "messages": [{"id": 5, "subject": "Hi", "message": "Hallo"}]})
    aioclient_mock.post(f"{BASE}/api/reservations/2/messages/send-message-to-guest", status=201, text="")


@pytest.fixture
async def setup(hass: HomeAssistant, aioclient_mock, freezer: FrozenDateTimeFactory):
    await hass.config.async_set_time_zone("Europe/Berlin")
    hass.config.language = "de"
    hass.config.external_url = "https://example.duckdns.org"
    freezer.move_to("2026-11-15T11:00:00+00:00")  # 12:00 lokal
    await async_setup_component(hass, "http", {})
    mock_api(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, unique_id="999", title="Max Host",
                            data={"api_key": "k", "api_secret": "s", "user_id": 999})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_entities(hass, setup, aioclient_mock):
    ents = sorted(e.entity_id for e in er.async_entries_for_config_entry(er.async_get(hass), setup.entry_id))
    print("\n".join(ents))
    for eid in ents:
        st = hass.states.get(eid)
        print(eid, "=", st.state if st else None)

    def s(suffix):
        # Sensoren zuerst (Binärsensor „Hund aktueller Gast“ endet ebenfalls auf aktueller_gast)
        matches = sorted((e for e in ents if e.endswith(suffix)), key=lambda e: not e.startswith("sensor."))
        assert matches, suffix
        return hass.states.get(matches[0])

    assert s("aktueller_gast").state == "Anna Beispiel"
    assert s("aktueller_gast").attributes["vorname"] == "Anna"
    assert s("aktueller_gast").attributes["kurtaxe"] == 7.5
    assert s("aktueller_vorname").state == "Anna"
    assert s("aktuelle_personen").state == "3"
    assert s("nachster_gast").state == "Max Mustermann"
    assert s("nachste_anreise").state == "2026-11-18T19:00:00+00:00"
    assert s("nachste_abreise").state == "2026-11-16T10:00:00+00:00"
    assert s("binary_sensor.smoobu_ferienwohnung_belegt").state == "on"
    assert s("anreise_heute").state == "off"
    assert s("offene_zahlungen").state == "1"
    assert s("buchungen_30_tage").state == "1"
    assert s("gastdaten_fehlen").state == "off"
    cal = s("calendar.smoobu_ferienwohnung_belegung")
    assert cal.state == "on" and cal.attributes["message"] == "Anna Beispiel"

    # Signatur-Header vorhanden
    _, url, _, headers = aioclient_mock.mock_calls[0]
    assert {"X-API-Key", "X-Timestamp", "X-Nonce", "X-Signature"} <= set(headers)
    assert any("departureFrom=" in str(c[1]) for c in aioclient_mock.mock_calls)
    # Webhook registriert
    assert setup.data["smoobu_webhook_id"] == 77
    assert setup.data["cloudhook_url"].startswith("https://example.duckdns.org/api/webhook/")
    assert hass.states.get("sensor.smoobu_webhook").state == "registriert"


async def test_calendar_events(hass, setup):
    resp = await hass.services.async_call(
        "calendar", "get_events",
        {"entity_id": "calendar.smoobu_ferienwohnung_belegung", "start_date_time": "2026-11-14 00:00:00", "end_date_time": "2026-12-01 00:00:00"},
        blocking=True, return_response=True)
    events = resp["calendar.smoobu_ferienwohnung_belegung"]["events"]
    print(events)
    assert [e["summary"] for e in events] == ["Anna Beispiel", "Max Mustermann 🐕", "Blockiert"]
    assert events[1]["start"] == "2026-11-18T20:00:00+01:00"


async def test_time_passes(hass, setup, freezer):
    # Nach Check-out 11:00 am 16.11. → frei
    freezer.move_to("2026-11-16T10:30:00+00:00")
    from pytest_homeassistant_custom_component.common import async_fire_time_changed
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.smoobu_ferienwohnung_belegt").state == "off"
    assert hass.states.get("binary_sensor.smoobu_ferienwohnung_abreise_heute").state == "on"


async def test_webhook(hass, setup, hass_client_no_auth, aioclient_mock):
    events = []
    hass.bus.async_listen("smoobu_event", lambda e: events.append(e))
    client = await hass_client_no_auth()
    wid = setup.data["webhook_id"]
    before = aioclient_mock.call_count
    r = await client.post(f"/api/webhook/{wid}", json={"action": "newReservation", "user": 999, "data": BOOKINGS[1]})
    assert r.status == 200
    await hass.async_block_till_done()
    assert events and events[0].data["action"] == "newReservation"
    assert events[0].data["guest_name"] == "Max Mustermann"
    assert aioclient_mock.call_count > before  # Refresh ausgelöst
    assert hass.states.get("sensor.smoobu_letztes_ereignis").state == "newReservation"
    r = await client.post(f"/api/webhook/{wid}", json={"action": "newReservation", "user": 1, "data": {}})
    assert r.status == 403


async def test_services(hass, setup, aioclient_mock):
    r = await hass.services.async_call(DOMAIN, "get_reservations", {"arrival_from": "2026-11-01"}, blocking=True, return_response=True)
    assert r["count"] == 3
    r = await hass.services.async_call(DOMAIN, "get_messages", {"reservation_id": 2}, blocking=True, return_response=True)
    assert r["messages"][0]["message"] == "Hallo"
    await hass.services.async_call(DOMAIN, "send_message", {"reservation_id": 2, "message": "Willkommen"}, blocking=True)
    call = [c for c in aioclient_mock.mock_calls if "send-message" in str(c[1])][0]
    assert b"Willkommen" in call[2]


async def test_config_flow(hass, aioclient_mock):
    mock_api(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "form"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": "k", "api_secret": "s"})
    assert result["type"] == "create_entry", result
    assert result["title"] == "Max Host"
    assert result["data"]["user_id"] == 999


async def test_auth_error(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/api/apartments", status=401, text="bad sig")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": "k", "api_secret": "s"})
    assert result["errors"] == {"base": "invalid_auth"}


async def test_options_and_unload(hass, setup):
    result = await hass.config_entries.options.async_init(setup.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {
        "scan_interval": 5, "use_webhook": True, "default_checkin": "15:00:00", "default_checkout": "11:00:00",
        "days_back": 30, "days_ahead": 365, "enrich_count": 3})
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    assert setup.options["default_checkin"] == "15:00"
    assert await hass.config_entries.async_unload(setup.entry_id)


async def test_diagnostics(hass, setup):
    from custom_components.smoobu.diagnostics import async_get_config_entry_diagnostics
    diag = await async_get_config_entry_diagnostics(hass, setup)
    assert "Anna" not in str(diag)


async def test_checkout_buffer(hass, setup, freezer):
    """Abreisezeit aus Smoobu + Puffer, ohne Zeit Standard-Check-out."""
    hass.config_entries.async_update_entry(setup, options={
        "scan_interval": 10, "use_webhook": True, "default_checkin": "16:00", "default_checkout": "11:30",
        "days_back": 30, "days_ahead": 365, "enrich_count": 3, "checkout_buffer": 60})
    await hass.async_block_till_done()
    # Buchung 1 ohne Abreisezeit → frei ab 11:30 am 16.11.
    st = hass.states.get("sensor.smoobu_ferienwohnung_nachste_abreise")
    assert st.state == "2026-11-16T10:30:00+00:00", st.state
    # Buchung 2 hat check-out 10:00 → Freigabe 11:00 (lokal) am 21.11.
    attrs = hass.states.get("sensor.smoobu_ferienwohnung_nachster_gast").attributes
    assert attrs["freigabe"] == "2026-11-21T11:00:00+01:00", attrs["freigabe"]
    assert attrs["abreise"] == "2026-11-21T10:00:00+01:00"


async def test_dog_and_payments(hass, setup):
    """Hunde-Erkennung über Preiselement/Notiz, offene Zahlungen ohne Portal-Kanäle."""
    assert hass.states.get("binary_sensor.smoobu_ferienwohnung_hund_nachster_gast").state == "on"
    assert hass.states.get("binary_sensor.smoobu_ferienwohnung_hund_aktueller_gast").state == "off"
    attrs = hass.states.get("binary_sensor.smoobu_ferienwohnung_hund_nachster_gast").attributes
    assert attrs["hund_hinweis"] == "Zusatzleistung: Endreinigung 1 Hund"
    st = hass.states.get("sensor.smoobu_ferienwohnung_offene_zahlungen")
    assert st.state == "1"
    assert st.attributes["offener_betrag"] == 350.5


def test_pet_hint_notice():
    from custom_components.smoobu.models import pet_hint
    assert pet_hint({"notice": "Wir kommen mit unserem Hund (Cocker Spaniel)"}).startswith("Notiz:")
    assert pet_hint({"notice": "Peter und Petra kommen"}) is None
    assert pet_hint({"notice": "We bring our dog"}) is not None


async def test_price_and_revenue(hass, setup):
    """Preis-Sensoren und Umsatz anteilig nach Nächten."""
    st = hass.states.get("sensor.smoobu_ferienwohnung_preis_aktueller_gast")
    assert float(st.state) == 300.0
    assert st.attributes["preis_pro_nacht"] == 100.0
    nx = hass.states.get("sensor.smoobu_ferienwohnung_preis_nachster_gast")
    assert float(nx.state) == 450.5
    assert nx.attributes["aufschluesselung"][0]["name"] == "Endreinigung 1 Hund"
    # Buchung 1: 13.11.–16.11. (300 €), Buchung 2: 18.11.–21.11. (450,50 €) → alles November
    m = hass.states.get("sensor.smoobu_ferienwohnung_umsatz_monat")
    assert float(m.state) == 750.5
    assert m.attributes["davon_bis_heute"] == 200.0  # Nächte 13. + 14.11.
    y = hass.states.get("sensor.smoobu_ferienwohnung_umsatz_jahr")
    assert float(y.state) == 750.5
    assert y.attributes["monate"] == {"2026-11": 750.5}


def test_revenue_split():
    from custom_components.smoobu.models import revenue_by_month
    r = revenue_by_month([{"arrival": "2026-12-27", "departure": "2027-01-06", "price": 552.6}])
    assert r == {"2026-12": 276.3, "2027-01": 276.3}

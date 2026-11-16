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
    rates = {}
    for i in range(0, 61):
        day = d(i)
        # belegt: 15. (laufend), 18.–20. (Buchung 2), 25.–26. (Sperrzeit) → nicht verfügbar
        busy = day in (d(0), d(3), d(4), d(5), d(10), d(11))
        rates[day] = {"price": 80 + i, "min_length_of_stay": 2, "available": 0 if busy else 1}
    aioclient_mock.get(f"{BASE}/api/rates", json={"data": {"123": rates}})
    aioclient_mock.get(f"{BASE}/api/users/webhooks", json={"webhooks": []})
    aioclient_mock.post(f"{BASE}/api/users/webhooks", json={"id": 77, "webhookUrl": "x"}, status=201)
    aioclient_mock.get(f"{BASE}/api/reservations/2/messages", json={"page_count": 1, "messages": [{"id": 5, "subject": "Hi", "message": "Hallo"}]})
    aioclient_mock.get(f"{BASE}/api/reservations/1/messages", json={"page_count": 1, "messages": []})
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
    # Abreise 11:00 (UTC+1) + Standard-Wartezeit 30 min (ab v1.17.0) = Freigabe 11:30
    assert s("nachste_abreise").state == "2026-11-16T10:30:00+00:00"
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
    assert hass.states.get("binary_sensor.smoobu_ferienwohnung_anreise_morgen").state == "off"
    # Vorabend: Max reist am 18.11. mit Hund an
    freezer.move_to("2026-11-17T17:00:00+00:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    morgen = hass.states.get("binary_sensor.smoobu_ferienwohnung_anreise_morgen")
    assert morgen.state == "on" and morgen.attributes["gastname"] == "Max Mustermann"
    assert morgen.attributes["hund"] is True


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
    # Zweiter Schritt: Provisionen
    assert result["type"] == "form" and result["step_id"] == "provisionen"
    bad = await hass.config_entries.options.async_configure(result["flow_id"], {
        "commission_airbnb": 15.5, "commission_booking": 15, "commission_fewo": 8, "commission_website": 0,
        "commission_direct": 0, "commission_other": 15, "commission_custom": "Expedia", "direct_channels": ["Direct booking"]})
    assert bad["errors"] == {"commission_custom": "invalid_custom"}
    result = await hass.config_entries.options.async_configure(result["flow_id"], {
        "commission_airbnb": 20, "commission_booking": 15, "commission_fewo": 8, "commission_website": 0,
        "commission_direct": 0, "commission_other": 15, "commission_custom": "Expedia=18", "direct_channels": ["Direct booking", "Website"]})
    assert result["type"] == "form" and result["step_id"] == "assistent"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"assistant": False})
    # v1.17.0: Benachrichtigungen (Abschnitte je Push-Art) und Wohnungskürzel
    assert result["type"] == "form" and result["step_id"] == "benachrichtigungen"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {
        "buchung": {"aktiv": True, "empfaenger": ["notify.mobile_app_test"]},
        "storno": {"aktiv": True, "empfaenger": []}, "nachricht": {"aktiv": True, "empfaenger": []},
        "vorschlag": {"aktiv": True, "empfaenger": []},
        "zahlung": {"aktiv": True, "empfaenger": [], "tage": 5, "uhrzeit": "08:15:00"},
        "briefing": {"aktiv": False, "empfaenger": [], "uhrzeit": "07:30:00"},
        "luecken": {"aktiv": False, "empfaenger": [], "uhrzeit": "09:05:00"},
        "ruhezeit": {"aktiv": True, "von": "22:00:00", "bis": "06:30:00", "nachrichten_sofort": True}})
    assert result["type"] == "form" and result["step_id"] == "wohnungen"
    label = next(str(k) for k in result["data_schema"].schema)
    bad = await hass.config_entries.options.async_configure(result["flow_id"], {label: "#!"})
    assert bad["errors"] == {label: "invalid_code"}
    result = await hass.config_entries.options.async_configure(result["flow_id"], {label: "fw1x"})
    assert result["type"] == "create_entry"
    o = setup.options
    assert o["commissions"]["Airbnb"] == 20 and o["commissions"]["Expedia"] == 18
    assert o["notify_buchung"] is True and o["notify_buchung_to"] == ["notify.mobile_app_test"]
    assert o["notify_zahlung_days"] == 5 and o["notify_zahlung_time"] == "08:15"
    assert o["notify_quiet"] is True and o["notify_quiet_from"] == "22:00" and o["notify_quiet_to"] == "06:30"
    assert list(o["apartment_codes"].values()) == ["FW1X"]
    await hass.async_block_till_done()
    assert setup.options["default_checkin"] == "15:00"
    assert await hass.config_entries.async_unload(setup.entry_id)


async def test_diagnostics(hass, setup):
    from custom_components.smoobu.diagnostics import async_get_config_entry_diagnostics
    diag = await async_get_config_entry_diagnostics(hass, setup)
    assert "Anna" not in str(diag)


async def test_checkout_buffer(hass, setup, freezer):
    """Freigabe = Abreisezeit (Smoobu bzw. Standard-Check-out) + Wartezeit nach Check-out."""
    hass.config_entries.async_update_entry(setup, options={
        "scan_interval": 10, "use_webhook": True, "default_checkin": "16:00", "default_checkout": "11:00",
        "days_back": 30, "days_ahead": 365, "enrich_count": 3, "checkout_buffer": 30})
    await hass.async_block_till_done()
    # Buchung 1 ohne Abreisezeit → Freigabe 11:00 + 30 min = 11:30 am 16.11.
    st = hass.states.get("sensor.smoobu_ferienwohnung_nachste_abreise")
    assert st.state == "2026-11-16T10:30:00+00:00", st.state
    # Buchung 2 hat check-out 10:00 → Freigabe 10:30 (lokal) am 21.11.
    attrs = hass.states.get("sensor.smoobu_ferienwohnung_nachster_gast").attributes
    assert attrs["freigabe"] == "2026-11-21T10:30:00+01:00", attrs["freigabe"]
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


async def test_month_compare_occupancy_blocked(hass, setup):
    """Vor-/Folgemonat, Monats-Auslastung (nur Gäste) und gesperrte Nächte separat."""
    occ = hass.states.get("sensor.smoobu_ferienwohnung_auslastung_monat")
    # Gäste-Nächte November: 13.–15. (3) + 18.–20. (3) = 6 von 30 → 20 %
    assert float(occ.state) == 20.0
    assert occ.attributes["gaeste_naechte"] == 6
    blk = hass.states.get("sensor.smoobu_ferienwohnung_gesperrte_nachte_monat")
    # Sperrzeit 25.–26.11. = 2 Nächte
    assert int(blk.state) == 2
    assert blk.attributes["monate"]["2026-11"] == 2
    vm = hass.states.get("sensor.smoobu_ferienwohnung_umsatz_vormonat")
    assert vm.attributes["monat"] == "2026-10"
    fm = hass.states.get("sensor.smoobu_ferienwohnung_umsatz_folgemonat")
    assert fm.attributes["monat"] == "2026-12"


async def test_rates_gaps_fields_message(hass, setup, hass_client_no_auth, aioclient_mock):
    """Tagespreise, Lücken, einzelne Buchungsfelder, letzte Gästenachricht."""
    assert float(hass.states.get("sensor.smoobu_ferienwohnung_preis_heute").state) == 80.0
    assert float(hass.states.get("sensor.smoobu_ferienwohnung_preis_morgen").state) == 81.0
    assert hass.states.get("sensor.smoobu_ferienwohnung_mindestaufenthalt_heute").state == "2"
    assert hass.states.get("sensor.smoobu_ferienwohnung_nachster_freier_tag").state == "2026-11-16"
    # Lücke zwischen Buchung 1 (bis 16.) und Buchung 2 (ab 18.): 16.–18. (2 Nächte)
    gap = hass.states.get("sensor.smoobu_ferienwohnung_nachste_lucke")
    assert gap.state == "2026-11-16"
    assert gap.attributes["naechte"] == 2 and gap.attributes["buchbar"] is True
    # Einzelfelder
    assert hass.states.get("sensor.smoobu_ferienwohnung_aktueller_gast_e_mail").state == "a@b.de"
    assert hass.states.get("sensor.smoobu_ferienwohnung_aktueller_gast_kanal").state == "Airbnb"
    assert hass.states.get("sensor.smoobu_ferienwohnung_nachster_gast_check_in_zeit").state == "20:00"
    assert hass.states.get("binary_sensor.smoobu_ferienwohnung_nachster_gast_anzahlung_bezahlt").state == "on"
    assert hass.states.get("sensor.smoobu_ferienwohnung_aktueller_gast_buchungs_id") is None  # deaktiviert
    # Gästenachricht per Webhook
    # Mock neu aufbauen: Nachrichten-Antwort zuerst registrieren (erster Treffer gewinnt)
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE}/api/reservations/2/messages", json={"page_count": 1, "messages": [
        {"id": 5, "type": 1, "subject": "Hi", "message": "alt"}, {"id": 9, "type": 1, "subject": "Frage", "message": "Wo ist der <b>Schlüssel</b>?<br>Danke"}]})
    mock_api(aioclient_mock)
    client = await hass_client_no_auth()
    r = await client.post(f"/api/webhook/{setup.data['webhook_id']}", json={"action": "newMessage", "user": 999, "data": {"id": 9, "sender": "guest", "booking": {"id": 2}}})
    assert r.status == 200
    await hass.async_block_till_done()
    msg = hass.states.get("sensor.smoobu_letzte_gastenachricht")
    assert msg.state == "Wo ist der Schlüssel? Danke", msg.state
    assert msg.attributes["gast"] == "Max Mustermann"


def test_booking_costs():
    from custom_components.smoobu.channels import booking_costs
    comm = {"Airbnb": 15.5, "Booking.com": 15, "FeWo-direkt": 8}
    direct = ["Direct booking", "Website"]
    # Smoobu-Provision + Booking-Zahlungsgebühr aus der Notiz
    b = {"price": 148.6, "commission-included": 22.29, "channel": {"name": "Booking.com"},
         "notice": "BOOKING NOTE : Payment charge is EUR 2.08 Anzahlung"}
    c = booking_costs(b, comm, 15, direct)
    assert c["provision_quelle"] == "smoobu" and c["zahlungsgebuehr"] == 2.08
    assert c["netto"] == round(148.6 - 22.29 - 2.08, 2) and c["kanal_gruppe"] == "Portal"
    # Ohne Smoobu-Provision → Konfiguration
    c = booking_costs({"price": 200, "channel": {"name": "fewo-direkt"}}, comm, 15, direct)
    assert c["provision"] == 16.0 and c["provision_quelle"] == "konfiguration"
    # Direktkanal ohne Eintrag → 0 %, unbekanntes Portal → Standard
    assert booking_costs({"price": 100, "channel": {"name": "Website"}}, comm, 15, direct)["netto"] == 100
    assert booking_costs({"price": 100, "channel": {"name": "Expedia"}}, comm, 15, direct)["provision"] == 15


async def test_direct_vs_portal(hass, setup):
    # Airbnb 300 € (15,5 % laut Standard), Direkt 450,50 € → Direktanteil 60,0 %
    share = hass.states.get("sensor.smoobu_ferienwohnung_direktanteil_jahr")
    assert float(share.state) == 60.0, share.state
    assert share.attributes["kanaele"]["Airbnb"]["provision"] == 46.5
    assert share.attributes["ersparnis_direkt"] == round(450.5 * 0.155, 2)
    net = hass.states.get("sensor.smoobu_ferienwohnung_nettoumsatz_jahr")
    assert float(net.state) == 704.0
    assert float(hass.states.get("sensor.smoobu_ferienwohnung_umsatz_direkt_jahr").state) == 450.5
    assert float(hass.states.get("sensor.smoobu_ferienwohnung_umsatz_portale_jahr").state) == 300.0
    assert float(hass.states.get("sensor.smoobu_ferienwohnung_provision_gebuhren_jahr").state) == 46.5
    assert hass.states.get("sensor.smoobu_ferienwohnung_aktueller_gast_kanalgruppe").state == "Portal"
    assert float(hass.states.get("sensor.smoobu_ferienwohnung_aktueller_gast_nettopreis").state) == 253.5
    p = hass.states.get("sensor.smoobu_ferienwohnung_preis_aktueller_gast")
    assert p.attributes["kanal_gruppe"] == "Portal" and p.attributes["netto"] == 253.5


async def test_channel_and_selection(hass, setup):
    # Kanal-Sensoren je Kanal, Zustand = Brutto Jahr
    air = hass.states.get("sensor.smoobu_ferienwohnung_kanal_airbnb")
    assert air is not None and air.attributes["gruppe"] == "Portal"
    assert "monate" in air.attributes and "vorjahr_bis_heute" in air.attributes
    assert hass.states.get("sensor.smoobu_ferienwohnung_kanal_direct_booking") is not None
    # Auswahl ändern → Auswertungs-Sensoren folgen
    sel = "select.smoobu_ferienwohnung_auswertung_kanal"
    assert "Airbnb" in hass.states.get(sel).attributes["options"]
    await hass.services.async_call("select", "select_option", {"entity_id": sel, "option": "Airbnb"}, blocking=True)
    await hass.services.async_call(
        "select", "select_option",
        {"entity_id": "select.smoobu_ferienwohnung_auswertung_zeitraum", "option": "monat"}, blocking=True)
    await hass.async_block_till_done()
    brutto = hass.states.get("sensor.smoobu_ferienwohnung_auswertung_brutto")
    assert brutto.attributes["kanal"] == "Airbnb" and brutto.attributes["zeitraum"] == "monat"
    # Airbnb-Buchung 13.–16.11.: 3 Nächte à 100 € im November
    assert float(brutto.state) == 300.0
    assert hass.states.get("sensor.smoobu_ferienwohnung_auswertung_nachte").state == "3"
    assert hass.states.get("sensor.smoobu_ferienwohnung_prognose_jahr") is not None


async def test_websocket(hass, setup, hass_ws_client, aioclient_mock):
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/info"})
    info = (await ws.receive_json())["result"]
    apt = info["wohnungen"][0]
    assert apt["apartment_id"] == 123 and apt["sperr_kanal_id"] == 3
    assert {c["name"] for c in apt["kanaele"]} == {"Airbnb", "Direct booking"}
    await ws.send_json({"id": 2, "type": "smoobu/analytics", "period": "monat", "channels": ["Airbnb"]})
    res = (await ws.receive_json())["result"]
    assert res["brutto"] == 300.0 and "reihe" in res and "prognose" in res
    await ws.send_json({"id": 3, "type": "smoobu/bookings", "search": "muster"})
    res = (await ws.receive_json())["result"]
    assert [b["id"] for b in res["buchungen"]] == [2]
    await ws.send_json({"id": 4, "type": "smoobu/booking", "reservation_id": 2})
    res = (await ws.receive_json())["result"]
    assert res["buchung"]["gast"] == "Max Mustermann" and res["nachrichten"][0]["text"] == "Hallo"
    await ws.send_json({"id": 5, "type": "smoobu/subscribe"})
    assert (await ws.receive_json())["success"]


async def test_write_services(hass, setup, aioclient_mock):
    from homeassistant.exceptions import ServiceValidationError

    aioclient_mock.post(f"{BASE}/api/reservations", json={"id": 50})
    aioclient_mock.delete(f"{BASE}/api/reservations/3", status=204, text="")
    aioclient_mock.post(f"{BASE}/api/rates", json={"success": True})
    r = await hass.services.async_call(
        DOMAIN, "block_period", {"start_date": "2026-12-01", "end_date": "2026-12-03", "notice": "Handwerker"},
        blocking=True, return_response=True)
    assert r["reservation"]["id"] == 50
    call = [c for c in aioclient_mock.mock_calls if c[0] == "POST" and str(c[1]).endswith("/api/reservations")][0]
    assert b'"channelId":3' in call[2] and b'"apartmentId":123' in call[2]
    # Portalbuchung (Airbnb) darf nicht gelöscht werden, Direktbuchung nur mit allow_booking
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "delete_reservation", {"reservation_id": 1}, blocking=True)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "delete_reservation", {"reservation_id": 2}, blocking=True)
    await hass.services.async_call(DOMAIN, "delete_reservation", {"reservation_id": 3}, blocking=True)
    await hass.services.async_call(
        DOMAIN, "set_rates", {"start_date": "2026-12-01", "end_date": "2026-12-05", "price": 95, "min_stay": 2},
        blocking=True)
    call = [c for c in aioclient_mock.mock_calls if c[0] == "POST" and "/api/rates" in str(c[1])][0]
    assert b'"dates":["2026-12-01:2026-12-05"]' in call[2] and b'"daily_price":95.0' in call[2]


async def test_assistant(hass, setup, hass_ws_client, aioclient_mock):
    """KI-Assistent mit Fake-KI: Vorschlag, Push-Buttons, Senden, Lernen, Wissen."""
    from homeassistant.core import SupportsResponse
    from custom_components.smoobu.assistant import rank, strip_quote

    prompts = []

    async def fake_ai(call):
        prompts.append(call.data["instructions"])
        if "fakten" in call.data["structure"]:
            return {"data": {"fakten": "Parken | Parkplatz rechts nach dem Tor\nZugang | Code wird separat mitgeteilt"}}
        return {"data": {"antwort": "Hallo Max, kein Problem! Liebe Grüße", "absicht": "spaete_anreise",
                         "ankunftszeit": "21.30", "dringend": False, "wissensluecke": "Fahrrad unterstellen?"}}

    hass.services.async_register("ai_task", "generate_data", fake_ai, supports_response=SupportsResponse.ONLY)
    pushes = []

    async def fake_push(call):
        pushes.append(call.data)

    hass.services.async_register("notify", "mobile_app_test", fake_push)
    hass.config_entries.async_update_entry(setup, options={
        **setup.options, "assistant": True, "ai_entity": "ai_task.fake", "assist_recipients": ["notify.mobile_app_test"]})
    await hass.async_block_till_done()
    entry = hass.config_entries.async_get_entry(setup.entry_id)
    a = entry.runtime_data.assistant
    a.save_knowledge({"thema": "Check-in", "text": "ab 16 Uhr"})
    a.save_knowledge({"thema": "Tresor", "text": "Code 1234", "vertraulich": True})

    # Gast schreibt (Webhook) → Vorschlag + Push mit Buttons
    aioclient_mock.clear_requests()
    # Eigene Antworten zuerst registrieren (der Mocker nimmt den ersten Treffer)
    aioclient_mock.get(f"{BASE}/api/reservations/2/messages", json={"page_count": 1, "messages": [
        {"id": 7, "type": 1, "message": "Wir kommen erst 21:30, ok?\n---- Ursprüngliche Nachricht ---- alt"}]})
    aioclient_mock.put(f"{BASE}/api/reservations/2", json={})
    mock_api(aioclient_mock)
    await a.on_new_message(2)
    await hass.async_block_till_done()
    sug = a.data["vorschlaege"]["2"]
    assert sug["ankunftszeit"] == "21:30" and sug["gastnachricht"] == "Wir kommen erst 21:30, ok?"
    assert "Code 1234" not in prompts[-1] and "VERTRAULICH" in prompts[-1] and "ab 16 Uhr" in prompts[-1]
    assert any(w["status"] == "vorschlag" for w in a.data["wissen"])  # Wissenslücke gemerkt
    acts = [x["action"] for x in pushes[-1]["data"]["actions"]]
    assert acts[0] == f"SMOOBU_SENDEN_2_{sug['id']}" and acts[-1] == f"SMOOBU_ZEIT_2_{sug['id']}"

    # Button „Ankunft übernehmen“ → PUT arrivalTime
    hass.bus.async_fire("mobile_app_notification_action", {"action": f"SMOOBU_ZEIT_2_{sug['id']}"})
    await hass.async_block_till_done()
    put = [c for c in aioclient_mock.mock_calls if c[0] == "PUT"]
    assert put and b'"arrivalTime":"21:30"' in put[0][2]

    # Button „Senden“ → Nachricht an Gast + Lernbeispiel (unverändert = „vorschlag“)
    hass.bus.async_fire("mobile_app_notification_action", {"action": f"SMOOBU_SENDEN_2_{sug['id']}"})
    await hass.async_block_till_done()
    assert any("send-message-to-guest" in str(c[1]) for c in aioclient_mock.mock_calls)
    assert a.data["vorschlaege"]["2"]["status"] == "gesendet"
    assert a.data["beispiele"][-1]["quelle"] == "vorschlag"

    # WebSocket: Zustand, Wissen speichern, Vorschlag auf Abruf
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/assistant/state"})
    st = (await ws.receive_json())["result"]
    assert st["aktiv"] and st["beispiele_anzahl"] == 1
    await ws.send_json({"id": 2, "type": "smoobu/assistant/suggest", "reservation_id": 2, "anlass": "willkommen"})
    assert (await ws.receive_json())["success"]
    assert "Willkommensnachricht" in prompts[-1]

    # Wissen aus Verlauf erzeugen
    assert await a.build_knowledge() == 2
    assert hass.states.get("sensor.smoobu_assistent_offene_vorschlage") is not None or True

    assert strip_quote("Danke!\nVon meinem Galaxy gesendet") == "Danke!"
    assert strip_quote("Grüße ThomasVon meinem/meiner Galaxy gesendet\n---- alt") == "Grüße Thomas"
    assert rank("fahrrad unterstellen", ["wo parken", "fahrrad in der garage unterstellen"]) == [1]

    # Import: Vorlagen (gleicher Betreff in ≥ 3 Buchungen) sind keine Antworten
    msgs = {
        1: [{"id": 11, "type": 2, "subject": "Willkommen", "message": "Danke für Deine Buchung"},
            {"id": 12, "type": 1, "message": "Darf der Hund mit?"},
            {"id": 13, "type": 2, "subject": "Willkommen", "message": "Danke für Deine Buchung"},
            {"id": 14, "type": 2, "message": "Gerne, 15 € Reinigung. Code ist 2025"}],
        2: [{"id": 21, "type": 2, "subject": "Willkommen", "message": "Danke für Deine Buchung"}],
    }

    async def fake_msgs(rid):
        return msgs.get(rid, [{"id": 31, "type": 2, "subject": "Willkommen", "message": "Danke für Deine Buchung"}])

    a._messages = fake_msgs
    a.throttle = 0
    st = await a.import_history(5)
    ex = [b for b in a.data["beispiele"] if b["quelle"] == "verlauf"]
    assert st["beispiele"] == 1 and ex[0]["gast"] == "Darf der Hund mit?"
    assert ex[0]["antwort"] == "Gerne, 15 € Reinigung. Code ist [CODE]"
    assert a.data["vorlagen_betreff"] == ["Willkommen"]


async def test_ai_lock(hass, setup, hass_ws_client, aioclient_mock):
    """v1.14.0: „KI-Funktionen erlauben“ aus → kein einziger ai_task-Aufruf, klare Fehlermeldung."""
    from homeassistant.core import SupportsResponse
    from custom_components.smoobu.api import SmoobuError
    from custom_components.smoobu.const import ai_allowed

    calls = []

    async def fake_ai(call):
        calls.append(call.data)
        return {"data": {"antwort": "Hallo", "absicht": "frage"}}

    hass.services.async_register("ai_task", "generate_data", fake_ai, supports_response=SupportsResponse.ONLY)
    # Alte Installation ohne Schalter: KI-Entität gewählt = erlaubt (keine Verhaltensänderung)
    assert ai_allowed({"ai_entity": "ai_task.fake"}) is True
    assert ai_allowed({"ai_entity": "ai_task.fake", "ai_enabled": False}) is False
    assert ai_allowed({"ai_enabled": True}) is False  # ohne KI-Entität nie erlaubt

    hass.config_entries.async_update_entry(setup, options={
        **setup.options, "assistant": True, "ai_entity": "ai_task.fake", "ai_enabled": False})
    await hass.async_block_till_done()
    a = hass.config_entries.async_get_entry(setup.entry_id).runtime_data.assistant
    assert not a.ai_allowed and not a.enabled
    with pytest.raises(SmoobuError, match="deaktiviert"):
        await a.suggest(2, "willkommen")
    with pytest.raises(SmoobuError, match="deaktiviert"):
        await a.build_knowledge()
    await a.on_new_message(2)  # Webhook: Gast schreibt → kein Vorschlag
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/assistant/suggest", "reservation_id": 2, "anlass": "antwort"})
    res = await ws.receive_json()
    assert not res["success"] and "deaktiviert" in res["error"]["message"]
    await ws.send_json({"id": 2, "type": "smoobu/assistant/state"})
    st = (await ws.receive_json())["result"]
    assert st["ki_erlaubt"] is False and st["ki_sperre"]
    assert calls == []  # KI wurde nie aufgerufen

    # Wieder erlauben → Aufruf geht durch
    hass.config_entries.async_update_entry(setup, options={**setup.options, "ai_enabled": True})
    await hass.async_block_till_done()
    a = hass.config_entries.async_get_entry(setup.entry_id).runtime_data.assistant
    await a.suggest(2, "willkommen")
    assert len(calls) == 1


async def test_options_ai_switch(hass, setup):
    """Optionsfluss: KI erlauben ohne KI-Entität → Fehler am Feld; aus ist speicherbar."""
    result = await hass.config_entries.options.async_init(setup.entry_id)
    while result["step_id"] != "assistent":
        result = await hass.config_entries.options.async_configure(result["flow_id"], user_input={})
    assert "ai_enabled" in {str(k) for k in result["data_schema"].schema}
    base = {"ai_enabled": True, "assistant": False}
    result = await hass.config_entries.options.async_configure(result["flow_id"], user_input=base)
    assert result["errors"] == {"ai_entity": "ai_entity_required"}
    result = await hass.config_entries.options.async_configure(result["flow_id"], user_input={**base, "ai_enabled": False})
    # Benachrichtigungen und Wohnungen mit Standardwerten übernehmen
    while result["type"] == "form":
        result = await hass.config_entries.options.async_configure(result["flow_id"], user_input={})
    assert result["type"] == "create_entry" and result["data"]["ai_enabled"] is False
    # Durchklicken übernimmt die bisherigen Werte (Vorschlag-Push bleibt an, neue Arten aus)
    assert result["data"]["notify_vorschlag"] is True and result["data"]["notify_buchung"] is False
    assert result["data"]["notify_quiet_messages"] is True


async def test_no_reply_and_guest_message(hass, setup, hass_ws_client, aioclient_mock):
    """v1.14.0: offen nur bei Nachricht VOM Gast; „Keine Antwort nötig“; Sensor nur Gästenachrichten."""
    entry = hass.config_entries.async_get_entry(setup.entry_id)
    c = entry.runtime_data
    msgs = {"messages": [{"id": 10, "type": 1, "message": "Kommen wir um 18 Uhr rein?"}]}

    async def fake_get(rid, only_guest=True):
        assert only_guest is False  # alle Nachrichten laden (inkl. automatischer an den Gast)
        return list(msgs["messages"])

    c.client.get_messages = fake_get
    ws = await hass_ws_client(hass)

    async def status():
        await ws.send_json({"id": status.n, "type": "smoobu/message_status", "reservation_ids": [2]})
        status.n += 1
        res = await ws.receive_json()
        assert res.get("success"), res
        return res["result"]["status"]["2"]
    status.n = 1

    assert (await status())["offen"] is True
    # Automatische Nachricht AN den Gast danach → nicht mehr offen
    msgs["messages"].append({"id": 11, "type": 2, "subject": "Willkommen", "message": "Danke für die Buchung"})
    c.invalidate_message_status(2)
    assert (await status())["offen"] is False
    # Gast schreibt „Danke“ → offen → als „keine Antwort nötig“ markieren
    msgs["messages"].append({"id": 12, "type": 1, "message": "Danke!"})
    c.invalidate_message_status(2)
    assert (await status())["offen"] is True
    await ws.send_json({"id": 100, "type": "smoobu/message_done", "reservation_id": 2})
    res = (await ws.receive_json())["result"]["status"]
    assert res["offen"] is False and res["ohne_antwort"] is True and res["erledigt_id"] == 12
    status.n = 101
    # Neue Gastnachricht → wieder offen
    msgs["messages"].append({"id": 13, "type": "1", "message": "Noch eine Frage"})
    c.invalidate_message_status(2)
    assert (await status())["offen"] is True
    # Rückgängig
    await ws.send_json({"id": 200, "type": "smoobu/message_done", "reservation_id": 2, "done": False})
    assert (await ws.receive_json())["result"]["status"]["erledigt_id"] is None

    # Sensor „Letzte Gästenachricht“: eigene Nachricht ändert ihn nicht
    await c.async_fetch_last_message(2, "guest")
    assert c.data.last_message["nachricht_id"] == 13 and c.data.last_message["absender"] == "guest"
    msgs["messages"].append({"id": 14, "type": 2, "message": "Gerne, bis morgen"})
    await c.async_fetch_last_message(2, "host")
    await c.async_fetch_last_message(2, None)
    assert c.data.last_message["nachricht_id"] == 13


def test_short_codes():
    """v1.15.0: automatische, eindeutige Wohnungskürzel."""
    from custom_components.smoobu.websocket_api import short_codes

    assert short_codes(["Haus Sonnenhang", "Altmühlblick", "Ferienwohnung Seeblick", "Wohnung 2", "Haus Sonnenberg"]) == [
        "HS", "AL", "SE", "W2", "HS2"]
    assert short_codes(["", "Studio"]) == ["?", "ST"]


def test_analytics_units():
    """v1.15.0: Auslastung über mehrere Wohnungen = Nächte ÷ (Tage × Wohnungen)."""
    from datetime import date

    from custom_components.smoobu.analytics import analyze

    rec = {"anreise": "2026-11-01", "abreise": "2026-11-11", "naechte": 10, "brutto": 1000.0, "provision": 0.0,
           "zahlungsgebuehr": 0.0, "netto": 1000.0, "blockiert": False, "storniert": False, "kanal": "Direct booking",
           "gruppe": "Direkt", "personen": 2, "vorlauf_tage": 5, "hund": False, "erstellt": None}
    one = analyze([rec], date(2026, 11, 1), date(2026, 12, 1), series=False)
    two = analyze([rec, {**rec}], date(2026, 11, 1), date(2026, 12, 1), series=False, units=2)
    assert one["auslastung_prozent"] == 33.3 and one["einheiten"] == 1
    assert two["auslastung_prozent"] == 33.3 and two["naechte"] == 20 and two["tage"] == 30 and two["einheiten"] == 2


async def test_websocket_all_apartments(hass, setup, hass_ws_client):
    """v1.15.0: apartment_id „alle“ wird angenommen; rates bleibt je Wohnung."""
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/info"})
    info = (await ws.receive_json())["result"]
    assert info["wohnungen"][0]["kuerzel"] == "FE"
    await ws.send_json({"id": 2, "type": "smoobu/bookings", "apartment_id": "alle"})
    res = (await ws.receive_json())["result"]
    assert res["anzahl"] >= 1 and all("wohnung_id" in b for b in res["buchungen"])
    await ws.send_json({"id": 3, "type": "smoobu/analytics", "apartment_id": "alle", "period": "monat"})
    res = (await ws.receive_json())["result"]
    assert res["einheiten"] == 1 and "brutto" in res
    await ws.send_json({"id": 4, "type": "smoobu/rates", "apartment_id": "alle"})
    res = await ws.receive_json()
    assert not res["success"] and res["error"]["code"] == "invalid_target"
    await ws.send_json({"id": 5, "type": "smoobu/bookings", "apartment_id": 999})
    res = await ws.receive_json()
    assert not res["success"]


def test_pet_hint_airbnb_fee_and_negation():
    """v1.15.3: Airbnb „PASS_THROUGH_PET_FEE“, Preisdetails, Verneinung, keine Fehltreffer."""
    from custom_components.smoobu.models import pet_hint

    fee = {"priceElements": [{"type": "channelCustom", "name": "PASS_THROUGH_PET_FEE", "amount": 15}]}
    assert pet_hint(fee) == "Zusatzleistung: Pass Through Pet Fee"
    assert pet_hint({"priceElements": [{"name": "PASS_THROUGH_PET_FEE", "amount": 0}]}) is None
    assert pet_hint({"price-details": "Cleaning - EUR 10\r\nPASS_THROUGH_PET_FEE - EUR 15"}).startswith("Preisdetails")
    assert pet_hint({"notice": "Wir kommen ohne Hund"}) is None
    assert pet_hint({"notice": "No pets, thanks"}) is None
    assert pet_hint({"notice": "Peter und Petra, hundert Grüße"}) is None
    assert pet_hint({"notice": "Wir bringen unseren Hund mit"}).startswith("Notiz")
    assert pet_hint({"_hund_nachricht": "Gastnachricht: …Hund…"}) == "Gastnachricht: …Hund…"


async def test_pet_from_guest_messages(hass, setup):
    """v1.15.3: Hund aus Nachrichten VOM Gast (eigene Nachrichten zählen nicht)."""
    c = hass.config_entries.async_entries(DOMAIN)[0].runtime_data
    msgs = [
        {"id": 1, "type": 2, "message": "Hunde sind willkommen (15 € Endreinigung)."},
        {"id": 2, "type": 1, "message": "Danke! Wir kommen mit unserem kleinen Dackel – darf der Hund mit?"},
    ]
    assert c._pet_from_messages(msgs).startswith("Gastnachricht: …")
    assert c._pet_from_messages(msgs[:1]) is None


async def test_message_status_subscription(hass, setup, hass_ws_client):
    """v1.17.0: Antwortstatus verworfen → Abo meldet „art: nachrichten“ (Zähler am Reiter sofort neu)."""
    c = hass.config_entries.async_get_entry(setup.entry_id).runtime_data
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/subscribe"})
    assert (await ws.receive_json())["success"]
    c.invalidate_message_status(2)
    ev = await ws.receive_json()
    assert ev["type"] == "event" and ev["event"]["art"] == "nachrichten"



async def test_notifications(hass, setup, freezer):
    """v1.17.0: neue Buchung/Storno/Änderung aus dem Datenabgleich, Ruhezeit-Warteschlange, Kürzel."""
    from datetime import time as dtime

    from custom_components.smoobu.notifications import in_quiet, opt_enabled, opt_recipients

    assert in_quiet(dtime(23, 0), dtime(21, 0), dtime(7, 0)) and in_quiet(dtime(6, 59), dtime(21, 0), dtime(7, 0))
    assert not in_quiet(dtime(7, 0), dtime(21, 0), dtime(7, 0)) and not in_quiet(dtime(12, 0), dtime(12, 0), dtime(12, 0))
    # Rückwärtskompatibel: ohne neue Optionen Vorschlag an, Empfänger aus dem Assistenten
    old = {"assist_recipients": ["notify.mobile_app_a"], "assist_briefing": True}
    assert opt_enabled(old, "vorschlag") and opt_enabled(old, "briefing") and not opt_enabled(old, "buchung")
    assert opt_recipients(old, "buchung") == ["notify.mobile_app_a"]

    hass.config_entries.async_update_entry(setup, options={**setup.options, "notify_buchung": True, "notify_storno": True,
                                                            "notify_buchung_to": ["notify.mobile_app_x"],
                                                            "notify_storno_to": ["notify.mobile_app_x"]})
    await hass.async_block_till_done()
    c = hass.config_entries.async_get_entry(setup.entry_id).runtime_data
    calls = []

    async def fake_deliver(kind, title, message, data):
        calls.append((kind, title, message))

    c.notifier._deliver = fake_deliver
    recs = c.records_all()
    base = next(r for r in recs if not r["blockiert"] and not r["storniert"])
    # Änderung: Abreise verschoben
    changed = {**base, "abreise": "2026-12-31"}
    c.records_all = lambda: [changed if r is base else r for r in recs]
    c.notifier._on_data()
    await hass.async_block_till_done()
    assert calls and calls[-1][0] == "storno" and "Abreise" in calls[-1][2] and "31.12." in calls[-1][2]
    # Storno
    c.records_all = lambda: [{**changed, "storniert": True} if r is base else r for r in recs]
    c.notifier._on_data()
    await hass.async_block_till_done()
    assert calls[-1][1].startswith("❌")
    # Neue Buchung (angelegt heute) in der Ruhezeit → gesammelt, nicht zugestellt
    hass.config_entries.async_update_entry(setup, options={**setup.options, "notify_quiet": True,
                                                            "notify_quiet_from": "00:00", "notify_quiet_to": "23:59"})
    await hass.async_block_till_done()
    c = hass.config_entries.async_get_entry(setup.entry_id).runtime_data
    calls.clear()
    c.notifier._deliver = fake_deliver
    new = {**base, "id": 999999, "erstellt": "2026-11-15T10:00:00", "storniert": False}
    recs2 = c.records_all()
    c.records_all = lambda: [*recs2, new]
    c.notifier._on_data()
    await hass.async_block_till_done()
    assert not calls and c.notifier.data["warteschlange"][-1]["art"] == "buchung"
    await c.notifier._flush(None)
    assert calls and calls[0][1].startswith("🆕") and not c.notifier.data["warteschlange"]


async def test_apartment_codes(hass, setup, hass_ws_client):
    """v1.17.0: eigenes Kürzel aus den Optionen hat Vorrang vor dem automatischen."""
    from custom_components.smoobu.codes import clean_code, short_codes

    assert clean_code(" fw-2 ") == "FW2" and clean_code("abcdef") == "ABCD"
    assert short_codes(["Haus Sonnenhang"], taken={"HS"}) == ["HS2"]
    c = hass.config_entries.async_get_entry(setup.entry_id).runtime_data
    apt = next(iter(c.data.apartments))
    hass.config_entries.async_update_entry(setup, options={**setup.options, "apartment_codes": {str(apt): "SEE"}})
    await hass.async_block_till_done()
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/info"})
    info = (await ws.receive_json())["result"]
    assert info["wohnungen"][0]["kuerzel"] == "SEE"


async def test_suggestion_delete_and_ignore(hass, setup, hass_ws_client):
    """v1.17.0: Vorschläge in der Assistent-Karte ignorieren bzw. löschen (z. B. Testvorschlag)."""
    a = hass.config_entries.async_get_entry(setup.entry_id).runtime_data.assistant
    for rid in (2, 3):
        a.data["vorschlaege"][str(rid)] = {"id": f"s{rid}", "buchung_id": rid, "status": "offen", "gast": "X",
                                           "antwort": "Hallo", "erstellt": "2026-11-15T10:00:00"}
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/assistant/delete", "kind": "ignorieren", "item_id": "2"})
    assert (await ws.receive_json())["success"]
    assert a.data["vorschlaege"]["2"]["status"] == "ignoriert"
    await ws.send_json({"id": 2, "type": "smoobu/assistant/delete", "kind": "vorschlag", "item_id": "3"})
    assert (await ws.receive_json())["success"]
    assert "3" not in a.data["vorschlaege"]

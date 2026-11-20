"""v1.18.0: Smoobu-Formate – einzelner Tag bei /api/rates, Pflichtfelder bei Sperrzeiten (Rückmeldung Betreiber 20.11.2026)."""
import pytest  # noqa: F401

from custom_components.smoobu.api import SmoobuClient, SmoobuError, block_missing_fields, block_placeholders, date_spec


def test_date_spec():
    assert date_spec("2026-11-19", "2026-11-19") == "2026-11-19"
    assert date_spec("2026-11-19", "2026-11-21") == "2026-11-19:2026-11-21"


def test_block_placeholders_only_requested():
    err = SmoobuError("400", 400, {"status": 400, "validation_messages": {
        "firstName": {"isEmpty": "x"}, "lastName": {"isEmpty": "x"}, "email": {"isEmpty": "x"}, "phone": {"isEmpty": "x"}}})
    miss = block_missing_fields(err)
    out = block_placeholders(miss, {"notice": "Renovierung"})
    assert set(out) == {"firstName", "lastName", "email", "phone"}
    assert out["email"].endswith("@example.com")
    # Adressfelder als Objekt, Notiz des Betreibers bleibt
    out2 = block_placeholders(["street", "notice"], {"notice": "Renovierung"})
    assert out2 == {"address": {"street": "-", "postalCode": "00000", "location": "-"}}
    # kein Validierungsfehler → nichts nachreichen
    assert block_missing_fields(SmoobuError("500", 500, None)) == []
    # unbekanntes Pflichtfeld → alle Platzhalter
    assert "firstName" in block_placeholders(["irgendwas"], {})


@pytest.mark.asyncio
async def test_create_block_retries_once():
    calls = []

    class Fake(SmoobuClient):
        def __init__(self):
            pass

        async def create_reservation(self, body):
            calls.append(dict(body))
            if len(calls) == 1:
                raise SmoobuError("400", 400, {"validation_messages": {"firstName": {}, "email": {}}})
            return {"id": 1}

    res = await Fake().create_block({"arrivalDate": "2026-11-19", "departureDate": "2026-11-20", "apartmentId": 7})
    assert res == {"id": 1} and len(calls) == 2
    assert "firstName" not in calls[0] and calls[1]["firstName"] == "Sperre" and calls[1]["arrivalDate"] == "2026-11-19"


@pytest.mark.asyncio
async def test_set_rates_single_day():
    sent = {}

    class Fake(SmoobuClient):
        def __init__(self):
            pass

        async def request(self, method, path, body=None, **kw):
            sent.update(body)
            return {}

    await Fake().set_rates(7, "2026-11-19", "2026-11-19", price=50)
    assert sent["operations"][0]["dates"] == ["2026-11-19"]


def test_preisaktion_single_night():
    """Last-Minute für genau eine Nacht: Smoobu bekommt "2026-11-19" statt "2026-11-19:2026-11-19"."""
    from custom_components.smoobu.preisaktion import operations
    ops = operations([{"datum": "2026-11-19", "preis_alt": 55, "preis_neu": 50, "min_alt": None, "min_neu": None},
                      {"datum": "2026-11-21", "preis_alt": 55, "preis_neu": 50, "min_alt": None, "min_neu": None},
                      {"datum": "2026-11-22", "preis_alt": 55, "preis_neu": 50, "min_alt": None, "min_neu": None}])
    assert ops == [{"dates": ["2026-11-19", "2026-11-21:2026-11-22"], "daily_price": 50}]


def test_umbuchung_inherits_storno():
    """v1.18.0: neue Push-Art „umbuchung“ – ohne eigene Einstellung wie „storno“."""
    from custom_components.smoobu.notifications import opt_enabled, opt_quiet, opt_recipients
    o = {"notify_storno": True, "notify_storno_to": ["notify.mobile_app_r"], "notify_storno_quiet": False}
    assert opt_enabled(o, "umbuchung") and opt_recipients(o, "umbuchung") == ["notify.mobile_app_r"] and not opt_quiet(o, "umbuchung")
    o2 = {**o, "notify_umbuchung": False, "notify_umbuchung_to": []}
    assert not opt_enabled(o2, "umbuchung") and opt_recipients(o2, "umbuchung") == []
    assert not opt_enabled({}, "umbuchung")

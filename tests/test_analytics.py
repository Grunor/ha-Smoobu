"""Auswertungslogik (analytics.py) ohne HA: Anteile, Stornos, Vorlauf, Filter, Prognose."""
from datetime import date

from custom_components.smoobu.analytics import (
    analyze,
    analyze_with_compare,
    build_records,
    compare_range,
    forecast_year,
    period_range,
)
from custom_components.smoobu.channels import booking_costs

TODAY = date(2026, 11, 15)
COMM = {"Airbnb": 15.5, "Booking.com": 15.0, "Direct booking": 0.0}


def costs(b):
    return booking_costs(b, COMM, 15.0, ["Direct booking", "Website"])


def bk(i, arr, dep, ch, price, **kw):
    return {"id": i, "arrival": arr, "departure": dep, "channel": {"id": i, "name": ch}, "price": price,
            "adults": 2, "children": 0, "apartment": {"id": 1, "name": "A"}, "type": "reservation", **kw}


BOOKINGS = [
    # über den Jahreswechsel 2025/26: 4 Nächte, 2 im Dez., 2 im Jan.
    bk(1, "2025-12-30", "2026-01-03", "Airbnb", 400, **{"created-at": "2025-10-01 10:00"}),
    bk(2, "2026-03-01", "2026-03-04", "Booking.com", 300, **{"created-at": "2026-02-19 09:00"},
       notice="Payment charge is EUR 4.20"),
    bk(3, "2026-03-10", "2026-03-12", "Direct booking", 200, adults=3, **{"created-at": "2026-01-09 09:00"},
       priceElements=[{"name": "Hund", "amount": 10}]),
    bk(4, "2026-03-20", "2026-03-25", "Booking.com", 500, type="cancellation", **{"created-at": "2026-02-01 09:00"}),
    {"id": 5, "arrival": "2026-03-26", "departure": "2026-03-28", "channel": {"id": 9, "name": "Blocked"},
     "apartment": {"id": 1}, "is-blocked-booking": True},
    # stornierte Sperrzeit: zählt weder als gesperrt noch als Storno einer Gästebuchung
    {"id": 7, "arrival": "2026-04-01", "departure": "2026-04-10", "channel": {"id": 9, "name": "Blocked"},
     "apartment": {"id": 1}, "is-blocked-booking": True, "type": "cancellation"},
    # Vorjahr gleicher Monat, nach dem Vorjahres-Stichtag gebucht (Pickup)
    bk(6, "2025-12-10", "2025-12-12", "Direct booking", 160, **{"created-at": "2025-11-20 09:00"}),
]
RECS = build_records(BOOKINGS, costs, ["Airbnb", "Booking.com"], TODAY)


def test_records():
    by = {r["id"]: r for r in RECS}
    assert by[4]["status"] == "storniert" and by[5]["status"] == "blockiert"
    assert by[2]["vorlauf_tage"] == 10
    assert by[2]["zahlungsgebuehr"] == 4.2 and by[2]["provision"] == 45.0
    assert by[3]["hund"] and by[3]["personen"] == 3


def test_proration_and_cancellations():
    jan = analyze(RECS, *period_range("jahr", TODAY), series=True)
    # 2 von 4 Nächten der Airbnb-Buchung zählen 2026 → 200 €; Storno zählt nicht zum Umsatz
    assert jan["kanaele"]["Airbnb"]["brutto"] == 200.0
    assert jan["brutto"] == 700.0
    assert jan["gesperrt_naechte"] == 2
    march = analyze(RECS, date(2026, 3, 1), date(2026, 4, 1))
    assert march["buchungen"] == 2 and march["stornos"] == 1
    assert march["stornoquote_prozent"] == 33.3
    assert march["kanaele"]["Booking.com"]["stornos"] == 1
    assert march["hunde"] == 1 and march["aufenthalt_schnitt"] == 2.5
    assert march["reihe"]["einheit"] == "tag" and len(march["reihe"]["labels"]) == 31
    assert jan["reihe"]["labels"][2] == "2026-03" and jan["reihe"]["kanaele"]["Booking.com"][2] == 300.0


def test_filter_and_compare():
    portals = analyze(RECS, *period_range("jahr", TODAY), "Portale", series=False)
    assert set(portals["kanaele"]) == {"Airbnb", "Booking.com"}
    single = analyze(RECS, *period_range("jahr", TODAY), ["Direct booking"], series=False)
    assert single["brutto"] == 200.0
    r = analyze_with_compare(RECS, *period_range("jahr", TODAY), None, "vorjahr", series=False)
    assert r["vergleich"]["brutto"] == 360.0  # 200 (Dez. Airbnb) + 160
    assert compare_range(date(2026, 3, 1), date(2026, 4, 1), "vorperiode") == (date(2026, 2, 1), date(2026, 3, 1))


def test_forecast():
    f = forecast_year(RECS, TODAY)
    # Vorjahr ab 15.11.2025 nachgebucht: Buchung 6 (160) – Buchung 1 war vorher gebucht
    assert f["nachbuchung_vorjahr"] == 160.0
    assert f["prognose"] == 860.0


def test_block_channel():
    from custom_components.smoobu.analytics import block_channel_id
    recs = [{"blockiert": True, "kanal": "Blocked channel auto", "kanal_id": 5},
            {"blockiert": True, "kanal": "Blocked channel auto", "kanal_id": 5},
            {"blockiert": True, "kanal": "Blocked channel", "kanal_id": 7}]
    assert block_channel_id(recs) == 7
    assert block_channel_id(recs[:2]) == 5


def test_assistant_clean_redact():
    from custom_components.smoobu.assistant import clean
    t = clean("Hallo Carmen,\nAnbei die Kontodaten:\nDE31 7655 0000 0009 0888 32\nLiebe Grüße")
    assert "DE31" not in t and "[IBAN]" in t
    t = clean("Der Code ist 2025, Mail an info@example.de oder 0176-40464701")
    assert "2025" not in t and "[CODE]" in t and "[E-MAIL]" in t and "[TELEFON]" in t
    assert clean("Danke&nbsp;Max\nGesendet von Outlook für iOSVon: x") == "Danke Max"
    assert clean("Kein Problem\n\n schrieb am Do., 31. Juli 2025:\n> Hallo") == "Kein Problem"
    assert "[LINK]" in clean("Mappe: https://guest.smoobu.com/?t=abc&b=1")
    assert clean("Ankunft 21:30, 3 Nächte, 2025 war schön") == "Ankunft 21:30, 3 Nächte, 2025 war schön"

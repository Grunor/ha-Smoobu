"""Statistik-Werkbank (stats.py): Baukasten-Abfrage und Pace-Modell ohne HA."""
from datetime import date

import pytest

from custom_components.smoobu.analytics import as_of, build_records
from custom_components.smoobu.stats import pace, query
from tests.test_analytics import costs, bk

TODAY = date(2026, 11, 16)


def recs(*bookings):
    return build_records(bookings, costs, [], TODAY)


R = recs(
    # 2025: Direkt Fr–So 2 Nächte 200 €, angelegt 01.02.2025
    bk(1, "2025-03-07", "2025-03-09", "Direct booking", 200, **{"created-at": "2025-02-01 10:00"}),
    # 2025: Airbnb, angelegt 01.12.2025 → Nachbuchung nach Stichtag 16.11.2025
    bk(2, "2025-12-20", "2025-12-22", "Airbnb", 300, **{"created-at": "2025-12-01 10:00"}),
    # 2026: Booking 3 Nächte 300 €, angelegt 01.01.2026
    bk(3, "2026-03-06", "2026-03-09", "Booking.com", 300, **{"created-at": "2026-01-01 10:00"}),
    # 2026: storniert
    bk(4, "2026-04-10", "2026-04-12", "Airbnb", 250, type="cancellation", **{"created-at": "2026-02-01 10:00"}),
)


def test_nacht_kennzahl_nach_wochentag():
    res = query(R, "naechte", "wochentag", date(2026, 1, 1), date(2027, 1, 1))
    werte = {z["fach"]: z["werte"]["Gesamt"]["wert"] for z in res["zeilen"]}
    assert werte["Fr"] == 1 and werte["Sa"] == 1 and werte["So"] == 1 and werte["Mo"] == 0
    # feste Reihenfolge Mo … So
    assert [z["fach"] for z in res["zeilen"]][:2] == ["Mo", "Di"]


def test_auslastung_je_monat_und_kanal_anteil():
    res = query(R, "auslastung", "monat", date(2026, 3, 1), date(2026, 4, 1))
    assert res["zeilen"][0]["werte"]["Gesamt"]["wert"] == round(3 / 31 * 100, 1)
    res = query(R, "umsatz", "kanal", date(2025, 1, 1), date(2027, 1, 1))
    werte = {z["fach"]: z["werte"]["Gesamt"] for z in res["zeilen"]}
    assert werte["Booking.com"]["wert"] == 300 and werte["Booking.com"]["wenig_daten"]
    assert "Airbnb" in werte  # Airbnb 2025 zählt, Storno 2026 nicht


def test_buchungs_kennzahlen_und_aufteilung():
    res = query(R, "stornoquote", "jahr", date(2025, 1, 1), date(2027, 1, 1))
    werte = {z["fach"]: z["werte"]["Gesamt"]["wert"] for z in res["zeilen"]}
    assert werte["2026"] == 50.0 and werte["2025"] == 0.0
    res = query(R, "buchungen", "jahr", date(2025, 1, 1), date(2027, 1, 1), split="kanal")
    assert set(res["serien"]) == {"Airbnb", "Booking.com", "Direct booking"}


def test_filter_und_fehler():
    res = query(R, "buchungen", "gesamt", date(2025, 1, 1), date(2027, 1, 1), filters={"min_naechte": 3})
    assert res["zeilen"][0]["werte"]["Gesamt"]["wert"] == 1
    with pytest.raises(ValueError):
        query(R, "gibtsnicht", "monat", date(2026, 1, 1), date(2027, 1, 1))


def test_pace_prognose_mit_nachbuchung():
    res = pace(R, 2026, TODAY, compare_years=1)
    assert res["prognose"]["gebucht"] == 300
    # Vorjahr: Stand 16.11.2025 = 200, Endstand 500 → Nachbuchung 300
    assert res["vergleich"][0]["nachbuchung"] == 300
    assert res["prognose"]["wahrscheinlich"] == 600
    assert res["vorjahr_stichtag"] == 200 and res["veraenderung_prozent"] == 50.0
    kurve = res["kurven"]["2026"]
    assert kurve[-1]["heute"] and kurve[-1]["wert"] == 300
    assert len(res["kurven"]["2025"]) == 24


def test_query_mit_stichtag():
    """Vergleich „Stichtag Vorjahr“ (Teil 2): Buchungsstand am 16.11.2025 kennt Buchung 2 noch nicht."""
    voll = query(R, "umsatz", "gesamt", date(2025, 1, 1), date(2026, 1, 1))
    stand = query(as_of(R, date(2025, 11, 16)), "umsatz", "gesamt", date(2025, 1, 1), date(2026, 1, 1))
    assert voll["zeilen"][0]["werte"]["Gesamt"]["wert"] == 500
    assert stand["zeilen"][0]["werte"]["Gesamt"]["wert"] == 200

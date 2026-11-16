"""Statistik-Werkbank (stats.py): Baukasten-Abfrage und Pace-Modell ohne HA."""
from datetime import date

import pytest

from custom_components.smoobu.analytics import as_of, build_records
from custom_components.smoobu.stats import gaps, pace, query, response_times, service, storno
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


G = recs(
    bk(11, "2026-05-01", "2026-05-04", "Airbnb", 300, **{"created-at": "2026-03-01 10:00"}),
    bk(12, "2026-05-06", "2026-05-10", "Booking.com", 400, **{"created-at": "2026-03-02 10:00"}),
    # Storno 05.–06.05., Änderungsdatum 20.04. → Storno-Vorlauf 15 Tage; Nächte danach nicht wiederbelegt
    bk(13, "2026-05-04", "2026-05-06", "Booking.com", 200, type="cancellation",
       **{"created-at": "2026-03-03 10:00", "modifiedAt": "2026-04-20 08:00:00"}),
)


def test_luecken_tagespreis_und_schaetzung():
    rates = {"2026-05-04": {"price": 90, "min_length_of_stay": 3}, "2026-05-05": {"price": 95, "min_length_of_stay": 3}}
    res = gaps(G, date(2026, 5, 1), date(2026, 6, 1), date(2026, 4, 1), rates_now=rates)
    (g,) = res["luecken"]
    assert g["naechte"] == 2 and g["wert"] == 185 and g["zu_kurz"] and g["quelle"] == "tagespreis"
    assert res["kommend"]["zu_kurz"] == 1 and res["vorschlaege"][0]["mindestaufenthalt"] == 3
    # Rückblick ohne gespeicherte Preise: Ø-Monatspreis Mai = 700 € / 7 Nächte = 100 €
    res = gaps(G, date(2026, 5, 1), date(2026, 6, 1), date(2026, 6, 1))
    (g,) = res["luecken"]
    assert g["vergangen"] and g["quelle"] == "geschaetzt" and g["wert"] == 200 and g["mindestaufenthalt"] is None
    # gespeicherte Historie hat Vorrang vor der Schätzung
    hist = {"2026-05-04": [80, 2], "2026-05-05": [80, 2]}
    (g,) = gaps(G, date(2026, 5, 1), date(2026, 6, 1), date(2026, 6, 1), price_history=hist)["luecken"]
    assert g["wert"] == 160 and not g["zu_kurz"] and g["quelle"] == "tagespreis"


def test_storno_auswertung():
    res = storno(G, date(2026, 5, 1), date(2026, 6, 1))
    assert res["stornos"] == 1 and res["buchungen"] == 3 and res["ausfall"] == 200
    assert res["wiederbelegt_naechte"] == 0 and res["vorlauf_median"] == 14
    booking = next(k for k in res["kanaele"] if k["kanal"] == "Booking.com")
    assert booking["quote"] == 50.0 and booking["wenig_daten"]


def test_antwortzeiten_und_service():
    msgs = [
        {"id": 1, "type": 1, "createdAt": "2026-05-01 10:00:00"},
        {"id": 2, "type": 1, "createdAt": "2026-05-01 10:20:00"},  # zweite Gastnachricht am Stück
        {"id": 3, "type": 2, "createdAt": "2026-05-01 10:45:00"},
        {"id": 4, "type": 2, "createdAt": "2026-05-02 09:00:00"},  # Nachricht ohne Frage
        {"id": 5, "type": "1", "createdAt": "2026-05-03 08:00:00"},
        {"id": 6, "type": 2, "createdAt": "2026-05-03 11:00:00"},
    ]
    assert response_times(msgs) == [45.0, 180.0]
    res = service(G, {"11": {"minuten": [45.0, 180.0]}}, date(2026, 5, 1), date(2026, 6, 1))
    assert res["gesamt"]["median"] == 112.5 and res["gesamt"]["unter_1h"] == 50.0
    assert res["buchungen"] == 3 and res["geladen"] == 1  # Stornos haben auch Nachrichten


def test_buchungszeitpunkt_matrix():
    """Aufenthaltsmonat × Monate vorher (Wunsch Betreiber): Nächte im März 2026, gebucht im Januar → „2 Monate“."""
    res = query(R, "naechte", "monat_im_jahr", date(2026, 1, 1), date(2027, 1, 1), split="vorlauf_monate")
    maerz = next(z for z in res["zeilen"] if z["fach"] == "03")
    assert maerz["werte"]["2 Monate"]["wert"] == 3
    res = query(R, "buchungen", "buchungsmonat_im_jahr", date(2025, 1, 1), date(2027, 1, 1))
    werte = {z["fach"]: z["werte"]["Gesamt"]["wert"] for z in res["zeilen"]}
    assert werte["02"] == 1 and werte["12"] == 1 and werte["01"] == 1

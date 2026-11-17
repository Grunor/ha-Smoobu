"""Bewertung & Preisempfehlung (empfehlung.py) ohne HA."""
from datetime import date, timedelta

import pytest

from custom_components.smoobu.analytics import build_records
from custom_components.smoobu.deckungsbeitrag import CostConfig, apply, build_table
from custom_components.smoobu.empfehlung import (
    PriceConfig,
    channel_factor,
    easter,
    floor_price,
    holiday_nights,
    recommend,
)
from tests.test_analytics import bk, costs

TODAY = date(2026, 11, 10)


def _bookings():
    out, i = [], 100
    # Vorjahre 2023–2025: November früh gebucht (bis 10.11. schon 15 Nächte), Fr/Sa-lastig
    for y in (2023, 2024, 2025):
        for start_day in (3, 10, 17):
            i += 1
            out.append(bk(i, f"{y}-11-{start_day:02d}", f"{y}-11-{start_day + 5:02d}", "Booking.com", 400,
                          **{"created-at": f"{y}-10-01 10:00"}))
        for d in range(1, 120, 7):  # jede Woche Fr→So (2 Nächte) im Frühjahr
            day = date(y, 3, 6) + timedelta(days=d)
            if day.weekday() != 4:
                day += timedelta(days=(4 - day.weekday()) % 7)
            i += 1
            out.append(bk(i, day.isoformat(), (day + timedelta(days=2)).isoformat(), "Direct booking", 160,
                          **{"created-at": f"{y}-02-01 10:00"}))
        i += 1  # einige Einzelnächte
        out.append(bk(i, f"{y}-09-02", f"{y}-09-03", "Airbnb", 70, **{"created-at": f"{y}-08-20 10:00"}))
    # 2026: November bisher nur 3 Nächte, eine Lücke von 1 Nacht am 20.11.
    out.append(bk(900, "2026-11-04", "2026-11-07", "Direct booking", 186, **{"created-at": "2026-10-20 10:00"}))
    out.append(bk(901, "2026-11-18", "2026-11-20", "Direct booking", 124, **{"created-at": "2026-11-01 10:00"}))
    out.append(bk(902, "2026-11-21", "2026-11-23", "Airbnb", 160, **{"created-at": "2026-11-02 10:00"}))
    return out


R = build_records(_bookings(), costs, [], TODAY)
CFG = CostConfig()
TABLE = build_table(R, CFG)
apply(R, TABLE)
RATES = {(TODAY + timedelta(days=i)).isoformat(): {"price": 62, "min_length_of_stay": 1} for i in range(60)}
PCFG = PriceConfig(markups={"Airbnb": 33, "Booking.com": 45, "HomeToGo": 10},
                   commissions={"Airbnb": 15.5, "Booking.com": 15.0}, genius_discount=10, genius_share=100)


def test_feiertage():
    assert easter(2026) == date(2026, 4, 5) and easter(2025) == date(2025, 4, 20)
    nights = holiday_nights(2026)
    assert nights[date(2026, 12, 24)] == "Heiligabend" and nights[date(2026, 10, 31)] == "vor Allerheiligen"


def test_kanalfaktor_und_untergrenze():
    # Booking: Basispreis × 1,45 × (1 − 10 % Genius) × (1 − 16,4 % Kosten)
    f = channel_factor("Booking.com", 0.164, PCFG)
    assert f == pytest.approx(1.45 * 0.9 * 0.836)
    fl = floor_price(TABLE, date(2026, 1, 15), 2, f)
    assert fl == pytest.approx(TABLE.stay(date(2026, 1, 15), 2) / (2 * f))
    assert floor_price(TABLE, date(2026, 1, 15), 2, 0) is None


def test_bewertung_und_empfehlung():
    res = recommend(R, RATES, TABLE, PCFG, TODAY, first=date(2023, 1, 1))
    nov = res["monate"][0]
    assert nov["monat"] == "2026-11" and nov["vergleich"]["n"] == 3
    # Vorjahre am 10.11.: Buchungen vom 03.–08. und 10.–15. (an dem Tag schon gebucht) → deutlich mehr als 2026
    assert nov["bewertung"] == "schwach"
    assert nov["empfehlung"]["aktion"] == "senken" and nov["empfehlung"]["prozent"] in (-10, -15)
    # Neuer Preis nie unter der maßgeblichen Untergrenze
    assert nov["empfehlung"]["preis_neu"] >= nov["untergrenze_massgeblich"]
    # Monat außerhalb des Horizonts → halten mit Begründung
    jan = res["monate"][2]
    assert jan["monat"] == "2027-01" and jan["empfehlung"]["aktion"] == "halten"
    assert res["basispreis"]["einheitlich"] is True
    kanal = {k["kanal"]: k for k in res["kanaele"]}
    assert kanal["Booking.com"]["kostenquote_quelle"] == "gemessen" and kanal["Booking.com"]["genius"]
    assert kanal["HomeToGo"]["kostenquote_quelle"] == "Option"


def test_hinweise():
    res = recommend(R, RATES, TABLE, PCFG, TODAY, first=date(2023, 1, 1))
    typen = {h["typ"]: h for h in res["hinweise"]}
    assert "einheitlich" in typen and "feiertag" in typen
    luecke = typen["luecke"]["luecken"][0]
    assert luecke["von"] == "2026-11-20" and luecke["naechte"] == 1 and luecke["untergrenze"] > 0
    feiertage = {t["datum"] for t in typen["feiertag"]["tage"]}
    assert "2026-12-24" in feiertage
    assert typen["wochenende"]["titel"].startswith("Wochenend-Aufschlag")

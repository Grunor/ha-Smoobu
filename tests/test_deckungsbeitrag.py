"""Variable Kosten und Deckungsbeitrag (deckungsbeitrag.py) ohne HA."""
from datetime import date

import pytest

from custom_components.smoobu.analytics import build_records
from custom_components.smoobu.deckungsbeitrag import (
    CostConfig,
    apply,
    build_table,
    config_from_options,
    ref_nights_by_month,
)
from custom_components.smoobu.stats import query
from tests.test_analytics import bk, costs

TODAY = date(2026, 11, 17)

R = build_records([
    # Bezugsjahr 2025: 3 Nächte Januar, 4 Nächte Juli
    bk(1, "2025-01-10", "2025-01-13", "Direct booking", 300),
    bk(2, "2025-07-01", "2025-07-05", "Direct booking", 400),
    # 2026: Booking 2 Nächte im Januar
    bk(3, "2026-01-20", "2026-01-22", "Booking.com", 200),
    bk(4, "2026-02-01", "2026-02-03", "Airbnb", 200, type="cancellation"),
], costs, [], TODAY)


def test_heizung_summe_entspricht_abrechnung():
    cfg = CostConfig(heating_year=500.0, hot_water_year=0.0, water_night=0, power_kwh=0, cleaning=0, laundry=0)
    table = build_table(R, cfg)
    nights = ref_nights_by_month(R, 2025)
    assert nights[1] == 3 and nights[7] == 4
    total = sum(table.night(date(2025, m, 15))["heizung"] * n for m, n in nights.items())
    assert total == pytest.approx(500.0)
    # Januar je Nacht deutlich teurer als Juli (170 ‰/31 Tage vs. 13,33 ‰/31 Tage)
    jan, jul = table.night(date(2026, 1, 5))["heizung"], table.night(date(2026, 7, 5))["heizung"]
    assert jan / jul == pytest.approx(170 / 13.33, rel=1e-3)
    # Oktober liegt dazwischen (Wunsch Betreiber: „Januar deutlich mehr als Oktober“)
    assert jul < table.night(date(2026, 10, 5))["heizung"] < jan


def test_strom_mischpreis_und_aufenthalt():
    cfg = CostConfig(heating_year=0, hot_water_year=0, water_night=0.5, power_kwh=10, grid_price=30, pv_value=10,
                     grid_share=(100,) + (0,) * 11, cleaning=17, laundry=5)
    table = build_table(R, cfg)
    assert table.night(date(2026, 1, 5))["strom"] == pytest.approx(3.0)   # 100 % Netz
    assert table.night(date(2026, 2, 5))["strom"] == pytest.approx(1.0)   # 100 % PV
    # 2 Nächte im Januar: 22 € Reinigung+Wäsche + 2 × (3,00 + 0,50)
    assert table.stay(date(2026, 1, 5), 2) == pytest.approx(29.0)


def test_deckungsbeitrag_je_buchung_und_kennzahl():
    recs = [dict(r) for r in R]
    table = build_table(recs, CostConfig(heating_year=0, hot_water_year=0, water_night=1, power_kwh=0,
                                         cleaning=17, laundry=5))
    apply(recs, table)
    b3 = next(r for r in recs if r["id"] == 3)
    assert b3["var_kosten"] == pytest.approx(24.0)  # 22 + 2 × 1
    assert b3["db"] == pytest.approx(b3["netto"] - 24.0)
    assert next(r for r in recs if r["id"] == 4)["db"] == 0.0  # Storno ohne Kosten
    res = query(recs, "db", "gesamt", date(2026, 1, 1), date(2026, 2, 1))
    assert res["zeilen"][0]["werte"]["Gesamt"]["wert"] == pytest.approx(round(b3["netto"] - 24.0, 2))
    res = query(recs, "db_revpar", "gesamt", date(2026, 1, 1), date(2026, 2, 1))
    assert res["zeilen"][0]["werte"]["Gesamt"]["wert"] == pytest.approx(round((b3["netto"] - 24.0) / 31, 2))


def test_optionen_mit_standardwerten():
    cfg = config_from_options({"cost_cleaning": 20, "cost_grid_share": [1, 2]})
    assert cfg.cleaning == 20 and cfg.laundry == 5.0
    assert len(cfg.grid_share) == 12 and cfg.grid_share[0] == 72  # ungültige Liste → Standard

"""v1.19.0: Stromkosten aus Zählerwerten – Aufenthalt ab Vorheizstart, Leerstand anteilig nach Nächten."""
from datetime import date, datetime, time

import pytest
from homeassistant.util import dt as dt_util

from custom_components.smoobu import deckungsbeitrag as db
from custom_components.smoobu.energie import Prices, allocate, average_kwh_per_night, hour_shares, price_ct

TZ = "Europe/Berlin"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_db_url, enable_custom_integrations):
    """Wie conftest, aber die Recorder-Datenbank muss vor `hass` vorbereitet sein (Recorder-Test unten)."""
    yield


def _ts(y, mo, d, h):
    return int(datetime(y, mo, d, h, tzinfo=dt_util.get_time_zone(TZ)).timestamp())


def _rec(rid, an, ab, n, **kw):
    return {"id": rid, "anreise": an, "abreise": ab, "naechte": n, "blockiert": False, "storniert": False,
            "check_in": None, "check_out": None, "netto": 100.0, **kw}


def test_price_ct_und_netzanteil():
    assert price_ct("0.305", "€/kWh") == 30.5 and price_ct("30.54", "ct/kWh") == 30.54 and price_ct("0.3", None) == 30.0
    assert price_ct("x", None) is None
    st = {"imp": {0: 1.0, 3600: 0.0}, "pv": {0: 1.0, 3600: 2.0}, "exp": {3600: 1.0}}
    assert hour_shares(st, ["imp"], ["exp"], ["pv"], [], []) == {0: 0.5, 3600: 0.0}
    # Preisverlauf: vor dem ersten Messwert der feste Preis, danach der jeweils letzte Wert
    p = Prices(30.0, 10.0, tuple([100] * 12), price_points=[(1000, 35.0), (2000, 40.0)])
    assert (p.grid(999), p.grid(1000), p.grid(1999), p.grid(5000)) == (30.0, 35.0, 35.0, 40.0)


def test_allocate_aufenthalt_und_leerstand():
    dt_util.set_default_time_zone(dt_util.get_time_zone(TZ))
    # 1 kWh je Stunde vom 1.11. 00:00 bis 3.11. 24:00 (72 h)
    hourly = {_ts(2026, 11, 1, 0) + i * 3600: 1.0 for i in range(72)}
    prices = Prices(grid_price=30.0, pv_value=10.0, month_share=tuple([100] * 12))  # 100 % Netz → 30 ct
    recs = [_rec(1, "2026-11-01", "2026-11-02", 1, check_in="16:00", check_out="10:00"),
            _rec(2, "2026-11-02", "2026-11-03", 1)]  # Standard 16:00 / 11:00
    res = allocate(recs, hourly, prices, time(16), time(11), preheat_hours=4, preheat={2: _ts(2026, 11, 2, 14)},
                   distribute_vacancy=True)
    b1, b2 = res["buchungen"][1], res["buchungen"][2]
    assert b1["kwh"] == 22.0                   # 12:00 (16 − 4 h) bis 10:00 = 22 h
    assert b2["kwh"] == 21.0                   # gemessener Vorheizstart 14:00 bis 11:00 = 21 h
    mo = res["monate"]["2026-11"]
    assert mo["kwh"] == 72.0 and mo["kwh_leerstand"] == 29.0 and mo["naechte"] == 2 and mo["netzanteil_prozent"] == 100.0
    # Leerstand 29 kWh × 0,30 € = 8,70 € anteilig nach Nächten (je 4,35 €)
    assert b1["kosten_leerstand"] == 4.35 and b1["kosten"] == round(22 * 0.3 + 4.35, 2)
    assert round(b1["kosten"] + b2["kosten"], 2) == round(72 * 0.3, 2)  # alle Stromkosten verteilt
    # Standard „separat“: Leerstand bleibt Fixkosten, Buchung trägt nur den Aufenthalt
    sep = allocate(recs, hourly, prices, time(16), time(11), preheat_hours=4, preheat={2: _ts(2026, 11, 2, 14)})
    assert sep["buchungen"][1]["kosten"] == round(22 * 0.3, 2) and sep["buchungen"][1]["kosten_leerstand"] == 0
    assert sep["monate"]["2026-11"]["kosten_leerstand"] == 8.7 and not sep["monate"]["2026-11"]["leerstand_verteilt"]
    from custom_components.smoobu.energie import vacancy_costs
    assert vacancy_costs(sep, date(2026, 11, 1), date(2026, 11, 16)) == {"kwh": 14.5, "kosten": 4.35}  # halber Monat
    # Buchung außerhalb des Messzeitraums bleibt geschätzt
    res2 = allocate([_rec(3, "2026-12-01", "2026-12-03", 2)], hourly, prices, time(16), time(11), 4)
    assert res2["buchungen"] == {}


def test_apply_gemessen_ersetzt_nur_strom():
    cfg = db.CostConfig(cleaning=10, laundry=0, heating_year=0, hot_water_year=0, water_night=0, power_kwh=5,
                        grid_price=30, pv_value=10, grid_share=tuple([100] * 12))
    table = db.CostTable(cfg, 0, 0)
    recs = [_rec(1, "2026-11-01", "2026-11-03", 2), _rec(2, "2026-11-05", "2026-11-06", 1)]
    db.apply(recs, table, {1: {"kwh": 20, "kosten": 6.0, "naechte_kosten": [3.0, 3.0]}})
    assert recs[0]["strom_quelle"] == "gemessen" and recs[0]["var_kosten"] == 16.0  # 10 Reinigung + 6 Strom
    assert recs[1]["strom_quelle"] == "geschätzt" and recs[1]["var_kosten"] == 11.5  # 10 + 5 kWh × 0,30


def test_durchschnitt_je_nacht():
    res = {"monate": {"2026-09": {"kwh": 90, "naechte": 10, "vollstaendig": True},
                      "2026-10": {"kwh": 60, "naechte": 10, "vollstaendig": True},
                      "2026-11": {"kwh": 5, "naechte": 1, "vollstaendig": False}}}
    assert average_kwh_per_night(res, date(2026, 11, 20)) == 7.5


async def test_messung_aus_recorder(recorder_mock, hass):
    """Ende-zu-Ende mit echter Recorder-Statistik (Wh → kWh), fester Preis-Entität und Netzanteil aus dem Energie-Dashboard."""
    from homeassistant.components.recorder.models import StatisticMeanType
    from homeassistant.components.recorder.statistics import async_import_statistics
    from pytest_homeassistant_custom_component.components.recorder.common import async_wait_recording_done

    from custom_components.smoobu.energie import EnergyData, measure

    await hass.config.async_set_time_zone(TZ)
    start = datetime(2026, 11, 1, 0, tzinfo=dt_util.get_time_zone(TZ))

    def series(sid, unit, per_hour):
        meta = {"has_sum": True, "mean_type": StatisticMeanType.NONE, "name": None, "source": "recorder",
                "statistic_id": sid, "unit_class": "energy", "unit_of_measurement": unit}
        rows, total = [], 0.0
        for i in range(72):
            total += per_hour
            rows.append({"start": start + __import__("datetime").timedelta(hours=i), "sum": total, "state": total})
        async_import_statistics(hass, meta, rows)

    series("sensor.fewo_strom", "Wh", 1000.0)   # 1 kWh je Stunde
    series("sensor.netzbezug", "kWh", 0.5)
    series("sensor.pv", "kWh", 0.5)             # Netzanteil 50 %
    await async_wait_recording_done(hass)
    hass.states.async_set("input_number.preis", "0.40", {"unit_of_measurement": "€/kWh"})

    data = EnergyData(hass)

    async def sources():
        return {"grid_from": ["sensor.netzbezug"], "grid_to": [], "solar": ["sensor.pv"], "bat_from": [], "bat_to": []}
    data.energy_sources = sources
    cfg = db.CostConfig(grid_price=30, pv_value=10, grid_share=tuple([100] * 12))
    opts = {"cost_power_source": "zaehler", "cost_power_entities": {"1": "sensor.fewo_strom"},
            "cost_price_entity": "input_number.preis", "cost_grid_share_auto": True}
    recs = {1: [_rec(7, "2026-11-01", "2026-11-02", 1)]}
    res = await measure(hass, data, opts, recs, cfg, time(16), time(11))
    b = res[1]["buchungen"][7]
    assert b["kwh"] == 23.0                                  # 12:00 bis 11:00
    assert res[1]["monate"]["2026-11"]["netzanteil_prozent"] == 50.0
    # Preis-Entität ist erst ab „jetzt“ bekannt → für November gilt der feste Netzpreis (30 ct):
    # 50 % × 30 ct + 50 % × 10 ct = 20 ct; Standard „separat“: nur der Aufenthalt (23 kWh) → 4,60 €
    assert b["kosten"] == 4.6 and res[1]["preis_entitaet"] == "input_number.preis" and res[1]["leerstand_modus"] == "separat"
    # „anteilig“: alle 72 kWh auf die Buchung → 14,40 €
    res = await measure(hass, data, {**opts, "cost_vacancy_mode": "anteilig"}, recs, cfg, time(16), time(11))
    assert res[1]["buchungen"][7]["kosten"] == 14.4
    # Modus konstant → keine Messung
    assert await measure(hass, data, {**opts, "cost_power_source": "konstant"}, recs, cfg, time(16), time(11)) == {}

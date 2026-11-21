"""v1.19.0: Stromkosten aus Zählerwerten – Aufenthalt ab Vorheizstart, Leerstand anteilig nach Nächten."""
from datetime import date, datetime, time

import pytest
from homeassistant.util import dt as dt_util

from custom_components.smoobu import deckungsbeitrag as db
from custom_components.smoobu.energie import (Prices, allocate, average_kwh_per_night, grid_share_mode, hour_shares, price_ct,
                                              sensor_shares)

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
    # v1.19.1b5: Netzanteil aus Sensor der Wohnung (0,25 kWh Netz je 1 kWh Verbrauch) statt Energie-Dashboard
    series("sensor.fewo_netz", "kWh", 0.25)
    await async_wait_recording_done(hass)
    sens = {**opts, "cost_grid_share_mode": "sensor", "cost_grid_share_entities": {"1": "sensor.fewo_netz"}}
    res = await measure(hass, data, sens, recs, cfg, time(16), time(11))
    assert res[1]["netzanteil_modus"] == "sensor" and res[1]["netzanteil_entitaet"] == "sensor.fewo_netz"
    assert res[1]["monate"]["2026-11"]["netzanteil_prozent"] == 25.0
    # 23 kWh × (25 % × 30 ct + 75 % × 10 ct = 15 ct) = 3,45 €
    assert res[1]["buchungen"][7]["kosten"] == 3.45
    # Jahreswert: kein Messwert → fester Anteil aus cfg (hier 100 % → 30 ct)
    res = await measure(hass, data, {**opts, "cost_grid_share_mode": "jahreswert"}, recs, cfg, time(16), time(11))
    assert res[1]["netzanteil_gemessen"] is False and res[1]["buchungen"][7]["kosten"] == 6.9


def test_apply_wasser_und_heizung_gemessen():
    """Wasser/Heizung aus Zähler ersetzen ihren Schätzanteil; Heizungszähler inkl. Warmwasser lässt dessen Schätzung weg."""
    cfg = db.CostConfig(cleaning=0, laundry=0, heating_year=0, hot_water_year=0, water_night=2, power_kwh=0,
                        grid_price=30, pv_value=10, grid_share=tuple([100] * 12))
    table = db.CostTable(cfg, heat_k=1.0, water_k=1.0)  # Heizung/WW > 0 je Nacht (Gradtage)
    base = [_rec(1, "2026-01-10", "2026-01-11", 1)]
    db.apply(base, table)
    est = base[0]["var_kosten"]
    recs = [_rec(1, "2026-01-10", "2026-01-11", 1)]
    measured = {"wasser": {"buchungen": {1: {"kwh": 0.2, "kosten": 1.0, "naechte_kosten": [1.0]}}},
                "heizung": {"inkl_warmwasser": True, "buchungen": {1: {"kwh": 30, "kosten": 3.0, "naechte_kosten": [3.0]}}}}
    db.apply(recs, table, measured)
    r = recs[0]
    assert r["wasser_quelle"] == r["heizung_quelle"] == "gemessen" and r["strom_quelle"] == "geschätzt"
    night = table.night(date(2026, 1, 10))
    assert r["var_kosten"] == round(est - night["wasser"] - night["heizung"] - night["warmwasser"] + 1.0 + 3.0, 2)


async def test_wasser_aus_recorder(recorder_mock, hass):
    """Wasserzähler in Litern → m³, fester Preis je m³, Leerstand separat."""
    from datetime import timedelta

    from homeassistant.components.recorder.models import StatisticMeanType
    from homeassistant.components.recorder.statistics import async_import_statistics
    from pytest_homeassistant_custom_component.components.recorder.common import async_wait_recording_done

    from custom_components.smoobu.energie import EnergyData, measure_meter

    await hass.config.async_set_time_zone(TZ)
    start = datetime(2026, 11, 1, 0, tzinfo=dt_util.get_time_zone(TZ))
    meta = {"has_sum": True, "mean_type": StatisticMeanType.NONE, "name": None, "source": "recorder",
            "statistic_id": "sensor.wasser", "unit_class": "volume", "unit_of_measurement": "L"}
    async_import_statistics(hass, meta, [{"start": start + timedelta(hours=i), "sum": 10.0 * (i + 1), "state": 10.0 * (i + 1)}
                                         for i in range(72)])  # 10 L je Stunde
    await async_wait_recording_done(hass)
    opts = {"cost_water_source": "zaehler", "cost_water_entities": {"1": "sensor.wasser"}, "cost_water_price": 5.0}
    res = await measure_meter(EnergyData(hass), "wasser", opts, {1: [_rec(7, "2026-11-01", "2026-11-02", 1)]}, time(16), time(11))
    b = res[1]["buchungen"][7]
    assert res[1]["einheit"] == "m³" and b["kwh"] == 0.23          # 23 h × 10 L = 0,23 m³
    assert b["kosten"] == round(0.23 * 5.0, 2)                      # 1,15 € (Leerstand separat)
    assert await measure_meter(EnergyData(hass), "wasser", {**opts, "cost_water_source": "konstant"}, {1: []}, time(16), time(11)) == {}


def test_reinigung_je_person():
    cfg = db.CostConfig(cleaning=17, laundry=5, heating_year=0, hot_water_year=0, water_night=0, power_kwh=0)
    table = db.CostTable(cfg, 0, 0)
    recs = [_rec(1, "2026-11-01", "2026-11-03", 2), _rec(2, "2026-11-05", "2026-11-06", 1)]
    db.apply(recs, table, cleaning={1: 30.0})
    assert recs[0]["reinigung_kosten"] == 30.0 and recs[0]["var_kosten"] == 35.0
    assert recs[1]["reinigung_kosten"] == 17.0 and recs[1]["var_kosten"] == 22.0
    # Altwert „€ je Aufenthalt“ = Standard-Stundenlohn bei 60 min → gleicher Betrag
    assert db.config_from_options({"cost_cleaning": 17.0}).cleaning == 17.0
    assert db.config_from_options({"cost_cleaning": 20.0, "cost_cleaning_minutes": 90}).cleaning == 30.0


def test_sensor_shares_mit_luecken():
    """v1.19.1b5: Netzanteil aus Netz-Sensor ÷ Stromzähler; Lücken im Sensor (importierte Monats-/Tageszeilen) gemittelt."""
    h = 3600
    total = {i * h: 1.0 for i in range(10)}            # Zähler: 1 kWh je Stunde
    grid = {0: 0.0, 4 * h: 2.0, 5 * h: 0.5, 6 * h: 3.0}  # Anker, Lücke 1–4, Stunde 5, 6 ohne Zählerwerte > Zähler
    s = sensor_shares(grid, total)
    assert all(s[i * h] == 0.5 for i in range(1, 5))     # 2 kWh Netz über 4 Stunden à 1 kWh
    assert s[5 * h] == 0.5 and s[6 * h] == 1.0            # auf 100 % begrenzt
    assert s[0] == 0.0 and 7 * h not in s                 # nach der letzten Sensorzeile: Rückfallwert
    assert sensor_shares({3 * h: 1.0}, {}) == {}          # ohne Verbrauch kein Anteil


def test_netzanteil_modus_und_jahreswert():
    """Alter Schalter wird übernommen; Jahreswert gilt für alle Monate (auch bei Strom „konstant“)."""
    assert grid_share_mode({}) == "energie_dashboard"
    assert grid_share_mode({"cost_grid_share_auto": False}) == "monatswerte"
    assert grid_share_mode({"cost_grid_share_auto": False, "cost_grid_share_mode": "sensor"}) == "sensor"
    assert grid_share_mode({"cost_grid_share_mode": "quatsch", "cost_grid_share_auto": True}) == "energie_dashboard"
    cfg = db.config_from_options({"cost_grid_share_mode": "jahreswert", "cost_grid_share_year": 35})
    assert cfg.grid_share == tuple([35.0] * 12)
    assert db.config_from_options({"cost_grid_share_mode": "monatswerte"}).grid_share[0] == 72.0

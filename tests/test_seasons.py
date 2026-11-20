"""v1.18.0: einstellbare Saisons + automatische Erkennung."""
from datetime import date

import pytest
import voluptuous as vol

from custom_components.smoobu import seasons
from custom_components.smoobu.stats import query


def test_validate_and_map():
    s = seasons.validate([{"name": "Sommer", "start": 5}, {"name": " Winter ", "start": "11"}])
    assert s == [{"name": "Sommer", "start": 5}, {"name": "Winter", "start": 11}]
    m = seasons.month_map(s)
    assert m[1] == "Winter" and m[4] == "Winter" and m[5] == "Sommer" and m[10] == "Sommer" and m[11] == "Winter"
    assert seasons.order(s) == ["Winter", "Sommer"]
    assert seasons.order(None) == ["Winter", "Frühling", "Sommer", "Herbst"]
    for bad, code in (([{"name": "A", "start": 1}], "invalid_season_count"),
                      ([{"name": "A", "start": 1}, {"name": "a", "start": 5}], "invalid_season_duplicate_name"),
                      ([{"name": "A", "start": 1}, {"name": "B", "start": 1}], "invalid_season_duplicate_start"),
                      ([{"name": "A", "start": 13}, {"name": "B", "start": 1}], "invalid_season_start")):
        with pytest.raises(vol.Invalid) as err:
            seasons.validate(bad)
        assert str(err.value.msg) == code
    assert seasons.from_options({"saisons": "kaputt"}) == sorted(seasons.DEFAULT_SEASONS, key=lambda x: x["start"])


def _rec(i, arr, dep, price):
    n = (date.fromisoformat(dep) - date.fromisoformat(arr)).days
    return {"id": i, "anreise": arr, "abreise": dep, "naechte": n, "brutto": price, "netto": price, "blockiert": False,
            "storniert": False, "kanal": "Direkt", "gruppe": "Direkt", "wohnung": "A", "wohnung_id": 1, "personen": 2,
            "hund": False, "sprache": "de", "erstellt": arr, "vorlauf_tage": 10, "gast": None, "email": None, "gast_id": None,
            "var": 0.0, "var_preis": 0.0}


def test_query_custom_seasons():
    recs = [_rec(1, "2025-01-10", "2025-01-12", 200), _rec(2, "2025-07-01", "2025-07-04", 600)]
    cfg = [{"name": "Hauptsaison", "start": 6}, {"name": "Nebensaison", "start": 9}]
    r = query(recs, "naechte", "saison", date(2025, 1, 1), date(2026, 1, 1), seasons=cfg)
    rows = {z["fach"]: z["werte"]["Gesamt"]["wert"] for z in r["zeilen"]}
    assert rows == {"Nebensaison": 2, "Hauptsaison": 3}
    assert [z["fach"] for z in r["zeilen"]] == ["Nebensaison", "Hauptsaison"]  # Januar-Saison zuerst


def test_detect():
    # 3 Jahre: Jun–Sep voll und teuer, sonst kaum belegt → 2 Saisons Jun–Sep / Okt–Mai
    recs, i = [], 0
    for y in (2022, 2023, 2024):
        for m in range(1, 13):
            i += 1
            high = 6 <= m <= 9
            recs.append(_rec(i, f"{y}-{m:02d}-01", f"{y}-{m:02d}-{25 if high else 5:02d}", 2400 if high else 200))
    res = seasons.detect(recs, date(2025, 3, 1))
    two = next(v for v in res["vorschlaege"] if v["anzahl"] == 2)
    assert {s["name"]: s["monate"] for s in two["saisons"]} == {"Hauptsaison": [6, 7, 8, 9], "Nebensaison": [10, 11, 12, 1, 2, 3, 4, 5]}
    assert two["erklaert"] >= 80 and res["empfohlen"] == 2
    assert seasons.detect(recs[:12], date(2025, 3, 1))["grund"] == "zu_wenig_jahre"

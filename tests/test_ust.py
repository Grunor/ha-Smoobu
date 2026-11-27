"""v1.20.0: Umsatzsteuer (optional) – „USt-pflichtig seit“, Sätze mit Gültigkeit, Zuordnung, Ansicht, Kosten."""

from datetime import date

from custom_components.smoobu import ust

CFG = ust.opts_of({"ust_mode": "regel", "ust_since": "2026-01-01"})


def _r(**kw):
    r = {"id": 1, "anreise": "2026-03-01", "naechte": 2, "brutto": 214.0, "netto": 214.0, "gruppe": "Direkt",
         "blockiert": False, "storniert": False, "positionen": []}
    r.update(kw)
    return r


def test_aus_und_vor_stichtag_ohne_ust():
    assert ust.split(_r(), ust.opts_of({}))["ust"] == 0
    s = ust.split(_r(anreise="2025-12-20"), CFG)
    assert s["ust"] == 0 and s["ohne_ust"] == 214.0
    # Aufenthalt über den Jahreswechsel: nur die Nacht ab 01.01.2026 trägt USt
    s = ust.split(_r(anreise="2025-12-31"), CFG)
    assert s["naechte_ohne_ust"] == [107.0, 100.0] and s["ust"] == 7.0


def test_saetze_zuordnung_portal():
    s = ust.split(_r(), CFG)
    assert s["ust"] == 14.0 and s["ohne_ust"] == 200.0 and s["je_satz"] == {7.0: 14.0}
    # Frühstück 19 %, Kurtaxe steuerfrei – Bestandteile nach Namen
    cfg = ust.opts_of({"ust_mode": "regel", "ust_map": {"Frühstück": "regel", "Kurtaxe": "frei"}})
    r = _r(brutto=226.0, positionen=[{"name": "", "typ": "basePrice", "betrag": 107}, {"name": "Frühstück", "betrag": 119},
                                     {"name": "Kurtaxe", "betrag": 0}])
    s = ust.split(r, cfg)
    assert s["ohne_ust"] == 200.0 and s["je_satz"] == {7.0: 7.0, 19.0: 19.0}
    # Portal: alles mit einer Steuerart, Bestandteile egal
    assert ust.split(_r(gruppe="Portal", positionen=[{"name": "Frühstück", "betrag": 119}]), cfg)["ust"] == 14.0
    # Befristete Senkung 2. Halbjahr 2020
    cfg20 = ust.opts_of({"ust_mode": "regel"})
    assert ust.split(_r(anreise="2020-08-01", brutto=210.0), cfg20)["ust"] == 10.0


def test_lexware_netto_und_ansicht():
    s = ust.split(_r(), CFG, lex_net=200.01)
    assert s["ohne_ust"] == 200.01
    assert ust.split(_r(), CFG, lex_net=150.0)["ohne_ust"] == 200.0  # passt nicht → Berechnung gilt
    recs = [_r(var_kosten=20.0, var_kosten_ohne_ust=18.0, db=194.0)]
    ust.enrich(recs, CFG)
    r = recs[0]
    assert r["brutto_ohne_ust"] == 200.0 and r["netto_ohne_ust"] == 200.0 and r["db_ohne_ust"] == 182.0
    v = ust.view(recs, "ohne")[0]
    assert v["brutto"] == 200.0 and v["db"] == 182.0 and v["var_kosten"] == 18.0 and recs[0]["brutto"] == 214.0
    assert ust.view(recs, "brutto") is recs
    assert ust.revenue_by_month_net(recs) == {"2026-03": 200.0}
    assert ust.vat_by_month(recs, CFG) == {"2026-03": {"7.0": 14.0}}
    rows = [(date(2026, 3, 1), 1, "Direct", True, 107.0, 0, 0), (date(2026, 3, 2), 1, "Direct", True, 107.0, 0, 0)]
    assert [x[4] for x in ust.night_rows_net(rows, {1: r["naechte_ohne_ust"]})] == [100.0, 100.0]


def test_kosten_ohne_vorsteuer():
    d = date(2026, 3, 1)
    assert round(ust.cost_net("strom", 11.9, d, CFG), 2) == 10.0
    assert round(ust.cost_net("wasser", 10.7, d, CFG), 2) == 10.0
    assert ust.cost_net("reinigung", 17.0, d, CFG) == 17.0
    assert ust.cost_net("strom", 11.9, date(2025, 12, 31), CFG) == 11.9  # vor „USt-pflichtig seit“


def test_bestandteile():
    recs = [_r(positionen=[{"name": "", "typ": "basePrice", "betrag": 100}, {"name": "Hund", "betrag": 10}]),
            _r(positionen=[{"name": "", "typ": "cleaningFee", "betrag": 10}, {"name": "Hund", "betrag": 10}])]
    assert [e["name"] for e in ust.elements_seen(recs)] == ["Hund", "Grundpreis", "Reinigungsgebühr"]


# --- Ende zu Ende: Einstellungen → Auswertung, Info, Sensoren ----------------------------------------------
from custom_components.smoobu.const import DOMAIN  # noqa: E402

from .test_smoobu import setup  # noqa: E402,F401  (Fixture)


async def test_ust_ende_zu_ende(hass, setup, hass_ws_client):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/settings/set", "entry_id": entry.entry_id,
                        "changes": {"ust_mode": "regel", "ust_since": "2026-01-01"}})
    res = await ws.receive_json()
    assert res["result"]["ok"], res
    await hass.async_block_till_done()
    await ws.send_json({"id": 2, "type": "smoobu/info"})
    info = (await ws.receive_json())["result"]
    assert info["ust"] == {"aktiv": True, "ansicht": "ohne", "seit": "2026-01-01"}
    q = {"type": "smoobu/analytics", "start": "2026-11-01", "end": "2026-12-01", "compare": "kein"}
    await ws.send_json({"id": 3, **q})
    ohne = (await ws.receive_json())["result"]
    await ws.send_json({"id": 4, **q, "ust": "brutto"})
    brutto = (await ws.receive_json())["result"]
    assert ohne["umsatzsteuer"]["aktiv"] and ohne["umsatzsteuer"]["summe"] > 0
    assert abs(brutto["brutto"] - ohne["brutto"] - ohne["umsatzsteuer"]["summe"]) <= 0.05  # Rundung je Nacht/Monat
    # Einstellungen zeigen die Preisbestandteile aus den Buchungen zur Zuordnung
    await ws.send_json({"id": 5, "type": "smoobu/settings/get", "entry_id": entry.entry_id})
    meta = (await ws.receive_json())["result"]["meta"]
    assert any(b["name"] == "Endreinigung 1 Hund" for b in meta["ust"]["bestandteile"])

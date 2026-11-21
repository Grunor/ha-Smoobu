"""v1.19.0: Nebenkostenabrechnung hochladen, KI-Auswertung (gemockt), Vorschlag mit Prüfungen, Medienquelle."""
from unittest.mock import AsyncMock

from aiohttp import FormData

from custom_components.smoobu.const import DOMAIN
from custom_components.smoobu.nebenkosten import proposal

from .test_smoobu import setup  # noqa: F401  (Fixture)

KI = {"abrechnungsjahr": 2025, "zeitraum": "01.01.–31.12.2025", "heizkosten_eur": 480.0, "warmwasser_eur": 150.0,
      "wasser_eur": 100.0, "strom_kwh": 1000.0, "strom_eur": 320.0, "strompreis_ct": 31.0,
      "fundstellen": "heizkosten_eur: Seite 2 – Heizkosten FeWo 480,00 €\nstrom_kwh: Seite 3 – 1.000 kWh",
      "hinweise": "Faktor Warmwasser 0,6 kWh/l wirkt hoch"}


def _rec(an, ab, n):
    return {"id": 1, "anreise": an, "abreise": ab, "naechte": n, "blockiert": False, "storniert": False}


def test_vorschlag_und_pruefungen():
    recs = [_rec("2025-03-01", "2025-03-11", 10), _rec("2025-07-01", "2025-07-11", 10)]  # 20 Gästenächte 2025
    p = proposal({**KI, "gaestenaechte": 30}, {"cost_heating_year": 473.31}, recs, measured_kwh={2025: 700.0})
    by = {w["key"]: w for w in p["werte"]}
    assert p["naechte"] == 20 and p["naechte_quelle"] == "smoobu"
    assert by["cost_heating_year"]["neu"] == 480.0 and by["cost_heating_year"]["alt"] == 473.31
    assert by["cost_heating_year"]["fundstelle"].startswith("Seite 2")
    assert by["cost_water_night"]["neu"] == 5.0 and by["cost_power_kwh"]["neu"] == 50.0
    assert by["cost_power_kwh"]["status"] == "pruefen" and "Zähler in HA misst 700" in by["cost_power_kwh"]["hinweis"]
    assert by["cost_grid_price"]["neu"] == 31.0 and by["cost_ref_year"]["neu"] == 2025
    assert any("Gästenächte laut Dokument 30" in c for c in p["pruefungen"])
    assert "0,6" in p["hinweise_ki"]
    # Ohne Arbeitspreis: aus Kosten ÷ kWh; ohne Nächte keine Werte je Nacht
    p = proposal({"strom_kwh": 1000, "strom_eur": 320, "wasser_eur": 50, "abrechnungsjahr": 2019}, {}, [])
    keys = {w["key"] for w in p["werte"]}
    assert "cost_water_night" not in keys and {w["key"]: w for w in p["werte"]}["cost_grid_price"]["neu"] == 32.0
    assert any("Keine Gästenächte" in c for c in p["pruefungen"])


async def test_upload_auswertung_und_medienquelle(hass, setup, hass_client, hass_ws_client):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    c = entry.runtime_data
    c.assistant._ai = AsyncMock(return_value=KI)
    # media_source vor dem HTTP-Client einrichten: danach ist der Router eingefroren (in CI sonst
    # „Cannot register a resource into frozen router“, je nach Lade-Reihenfolge der Komponenten)
    from homeassistant.setup import async_setup_component
    assert await async_setup_component(hass, "media_source", {})
    await hass.async_block_till_done()
    client = await hass_client()
    form = FormData()
    form.add_field("datei", b"%PDF-1.4 demo", filename="Nebenkosten 2025.pdf", content_type="application/pdf")
    resp = await client.post(f"/api/smoobu/nebenkosten/{entry.entry_id}", data=form)
    assert resp.status == 200
    item = await resp.json()
    assert item["fehler"] is None and item["jahr"] == 2025 and item["name"] == "Nebenkosten 2025.pdf"
    werte = {w["key"]: w for w in item["auswertung"]["vorschlag"]["werte"]}
    assert werte["cost_heating_year"]["neu"] == 480.0
    # Anhang zeigt auf die eigene Medienquelle
    kwargs = c.assistant._ai.call_args.kwargs
    assert kwargs["attachments"][0]["media_content_id"] == f"media-source://smoobu/{entry.entry_id}/{item['datei']}"
    # Medienquelle löst auf (Pfad im Belegordner), Durchsuchen gesperrt, fremde Pfade abgelehnt
    from homeassistant.components.media_source import MediaSourceItem
    from homeassistant.components.media_player import BrowseError
    from homeassistant.components.media_source.error import Unresolvable
    import pytest

    from custom_components.smoobu.media_source import SmoobuBelege
    src = SmoobuBelege(hass)
    play = await src.async_resolve_media(MediaSourceItem(hass, DOMAIN, f"{entry.entry_id}/{item['datei']}", None))
    assert play.mime_type == "application/pdf" and play.path.read_bytes().startswith(b"%PDF")
    with pytest.raises(Unresolvable):
        await src.async_resolve_media(MediaSourceItem(hass, DOMAIN, f"{entry.entry_id}/../secrets.yaml", None))
    with pytest.raises(BrowseError):
        await src.async_browse_media(MediaSourceItem(hass, DOMAIN, "", None))
    # Über HA selbst (wie ai_task): Medienquelle wird als Plattform gefunden
    from homeassistant.components import media_source
    res = await media_source.async_resolve_media(hass, f"media-source://smoobu/{entry.entry_id}/{item['datei']}", None)
    assert res.path == play.path
    # Liste, falscher Dateityp, Löschen
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/nebenkosten/list", "entry_id": entry.entry_id})
    assert len((await ws.receive_json())["result"]["belege"]) == 1
    form = FormData()
    form.add_field("datei", b"MZ...", filename="virus.exe")
    assert (await client.post(f"/api/smoobu/nebenkosten/{entry.entry_id}", data=form)).status == 400
    await ws.send_json({"id": 2, "type": "smoobu/nebenkosten/delete", "entry_id": entry.entry_id, "beleg_id": item["id"]})
    assert (await ws.receive_json())["result"]["belege"] == []
    assert not play.path.exists()


async def test_upload_ohne_recht(hass, setup, hass_client, hass_read_only_access_token, hass_read_only_user):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    hass.config_entries.async_update_entry(entry, options={**entry.options, "user_roles": {hass_read_only_user.id: "betrieb"}})
    await hass.async_block_till_done()
    client = await hass_client(hass_read_only_access_token)
    form = FormData()
    form.add_field("datei", b"%PDF-1.4", filename="a.pdf")
    assert (await client.post(f"/api/smoobu/nebenkosten/{entry.entry_id}", data=form)).status == 403

"""Benutzerrollen (rechte.py): Rollen, Prüfung in Websocket-Befehlen und Aktionen."""
from types import SimpleNamespace

import pytest

from homeassistant.core import Context
from homeassistant.exceptions import Unauthorized

from custom_components.smoobu import rechte
from custom_components.smoobu.const import DOMAIN

from .test_smoobu import setup  # noqa: F401  (Fixture)


async def _call(ws, msg_id, **msg):
    await ws.send_json({"id": msg_id, **msg})
    return await ws.receive_json()


def test_rollen_und_rechte():
    admin = SimpleNamespace(id="a", is_admin=True)
    ma2 = SimpleNamespace(id="l", is_admin=False)
    other = SimpleNamespace(id="o", is_admin=False)
    opts = {"user_roles": {"l": "mitarbeiter"}, "settings_users": ["o"]}
    assert rechte.role_of(admin, opts) == "admin" and rechte.role_of(None, opts) == "system"
    assert rechte.role_of(ma2, opts) == "mitarbeiter"
    assert rechte.role_of(other, opts) == "verwalter"  # Altwert „Einstellungen erlauben für“
    assert rechte.role_of(SimpleNamespace(id="x", is_admin=False), opts) == "betrieb"  # Standardrolle
    # Standard ab 1.19.0b5: Mitarbeiter ohne „Belegung ändern“, mit „Reinigung zuweisen“; Betrieb ohne „Preise“
    assert rechte.allowed(ma2, opts, "reinigung_zuweisen") and not rechte.allowed(ma2, opts, "belegung")
    assert not rechte.allowed(ma2, opts, "finanzen")
    assert not rechte.allowed(SimpleNamespace(id="x", is_admin=False), opts, "preise")
    assert not rechte.allowed(ma2, opts, "preise")
    assert rechte.allowed(None, opts, "preise")  # Automationen dürfen immer
    stripped = rechte.strip({"id": 1, "brutto": 100, "gast": "Max"}, rechte.ROLES["mitarbeiter"][1])
    assert stripped == {"id": 1, "gast": "Max"}
    assert rechte.strip({"id": 1, "gast": "Max", "email": "x"}, frozenset()) == {"id": 1}


async def test_websocket_und_aktionen(hass, setup, hass_ws_client, hass_read_only_access_token, hass_read_only_user):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    ws = await hass_ws_client(hass, hass_read_only_access_token)
    # Ohne Eintrag: Standardrolle „betrieb“ → Finanzen erlaubt, Einstellungen nicht
    info = (await _call(ws, 1, type="smoobu/info"))["result"]
    assert info["wohnungen"][0]["zugriff"]["rolle"] == "betrieb"
    assert (await _call(ws, 2, type="smoobu/analytics"))["success"] is True

    # Rolle „mitarbeiter“: keine Finanzen, Buchungen ohne Preise, keine Preisänderung
    hass.config_entries.async_update_entry(entry, options={**entry.options, "user_roles": {hass_read_only_user.id: "mitarbeiter"}})
    await hass.async_block_till_done()
    res = await _call(ws, 3, type="smoobu/analytics")
    assert res["success"] is False and res["error"]["code"] == "unauthorized"
    res = await _call(ws, 4, type="smoobu/stats", mode="query", measure="umsatz", dimension="monat")
    assert res["error"]["code"] == "unauthorized"
    buchungen = (await _call(ws, 5, type="smoobu/bookings"))["result"]["buchungen"]
    assert buchungen and "brutto" not in buchungen[0] and "gast" in buchungen[0]
    ctx = Context(user_id=hass_read_only_user.id)
    with pytest.raises(Unauthorized):
        await hass.services.async_call(DOMAIN, "set_rates", {"start_date": "2026-12-01", "end_date": "2026-12-02", "price": 70},
                                       blocking=True, context=ctx)
    # Rolle „kein“: nicht einmal Buchungen
    hass.config_entries.async_update_entry(entry, options={**entry.options, "user_roles": {hass_read_only_user.id: "kein"}})
    await hass.async_block_till_done()
    res = await _call(ws, 6, type="smoobu/bookings")
    assert res["error"]["code"] == "unauthorized"

    # Rollen ändern nur Admins (auch ein Verwalter nicht)
    hass.config_entries.async_update_entry(entry, options={**entry.options, "user_roles": {hass_read_only_user.id: "verwalter"}})
    await hass.async_block_till_done()
    res = (await _call(ws, 7, type="smoobu/settings/set", changes={"user_roles": {hass_read_only_user.id: "kein"}}))["result"]
    assert res["fehler"] == {"user_roles": "admin_only"}


async def test_admin_vergibt_rollen(hass, setup, hass_ws_client, hass_read_only_user):  # noqa: F811
    ws = await hass_ws_client(hass)
    res = (await _call(ws, 1, type="smoobu/settings/get"))["result"]
    assert {r["id"] for r in res["meta"]["rollen"]["rollen"]} == set(rechte.ROLES)
    res = (await _call(ws, 2, type="smoobu/settings/set", changes={
        "user_roles": {hass_read_only_user.id: "lesen"}, "default_role": "mitarbeiter"}))["result"]
    await hass.async_block_till_done()
    assert res["ok"] is True
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.options["user_roles"] == {hass_read_only_user.id: "lesen"} and entry.options["default_role"] == "mitarbeiter"
    res = (await _call(ws, 3, type="smoobu/settings/set", changes={"user_roles": {"x": "chef"}}))["result"]
    assert res["fehler"] == {"user_roles": "invalid_role"}


async def test_aufgaben_board(hass, setup, hass_ws_client, hass_read_only_access_token, hass_read_only_user):  # noqa: F811
    """v1.18.0: Aufgaben erledigen/verschieben – gemeinsam gespeichert, Recht je Kategorie."""
    ws = await hass_ws_client(hass)
    res = (await _call(ws, 1, type="smoobu/tasks/get"))["result"]
    assert res["kategorien"] == ["nachrichten", "reinigung", "rechnungen", "preise", "lastminute", "luecken", "einrichtung"] and res["zustand"] == {}
    res = (await _call(ws, 2, type="smoobu/tasks/set", key="preis:123:2026-11:senken", kategorie="preise", aktion="spaeter", tage=2))["result"]
    assert res["zustand"]["preis:123:2026-11:senken"]["status"] == "spaeter"
    await _call(ws, 3, type="smoobu/tasks/set", key="msg:1:x", kategorie="nachrichten", aktion="erledigt")
    res = (await _call(ws, 4, type="smoobu/tasks/get"))["result"]
    assert set(res["zustand"]) == {"preis:123:2026-11:senken", "msg:1:x"}
    await _call(ws, 5, type="smoobu/tasks/set", key="msg:1:x", kategorie="nachrichten", aktion="zuruecksetzen")
    assert "msg:1:x" not in (await _call(ws, 6, type="smoobu/tasks/get"))["result"]["zustand"]
    # Mitarbeiter darf Nachrichten-Aufgaben erledigen, aber keine Preis-Aufgaben
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    hass.config_entries.async_update_entry(entry, options={**entry.options, "user_roles": {hass_read_only_user.id: "mitarbeiter"},
                                                          "task_categories": ["nachrichten"], "task_categories_rev": 3})
    await hass.async_block_till_done()
    guest = await hass_ws_client(hass, hass_read_only_access_token)
    assert (await _call(guest, 7, type="smoobu/tasks/get"))["result"]["kategorien"] == ["nachrichten"]
    # v1.18.0: ältere gespeicherte Auswahl ohne Marker → neue Kategorie „einrichtung“ wird ergänzt
    hass.config_entries.async_update_entry(entry, options={**entry.options, "task_categories_rev": 0})
    await hass.async_block_till_done()
    guest2 = await hass_ws_client(hass, hass_read_only_access_token)
    assert (await _call(guest2, 1, type="smoobu/tasks/get"))["result"]["kategorien"] == ["nachrichten", "reinigung", "einrichtung"]
    res = await _call(guest, 8, type="smoobu/tasks/set", key="preis:x", kategorie="preise", aktion="erledigt")
    assert res["error"]["code"] == "unauthorized"
    res = await _call(guest, 9, type="smoobu/tasks/set", key="msg:2:y", kategorie="nachrichten", aktion="erledigt")
    assert res["success"] is True


async def test_fokus_modus(hass, setup, hass_ws_client, hass_read_only_access_token, hass_read_only_user):  # noqa: F811
    """v1.19.0b7: Fokus-Modus – Standard für Rolle „Reinigung“, Startseite automatisch/einstellbar, Admins nie."""
    from custom_components.smoobu import settings

    admin = SimpleNamespace(id="a", is_admin=True)
    u = SimpleNamespace(id="u", is_admin=False)
    opts = {"user_roles": {"u": "reinigung"}, "assist_path": "/dashboard-fewo/smoobu-nachrichten"}
    assert rechte.focus_of(admin, opts) is None
    f = rechte.focus_of(u, opts)
    assert f["start"] == "/dashboard-fewo/smoobu-reinigung" and f["erlaubt"] == ["/dashboard-fewo/smoobu", "/dashboard-fewo/smoobu-reinigung", "/profile/security"]
    assert rechte.focus_of(u, {**opts, "user_roles": {"u": "betrieb"}}) is None
    f = rechte.focus_of(u, {**opts, "user_roles": {"u": "lesen"}, "focus_roles": {"lesen": ""}})
    assert f["start"] == "/dashboard-fewo/smoobu"
    f = rechte.focus_of(u, {**opts, "focus_roles": {"reinigung": "/x-y/smoobu-kalender"}})
    assert f["start"] == "/x-y/smoobu-kalender" and "/x-y/smoobu" in f["erlaubt"]
    assert rechte.focus_of(u, {**opts, "focus_roles": {}}) is None  # abgeschaltet

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    _v, err = settings.validate(hass, entry, {"focus_roles": {"reinigung": "javascript:alert(1)"}}, admin)
    assert err["focus_roles"] == "invalid_focus_path"
    _v, err = settings.validate(hass, entry, {"focus_roles": {"kein": ""}}, admin)
    assert err["focus_roles"] == "invalid_role"
    _v, err = settings.validate(hass, entry, {"focus_roles": {}}, u)
    assert err["focus_roles"] == "admin_only"

    hass.config_entries.async_update_entry(entry, options={**entry.options, "user_roles": {hass_read_only_user.id: "reinigung"}})
    await hass.async_block_till_done()
    ws = await hass_ws_client(hass, hass_read_only_access_token)
    await ws.send_json({"id": 1, "type": "smoobu/focus"})
    res = (await ws.receive_json())["result"]
    assert res["aktiv"] and res["start"].endswith("/smoobu-reinigung")
    adm = await hass_ws_client(hass)
    await adm.send_json({"id": 1, "type": "smoobu/focus"})
    assert (await adm.receive_json())["result"] == {"aktiv": False}


async def test_module_abschaltbar(hass, setup, hass_ws_client):  # noqa: F811
    """v1.19.0b10: Module Reinigung, Kosten, Preise abschaltbar (Standard an)."""
    from custom_components.smoobu import settings

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert all(settings.current(entry)[f"module_{m}"] for m in ("reinigung", "kosten", "preise"))
    vals, err = settings.validate(hass, entry, {"module_reinigung": False, "module_kosten": False, "module_preise": False}, None)
    assert not err
    hass.config_entries.async_update_entry(entry, options={**entry.options, "module_reinigung": False, "module_kosten": False,
                                                          "module_preise": False, "task_categories": ["nachrichten", "reinigung", "preise", "lastminute", "luecken"]})
    await hass.async_block_till_done()
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/info"})
    info = (await ws.receive_json())["result"]
    assert info["wohnungen"][0]["module"] == {"reinigung": False, "kosten": False, "preise": False}
    await ws.send_json({"id": 2, "type": "smoobu/cleaning/get"})
    assert (await ws.receive_json())["error"]["code"] == "module_off"
    await ws.send_json({"id": 3, "type": "smoobu/tasks/get"})
    assert [k for k in (await ws.receive_json())["result"]["kategorien"] if k != "einrichtung"] == ["nachrichten", "luecken"]
    await ws.send_json({"id": 4, "type": "smoobu/stats", "mode": "meta"})
    ids = {k["id"] for k in (await ws.receive_json())["result"]["kennzahlen"]}
    assert "db" not in ids and "netto" in ids
    await ws.send_json({"id": 5, "type": "smoobu/nebenkosten/list", "entry_id": entry.entry_id})
    assert (await ws.receive_json())["success"] is False
    # Fokus-Startseite ohne Modul Reinigung: Übersicht
    u = SimpleNamespace(id="u", is_admin=False)
    assert rechte.focus_of(u, {**entry.options, "user_roles": {"u": "reinigung"}})["start"].endswith("/smoobu")

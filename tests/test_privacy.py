"""Datenschutz für KI-Anfragen (v1.18.0b6): Stufen, Pseudonymisierung, Schwärzung, Vorschau."""

from datetime import date

from homeassistant.core import SupportsResponse

from custom_components.smoobu import privacy
from custom_components.smoobu.const import DOMAIN  # noqa: F401

from .test_smoobu import BASE, mock_api, setup  # noqa: F401  (Fixture)


# ---------------------------------------------------------------------------
# Reine Funktionen
# ---------------------------------------------------------------------------
def test_levels_and_defaults():
    # Ohne gespeicherte Stufe (bestehende Installation) gilt „standard“ (Entscheidung Betreiber)
    assert privacy.level({}) == "standard" and privacy.level({"ai_privacy": "quatsch"}) == "standard"
    std = privacy.resolve({})
    assert std["ai_pseudonym"] and std["ai_history"] == 6 and std["ai_examples"] and std["ai_send_payment"]
    strict = privacy.resolve({"ai_privacy": "streng"})
    assert strict["ai_history"] == 2 and not strict["ai_send_payment"] and strict["ai_examples"]
    mx = privacy.resolve({"ai_privacy": "maximal"})
    assert mx["ai_history"] == 0 and not any(mx[k] for k in ("ai_examples", "ai_status", "ai_send_dates", "ai_send_guests"))
    # Einzelschalter wirken nur bei „individuell“
    assert privacy.resolve({"ai_examples": False})["ai_examples"] is True
    custom = privacy.resolve({"ai_privacy": "individuell", "ai_examples": False, "ai_history": 99})
    assert custom["ai_examples"] is False and custom["ai_history"] == 6 and custom["ai_pseudonym"] is True
    # Eigene Namen: Option, sonst Wörter des Kontonamens
    assert privacy.host_names({}, "Anna & Ben Beispiel") == ["Anna", "Ben", "Beispiel"]
    assert privacy.host_names({"ai_host_names": ["Ben"]}, "Anna & Ben Beispiel") == ["Ben"]


def test_pseudonymize_and_restore():
    ps = privacy.Pseudonymizer(["Clara", "Ben"])
    rec = {"gast": "Thomas Müller-Lüdenscheidt", "vorname": "Thomas", "nachname": "Müller-Lüdenscheidt",
           "anreise": "2026-11-21", "abreise": "2026-11-23"}
    out = ps.apply("Hi Ben, THOMAS Müller-Lüdenscheidt here. Thomas & family. Grüße Clara, Ben", rec)
    assert out == "Hi Ben, [GAST_NAME] here. [GAST_VORNAME] & family. Grüße Clara, Ben"
    # Teilwort bleibt (Thomasson ist ein anderes Wort), Umlaute/Akzente als Wortgrenze
    assert ps.apply("Thomasson grüßt", rec) == "Thomasson grüßt"
    # Nur voller Name bekannt → erster Teil Vorname, Rest Nachname
    assert ps.apply("Danke Anna, viele Grüße an Herrn Beispiel", {"gast": "Anna Beispiel"}) == \
        "Danke [GAST_VORNAME], viele Grüße an Herrn [GAST_NACHNAME]"
    # Gastname = eigener Name → bleibt (sonst würde eure Signatur ersetzt)
    assert ps.apply("Grüße, Ben", {"gast": "Ben Schmidt", "vorname": "Ben"}) == "Grüße, Ben"
    assert privacy.restore("Hallo [GAST_VORNAME], bis [ANREISE]!", rec) == "Hallo Thomas, bis 21.11.2026!"
    assert privacy.restore("Frage von [GAST_NAME]", rec, generic=True) == "Frage von Gast"


def test_redact_extended():
    text = ("Wir wohnen Hauptstraße 12a, 10115 Berlin. Parkplatz 2 ok? Kennzeichen AN-RG 123, "
            "geb. 03.04.1985, Ausweisnr: L01X00T47. 12 Baker Street. Rundweg 3 km, um 16 Uhr.")
    assert privacy.redact_extended(text) == (
        "Wir wohnen [ADRESSE], [PLZ ORT]. Parkplatz 2 ok? Kennzeichen [KENNZEICHEN], "
        "geb. [GEBURTSDATUM], Ausweisnr: [AUSWEIS]. [ADRESSE]. Rundweg 3 km, um 16 Uhr.")


def test_relative_dates():
    today = date(2026, 11, 17)
    assert privacy.relative("2026-11-21", today) == "Sa., in 4 Tagen"
    assert privacy.relative("2026-11-17", today) == "Di., heute"
    assert privacy.relative("2026-11-15", today) == "So., vor 2 Tagen"


# ---------------------------------------------------------------------------
# Integration: was wirklich an die KI geht
# ---------------------------------------------------------------------------
def _fake_ai(hass, prompts, answer="Hallo [GAST_VORNAME], bis [ANREISE]! Liebe Grüße"):
    async def fake(call):
        prompts.append(call.data["instructions"])
        return {"data": {"antwort": answer, "absicht": "frage", "dringend": False,
                         "wissensluecke": "Darf [GAST_VORNAME] parken?"}}

    hass.services.async_register("ai_task", "generate_data", fake, supports_response=SupportsResponse.ONLY)


async def _prepare(hass, setup, aioclient_mock, **opts):  # noqa: F811
    hass.states.async_set("sensor.aktueller_gast", "Anna Beispiel", {"friendly_name": "Aktueller Gast"})
    hass.config_entries.async_update_entry(setup, options={
        **setup.options, "assistant": False, "ai_entity": "ai_task.fake", "ai_enabled": True,
        # Testkonto heißt „Max Host“; Gast 2 heißt Max Mustermann → eigene Namen hier nur „Host“
        "ai_host_names": ["Host"], "assist_status": ["sensor.aktueller_gast"], **opts})
    await hass.async_block_till_done()
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE}/api/reservations/2/messages", json={"page_count": 1, "messages": [
        {"id": 6, "type": 2, "message": "Hallo Max, danke für die Buchung!"},
        {"id": 7, "type": 1, "message": "Hi, hier Max Mustermann. Wir wohnen Hauptstraße 5, 10115 Berlin, "
                                        "Kennzeichen AN-MM 42. Wann können wir rein?"}]})
    mock_api(aioclient_mock)
    a = hass.config_entries.async_get_entry(setup.entry_id).runtime_data.assistant
    # Lernbeispiel aus der Buchung von Anna (anderer Gast) – ihr Name darf nicht an die KI
    a.learn(1, "Hallo, Anna hier. Gibt es WLAN?", "Hallo Anna, ja – das WLAN steht im Hausbuch. Liebe Grüße", "smoobu")
    return a


async def test_standard_prompt(hass, setup, aioclient_mock):  # noqa: F811
    prompts: list[str] = []
    _fake_ai(hass, prompts)
    a = await _prepare(hass, setup, aioclient_mock)
    sug = await a.suggest(2, "antwort")
    p = prompts[-1]
    for leak in ("Mustermann", "Max", "Anna", "Beispiel", "Hauptstraße", "10115", "AN-MM", "2026-11-18"):
        assert leak not in p, leak
    assert "[GAST_VORNAME]" in p and "[ADRESSE]" in p and "[KENNZEICHEN]" in p and "[ANREISE] (" in p
    assert "Hallo [GAST_VORNAME], ja – das WLAN" in p  # Beispiel mit Platzhalter statt „Anna“
    assert "Aktueller Gast: [GAST_NAME]" in p  # Status-Entität mit Gastnamen geschützt
    assert "Kanal Direct booking" in p and "Gastgeber: Hallo [GAST_VORNAME], danke" in p
    # Antwort lokal zurückgesetzt, Wissenslücke neutral
    assert sug["antwort"] == "Hallo Max, bis 18.11.2026! Liebe Grüße"
    assert sug["wissensluecke"] == "Darf Gast parken?"
    assert a.last_prompt["text"] == p and a.last_prompt["stufe"] == "standard"


async def test_strict_and_maximal(hass, setup, aioclient_mock):  # noqa: F811
    prompts: list[str] = []
    _fake_ai(hass, prompts)
    a = await _prepare(hass, setup, aioclient_mock, ai_privacy="streng")
    await a.suggest(2, "antwort")
    assert "Kanal" not in prompts[-1] and "bezahlt" not in prompts[-1]
    assert prompts[-1].count("Gastgeber: Hallo") == 2  # 1 Beispiel + 1 Nachricht aus dem Verlauf (2 Nachrichten)

    a = await _prepare(hass, setup, aioclient_mock, ai_privacy="maximal")
    await a.suggest(2, "antwort")
    p = prompts[-1]
    assert "WLAN steht im Hausbuch" not in p and "danke für die Buchung" not in p
    assert "Aktueller Gast" not in p and "Erwachsene" not in p and "Anreise" not in p.split("BUCHUNG:")[1].split("\n")[0]
    assert "Wann können wir rein?" in p  # Gästenachricht selbst geht immer mit

    # Individuell ohne Pseudonymisierung → Name geht mit (bewusste Wahl)
    a = await _prepare(hass, setup, aioclient_mock, ai_privacy="individuell", ai_pseudonym=False)
    await a.suggest(2, "antwort")
    assert "Max Mustermann" in prompts[-1]


async def test_preview(hass, setup, aioclient_mock, hass_ws_client):  # noqa: F811
    prompts: list[str] = []
    _fake_ai(hass, prompts)
    await _prepare(hass, setup, aioclient_mock, ai_enabled=False)  # Probelauf geht auch bei gesperrter KI
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/assistant/preview"})
    res = (await ws.receive_json())["result"]
    assert res["quelle"] == "letzte" and res["text"] is None and res["stufe"] == "standard"
    await ws.send_json({"id": 2, "type": "smoobu/assistant/preview", "reservation_id": 2})
    res = (await ws.receive_json())["result"]
    assert res["quelle"] == "vorschau" and "[GAST_VORNAME]" in res["text"] and "Mustermann" not in res["text"]
    assert prompts == []  # Vorschau ruft die KI nie auf


async def test_settings_privacy(hass, setup, hass_ws_client):  # noqa: F811
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "smoobu/settings/get"})
    werte = (await ws.receive_json())["result"]["werte"]
    assert werte["ai_privacy"] == "standard" and werte["ai_history"] == 6 and werte["ai_host_names"] == ["Max", "Host"]
    await ws.send_json({"id": 2, "type": "smoobu/settings/set", "changes": {"ai_privacy": "geheim", "ai_history": 9}})
    res = (await ws.receive_json())["result"]
    assert res["ok"] is False and set(res["fehler"]) == {"ai_privacy", "ai_history"}
    await ws.send_json({"id": 3, "type": "smoobu/settings/set", "changes": {
        "ai_privacy": "individuell", "ai_examples": False, "ai_host_names": ["Host"]}})
    assert (await ws.receive_json())["result"]["ok"] is True
    await hass.async_block_till_done()
    assert privacy.resolve(setup.options)["ai_examples"] is False and setup.options["ai_host_names"] == ["Host"]


async def test_options_flow_privacy(hass, setup):  # noqa: F811
    result = await hass.config_entries.options.async_init(setup.entry_id)
    while result["step_id"] != "assistent":
        result = await hass.config_entries.options.async_configure(result["flow_id"], user_input={})
    keys = {str(k) for k in result["data_schema"].schema}
    assert {"ai_privacy", "datenschutz_einzeln"} <= keys
    result = await hass.config_entries.options.async_configure(result["flow_id"], user_input={
        "ai_enabled": False, "assistant": False, "ai_privacy": "individuell",
        "datenschutz_einzeln": {"ai_history": 3, "ai_examples": False, "ai_host_names": "Max; Host"}})
    while result["type"] == "form":
        result = await hass.config_entries.options.async_configure(result["flow_id"], user_input={})
    data = result["data"]
    assert data["ai_privacy"] == "individuell" and data["ai_history"] == 3 and data["ai_examples"] is False
    assert data["ai_pseudonym"] is True and data["ai_host_names"] == ["Max", "Host"]
    assert "datenschutz_einzeln" not in data

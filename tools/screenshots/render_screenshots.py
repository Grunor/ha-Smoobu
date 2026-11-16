"""README-Screenshots mit Demodaten erzeugen (ab v1.14.0).

Aufruf (aus dem Repo-Stamm):
    pip install pytest-homeassistant-custom-component playwright
    python -m pytest tools/screenshots/render_screenshots.py -p no:cacheprovider
Ergebnis: docs/screenshots/*.png

Ablauf
------
1. Home Assistant (Testumgebung) startet die echte Integration; der Smoobu-Client
   wird durch `DemoClient` ersetzt (erfundene Wohnung, Gäste, Nachrichten).
2. Der KI-Assistent bekommt erfundene Wissenseinträge, Lernbeispiele und einen Vorschlag.
   Es wird keine KI aufgerufen.
3. Headless Chrome öffnet harness.html, verbindet sich per WebSocket mit dieser
   Instanz und rendert die echten Karten. Je Karte entsteht ein PNG.
4. Zum Schluss: KI per Option sperren → Screenshot der ausgegrauten KI-Bedienung.

Playwright läuft in einem eigenen Thread (sync API), damit die Ereignisschleife
von Home Assistant ungestört die WebSocket-Anfragen beantwortet.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

sys.path.insert(0, str(Path(__file__).parent))
from demo_data import DemoClient  # noqa: E402

from custom_components.smoobu.const import DOMAIN  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "screenshots"
HARNESS = Path(__file__).parent / "harness.html"
SCALE = float(os.environ.get("SMOOBU_SHOT_SCALE", "1.5"))  # Pixeldichte der PNGs

OPTIONS = {
    "ai_enabled": True,
    "assistant": True,
    "ai_entity": "ai_task.demo_ki",
    "assist_briefing": True,
    "assist_gaps": True,
    "default_checkin": "16:00",
    "default_checkout": "11:00",
    "checkout_buffer": 30,
}


def _shots(base: str, token: str, set_options) -> list[str]:
    """Läuft im Executor-Thread: Browser steuern, PNGs schreiben."""
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    done: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=os.environ.get("CHROME_PATH") or None, args=["--no-sandbox", "--lang=de-DE"]
        )
        page = browser.new_page(viewport={"width": 1212, "height": 900}, device_scale_factor=SCALE, locale="de-DE",
                                timezone_id="Europe/Berlin")
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        def start() -> None:
            page.goto(HARNESS.as_uri())
            page.evaluate("([b, t]) => setup(b, t)", [base, token])

        def card(name: str, type_: str, config: dict | None = None, *, width: int = 1180, prepare=None,
                 wait_text: str | None = None, dialog: bool = False) -> None:
            page.evaluate("([t, c, w]) => showCard(t, c, w)", [type_, config or {}, width])
            el = page.locator(type_)
            # Warten, bis die Karte geladen ist (kein „Laden …“ mehr)
            page.wait_for_function(
                "t => { const e = document.querySelector(t); const r = e && e.shadowRoot;"
                " return r && r.querySelector('ha-card') && !r.textContent.includes('Laden …'); }",
                arg=type_, timeout=20000,
            )
            if prepare:
                prepare(el)
            if wait_text:
                el.get_by_text(wait_text).first.wait_for(timeout=15000)
            page.wait_for_timeout(400)  # Diagramme/Layout setzen
            path = OUT / f"{name}.png"
            if dialog:
                # Das Dialog-Element selbst hat keine Größe (Inhalt liegt fixiert im Shadow-DOM)
                page.wait_for_function(
                    "() => { const d = document.querySelector('smoobu-booking-dialog');"
                    " return d && d.shadowRoot && d.shadowRoot.textContent.includes('Nachrichten'); }",
                    timeout=15000,
                )
                page.wait_for_timeout(800)
                page.screenshot(path=str(path), full_page=False)
            else:
                page.locator("#stage").screenshot(path=str(path))
            done.append(path.name)

        start()
        card("uebersicht", "smoobu-overview-card",
             {"entities": ["climate.ferienwohnung", "binary_sensor.ferienwohnung_eingangstuer",
                           "sensor.ferienwohnung_vorheizstart", "vacuum.ferienwohnung_saugroboter"]})
        card("belegungsplan", "smoobu-timeline-card", {"months": 3})
        card("buchungen", "smoobu-bookings-card")
        card("finanzen", "smoobu-analytics-card")
        card("posteingang", "smoobu-inbox-card", {"message_entity": "sensor.smoobu_letzte_gastenachricht"},
             prepare=lambda el: el.locator(".item", has_text="Lukas Berg").click(), wait_text="Keine Antwort nötig")
        card("assistent", "smoobu-assistant-card")
        page.set_viewport_size({"width": 1212, "height": 1000})
        card("buchungsdetails", "smoobu-bookings-card",
             prepare=lambda el: el.locator("tr[data-id]", has_text="Lukas Berg").first.click(), dialog=True)
        # v1.17.0: Buchung mit offener Zahlung + offener Anzahlung → Buttons „Zahlung/Anzahlung erhalten“
        card("buchungsdetails_zahlung", "smoobu-bookings-card",
             prepare=lambda el: el.locator("tr[data-id]", has_text="Lea Kraus").first.click(), dialog=True)

        # KI sperren (Option aus) → Seite neu laden, gesperrte Bedienung zeigen
        set_options({"ai_enabled": False})
        page.set_viewport_size({"width": 1212, "height": 900})
        start()
        card("ki_gesperrt_posteingang", "smoobu-inbox-card", {"message_entity": "sensor.smoobu_letzte_gastenachricht"},
             prepare=lambda el: el.locator(".item", has_text="Lukas Berg").click(), wait_text="KI gesperrt")
        card("ki_gesperrt_assistent", "smoobu-assistant-card", wait_text="KI gesperrt")
        browser.close()
        _optimize([OUT / f for f in done])
        if errors:
            raise AssertionError(f"Fehler im Browser: {errors}")
    return done


def _optimize(paths: list[Path]) -> None:
    """PNGs auf 256 Farben reduzieren (Screenshots → ca. ⅓ der Größe, Text bleibt scharf)."""
    from PIL import Image

    for p in paths:
        img = Image.open(p).convert("RGB")
        img.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(p, optimize=True)


def _demo_states(hass: HomeAssistant, today: date) -> None:
    """Erfundene HA-Entitäten für die Chips der Übersichtskarte."""
    hass.states.async_set("climate.ferienwohnung", "heat",
                          {"friendly_name": "Heizung", "current_temperature": 21.5, "temperature": 21})
    hass.states.async_set("binary_sensor.ferienwohnung_eingangstuer", "off",
                          {"friendly_name": "Eingangstür", "device_class": "door"})
    hass.states.async_set("sensor.ferienwohnung_vorheizstart", "14:30", {"friendly_name": "Vorheizstart"})
    hass.states.async_set("vacuum.ferienwohnung_saugroboter", "docked", {"friendly_name": "Saugroboter"})


def _demo_assistant(a, demo: DemoClient, today: date) -> None:
    """Wissensdatenbank, Lernbeispiele und ein offener Vorschlag – alles erfunden."""
    a.data.update({"wissen": [], "beispiele": [], "vorschlaege": {}})
    for thema, text, extra in [
        ("Check-in / Check-out", "Check-in ab 16 Uhr, Check-out bis 11 Uhr. Späte Anreise ist mit Schlüsselbox möglich.", {}),
        ("Parken", "Eigener Parkplatz direkt rechts nach dem Einfahrtstor.", {}),
        ("Hunde", "Hunde willkommen, 15 € Endreinigung je Hund. Näpfe und Decke vorhanden.", {}),
        ("Bäcker", "Bäckerei am Marktplatz, 5 Gehminuten, sonntags 7–11 Uhr geöffnet.", {}),
        ("E-Auto", "Wallbox 11 kW an der Garage, Abrechnung nach Verbrauch.", {}),
        ("Schlüsselbox", "Code wird am Anreisetag separat mitgeteilt.", {"vertraulich": True}),
        ("Fahrräder", "", {"status": "vorschlag", "quelle": "wissensluecke"}),
        ("Brötchenservice", "Auf Wunsch bis 18 Uhr am Vortag bestellbar.", {"status": "vorschlag", "quelle": "verlauf"}),
    ]:
        a.save_knowledge({"thema": thema, "text": text, **extra})
    recs = {r["gast"]: r for r in a.c.records_all() if r.get("gast")}
    jana = recs["Jana Winter"]["id"]
    a.learn(jana, "Hallo, dürfen wir unseren Hund mitbringen? Er ist ruhig und stubenrein.",
            "Hallo Jana, sehr gerne! Für den Hund berechnen wir 15 € Endreinigung. Näpfe und eine Decke sind da.",
            "verlauf", key="demo1")
    sophie = recs["Sophie Sommer"]["id"]
    a.learn(sophie, "Guten Morgen, gibt es ein Kinderbett? Unsere Tochter ist 2 Jahre alt.",
            "Hallo Sophie, ja, Reisebett und Hochstuhl stellen wir gerne bereit.", "gesendet", key="demo2")
    lukas = recs["Lukas Berg"]["id"]
    a.data["vorschlaege"][str(lukas)] = {
        "id": "demo0001", "buchung_id": lukas, "gast": "Lukas Berg", "anlass": "antwort",
        "gastnachricht": "Hi! Wir kommen erst gegen 20:30 Uhr an – ist das in Ordnung? Und gibt es in der Nähe einen Bäcker?",
        "nachricht_id": None,
        "antwort": ("Hallo Lukas,\n\n20:30 Uhr ist kein Problem – die Schlüsselbox ist ab 16 Uhr bereit, den Code "
                    "bekommst Du am Anreisetag. Die Bäckerei am Marktplatz ist 5 Gehminuten entfernt und hat "
                    "sonntags von 7 bis 11 Uhr geöffnet.\n\nGute Fahrt und bis heute Abend!"),
        "absicht": "spaete_anreise", "sprache": "de", "ankunftszeit": "20:30", "abreisezeit": None,
        "dringend": False, "hinweis": "Ankunftszeit 20:30 kann in Smoobu übernommen werden.", "wissensluecke": "",
        "zusammenfassung": "Gast kommt gegen 20:30 Uhr und fragt nach einem Bäcker.", "offen": False,
        "status": "offen", "erstellt": dt_util.now().isoformat(),
    }
    a._changed()


async def test_render_screenshots(socket_enabled, hass: HomeAssistant, aiohttp_client, hass_access_token) -> None:
    today = dt_util.now().date()
    await hass.config.async_set_time_zone("Europe/Berlin")
    hass.config.language = "de"
    await async_setup_component(hass, "http", {})
    demo = DemoClient(today)
    with patch("custom_components.smoobu.SmoobuClient", lambda *a, **k: demo):
        entry = MockConfigEntry(domain=DOMAIN, unique_id="1000", title="Demo",
                                data={"api_key": "demo", "api_secret": "demo", "user_id": 1000},
                                options={**OPTIONS, "use_webhook": False})
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        _demo_states(hass, today)
        _demo_assistant(entry.runtime_data.assistant, demo, today)
        await hass.async_block_till_done()
        client = await aiohttp_client(hass.http.app)
        base = f"http://127.0.0.1:{client.server.port}"
        loop = hass.loop

        def set_options(change: dict) -> None:
            """Aus dem Browser-Thread: Optionen ändern, Integration lädt neu, Demodaten wieder setzen."""
            async def run() -> None:
                hass.config_entries.async_update_entry(entry, options={**entry.options, **change})
                await hass.async_block_till_done()
                _demo_assistant(entry.runtime_data.assistant, demo, today)
            import asyncio
            asyncio.run_coroutine_threadsafe(run(), loop).result(60)

        files = await hass.async_add_executor_job(_shots, base, hass_access_token, set_options)
        print("Screenshots:", ", ".join(files))
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

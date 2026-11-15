"""Seiten-Screenshots im Design v1.15.0 (hell/dunkel, eine und drei Wohnungen).

Aufruf (aus dem Repo-Stamm):
    python -m pytest tools/screenshots/render_pages.py -p no:cacheprovider
Ergebnis: docs/screenshots/seite_*.png

Gleicher Aufbau wie render_screenshots.py (echte Integration + Demodaten), aber
je Bild eine ganze Smoobu-Seite: Kopfleiste + Karten untereinander. Mit
SMOOBU_WOHNUNGEN=3 entstehen zusätzlich die Bilder der Ansicht „Alle Wohnungen“.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

sys.path.insert(0, str(Path(__file__).parent))
from demo_data import DemoClient  # noqa: E402
from render_screenshots import OPTIONS, _demo_assistant, _demo_states, _optimize  # noqa: E402

from custom_components.smoobu.const import DOMAIN  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("SMOOBU_SHOT_DIR", ROOT / "docs" / "screenshots"))
HARNESS = Path(__file__).parent / "harness.html"
SCALE = float(os.environ.get("SMOOBU_SHOT_SCALE", "1.5"))
APTS = int(os.environ.get("SMOOBU_WOHNUNGEN", "1"))
CHIPS = ["climate.ferienwohnung", "binary_sensor.ferienwohnung_eingangstuer", "sensor.ferienwohnung_vorheizstart"]
PAGES = {
    "uebersicht": [["smoobu-header-card", {}], ["smoobu-overview-card", {"entities": CHIPS}]],
    "belegung": [["smoobu-header-card", {}], ["smoobu-timeline-card", {"months": 2}]],
    "buchungen": [["smoobu-header-card", {}], ["smoobu-bookings-card", {}]],
    "finanzen": [["smoobu-header-card", {}], ["smoobu-analytics-card", {}]],
    "nachrichten": [["smoobu-header-card", {}], ["smoobu-inbox-card", {"message_entity": "sensor.smoobu_letzte_gastenachricht"}]],
    "assistent": [["smoobu-header-card", {}], ["smoobu-assistant-card", {}]],
}


def _shots(base: str, token: str) -> list[str]:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    done: list[str] = []
    only = os.environ.get("SMOOBU_SEITEN")
    pages = {k: v for k, v in PAGES.items() if not only or k in only.split(",")}
    themes = os.environ.get("SMOOBU_MODI", "hell,dunkel").split(",")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--lang=de-DE"])
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=SCALE, locale="de-DE",
                                timezone_id="Europe/Berlin")
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        # Harness läuft als file:// → Schrift mit CORS-Kopf ausliefern (in HA gleiche Herkunft, dort unnötig)
        font = ROOT / "custom_components" / "smoobu" / "www" / "fonts" / "schibsted-grotesk.woff2"
        page.route("**/fonts/schibsted-grotesk.woff2", lambda r: r.fulfill(
            status=200, body=font.read_bytes(), headers={"Access-Control-Allow-Origin": "*", "Content-Type": "font/woff2"}))
        page.goto(HARNESS.as_uri())
        page.evaluate("([b, t]) => setup(b, t)", [base, token])
        variants = [("", None)] + ([("_alle", "alle")] if APTS > 1 else [])
        for suffix, apt in variants:
            for name, cards in pages.items():
                for theme in themes:
                    page.evaluate("([c, w, th, a]) => showPage(c, w, th, a)", [cards, 1440, theme, apt])
                    page.wait_for_function(
                        "() => [...document.querySelectorAll('#stage > *')].every(e => e.shadowRoot && e.shadowRoot.querySelector('ha-card')"
                        " && !e.shadowRoot.textContent.includes('Laden …'))", timeout=30000)
                    page.wait_for_timeout(700)
                    path = OUT / f"seite_{name}{suffix}_{theme}.png"
                    page.locator("#stage").screenshot(path=str(path))
                    done.append(path.name)
        browser.close()
    _optimize([OUT / f for f in done])
    if errors:
        raise AssertionError(f"Fehler im Browser: {errors[:5]}")
    return done


async def test_render_pages(socket_enabled, hass: HomeAssistant, aiohttp_client, hass_access_token) -> None:
    today = dt_util.now().date()
    await hass.config.async_set_time_zone("Europe/Berlin")
    hass.config.language = "de"
    await async_setup_component(hass, "http", {})
    demo = DemoClient(today, extra_apartments=APTS - 1)
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
        files = await hass.async_add_executor_job(_shots, f"http://127.0.0.1:{client.server.port}", hass_access_token)
        print("Seiten:", ", ".join(files))
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

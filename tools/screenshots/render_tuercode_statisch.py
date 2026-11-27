"""Screenshot Türcodes: statischer Code mit Gültigkeit und nächstem Code (v1.20.0), Einstellungen + Aufgabe.

Aufruf (aus dem Repo-Stamm):
    python -m pytest tools/screenshots/render_tuercode_statisch.py -p no:cacheprovider
Ergebnis: docs/screenshots/einstellungen_tuercode_statisch.png, tuercode_aufgabe.png
Es geht nichts an Smoobu (DemoClient protokolliert Schreibaktionen nur).
"""

from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

sys.path.insert(0, str(Path(__file__).parent))
from demo_data import APT, DemoClient  # noqa: E402

from custom_components.smoobu.const import DOMAIN  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "screenshots"
HARNESS = Path(__file__).parent / "harness.html"
SCALE = float(os.environ.get("SMOOBU_SHOT_SCALE", "1.5"))


class NoteDemo(DemoClient):
    async def update_reservation(self, reservation_id: int, body: dict[str, Any]) -> dict[str, Any]:
        return {}


def _shots(base: str, token: str) -> list[str]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH") or None, args=["--no-sandbox", "--lang=de-DE"])
        page = browser.new_page(viewport={"width": 1212, "height": 1400}, device_scale_factor=SCALE, locale="de-DE", timezone_id="Europe/Berlin")
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(HARNESS.as_uri())
        page.evaluate("([b, t]) => setup(b, t)", [base, token])
        page.evaluate("([t, c, w]) => showCard(t, c, w)", ["smoobu-settings-card", {"tab": "reinigung"}, 1180])
        page.wait_for_function("() => { const e = document.querySelector('smoobu-settings-card'); const r = e && e.shadowRoot;"
                               " return r && r.querySelector('[data-neu=tuercode]'); }", timeout=20000)
        page.wait_for_timeout(500)
        page.locator("smoobu-settings-card").locator('[data-neu="tuercode"]').screenshot(path=str(OUT / "einstellungen_tuercode_statisch.png"))
        page.evaluate("([t, c, w]) => showCard(t, c, w)", ["smoobu-overview-card", {}, 1400])
        page.wait_for_function("() => { const e = document.querySelector('smoobu-overview-card'); const r = e && e.shadowRoot;"
                               " return r && r.querySelector('[data-ttab=einrichtung]'); }", timeout=20000)
        page.locator("smoobu-overview-card").locator('[data-ttab="einrichtung"]').first.click()
        page.wait_for_function("() => { const e = document.querySelector('smoobu-overview-card'); const r = e && e.shadowRoot;"
                               " return r && r.textContent.includes('Türcode läuft ab'); }", timeout=20000)
        page.wait_for_timeout(500)
        page.locator("smoobu-overview-card").locator(".todo", has_text="Türcode läuft ab").first.screenshot(path=str(OUT / "tuercode_aufgabe.png"))
        browser.close()
        assert not errors, errors
    return ["einstellungen_tuercode_statisch.png", "tuercode_aufgabe.png"]


async def test_render_tuercode(socket_enabled, hass: HomeAssistant, aiohttp_client, hass_access_token) -> None:
    today = dt_util.now().date()
    await hass.config.async_set_time_zone("Europe/Berlin")
    hass.config.language = "de"
    await async_setup_component(hass, "http", {})
    demo = NoteDemo(today)
    lock = {"typ": "kein", "modus": "statisch", "code": "4711", "ab": f"{today.year}-01-01", "bis": (today + timedelta(days=10)).isoformat()}
    opts = {"default_checkin": "16:00", "default_checkout": "11:00", "use_webhook": False, "door_code_enabled": True,
            "door_locks": {str(APT["id"]): lock}}
    with patch("custom_components.smoobu.SmoobuClient", lambda *a, **k: demo):
        entry = MockConfigEntry(domain=DOMAIN, unique_id="1000", title="Demo",
                                data={"api_key": "demo", "api_secret": "demo", "user_id": 1000}, options=opts)
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        await entry.runtime_data.doorcodes.async_sync()
        client = await aiohttp_client(hass.http.app)
        base = f"http://127.0.0.1:{client.server.port}"
        files = await hass.async_add_executor_job(_shots, base, hass_access_token)
        print("Screenshots:", ", ".join(files))
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

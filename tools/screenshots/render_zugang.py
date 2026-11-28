"""Screenshot Zugangs-Anleitung (v1.20.0b4): Einstellungen → Benutzer & Rechte mit erzeugtem Text,
Reinigungsseite mit Button 🔑 „Passwort ändern“ (Fokus-Modus simuliert).

Aufruf (aus dem Repo-Stamm):
    python -m pytest tools/screenshots/render_zugang.py -p no:cacheprovider
Ergebnis: docs/screenshots/einstellungen_zugang.png, reinigung_passwort.png
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

from custom_components.smoobu.const import DOMAIN  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "screenshots"
HARNESS = Path(__file__).parent / "harness.html"
SCALE = float(os.environ.get("SMOOBU_SHOT_SCALE", "1.5"))
CARD = "smoobu-settings-card"


def _root(tag: str) -> str:
    return f"document.querySelector('{tag}') && document.querySelector('{tag}').shadowRoot"


def _shots(base: str, token: str) -> list[str]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH") or None, args=["--no-sandbox", "--lang=de-DE"])
        page = browser.new_page(viewport={"width": 1212, "height": 1800}, device_scale_factor=SCALE, locale="de-DE", timezone_id="Europe/Berlin")
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(HARNESS.as_uri())
        page.evaluate("([b, t]) => setup(b, t)", [base, token])
        page.evaluate("([t, c, w]) => showCard(t, c, w)", [CARD, {"tab": "rechte"}, 1180])
        page.wait_for_function(f"() => {{ const r = {_root(CARD)}; return r && r.querySelector('[data-guide]'); }}", timeout=20000)
        page.locator(CARD).locator("[data-guide]").first.click()
        page.wait_for_function(f"() => {{ const r = {_root(CARD)}; return r && r.querySelector('.sprop textarea'); }}", timeout=20000)
        page.wait_for_timeout(400)
        page.locator(CARD).locator('[data-neu="zugang"]').screenshot(path=str(OUT / "einstellungen_zugang.png"))
        page.evaluate("() => { window.__smoobuFocus = { aktiv: true }; }")
        page.evaluate("([t, c, w]) => showCard(t, c, w)", ["smoobu-cleaning-card", {}, 900])
        page.wait_for_function(f"() => {{ const r = {_root('smoobu-cleaning-card')}; return r && r.querySelector('[data-pw]'); }}", timeout=20000)
        page.wait_for_timeout(400)
        page.locator("smoobu-cleaning-card").locator(".head").screenshot(path=str(OUT / "reinigung_passwort.png"))
        browser.close()
        assert not errors, errors
    return ["einstellungen_zugang.png", "reinigung_passwort.png"]


async def test_render_zugang(socket_enabled, hass: HomeAssistant, aiohttp_client, hass_access_token,
                             hass_read_only_user) -> None:
    today = dt_util.now().date()
    await hass.config.async_set_time_zone("Europe/Berlin")
    hass.config.language = "de"
    hass.config.external_url = "https://abcd1234example.ui.nabu.casa"
    await async_setup_component(hass, "http", {})
    demo = DemoClient(today)
    await hass.auth.async_update_user(hass_read_only_user, name="Maria")
    opts = {"default_checkin": "16:00", "default_checkout": "11:00", "use_webhook": False,
            "user_roles": {hass_read_only_user.id: "reinigung"}, "zugang_sprachen": {hass_read_only_user.id: "de"},
            "zugang_kontakt_name": "René", "zugang_kontakt_telefon": "0170 1234567"}
    with patch("custom_components.smoobu.SmoobuClient", lambda *a, **k: demo):
        entry = MockConfigEntry(domain=DOMAIN, unique_id="1000", title="Demo",
                                data={"api_key": "demo", "api_secret": "demo", "user_id": 1000}, options=opts)
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        client = await aiohttp_client(hass.http.app)
        base = f"http://127.0.0.1:{client.server.port}"
        files = await hass.async_add_executor_job(_shots, base, hass_access_token)
        print("Screenshots:", ", ".join(files))
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

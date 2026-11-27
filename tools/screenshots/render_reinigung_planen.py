"""Screenshot Reinigungsboard mit geplanter (späterer) Reinigung und automatischer Sperre (v1.20.0).

Aufruf (aus dem Repo-Stamm):
    python -m pytest tools/screenshots/render_reinigung_planen.py -p no:cacheprovider
Ergebnis: docs/screenshots/reinigung_planen.png

Ablauf: Integration mit DemoClient starten, die nächste Reinigung mit Lücke bis zur Folgebelegung auf einen
späteren Tag planen. Die Sperre legt der DemoClient nur in seinen Demodaten an – es geht nichts an Smoobu.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any
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
OPTIONS = {"default_checkin": "16:00", "default_checkout": "11:00", "use_webhook": False}


class PlanDemo(DemoClient):
    """DemoClient mit Sperre anlegen/löschen (nur in den Demodaten)."""

    async def create_block(self, body: dict[str, Any]) -> dict[str, Any]:
        rid = 990000 + len(self.bookings)
        self.bookings.append({"id": rid, "type": "reservation", "arrival": body["arrivalDate"], "departure": body["departureDate"],
                              "apartment": {"id": body["apartmentId"], "name": "Demo"}, "channel": {"id": body["channelId"], "name": "Blocked channel"},
                              "guest-name": "", "adults": 0, "children": 0, "is-blocked-booking": True, "notice": body.get("notice"),
                              "modifiedAt": "2026-11-27 20:00"})
        return {"id": rid}

    async def delete_reservation(self, reservation_id: int) -> None:
        self.bookings = [b for b in self.bookings if b["id"] != int(reservation_id)]


def _shots(base: str, token: str) -> list[str]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH") or None, args=["--no-sandbox", "--lang=de-DE"])
        page = browser.new_page(viewport={"width": 1212, "height": 1400}, device_scale_factor=SCALE, locale="de-DE", timezone_id="Europe/Berlin")
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(HARNESS.as_uri())
        page.evaluate("([b, t]) => setup(b, t)", [base, token])
        page.evaluate("([t, c, w]) => showCard(t, c, w)", ["smoobu-cleaning-card", {"days": 21}, 1000])
        page.wait_for_function("() => { const e = document.querySelector('smoobu-cleaning-card'); const r = e && e.shadowRoot;"
                               " return r && r.textContent.includes('In Smoobu gesperrt'); }", timeout=20000)
        page.wait_for_timeout(500)
        page.locator("#stage").screenshot(path=str(OUT / "reinigung_planen.png"))
        browser.close()
        assert not errors, errors
    return ["reinigung_planen.png"]


async def test_render_reinigung_planen(socket_enabled, hass: HomeAssistant, aiohttp_client, hass_access_token, hass_admin_user) -> None:
    today = dt_util.now().date()
    await hass.config.async_set_time_zone("Europe/Berlin")
    hass.config.language = "de"
    await async_setup_component(hass, "http", {})
    demo = PlanDemo(today)
    with patch("custom_components.smoobu.SmoobuClient", lambda *a, **k: demo):
        entry = MockConfigEntry(domain=DOMAIN, unique_id="1000", title="Demo",
                                data={"api_key": "demo", "api_secret": "demo", "user_id": 1000}, options=OPTIONS)
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        board = entry.runtime_data.cleaning
        items = await board.items(None, hass_admin_user)
        gap = next(x for x in items if x["datum"] > today.isoformat() and x["planbar_bis"] > (date.fromisoformat(x["datum"]) + timedelta(days=1)).isoformat())
        day = (date.fromisoformat(x := gap["datum"]) + timedelta(days=2)).isoformat()
        day = min(day, gap["planbar_bis"])
        await board.async_set(gap["key"], "planen", hass_admin_user, day=day)
        await hass.async_block_till_done()
        assert any(b["id"] >= 990000 for b in demo.bookings), x
        client = await aiohttp_client(hass.http.app)
        base = f"http://127.0.0.1:{client.server.port}"
        files = await hass.async_add_executor_job(_shots, base, hass_access_token)
        print("Screenshots:", ", ".join(files))
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

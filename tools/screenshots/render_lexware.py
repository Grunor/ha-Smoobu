"""Screenshots Lexware Office (BETA, v1.20.0) mit Demodaten und Beispiel-Lexware (Testmodus).

Aufruf (aus dem Repo-Stamm):
    python -m pytest tools/screenshots/render_lexware.py -p no:cacheprovider
Ergebnis: docs/screenshots/lexware_*.png

Ablauf: Integration mit DemoClient (erfundene Gäste) und Lexware im Testmodus starten, für eine
Direktbuchung einen Entwurf anlegen, ihn im Beispiel-Lexware „finalisieren“ und eine Anzahlung buchen.
Dann Buchungsdetails (Abschnitt Rechnung), Vorschau eines neuen Entwurfs, Einstellungsreiter und
„Wartet auf dich“ abfotografieren. Es geht nichts an Lexware oder Smoobu.
"""

from __future__ import annotations

import os
import sys
from datetime import timedelta
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

RULES = {
    "direkt": [
        {"artikel": "demo-uebernachtung", "hinweis": "Übernachtung", "menge": "nacht", "preis": "rest"},
        {"artikel": "demo-person", "hinweis": "Aufpreis 2. Person", "menge": "zusatzperson_nacht", "ab": 2, "preis": "artikel"},
        {"artikel": "demo-kind", "hinweis": "Aufpreis Kind", "menge": "kind_nacht", "preis": "artikel"},
        {"artikel": "demo-hund", "hinweis": "Sonderreinigung Hund", "menge": "hund", "max": 2, "preis": "artikel"},
        {"artikel": "demo-kurz", "hinweis": "Endreinigung Kurzzeit", "menge": "pauschal", "bedingung": "naechte_max", "wert": 14, "preis": "artikel"},
        {"artikel": "demo-lang", "hinweis": "Endreinigung Langzeit", "menge": "pauschal", "bedingung": "naechte_min", "wert": 15, "preis": "artikel"},
    ],
    "portal": [{"artikel": "demo-portal", "hinweis": "Übernachtung [n] Person(en)", "menge": "pauschal", "preis": "rest"}],
}
OPTIONS = {"default_checkin": "16:00", "default_checkout": "11:00", "checkout_buffer": 30, "use_webhook": False,
           "lexware_enabled": True, "lexware_mock": True, "lexware_rules": RULES,
           # v1.20.0: Umsatzsteuer (Regelbesteuerung seit Jahresbeginn)
           "ust_mode": "regel", "ust_map": {"Frühstück": "regel"}}


def _shots(base: str, token: str, names: dict[str, str]) -> list[str]:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    done: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH") or None, args=["--no-sandbox", "--lang=de-DE"])
        page = browser.new_page(viewport={"width": 1212, "height": 1400}, device_scale_factor=SCALE, locale="de-DE", timezone_id="Europe/Berlin")
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(HARNESS.as_uri())
        page.evaluate("([b, t]) => setup(b, t)", [base, token])

        def wait_card(type_: str) -> None:
            page.wait_for_function("t => { const e = document.querySelector(t); const r = e && e.shadowRoot;"
                                   " return r && r.querySelector('ha-card') && !r.textContent.includes('Laden …'); }", arg=type_, timeout=20000)

        def dialog(guest: str) -> None:
            page.evaluate("([t, c, w]) => showCard(t, c, w)", ["smoobu-bookings-card", {}, 1180])
            wait_card("smoobu-bookings-card")
            page.locator("smoobu-bookings-card").locator("tr[data-id]", has_text=guest).first.click()
            page.wait_for_function("() => { const d = document.querySelector('smoobu-booking-dialog');"
                                   " return d && d.shadowRoot && d.shadowRoot.textContent.includes('Rechnung'); }", timeout=15000)
            page.wait_for_timeout(600)

        def section(file: str) -> None:
            loc = page.locator("smoobu-booking-dialog").locator(".sec > div", has_text="Rechnung").last
            loc.screenshot(path=str(OUT / file))
            done.append(file)

        # 1) Bestehende Rechnung mit Anzahlung
        dialog(names["mit"])
        section("lexware_rechnung.png")
        page.evaluate("() => document.querySelector('smoobu-booking-dialog')?.remove()")
        # 2) Vorschau eines neuen Entwurfs
        dialog(names["ohne"])
        page.evaluate("() => document.querySelector('smoobu-booking-dialog').shadowRoot.querySelector('[data-act=lexnew]').click()")
        page.wait_for_function("() => document.querySelector('smoobu-booking-dialog').shadowRoot.querySelector('[data-act=lexcreate]')", timeout=15000)
        page.wait_for_timeout(500)
        section("lexware_vorschau.png")
        page.evaluate("() => document.querySelector('smoobu-booking-dialog')?.remove()")
        # 3) Einstellungen, Reiter Lexware
        page.evaluate("([t, c, w]) => showCard(t, c, w)", ["smoobu-settings-card", {"tab": "lexware"}, 1180])
        wait_card("smoobu-settings-card")
        page.wait_for_timeout(500)
        page.locator("#stage").screenshot(path=str(OUT / "einstellungen_lexware.png"))
        done.append("einstellungen_lexware.png")
        # 4) Übersicht – „Wartet auf dich“, Reiter Rechnungen
        page.evaluate("([t, c, w]) => showCard(t, c, w)", ["smoobu-overview-card", {}, 1400])
        wait_card("smoobu-overview-card")
        page.wait_for_timeout(800)
        tab = page.locator("smoobu-overview-card").get_by_role("button", name="Rechnungen").first
        if tab.count():
            tab.click()
            page.wait_for_timeout(400)
        page.locator("smoobu-overview-card").locator("section.three > .panel").nth(2).screenshot(path=str(OUT / "lexware_wartet.png"))
        done.append("lexware_wartet.png")
        # 4b) v1.20.0b3: Allgemein & Abruf → Module mit Schalter Lexware
        page.evaluate("([t, c, w]) => showCard(t, c, w)", ["smoobu-settings-card", {"tab": "allgemein"}, 1180])
        wait_card("smoobu-settings-card")
        page.wait_for_timeout(500)
        page.locator("smoobu-settings-card").locator('[data-neu="module"]').screenshot(path=str(OUT / "einstellungen_module.png"))
        done.append("einstellungen_module.png")
        # 5) Einstellungen, Reiter Umsatzsteuer
        page.evaluate("([t, c, w]) => showCard(t, c, w)", ["smoobu-settings-card", {"tab": "umsatzsteuer"}, 1180])
        wait_card("smoobu-settings-card")
        page.wait_for_timeout(500)
        page.locator("#stage").screenshot(path=str(OUT / "einstellungen_umsatzsteuer.png"))
        done.append("einstellungen_umsatzsteuer.png")
        # 6) Finanzen mit Umschalter Brutto / ohne USt und Kachel Umsatzsteuer
        page.evaluate("([t, c, w]) => showCard(t, c, w)", ["smoobu-analytics-card", {}, 1180])
        wait_card("smoobu-analytics-card")
        page.wait_for_timeout(800)
        page.locator("smoobu-analytics-card").locator(".grid").first.screenshot(path=str(OUT / "finanzen_umsatzsteuer.png"))
        page.locator("smoobu-analytics-card").locator(".fbar").first.screenshot(path=str(OUT / "finanzen_ust_umschalter.png"))
        done += ["finanzen_umsatzsteuer.png", "finanzen_ust_umschalter.png"]
        browser.close()
        assert not errors, errors
    return done


async def test_render_lexware(socket_enabled, hass: HomeAssistant, aiohttp_client, hass_access_token) -> None:
    today = dt_util.now().date()
    await hass.config.async_set_time_zone("Europe/Berlin")
    hass.config.language = "de"
    await async_setup_component(hass, "http", {})
    demo = DemoClient(today)
    with patch("custom_components.smoobu.SmoobuClient", lambda *a, **k: demo):
        entry = MockConfigEntry(domain=DOMAIN, unique_id="1000", title="Demo",
                                data={"api_key": "demo", "api_secret": "demo", "user_id": 1000}, options=OPTIONS)
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        c = entry.runtime_data
        lex = c.lexware
        lex.data["aktiv_seit"] = (today - timedelta(days=30)).isoformat()
        hass.config_entries.async_update_entry(entry, options={**entry.options, "ust_since": f"{today.year}-01-01"})
        await hass.async_block_till_done()
        c = entry.runtime_data
        lex = c.lexware
        lex.data["aktiv_seit"] = (today - timedelta(days=30)).isoformat()
        direct = [r for r in c.records_all() if r.get("gruppe") == "Direkt" and not r.get("storniert") and not r.get("blockiert")
                  and r.get("anreise") and r["anreise"] >= today.isoformat()]
        direct.sort(key=lambda r: r["anreise"])
        assert len(direct) >= 2, "Demodaten brauchen zwei kommende Direktbuchungen"
        mit, ohne = direct[0], direct[1]
        res = await lex.create(mit["id"])
        lex.client.finalize(res["id"], res["summe"])
        lex.client.pay(res["id"], round(res["summe"] / 2, 2), today)
        await lex.async_poll()
        await hass.async_block_till_done()
        client = await aiohttp_client(hass.http.app)
        base = f"http://127.0.0.1:{client.server.port}"
        files = await hass.async_add_executor_job(_shots, base, hass_access_token, {"mit": mit["gast"], "ohne": ohne["gast"]})
        print("Screenshots:", ", ".join(files))
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

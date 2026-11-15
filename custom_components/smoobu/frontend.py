"""Dashboard-Karten der Integration bereitstellen (ab v1.8.0).

Die Datei www/smoobu-cards.js wird unter /smoobu_static/ ausgeliefert und
automatisch auf allen Dashboards geladen (kein manuelles Eintragen als
Ressource nötig). Die Versionsnummer im Link sorgt dafür, dass Browser nach
einem Update die neue Datei laden statt einer zwischengespeicherten.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

URL_BASE = "/smoobu_static"
CARDS_FILE = "smoobu-cards.js"


async def async_register_frontend(hass: HomeAssistant) -> None:
    if hass.data.get(f"{DOMAIN}_frontend"):
        return
    hass.data[f"{DOMAIN}_frontend"] = True
    path = Path(__file__).parent / "www"
    if getattr(hass, "http", None) is None:
        return  # z. B. in Tests ohne HTTP-Server
    await hass.http.async_register_static_paths(
        [StaticPathConfig(URL_BASE, str(path), cache_headers=False)]
    )
    version = (await async_get_integration(hass, DOMAIN)).version
    if "frontend" not in hass.config.components:
        # frontend ist after_dependency → wäre bereits geladen, wenn vorhanden
        _LOGGER.debug("Frontend nicht geladen – Smoobu-Karten nicht registriert")
        return
    from homeassistant.components.frontend import add_extra_js_url

    add_extra_js_url(hass, f"{URL_BASE}/{CARDS_FILE}?v={version}")

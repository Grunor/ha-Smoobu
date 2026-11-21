"""Dashboard-Karten der Integration bereitstellen (ab v1.8.0).

Die Datei www/smoobu-cards.js wird unter /smoobu_static/ ausgeliefert und
automatisch auf allen Dashboards geladen (kein manuelles Eintragen als
Ressource nötig). Die Versionsnummer im Link sorgt dafür, dass Browser nach
einem Update die neue Datei laden statt einer zwischengespeicherten.

v1.19.0b11 (Geschwindigkeit, ohne Funktionsverlust):
- Komprimiert ausliefern: beim Start entsteht neben der Datei eine gzip-Fassung (smoobu-cards.js.gz,
  ca. 1/5 der Größe). aiohttp liefert sie automatisch an Browser, die gzip akzeptieren (alle üblichen).
  Neu erzeugt nur, wenn sie fehlt oder älter als die Karte ist; ohne Schreibrecht bleibt alles wie bisher.
- Zwischenspeichern erlaubt (Cache-Control 31 Tage): die Adresse enthält die Version (?v=…), nach einem
  Update lädt der Browser also trotzdem die neue Datei. Vorher fragte er bei jedem App-Start neu an.
"""

from __future__ import annotations

import gzip
import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

URL_BASE = "/smoobu_static"
CARDS_FILE = "smoobu-cards.js"


def _write_gzip(src: Path) -> None:
    """gzip-Fassung neben die Karte legen (nur wenn fehlend oder veraltet). Läuft im Executor."""
    dst = src.with_name(src.name + ".gz")
    try:
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            return
        tmp = dst.with_name(dst.name + ".tmp")
        tmp.write_bytes(gzip.compress(src.read_bytes(), compresslevel=9, mtime=0))
        tmp.replace(dst)  # atomar: nie eine halb geschriebene Datei ausliefern
    except OSError as err:  # z. B. schreibgeschützt – dann eben unkomprimiert
        _LOGGER.debug("Smoobu: gzip-Fassung der Karten nicht erzeugt: %s", err)


async def async_register_frontend(hass: HomeAssistant) -> None:
    if hass.data.get(f"{DOMAIN}_frontend"):
        return
    hass.data[f"{DOMAIN}_frontend"] = True
    path = Path(__file__).parent / "www"
    if getattr(hass, "http", None) is None:
        return  # z. B. in Tests ohne HTTP-Server
    await hass.async_add_executor_job(_write_gzip, path / CARDS_FILE)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(URL_BASE, str(path), cache_headers=True)]
    )
    version = (await async_get_integration(hass, DOMAIN)).version
    if "frontend" not in hass.config.components:
        # frontend ist after_dependency → wäre bereits geladen, wenn vorhanden
        _LOGGER.debug("Frontend nicht geladen – Smoobu-Karten nicht registriert")
        return
    from homeassistant.components.frontend import add_extra_js_url

    add_extra_js_url(hass, f"{URL_BASE}/{CARDS_FILE}?v={version}")

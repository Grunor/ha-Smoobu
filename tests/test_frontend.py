"""v1.19.0b11: Karten komprimiert (gzip) und mit Cache-Header ausliefern."""
import gzip
from pathlib import Path

from homeassistant.setup import async_setup_component

from custom_components.smoobu import frontend


def test_gzip_fassung(tmp_path: Path):
    src = tmp_path / "smoobu-cards.js"
    src.write_text("console.log('x');" * 500)
    frontend._write_gzip(src)  # noqa: SLF001
    gz = tmp_path / "smoobu-cards.js.gz"
    assert gz.exists() and gzip.decompress(gz.read_bytes()) == src.read_bytes() and gz.stat().st_size < src.stat().st_size / 5
    before = gz.stat().st_mtime_ns
    frontend._write_gzip(src)  # aktuell → nicht neu schreiben  # noqa: SLF001
    assert gz.stat().st_mtime_ns == before


async def test_auslieferung(hass, hass_client):
    assert await async_setup_component(hass, "http", {})
    hass.data.pop("smoobu_frontend", None)
    await frontend.async_register_frontend(hass)
    client = await hass_client()
    resp = await client.get(f"{frontend.URL_BASE}/{frontend.CARDS_FILE}", headers={"Accept-Encoding": "gzip"})
    assert resp.status == 200
    assert resp.headers.get("Content-Encoding") == "gzip"
    assert "max-age" in resp.headers.get("Cache-Control", "")
    assert "SMOOBU-CARDS" in await resp.text()

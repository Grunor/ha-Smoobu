"""Medienquelle „smoobu“ (ab v1.19.0): nur damit die KI hochgeladene Belege als Anhang lesen kann.

HA nimmt Anhänge für `ai_task.generate_data` nur über Medienquellen mit lokalem Pfad an. Die Belege
(Nebenkostenabrechnungen) liegen bewusst NICHT im Medien-Ordner, den alle HA-Benutzer durchsuchen
können. Deshalb diese eigene Quelle: Auflösen ja (für die KI), Durchsuchen nein.
ID: media-source://smoobu/<entry_id>/<datei>
"""

from __future__ import annotations

from homeassistant.components.media_source import BrowseMediaSource, MediaSource, MediaSourceItem, PlayMedia
from homeassistant.components.media_player import BrowseError
from homeassistant.components.media_source.error import Unresolvable
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .nebenkosten import MIME


async def async_get_media_source(hass: HomeAssistant) -> MediaSource:
    return SmoobuBelege(hass)


class SmoobuBelege(MediaSource):
    name = "Smoobu Belege"

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        entry_id, _, file = (item.identifier or "").partition("/")
        entry = self.hass.config_entries.async_get_entry(entry_id)
        bills = getattr(getattr(entry, "runtime_data", None), "bills", None) if entry else None
        path = bills.path(file) if bills else None
        if path is None:
            raise Unresolvable("Beleg nicht gefunden")
        return PlayMedia(url="", mime_type=MIME.get(path.suffix.lower(), "application/octet-stream"), path=path)

    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        raise BrowseError("Smoobu-Belege sind nicht durchsuchbar")

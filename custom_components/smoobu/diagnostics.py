"""Diagnose-Download (Einstellungen → Geräte & Dienste → Smoobu → Diagnose).

Gästedaten und Zugangsdaten werden geschwärzt.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import SmoobuConfigEntry
from .const import REDACT_KEYS


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SmoobuConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    data = asdict(coordinator.data) if coordinator.data else {}
    return {
        "entry_data": async_redact_data(dict(entry.data), REDACT_KEYS),
        "options": dict(entry.options),
        "window": [str(d) for d in coordinator.window],
        "data": async_redact_data(data, REDACT_KEYS),
    }

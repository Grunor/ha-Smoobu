"""Neue Home-Assistant-Benutzer erkennen und melden (v1.19.0b8, Wunsch Betreiber 21.11.2026).

Hintergrund: Smoobu-Rechte (Rolle, Fokus-Modus) gelten je HA-Benutzer. Ein neu angelegter Benutzer bekommt
die Standardrolle und sieht in Home Assistant zunächst alles, was HA Nicht-Admins zeigt (Entscheidung
Betreiber: neue Benutzer sehen in HA erst einmal alles). Damit das nicht übersehen wird, meldet die
Integration jeden neuen Benutzer dringend:
- HA-Meldung (Glocke, für Admins sichtbar) mit Hinweis, wo die Rechte eingestellt werden
- Push an alle Smoobu-Empfänger (Vereinigung der Empfänger aller Push-Arten), sofort, auch in der Ruhezeit

Erkennung:
- Ereignis `user_added` (Benutzer im laufenden Betrieb angelegt)
- beim Start Abgleich mit der gespeicherten Liste bekannter Benutzer (Benutzer, die angelegt wurden,
  während die Integration nicht lief). Beim allerersten Start werden alle vorhandenen Benutzer still als
  bekannt übernommen – gemeldet wird nur, was danach neu dazukommt.
Systembenutzer (Supervisor, Apps, Home Assistant Cloud …) werden ignoriert.

Speicher: Store `smoobu_benutzer` {"bekannt": [Benutzer-IDs]} (kontoübergreifend, einmal je HA).
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, Event, HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

EVENT_USER_ADDED = "user_added"  # von HA beim Anlegen eines Benutzers gefeuert (data: user_id)
NOTIFY_PREFIX = "smoobu_neuer_benutzer_"


async def async_setup_user_watch(hass: HomeAssistant) -> None:
    """Einmal je HA (aus async_setup): bekannte Benutzer laden, Start-Abgleich planen, Ereignis abonnieren."""
    if hass.data.get(f"{DOMAIN}_benutzer"):
        return
    hass.data[f"{DOMAIN}_benutzer"] = True
    store: Store = Store(hass, 1, f"{DOMAIN}_benutzer")
    data = await store.async_load()
    first_run = data is None
    known: set[str] = set((data or {}).get("bekannt") or [])

    async def _save() -> None:
        await store.async_save({"bekannt": sorted(known)})

    async def _check_all(_event: Any = None) -> None:
        """Start-Abgleich (erst wenn HA läuft, damit die Smoobu-Konten und Notify-Dienste geladen sind)."""
        users = [u for u in await hass.auth.async_get_users() if not u.system_generated]
        if first_run:
            known.update(u.id for u in users)  # Bestand still übernehmen
            await _save()
            return
        new = [u for u in users if u.id not in known]
        for user in new:
            known.add(user.id)
            await _notify(hass, user)
        if new:
            await _save()

    @callback
    def _on_added(event: Event) -> None:
        hass.async_create_task(_added(event.data.get("user_id")))

    async def _added(user_id: str | None) -> None:
        user = await hass.auth.async_get_user(user_id) if user_id else None
        if user is None or user.system_generated or user.id in known:
            return
        known.add(user.id)
        await _save()
        await _notify(hass, user)

    hass.bus.async_listen(EVENT_USER_ADDED, _on_added)
    if hass.state is CoreState.running:
        hass.async_create_task(_check_all())
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _check_all)


def _settings_path(entry: Any) -> str:
    """Seite Einstellungen im Dashboard der Smoobu-Seiten (aus dem Assistent-Pfad), sonst /lovelace/…."""
    from .rechte import focus_dashboard

    return f"{focus_dashboard(entry.options if entry else {})}/smoobu-einstellungen"


async def _notify(hass: HomeAssistant, user: Any) -> None:
    """HA-Meldung + dringender Push an alle Smoobu-Empfänger."""
    from . import rechte
    from .notifications import NOTIFY_TYPES, opt_recipients

    entries = [e for e in hass.config_entries.async_entries(DOMAIN) if getattr(e, "runtime_data", None)]
    entry = entries[0] if entries else None
    opts = dict(entry.options) if entry else {}
    role = rechte.role_of(user, opts)
    role_name = "Admin" if role == rechte.ADMIN else rechte.roles(opts).get(role, {}).get("name", role)
    path = _settings_path(entry)
    name = user.name or user.id
    title = f"Neuer HA-Benutzer: {name}"
    text = (f"Bitte dringend die Rechte prüfen. In Home Assistant sieht „{name}“ jetzt alles, was Nicht-Admins sehen; "
            f"in Smoobu gilt die Rolle „{role_name}“. Rolle und Fokus-Modus: Smoobu-Einstellungen → Benutzer & Rechte.")
    persistent_notification.async_create(hass, f"{text}\n\n[Smoobu-Einstellungen öffnen]({path})", title,
                                         f"{NOTIFY_PREFIX}{user.id}")
    if entry is None or getattr(entry.runtime_data, "notifier", None) is None:
        return
    to = sorted({svc for kind in NOTIFY_TYPES for svc in opt_recipients(opts, kind)})
    if not to:
        return
    try:
        await entry.runtime_data.notifier.send("buchung", title, text, {"url": path, "clickAction": path,
                                                                         "tag": f"{NOTIFY_PREFIX}{user.id}"},
                                               urgent=True, check_enabled=False, to=to)
    except Exception as err:  # noqa: BLE001 – Meldung darf den Ablauf nie stören
        _LOGGER.warning("Smoobu: Push zu neuem Benutzer fehlgeschlagen: %s", err)

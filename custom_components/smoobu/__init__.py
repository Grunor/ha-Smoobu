"""Smoobu-Integration für Home Assistant.

Aufbau:
- api.py          HMAC-signierter API-Client
- coordinator.py  zentraler Datenabruf (Polling, Standard 10 min)
- calendar.py     Belegungskalender je Wohnung mit vollem Gastnamen
- sensor.py       Gäste-, Termin- und Statistik-Sensoren
- binary_sensor.py belegt / Anreise heute / Abreise heute / Gästewechsel
- hier:           Einrichtung, Echtzeit-Webhook (Nabu Casa), Aktionen

Webhook-Ablauf:
1. HA-Webhook mit zufälliger ID registrieren.
2. Öffentliche URL über Nabu Casa (Cloudhook) erzeugen, sonst externe HA-URL.
3. URL per API bei Smoobu registrieren (/api/users/webhooks).
   Klappt das nicht, erscheint eine Benachrichtigung mit der URL zum
   manuellen Eintragen in Smoobu (Einstellungen → API).
4. Eingehende Ereignisse → Event `smoobu_event` + sofortige Aktualisierung.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from aiohttp import web

from homeassistant.components import cloud, persistent_notification, webhook
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import Unauthorized, HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import NoURLAvailableError
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .api import SmoobuClient, SmoobuError
from . import rechte
from .const import (
    ATTR_APARTMENT_ID,
    ATTR_ARRIVAL_FROM,
    ATTR_ARRIVAL_TO,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_DEPARTURE_FROM,
    ATTR_DEPARTURE_TO,
    ATTR_INTERNAL,
    ATTR_MESSAGE,
    ATTR_ONLY_GUEST,
    ATTR_RECIPIENT,
    ATTR_RESERVATION_ID,
    ATTR_SHOW_CANCELLATION,
    ATTR_SUBJECT,
    ATTR_ALLOW_BOOKING,
    ATTR_ARRIVAL_TIME,
    ATTR_DEPARTURE_TIME,
    ATTR_END,
    ATTR_MIN_STAY,
    ATTR_NOTICE,
    ATTR_PRICE,
    ATTR_START,
    SERVICE_BLOCK_PERIOD,
    SERVICE_ASSIST_IMPORT,
    SERVICE_ASSIST_KNOWLEDGE,
    SERVICE_ASSIST_SUGGEST,
    SERVICE_DELETE_RESERVATION,
    SERVICE_SET_RATES,
    SERVICE_UPDATE_RESERVATION,
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_CLOUDHOOK_URL,
    CONF_SMOOBU_WEBHOOK_ID,
    CONF_USE_WEBHOOK,
    CONF_USER_ID,
    CONF_WEBHOOK_ID,
    DEFAULT_USE_WEBHOOK,
    DOMAIN,
    EVENT_SMOOBU,
    SERVICE_GET_MESSAGES,
    SERVICE_GET_RESERVATION,
    SERVICE_GET_RESERVATIONS,
    SERVICE_REFRESH,
    SERVICE_SEND_MESSAGE,
)
from .analytics import block_channel_id
from .assistant import SmoobuAssistant
from .notifications import SmoobuNotifier
from .reinigung import CleaningBoard
from .nebenkosten import UtilityBills
from .tuercode import DoorCodes, fill as fill_door_code
from .lexware import LexwareModule
from .websocket_api import NebenkostenUploadView
from .coordinator import SmoobuCoordinator
from .frontend import async_register_frontend
from .websocket_api import async_register as async_register_websocket

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CALENDAR, Platform.SELECT, Platform.SENSOR]

type SmoobuConfigEntry = ConfigEntry[SmoobuCoordinator]

# Nur UI-Einrichtung, keine YAML-Konfiguration.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

NOTIFICATION_ID = "smoobu_webhook"


# ===========================================================================
# Einrichtung
# ===========================================================================
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Aktionen, WebSocket-Befehle und Dashboard-Karten einmalig registrieren."""
    _register_services(hass)
    async_register_websocket(hass)
    hass.http.register_view(NebenkostenUploadView())  # v1.19.0: Upload Nebenkostenabrechnung
    await async_register_frontend(hass)
    # v1.19.0b8: neue HA-Benutzer erkennen und melden (Rechte dringend prüfen)
    from .benutzer import async_setup_user_watch

    await async_setup_user_watch(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: SmoobuConfigEntry) -> bool:
    client = SmoobuClient(
        async_get_clientsession(hass), entry.data[CONF_API_KEY], entry.data[CONF_API_SECRET]
    )
    coordinator = SmoobuCoordinator(hass, entry, client)
    # Erste Abfrage: Fehler hier → HA versucht die Einrichtung später erneut.
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    # KI-Assistent (Wissensdatenbank, Beispiele, Push-Aktionen); ohne KI-Option inaktiv
    # v1.17.0: Benachrichtigungen (Push-Arten, Empfänger, Ruhezeit) – vor dem Assistenten,
    # weil dessen Pushes darüber laufen
    coordinator.notifier = SmoobuNotifier(hass, coordinator)
    await coordinator.notifier.async_setup()
    # v1.19.0: Reinigungsboard (Zuweisungen, Vorabend-Erinnerung)
    coordinator.cleaning = CleaningBoard(hass, coordinator)
    await coordinator.cleaning.async_setup()
    coordinator.bills = UtilityBills(hass, coordinator)  # v1.19.0: Nebenkostenabrechnungen (KI-Auswertung)
    # v1.19.0: Türcodes (vor den Plattformen, damit die Sensoren beim Start schon Codes kennen)
    coordinator.doorcodes = DoorCodes(hass, coordinator)
    await coordinator.doorcodes.async_setup()
    # v1.20.0 (BETA): Lexware Office (Rechnungsentwürfe, Zahlungsstand) – ohne Schalter/API-Key inaktiv
    coordinator.lexware = LexwareModule(hass, coordinator)
    await coordinator.lexware.async_setup()
    coordinator.assistant = SmoobuAssistant(hass, coordinator)
    await coordinator.assistant.async_setup()

    # Webhook vor den Plattformen, damit der Webhook-Sensor gleich den
    # richtigen Status zeigt.
    await _async_setup_webhook(hass, entry, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Optionen geändert → Eintrag neu laden (neues Intervall, Webhook an/aus …).
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


# v1.18.0: Einträge, deren Neuladen die Einstellungskarte selbst übernimmt (settings.save wartet darauf,
# damit die Karte erst nach dem Neuladen antwortet) → der Update-Listener lädt dann nicht ein zweites Mal
SKIP_RELOAD = f"{DOMAIN}_skip_reload"


async def _async_reload(hass: HomeAssistant, entry: SmoobuConfigEntry) -> None:
    skip: set[str] = hass.data.setdefault(SKIP_RELOAD, set())
    if entry.entry_id in skip:
        skip.discard(entry.entry_id)
        return
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: SmoobuConfigEntry) -> bool:
    if getattr(entry, "runtime_data", None) and entry.runtime_data.assistant:
        await entry.runtime_data.assistant.async_unload()
    if getattr(entry, "runtime_data", None) and entry.runtime_data.notifier:
        await entry.runtime_data.notifier.async_unload()
    if getattr(entry, "runtime_data", None) and getattr(entry.runtime_data, "cleaning", None):
        await entry.runtime_data.cleaning.async_unload()
    if getattr(entry, "runtime_data", None) and getattr(entry.runtime_data, "doorcodes", None):
        await entry.runtime_data.doorcodes.async_unload()
    if getattr(entry, "runtime_data", None) and getattr(entry.runtime_data, "lexware", None):
        await entry.runtime_data.lexware.async_unload()
    if webhook_id := entry.data.get(CONF_WEBHOOK_ID):
        webhook.async_unregister(hass, webhook_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: SmoobuConfigEntry) -> None:
    """Integration gelöscht → Webhook bei Smoobu und Cloudhook aufräumen."""
    client = SmoobuClient(
        async_get_clientsession(hass), entry.data[CONF_API_KEY], entry.data[CONF_API_SECRET]
    )
    await _async_remove_remote_webhook(hass, entry, client, update_entry=False)
    # v1.17.0: Warteschlange/Erinnerungsstand der Benachrichtigungen entfernen
    await Store(hass, 1, f"{DOMAIN}_notify_{entry.entry_id}").async_remove()
    # v1.20.0: Lexware-Zuordnungen (Buchung ↔ Rechnung) entfernen; die Rechnungen in Lexware bleiben
    await Store(hass, 1, f"{DOMAIN}_lexware_{entry.entry_id}").async_remove()


# ===========================================================================
# Webhook
# ===========================================================================
def _update_data(hass: HomeAssistant, entry: ConfigEntry, **changes: Any) -> None:
    """Werte in entry.data setzen/entfernen (None = entfernen).

    Wird nur während der Einrichtung aufgerufen – also bevor der
    Update-Listener (Reload bei Optionsänderung) registriert ist.
    Dadurch löst das Speichern der Webhook-Daten kein Neuladen aus.
    Geschrieben wird nur bei echter Änderung.
    """
    data = dict(entry.data)
    for key, value in changes.items():
        if value is None:
            data.pop(key, None)
        else:
            data[key] = value
    if data != dict(entry.data):
        hass.config_entries.async_update_entry(entry, data=data)


async def _async_setup_webhook(
    hass: HomeAssistant, entry: SmoobuConfigEntry, coordinator: SmoobuCoordinator
) -> None:
    client = coordinator.client
    if not entry.options.get(CONF_USE_WEBHOOK, DEFAULT_USE_WEBHOOK):
        # Webhook in den Optionen abgeschaltet → Registrierungen entfernen.
        await _async_remove_remote_webhook(hass, entry, client, update_entry=True)
        return

    webhook_id = entry.data.get(CONF_WEBHOOK_ID) or webhook.async_generate_id()
    webhook.async_register(
        hass,
        DOMAIN,
        f"Smoobu ({entry.title})",
        webhook_id,
        _handle_webhook,
        allowed_methods=["POST"],
    )

    url = entry.data.get(CONF_CLOUDHOOK_URL)
    if not url:
        url = await _async_public_url(hass, webhook_id)

    smoobu_hook_id = entry.data.get(CONF_SMOOBU_WEBHOOK_ID)
    if url and not smoobu_hook_id:
        try:
            # Nicht doppelt registrieren: erst prüfen, ob die URL schon bekannt ist.
            for hook in await client.list_webhooks():
                if hook.get("webhookUrl") == url:
                    smoobu_hook_id = hook.get("id")
                    break
            else:
                created = await client.create_webhook(url)
                smoobu_hook_id = created.get("id")
            persistent_notification.async_dismiss(hass, NOTIFICATION_ID)
            _LOGGER.info("Smoobu-Webhook registriert (ID %s)", smoobu_hook_id)
        except SmoobuError as err:
            _LOGGER.warning("Webhook konnte nicht bei Smoobu registriert werden: %s", err)
            persistent_notification.async_create(
                hass,
                "Der Smoobu-Webhook konnte nicht automatisch registriert werden.\n\n"
                "Bitte in Smoobu unter **Einstellungen → API** als Webhook-URL eintragen:\n\n"
                f"`{url}`\n\nFehler: {err}",
                title="Smoobu: Webhook manuell eintragen",
                notification_id=NOTIFICATION_ID,
            )
    elif not url:
        persistent_notification.async_create(
            hass,
            "Für den Smoobu-Webhook ist keine öffentliche HTTPS-URL verfügbar "
            "(Nabu Casa nicht angemeldet und keine externe URL gesetzt). "
            "Die Integration arbeitet weiter per Polling.",
            title="Smoobu: kein Webhook",
            notification_id=NOTIFICATION_ID,
        )

    _update_data(
        hass,
        entry,
        **{
            CONF_WEBHOOK_ID: webhook_id,
            CONF_CLOUDHOOK_URL: url,
            CONF_SMOOBU_WEBHOOK_ID: smoobu_hook_id,
        },
    )


async def _async_public_url(hass: HomeAssistant, webhook_id: str) -> str | None:
    """HTTPS-URL: bevorzugt Nabu Casa Cloudhook, sonst externe HA-URL."""
    if cloud.async_active_subscription(hass):
        try:
            return await cloud.async_create_cloudhook(hass, webhook_id)
        except cloud.CloudNotAvailable as err:
            _LOGGER.debug("Cloudhook nicht verfügbar: %s", err)
    try:
        url = webhook.async_generate_url(
            hass, webhook_id, allow_internal=False, prefer_external=True
        )
    except NoURLAvailableError:
        return None
    # Smoobu verlangt HTTPS.
    return url if url.startswith("https://") else None


async def _async_remove_remote_webhook(
    hass: HomeAssistant, entry: ConfigEntry, client: SmoobuClient, update_entry: bool
) -> None:
    if hook_id := entry.data.get(CONF_SMOOBU_WEBHOOK_ID):
        try:
            await client.delete_webhook(hook_id)
        except SmoobuError as err:
            _LOGGER.warning("Smoobu-Webhook %s konnte nicht gelöscht werden: %s", hook_id, err)
    webhook_id = entry.data.get(CONF_WEBHOOK_ID)
    if webhook_id and entry.data.get(CONF_CLOUDHOOK_URL) and cloud.async_active_subscription(hass):
        try:
            await cloud.async_delete_cloudhook(hass, webhook_id)
        except (cloud.CloudNotAvailable, ValueError):
            pass
    if update_entry:
        _update_data(
            hass,
            entry,
            **{CONF_SMOOBU_WEBHOOK_ID: None, CONF_CLOUDHOOK_URL: None, CONF_WEBHOOK_ID: None},
        )


async def _handle_webhook(
    hass: HomeAssistant, webhook_id: str, request: web.Request
) -> web.Response:
    """Eingehendes Smoobu-Ereignis verarbeiten."""
    entry = next(
        (
            e
            for e in hass.config_entries.async_entries(DOMAIN)
            if e.data.get(CONF_WEBHOOK_ID) == webhook_id and e.state is ConfigEntryState.LOADED
        ),
        None,
    )
    if entry is None:
        return web.Response(status=404)

    try:
        payload = await request.json()
    except ValueError:
        return web.Response(status=400)
    if not isinstance(payload, dict):
        return web.Response(status=400)

    # Schutz: Nur Ereignisse des eigenen Smoobu-Kontos annehmen.
    expected_user = entry.data.get(CONF_USER_ID)
    if expected_user and payload.get("user") and str(payload.get("user")) != str(expected_user):
        _LOGGER.warning("Smoobu-Webhook für fremden Benutzer %s ignoriert", payload.get("user"))
        return web.Response(status=403)

    action = payload.get("action")
    data = payload.get("data") or {}
    booking = data.get("booking") if isinstance(data.get("booking"), dict) else None
    reservation_id = (booking or {}).get("id") if action == "newMessage" else data.get("id")

    event_data = {
        "config_entry_id": entry.entry_id,
        "action": action,
        "reservation_id": reservation_id,
        "apartment_id": (data.get("apartment") or {}).get("id"),
        "apartment": (data.get("apartment") or {}).get("name"),
        "guest_name": data.get("guest-name"),
        "arrival": data.get("arrival"),
        "departure": data.get("departure"),
        "channel": (data.get("channel") or {}).get("name"),
        "data": data,
    }
    hass.bus.async_fire(EVENT_SMOOBU, event_data)

    coordinator: SmoobuCoordinator = entry.runtime_data
    coordinator.set_last_event({**event_data, "received": dt_util.now().isoformat()})
    # Neue Gästenachricht → Text nachladen (Webhook enthält nur IDs)
    if action == "newMessage" and reservation_id:
        # v1.17.0: Antwortstatus sofort verwerfen (nicht erst im Task), damit das folgende
        # Datenabo-Ereignis an die Karten schon den neuen Stand liefert (Zähler „Nachrichten“)
        coordinator.invalidate_message_status(int(reservation_id))
        hass.async_create_task(
            coordinator.async_fetch_last_message(int(reservation_id), data.get("sender"))
        )
        # Assistent: Gast schreibt → Vorschlag; Gastgeber schreibt → lernen
        if coordinator.assistant:
            hass.async_create_task(coordinator.assistant.on_new_message(int(reservation_id)))
    # Preisänderungen betreffen keine Buchungsdaten → kein Neuladen nötig.
    if action != "updateRates":
        # Buchung neu/geändert/storniert → auch Umsatzdaten sofort neu laden
        if action in ("newReservation", "updateReservation", "cancelReservation", "deleteReservation"):
            coordinator.force_revenue_refresh = True
        await coordinator.async_request_refresh()
    return web.Response(status=200)


# ===========================================================================
# Aktionen (Services)
# ===========================================================================
def _get_coordinator(hass: HomeAssistant, call: ServiceCall) -> SmoobuCoordinator:
    """Coordinator zum angegebenen Eintrag, sonst den einzigen geladenen."""
    entries = [
        e for e in hass.config_entries.async_entries(DOMAIN) if e.state is ConfigEntryState.LOADED
    ]
    if entry_id := call.data.get(ATTR_CONFIG_ENTRY_ID):
        entries = [e for e in entries if e.entry_id == entry_id]
    if not entries:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="no_entry"
        )
    return entries[0].runtime_data


def _date_str(value: Any) -> str | None:
    return value.isoformat() if value else None


def _register_services(hass: HomeAssistant) -> None:
    entry_field = {vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string}

    async def refresh(call: ServiceCall) -> None:
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is ConfigEntryState.LOADED:
                entry.runtime_data.force_revenue_refresh = True  # auch Umsatzdaten
                await entry.runtime_data.async_request_refresh()

    async def _require(call: ServiceCall, coordinator: SmoobuCoordinator, right: str) -> None:
        """v1.18.0: Benutzerrolle prüfen (Automationen/Skripte ohne Benutzer dürfen immer)."""
        if call.context.user_id is None:
            return
        user = await hass.auth.async_get_user(call.context.user_id)
        if not rechte.allowed(user, coordinator.config_entry.options, right):
            raise Unauthorized(context=call.context, permission=f"smoobu.{right}")

    async def get_reservations(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "gaeste")
        try:
            bookings = await coordinator.client.get_reservations(
                arrivalFrom=_date_str(call.data.get(ATTR_ARRIVAL_FROM)),
                arrivalTo=_date_str(call.data.get(ATTR_ARRIVAL_TO)),
                departureFrom=_date_str(call.data.get(ATTR_DEPARTURE_FROM)),
                departureTo=_date_str(call.data.get(ATTR_DEPARTURE_TO)),
                apartmentId=call.data.get(ATTR_APARTMENT_ID),
                showCancellation=call.data.get(ATTR_SHOW_CANCELLATION, False),
                includePriceElements=True,
            )
        except SmoobuError as err:
            raise HomeAssistantError(str(err)) from err
        return {"count": len(bookings), "reservations": bookings}

    async def get_reservation(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "gaeste")
        try:
            booking = await coordinator.client.get_reservation(call.data[ATTR_RESERVATION_ID])
        except SmoobuError as err:
            raise HomeAssistantError(str(err)) from err
        return {"reservation": booking}

    async def get_messages(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "nachrichten")
        try:
            messages = await coordinator.client.get_messages(
                call.data[ATTR_RESERVATION_ID], call.data.get(ATTR_ONLY_GUEST, False)
            )
        except SmoobuError as err:
            raise HomeAssistantError(str(err)) from err
        return {"count": len(messages), "messages": messages}

    async def send_message(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "antworten")
        to_guest = call.data.get(ATTR_RECIPIENT, "guest") == "guest"
        try:
            if to_guest and not call.data.get(ATTR_SUBJECT) and coordinator.assistant:
                # Über den Assistenten: Antwort wird als Lernbeispiel gespeichert
                await coordinator.assistant.send(call.data[ATTR_RESERVATION_ID], call.data[ATTR_MESSAGE])
                return
            text = call.data[ATTR_MESSAGE]
            if to_guest and coordinator.doorcodes:  # v1.19.0: Platzhalter {{ turcode }} lokal ersetzen
                text = fill_door_code(text, coordinator.doorcodes.code_for_send(call.data[ATTR_RESERVATION_ID]))
            await coordinator.client.send_message(
                call.data[ATTR_RESERVATION_ID],
                text,
                subject=call.data.get(ATTR_SUBJECT),
                to_host=call.data.get(ATTR_RECIPIENT, "guest") == "host",
                internal=call.data.get(ATTR_INTERNAL, False),
            )
        except SmoobuError as err:
            raise HomeAssistantError(str(err)) from err

    # --- Schreibende Aktionen (v1.9.0) ---------------------------------
    def _apartment(coordinator: SmoobuCoordinator, call: ServiceCall) -> int:
        apts = list(coordinator.data.apartments) if coordinator.data else []
        apt = call.data.get(ATTR_APARTMENT_ID)
        if apt is None and len(apts) == 1:
            return apts[0]
        if apt not in apts:
            raise ServiceValidationError(f"Wohnung {apt} unbekannt (vorhanden: {apts})")
        return apt

    async def _after_write(coordinator: SmoobuCoordinator) -> None:
        # Geänderte Buchungen/Preise sofort neu laden (auch Umsatz- und Preisdaten)
        coordinator.force_revenue_refresh = True
        await coordinator.async_request_refresh()

    async def block_period(call: ServiceCall) -> ServiceResponse:
        """Zeitraum sperren: Buchung über den Sperr-Kanal von Smoobu."""
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "belegung")
        apt = _apartment(coordinator, call)
        start, end = call.data[ATTR_START], call.data[ATTR_END]
        if end <= start:
            raise ServiceValidationError("Enddatum (Abreise) muss nach dem Startdatum liegen")
        # Sperr-Kanal-ID aus vorhandenen Sperrzeiten (Smoobu „Blocked channel“)
        channel_id = block_channel_id(coordinator.records(apt))
        if channel_id is None:
            raise ServiceValidationError(
                "Keine Sperrzeit in Smoobu gefunden, aus der die ID des Sperr-Kanals gelesen werden kann. "
                "Bitte einmal in Smoobu einen Zeitraum sperren."
            )
        body: dict[str, Any] = {
            "arrivalDate": start.isoformat(),
            "departureDate": end.isoformat(),
            "apartmentId": apt,
            "channelId": channel_id,
        }
        if call.data.get(ATTR_NOTICE):
            body["notice"] = call.data[ATTR_NOTICE]
        try:
            # v1.18.0: create_block ergänzt Pflichtfelder (Gastdaten) nur, wenn das Smoobu-Konto sie verlangt
            result = await coordinator.client.create_block(body)
        except SmoobuError as err:
            raise HomeAssistantError(str(err)) from err
        await _after_write(coordinator)
        return {"reservation": result}

    async def delete_reservation(call: ServiceCall) -> None:
        """Sperrzeit löschen bzw. Direktbuchung stornieren. Portalbuchungen nie."""
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "belegung")
        rid = call.data[ATTR_RESERVATION_ID]
        record = next(
            (r for apt in (coordinator.data.apartments if coordinator.data else {})
             for r in coordinator.records(apt) if r["id"] == rid),
            None,
        )
        if record is None:
            raise ServiceValidationError(f"Buchung {rid} nicht gefunden")
        if not record["blockiert"]:
            # Schutz: Portalbuchungen müssen im Portal storniert werden;
            # Direktbuchungen nur mit ausdrücklicher Freigabe (allow_booking).
            if record["gruppe"] != "Direkt":
                raise ServiceValidationError(
                    f"Buchung {rid} kommt über {record['kanal']} und muss dort storniert werden"
                )
            if not call.data.get(ATTR_ALLOW_BOOKING):
                raise ServiceValidationError(
                    f"Buchung {rid} ist eine Gästebuchung. Zum Stornieren allow_booking: true setzen"
                )
        try:
            await coordinator.client.delete_reservation(rid)
        except SmoobuError as err:
            raise HomeAssistantError(str(err)) from err
        await _after_write(coordinator)

    async def set_rates(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "preise")
        apt = _apartment(coordinator, call)
        price, min_stay = call.data.get(ATTR_PRICE), call.data.get(ATTR_MIN_STAY)
        if price is None and min_stay is None:
            raise ServiceValidationError("Preis und/oder Mindestaufenthalt angeben")
        start, end = call.data[ATTR_START], call.data[ATTR_END]
        if end < start:
            raise ServiceValidationError("Enddatum liegt vor dem Startdatum")
        try:
            await coordinator.client.set_rates(apt, start.isoformat(), end.isoformat(), price, min_stay)
        except SmoobuError as err:
            raise HomeAssistantError(str(err)) from err
        await _after_write(coordinator)

    async def update_reservation(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "belegung")
        body: dict[str, Any] = {}
        if call.data.get(ATTR_ARRIVAL_TIME):
            body["arrivalTime"] = call.data[ATTR_ARRIVAL_TIME].strftime("%H:%M")
        if call.data.get(ATTR_DEPARTURE_TIME):
            body["departureTime"] = call.data[ATTR_DEPARTURE_TIME].strftime("%H:%M")
        if ATTR_NOTICE in call.data:
            body["notice"] = call.data[ATTR_NOTICE]
        # v1.17.0: Zahlungsstatus (Smoobu: priceStatus/prepaymentStatus/depositStatus, 1 = bezahlt, 0 = offen)
        for attr, key in (("price_paid", "priceStatus"), ("prepayment_paid", "prepaymentStatus"),
                          ("deposit_paid", "depositStatus")):
            if attr in call.data:
                body[key] = 1 if call.data[attr] else 0
        if not body:
            raise ServiceValidationError("Nichts zu ändern angegeben")
        try:
            await coordinator.client.update_reservation(call.data[ATTR_RESERVATION_ID], body)
        except SmoobuError as err:
            raise HomeAssistantError(str(err)) from err
        await _after_write(coordinator)

    hass.services.async_register(
        DOMAIN,
        SERVICE_BLOCK_PERIOD,
        block_period,
        vol.Schema(
            {
                **entry_field,
                vol.Optional(ATTR_APARTMENT_ID): vol.Coerce(int),
                vol.Required(ATTR_START): cv.date,
                vol.Required(ATTR_END): cv.date,
                vol.Optional(ATTR_NOTICE): cv.string,
            }
        ),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_RESERVATION,
        delete_reservation,
        vol.Schema(
            {
                **entry_field,
                vol.Required(ATTR_RESERVATION_ID): vol.Coerce(int),
                vol.Optional(ATTR_ALLOW_BOOKING, default=False): cv.boolean,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_RATES,
        set_rates,
        vol.Schema(
            {
                **entry_field,
                vol.Optional(ATTR_APARTMENT_ID): vol.Coerce(int),
                vol.Required(ATTR_START): cv.date,
                vol.Required(ATTR_END): cv.date,
                vol.Optional(ATTR_PRICE): vol.All(vol.Coerce(float), vol.Range(min=1)),
                vol.Optional(ATTR_MIN_STAY): vol.All(vol.Coerce(int), vol.Range(min=1, max=90)),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_RESERVATION,
        update_reservation,
        vol.Schema(
            {
                **entry_field,
                vol.Required(ATTR_RESERVATION_ID): vol.Coerce(int),
                vol.Optional(ATTR_ARRIVAL_TIME): cv.time,
                vol.Optional(ATTR_DEPARTURE_TIME): cv.time,
                vol.Optional(ATTR_NOTICE): cv.string,
                vol.Optional("price_paid"): cv.boolean,
                vol.Optional("prepayment_paid"): cv.boolean,
                vol.Optional("deposit_paid"): cv.boolean,
            }
        ),
    )

    # --- KI-Assistent (v1.10.0) ---------------------------------------
    async def assistant_suggest(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "antworten")
        try:
            return await coordinator.assistant.suggest(
                call.data[ATTR_RESERVATION_ID], call.data.get("anlass", "antwort"),
                call.data.get(ATTR_MESSAGE), notify=call.data.get("push", False))
        except SmoobuError as err:
            raise HomeAssistantError(str(err)) from err

    async def assistant_import(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "antworten")
        state = await coordinator.assistant.import_history(call.data.get("jahre", 2))
        return {k: v for k, v in state.items() if k != "vorlagen"}

    async def assistant_knowledge(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call)
        await _require(call, coordinator, "antworten")
        try:
            return {"neu": await coordinator.assistant.build_knowledge()}
        except SmoobuError as err:
            raise HomeAssistantError(str(err)) from err

    hass.services.async_register(
        DOMAIN, SERVICE_ASSIST_SUGGEST, assistant_suggest,
        vol.Schema({**entry_field, vol.Required(ATTR_RESERVATION_ID): vol.Coerce(int),
                    vol.Optional("anlass", default="antwort"): vol.In(["antwort", "willkommen", "anreise", "abreise", "bewertung"]),
                    vol.Optional(ATTR_MESSAGE): cv.string, vol.Optional("push", default=False): cv.boolean}),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ASSIST_IMPORT, assistant_import,
        vol.Schema({**entry_field, vol.Optional("jahre", default=2): vol.All(vol.Coerce(int), vol.Range(min=1, max=5))}),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ASSIST_KNOWLEDGE, assistant_knowledge, vol.Schema({**entry_field}),
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(DOMAIN, SERVICE_REFRESH, refresh, vol.Schema({}))
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_RESERVATIONS,
        get_reservations,
        vol.Schema(
            {
                **entry_field,
                vol.Optional(ATTR_ARRIVAL_FROM): cv.date,
                vol.Optional(ATTR_ARRIVAL_TO): cv.date,
                vol.Optional(ATTR_DEPARTURE_FROM): cv.date,
                vol.Optional(ATTR_DEPARTURE_TO): cv.date,
                vol.Optional(ATTR_APARTMENT_ID): vol.Coerce(int),
                vol.Optional(ATTR_SHOW_CANCELLATION): cv.boolean,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_RESERVATION,
        get_reservation,
        vol.Schema({**entry_field, vol.Required(ATTR_RESERVATION_ID): vol.Coerce(int)}),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_MESSAGES,
        get_messages,
        vol.Schema(
            {
                **entry_field,
                vol.Required(ATTR_RESERVATION_ID): vol.Coerce(int),
                vol.Optional(ATTR_ONLY_GUEST): cv.boolean,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_MESSAGE,
        send_message,
        vol.Schema(
            {
                **entry_field,
                vol.Required(ATTR_RESERVATION_ID): vol.Coerce(int),
                vol.Required(ATTR_MESSAGE): cv.string,
                vol.Optional(ATTR_SUBJECT): cv.string,
                vol.Optional(ATTR_RECIPIENT, default="guest"): vol.In(["guest", "host"]),
                vol.Optional(ATTR_INTERNAL, default=False): cv.boolean,
            }
        ),
    )

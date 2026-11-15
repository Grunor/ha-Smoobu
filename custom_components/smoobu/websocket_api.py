"""WebSocket-Schnittstelle für die Smoobu-Karten im Dashboard (ab v1.8.0).

Die Karten (www/smoobu-cards.js) holen ihre Daten hierüber statt aus
Entitäts-Attributen. Vorteil: frei wählbare Zeiträume und Kanäle, Buchungslisten
ohne Größenbegrenzung der Attribute und keine Last auf der HA-Datenbank.

Befehle (alle nur für angemeldete HA-Benutzer):
- smoobu/info              Wohnungen, Kanäle (mit Farbe/Gruppe), Zeiträume, Optionen
- smoobu/analytics         Kennzahlen + Reihe + Vergleich + Prognose für Zeitraum/Kanäle
- smoobu/bookings          Buchungsliste mit Filtern (Zeitraum, Kanal, Status, Suche)
- smoobu/booking           Einzelbuchung frisch von Smoobu inkl. Nachrichtenverlauf
- smoobu/rates             Tagespreise, Mindestaufenthalt, Verfügbarkeit für einen Zeitraum
- smoobu/subscribe         Meldung bei jedem neuen Datenstand (Karten laden dann neu)
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .analytics import (
    COMPARES,
    PERIODS,
    analyze_with_compare,
    block_channel_id,
    channels_of,
    forecast_year,
    period_range,
)
from .api import SmoobuError
from .const import DOMAIN
from .coordinator import SmoobuCoordinator
from .models import strip_html

# Feste, gut unterscheidbare Farben je Kanal (Portalfarben angelehnt an die Marken,
# Direktkanäle in Grüntönen). Unbekannte Kanäle bekommen Farben aus PALETTE.
CHANNEL_COLORS = {
    "airbnb": "#FF5A5F",
    "booking.com": "#1E5BB8",
    "fewo-direkt": "#F2A900",
    "vrbo": "#F2A900",
    "expedia": "#7B3FBF",
    "hometogo": "#E4572E",
    "direct booking": "#2E9E5B",
    "website": "#61C08A",
}
PALETTE = ["#00A6A6", "#B05FB5", "#8D6E63", "#5C6BC0", "#C0CA33", "#26A69A"]
BLOCKED_COLOR = "#9E9E9E"


def _coordinators(hass: HomeAssistant) -> list[SmoobuCoordinator]:
    return [
        e.runtime_data
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.state is ConfigEntryState.LOADED
    ]


def _resolve(hass: HomeAssistant, msg: dict[str, Any]) -> tuple[SmoobuCoordinator, int]:
    """Coordinator + Wohnung aus entry_id/apartment_id, sonst die erste."""
    coords = _coordinators(hass)
    if entry_id := msg.get("entry_id"):
        coords = [c for c in coords if c.config_entry.entry_id == entry_id]
    if not coords:
        raise vol.Invalid("Keine geladene Smoobu-Integration")
    apt = msg.get("apartment_id")
    for c in coords:
        apts = list(c.data.apartments) if c.data else []
        if apt is None and apts:
            return c, apts[0]
        if apt in apts:
            return c, apt
    raise vol.Invalid(f"Wohnung {apt} nicht gefunden")


def channel_colors(names: list[str]) -> dict[str, str]:
    out, i = {}, 0
    for name in names:
        color = CHANNEL_COLORS.get(name.casefold())
        if color is None:
            color = PALETTE[i % len(PALETTE)]
            i += 1
        out[name] = color
    return out


def _date(value: str | None, default: date | None = None) -> date | None:
    return date.fromisoformat(value[:10]) if value else default


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_info)
    websocket_api.async_register_command(hass, ws_analytics)
    websocket_api.async_register_command(hass, ws_bookings)
    websocket_api.async_register_command(hass, ws_booking)
    websocket_api.async_register_command(hass, ws_rates)
    websocket_api.async_register_command(hass, ws_subscribe)
    websocket_api.async_register_command(hass, ws_assistant_state)
    websocket_api.async_register_command(hass, ws_assistant_knowledge)
    websocket_api.async_register_command(hass, ws_assistant_delete)
    websocket_api.async_register_command(hass, ws_assistant_suggest)
    websocket_api.async_register_command(hass, ws_assistant_send)
    websocket_api.async_register_command(hass, ws_assistant_job)


_TARGET = {vol.Optional("entry_id"): str, vol.Optional("apartment_id"): vol.Coerce(int)}


@websocket_api.websocket_command({vol.Required("type"): "smoobu/info"})
@callback
def ws_info(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    result = []
    for c in _coordinators(hass):
        for apt_id, apt in (c.data.apartments if c.data else {}).items():
            chans = channels_of(c.records(apt_id))
            colors = channel_colors([ch["name"] for ch in chans])
            blocked = block_channel_id(c.records(apt_id))
            result.append(
                {
                    "entry_id": c.config_entry.entry_id,
                    "title": c.config_entry.title,
                    "apartment_id": apt_id,
                    "name": apt.get("name"),
                    "currency": apt.get("currency") or "EUR",
                    "max_personen": (apt.get("rooms") or {}).get("maxOccupancy"),
                    "kanaele": [{**ch, "farbe": colors[ch["name"]]} for ch in chans],
                    "sperr_kanal_id": blocked,
                    "direktkanaele": c.direct_channels,
                    "check_in": c.config_entry.options.get("default_checkin"),
                    "check_out": c.config_entry.options.get("default_checkout"),
                    "erster_tag": min((r["anreise"] for r in c.records(apt_id)), default=None),
                    "aktualisiert": c.data.last_update.isoformat() if c.data and c.data.last_update else None,
                }
            )
    connection.send_result(
        msg["id"],
        {"wohnungen": result, "zeitraeume": PERIODS, "vergleiche": COMPARES, "sperr_farbe": BLOCKED_COLOR,
         "heute": dt_util.now().date().isoformat()},
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "smoobu/analytics",
        **_TARGET,
        vol.Optional("period"): vol.In(PERIODS),
        vol.Optional("start"): str,
        vol.Optional("end"): str,  # exklusiv
        vol.Optional("channels"): [str],
        vol.Optional("compare", default="vorjahr"): vol.In(COMPARES),
    }
)
@callback
def ws_analytics(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        c, apt = _resolve(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    recs = c.records(apt)
    today = dt_util.now().date()
    if msg.get("period"):
        first = min((date.fromisoformat(r["anreise"]) for r in recs), default=None)
        start, end = period_range(msg["period"], today, first)
    else:
        start = _date(msg.get("start"), date(today.year, 1, 1))
        end = _date(msg.get("end"), date(today.year + 1, 1, 1))
    if end <= start:
        connection.send_error(msg["id"], "invalid_range", "Ende muss nach dem Start liegen")
        return
    channels = msg.get("channels") or None
    result = analyze_with_compare(recs, start, end, channels, msg["compare"])
    result["prognose"] = forecast_year(recs, today, channels)
    result["farben"] = channel_colors([ch["name"] for ch in channels_of(recs)])
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "smoobu/bookings",
        **_TARGET,
        vol.Optional("start"): str,
        vol.Optional("end"): str,
        vol.Optional("channels"): [str],
        vol.Optional("status"): [str],
        vol.Optional("search"): str,
    }
)
@callback
def ws_bookings(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        c, apt = _resolve(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    start, end = _date(msg.get("start")), _date(msg.get("end"))
    names = {n.casefold() for n in msg.get("channels") or []}
    status = set(msg.get("status") or [])
    needle = (msg.get("search") or "").casefold().strip()
    out = []
    for r in c.records(apt):
        if start and r["abreise"] <= start.isoformat():
            continue
        if end and r["anreise"] >= end.isoformat():
            continue
        if names and (r["kanal"] or "").casefold() not in names and not (
            ("direkt" in names and r["gruppe"] == "Direkt") or ("portale" in names and r["gruppe"] == "Portal")
        ):
            continue
        if status and r["status"] not in status:
            continue
        if needle:
            hay = " ".join(
                str(r.get(k) or "") for k in ("gast", "email", "telefon", "referenz", "notiz", "kanal", "id")
            ).casefold()
            if needle not in hay:
                continue
        out.append(r)
    connection.send_result(msg["id"], {"buchungen": out, "anzahl": len(out)})


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/booking", **_TARGET, vol.Required("reservation_id"): vol.Coerce(int)}
)
@websocket_api.async_response
async def ws_booking(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        c, apt = _resolve(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    rid = msg["reservation_id"]
    record = next((r for r in c.records(apt) if r["id"] == rid), None)
    raw: dict[str, Any] = {}
    messages: list[dict[str, Any]] = []
    error = None
    try:
        raw = await c.client.get_reservation(rid)
        if record is None or not record["blockiert"]:
            messages = await c.client.get_messages(rid, False)
    except SmoobuError as err:
        error = str(err)
    msgs = [
        {
            "id": m.get("id"),
            "betreff": m.get("subject"),
            "text": strip_html(m.get("message") or m.get("messageHtml") or m.get("htmlMessage") or ""),
            # type 1 = Gast → Gastgeber, 2 = Gastgeber → Gast (laut Smoobu); sonst unbekannt
            "typ": m.get("type"),
            "zeit": m.get("createdAt") or m.get("created-at") or m.get("created_at"),
            "intern": bool(m.get("internal") or m.get("isInternal")),
        }
        for m in sorted(messages, key=lambda m: int(m.get("id") or 0))
    ]
    connection.send_result(msg["id"], {"buchung": record, "smoobu": raw, "nachrichten": msgs, "fehler": error})


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/rates", **_TARGET, vol.Optional("start"): str, vol.Optional("end"): str}
)
@websocket_api.async_response
async def ws_rates(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        c, apt = _resolve(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    today = dt_util.now().date()
    start = _date(msg.get("start"), today)
    end = _date(msg.get("end"), start + timedelta(days=90))
    if (end - start).days > 400:
        connection.send_error(msg["id"], "invalid_range", "Maximal 400 Tage")
        return
    try:
        rates = await c.client.get_rates(apt, start.isoformat(), end.isoformat())
    except SmoobuError as err:
        connection.send_error(msg["id"], "smoobu_error", str(err))
        return
    connection.send_result(msg["id"], {"preise": rates})


@websocket_api.websocket_command({vol.Required("type"): "smoobu/subscribe"})
@callback
def ws_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Bei jedem neuen Datenstand ein Ereignis senden (Karten laden neu)."""
    removers = []

    @callback
    def changed() -> None:
        connection.send_message(
            websocket_api.event_message(msg["id"], {"zeit": dt_util.now().isoformat()})
        )

    for c in _coordinators(hass):
        removers.append(c.async_add_listener(changed))
        if c.assistant is not None:  # Wissensdatenbank/Vorschläge geändert
            removers.append(c.assistant.add_listener(changed))

    @callback
    def unsub() -> None:
        for r in removers:
            r()

    connection.subscriptions[msg["id"]] = unsub
    connection.send_result(msg["id"])


# ---------------------------------------------------------------------------
# KI-Assistent (v1.10.0)
# ---------------------------------------------------------------------------
def _assistant(hass: HomeAssistant, msg: dict[str, Any]):
    c, _apt = _resolve(hass, msg)
    if c.assistant is None:
        raise vol.Invalid("Assistent nicht geladen")
    return c.assistant


@websocket_api.websocket_command({vol.Required("type"): "smoobu/assistant/state", **_TARGET})
@callback
def ws_assistant_state(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        connection.send_result(msg["id"], _assistant(hass, msg).state())
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "smoobu/assistant/knowledge",
        **_TARGET,
        vol.Required("item"): {
            vol.Optional("id"): str,
            vol.Optional("thema"): str,
            vol.Optional("text"): str,
            vol.Optional("status"): vol.In(["aktiv", "vorschlag", "aus"]),
            vol.Optional("vertraulich"): bool,
        },
    }
)
@callback
def ws_assistant_knowledge(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        connection.send_result(msg["id"], _assistant(hass, msg).save_knowledge(msg["item"]))
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/assistant/delete", **_TARGET,
     vol.Required("kind"): vol.In(["wissen", "beispiel"]), vol.Required("item_id"): str}
)
@callback
def ws_assistant_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        a = _assistant(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    (a.delete_knowledge if msg["kind"] == "wissen" else a.delete_example)(msg["item_id"])
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/assistant/suggest", **_TARGET, vol.Required("reservation_id"): vol.Coerce(int),
     vol.Optional("anlass", default="antwort"): str, vol.Optional("text"): str}
)
@websocket_api.async_response
async def ws_assistant_suggest(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        a = _assistant(hass, msg)
        connection.send_result(msg["id"], await a.suggest(msg["reservation_id"], msg["anlass"], msg.get("text")))
    except (vol.Invalid, SmoobuError) as err:
        connection.send_error(msg["id"], "assistant_error", str(err))


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/assistant/send", **_TARGET, vol.Required("reservation_id"): vol.Coerce(int),
     vol.Required("text"): str}
)
@websocket_api.async_response
async def ws_assistant_send(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        await _assistant(hass, msg).send(msg["reservation_id"], msg["text"])
        connection.send_result(msg["id"])
    except (vol.Invalid, SmoobuError) as err:
        connection.send_error(msg["id"], "assistant_error", str(err))


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/assistant/job", **_TARGET,
     vol.Required("job"): vol.In(["import", "wissen", "luecke"]), vol.Optional("arg"): str}
)
@websocket_api.async_response
async def ws_assistant_job(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        a = _assistant(hass, msg)
        if msg["job"] == "import":
            # Läuft länger (je Buchung eine Abfrage) → im Hintergrund, Fortschritt über state()
            hass.async_create_background_task(a.import_history(), "smoobu_assistant_import")
            connection.send_result(msg["id"], {"gestartet": True})
        elif msg["job"] == "wissen":
            connection.send_result(msg["id"], {"neu": await a.build_knowledge()})
        else:
            await a.apply_gap(msg.get("arg") or "")
            connection.send_result(msg["id"])
    except (vol.Invalid, SmoobuError) as err:
        connection.send_error(msg["id"], "assistant_error", str(err))

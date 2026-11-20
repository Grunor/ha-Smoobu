"""WebSocket-Schnittstelle für die Smoobu-Karten im Dashboard (ab v1.8.0).

Die Karten (www/smoobu-cards.js) holen ihre Daten hierüber statt aus
Entitäts-Attributen. Vorteil: frei wählbare Zeiträume und Kanäle, Buchungslisten
ohne Größenbegrenzung der Attribute und keine Last auf der HA-Datenbank.

Befehle (alle nur für angemeldete HA-Benutzer):
- smoobu/info              Wohnungen, Kanäle (mit Farbe/Gruppe), Zeiträume, Optionen
- smoobu/analytics         Kennzahlen + Reihe + Vergleich + Prognose für Zeitraum/Kanäle
- smoobu/bookings          Buchungsliste mit Filtern (Zeitraum, Kanal, Status, Suche)
- smoobu/booking           Einzelbuchung frisch von Smoobu inkl. Nachrichtenverlauf
- smoobu/message_status   Antwortstatus je Buchung (letzte Nachricht vom Gast = offen, v1.13.0)
- smoobu/message_done     „Keine Antwort erforderlich“ setzen/aufheben (v1.14.0)
- smoobu/rates             Tagespreise, Mindestaufenthalt, Verfügbarkeit für einen Zeitraum
- smoobu/stats             Statistik-Werkbank: Baukasten-Abfrage und Pace-Modell (v1.18.0)
- smoobu/subscribe         Meldung bei jedem neuen Datenstand (Karten laden dann neu)
- smoobu/settings/get      Optionen + Auswahllisten für die Einstellungskarte (v1.18.0)
- smoobu/settings/set      geänderte Optionen prüfen und speichern (v1.18.0)
- smoobu/rates/apply       Preise/Mindestaufenthalt übernehmen (Vorschau mit dry_run), v1.18.0
- smoobu/rates/undo        gespeicherte Preisänderung rückgängig machen (v1.18.0)
- smoobu/rates/changes     letzte Preisänderungen (v1.18.0)
- smoobu/tasks/get         Aufgaben-Board: erledigte/verschobene Aufgaben + sichtbare Kategorien (v1.18.0)
- smoobu/tasks/set         Aufgabe erledigen / später / zurücksetzen (v1.18.0)

Ab v1.18.0 prüfen alle Befehle die Benutzerrolle (rechte.py): Finanzen/Statistik nur mit
„finanzen“, Buchungen mit „gaeste“ (Preisfelder nur mit „finanzen“), Nachrichten mit
„nachrichten“/„antworten“, Preise übernehmen mit „preise“.

Die beiden settings-Befehle prüfen die Berechtigung selbst: HA-Admins oder die in
der Option „Einstellungen im Dashboard erlauben für“ gewählten Benutzer.

Ab v1.15.0 akzeptieren bookings, analytics, booking, message_status,
message_done und der Assistent `apartment_id: "alle"` (Ansicht „Alle
Wohnungen“): Datensätze aller Wohnungen aller geladenen Smoobu-Konten,
Auslastung über die Summe der verfügbaren Nächte. rates bleibt je Wohnung,
weil Preise immer zu genau einer Wohnung gehören.
"""

from __future__ import annotations


from datetime import date, timedelta
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .codes import all_codes, short_codes  # noqa: F401  (short_codes: Rückwärtskompatibilität)
from .analytics import (
    COMPARES,
    RASTERS,
    PERIODS,
    analyze_with_compare,
    as_of as stats_as_of,
    block_channel_id,
    channels_of,
    forecast_year,
    guest_history,
    period_range,
)
from .api import SmoobuError
from .seasons import from_options as seasons_from_options
from . import umbuchung
from .stats import DIMENSIONS, MEASURES, gaps as stats_gaps, pace as stats_pace, query as stats_query
from .stats import ranking as stats_ranking, service as stats_service, storno as stats_storno
from .empfehlung import recommend as stats_recommend
from .const import CONF_TASK_CATEGORIES, DEFAULT_TASK_CATEGORIES, DOMAIN, TASK_CATEGORIES, TASK_RIGHTS
from .coordinator import SmoobuCoordinator
from .models import strip_html
from . import settings as smoobu_settings
from . import rechte

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


ALL = "alle"  # apartment_id für die Ansicht „Alle Wohnungen“ (v1.15.0)


def _targets(hass: HomeAssistant, msg: dict[str, Any]) -> list[tuple[SmoobuCoordinator, int]]:
    """Alle (Coordinator, Wohnung)-Paare, die eine Anfrage betrifft.

    apartment_id = Zahl → genau diese Wohnung; „alle“ → jede Wohnung jedes
    geladenen Kontos (optional auf entry_id begrenzt); fehlt sie → die erste
    Wohnung (Verhalten bis v1.14, damit bestehende Karten unverändert bleiben).
    """
    coords = _coordinators(hass)
    if entry_id := msg.get("entry_id"):
        coords = [c for c in coords if c.config_entry.entry_id == entry_id]
    if not coords:
        raise vol.Invalid("Keine geladene Smoobu-Integration")
    apt = msg.get("apartment_id")
    pairs = [(c, a) for c in coords for a in (list(c.data.apartments) if c.data else [])]
    if apt == ALL:
        if not pairs:
            raise vol.Invalid("Keine Wohnung gefunden")
        return pairs
    if apt is None:
        if pairs:
            return pairs[:1]
        raise vol.Invalid("Keine Wohnung gefunden")
    for c, a in pairs:
        if a == apt:
            return [(c, a)]
    raise vol.Invalid(f"Wohnung {apt} nicht gefunden")


def _resolve(hass: HomeAssistant, msg: dict[str, Any]) -> tuple[SmoobuCoordinator, int]:
    """Coordinator + Wohnung; bei „alle“ die Wohnung der Buchung (reservation_id), sonst die erste."""
    pairs = _targets(hass, msg)
    rid = msg.get("reservation_id")
    if len(pairs) > 1 and rid is not None:
        for c, a in pairs:
            if any(r["id"] == rid for r in c.records(a)):
                return c, a
    return pairs[0]


def _apt_id(value: Any) -> Any:
    """apartment_id aus der Anfrage: „alle“ bleibt Text, sonst ganze Zahl."""
    if value == ALL:
        return ALL
    return vol.Coerce(int)(value)


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
    websocket_api.async_register_command(hass, ws_stats)
    websocket_api.async_register_command(hass, ws_bookings)
    websocket_api.async_register_command(hass, ws_booking)
    websocket_api.async_register_command(hass, ws_rates)
    websocket_api.async_register_command(hass, ws_message_status)
    websocket_api.async_register_command(hass, ws_message_done)
    websocket_api.async_register_command(hass, ws_subscribe)
    websocket_api.async_register_command(hass, ws_assistant_state)
    websocket_api.async_register_command(hass, ws_assistant_knowledge)
    websocket_api.async_register_command(hass, ws_assistant_delete)
    websocket_api.async_register_command(hass, ws_assistant_suggest)
    websocket_api.async_register_command(hass, ws_assistant_send)
    websocket_api.async_register_command(hass, ws_assistant_job)
    websocket_api.async_register_command(hass, ws_assistant_preview)
    websocket_api.async_register_command(hass, ws_settings_get)
    websocket_api.async_register_command(hass, ws_settings_set)
    websocket_api.async_register_command(hass, ws_rates_apply)
    websocket_api.async_register_command(hass, ws_rates_undo)
    websocket_api.async_register_command(hass, ws_rates_changes)
    websocket_api.async_register_command(hass, ws_tasks_get)
    websocket_api.async_register_command(hass, ws_tasks_set)
    websocket_api.async_register_command(hass, ws_booking_move)


_TARGET = {vol.Optional("entry_id"): str, vol.Optional("apartment_id"): _apt_id}


def _guard(connection: websocket_api.ActiveConnection, msg: dict[str, Any], coords, right: str) -> bool:
    """v1.18.0: Benutzerrolle prüfen; ohne Recht Fehler „unauthorized“ senden und False liefern."""
    for c in dict.fromkeys(coords):
        if not rechte.allowed(connection.user, c.config_entry.options, right):
            connection.send_error(msg["id"], "unauthorized", f"Keine Berechtigung: {rechte.RIGHTS[right]}")
            return False
    return True


def _rights(connection: websocket_api.ActiveConnection, coords) -> frozenset[str]:
    """Schnittmenge der Rechte über alle beteiligten Konten (für das Ausdünnen von Daten)."""
    out = frozenset(rechte.RIGHTS)
    for c in dict.fromkeys(coords):
        out &= rechte.rights_of(connection.user, c.config_entry.options)
    return out


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
                    # v1.18.0: Rolle und Rechte des angemeldeten Benutzers (Karten blenden danach aus)
                    "zugriff": rechte.describe(connection.user, c.config_entry.options),
                }
            )
    # v1.17.0: eigene Kürzel aus den Optionen, sonst automatisch (eindeutig über alle Konten)
    codes = all_codes(hass)
    for apt in result:
        apt["kuerzel"] = codes.get((apt["entry_id"], apt["apartment_id"]), "?")
    connection.send_result(
        msg["id"],
        # v1.18.0: Saisons (Zeitraum-Filter „Saison“, Anzeige der Definition) – bei mehreren Konten die des ersten
        {"wohnungen": result, "zeitraeume": PERIODS, "vergleiche": COMPARES, "sperr_farbe": BLOCKED_COLOR,
         "saisons": seasons_from_options(next(iter(_coordinators(hass)), None).config_entry.options) if _coordinators(hass) else seasons_from_options({}),
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
        # v1.17.0: Anzahl Vergleichszeiträume (1 = wie bisher)
        vol.Optional("compare_count", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
        # v1.18.0b8: Raster der Reihe (Filterleiste der Finanzen wie in der Statistik)
        vol.Optional("raster", default="auto"): vol.In(RASTERS),
    }
)
@callback
def ws_analytics(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        pairs = _targets(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c for c, _ in pairs], "finanzen"):
        return
    recs = [r for c, a in pairs for r in c.records(a)]
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
    result = analyze_with_compare(recs, start, end, channels, msg["compare"], today=today, units=len(pairs),
                                  count=msg["compare_count"], raster=msg["raster"])
    result["prognose"] = forecast_year(recs, today, channels)
    result["farben"] = channel_colors([ch["name"] for ch in channels_of(recs)])
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "smoobu/stats",
        **_TARGET,
        # "query" = Baukasten (Kennzahl × Gruppierung × Aufteilung), "pace" = Buchungstempo + Prognose,
        # "meta" = verfügbare Kennzahlen/Dimensionen für die Auswahlfelder der Karte
        # Teilschritte 3/4: "gaps" = verlorene Nächte, "storno" = Storno-Auswertung, "service" = Antwortzeiten
        # v1.18.0: "empfehlung" = Bewertung (Pace je Monat), Preisuntergrenzen und Preis-Hinweise
        # v1.18.0b7: "ranking" = Ehrentafel (Goldene Fußmatte / Rostige Klobürste, Fun-Statistik)
        vol.Required("mode"): vol.In(("query", "pace", "meta", "gaps", "storno", "service", "empfehlung", "ranking")),
        vol.Optional("measure"): vol.In(tuple(MEASURES)),
        vol.Optional("dimension", default="monat"): vol.In(DIMENSIONS),
        vol.Optional("split"): vol.Any(None, vol.In(DIMENSIONS)),
        vol.Optional("start"): str,
        vol.Optional("end"): str,  # exklusiv
        vol.Optional("channels"): [str],
        vol.Optional("filters"): dict,
        vol.Optional("year"): vol.Coerce(int),
        # Teil 2 (Karte): Buchungsstand an diesem Tag statt heute – für den Vergleich
        # „Stichtag Vorjahr“ (gleiche Rechnung wie analytics.as_of: später angelegte
        # Buchungen fallen weg, Stornos über das Änderungsdatum angenähert)
        vol.Optional("as_of"): str,
    }
)
@websocket_api.async_response
async def ws_stats(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if msg["mode"] == "meta":
        connection.send_result(msg["id"], {
            "kennzahlen": [{"id": k, "art": v[0], "name": v[1], "einheit": v[2]} for k, v in MEASURES.items()],
            "dimensionen": list(DIMENSIONS),
        })
        return
    try:
        pairs = _targets(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c for c, _ in pairs], "finanzen"):
        return
    recs = [r for c, a in pairs for r in c.records(a)]
    today = dt_util.now().date()
    channels = msg.get("channels") or None
    if msg["mode"] == "pace":
        # Vorjahre nur, soweit die Historie reicht (frühester history_start der beteiligten Konten)
        first = min((c.history_start for c, _ in pairs), default=None)
        result = stats_pace(recs, msg.get("year") or today.year, today, channels=channels, first=first)
        connection.send_result(msg["id"], result)
        return
    if msg["mode"] == "empfehlung":
        # Preise und Kosten gehören zu genau einer Wohnung → je Wohnung rechnen, bei „Alle
        # Wohnungen“ eine Liste (die Karte zeigt dann je Wohnung einen Block)
        out = []
        for c, apt in pairs:
            table = c.data.cost_tables.get(apt) if c.data else None
            if table is None:
                continue
            res = stats_recommend(c.records(apt), c.rates_now(apt), table, c.price_config, today, first=c.history_start)
            res["wohnung"] = c.apartment_code(apt) if len(pairs) > 1 else ""
            res["apartment_id"] = apt
            # v1.18.0: Übernehmen-Buttons nur mit „preise“; letzte Änderungen für „Rückgängig“
            res["darf_aendern"] = rechte.allowed(connection.user, c.config_entry.options, "preise")
            res["aenderungen"] = [ch for ch in await c.async_price_changes() if ch["wohnung_id"] == apt][:5]
            res["wohnung_name"] = (c.data.apartments.get(apt) or {}).get("name")
            out.append(res)
        connection.send_result(msg["id"], {"wohnungen": out})
        return
    if msg["mode"] in ("gaps", "storno", "service", "ranking"):
        start = _date(msg.get("start"), date(today.year, 1, 1))
        end = _date(msg.get("end"), date(today.year + 1, 1, 1))
        if end <= start or (end - start).days > 3700:
            connection.send_error(msg["id"], "invalid_range", "Zeitraum ungültig (max. ~10 Jahre)")
            return
        if msg["mode"] == "storno":
            connection.send_result(msg["id"], stats_storno(recs, start, end, channels=channels))
        elif msg["mode"] == "ranking":
            # Standardzeiten der ersten beteiligten Integration (bei mehreren Konten in der Regel gleich)
            c0 = pairs[0][0] if pairs else None
            hours = lambda tm, fb: (tm.hour + tm.minute / 60) if tm else fb  # noqa: E731
            responses = {k: v for c, _ in pairs for k, v in c.responses.items()}
            connection.send_result(msg["id"], stats_ranking(
                recs, responses, start, end, today, channels=channels,
                checkin=hours(c0.default_checkin if c0 else None, 16.0),
                checkout=hours(c0.default_checkout if c0 else None, 11.0)))
        elif msg["mode"] == "service":
            responses = {k: v for c, _ in pairs for k, v in c.responses.items()}
            result = stats_service(recs, responses, start, end, channels=channels)
            result["abruf_laeuft"] = any(c._resp_task is not None and not c._resp_task.done() for c, _ in pairs)
            connection.send_result(msg["id"], result)
        else:
            connection.send_result(msg["id"], _gaps_all(pairs, start, end, today))
        return
    if not msg.get("measure"):
        connection.send_error(msg["id"], "invalid_format", "measure fehlt")
        return
    if msg.get("as_of"):
        try:
            stichtag = date.fromisoformat(msg["as_of"][:10])
        except ValueError:
            connection.send_error(msg["id"], "invalid_format", "as_of ungültig")
            return
        recs = stats_as_of(recs, stichtag)
    start = _date(msg.get("start"), date(today.year, 1, 1))
    end = _date(msg.get("end"), date(today.year + 1, 1, 1))
    if end <= start or (end - start).days > 3700:
        connection.send_error(msg["id"], "invalid_range", "Zeitraum ungültig (max. ~10 Jahre)")
        return
    try:
        result = stats_query(recs, msg["measure"], msg["dimension"], start, end, split=msg.get("split"),
                             channels=channels, units=len(pairs), filters=msg.get("filters"),
                             seasons=seasons_from_options(pairs[0][0].config_entry.options) if pairs else None)
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    connection.send_result(msg["id"], result)


def _gaps_all(pairs: list[tuple[SmoobuCoordinator, int]], start: date, end: date, today: date) -> dict[str, Any]:
    """Verlorene Nächte je Wohnung berechnen und zusammenführen (Lücken gibt es nur je Wohnung)."""
    items, hints = [], []
    lengths: dict[str, int] = {}
    for c, apt in pairs:
        res = stats_gaps(c.records(apt), start, end, today, rates_now=c.rates_now(apt), price_history=c.price_history(apt))
        code = c.apartment_code(apt) if len(pairs) > 1 else ""
        items += [{**g, "wohnung": code} for g in res["luecken"]]
        hints += [{**h, "wohnung": code} for h in res["vorschlaege"]]
        for x in res["laengen"]:
            lengths[x["fach"]] = lengths.get(x["fach"], 0) + x["anzahl"]

    def summary(sel: list[dict[str, Any]]) -> dict[str, Any]:
        return {"luecken": len(sel), "naechte": sum(g["naechte"] for g in sel), "wert": round(sum(g["wert"] for g in sel), 2),
                "zu_kurz": sum(1 for g in sel if g["zu_kurz"]), "zu_kurz_naechte": sum(g["naechte"] for g in sel if g["zu_kurz"]),
                "geschaetzt": sum(1 for g in sel if g["quelle"] == "geschaetzt")}

    items.sort(key=lambda g: g["von"])
    return {"luecken": items, "vergangen": summary([g for g in items if g["vergangen"]]),
            "kommend": summary([g for g in items if not g["vergangen"]]), "vorschlaege": hints,
            "laengen": [{"fach": k, "anzahl": lengths.get(k, 0)} for k in ["1", "2", "3", "4", "5", "6", "7+"]]}


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
        pairs = _targets(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c for c, _ in pairs], "gaeste"):
        return
    allowed = _rights(connection, [c for c, _ in pairs])
    start, end = _date(msg.get("start")), _date(msg.get("end"))
    names = {n.casefold() for n in msg.get("channels") or []}
    status = set(msg.get("status") or [])
    needle = (msg.get("search") or "").casefold().strip()
    out = []
    # v1.18.0: frühere Aufenthalte je Gast – über alle Wohnungen des Kontos („bei uns“), nicht nur die gewählte
    hist: dict[Any, dict[str, Any]] = {}
    for c in dict.fromkeys(c for c, _ in pairs):
        hist.update(guest_history(c.records_all()))
    recs = [r for c, a in pairs for r in c.records(a)]
    if len(pairs) > 1:  # gemischt → nach Anreise sortieren wie bei einer Wohnung
        recs.sort(key=lambda r: (r["anreise"], r["id"]))
    for r in recs:
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
        out.append(rechte.strip({**r, **hist.get(r["id"], {})}, allowed))
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
    if not _guard(connection, msg, [c], "gaeste"):
        return
    allowed = _rights(connection, [c])
    rid = msg["reservation_id"]
    record = next((r for r in c.records(apt) if r["id"] == rid), None)
    raw: dict[str, Any] = {}
    messages: list[dict[str, Any]] = []
    error = None
    try:
        raw = await c.client.get_reservation(rid)
        if (record is None or not record["blockiert"]) and "nachrichten" in allowed:
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
    if record:  # v1.18.0: frühere Aufenthalte des Gastes (alle Wohnungen des Kontos)
        record = {**record, **guest_history(c.records_all()).get(record["id"], {})}
    connection.send_result(msg["id"], {"buchung": rechte.strip(record, allowed) if record else None,
                                       "smoobu": rechte.strip(raw or {}, allowed), "nachrichten": msgs, "fehler": error})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "smoobu/message_status",
        **_TARGET,
        # Begrenzung schützt vor zu vielen Smoobu-Abrufen auf einmal
        vol.Required("reservation_ids"): vol.All([vol.Coerce(int)], vol.Length(max=60)),
    }
)
@websocket_api.async_response
async def ws_message_status(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Posteingang: welche Gäste warten auf eine Antwort? (Schlüssel = Buchungs-ID als Text)"""
    try:
        pairs = _targets(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c for c, _ in pairs], "nachrichten"):
        return
    # Je Konto nur dessen Buchungen abfragen (Buchungs-IDs gelten je Smoobu-Konto)
    ids = msg["reservation_ids"]
    status: dict[Any, Any] = {}
    coords = list(dict.fromkeys(c for c, _a in pairs))
    for c in coords:
        own = {r["id"] for r in c.records_all()}
        mine = ids if len(coords) == 1 else [i for i in ids if i in own]
        if mine:
            status.update(await c.async_message_status(mine))
    connection.send_result(msg["id"], {"status": {str(k): v for k, v in status.items()}})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "smoobu/message_done",
        **_TARGET,
        vol.Required("reservation_id"): vol.Coerce(int),
        # True = keine Antwort nötig (neueste Gastnachricht gilt als erledigt), False = wieder offen
        vol.Optional("done", default=True): bool,
    }
)
@websocket_api.async_response
async def ws_message_done(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Posteingang: Gastnachricht bewusst ohne Antwort abhaken (Status der Buchung zurück)."""
    try:
        c, _apt = _resolve(hass, msg)
        if not _guard(connection, msg, [c], "antworten"):
            return
        status = await c.async_set_no_reply(msg["reservation_id"], msg["done"])
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    except SmoobuError as err:
        connection.send_error(msg["id"], "smoobu_error", str(err))
        return
    connection.send_result(msg["id"], {"status": status})


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/rates", **_TARGET, vol.Optional("start"): str, vol.Optional("end"): str}
)
@websocket_api.async_response
async def ws_rates(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if msg.get("apartment_id") == ALL:  # Preise gehören immer zu genau einer Wohnung
        connection.send_error(msg["id"], "invalid_target", "Preise nur je Wohnung abrufbar")
        return
    try:
        c, apt = _resolve(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c], "gaeste"):
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
    if not rechte.allowed(connection.user, c.config_entry.options, "finanzen"):
        # Ohne „finanzen“ nur Verfügbarkeit und Mindestaufenthalt (Belegungsplan bleibt nutzbar)
        rates = {d: {k: v for k, v in (x or {}).items() if k != "price"} for d, x in rates.items()}
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

    @callback
    def messages() -> None:
        # v1.17.0: nur Antwortstatus geändert → Karten zählen neu, ohne alles neu zu laden
        connection.send_message(
            websocket_api.event_message(msg["id"], {"zeit": dt_util.now().isoformat(), "art": "nachrichten"})
        )

    for c in _coordinators(hass):
        removers.append(c.async_add_listener(changed))
        removers.append(c.add_message_listener(messages))
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
def _assistant(hass: HomeAssistant, msg: dict[str, Any], connection=None, right: str = "nachrichten"):
    c, _apt = _resolve(hass, msg)
    # v1.18.0: Lesen = „nachrichten“, Ändern/Senden = „antworten“
    if connection is not None and not rechte.allowed(connection.user, c.config_entry.options, right):
        raise vol.Invalid(f"Keine Berechtigung: {rechte.RIGHTS[right]}")
    if c.assistant is None:
        raise vol.Invalid("Assistent nicht geladen")
    return c.assistant


@websocket_api.websocket_command({vol.Required("type"): "smoobu/assistant/state", **_TARGET})
@callback
def ws_assistant_state(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        connection.send_result(msg["id"], _assistant(hass, msg, connection, "nachrichten").state())
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
        connection.send_result(msg["id"], _assistant(hass, msg, connection, "antworten").save_knowledge(msg["item"]))
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/assistant/delete", **_TARGET,
     vol.Required("kind"): vol.In(["wissen", "beispiel", "vorschlag", "ignorieren"]), vol.Required("item_id"): str}
)
@websocket_api.async_response
async def ws_assistant_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Wissen/Beispiel löschen; v1.17.0: Vorschlag löschen bzw. ignorieren (item_id = Buchungs-ID)."""
    try:
        a = _assistant(hass, msg, connection, "antworten")
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    kind = msg["kind"]
    if kind == "wissen":
        a.delete_knowledge(msg["item_id"])
    elif kind == "beispiel":
        a.delete_example(msg["item_id"])
    else:
        try:
            rid = int(msg["item_id"])
        except ValueError:
            connection.send_error(msg["id"], "invalid_format", "Buchungs-ID erwartet")
            return
        await (a.delete_suggestion(rid) if kind == "vorschlag" else a.dismiss(rid))
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/assistant/suggest", **_TARGET, vol.Required("reservation_id"): vol.Coerce(int),
     vol.Optional("anlass", default="antwort"): str, vol.Optional("text"): str}
)
@websocket_api.async_response
async def ws_assistant_suggest(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        a = _assistant(hass, msg, connection, "antworten")
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
        await _assistant(hass, msg, connection, "antworten").send(msg["reservation_id"], msg["text"])
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
        a = _assistant(hass, msg, connection, "antworten")
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


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/assistant/preview", **_TARGET, vol.Optional("reservation_id"): vol.Coerce(int),
     vol.Optional("probelauf", default=False): bool,
     vol.Optional("anlass", default="antwort"): vol.In(["antwort", "willkommen", "anreise", "abreise", "bewertung"])}
)
@websocket_api.async_response
async def ws_assistant_preview(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """v1.18.0b6: Was geht an die KI? Ohne Buchung = zuletzt gesendeter Text, mit Buchung = Probelauf.

    Recht „antworten“ wie bei den Vorschlägen – der Text enthält die (geschützte) Gästenachricht.
    """
    try:
        a = _assistant(hass, msg, connection, "antworten")
        connection.send_result(msg["id"], await a.preview(msg.get("reservation_id"), msg["anlass"], msg["probelauf"]))
    except (vol.Invalid, SmoobuError) as err:
        connection.send_error(msg["id"], "assistant_error", str(err))


# ---------------------------------------------------------------------------
# Einstellungen im Dashboard (v1.18.0)
# ---------------------------------------------------------------------------
def _settings_entry(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]):
    """Smoobu-Konto, das der Benutzer ändern darf (entry_id oder das erste erlaubte)."""
    entries = smoobu_settings.editable_entries(hass, connection.user)
    if entry_id := msg.get("entry_id"):
        entries = [e for e in entries if e.entry_id == entry_id]
    return entries[0] if entries else None


@websocket_api.websocket_command({vol.Required("type"): "smoobu/settings/get", vol.Optional("entry_id"): str})
@websocket_api.async_response
async def ws_settings_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _settings_entry(hass, connection, msg)
    if entry is None:
        # Kein Fehler, sondern Hinweis in der Karte („keine Berechtigung“)
        connection.send_result(msg["id"], {"erlaubt": False})
        return
    connection.send_result(
        msg["id"],
        {
            "erlaubt": True,
            "entry_id": entry.entry_id,
            "konten": [{"entry_id": e.entry_id, "title": e.title}
                       for e in smoobu_settings.editable_entries(hass, connection.user)],
            "werte": smoobu_settings.current(entry),
            "meta": await smoobu_settings.meta(hass, entry, connection.user),
        },
    )


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/settings/set", vol.Optional("entry_id"): str, vol.Required("changes"): dict}
)
@websocket_api.async_response
async def ws_settings_set(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _settings_entry(hass, connection, msg)
    if entry is None:
        connection.send_error(msg["id"], "unauthorized", "Keine Berechtigung für die Smoobu-Einstellungen")
        return
    options, errors = smoobu_settings.validate(hass, entry, msg["changes"], connection.user)
    if errors:
        connection.send_result(msg["id"], {"ok": False, "fehler": errors})
        return
    changed = await smoobu_settings.save(hass, entry, options)
    connection.send_result(msg["id"], {"ok": True, "geaendert": changed, "werte": smoobu_settings.current(entry)})


# ---------------------------------------------------------------------------
# Preise übernehmen / rückgängig (v1.18.0)
# ---------------------------------------------------------------------------
_SPEC = vol.Schema({
    vol.Optional("von"): str,
    vol.Optional("bis"): str,  # inklusive
    vol.Optional("tage"): vol.All([str], vol.Length(max=400)),
    vol.Optional("wochentage"): [vol.All(vol.Coerce(int), vol.Range(min=0, max=6))],
    vol.Optional("preis"): vol.Any(None, vol.All(vol.Coerce(float), vol.Range(min=1, max=100000))),
    vol.Optional("prozent"): vol.Any(None, vol.All(vol.Coerce(float), vol.Range(min=-80, max=300))),
    vol.Optional("mindestaufenthalt"): vol.Any(None, vol.All(vol.Coerce(int), vol.Range(min=1, max=90))),
    vol.Optional("ohne_feiertage", default=False): bool,
    vol.Optional("nur_basispreis", default=False): bool,
    vol.Optional("label"): vol.All(str, vol.Length(max=200)),
})


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/rates/apply", **_TARGET, vol.Required("vorgabe"): _SPEC,
     vol.Optional("dry_run", default=False): bool}
)
@websocket_api.async_response
async def ws_rates_apply(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Empfehlung bzw. Hinweis übernehmen. dry_run=True liefert nur die Vorschau (je Tag alt → neu)."""
    if msg.get("apartment_id") == ALL:
        connection.send_error(msg["id"], "invalid_target", "Preise nur je Wohnung")
        return
    try:
        c, apt = _resolve(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c], "preise"):
        return
    spec = msg["vorgabe"]
    if not spec.get("tage") and not (spec.get("von") and spec.get("bis")):
        connection.send_error(msg["id"], "invalid_format", "Zeitraum (von/bis) oder Tage angeben")
        return
    user = connection.user.name if connection.user else None
    try:
        result = await c.async_apply_prices(apt, spec, user=user, dry_run=msg["dry_run"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    except SmoobuError as err:
        connection.send_error(msg["id"], "smoobu_error", str(err))
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/rates/undo", **_TARGET, vol.Required("aenderung_id"): str}
)
@websocket_api.async_response
async def ws_rates_undo(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        c, _apt = _resolve(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c], "preise"):
        return
    try:
        result = await c.async_undo_prices(msg["aenderung_id"], user=connection.user.name if connection.user else None)
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    except SmoobuError as err:
        connection.send_error(msg["id"], "smoobu_error", str(err))
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({vol.Required("type"): "smoobu/rates/changes", **_TARGET})
@websocket_api.async_response
async def ws_rates_changes(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        c, apt = _resolve(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c], "finanzen"):
        return
    changes = [ch for ch in await c.async_price_changes() if ch["wohnung_id"] == apt]
    connection.send_result(msg["id"], {"aenderungen": changes[:10],
                                       "darf_aendern": rechte.allowed(connection.user, c.config_entry.options, "preise")})


# ---------------------------------------------------------------------------
# Aufgaben-Board „Wartet auf dich“ (v1.18.0)
# ---------------------------------------------------------------------------
@websocket_api.websocket_command({vol.Required("type"): "smoobu/tasks/get", **_TARGET})
@websocket_api.async_response
async def ws_tasks_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Zustand je Konto (bei „Alle Wohnungen“ zusammengeführt). Die Aufgaben selbst baut die Karte."""
    try:
        pairs = _targets(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c for c, _ in pairs], "gaeste"):
        return
    state: dict[str, Any] = {}
    cats: list[str] = []
    for c in dict.fromkeys(c for c, _ in pairs):
        state.update(await c.async_task_state())
        for cat in c.config_entry.options.get(CONF_TASK_CATEGORIES, DEFAULT_TASK_CATEGORIES):
            if cat not in cats:
                cats.append(cat)
    connection.send_result(msg["id"], {"zustand": state, "kategorien": cats})


@websocket_api.websocket_command(
    {vol.Required("type"): "smoobu/tasks/set", **_TARGET, vol.Required("key"): vol.All(str, vol.Length(max=200)),
     vol.Required("kategorie"): vol.In(TASK_CATEGORIES),
     vol.Required("aktion"): vol.In(["erledigt", "spaeter", "zuruecksetzen"]),
     vol.Optional("tage", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=30))}
)
@websocket_api.async_response
async def ws_tasks_set(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        c, _apt = _resolve(hass, msg) if msg.get("apartment_id") != ALL else (_targets(hass, msg)[0][0], None)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c], TASK_RIGHTS[msg["kategorie"]]):
        return
    state = await c.async_set_task(msg["key"], msg["aktion"], connection.user.name if connection.user else None, msg["tage"])
    connection.send_result(msg["id"], {"zustand": state})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "smoobu/booking/move",
        **_TARGET,
        vol.Required("reservation_id"): vol.Coerce(int),
        vol.Required("anreise"): str,
        vol.Required("abreise"): str,  # exklusiv (Abreisetag)
        vol.Optional("wohnung_id"): vol.Coerce(int),  # Ziel-Unterkunft (Standard: bisherige)
        vol.Optional("preis"): vol.Any(None, vol.All(vol.Coerce(float), vol.Range(min=0, max=100000))),
        vol.Optional("dry_run", default=True): bool,
    }
)
@websocket_api.async_response
async def ws_booking_move(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """v1.18.0: Direktbuchung umbuchen (Zeitraum/Unterkunft), siehe umbuchung.py. dry_run = nur prüfen + Preisvorschlag."""
    try:
        c, _apt = _resolve(hass, msg)
    except vol.Invalid as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    if not _guard(connection, msg, [c], "belegung"):
        return
    finance = rechte.allowed(connection.user, c.config_entry.options, "finanzen")
    rid = msg["reservation_id"]
    record = next((r for r in c.records_all() if r["id"] == rid), None)
    if record is None:
        connection.send_error(msg["id"], "not_found", f"Buchung {rid} nicht gefunden")
        return
    try:
        arrival, departure = date.fromisoformat(msg["anreise"][:10]).isoformat(), date.fromisoformat(msg["abreise"][:10]).isoformat()
    except ValueError:
        connection.send_error(msg["id"], "invalid_format", "Datum ungültig")
        return
    target = msg.get("wohnung_id") or record.get("wohnung_id")
    if not c.data or target not in c.data.apartments:
        connection.send_error(msg["id"], "not_found", f"Unterkunft {target} unbekannt")
        return
    today = dt_util.now().date()
    errors = umbuchung.check(record, c.records(target), arrival, departure, target, today)
    clash = umbuchung.conflicts(record, c.records(target), arrival, departure)
    if clash:
        errors.append("belegt")
    # Tagespreise für den Vorschlag (alte Nächte ggf. ohne Preis → anteilig)
    rates_new: dict[str, Any] = {}
    rates_old: dict[str, Any] = {}
    try:
        last_new = (date.fromisoformat(departure) - timedelta(days=1)).isoformat()
        last_old = (date.fromisoformat(record["abreise"]) - timedelta(days=1)).isoformat()
        if departure > arrival:
            rates_new = await c.client.get_rates(target, arrival, last_new)
        rates_old = await c.client.get_rates(record["wohnung_id"], record["anreise"], last_old)
    except SmoobuError:
        pass  # Vorschlag dann anteilig; Prüfung der Belegung läuft über die Buchungsdaten
    result: dict[str, Any] = {
        "moeglich": not errors, "gruende": errors, "konflikte": clash,
        "naechte": max((date.fromisoformat(departure) - date.fromisoformat(arrival)).days, 0),
        "naechte_alt": record["naechte"], "mindestaufenthalt": umbuchung.min_stay_hint(rates_new, arrival, departure),
        **(umbuchung.price_suggestion(record, arrival, departure, target, rates_old, rates_new) if finance else {}),
    }
    if msg["dry_run"] or errors:
        connection.send_result(msg["id"], {**result, "gespeichert": False})
        return
    if msg.get("preis") is not None and not finance:
        connection.send_error(msg["id"], "unauthorized", f"Keine Berechtigung: {rechte.RIGHTS['finanzen']}")
        return
    body: dict[str, Any] = {"arrivalDate": arrival, "departureDate": departure}
    if target != record.get("wohnung_id"):
        body["apartmentId"] = target
    try:
        await c.client.update_reservation(rid, body)
        raw = await c.client.get_reservation(rid)
    except SmoobuError as err:
        connection.send_error(msg["id"], "smoobu_error", str(err))
        return
    check = umbuchung.verify(raw or {}, arrival, departure, target)
    if not check["ok"]:
        # Smoobu hat die (nicht dokumentierte) Änderung nicht übernommen → nichts weiter ändern, klar melden
        connection.send_result(msg["id"], {**result, "gespeichert": False, "nicht_uebernommen": True, "smoobu": check["smoobu"]})
        return
    price_saved = False
    if msg.get("preis") is not None and msg["preis"] != record.get("brutto"):
        try:
            await c.client.update_reservation(rid, {"price": msg["preis"]})
            price_saved = True
        except SmoobuError as err:
            result["preis_fehler"] = str(err)
    c.force_revenue_refresh = True
    await c.async_request_refresh()
    connection.send_result(msg["id"], {**result, "gespeichert": True, "preis_gespeichert": price_saved})

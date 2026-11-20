"""Einstellungen im Dashboard (ab v1.18.0).

Die Karte `custom:smoobu-settings-card` liest und schreibt hierüber dieselben
Optionen wie der Options-Dialog der Integration (config_entry.options).

Warum eigenes Modul statt Options-Flow im Dashboard:
- Den Options-Dialog dürfen nur HA-Admins öffnen. Hier dürfen zusätzlich die in
  der Option „Einstellungen im Dashboard erlauben für“ gewählten HA-Benutzer
  ändern (Prüfung im Backend, nicht nur in der Karte).
- Die Karte bekommt alle Werte flach mit Standardwerten und eine Liste der
  Auswahlmöglichkeiten (Handys, KI-Entitäten, Kanäle, Wohnungen).

Gespeichert wird über `async_update_entry` – der Update-Listener der
Integration lädt den Eintrag danach neu, genau wie beim Options-Dialog.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .channel_catalog import channel_choices, configured_channels
from . import seasons as season_cfg
from .codes import all_codes, clean_code
from .deckungsbeitrag import parse_grid_share, parse_markups
from . import rechte
from .const import (
    CONF_TASK_CATEGORIES,
    DEFAULT_TASK_CATEGORIES,
    TASK_CATEGORIES,
    CONF_LASTMINUTE_DAYS,
    CONF_LASTMINUTE_MAX_DISCOUNT,
    DEFAULT_LASTMINUTE_DAYS,
    DEFAULT_LASTMINUTE_MAX_DISCOUNT,
    CONF_DEFAULT_ROLE,
    CONF_USER_ROLES,
    DEFAULT_ROLE,
    CONF_CHANNEL_MARKUPS,
    DEFAULT_CHANNEL_MARKUPS,
    CONF_COST_CLEANING,
    DEFAULT_COST_CLEANING,
    CONF_COST_GRID_PRICE,
    DEFAULT_COST_GRID_PRICE,
    CONF_COST_GRID_SHARE,
    DEFAULT_COST_GRID_SHARE,
    CONF_COST_HEATING_YEAR,
    DEFAULT_COST_HEATING_YEAR,
    CONF_COST_HOT_WATER_YEAR,
    DEFAULT_COST_HOT_WATER_YEAR,
    CONF_COST_LAUNDRY,
    DEFAULT_COST_LAUNDRY,
    CONF_COST_POWER_KWH,
    DEFAULT_COST_POWER_KWH,
    CONF_COST_PV_VALUE,
    DEFAULT_COST_PV_VALUE,
    CONF_COST_REF_YEAR,
    DEFAULT_COST_REF_YEAR,
    CONF_COST_WATER_NIGHT,
    DEFAULT_COST_WATER_NIGHT,
    CONF_GENIUS_DISCOUNT,
    DEFAULT_GENIUS_DISCOUNT,
    CONF_GENIUS_SHARE,
    DEFAULT_GENIUS_SHARE,
    COMMISSION_FIELDS,
    CONF_AI_ENABLED,
    CONF_AI_ENTITY,
    CONF_APARTMENT_CODES,
    CONF_ASSIST_BRIEFING,
    CONF_ASSIST_BRIEFING_TIME,
    CONF_ASSIST_GAPS,
    CONF_ASSIST_PATH,
    CONF_ASSIST_STATUS,
    CONF_ASSISTANT,
    CONF_CHECKOUT_BUFFER,
    CONF_COMMISSION_OTHER,
    CONF_COMMISSIONS,
    CONF_DAYS_AHEAD,
    CONF_DAYS_BACK,
    CONF_DEFAULT_CHECKIN,
    CONF_DEFAULT_CHECKOUT,
    CONF_DIRECT_CHANNELS,
    CONF_ENRICH_COUNT,
    CONF_HISTORY_SINCE,
    CONF_HISTORY_YEARS,
    CONF_NOTIFY_GAPS_TIME,
    CONF_NOTIFY_PAYMENT_DAYS,
    CONF_NOTIFY_PAYMENT_TIME,
    CONF_NOTIFY_QUIET,
    CONF_NOTIFY_QUIET_FROM,
    CONF_NOTIFY_QUIET_MESSAGES,
    CONF_NOTIFY_QUIET_TO,
    CONF_PAYMENT_EXCLUDED_CHANNELS,
    CONF_SCAN_INTERVAL,
    CONF_SETTINGS_USERS,
    CONF_USE_WEBHOOK,
    DEFAULT_CHECKIN,
    DEFAULT_CHECKOUT,
    DEFAULT_CHECKOUT_BUFFER,
    DEFAULT_COMMISSION_OTHER,
    DEFAULT_COMMISSIONS,
    DEFAULT_DAYS_AHEAD,
    DEFAULT_DAYS_BACK,
    DEFAULT_DIRECT_CHANNELS,
    DEFAULT_ENRICH_COUNT,
    DEFAULT_HISTORY_YEARS,
    DEFAULT_NOTIFY_GAPS_TIME,
    DEFAULT_NOTIFY_PAYMENT_DAYS,
    DEFAULT_NOTIFY_PAYMENT_TIME,
    DEFAULT_NOTIFY_QUIET_FROM,
    DEFAULT_NOTIFY_QUIET_TO,
    DEFAULT_PAYMENT_EXCLUDED_CHANNELS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USE_WEBHOOK,
    DOMAIN,
    NOTIFY_TYPES,
)
from .notifications import opt_enabled, opt_quiet, opt_recipients
from . import privacy


_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_NOTIFY_RE = re.compile(r"^notify\.[a-z0-9_]+$")
_ENTITY_RE = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")


# ---------------------------------------------------------------------------
# Berechtigung
# ---------------------------------------------------------------------------
def can_edit(user: Any, entry: ConfigEntry) -> bool:
    """Admins immer; sonst Benutzer mit dem Recht „einstellungen“ (Rolle Verwalter, v1.18.0).

    Ohne Benutzer (interne Aufrufe) gibt es hier bewusst keine Freigabe – die Karte ist immer
    an einen angemeldeten Benutzer gebunden.
    """
    if user is None:
        return False
    return rechte.allowed(user, entry.options, "einstellungen")


# ---------------------------------------------------------------------------
# Lesen: alle Werte flach mit Standardwerten
# ---------------------------------------------------------------------------
def current(entry: ConfigEntry) -> dict[str, Any]:
    """Aktuelle Optionen so aufbereitet, wie die Karte sie anzeigt (fehlende Schlüssel = Standard)."""
    o = entry.options
    commissions = {str(k): float(v) for k, v in (o.get(CONF_COMMISSIONS) or DEFAULT_COMMISSIONS).items()}
    # Die festen Kanäle des Options-Dialogs immer zeigen (gleiche Reihenfolge, fehlende mit Standard)
    for channel in COMMISSION_FIELDS.values():
        commissions.setdefault(channel, DEFAULT_COMMISSIONS[channel])
    values: dict[str, Any] = {
        # Allgemein & Abruf
        CONF_SCAN_INTERVAL: int(o.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        CONF_USE_WEBHOOK: bool(o.get(CONF_USE_WEBHOOK, DEFAULT_USE_WEBHOOK)),
        CONF_DEFAULT_CHECKIN: str(o.get(CONF_DEFAULT_CHECKIN, DEFAULT_CHECKIN))[:5],
        CONF_DEFAULT_CHECKOUT: str(o.get(CONF_DEFAULT_CHECKOUT, DEFAULT_CHECKOUT))[:5],
        CONF_CHECKOUT_BUFFER: int(o.get(CONF_CHECKOUT_BUFFER, DEFAULT_CHECKOUT_BUFFER)),
        CONF_DAYS_BACK: int(o.get(CONF_DAYS_BACK, DEFAULT_DAYS_BACK)),
        CONF_DAYS_AHEAD: int(o.get(CONF_DAYS_AHEAD, DEFAULT_DAYS_AHEAD)),
        CONF_ENRICH_COUNT: int(o.get(CONF_ENRICH_COUNT, DEFAULT_ENRICH_COUNT)),
        CONF_HISTORY_YEARS: int(o.get(CONF_HISTORY_YEARS, DEFAULT_HISTORY_YEARS)),
        CONF_HISTORY_SINCE: o.get(CONF_HISTORY_SINCE) or None,
        CONF_APARTMENT_CODES: {str(k): str(v) for k, v in (o.get(CONF_APARTMENT_CODES) or {}).items()},
        # Provisionen & Kanäle
        CONF_COMMISSIONS: commissions,
        CONF_COMMISSION_OTHER: float(o.get(CONF_COMMISSION_OTHER, DEFAULT_COMMISSION_OTHER)),
        CONF_DIRECT_CHANNELS: list(o.get(CONF_DIRECT_CHANNELS, DEFAULT_DIRECT_CHANNELS)),
        CONF_PAYMENT_EXCLUDED_CHANNELS: list(o.get(CONF_PAYMENT_EXCLUDED_CHANNELS, DEFAULT_PAYMENT_EXCLUDED_CHANNELS)),
        # KI-Assistent (Standardwerte wie im Options-Dialog)
        CONF_AI_ENABLED: bool(o.get(CONF_AI_ENABLED, bool(o.get(CONF_AI_ENTITY)))),
        CONF_ASSISTANT: bool(o.get(CONF_ASSISTANT, True)),
        CONF_AI_ENTITY: o.get(CONF_AI_ENTITY) or None,
        CONF_ASSIST_STATUS: list(o.get(CONF_ASSIST_STATUS) or []),
        CONF_ASSIST_PATH: str(o.get(CONF_ASSIST_PATH, "/lovelace")),
        # Datenschutz für die KI (v1.18.0b6): Stufe + Einzelschalter. Die Einzelschalter zeigen bei einer
        # festen Stufe deren Voreinstellung (zum Vergleich), wirksam werden sie nur bei „individuell“.
        privacy.CONF_AI_PRIVACY: privacy.level(o),
        **({**privacy.resolve(o), **{k: o[k] for k in privacy.FLAGS if k in o}}
           if privacy.level(o) == "individuell" else privacy.resolve(o)),
        privacy.CONF_AI_HOST_NAMES: privacy.host_names(o, entry.title),
        # Benachrichtigungen: Zeiten und Ruhezeit
        CONF_ASSIST_BRIEFING_TIME: str(o.get(CONF_ASSIST_BRIEFING_TIME, "07:30"))[:5],
        CONF_NOTIFY_GAPS_TIME: str(o.get(CONF_NOTIFY_GAPS_TIME, DEFAULT_NOTIFY_GAPS_TIME))[:5],
        CONF_NOTIFY_PAYMENT_TIME: str(o.get(CONF_NOTIFY_PAYMENT_TIME, DEFAULT_NOTIFY_PAYMENT_TIME))[:5],
        CONF_NOTIFY_PAYMENT_DAYS: int(o.get(CONF_NOTIFY_PAYMENT_DAYS, DEFAULT_NOTIFY_PAYMENT_DAYS)),
        CONF_NOTIFY_QUIET: bool(o.get(CONF_NOTIFY_QUIET, False)),
        CONF_NOTIFY_QUIET_FROM: str(o.get(CONF_NOTIFY_QUIET_FROM, DEFAULT_NOTIFY_QUIET_FROM))[:5],
        CONF_NOTIFY_QUIET_TO: str(o.get(CONF_NOTIFY_QUIET_TO, DEFAULT_NOTIFY_QUIET_TO))[:5],
        # v1.18.0: je Push-Art „hält Ruhezeit ein“ (ersetzt den Schalter „Gästenachrichten sofort“)
        **{f"notify_{kind}_quiet": opt_quiet(o, kind) for kind in NOTIFY_TYPES},
        # Wer im Dashboard ändern darf (nur Admins können das selbst ändern)
        CONF_SETTINGS_USERS: list(o.get(CONF_SETTINGS_USERS) or []),
        # Benutzerrollen (v1.18.0): nur Admins ändern; Altwert settings_users → „verwalter“
        CONF_USER_ROLES: {**{u: "verwalter" for u in (o.get(CONF_SETTINGS_USERS) or [])},
                          **{str(k): str(v) for k, v in (o.get(CONF_USER_ROLES) or {}).items()}},
        CONF_DEFAULT_ROLE: str(o.get(CONF_DEFAULT_ROLE, DEFAULT_ROLE)),
        # Kosten & Preise (v1.18.0)
        CONF_COST_CLEANING: float(o.get(CONF_COST_CLEANING, DEFAULT_COST_CLEANING)),
        CONF_COST_LAUNDRY: float(o.get(CONF_COST_LAUNDRY, DEFAULT_COST_LAUNDRY)),
        CONF_COST_HEATING_YEAR: float(o.get(CONF_COST_HEATING_YEAR, DEFAULT_COST_HEATING_YEAR)),
        CONF_COST_HOT_WATER_YEAR: float(o.get(CONF_COST_HOT_WATER_YEAR, DEFAULT_COST_HOT_WATER_YEAR)),
        CONF_COST_REF_YEAR: int(o.get(CONF_COST_REF_YEAR, DEFAULT_COST_REF_YEAR)),
        CONF_COST_WATER_NIGHT: float(o.get(CONF_COST_WATER_NIGHT, DEFAULT_COST_WATER_NIGHT)),
        CONF_COST_POWER_KWH: float(o.get(CONF_COST_POWER_KWH, DEFAULT_COST_POWER_KWH)),
        CONF_COST_GRID_PRICE: float(o.get(CONF_COST_GRID_PRICE, DEFAULT_COST_GRID_PRICE)),
        CONF_COST_PV_VALUE: float(o.get(CONF_COST_PV_VALUE, DEFAULT_COST_PV_VALUE)),
        CONF_COST_GRID_SHARE: [float(x) for x in (o.get(CONF_COST_GRID_SHARE) or DEFAULT_COST_GRID_SHARE)],
        CONF_CHANNEL_MARKUPS: {str(k): float(v) for k, v in (o.get(CONF_CHANNEL_MARKUPS, DEFAULT_CHANNEL_MARKUPS)).items()},
        CONF_GENIUS_DISCOUNT: float(o.get(CONF_GENIUS_DISCOUNT, DEFAULT_GENIUS_DISCOUNT)),
        CONF_GENIUS_SHARE: float(o.get(CONF_GENIUS_SHARE, DEFAULT_GENIUS_SHARE)),
        CONF_TASK_CATEGORIES: list(o.get(CONF_TASK_CATEGORIES, DEFAULT_TASK_CATEGORIES)),
        CONF_LASTMINUTE_DAYS: int(o.get(CONF_LASTMINUTE_DAYS, DEFAULT_LASTMINUTE_DAYS)),
        CONF_LASTMINUTE_MAX_DISCOUNT: float(o.get(CONF_LASTMINUTE_MAX_DISCOUNT, DEFAULT_LASTMINUTE_MAX_DISCOUNT)),
        # v1.18.0: Saisons (Statistik/Finanzen: Zeitraum „Saison“, Gruppierung „Saison“)
        "saisons": season_cfg.from_options(o),
    }
    # Je Push-Art an/aus und Empfänger (gleiche Rückfallregeln wie der Benachrichtigungsdienst)
    for kind in NOTIFY_TYPES:
        values[f"notify_{kind}"] = opt_enabled(o, kind)
        values[f"notify_{kind}_to"] = opt_recipients(o, kind)
    return values


def commission_sources(records: list[dict[str, Any]], today: date) -> dict[str, dict[str, Any]]:
    """Je Kanal: liefert Smoobu eine gültige Provision mit der Buchung? (v1.18.0, Wunsch Betreiber)

    Grundlage: Gästebuchungen mit Preis der letzten 24 Monate (ohne Stornos). „Gültig“ = Smoobu
    liefert `commission-included` > 0 und der Anteil liegt zwischen 1 % und 40 % des Preises –
    darüber ist es eher ein Datenfehler. Status:
    - smoobu: ≥ 80 % der Buchungen mit gültiger Provision → die Option ist nur Rückfall
    - teilweise: einige Buchungen mit, andere ohne → für die ohne gilt die Option
    - option: keine → immer der %-Wert aus den Optionen
    """
    since = date(today.year - 2, today.month, 1).isoformat()
    acc: dict[str, dict[str, Any]] = {}
    for r in records:
        if r["blockiert"] or r["storniert"] or not r["brutto"] or r["anreise"] < since:
            continue
        a = acc.setdefault(r["kanal"], {"buchungen": 0, "smoobu": 0, "ungueltig": 0, "_pct": [], "letzte": None})
        a["buchungen"] += 1
        if r.get("provision_quelle") == "smoobu":
            pct = r["provision"] / r["brutto"] * 100
            if 1 <= pct <= 40:
                a["smoobu"] += 1
                a["_pct"].append(pct)
                a["letzte"] = max(a["letzte"] or "", r["anreise"])
            else:
                a["ungueltig"] += 1
    out = {}
    for ch, a in acc.items():
        share = a["smoobu"] / a["buchungen"]
        status = "smoobu" if share >= 0.8 else "teilweise" if a["smoobu"] else "option"
        out[ch] = {"status": status, "buchungen": a["buchungen"], "mit_provision": a["smoobu"],
                   "ungueltig": a["ungueltig"], "prozent_schnitt": round(sum(a["_pct"]) / len(a["_pct"]), 1) if a["_pct"] else None,
                   "letzte": a["letzte"]}
    return out


def genius_check(records: list[dict[str, Any]], today: date) -> dict[str, Any]:
    """Wie viele Booking.com-Buchungen der letzten 24 Monate kamen von Genius-Gästen? (v1.18.0)

    Booking.com schreibt „booker_is_genius“ in die Notiz, die Smoobu mitliefert. Den Rabatt selbst
    (10/15/20 %) liefert es nicht – der bleibt eine Option.
    """
    since = date(today.year - 2, today.month, 1).isoformat()
    items = [r for r in records if not r["blockiert"] and not r["storniert"] and r["anreise"] >= since
             and (r["kanal"] or "").casefold() == "booking.com"]
    genius = sum(1 for r in items if r.get("genius"))
    return {"buchungen": len(items), "genius": genius,
            "anteil": round(genius / len(items) * 100) if items else None,
            "letzte": max((r["anreise"] for r in items), default=None)}


async def meta(hass: HomeAssistant, entry: ConfigEntry, user: Any) -> dict[str, Any]:
    """Auswahlmöglichkeiten für die Karte: Handys, KI-Entitäten, Kanäle, Wohnungen, Benutzer."""
    phones = sorted(
        f"notify.{svc}" for svc in hass.services.async_services().get("notify", {}) if svc.startswith("mobile_app_")
    )
    ai = [
        {"entity_id": s.entity_id, "name": s.attributes.get("friendly_name") or s.entity_id}
        for s in hass.states.async_all("ai_task")
    ]
    coordinator = getattr(entry, "runtime_data", None)
    data = coordinator.data if coordinator else None
    apartments = []
    auto = all_codes(hass, {entry.entry_id: {}})  # automatische Kürzel (ohne eigene) als Vorschau
    for apt_id, apt in (data.apartments if data else {}).items():
        apartments.append({"id": str(apt_id), "name": apt.get("name") or str(apt_id),
                           "auto": auto.get((entry.entry_id, int(apt_id)), "?")})
    users = []
    if user is not None and user.is_admin:
        users = [
            {"id": u.id, "name": u.name or u.id, "admin": u.is_admin}
            for u in await hass.auth.async_get_users()
            if u.is_active and not u.system_generated
        ]
    # v1.18.0: Kanal-Auswahl (Dropdowns statt Freitext). Smoobu hat keinen Endpunkt für angebundene
    # Kanäle → Buchungen (alle geladenen, inkl. Stornos) + in den Optionen genutzte + Smoobu-Katalog
    o = entry.options
    choices = channel_choices(
        [r for apt_id in (data.apartments if data else {}) for r in coordinator.records(apt_id)],
        configured_channels(o, o.get(CONF_COMMISSIONS) or DEFAULT_COMMISSIONS,
                            o.get(CONF_DIRECT_CHANNELS, DEFAULT_DIRECT_CHANNELS),
                            o.get(CONF_PAYMENT_EXCLUDED_CHANNELS, DEFAULT_PAYMENT_EXCLUDED_CHANNELS),
                            o.get(CONF_CHANNEL_MARKUPS, DEFAULT_CHANNEL_MARKUPS)),
    )
    return {
        "handys": phones,
        "ki_entitaeten": ai,
        # Chips (Direktkanäle, Portal-Zahlung): genutzte Kanäle; Dropdowns zusätzlich der Katalog
        "kanaele": [c["name"] for c in choices["buchungen"]] + choices["eingestellt"],
        "kanal_auswahl": choices,
        "wohnungen": apartments,
        "benutzer": users,
        "feste_provisionen": list(COMMISSION_FIELDS.values()),
        "push_arten": NOTIFY_TYPES,
        "admin": bool(user and user.is_admin),
        # v1.18.0: je Kanal, ob Smoobu eine gültige Provision liefert (Markierung im Reiter Provisionen)
        "genius_check": genius_check(
            [r for apt_id in (data.apartments if data else {}) for r in coordinator.records(apt_id)], date.today()),
        "provision_herkunft": commission_sources(
            [r for apt_id in (data.apartments if data else {}) for r in coordinator.records(apt_id)], date.today()),
        # v1.18.0: Rollen × Rechte und eigene Rolle (Anzeige im Reiter „Benutzer & Rechte“)
        "rollen": rechte.matrix(),
        "zugriff": rechte.describe(user, entry.options),
        # v1.18.0b6: Voreinstellungen der Datenschutz-Stufen (Karte setzt die Einzelschalter beim Wechsel)
        "datenschutz_stufen": privacy.PRESETS,
        # v1.18.0: Saison-Vorschläge aus abgeschlossenen Jahren (RevPAR-Profil je Monat) + Standard
        "saison_erkennung": season_cfg.detect(
            [r for apt_id in (data.apartments if data else {}) for r in coordinator.records(apt_id)], date.today(),
            units=max(len(data.apartments), 1) if data else 1),
        "saison_standard": season_cfg.DEFAULT_SEASONS,
    }


# ---------------------------------------------------------------------------
# Schreiben: prüfen, zusammenführen, speichern
# ---------------------------------------------------------------------------
def _hhmm(value: Any) -> str:
    text = str(value or "")[:5]
    if not _HHMM_RE.match(text):
        raise vol.Invalid("invalid_time")
    return text


def _int(lo: int, hi: int):
    return vol.All(vol.Coerce(int), vol.Range(min=lo, max=hi))


def _pct(value: Any) -> float:
    number = float(str(value).replace(",", "."))
    if not 0 <= number <= 50:
        raise vol.Invalid("invalid_percent")
    return round(number, 2)


def _names(value: Any) -> list[str]:
    """Liste von Kanalnamen: getrimmt, ohne Leere und Doppelte, Reihenfolge bleibt."""
    if not isinstance(value, list):
        raise vol.Invalid("invalid_list")
    out: list[str] = []
    for item in value:
        name = str(item or "").strip()
        if name and name not in out:
            out.append(name)
    return out


def _pattern_list(pattern: re.Pattern):
    def check(value: Any) -> list[str]:
        items = _names(value)
        if any(not pattern.match(i) for i in items):
            raise vol.Invalid("invalid_entity")
        return items
    return check


def _since(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError as err:
        raise vol.Invalid("invalid_date") from err


def _commissions(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out: dict[str, float] = {}
    for name, pct in value.items():
        channel = str(name or "").strip()
        if channel:
            out[channel] = _pct(pct)
    return out


def _num(lo: float, hi: float):
    """Zahl (auch mit Komma) im Bereich lo–hi."""
    def check(value: Any) -> float:
        try:
            number = float(str(value).replace(",", "."))
        except ValueError as err:
            raise vol.Invalid("invalid_number") from err
        if not lo <= number <= hi:
            raise vol.Invalid("invalid_number")
        return round(number, 2)
    return check


def _grid_share(value: Any) -> list[float]:
    try:
        return parse_grid_share(value)
    except (TypeError, ValueError) as err:
        raise vol.Invalid("invalid_grid_share") from err


def _markups(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    try:
        return parse_markups(value)
    except (TypeError, ValueError) as err:
        raise vol.Invalid("invalid_number") from err


def _roles(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out = {}
    for uid, role in value.items():
        if role in (None, ""):
            continue  # leer = Standardrolle
        if role not in rechte.ROLES:
            raise vol.Invalid("invalid_role")
        out[str(uid)] = str(role)
    return out


def _role(value: Any) -> str:
    if value not in rechte.ROLES:
        raise vol.Invalid("invalid_role")
    return str(value)


def _codes(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    return {str(k): str(v or "") for k, v in value.items()}


# Prüfregeln je Feld – Grenzen wie im Options-Dialog
FIELDS: dict[str, Any] = {
    CONF_SCAN_INTERVAL: _int(1, 120),
    CONF_USE_WEBHOOK: bool,
    CONF_DEFAULT_CHECKIN: _hhmm,
    CONF_DEFAULT_CHECKOUT: _hhmm,
    CONF_CHECKOUT_BUFFER: _int(0, 240),
    CONF_DAYS_BACK: _int(0, 365),
    CONF_DAYS_AHEAD: _int(30, 730),
    CONF_ENRICH_COUNT: _int(0, 20),
    CONF_HISTORY_YEARS: _int(1, 5),
    CONF_HISTORY_SINCE: _since,
    CONF_APARTMENT_CODES: _codes,
    CONF_COMMISSIONS: _commissions,
    CONF_COMMISSION_OTHER: _pct,
    CONF_DIRECT_CHANNELS: _names,
    CONF_PAYMENT_EXCLUDED_CHANNELS: _names,
    CONF_AI_ENABLED: bool,
    CONF_ASSISTANT: bool,
    CONF_AI_ENTITY: vol.Any(None, vol.Match(r"^ai_task\.[a-z0-9_]+$")),
    CONF_ASSIST_STATUS: _pattern_list(_ENTITY_RE),
    CONF_ASSIST_PATH: vol.All(str, vol.Length(max=200)),
    privacy.CONF_AI_PRIVACY: vol.In(privacy.PRIVACY_LEVELS),
    privacy.CONF_AI_HISTORY: _int(0, privacy.MAX_HISTORY),
    **{k: bool for k in privacy.FLAGS if k != privacy.CONF_AI_HISTORY},
    privacy.CONF_AI_HOST_NAMES: _names,
    CONF_ASSIST_BRIEFING_TIME: _hhmm,
    CONF_NOTIFY_GAPS_TIME: _hhmm,
    CONF_NOTIFY_PAYMENT_TIME: _hhmm,
    CONF_NOTIFY_PAYMENT_DAYS: _int(1, 60),
    CONF_NOTIFY_QUIET: bool,
    CONF_NOTIFY_QUIET_FROM: _hhmm,
    CONF_NOTIFY_QUIET_TO: _hhmm,
    CONF_SETTINGS_USERS: _names,
    CONF_USER_ROLES: _roles,
    CONF_DEFAULT_ROLE: _role,
    CONF_COST_CLEANING: _num(0, 1000),
    CONF_COST_LAUNDRY: _num(0, 1000),
    CONF_COST_HEATING_YEAR: _num(0, 100000),
    CONF_COST_HOT_WATER_YEAR: _num(0, 100000),
    CONF_COST_REF_YEAR: _int(2015, 2100),
    CONF_COST_WATER_NIGHT: _num(0, 100),
    CONF_COST_POWER_KWH: _num(0, 200),
    CONF_COST_GRID_PRICE: _num(0, 200),
    CONF_COST_PV_VALUE: _num(0, 200),
    CONF_COST_GRID_SHARE: _grid_share,
    CONF_CHANNEL_MARKUPS: _markups,
    CONF_GENIUS_DISCOUNT: _num(0, 50),
    CONF_GENIUS_SHARE: _num(0, 100),
    CONF_TASK_CATEGORIES: vol.All(_names, [vol.In(TASK_CATEGORIES)]),
    CONF_LASTMINUTE_DAYS: _int(1, 14),
    CONF_LASTMINUTE_MAX_DISCOUNT: _num(0, 30),
    "saisons": season_cfg.validate,
    **{f"notify_{kind}": bool for kind in NOTIFY_TYPES},
    **{f"notify_{kind}_to": _pattern_list(_NOTIFY_RE) for kind in NOTIFY_TYPES},
    **{f"notify_{kind}_quiet": bool for kind in NOTIFY_TYPES},
}


def validate(hass: HomeAssistant, entry: ConfigEntry, changes: dict[str, Any], user: Any) -> tuple[dict[str, Any], dict[str, str]]:
    """Geänderte Werte prüfen. Ergebnis: (neue Optionen komplett, Fehler je Feld)."""
    errors: dict[str, str] = {}
    values = current(entry)
    for key, raw in changes.items():
        rule = FIELDS.get(key)
        if rule is None:
            errors[key] = "unknown_field"
            continue
        try:
            values[key] = vol.Schema(rule)(raw)
        except vol.Invalid as err:
            # Eigene Fehlercodes durchreichen, sonst allgemein „ungültig“
            msg = str(err.msg) if getattr(err, "msg", None) else ""
            errors[key] = msg if msg.startswith("invalid_") else "invalid"

    # Wer im Dashboard ändern darf und welche Rolle jemand hat, legen nur Admins fest
    if not (user and user.is_admin):
        before = current(entry)
        for key in (CONF_SETTINGS_USERS, CONF_USER_ROLES, CONF_DEFAULT_ROLE):
            if key in changes and key not in errors and values[key] != before[key]:
                errors[key] = "admin_only"

    # KI erlauben ohne KI-Entität ergibt keinen Sinn (gleiche Regel wie im Options-Dialog)
    if values[CONF_AI_ENABLED] and not values[CONF_AI_ENTITY]:
        errors[CONF_AI_ENTITY] = "ai_entity_required"

    # Wohnungskürzel normalisieren und auf Eindeutigkeit prüfen (auch gegen andere Smoobu-Konten)
    own: dict[str, str] = {}
    for apt_id, raw in values[CONF_APARTMENT_CODES].items():
        code = clean_code(raw)
        if raw.strip() and not code:
            errors[f"{CONF_APARTMENT_CODES}.{apt_id}"] = "invalid_code"
        elif code:
            own[apt_id] = code
    others = {v for (eid, _a), v in all_codes(hass, {entry.entry_id: own}).items() if eid != entry.entry_id}
    seen: set[str] = set()
    for apt_id, code in own.items():
        if code in seen or code in others:
            errors[f"{CONF_APARTMENT_CODES}.{apt_id}"] = "duplicate_code"
        seen.add(code)
    values[CONF_APARTMENT_CODES] = own

    if errors:
        return {}, errors

    merged = {**entry.options, **values}
    # Rollen gespeichert → Altwert settings_users ist darin aufgegangen (sonst zählte er weiter als „verwalter“)
    if CONF_USER_ROLES in changes:
        merged[CONF_SETTINGS_USERS] = []
    # Alte Schalter mitführen (wie der Options-Dialog), damit ein Downgrade dasselbe tut
    merged[CONF_ASSIST_BRIEFING] = merged["notify_briefing"]
    merged[CONF_ASSIST_GAPS] = merged["notify_luecken"]
    merged[CONF_NOTIFY_QUIET_MESSAGES] = not merged["notify_nachricht_quiet"]
    # Leere Werte entfernen statt als None speichern (gleiches Verhalten wie der Options-Dialog)
    for key in (CONF_AI_ENTITY, CONF_HISTORY_SINCE):
        if not merged.get(key):
            merged.pop(key, None)
    return merged, {}


async def save(hass: HomeAssistant, entry: ConfigEntry, options: dict[str, Any]) -> bool:
    """Optionen speichern und den Eintrag selbst neu laden (Antwort erst danach).

    Der Update-Listener der Integration würde im Hintergrund neu laden; dann wüsste die Karte
    nicht, wann neue Daten da sind. Deshalb überspringt er dieses eine Mal (SKIP_RELOAD) und
    das Neuladen passiert hier. Rückgabe False = keine Änderung (dann wird nicht neu geladen).
    """
    skip: set[str] = hass.data.setdefault(f"{DOMAIN}_skip_reload", set())
    skip.add(entry.entry_id)
    if not hass.config_entries.async_update_entry(entry, options=options):
        skip.discard(entry.entry_id)
        return False
    await hass.config_entries.async_reload(entry.entry_id)
    return True


def editable_entries(hass: HomeAssistant, user: Any) -> list[ConfigEntry]:
    return [e for e in hass.config_entries.async_entries(DOMAIN) if can_edit(user, e)]

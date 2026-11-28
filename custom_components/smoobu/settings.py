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
from . import energie
from .energie import (
    CONF_COST_GRID_SHARE_AUTO,
    CONF_COST_GRID_SHARE_ENTITIES,
    CONF_COST_GRID_SHARE_MODE,
    CONF_COST_GRID_SHARE_YEAR,
    DEFAULT_COST_GRID_SHARE_YEAR,
    GRID_SHARE_MODES,
    grid_share_mode,
    CONF_COST_POWER_ENTITIES,
    CONF_COST_POWER_SOURCE,
    CONF_COST_PREHEAT_ENTITIES,
    CONF_COST_PREHEAT_HOURS,
    CONF_COST_PRICE_ENTITY,
    CONF_COST_VACANCY_MODE,
    CONF_COST_HEAT_ENTITIES,
    CONF_COST_HEAT_INCL_HOT_WATER,
    CONF_COST_HEAT_PRICE,
    CONF_COST_HEAT_PRICE_ENTITY,
    CONF_COST_HEAT_SOURCE,
    CONF_COST_WATER_ENTITIES,
    CONF_COST_WATER_PRICE,
    CONF_COST_WATER_PRICE_ENTITY,
    CONF_COST_WATER_SOURCE,
    DEFAULT_COST_POWER_SOURCE,
    DEFAULT_COST_VACANCY_MODE,
    VACANCY_MODES,
    DEFAULT_COST_PREHEAT_HOURS,
    POWER_SOURCES,
)
from . import lexware as lex
from . import ust as ust_mod
from . import lexware_regeln as lex_regeln
from .lexware_zahlung import DEFAULT_PAID_MEANING, PAID_MEANINGS
from .tuercode import (
    CONF_DOOR_CODE_AFTER,
    CONF_DOOR_CODE_BEFORE,
    CONF_DOOR_CODE_DIGITS,
    CONF_DOOR_CODE_ENABLED,
    CONF_DOOR_CODE_NOTE,
    CONF_DOOR_CODE_REMIND,
    CONF_DOOR_LOCKS,
    DEFAULT_AFTER_H,
    DEFAULT_BEFORE_H,
    DEFAULT_DIGITS,
    DEFAULT_REMIND_DAYS,
    LOCK_TYPES,
    MODES,
    STATIC_RE,
)
from .reinigung import (
    CONF_CLEANING_NOTIFY,
    CONF_CLEANING_PHONES,
    CONF_CLEANING_REMIND_TIME,
    CONF_CLEANING_KEEP_YEARS,
    CONF_CLEANING_MINUTES_BY_USER,
    DEFAULT_CLEANING_KEEP_YEARS,
    DEFAULT_CLEANING_REMIND_TIME,
)
from .const import (
    MODULES,
    CONF_TASK_CATEGORIES,
    DEFAULT_TASK_CATEGORIES,
    TASK_CATEGORIES,
    CONF_LASTMINUTE_DAYS,
    CONF_LASTMINUTE_MAX_DISCOUNT,
    DEFAULT_LASTMINUTE_DAYS,
    DEFAULT_LASTMINUTE_MAX_DISCOUNT,
    CONF_CUSTOM_ROLES,
    CONF_FOCUS_ROLES,
    CONF_DEFAULT_ROLE,
    CONF_ROLE_RIGHTS,
    CONF_USER_ROLES,
    DEFAULT_ROLE,
    CONF_CHANNEL_MARKUPS,
    DEFAULT_CHANNEL_MARKUPS,
    CONF_COST_CLEANING,
    CONF_COST_CLEANING_MINUTES,
    DEFAULT_COST_CLEANING_MINUTES,
    CONF_CLEANING_WAGES,
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
from . import zugang


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
        # Rollenkonfigurator (v1.19.0): wirksame Rechte je einstellbarer Standardrolle und eigene Rollen.
        # Gespeichert werden nur Abweichungen vom Standard (siehe validate), angezeigt wird der volle Stand.
        CONF_ROLE_RIGHTS: {rid: sorted(r["rechte"]) for rid, r in rechte.roles(o).items()
                           if r["art"] == "standard" and rid not in rechte.LOCKED_ROLES},
        CONF_CUSTOM_ROLES: {rid: {"name": r["name"], "rechte": sorted(r["rechte"])}
                            for rid, r in rechte.roles(o).items() if r["art"] == "eigen"},
        # Module (v1.19.0b10): abschaltbar, Standard an
        **{f"module_{m}": rechte.module_on(o, m) for m in MODULES},
        # Fokus-Modus (v1.19.0b7): {Rolle: Startseite} – Rollen, die in HA nur Smoobu sehen
        CONF_FOCUS_ROLES: rechte.focus_roles(o),
        # Reinigungsboard (v1.19.0): Pushes, Vorabend-Erinnerung, Handy je HA-Benutzer
        CONF_CLEANING_NOTIFY: bool(o.get(CONF_CLEANING_NOTIFY, True)),
        CONF_CLEANING_REMIND_TIME: str(o.get(CONF_CLEANING_REMIND_TIME, DEFAULT_CLEANING_REMIND_TIME))[:5],
        CONF_CLEANING_PHONES: {str(k): str(v) for k, v in (o.get(CONF_CLEANING_PHONES) or {}).items() if v},
        # v1.19.1b3: Datenschutz – Person in erledigten Reinigungen nach N Jahren anonymisieren
        CONF_CLEANING_KEEP_YEARS: int(o.get(CONF_CLEANING_KEEP_YEARS, DEFAULT_CLEANING_KEEP_YEARS)),
        # v1.20.0b4: Zugangs-Anleitung – Sprache je Benutzer, Ansprechpartner (leer = wer den Text erzeugt)
        zugang.CONF_GUIDE_LANGS: {str(k): str(v) for k, v in (o.get(zugang.CONF_GUIDE_LANGS) or {}).items() if v in zugang.LANGS},
        zugang.CONF_GUIDE_CONTACT_NAME: str(o.get(zugang.CONF_GUIDE_CONTACT_NAME) or ""),
        zugang.CONF_GUIDE_CONTACT_PHONE: str(o.get(zugang.CONF_GUIDE_CONTACT_PHONE) or ""),
        # Kosten & Preise (v1.18.0)
        CONF_COST_CLEANING: float(o.get(CONF_COST_CLEANING, DEFAULT_COST_CLEANING)),  # ab v1.19.0: €/h
        CONF_COST_CLEANING_MINUTES: float(o.get(CONF_COST_CLEANING_MINUTES, DEFAULT_COST_CLEANING_MINUTES)),
        CONF_CLEANING_WAGES: {str(k): float(v) for k, v in (o.get(CONF_CLEANING_WAGES) or {}).items() if v not in (None, "")},
        # v1.19.1b4: Standard-Reinigungszeit je Person (Minuten)
        CONF_CLEANING_MINUTES_BY_USER: {str(k): float(v) for k, v in (o.get(CONF_CLEANING_MINUTES_BY_USER) or {}).items() if v not in (None, "")},  # 0 €/h bleibt sichtbar
        CONF_COST_LAUNDRY: float(o.get(CONF_COST_LAUNDRY, DEFAULT_COST_LAUNDRY)),
        CONF_COST_HEATING_YEAR: float(o.get(CONF_COST_HEATING_YEAR, DEFAULT_COST_HEATING_YEAR)),
        CONF_COST_HOT_WATER_YEAR: float(o.get(CONF_COST_HOT_WATER_YEAR, DEFAULT_COST_HOT_WATER_YEAR)),
        CONF_COST_REF_YEAR: int(o.get(CONF_COST_REF_YEAR, DEFAULT_COST_REF_YEAR)),
        CONF_COST_WATER_NIGHT: float(o.get(CONF_COST_WATER_NIGHT, DEFAULT_COST_WATER_NIGHT)),
        CONF_COST_POWER_KWH: float(o.get(CONF_COST_POWER_KWH, DEFAULT_COST_POWER_KWH)),
        CONF_COST_GRID_PRICE: float(o.get(CONF_COST_GRID_PRICE, DEFAULT_COST_GRID_PRICE)),
        CONF_COST_PV_VALUE: float(o.get(CONF_COST_PV_VALUE, DEFAULT_COST_PV_VALUE)),
        CONF_COST_GRID_SHARE: [float(x) for x in (o.get(CONF_COST_GRID_SHARE) or DEFAULT_COST_GRID_SHARE)],
        # v1.19.0: Stromkosten konstant oder aus Zähler-Entitäten (energie.py)
        CONF_COST_POWER_SOURCE: str(o.get(CONF_COST_POWER_SOURCE, DEFAULT_COST_POWER_SOURCE)),
        CONF_COST_POWER_ENTITIES: {str(k): str(v) for k, v in (o.get(CONF_COST_POWER_ENTITIES) or {}).items() if v},
        CONF_COST_PRICE_ENTITY: o.get(CONF_COST_PRICE_ENTITY) or None,
        CONF_COST_GRID_SHARE_AUTO: bool(o.get(CONF_COST_GRID_SHARE_AUTO, True)),
        # v1.19.1b5: Netzanteil aus Sensor / Energie-Dashboard / Monatswerten / Jahreswert (alter Schalter wird übernommen)
        CONF_COST_GRID_SHARE_MODE: grid_share_mode(o),
        CONF_COST_GRID_SHARE_ENTITIES: {str(k): str(v) for k, v in (o.get(CONF_COST_GRID_SHARE_ENTITIES) or {}).items() if v},
        CONF_COST_GRID_SHARE_YEAR: float(o.get(CONF_COST_GRID_SHARE_YEAR, DEFAULT_COST_GRID_SHARE_YEAR)),
        CONF_COST_PREHEAT_ENTITIES: {str(k): str(v) for k, v in (o.get(CONF_COST_PREHEAT_ENTITIES) or {}).items() if v},
        CONF_COST_PREHEAT_HOURS: float(o.get(CONF_COST_PREHEAT_HOURS, DEFAULT_COST_PREHEAT_HOURS)),
        CONF_COST_VACANCY_MODE: str(o.get(CONF_COST_VACANCY_MODE, DEFAULT_COST_VACANCY_MODE)),
        # v1.19.0: Türcodes (tuercode.py)
        CONF_DOOR_CODE_ENABLED: bool(o.get(CONF_DOOR_CODE_ENABLED, False)),
        CONF_DOOR_CODE_DIGITS: int(o.get(CONF_DOOR_CODE_DIGITS, DEFAULT_DIGITS)),
        CONF_DOOR_CODE_BEFORE: float(o.get(CONF_DOOR_CODE_BEFORE, DEFAULT_BEFORE_H)),
        CONF_DOOR_CODE_AFTER: float(o.get(CONF_DOOR_CODE_AFTER, DEFAULT_AFTER_H)),
        CONF_DOOR_CODE_NOTE: bool(o.get(CONF_DOOR_CODE_NOTE, True)),
        CONF_DOOR_LOCKS: {str(k): dict(v) for k, v in (o.get(CONF_DOOR_LOCKS) or {}).items()},
        CONF_DOOR_CODE_REMIND: int(o.get(CONF_DOOR_CODE_REMIND, DEFAULT_REMIND_DAYS)),  # v1.20.0
        # v1.19.0: Wasser und Heizung ebenfalls konstant (Standard) oder aus Zähler
        CONF_COST_WATER_SOURCE: str(o.get(CONF_COST_WATER_SOURCE, "konstant")),
        CONF_COST_WATER_ENTITIES: {str(k): str(v) for k, v in (o.get(CONF_COST_WATER_ENTITIES) or {}).items() if v},
        CONF_COST_WATER_PRICE: float(o.get(CONF_COST_WATER_PRICE) or 0),
        CONF_COST_WATER_PRICE_ENTITY: o.get(CONF_COST_WATER_PRICE_ENTITY) or None,
        CONF_COST_HEAT_SOURCE: str(o.get(CONF_COST_HEAT_SOURCE, "konstant")),
        CONF_COST_HEAT_ENTITIES: {str(k): str(v) for k, v in (o.get(CONF_COST_HEAT_ENTITIES) or {}).items() if v},
        CONF_COST_HEAT_PRICE: float(o.get(CONF_COST_HEAT_PRICE) or 0),
        CONF_COST_HEAT_PRICE_ENTITY: o.get(CONF_COST_HEAT_PRICE_ENTITY) or None,
        CONF_COST_HEAT_INCL_HOT_WATER: bool(o.get(CONF_COST_HEAT_INCL_HOT_WATER, False)),
        CONF_CHANNEL_MARKUPS: {str(k): float(v) for k, v in (o.get(CONF_CHANNEL_MARKUPS, DEFAULT_CHANNEL_MARKUPS)).items()},
        CONF_GENIUS_DISCOUNT: float(o.get(CONF_GENIUS_DISCOUNT, DEFAULT_GENIUS_DISCOUNT)),
        CONF_GENIUS_SHARE: float(o.get(CONF_GENIUS_SHARE, DEFAULT_GENIUS_SHARE)),
        CONF_TASK_CATEGORIES: list(o.get(CONF_TASK_CATEGORIES, DEFAULT_TASK_CATEGORIES)),
        CONF_LASTMINUTE_DAYS: int(o.get(CONF_LASTMINUTE_DAYS, DEFAULT_LASTMINUTE_DAYS)),
        CONF_LASTMINUTE_MAX_DISCOUNT: float(o.get(CONF_LASTMINUTE_MAX_DISCOUNT, DEFAULT_LASTMINUTE_MAX_DISCOUNT)),
        # v1.18.0: Saisons (Statistik/Finanzen: Zeitraum „Saison“, Gruppierung „Saison“)
        "saisons": season_cfg.from_options(o),
        # v1.20.0 (BETA): Lexware Office (lexware.py). Der API-Key geht nie an die Karte (siehe public()).
        lex.CONF_LEX_ENABLED: bool(lex.opt(o, lex.CONF_LEX_ENABLED)),
        lex.CONF_LEX_KEY: str(o.get(lex.CONF_LEX_KEY) or ""),
        lex.CONF_LEX_MOCK: bool(lex.opt(o, lex.CONF_LEX_MOCK)),
        lex.CONF_LEX_RULES: {g: [dict(r) for r in (o.get(lex.CONF_LEX_RULES) or {}).get(g, [])] for g in lex_regeln.GROUPS},
        lex.CONF_LEX_TAX_COMPANY: str(lex.opt(o, lex.CONF_LEX_TAX_COMPANY)),
        lex.CONF_LEX_TAX_PRIVATE: str(lex.opt(o, lex.CONF_LEX_TAX_PRIVATE)),
        lex.CONF_LEX_INVOICE_DATE: str(lex.opt(o, lex.CONF_LEX_INVOICE_DATE)),
        lex.CONF_LEX_PAYMENT_TEXT: {g: str((o.get(lex.CONF_LEX_PAYMENT_TEXT) or {}).get(g) or lex_regeln.DEFAULT_PAYMENT_TEXT[g])
                                    for g in lex_regeln.GROUPS},
        lex.CONF_LEX_DEPOSIT_PCT: float(lex.opt(o, lex.CONF_LEX_DEPOSIT_PCT)),
        lex.CONF_LEX_DEPOSIT_DAYS: int(lex.opt(o, lex.CONF_LEX_DEPOSIT_DAYS)),
        lex.CONF_LEX_DRAFT_DAYS: int(lex.opt(o, lex.CONF_LEX_DRAFT_DAYS)),
        lex.CONF_LEX_MISSING_DAYS: int(lex.opt(o, lex.CONF_LEX_MISSING_DAYS)),
        lex.CONF_LEX_SEARCH: str(lex.opt(o, lex.CONF_LEX_SEARCH)),
        lex.CONF_LEX_COUNTRY: str(lex.opt(o, lex.CONF_LEX_COUNTRY)),
        lex.CONF_LEX_WEBHOOK: bool(lex.opt(o, lex.CONF_LEX_WEBHOOK)),
        lex.CONF_LEX_SYNC: bool(lex.opt(o, lex.CONF_LEX_SYNC)),
        # v1.20.0: Umsatzsteuer (ust.py) – Grundschalter, „USt-pflichtig seit“, Ansicht, Sätze, Zuordnung, Kosten
        **_ust_values(o),
        # Bedeutung des Smoobu-Hakens „bezahlt“ je Kanalgruppe – gilt auch ohne Lexware
        lex.CONF_PAID_MEANING: {g: str((o.get(lex.CONF_PAID_MEANING) or {}).get(g) or DEFAULT_PAID_MEANING[g]) for g in lex_regeln.GROUPS},
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
        "rollen": rechte.matrix(entry.options),
        # v1.19.0b7: Fokus-Modus – Dashboard der Smoobu-Seiten und auswählbare Startseiten
        "fokus": {"dashboard": rechte.focus_dashboard(entry.options),
                  "seiten": [p for p in rechte.FOCUS_PAGES if p != "smoobu-reinigung" or rechte.module_on(entry.options, "reinigung")]},
        # v1.19.0: Benutzer mit Recht „reinigung“ (Handy je Person im Reiter Benachrichtigungen)
        "reinigungskraefte": await coordinator.cleaning.cleaners() if coordinator and getattr(coordinator, "cleaning", None) else [],
        "zugriff": rechte.describe(user, entry.options),
        # v1.18.0b6: Voreinstellungen der Datenschutz-Stufen (Karte setzt die Einzelschalter beim Wechsel)
        "datenschutz_stufen": privacy.PRESETS,
        # v1.18.0: Saison-Vorschläge aus abgeschlossenen Jahren (RevPAR-Profil je Monat) + Standard
        "saison_erkennung": season_cfg.detect(
            [r for apt_id in (data.apartments if data else {}) for r in coordinator.records(apt_id)], date.today(),
            units=max(len(data.apartments), 1) if data else 1),
        "saison_standard": season_cfg.DEFAULT_SEASONS,
        # v1.19.0: Auswahl für Stromzähler, Strompreis und Vorheizstart + Messergebnis je Wohnung
        **energy_meta(hass, coordinator),
        # v1.20.0: Umsatzsteuer – Preisbestandteile aus den Buchungen (für die Zuordnung)
        "ust": {"bestandteile": ust_mod.elements_seen(coordinator.records_all(), (o.get(ust_mod.CONF_UST_SINCE) or None))
                if coordinator else [],
                "standard_saetze": ust_mod.DEFAULT_RATES, "kostenarten": list(ust_mod.COST_KINDS)},
        # v1.20.0 (BETA): Lexware – Artikel-Auswahl, Vorlage der Regelzeilen, Verbindungsstand
        "lexware": {
            "artikel": coordinator.lexware.articles_choice() if coordinator and getattr(coordinator, "lexware", None) else [],
            "vorlage": lex_regeln.TEMPLATE, "mengen": list(lex_regeln.QUANTITIES), "bedingungen": list(lex_regeln.CONDITIONS),
            "bedeutungen": list(PAID_MEANINGS),
            "status": dict(coordinator.lexware.status) if coordinator and getattr(coordinator, "lexware", None) else {},
            "aktiv": bool(coordinator and getattr(coordinator, "lexware", None) and coordinator.lexware.enabled),
        },
    }


def energy_meta(hass: HomeAssistant, coordinator: Any) -> dict[str, Any]:
    """Entitäten-Vorschläge (Energiezähler, Preise, Zeitstempel) und Messung je Wohnung (letzte 13 Monate).

    Korrektur 21.11.2026 (Wunsch Betreiber, Dropdown statt Datalist): jede Auswahl wird vorgefiltert –
    `passend: True` markiert Entitäten, deren ID, Name oder Bereich zur Ferienwohnung passt (Wohnungsname,
    Kürzel, „fewo“/„ferienwohnung“) bzw. zum Zweck (z. B. „vorheiz“, „strompreis“). Die Karte zeigt diese
    zuerst als Gruppe „Vorschläge“, den Rest darunter.
    """
    from homeassistant.helpers import area_registry as ar, entity_registry as er

    ents, areas = er.async_get(hass), ar.async_get(hass)
    apts = coordinator.data.apartments if coordinator and coordinator.data else {}
    words = {"fewo", "ferienwohnung", "ferienhaus", "apartment"}
    for apt_id, apt in (apts or {}).items():
        name = str(getattr(apt, "name", None) or (apt.get("name") if isinstance(apt, dict) else "") or "")
        # zu allgemeine Wörter („Haus“ träfe z. B. jeden Hausverbrauch) nicht als Treffer werten
        words |= {w for w in re.split(r"[^0-9a-zäöüß]+", name.casefold()) if len(w) >= 4} - {"haus", "house", "wohnung", "home", "zimmer"}
    words |= {str(c).casefold() for c in (coordinator.config_entry.options.get("apartment_codes") or {}).values() if len(str(c)) >= 3} if coordinator else set()

    def area_name(entity_id: str) -> str:
        entry = ents.async_get(entity_id)
        area_id = entry.area_id if entry else None
        if not area_id and entry and entry.device_id:
            from homeassistant.helpers import device_registry as dr

            dev = dr.async_get(hass).async_get(entry.device_id)
            area_id = dev.area_id if dev else None
        area = areas.async_get_area(area_id) if area_id else None
        return area.name if area else ""

    def item(st, extra: tuple[str, ...] = ()):
        name = st.attributes.get("friendly_name") or st.entity_id
        hay = f"{st.entity_id} {name} {area_name(st.entity_id)}".casefold()
        return {"entity_id": st.entity_id, "name": name, "unit": st.attributes.get("unit_of_measurement"),
                "passend": any(w in hay for w in words) or any(w in hay for w in extra)}
    states = hass.states.async_all(["sensor", "input_number", "number"])
    meters = [item(st) for st in states if st.domain == "sensor" and st.attributes.get("device_class") == "energy"
              and st.attributes.get("state_class") in ("total", "total_increasing")]
    prices = [item(st, ("strompreis", "electricity_price", "arbeitspreis")) for st in states
              if "/kwh" in (u := str(st.attributes.get("unit_of_measurement") or "").casefold()) and any(c in u for c in ("€", "eur", "ct"))]
    stamps = [item(st, ("vorheiz", "preheat")) for st in states if st.domain == "sensor" and st.attributes.get("device_class") == "timestamp"]
    data = coordinator.data if coordinator else None
    today = date.today()
    def summary(res: dict[str, Any]) -> dict[str, Any]:
        months = sorted(res.get("monate", {}).items())[-13:]
        return {
            "entitaet": res.get("entitaet"), "von": res.get("von"), "bis": res.get("bis"), "fehler": res.get("fehler"),
            "netzanteil_gemessen": res.get("netzanteil_gemessen"), "preis_entitaet": res.get("preis_entitaet"),
            # v1.19.1b5: Quelle des Netzanteils (sensor/energie_dashboard/monatswerte/jahreswert) und Sensor
            "netzanteil_modus": res.get("netzanteil_modus"), "netzanteil_entitaet": res.get("netzanteil_entitaet"),
            "leerstand_modus": res.get("leerstand_modus"), "einheit": res.get("einheit") or "kWh",
            "monate": [{"monat": k, **v} for k, v in months],
            "buchungen_gemessen": len(res.get("buchungen", {})),
            "kwh_je_nacht": energie.average_kwh_per_night(res, today),
        }
    measured: dict[str, dict[str, Any]] = {"strom": {}, "wasser": {}, "heizung": {}}
    for apt, kinds in ((data.energy if data else {}) or {}).items():
        for kind, res in kinds.items():
            measured.setdefault(kind, {})[str(apt)] = summary(res)
    volumes = [item(st) for st in states if st.domain == "sensor" and st.attributes.get("device_class") in ("water", "gas", "volume", "volume_storage")
               and st.attributes.get("state_class") in ("total", "total_increasing")]
    unit_prices = [item(st) for st in states if "/" in str(st.attributes.get("unit_of_measurement") or "")
                   and any(u in str(st.attributes.get("unit_of_measurement")).casefold() for u in ("€", "eur", "ct"))]
    key = lambda x: (not x["passend"], x["name"].casefold())  # noqa: E731  passende zuerst
    locks = [item(s) for s in hass.states.async_all("lock")]
    scripts = [item(s) for s in hass.states.async_all("script")]
    return {"schloesser": sorted(locks, key=key), "skripte": sorted(scripts, key=key),
            "energie_zaehler": sorted(meters, key=key), "energie_preise": sorted(prices, key=key),
            "energie_zeitstempel": sorted(stamps, key=key), "energie_messung": measured["strom"],
            "messung_wasser": measured["wasser"], "messung_heizung": measured["heizung"],
            # Wasser: Volumen-Zähler; Heizung: Wärme-/Energiezähler oder Gas/Öl (Volumen)
            "zaehler_wasser": sorted([v for v in volumes if v["entity_id"]], key=key),
            "zaehler_heizung": sorted(meters + volumes, key=key), "preise_einheit": sorted(unit_prices, key=key)}


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


def _role_id(value: Any) -> str:
    """Standardrolle oder eigene Rolle („eigen_…“); ob die eigene Rolle existiert, prüft validate()."""
    value = str(value or "")
    if value in rechte.ROLES or re.fullmatch(rf"{rechte.CUSTOM_PREFIX}[a-z0-9]{{1,16}}", value):
        return value
    raise vol.Invalid("invalid_role")


def _roles(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out = {}
    for uid, role in value.items():
        if role in (None, ""):
            continue  # leer = Standardrolle
        out[str(uid)] = _role_id(role)
    return out


def _role(value: Any) -> str:
    return _role_id(value)


def _rights_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)) or any(r not in rechte.RIGHTS for r in value):
        raise vol.Invalid("invalid_right")
    return sorted(set(value))


def _role_rights(value: Any) -> dict[str, list[str]]:
    """{Standardrolle: [Rechte]}; „Kein Zugriff“ ist fest und wird ignoriert."""
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out = {}
    for rid, rights in value.items():
        if rid not in rechte.ROLES:
            raise vol.Invalid("invalid_role")
        if rid in rechte.LOCKED_ROLES:
            continue
        out[str(rid)] = sorted(rechte._clean(_rights_list(rights)))
    return out


def _focus(value: Any) -> dict[str, str]:
    """{Rolle: Startseite}: Startseite leer (automatisch) oder ein Dashboard-Pfad „/dashboard/ansicht“ (v1.19.0b7)."""
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out = {}
    for role, start in value.items():
        rid = _role_id(role)
        if rid in rechte.LOCKED_ROLES:
            raise vol.Invalid("invalid_role")
        start = str(start or "").strip()
        if start and not re.fullmatch(r"/[a-z0-9_\-]+/[a-z0-9_\-]+", start):
            raise vol.Invalid("invalid_focus_path")
        out[rid] = start
    return out


def _custom_roles(value: Any) -> dict[str, dict[str, Any]]:
    """{"eigen_…": {name, rechte}}: Name 1–30 Zeichen, eindeutig (auch ggü. Standardrollen), max. 10."""
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    if len(value) > rechte.MAX_CUSTOM_ROLES:
        raise vol.Invalid("invalid_role_count")
    out: dict[str, dict[str, Any]] = {}
    seen = {n.casefold() for n, _r in rechte.ROLES.values()}
    for rid, cfg in value.items():
        rid = _role_id(rid)
        if rid in rechte.ROLES or not isinstance(cfg, dict):
            raise vol.Invalid("invalid_role")
        name = str(cfg.get("name") or "").strip()
        if not name or len(name) > rechte.MAX_ROLE_NAME:
            raise vol.Invalid("invalid_role_name")
        if name.casefold() in seen:
            raise vol.Invalid("duplicate_role_name")
        seen.add(name.casefold())
        out[rid] = {"name": name, "rechte": sorted(rechte._clean(_rights_list(cfg.get("rechte") or [])))}
    return out


def _entity_map(value: Any) -> dict[str, str]:
    """{Wohnungs-ID: sensor.…} – leere Einträge fallen weg (v1.19.0, Strom je Wohnung)."""
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out = {}
    for apt, ent in value.items():
        if ent in (None, ""):
            continue
        if not re.fullmatch(r"sensor\.[a-z0-9_]+", str(ent)):
            raise vol.Invalid("invalid_entity")
        out[str(apt)] = str(ent)
    return out


def _wages(value: Any) -> dict[str, float]:
    """{HA-Benutzer-ID: €/h}; leer = Standard-Stundenlohn (v1.19.0)."""
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out = {}
    for uid, wage in value.items():
        if wage in (None, ""):
            continue
        try:
            w = float(wage)
        except (TypeError, ValueError) as err:
            raise vol.Invalid("invalid_number") from err
        if not 0 <= w <= 500:
            raise vol.Invalid("invalid_number")
        out[str(uid)] = round(w, 2)
    return out


def _user_minutes(value: Any) -> dict[str, float]:
    """v1.19.1b4: {HA-Benutzer-ID: Minuten 1–600}; leer = allgemeine Standard-Reinigungszeit."""
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out = {}
    for uid, mins in value.items():
        if mins in (None, ""):
            continue
        try:
            m = float(mins)
        except (TypeError, ValueError) as err:
            raise vol.Invalid("invalid_number") from err
        if not 1 <= m <= 600:
            raise vol.Invalid("invalid_number")
        out[str(uid)] = round(m)
    return out


def _lex_rules(value: Any) -> dict[str, list[dict[str, Any]]]:
    """v1.20.0: Regelzeilen je Kanalgruppe (Lexware). Nur bekannte Schlüssel, höchstens 30 Zeilen je Gruppe."""
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_rules")
    out: dict[str, list[dict[str, Any]]] = {}
    for group in lex_regeln.GROUPS:
        rows = value.get(group) or []
        if not isinstance(rows, list) or len(rows) > 30:
            raise vol.Invalid("invalid_rules")
        clean = []
        for r in rows:
            if not isinstance(r, dict):
                raise vol.Invalid("invalid_rules")
            row = {k: r[k] for k in ("artikel", "hinweis", "menge", "ab", "max", "anzahl", "bedingung", "wert", "preis") if r.get(k) not in (None, "")}
            row.setdefault("menge", "pauschal")
            row.setdefault("preis", "artikel")
            clean.append(row)
        errs = lex_regeln.validate_rules(clean)
        if errs:
            raise vol.Invalid("invalid_" + errs[0].removeprefix("invalid_"))
        out[group] = clean
    return out


def _lex_texts(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise vol.Invalid("invalid")
    return {g: str(value.get(g) or "")[:500] for g in lex_regeln.GROUPS}


def _paid_meaning(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or any(value.get(g) not in PAID_MEANINGS for g in lex_regeln.GROUPS):
        raise vol.Invalid("invalid")
    return {g: value[g] for g in lex_regeln.GROUPS}


def _ust_values(o: Any) -> dict[str, Any]:
    cfg = ust_mod.opts_of(dict(o))
    return {
        ust_mod.CONF_UST_MODE: cfg["modus"],
        ust_mod.CONF_UST_SINCE: cfg["seit"].isoformat() if cfg["seit"] else None,
        ust_mod.CONF_UST_VIEW: cfg["ansicht"],
        ust_mod.CONF_UST_RATES: [{"ab": str(r.get("ab"))[:10], "ermaessigt": float(r.get("ermaessigt") or 0), "regel": float(r.get("regel") or 0)}
                                 for r in cfg["saetze"]],
        ust_mod.CONF_UST_MAP: dict(cfg["zuordnung"]),
        ust_mod.CONF_UST_PORTAL: cfg["portal"],
        ust_mod.CONF_UST_DEFAULT: cfg["standard"],
        ust_mod.CONF_UST_COSTS: dict(cfg["kosten"]),
        ust_mod.CONF_UST_LEXWARE: cfg["lexware"],
    }


def _ust_rates(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not 1 <= len(value) <= 20:
        raise vol.Invalid("invalid_ust_rates")
    out = []
    for r in value:
        try:
            ab = date.fromisoformat(str(r.get("ab"))[:10]).isoformat()
            e, g = float(r.get("ermaessigt")), float(r.get("regel"))
        except (TypeError, ValueError, AttributeError) as err:
            raise vol.Invalid("invalid_ust_rates") from err
        if not (0 <= e <= 50 and 0 <= g <= 50):
            raise vol.Invalid("invalid_ust_rates")
        out.append({"ab": ab, "ermaessigt": e, "regel": g})
    return sorted(out, key=lambda x: x["ab"])


def _ust_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or len(value) > 100 or any(v not in ust_mod.KINDS for v in value.values()):
        raise vol.Invalid("invalid")
    return {str(k)[:120]: v for k, v in value.items()}


def _ust_costs(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or any(k not in ust_mod.COST_KINDS or v not in ust_mod.KINDS for k, v in value.items()):
        raise vol.Invalid("invalid")
    return dict(value)


def public(values: dict[str, Any]) -> dict[str, Any]:
    """Werte für die Karte: API-Key nie im Klartext, nur ob einer gespeichert ist (v1.20.0)."""
    out = dict(values)
    out["lexware_api_key_gesetzt"] = bool(out.get(lex.CONF_LEX_KEY))
    out[lex.CONF_LEX_KEY] = ""
    return out


def _locks(value: Any) -> dict[str, dict[str, Any]]:
    """{Wohnungs-ID: {typ, entitaet, slot_von, slot_bis, modus, code}} – Schloss-Adapter und Code-Modus
    für Türcodes (v1.19.0; Modus „statisch“ z. B. für einen Schlüsseltresor ab v1.19.0b2)."""
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out = {}
    for apt, cfg in value.items():
        if not isinstance(cfg, dict) or cfg.get("typ", "kein") not in LOCK_TYPES or cfg.get("modus", "zufall") not in MODES:
            raise vol.Invalid("invalid_lock")
        typ = cfg.get("typ", "kein")
        # Modus: „zufall“ wird nicht gespeichert (Standard); „statisch“ braucht einen gültigen Code
        mode = {}
        if cfg.get("modus") == "statisch":
            code = str(cfg.get("code") or "").strip()
            if not STATIC_RE.fullmatch(code):
                raise vol.Invalid("invalid_static_code")
            mode = {"modus": "statisch", "code": code, **_static_validity(cfg, code)}
        if typ == "kein":
            out[str(apt)] = {"typ": "kein", **mode}
            continue
        ent = str(cfg.get("entitaet") or "").strip()
        pattern = {"skript": r"script\.[a-z0-9_]+", "z2m": r"[^\s#+]{1,120}"}.get(typ, r"lock\.[a-z0-9_]+")
        if not re.fullmatch(pattern, ent):
            raise vol.Invalid("invalid_lock_entity")
        try:
            lo, hi = int(cfg.get("slot_von") or 1), int(cfg.get("slot_bis") or cfg.get("slot_von") or 1)
        except (TypeError, ValueError) as err:
            raise vol.Invalid("invalid_lock_slot") from err
        if not 1 <= lo <= hi <= 250:
            raise vol.Invalid("invalid_lock_slot")
        out[str(apt)] = {"typ": typ, "entitaet": ent, "slot_von": lo, "slot_bis": hi, **mode}
    return out


def _day(value: Any) -> str | None:
    """Datum JJJJ-MM-TT oder leer."""
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError as err:
        raise vol.Invalid("invalid_static_dates") from err


def _static_validity(cfg: dict[str, Any], code: str) -> dict[str, Any]:
    """v1.20.0: Gültigkeit des statischen Codes (ganze Tage) und nächster Code mit eigenem Zeitraum.

    Regeln: bis ≥ ab; nächster Code braucht „ab“; er beginnt nach dem aktuellen (nach „ab“ und nach „bis“,
    falls gesetzt), sein „bis“ ≥ sein „ab“. Leere Felder werden nicht gespeichert."""
    ab, bis = _day(cfg.get("ab")), _day(cfg.get("bis"))
    if ab and bis and bis < ab:
        raise vol.Invalid("invalid_static_dates")
    out: dict[str, Any] = {k: v for k, v in (("ab", ab), ("bis", bis)) if v}
    nxt = str(cfg.get("naechster_code") or "").strip()
    if not nxt:
        return out
    if not STATIC_RE.fullmatch(nxt):
        raise vol.Invalid("invalid_static_code")
    nab, nbis = _day(cfg.get("naechster_ab")), _day(cfg.get("naechster_bis"))
    if not nab or (ab and nab <= ab) or (bis and nab <= bis) or (nbis and nbis < nab):
        raise vol.Invalid("invalid_static_dates")
    out.update({"naechster_code": nxt, "naechster_ab": nab})
    if nbis:
        out["naechster_bis"] = nbis
    return out


def _phones(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out = {}
    for uid, svc in value.items():
        if svc in (None, ""):
            continue
        if not _NOTIFY_RE.fullmatch(str(svc)):
            raise vol.Invalid("invalid_entity")
        out[str(uid)] = str(svc)
    return out


def _guide_langs(value: Any) -> dict[str, str]:
    """v1.20.0b4: {Benutzer-ID: Sprache} der Zugangs-Anleitung; leer = Deutsch (wird nicht gespeichert)."""
    if not isinstance(value, dict):
        raise vol.Invalid("invalid_list")
    out = {}
    for uid, lang in value.items():
        if lang in (None, ""):
            continue
        if lang not in zugang.LANGS:
            raise vol.Invalid("invalid_lang")
        out[str(uid)] = str(lang)
    return out


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
    CONF_ROLE_RIGHTS: _role_rights,
    CONF_CUSTOM_ROLES: _custom_roles,
    CONF_FOCUS_ROLES: _focus,
    **{f"module_{m}": bool for m in MODULES},
    CONF_CLEANING_NOTIFY: bool,
    CONF_CLEANING_REMIND_TIME: _hhmm,
    CONF_CLEANING_PHONES: _phones,
    CONF_CLEANING_KEEP_YEARS: _int(1, 30),
    zugang.CONF_GUIDE_LANGS: _guide_langs,
    zugang.CONF_GUIDE_CONTACT_NAME: vol.All(vol.Coerce(str), vol.Strip, vol.Length(max=60)),
    zugang.CONF_GUIDE_CONTACT_PHONE: vol.All(vol.Coerce(str), vol.Strip, vol.Length(max=40),
                                             vol.Match(r"^[0-9+()/ .\-]*$", msg="invalid_phone")),
    CONF_COST_CLEANING: _num(0, 1000),
    CONF_COST_CLEANING_MINUTES: _num(0, 600),
    CONF_CLEANING_WAGES: _wages,
    CONF_CLEANING_MINUTES_BY_USER: _user_minutes,
    CONF_COST_LAUNDRY: _num(0, 1000),
    CONF_COST_HEATING_YEAR: _num(0, 100000),
    CONF_COST_HOT_WATER_YEAR: _num(0, 100000),
    CONF_COST_REF_YEAR: _int(2015, 2100),
    CONF_COST_WATER_NIGHT: _num(0, 100),
    CONF_COST_POWER_KWH: _num(0, 200),
    CONF_COST_GRID_PRICE: _num(0, 200),
    CONF_COST_PV_VALUE: _num(0, 200),
    CONF_COST_GRID_SHARE: _grid_share,
    CONF_COST_POWER_SOURCE: vol.In(POWER_SOURCES),
    CONF_COST_POWER_ENTITIES: _entity_map,
    CONF_COST_PRICE_ENTITY: vol.Any(None, "", vol.Match(r"^(sensor|input_number|number)\.[a-z0-9_]+$")),
    CONF_COST_GRID_SHARE_AUTO: bool,
    CONF_COST_GRID_SHARE_MODE: vol.In(GRID_SHARE_MODES),
    CONF_COST_GRID_SHARE_ENTITIES: _entity_map,
    CONF_COST_GRID_SHARE_YEAR: _num(0, 100),
    CONF_COST_PREHEAT_ENTITIES: _entity_map,
    CONF_COST_PREHEAT_HOURS: _num(0, 24),
    CONF_COST_VACANCY_MODE: vol.In(VACANCY_MODES),
    CONF_DOOR_CODE_ENABLED: bool,
    CONF_DOOR_CODE_DIGITS: _int(4, 10),
    CONF_DOOR_CODE_BEFORE: _num(0, 48),
    CONF_DOOR_CODE_AFTER: _num(0, 48),
    CONF_DOOR_CODE_NOTE: bool,
    CONF_DOOR_LOCKS: _locks,
    CONF_DOOR_CODE_REMIND: _int(0, 90),  # v1.20.0: Erinnerung vor Ablauf des statischen Codes (0 = aus)
    CONF_COST_WATER_SOURCE: vol.In(POWER_SOURCES),
    CONF_COST_WATER_ENTITIES: _entity_map,
    CONF_COST_WATER_PRICE: _num(0, 100),
    CONF_COST_WATER_PRICE_ENTITY: vol.Any(None, "", vol.Match(r"^(sensor|input_number|number)\.[a-z0-9_]+$")),
    CONF_COST_HEAT_SOURCE: vol.In(POWER_SOURCES),
    CONF_COST_HEAT_ENTITIES: _entity_map,
    CONF_COST_HEAT_PRICE: _num(0, 100),
    CONF_COST_HEAT_PRICE_ENTITY: vol.Any(None, "", vol.Match(r"^(sensor|input_number|number)\.[a-z0-9_]+$")),
    CONF_COST_HEAT_INCL_HOT_WATER: bool,
    CONF_CHANNEL_MARKUPS: _markups,
    CONF_GENIUS_DISCOUNT: _num(0, 50),
    CONF_GENIUS_SHARE: _num(0, 100),
    CONF_TASK_CATEGORIES: vol.All(_names, [vol.In(TASK_CATEGORIES)]),
    CONF_LASTMINUTE_DAYS: _int(1, 14),
    CONF_LASTMINUTE_MAX_DISCOUNT: _num(0, 30),
    "saisons": season_cfg.validate,
    lex.CONF_LEX_ENABLED: bool,
    lex.CONF_LEX_KEY: vol.All(str, vol.Length(max=200)),
    "lexware_api_key_loeschen": bool,
    lex.CONF_LEX_MOCK: bool,
    lex.CONF_LEX_RULES: _lex_rules,
    lex.CONF_LEX_TAX_COMPANY: vol.In(lex_regeln.TAX_TYPES),
    lex.CONF_LEX_TAX_PRIVATE: vol.In(lex_regeln.TAX_TYPES),
    lex.CONF_LEX_INVOICE_DATE: vol.In(lex_regeln.INVOICE_DATES),
    lex.CONF_LEX_PAYMENT_TEXT: _lex_texts,
    lex.CONF_LEX_DEPOSIT_PCT: _num(0, 100),
    lex.CONF_LEX_DEPOSIT_DAYS: _int(1, 60),
    lex.CONF_LEX_DRAFT_DAYS: _int(0, 30),
    lex.CONF_LEX_MISSING_DAYS: _int(0, 365),
    lex.CONF_LEX_SEARCH: vol.In(("name", "email", "beide")),
    lex.CONF_LEX_COUNTRY: vol.Match(r"^[A-Z]{2}$"),
    lex.CONF_LEX_WEBHOOK: bool,
    lex.CONF_LEX_SYNC: bool,
    lex.CONF_PAID_MEANING: _paid_meaning,
    ust_mod.CONF_UST_MODE: vol.In(ust_mod.MODES),
    ust_mod.CONF_UST_SINCE: vol.Any(None, "", vol.All(str, vol.Match(r"^\d{4}-\d{2}-\d{2}$", msg="invalid_date"))),
    ust_mod.CONF_UST_VIEW: vol.In(ust_mod.VIEWS),
    ust_mod.CONF_UST_RATES: _ust_rates,
    ust_mod.CONF_UST_MAP: _ust_map,
    ust_mod.CONF_UST_PORTAL: vol.In(ust_mod.KINDS),
    ust_mod.CONF_UST_DEFAULT: vol.In(ust_mod.KINDS),
    ust_mod.CONF_UST_COSTS: _ust_costs,
    ust_mod.CONF_UST_LEXWARE: bool,
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
            errors[key] = msg if msg.startswith(("invalid_", "duplicate_")) else "invalid"

    # v1.20.0: leerer API-Key aus der Karte = bisherigen behalten; entfernen nur über „lexware_api_key_loeschen“
    if lex.CONF_LEX_KEY in changes and not str(changes.get(lex.CONF_LEX_KEY) or "").strip():
        values[lex.CONF_LEX_KEY] = current(entry)[lex.CONF_LEX_KEY]
    if values.pop("lexware_api_key_loeschen", False):
        values[lex.CONF_LEX_KEY] = ""
    # v1.20.0b3 (Wunsch Betreiber 28.11.2026): Lexware ist ein Modul unter „Allgemein“ – einschalten geht auch ohne
    # API-Key (Reiter „Lexware“ erscheint, dort Key oder Testmodus eintragen); ohne beides bleibt es inaktiv
    # (LexwareModule.enabled), der Reiter zeigt „API-Key fehlt“.

    # Wer im Dashboard ändern darf und welche Rolle jemand hat, legen nur Admins fest
    if not (user and user.is_admin):
        before = current(entry)
        for key in (CONF_SETTINGS_USERS, CONF_USER_ROLES, CONF_DEFAULT_ROLE, CONF_ROLE_RIGHTS, CONF_CUSTOM_ROLES,
                    CONF_FOCUS_ROLES):  # v1.19.0b7: Fokus-Modus ebenfalls nur Admins
            if key in changes and key not in errors and values[key] != before[key]:
                errors[key] = "admin_only"

    # v1.19.0: Rollen müssen existieren. Gelöschte eigene Rolle: Benutzer damit bekommen die Standardrolle;
    # ist sie selbst die Standardrolle, wird das abgelehnt (sonst fiele jeder still auf „Betrieb“ zurück).
    known = set(rechte.ROLES) | set(values[CONF_CUSTOM_ROLES])
    if CONF_FOCUS_ROLES not in errors:  # Fokus für gelöschte eigene Rollen stillschweigend entfernen
        values[CONF_FOCUS_ROLES] = {r: p for r, p in values[CONF_FOCUS_ROLES].items() if r in known}
    if CONF_DEFAULT_ROLE not in errors and values[CONF_DEFAULT_ROLE] not in known:
        errors[CONF_DEFAULT_ROLE] = "role_is_default" if CONF_CUSTOM_ROLES in changes else "invalid_role"
    if CONF_USER_ROLES not in errors:
        unknown = {u for u, r in values[CONF_USER_ROLES].items() if r not in known}
        if unknown and CONF_USER_ROLES in changes and CONF_CUSTOM_ROLES not in changes:
            errors[CONF_USER_ROLES] = "invalid_role"
        values[CONF_USER_ROLES] = {u: r for u, r in values[CONF_USER_ROLES].items() if r in known}

    # v1.19.0: Modus „zaehler“ braucht mindestens einen Zähler
    if values[CONF_COST_POWER_SOURCE] == "zaehler" and not values[CONF_COST_POWER_ENTITIES] and CONF_COST_POWER_ENTITIES not in errors:
        errors[CONF_COST_POWER_ENTITIES] = "power_entity_required"
    # v1.19.1b5: Netzanteil aus Sensor braucht je gemessener Wohnung einen Netz-Sensor
    if (values[CONF_COST_GRID_SHARE_MODE] == "sensor" and values[CONF_COST_POWER_SOURCE] == "zaehler"
            and CONF_COST_GRID_SHARE_ENTITIES not in errors
            and any(apt not in values[CONF_COST_GRID_SHARE_ENTITIES] for apt in values[CONF_COST_POWER_ENTITIES])):
        errors[CONF_COST_GRID_SHARE_ENTITIES] = "grid_share_entity_required"
    # Wasser/Heizung aus Zähler: Zähler und ein Preis (fest oder Entität) nötig
    for src, ents, price, pent in ((CONF_COST_WATER_SOURCE, CONF_COST_WATER_ENTITIES, CONF_COST_WATER_PRICE, CONF_COST_WATER_PRICE_ENTITY),
                                   (CONF_COST_HEAT_SOURCE, CONF_COST_HEAT_ENTITIES, CONF_COST_HEAT_PRICE, CONF_COST_HEAT_PRICE_ENTITY)):
        if values[src] == "zaehler":
            if not values[ents] and ents not in errors:
                errors[ents] = "meter_entity_required"
            if not values[price] and not values[pent] and price not in errors:
                errors[price] = "price_required"

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
    # v1.19.0: nur Abweichungen vom Standard speichern (nicht angepasste Rollen erhalten so neue Rechte
    # späterer Versionen); leere Optionen ganz entfernen
    overrides = {rid: r for rid, r in values[CONF_ROLE_RIGHTS].items()
                 if rid in rechte.ROLES and frozenset(r) != rechte._clean(rechte.ROLES[rid][1])}
    for key, val in ((CONF_ROLE_RIGHTS, overrides), (CONF_CUSTOM_ROLES, values[CONF_CUSTOM_ROLES]),
                     (CONF_CLEANING_PHONES, values[CONF_CLEANING_PHONES]),
                     (CONF_CLEANING_WAGES, values[CONF_CLEANING_WAGES]),
                     (CONF_COST_POWER_ENTITIES, values[CONF_COST_POWER_ENTITIES]),
                     (CONF_COST_PREHEAT_ENTITIES, values[CONF_COST_PREHEAT_ENTITIES]),
                     (CONF_COST_PRICE_ENTITY, values[CONF_COST_PRICE_ENTITY]),
                     (CONF_COST_WATER_ENTITIES, values[CONF_COST_WATER_ENTITIES]),
                     (CONF_COST_WATER_PRICE_ENTITY, values[CONF_COST_WATER_PRICE_ENTITY]),
                     (CONF_COST_HEAT_ENTITIES, values[CONF_COST_HEAT_ENTITIES]),
                     (CONF_COST_HEAT_PRICE_ENTITY, values[CONF_COST_HEAT_PRICE_ENTITY])):
        if val:
            merged[key] = val
        else:
            merged.pop(key, None)
    # Rollen gespeichert → Altwert settings_users ist darin aufgegangen (sonst zählte er weiter als „verwalter“)
    if CONF_USER_ROLES in changes:
        merged[CONF_SETTINGS_USERS] = []
    # v1.18.0: Aufgaben-Kategorien bewusst gespeichert → neue Kategorie „einrichtung“ nicht mehr automatisch ergänzen
    if CONF_TASK_CATEGORIES in changes:
        merged["task_categories_rev"] = 3  # v1.19.0: 3 = kennt „reinigung“
    # Alte Schalter mitführen (wie der Options-Dialog), damit ein Downgrade dasselbe tut
    merged[CONF_ASSIST_BRIEFING] = merged["notify_briefing"]
    merged[CONF_ASSIST_GAPS] = merged["notify_luecken"]
    merged[CONF_NOTIFY_QUIET_MESSAGES] = not merged["notify_nachricht_quiet"]
    # Leere Werte entfernen statt als None speichern (gleiches Verhalten wie der Options-Dialog)
    # v1.20.0: Ansicht nur speichern, wenn bewusst gewählt – sonst folgt sie dem Modus (Regelbesteuerung → ohne USt)
    if ust_mod.CONF_UST_VIEW not in changes and ust_mod.CONF_UST_VIEW not in entry.options:
        merged.pop(ust_mod.CONF_UST_VIEW, None)
    for key in (CONF_AI_ENTITY, CONF_HISTORY_SINCE, lex.CONF_LEX_KEY, ust_mod.CONF_UST_SINCE):
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

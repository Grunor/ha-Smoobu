"""Konstanten der Smoobu-Integration.

Zentrale Stelle für Domain, Konfigurationsschlüssel und Standardwerte,
damit alle Module dieselben Namen verwenden.
"""

from __future__ import annotations

from datetime import time

DOMAIN = "smoobu"

# Basis-URL der Smoobu-API (Pfade beginnen mit /api/...).
API_BASE_URL = "https://login.smoobu.com"

# --- Einträge in config_entry.data -----------------------------------------
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"
CONF_USER_ID = "user_id"
# Webhook: lokale HA-Webhook-ID, öffentliche URL (Nabu Casa Cloudhook)
# und die ID der Registrierung bei Smoobu (zum späteren Löschen).
CONF_WEBHOOK_ID = "webhook_id"
CONF_CLOUDHOOK_URL = "cloudhook_url"
CONF_SMOOBU_WEBHOOK_ID = "smoobu_webhook_id"

# --- Optionen (config_entry.options) ---------------------------------------
CONF_SCAN_INTERVAL = "scan_interval"  # Minuten
CONF_DAYS_BACK = "days_back"  # Tage Rückblick (laufende Buchungen)
CONF_DAYS_AHEAD = "days_ahead"  # Tage Vorschau
CONF_DEFAULT_CHECKIN = "default_checkin"  # "HH:MM", wenn Smoobu keine Zeit liefert
CONF_DEFAULT_CHECKOUT = "default_checkout"  # "HH:MM"
CONF_USE_WEBHOOK = "use_webhook"
CONF_ENRICH_COUNT = "enrich_count"  # Wie viele kommende Buchungen je Wohnung Detaildaten bekommen
# Puffer in Minuten nach einer in Smoobu angegebenen Abreisezeit, bis die
# Wohnung als frei gilt (Gast verlässt die Wohnung oft später als angegeben).
# Gilt NICHT für den Standard-Check-out (der ist bereits die Freigabezeit).
CONF_CHECKOUT_BUFFER = "checkout_buffer"
# Kanäle, deren Zahlung über das Portal läuft (Smoobu meldet dort oft
# "price-paid: No", obwohl das Portal kassiert) → nicht als offen zählen.
CONF_PAYMENT_EXCLUDED_CHANNELS = "payment_excluded_channels"

DEFAULT_SCAN_INTERVAL = 10
DEFAULT_DAYS_BACK = 30
DEFAULT_DAYS_AHEAD = 365
# 16:00, wenn Smoobu keine Ankunftszeit liefert (übliche Check-in-Zeit).
DEFAULT_CHECKIN = "16:00"
# Übliche Check-out-Zeit 11 Uhr.
DEFAULT_CHECKOUT = "11:00"
DEFAULT_USE_WEBHOOK = True
DEFAULT_ENRICH_COUNT = 3
# Wartezeit nach Check-out bis zur Freigabe (z. B. Reinigungsstart); Standard seit v1.17.0: 30 min
DEFAULT_CHECKOUT_BUFFER = 30
DEFAULT_PAYMENT_EXCLUDED_CHANNELS = ["Airbnb", "Booking.com"]

# Provisionen (nur genutzt, wenn Smoobu keine Provision zur Buchung liefert)
CONF_COMMISSIONS = "commissions"  # {Kanalname: Prozent}
CONF_COMMISSION_OTHER = "commission_other"  # % für Portale ohne eigenen Eintrag
CONF_DIRECT_CHANNELS = "direct_channels"  # Kanäle, die als Direktvermarktung zählen
DEFAULT_COMMISSIONS = {
    "Airbnb": 15.5,
    "Booking.com": 15.0,
    "FeWo-direkt": 8.0,
    "Website": 0.0,
    "Direct booking": 0.0,
}
DEFAULT_COMMISSION_OTHER = 15.0
DEFAULT_DIRECT_CHANNELS = ["Direct booking", "Website"]
# Feldnamen im Optionsformular → Kanalname in Smoobu
COMMISSION_FIELDS = {
    "commission_airbnb": "Airbnb",
    "commission_booking": "Booking.com",
    "commission_fewo": "FeWo-direkt",
    "commission_website": "Website",
    "commission_direct": "Direct booking",
}
CONF_COMMISSION_CUSTOM = "commission_custom"  # Freitext "Kanal=Prozent; Kanal=Prozent"

# Auswertungen: so viele Jahre vor dem laufenden Jahr werden geladen
CONF_HISTORY_YEARS = "history_years"
DEFAULT_HISTORY_YEARS = 2
# Alternativ fester Startpunkt (ISO-Datum „YYYY-MM-DD“, ab v1.17.0). Ist er gesetzt, gilt er
# statt CONF_HISTORY_YEARS – spätestens aber ab 01.01. des Vorjahres, weil Jahres- und
# Vorjahresvergleiche sonst keine Daten hätten.
CONF_HISTORY_SINCE = "history_since"

# KI-Assistent (ab v1.10.0)
CONF_ASSISTANT = "assistant"  # automatische Antwortvorschläge an/aus (wirkt nur mit erlaubter KI)
CONF_AI_ENTITY = "ai_entity"  # ai_task.* Entität
# Hauptschalter KI (ab v1.14.0): aus = keinerlei Aufruf von ai_task, keine Daten an KI-Anbieter.
# Fehlt der Schlüssel (Installation vor 1.14.0), gilt: erlaubt, wenn eine KI-Entität gewählt ist –
# so ändert sich für bestehende Installationen nichts. Neue Installationen starten ohne KI.
CONF_AI_ENABLED = "ai_enabled"
CONF_ASSIST_RECIPIENTS = "assist_recipients"  # notify-Dienste (mobile_app_*), Pushes mit Buttons
CONF_ASSIST_STATUS = "assist_status"  # HA-Entitäten als Kontext (Heizung, Tür …)
CONF_ASSIST_PATH = "assist_path"  # Dashboard-Pfad für „Bearbeiten“
CONF_ASSIST_BRIEFING = "assist_briefing"
CONF_ASSIST_BRIEFING_TIME = "assist_briefing_time"
CONF_ASSIST_GAPS = "assist_gaps"
# Benachrichtigungen (v1.17.0): je Push-Art notify_<art> (an/aus) und notify_<art>_to (Empfänger)
NOTIFY_TYPES = ["buchung", "storno", "nachricht", "vorschlag", "zahlung", "briefing", "luecken"]
CONF_NOTIFY_QUIET = "notify_quiet"  # Ruhezeit an/aus
CONF_NOTIFY_QUIET_FROM = "notify_quiet_from"
CONF_NOTIFY_QUIET_TO = "notify_quiet_to"
CONF_NOTIFY_QUIET_MESSAGES = "notify_quiet_messages"  # Gästenachrichten auch in der Ruhezeit sofort
CONF_NOTIFY_PAYMENT_DAYS = "notify_zahlung_days"
CONF_NOTIFY_PAYMENT_TIME = "notify_zahlung_time"
CONF_NOTIFY_GAPS_TIME = "notify_luecken_time"
DEFAULT_NOTIFY_QUIET_FROM = "21:00"
DEFAULT_NOTIFY_QUIET_TO = "07:00"
DEFAULT_NOTIFY_PAYMENT_DAYS = 7
DEFAULT_NOTIFY_PAYMENT_TIME = "09:00"
DEFAULT_NOTIFY_GAPS_TIME = "09:05"  # bisher fest 09:05

# Wohnungskürzel (v1.17.0): {apartment_id (Text): Kürzel}; fehlt eine Wohnung → automatisch
CONF_APARTMENT_CODES = "apartment_codes"
MAX_CODE_LEN = 4

# Einstellungen im Dashboard (v1.18.0): HA-Benutzer-IDs, die außer den Admins ändern dürfen
CONF_SETTINGS_USERS = "settings_users"
# Benutzerrollen (v1.18.0): {HA-Benutzer-ID: Rolle} und Rolle für Benutzer ohne Eintrag (siehe rechte.py).
# settings_users bleibt als Altwert lesbar: Benutzer darin gelten als „verwalter“.
CONF_USER_ROLES = "user_roles"
CONF_DEFAULT_ROLE = "default_role"
DEFAULT_ROLE = "betrieb"

# Kosten & Preise (v1.18.0, Entscheidung Betreiber 17.11.2026): variable Kosten für den
# Deckungsbeitrag und Smoobu-Preisaufschläge je Kanal für Empfehlungen.
# Standardwerte = Nebenkostenabrechnung der Referenz-Ferienwohnung 2025 (siehe deckungsbeitrag.py)
CONF_COST_CLEANING = "cost_cleaning"            # € je Aufenthalt
CONF_COST_LAUNDRY = "cost_laundry"              # € je Aufenthalt
CONF_COST_HEATING_YEAR = "cost_heating_year"    # € Heizung im Bezugsjahr
CONF_COST_HOT_WATER_YEAR = "cost_hot_water_year"  # € Warmwasser im Bezugsjahr
CONF_COST_REF_YEAR = "cost_ref_year"            # Abrechnungsjahr der Jahreswerte
CONF_COST_WATER_NIGHT = "cost_water_night"      # € Wasser/Abwasser je Nacht
CONF_COST_POWER_KWH = "cost_power_kwh"          # kWh Strom je Nacht
CONF_COST_GRID_PRICE = "cost_grid_price"        # ct/kWh Netzstrom
CONF_COST_PV_VALUE = "cost_pv_value"            # ct/kWh PV-Strom (Einspeisevergütung)
CONF_COST_GRID_SHARE = "cost_grid_share"        # 12 Werte: % Netzbezug je Monat
CONF_CHANNEL_MARKUPS = "channel_markups"        # {Kanal: % Aufschlag auf den Smoobu-Basispreis}
CONF_GENIUS_DISCOUNT = "genius_discount"        # % Booking.com-Genius-Rabatt
CONF_GENIUS_SHARE = "genius_share"              # % der Booking.com-Buchungen mit Genius
DEFAULT_COST_CLEANING = 17.0
DEFAULT_COST_LAUNDRY = 5.0
DEFAULT_COST_HEATING_YEAR = 473.31
DEFAULT_COST_HOT_WATER_YEAR = 161.53
DEFAULT_COST_REF_YEAR = 2025
DEFAULT_COST_WATER_NIGHT = 0.47
DEFAULT_COST_POWER_KWH = 4.6
DEFAULT_COST_GRID_PRICE = 30.54
DEFAULT_COST_PV_VALUE = 8.2
DEFAULT_COST_GRID_SHARE = [72, 55, 15, 11, 7, 10, 5, 26, 20, 47, 67, 80]
DEFAULT_CHANNEL_MARKUPS = {"Airbnb": 33.0, "Booking.com": 45.0, "HomeToGo": 10.0}
DEFAULT_GENIUS_DISCOUNT = 10.0
# Konservativ: ohne Angabe wird angenommen, dass jeder Booking.com-Gast Genius-Rabatt bekommt
DEFAULT_GENIUS_SHARE = 100.0

SERVICE_ASSIST_SUGGEST = "assistant_suggest"
SERVICE_ASSIST_IMPORT = "assistant_import"
SERVICE_ASSIST_KNOWLEDGE = "assistant_build_knowledge"

FALLBACK_CHECKIN = time(16, 0)
FALLBACK_CHECKOUT = time(11, 0)

# Zeitraum für die Statistik-Sensoren (Buchungen/Auslastung).
STATS_DAYS = 30

# --- Events auf dem HA-Eventbus ---------------------------------------------
# Ein Eventtyp, Unterscheidung über event_data.action
# (newReservation, updateReservation, cancelReservation, deleteReservation,
#  newMessage, onlineCheckInUpdate, updateRates).
EVENT_SMOOBU = "smoobu_event"

# --- Services ----------------------------------------------------------------
SERVICE_REFRESH = "refresh"
SERVICE_GET_RESERVATIONS = "get_reservations"
SERVICE_GET_RESERVATION = "get_reservation"
SERVICE_GET_MESSAGES = "get_messages"
SERVICE_SEND_MESSAGE = "send_message"
# Schreibende Aktionen (ab v1.9.0)
SERVICE_BLOCK_PERIOD = "block_period"
SERVICE_DELETE_RESERVATION = "delete_reservation"
SERVICE_SET_RATES = "set_rates"
SERVICE_UPDATE_RESERVATION = "update_reservation"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_RESERVATION_ID = "reservation_id"
ATTR_APARTMENT_ID = "apartment_id"
ATTR_ARRIVAL_FROM = "arrival_from"
ATTR_ARRIVAL_TO = "arrival_to"
ATTR_DEPARTURE_FROM = "departure_from"
ATTR_DEPARTURE_TO = "departure_to"
ATTR_SHOW_CANCELLATION = "show_cancellation"
ATTR_ONLY_GUEST = "only_related_to_guest"
ATTR_RECIPIENT = "recipient"
ATTR_SUBJECT = "subject"
ATTR_MESSAGE = "message"
ATTR_INTERNAL = "internal"
ATTR_START = "start_date"
ATTR_END = "end_date"
ATTR_NOTICE = "notice"
ATTR_PRICE = "price"
ATTR_MIN_STAY = "min_stay"
ATTR_ARRIVAL_TIME = "arrival_time"
ATTR_DEPARTURE_TIME = "departure_time"
ATTR_ALLOW_BOOKING = "allow_booking"

# Felder, die in Diagnosen geschwärzt werden (Gästedaten / Zugangsdaten).
REDACT_KEYS = {
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_CLOUDHOOK_URL,
    CONF_WEBHOOK_ID,
    "guest-name",
    "firstname",
    "lastname",
    "email",
    "phone",
    "guest-app-url",
    "notice",
    "assistant-notice",
    # Felder der Auswertungs-Datensätze (analytics.py)
    "gast",
    "vorname",
    "telefon",
    "notiz",
    "assistent_notiz",
    "hund_hinweis",
}


def ai_allowed(options: dict) -> bool:
    """KI-Hauptschalter auswerten (ab v1.14.0).

    Erlaubt nur, wenn der Schalter an ist UND eine KI-Entität gewählt ist.
    Ohne gespeicherten Schalter (alte Installation) zählt die gewählte KI-Entität.
    """
    if not options.get(CONF_AI_ENTITY):
        return False
    return bool(options.get(CONF_AI_ENABLED, True))

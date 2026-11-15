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
DEFAULT_CHECKOUT_BUFFER = 0
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
}

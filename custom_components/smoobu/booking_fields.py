"""Einzelne Buchungsfelder des aktuellen und nächsten Gastes als eigene Entitäten.

Jedes Feld der Smoobu-Buchung wird zweimal angelegt (Präfix „aktueller_gast_“
bzw. „naechster_gast_“). Selten benötigte Felder (IDs, Zeitstempel, Links)
sind standardmäßig deaktiviert und können in HA eingeschaltet werden.
Kontaktdaten und Notizen sind aktiv (Entscheidung Betreiber).

Hinweis: Ein Entitätszustand darf max. 255 Zeichen lang sein – lange
Notizen werden gekürzt, der volle Text steht im Attribut „text“.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass

from .models import (
    booking_end,
    booking_start,
    guest_count,
    is_yes,
    nights,
    open_amount,
    parse_datetime,
)


@dataclass(frozen=True)
class BookingField:
    """Beschreibung eines Buchungsfeldes."""

    key: str  # Teil des translation_key / unique_id
    name_de: str
    name_en: str
    value: Callable[[Any, dict[str, Any]], Any]  # (coordinator, booking) -> Wert
    icon: str
    device_class: str | None = None  # SensorDeviceClass bzw. BinarySensorDeviceClass
    unit: str | None = None
    monetary: bool = False
    binary: bool = False
    enabled: bool = True
    # nur für eine Seite aktiv (Dubletten zu bestehenden Sensoren vermeiden)
    enabled_current: bool | None = None
    enabled_next: bool | None = None


def _text(value: Any) -> str | None:
    """Leere Werte → None, lange Texte auf 255 Zeichen kürzen."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text if len(text) <= 255 else text[:252] + "…"


def _num(value: Any) -> float | None:
    try:
        return None if value in (None, "") else round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _ts(dt: datetime | None) -> datetime | None:
    return dt


FIELDS: tuple[BookingField, ...] = (
    BookingField("buchungs_id", "Buchungs-ID", "Booking ID", lambda c, b: b.get("id"), "mdi:identifier", enabled=False),
    BookingField("referenz_id", "Referenz-ID", "Reference ID", lambda c, b: _text(b.get("reference-id")), "mdi:barcode", enabled=False),
    BookingField("gast_id", "Gast-ID", "Guest ID", lambda c, b: b.get("guestId"), "mdi:card-account-details", enabled=False),
    BookingField("typ", "Buchungstyp", "Booking type", lambda c, b: _text(b.get("type")), "mdi:tag", enabled=False),
    BookingField("kanal", "Kanal", "Channel", lambda c, b: _text((b.get("channel") or {}).get("name")), "mdi:web"),
    BookingField("kanal_gruppe", "Kanalgruppe", "Channel group", lambda c, b: c.costs(b)["kanal_gruppe"], "mdi:source-branch"),
    BookingField("provision", "Provision", "Commission", lambda c, b: round(c.costs(b)["provision"] + c.costs(b)["zahlungsgebuehr"], 2), "mdi:hand-coin", monetary=True),
    BookingField("netto_preis", "Nettopreis", "Net price", lambda c, b: c.costs(b)["netto"], "mdi:cash-check", monetary=True),
    BookingField("sprache", "Sprache", "Language", lambda c, b: _text(b.get("language")), "mdi:translate"),
    BookingField("email", "E-Mail", "Email", lambda c, b: _text(b.get("email")), "mdi:email"),
    BookingField("telefon", "Telefon", "Phone", lambda c, b: _text(b.get("phone")), "mdi:phone"),
    BookingField("erwachsene", "Erwachsene", "Adults", lambda c, b: b.get("adults"), "mdi:human-male-female"),
    BookingField("kinder", "Kinder", "Children", lambda c, b: b.get("children"), "mdi:human-child"),
    BookingField("personen", "Personen", "Guests", lambda c, b: guest_count(b), "mdi:account-group", enabled=False),
    BookingField("naechte", "Nächte", "Nights", lambda c, b: nights(b), "mdi:weather-night"),
    BookingField("check_in_zeit", "Check-in-Zeit", "Check-in time", lambda c, b: _text(b.get("check-in")), "mdi:clock-in"),
    BookingField("check_out_zeit", "Check-out-Zeit", "Check-out time", lambda c, b: _text(b.get("check-out")), "mdi:clock-out"),
    BookingField(
        "anreise", "Anreise", "Arrival",
        lambda c, b: booking_start(b, c.default_checkin), "mdi:calendar-arrow-right",
        device_class=SensorDeviceClass.TIMESTAMP, enabled_next=False,  # Dublette zu „Nächste Anreise“
    ),
    BookingField(
        "abreise", "Abreise", "Departure",
        lambda c, b: booking_end(b, c.default_checkout), "mdi:calendar-arrow-left",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    BookingField(
        "freigabe", "Freigabe", "Release",
        lambda c, b: c.release(b), "mdi:door-open",
        device_class=SensorDeviceClass.TIMESTAMP, enabled_current=False,  # = „Nächste Abreise“
        enabled_next=False,
    ),
    BookingField("anzahlung", "Anzahlung", "Prepayment", lambda c, b: _num(b.get("prepayment")), "mdi:cash-plus", monetary=True),
    BookingField("kaution", "Kaution", "Deposit", lambda c, b: _num(b.get("deposit")), "mdi:shield-account", monetary=True, enabled=False),
    BookingField("kurtaxe", "Kurtaxe", "City tax", lambda c, b: _num(b.get("city-tax")), "mdi:bank", monetary=True, enabled=False),
    BookingField(
        "offener_betrag", "Offener Betrag", "Open amount",
        lambda c, b: open_amount(b, c.payment_excluded_channels), "mdi:cash-clock", monetary=True,
    ),
    BookingField("notiz", "Notiz", "Note", lambda c, b: _text(b.get("notice")), "mdi:note-text"),
    BookingField("assistent_notiz", "Assistent-Notiz", "Assistant note", lambda c, b: _text(b.get("assistant-notice")), "mdi:note-text-outline"),
    BookingField("gaeste_app", "Gäste-App", "Guest app", lambda c, b: _text(b.get("guest-app-url")), "mdi:cellphone-link", enabled=False),
    BookingField(
        "erstellt", "Erstellt", "Created",
        lambda c, b: parse_datetime(b.get("created-at")), "mdi:calendar-plus",
        device_class=SensorDeviceClass.TIMESTAMP, enabled=False,
    ),
    BookingField(
        "geaendert", "Geändert", "Modified",
        lambda c, b: parse_datetime(b.get("modifiedAt")), "mdi:calendar-edit",
        device_class=SensorDeviceClass.TIMESTAMP, enabled=False,
    ),
    # --- Binärsensoren (Zahlungsstatus) ---
    BookingField("preis_bezahlt", "Preis bezahlt", "Price paid", lambda c, b: is_yes(b.get("price-paid")), "mdi:cash-check", binary=True),
    BookingField("anzahlung_bezahlt", "Anzahlung bezahlt", "Prepayment paid", lambda c, b: is_yes(b.get("prepayment-paid")), "mdi:cash-check", binary=True),
    BookingField("kaution_bezahlt", "Kaution bezahlt", "Deposit paid", lambda c, b: is_yes(b.get("deposit-paid")), "mdi:shield-check", binary=True, enabled=False),
)

# Präfix → (Name DE, Name EN, Coordinator-Methode)
SCOPES: dict[str, tuple[str, str, str]] = {
    "aktueller_gast": ("Aktueller Gast", "Current guest", "current_booking"),
    "naechster_gast": ("Nächster Gast", "Next guest", "next_booking"),
}


def is_enabled(field: BookingField, scope: str) -> bool:
    """Standard-Aktivierung je Feld und Seite."""
    override = field.enabled_current if scope == "aktueller_gast" else field.enabled_next
    return field.enabled if override is None else override

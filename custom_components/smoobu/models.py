"""Hilfsfunktionen zum Auswerten von Smoobu-Buchungen.

Smoobu liefert Datumswerte als Text (arrival "YYYY-MM-DD", check-in "HH:MM"
oder null). Hier wird alles einmal zentral in echte Zeitpunkte in der
HA-Zeitzone umgerechnet, damit Kalender, Sensoren und Binärsensoren
dieselbe Logik verwenden.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from homeassistant.util import dt as dt_util


@dataclass
class SmoobuData:
    """Vom Coordinator bereitgestellter Datenstand."""

    # Wohnungs-ID → Wohnungsdaten (inkl. Details aus /api/apartments/{id})
    apartments: dict[int, dict[str, Any]] = field(default_factory=dict)
    # Wohnungs-ID → nach Anreise sortierte Buchungen (ohne Stornos)
    bookings: dict[int, list[dict[str, Any]]] = field(default_factory=dict)
    # False, wenn der API-Schlüssel keine Gästedaten (PII) liefert
    pii_available: bool | None = None
    last_update: datetime | None = None
    last_event: dict[str, Any] | None = None


def parse_time(value: Any, fallback: time | None) -> time | None:
    """'16:00' / '16:00:00' → time; leer/ungültig → fallback."""
    if not value or not isinstance(value, str):
        return fallback
    parts = value.strip().split(":")
    try:
        return time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    except (ValueError, IndexError):
        return fallback


def parse_date(value: Any) -> date | None:
    """'YYYY-MM-DD' → date."""
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def parse_datetime(value: Any) -> datetime | None:
    """'YYYY-MM-DD HH:MM' (Smoobu-Format für created-at/modifiedAt) → aware datetime."""
    if not value or not isinstance(value, str):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=dt_util.get_default_time_zone())
        except ValueError:
            continue
    return None


def booking_start(booking: dict[str, Any], default_checkin: time) -> datetime | None:
    """Anreisezeitpunkt = arrival + check-in (sonst Standard-Check-in)."""
    day = parse_date(booking.get("arrival"))
    if day is None:
        return None
    return datetime.combine(
        day,
        parse_time(booking.get("check-in"), default_checkin),
        tzinfo=dt_util.get_default_time_zone(),
    )


def booking_end(booking: dict[str, Any], default_checkout: time) -> datetime | None:
    """Abreisezeitpunkt = departure + check-out (sonst Standard-Check-out)."""
    day = parse_date(booking.get("departure"))
    if day is None:
        return None
    return datetime.combine(
        day,
        parse_time(booking.get("check-out"), default_checkout),
        tzinfo=dt_util.get_default_time_zone(),
    )


def booking_release(
    booking: dict[str, Any], default_checkout: time, buffer_minutes: int
) -> datetime | None:
    """Zeitpunkt, ab dem die Wohnung als frei gilt („Freigabe“).

    - Abreisezeit in Smoobu angegeben → diese Zeit + Puffer
    - keine Abreisezeit → Standard-Check-out (ohne Puffer)
    """
    end = booking_end(booking, default_checkout)
    if end is None:
        return None
    # parse_time mit fallback=None → None, wenn Smoobu keine gültige Zeit liefert
    if parse_time(booking.get("check-out"), None) is not None:
        return end + timedelta(minutes=buffer_minutes)
    return end


def is_blocked(booking: dict[str, Any]) -> bool:
    """Vom Gastgeber blockierter Zeitraum (keine echte Gästebuchung)."""
    return bool(booking.get("is-blocked-booking"))


def guest_name(booking: dict[str, Any]) -> str:
    """Bester verfügbarer Gastname (voller Name, sonst Vor-/Nachname)."""
    name = (booking.get("guest-name") or "").strip()
    if not name:
        name = " ".join(
            part for part in (booking.get("firstname"), booking.get("lastname")) if part
        ).strip()
    return name


def first_name(booking: dict[str, Any]) -> str:
    """Vorname (Detaildaten), sonst erstes Wort des Gastnamens."""
    if booking.get("firstname"):
        return str(booking["firstname"]).strip()
    name = guest_name(booking)
    return name.split(" ")[0] if name else ""


def guest_count(booking: dict[str, Any]) -> int:
    """Erwachsene + Kinder."""
    return int(booking.get("adults") or 0) + int(booking.get("children") or 0)


def nights(booking: dict[str, Any]) -> int | None:
    arrival = parse_date(booking.get("arrival"))
    departure = parse_date(booking.get("departure"))
    if arrival is None or departure is None:
        return None
    return (departure - arrival).days


def is_yes(value: Any) -> bool:
    """Smoobu liefert Zahlungsflags teils als 'Yes'/'No', teils als bool."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("yes", "true", "1", "ja")


def booking_attributes(
    booking: dict[str, Any] | None,
    default_checkin: time,
    default_checkout: time,
    buffer_minutes: int = 0,
) -> dict[str, Any]:
    """Aufbereitete Attribute einer Buchung für Sensoren.

    Deutsche, sprechende Schlüssel für Automationen/Dashboards plus
    die vollständigen Rohdaten unter `smoobu_rohdaten`, damit wirklich
    alle Felder verfügbar sind (auch neue, die Smoobu später ergänzt).
    """
    if not booking:
        return {}
    start = booking_start(booking, default_checkin)
    end = booking_end(booking, default_checkout)
    release = booking_release(booking, default_checkout, buffer_minutes)
    channel = booking.get("channel") or {}
    apartment = booking.get("apartment") or {}
    return {
        "buchungs_id": booking.get("id"),
        "referenz_id": booking.get("reference-id"),
        "typ": booking.get("type"),
        "blockiert": is_blocked(booking),
        "wohnung": apartment.get("name"),
        "wohnung_id": apartment.get("id"),
        "gastname": guest_name(booking),
        "vorname": first_name(booking),
        "nachname": booking.get("lastname"),
        "gast_id": booking.get("guestId"),
        "email": booking.get("email"),
        "telefon": booking.get("phone"),
        "sprache": booking.get("language"),
        "kanal": channel.get("name"),
        "kanal_id": channel.get("id"),
        "anreise": start.isoformat() if start else None,
        "abreise": end.isoformat() if end else None,
        # Ab hier gilt die Wohnung als frei (Abreisezeit + Puffer bzw. Standard-Check-out)
        "freigabe": release.isoformat() if release else None,
        "check_in_zeit": booking.get("check-in"),
        "check_out_zeit": booking.get("check-out"),
        "naechte": nights(booking),
        "erwachsene": booking.get("adults"),
        "kinder": booking.get("children"),
        "personen": guest_count(booking),
        "preis": booking.get("price"),
        "preis_bezahlt": is_yes(booking.get("price-paid")),
        "anzahlung": booking.get("prepayment"),
        "anzahlung_bezahlt": is_yes(booking.get("prepayment-paid")),
        "kaution": booking.get("deposit"),
        "kaution_bezahlt": is_yes(booking.get("deposit-paid")),
        "kurtaxe": booking.get("city-tax"),
        "provision_enthalten": booking.get("commission-included"),
        "notiz": booking.get("notice"),
        "assistent_notiz": booking.get("assistant-notice"),
        "gaeste_app": booking.get("guest-app-url"),
        "erstellt": booking.get("created-at"),
        "geaendert": booking.get("modifiedAt"),
        "smoobu_rohdaten": booking,
    }


def stay_overlap_nights(
    booking: dict[str, Any], window_start: date, window_end: date
) -> int:
    """Belegte Nächte einer Buchung im Fenster [window_start, window_end)."""
    arrival = parse_date(booking.get("arrival"))
    departure = parse_date(booking.get("departure"))
    if arrival is None or departure is None:
        return 0
    start = max(arrival, window_start)
    end = min(departure, window_end)
    return max((end - start).days, 0)


def window(days: int) -> tuple[date, date]:
    """Heute bis heute + days (exklusiv) in lokaler Zeit."""
    today = dt_util.now().date()
    return today, today + timedelta(days=days)

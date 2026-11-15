"""Kalender je Smoobu-Wohnung – mit vollem Gastnamen statt iCal-Platzhalter.

Termine laufen von Anreise (Datum + Check-in-Zeit) bis Abreise
(Datum + Check-out-Zeit). Fehlt die Zeit in Smoobu, gelten die
Standardzeiten aus den Optionen (16:00 / 11:00).
Blockierte Zeiträume erscheinen als „Blockiert“.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import SmoobuConfigEntry
from .api import SmoobuError
from .coordinator import SmoobuCoordinator
from .entity import SmoobuEntity
from .models import booking_end, booking_start, guest_count, guest_name, is_blocked, nights

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmoobuConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        SmoobuCalendar(coordinator, apt_id) for apt_id in coordinator.data.apartments
    )


class SmoobuCalendar(SmoobuEntity, CalendarEntity):
    """Belegungskalender einer Wohnung."""

    def __init__(self, coordinator: SmoobuCoordinator, apartment_id: int) -> None:
        super().__init__(coordinator, apartment_id, "belegung")

    def _to_event(self, booking: dict[str, Any]) -> CalendarEvent | None:
        coordinator = self.coordinator
        start = booking_start(booking, coordinator.default_checkin)
        end = booking_end(booking, coordinator.default_checkout)
        if start is None or end is None or end <= start:
            return None
        if is_blocked(booking):
            summary = "Blockiert"
        else:
            summary = guest_name(booking) or "Gast"
        channel = (booking.get("channel") or {}).get("name") or ""
        # Beschreibung zeilenweise, damit Kalenderkarten sie lesbar anzeigen.
        lines = [
            f"Buchung: {booking.get('id')} ({booking.get('reference-id') or '-'})",
            f"Kanal: {channel}",
            f"Personen: {guest_count(booking)} "
            f"({booking.get('adults') or 0} Erw., {booking.get('children') or 0} Ki.)",
            f"Nächte: {nights(booking)}",
            f"Check-in: {booking.get('check-in') or 'Standard'} · "
            f"Check-out: {booking.get('check-out') or 'Standard'}",
        ]
        if booking.get("price") is not None:
            lines.append(f"Preis: {booking.get('price')} (bezahlt: {booking.get('price-paid')})")
        if booking.get("phone"):
            lines.append(f"Telefon: {booking.get('phone')}")
        if booking.get("email"):
            lines.append(f"E-Mail: {booking.get('email')}")
        if booking.get("language"):
            lines.append(f"Sprache: {booking.get('language')}")
        if booking.get("notice"):
            lines.append(f"Notiz: {booking.get('notice')}")
        return CalendarEvent(
            start=start,
            end=end,
            summary=summary,
            description="\n".join(lines),
            uid=str(booking.get("id")),
            location=(booking.get("apartment") or {}).get("name"),
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Laufende Buchung, sonst die nächste (inkl. Blockierungen)."""
        coordinator = self.coordinator
        booking = coordinator.current_booking(self.apartment_id, guests_only=False)
        if booking is None:
            booking = coordinator.next_booking(self.apartment_id, guests_only=False)
        return self._to_event(booking) if booking else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Termine im angefragten Zeitraum.

        Liegt der Zeitraum außerhalb des gecachten Fensters (z. B. Kalender-
        karte blättert weit zurück), wird direkt bei Smoobu nachgefragt.
        Bei Fehler: Rückfall auf die gecachten Daten.
        """
        cached = self.coordinator.bookings_for(self.apartment_id)
        bookings = cached
        start_day = dt_util.as_local(start_date).date()
        end_day = dt_util.as_local(end_date).date()
        win_start, win_end = self.coordinator.window
        if win_start is None or start_day < win_start or end_day > win_end:
            try:
                bookings = await self.coordinator.client.get_reservations(
                    apartmentId=self.apartment_id,
                    departureFrom=start_day.isoformat(),
                    arrivalTo=end_day.isoformat(),
                    showCancellation=False,
                )
            except SmoobuError as err:
                _LOGGER.debug("Kalenderabruf direkt fehlgeschlagen, nutze Cache: %s", err)
                bookings = cached

        events: list[CalendarEvent] = []
        for booking in bookings:
            event = self._to_event(booking)
            if event and event.end > start_date and event.start < end_date:
                events.append(event)
        events.sort(key=lambda e: e.start)
        return events

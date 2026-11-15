"""DataUpdateCoordinator: holt Wohnungen und Buchungen zentral von Smoobu.

Ein Coordinator je Smoobu-Konto. Alle Entitäten lesen aus demselben
Datenstand → eine API-Abfrage pro Intervall statt einer pro Entität.
Der Webhook stößt zusätzlich sofort eine Aktualisierung an.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import SmoobuAuthError, SmoobuClient, SmoobuError
from .const import (
    CONF_DAYS_AHEAD,
    CONF_DAYS_BACK,
    CONF_DEFAULT_CHECKIN,
    CONF_DEFAULT_CHECKOUT,
    CONF_ENRICH_COUNT,
    CONF_SCAN_INTERVAL,
    DEFAULT_CHECKIN,
    DEFAULT_CHECKOUT,
    DEFAULT_DAYS_AHEAD,
    DEFAULT_DAYS_BACK,
    DEFAULT_ENRICH_COUNT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FALLBACK_CHECKIN,
    FALLBACK_CHECKOUT,
)
from .models import SmoobuData, booking_end, booking_start, guest_name, is_blocked, parse_time

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

# Wohnungsdetails ändern sich selten → nur alle 24 h neu laden.
APARTMENT_REFRESH = timedelta(hours=24)


class SmoobuCoordinator(DataUpdateCoordinator[SmoobuData]):
    """Zentraler Abruf aller Smoobu-Daten."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: SmoobuClient) -> None:
        self.client = client
        minutes = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=max(minutes, 1)),
        )
        self._apartments_loaded: Any = None  # Zeitpunkt der letzten Wohnungsabfrage
        # Cache der Einzelbuchungen: id → (modifiedAt, Detaildaten).
        # Detaildaten (Vor-/Nachname, Kurtaxe …) gibt es nur über den
        # Einzelabruf; per Cache wird nur bei Änderung neu geladen.
        self._detail_cache: dict[int, tuple[Any, dict[str, Any]]] = {}
        self._pii_warned = False
        # Zeitraum (von, bis) der zuletzt geladenen Buchungen.
        self.window: tuple[Any, Any] = (None, None)

    # --- Optionen bequem lesbar ----------------------------------------
    @property
    def default_checkin(self):
        return parse_time(
            self.config_entry.options.get(CONF_DEFAULT_CHECKIN, DEFAULT_CHECKIN), FALLBACK_CHECKIN
        )

    @property
    def default_checkout(self):
        return parse_time(
            self.config_entry.options.get(CONF_DEFAULT_CHECKOUT, DEFAULT_CHECKOUT),
            FALLBACK_CHECKOUT,
        )

    # ------------------------------------------------------------------
    async def _async_update_data(self) -> SmoobuData:
        """Wohnungen (24 h gecacht) + Buchungen im Zeitfenster laden."""
        previous = self.data or SmoobuData()
        try:
            apartments = await self._async_load_apartments(previous)
            bookings = await self._async_load_bookings()
            bookings = await self._async_enrich(bookings)
        except SmoobuAuthError as err:
            # Löst in HA den Reauth-Dialog aus (neuer Schlüssel/Secret).
            raise ConfigEntryAuthFailed(str(err)) from err
        except SmoobuError as err:
            raise UpdateFailed(str(err)) from err

        # Nach Wohnung gruppieren, nach Anreise sortieren.
        grouped: dict[int, list[dict[str, Any]]] = {apt_id: [] for apt_id in apartments}
        for booking in bookings:
            apt_id = (booking.get("apartment") or {}).get("id")
            if apt_id is None:
                continue
            grouped.setdefault(int(apt_id), []).append(booking)
        for items in grouped.values():
            items.sort(key=lambda b: (b.get("arrival") or "", b.get("id") or 0))

        # PII-Prüfung: Gibt es echte Gästebuchungen, aber alle Namen leer,
        # fehlt dem Schlüssel die Berechtigung "Guest Data (PII)".
        guests = [b for b in bookings if not is_blocked(b)]
        pii = None
        if guests:
            pii = any(guest_name(b) for b in guests)
            if not pii and not self._pii_warned:
                _LOGGER.warning(
                    "Smoobu liefert keine Gastnamen. Beim API-Schlüssel in Smoobu "
                    "(Einstellungen → Erweitert → API-Schlüssel) die Option "
                    "'Guest Data (PII)' aktivieren"
                )
                self._pii_warned = True

        return SmoobuData(
            apartments=apartments,
            bookings=grouped,
            pii_available=pii,
            last_update=dt_util.utcnow(),
            last_event=previous.last_event,
        )

    async def _async_load_apartments(self, previous: SmoobuData) -> dict[int, dict[str, Any]]:
        now = dt_util.utcnow()
        if (
            previous.apartments
            and self._apartments_loaded
            and now - self._apartments_loaded < APARTMENT_REFRESH
        ):
            return previous.apartments
        apartments: dict[int, dict[str, Any]] = {}
        for apt in await self.client.get_apartments():
            apt_id = int(apt["id"])
            details: dict[str, Any] = {}
            try:
                details = await self.client.get_apartment(apt_id)
            except SmoobuAuthError:
                raise
            except SmoobuError as err:
                # Details sind nur Zusatzinfo – Fehler hier nicht fatal.
                _LOGGER.debug("Wohnungsdetails %s nicht ladbar: %s", apt_id, err)
            apartments[apt_id] = {**details, **apt}
        self._apartments_loaded = now
        return apartments

    async def _async_load_bookings(self) -> list[dict[str, Any]]:
        """Alle Buchungen, die im Fenster [heute − Rückblick, heute + Vorschau] liegen.

        departureFrom erfasst auch laufende Aufenthalte (Anreise in der
        Vergangenheit, Abreise noch offen). Stornos werden nicht geladen,
        blockierte Zeiträume schon (für den Kalender).
        """
        today = dt_util.now().date()
        days_back = int(self.config_entry.options.get(CONF_DAYS_BACK, DEFAULT_DAYS_BACK))
        days_ahead = int(self.config_entry.options.get(CONF_DAYS_AHEAD, DEFAULT_DAYS_AHEAD))
        win_start = today - timedelta(days=days_back)
        win_end = today + timedelta(days=days_ahead)
        # Merken, damit der Kalender weiß, welcher Zeitraum im Cache liegt.
        self.window = (win_start, win_end)
        return await self.client.get_reservations(
            departureFrom=win_start.isoformat(),
            arrivalTo=win_end.isoformat(),
            showCancellation=False,
            includePriceElements=True,
        )

    async def _async_enrich(self, bookings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Laufende + nächste N Buchungen je Wohnung mit Detaildaten ergänzen."""
        count = int(self.config_entry.options.get(CONF_ENRICH_COUNT, DEFAULT_ENRICH_COUNT))
        now = dt_util.now()
        candidates: dict[int, list[dict[str, Any]]] = {}
        for booking in bookings:
            if is_blocked(booking):
                continue
            end = booking_end(booking, self.default_checkout)
            if end is None or end < now:
                continue  # Vergangene Buchungen brauchen keine Details.
            apt_id = (booking.get("apartment") or {}).get("id")
            candidates.setdefault(apt_id, []).append(booking)

        wanted: set[int] = set()
        for items in candidates.values():
            items.sort(key=lambda b: booking_start(b, self.default_checkin) or now)
            wanted.update(int(b["id"]) for b in items[: count + 1])  # +1 = laufende

        enriched: list[dict[str, Any]] = []
        for booking in bookings:
            bid = int(booking.get("id") or 0)
            if bid in wanted:
                stamp = booking.get("modifiedAt")
                cached = self._detail_cache.get(bid)
                if cached and cached[0] == stamp:
                    details = cached[1]
                else:
                    try:
                        details = await self.client.get_reservation(bid)
                        self._detail_cache[bid] = (stamp, details)
                    except SmoobuAuthError:
                        raise
                    except SmoobuError as err:
                        _LOGGER.debug("Buchungsdetails %s nicht ladbar: %s", bid, err)
                        details = {}
                # Listen-Daten haben Vorrang (enthalten priceElements),
                # Details ergänzen fehlende Felder.
                booking = {**details, **booking}
            enriched.append(booking)
        # Cache aufräumen (nur noch relevante IDs behalten).
        self._detail_cache = {k: v for k, v in self._detail_cache.items() if k in wanted}
        return enriched

    # ------------------------------------------------------------------
    def bookings_for(self, apartment_id: int) -> list[dict[str, Any]]:
        if not self.data:
            return []
        return self.data.bookings.get(apartment_id, [])

    def current_booking(self, apartment_id: int, guests_only: bool = True) -> dict[str, Any] | None:
        """Buchung, deren Zeitraum (Check-in bis Check-out) gerade läuft."""
        now = dt_util.now()
        for booking in self.bookings_for(apartment_id):
            if guests_only and is_blocked(booking):
                continue
            start = booking_start(booking, self.default_checkin)
            end = booking_end(booking, self.default_checkout)
            if start and end and start <= now < end:
                return booking
        return None

    def next_booking(self, apartment_id: int, guests_only: bool = True) -> dict[str, Any] | None:
        """Nächste Buchung mit Anreise in der Zukunft."""
        now = dt_util.now()
        for booking in self.bookings_for(apartment_id):
            if guests_only and is_blocked(booking):
                continue
            start = booking_start(booking, self.default_checkin)
            if start and start > now:
                return booking
        return None

    def set_last_event(self, event: dict[str, Any]) -> None:
        """Letztes Webhook-Ereignis merken (für den Diagnose-Sensor)."""
        if self.data is not None:
            self.data.last_event = event
            self.async_update_listeners()

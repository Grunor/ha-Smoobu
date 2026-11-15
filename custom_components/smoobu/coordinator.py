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
    CONF_CHECKOUT_BUFFER,
    CONF_ENRICH_COUNT,
    CONF_COMMISSION_OTHER,
    CONF_COMMISSIONS,
    CONF_DIRECT_CHANNELS,
    CONF_PAYMENT_EXCLUDED_CHANNELS,
    CONF_SCAN_INTERVAL,
    CONF_HISTORY_YEARS,
    DEFAULT_HISTORY_YEARS,
    DEFAULT_COMMISSION_OTHER,
    DEFAULT_COMMISSIONS,
    DEFAULT_DIRECT_CHANNELS,
    DEFAULT_CHECKIN,
    DEFAULT_CHECKOUT,
    DEFAULT_CHECKOUT_BUFFER,
    DEFAULT_DAYS_AHEAD,
    DEFAULT_DAYS_BACK,
    DEFAULT_ENRICH_COUNT,
    DEFAULT_PAYMENT_EXCLUDED_CHANNELS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FALLBACK_CHECKIN,
    FALLBACK_CHECKOUT,
)
from .analytics import build_records, is_cancelled
from .channels import booking_costs, night_rows
from .models import (
    SmoobuData,
    nights_by_month,
    revenue_by_month,
    strip_html,
    booking_end,
    booking_release,
    booking_start,
    guest_name,
    is_blocked,
    parse_time,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

# Wohnungsdetails ändern sich selten → nur alle 24 h neu laden.
APARTMENT_REFRESH = timedelta(hours=24)
# Umsatzdaten (Vorjahr + laufendes Jahr) stündlich bzw. nach Webhook neu laden.
REVENUE_REFRESH = timedelta(hours=1)
# Tagespreise/Verfügbarkeit: 60 Tage Vorschau, stündlich neu laden.
RATES_DAYS = 60
RATES_REFRESH = timedelta(hours=1)


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
        # Umsatz-Cache: Zeitpunkt der letzten Jahresabfrage + Merker für Webhook
        self._revenue_loaded: Any = None
        self._revenue_bookings: list[dict[str, Any]] = []
        self.force_revenue_refresh = False
        # Tagespreise-Cache
        self._rates_loaded: Any = None
        self._rates: dict[int, dict[str, dict[str, Any]]] = {}
        # Zeitraum (von, bis) der zuletzt geladenen Buchungen.
        self.window: tuple[Any, Any] = (None, None)
        # Auswahl der Lovelace-Filter je Wohnung: {"kanal", "zeitraum", "vergleich"}
        # (gesetzt von den select-Entitäten, die ihren Stand selbst wiederherstellen)
        self.selection: dict[int, dict[str, str]] = {}

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

    @property
    def checkout_buffer(self) -> int:
        """Puffer (min) nach einer in Smoobu angegebenen Abreisezeit."""
        return int(self.config_entry.options.get(CONF_CHECKOUT_BUFFER, DEFAULT_CHECKOUT_BUFFER))

    @property
    def payment_excluded_channels(self) -> list[str]:
        """Kanäle, deren Zahlung über das Portal läuft."""
        return list(
            self.config_entry.options.get(
                CONF_PAYMENT_EXCLUDED_CHANNELS, DEFAULT_PAYMENT_EXCLUDED_CHANNELS
            )
        )

    @property
    def commissions(self) -> dict[str, float]:
        """Provision in % je Kanal (Fallback, wenn Smoobu keine liefert)."""
        return dict(self.config_entry.options.get(CONF_COMMISSIONS, DEFAULT_COMMISSIONS))

    @property
    def commission_other(self) -> float:
        return float(self.config_entry.options.get(CONF_COMMISSION_OTHER, DEFAULT_COMMISSION_OTHER))

    @property
    def direct_channels(self) -> list[str]:
        return list(self.config_entry.options.get(CONF_DIRECT_CHANNELS, DEFAULT_DIRECT_CHANNELS))

    def costs(self, booking: dict[str, Any]) -> dict[str, Any]:
        """Kanalgruppe, Provision, Zahlungsgebühr und Netto einer Buchung."""
        return booking_costs(booking, self.commissions, self.commission_other, self.direct_channels)

    @property
    def history_years(self) -> int:
        """Wie viele Jahre vor dem laufenden für Auswertungen geladen werden."""
        return max(int(self.config_entry.options.get(CONF_HISTORY_YEARS, DEFAULT_HISTORY_YEARS)), 1)

    def records(self, apartment_id: int) -> list[dict[str, Any]]:
        """Aufbereitete Buchungsdatensätze (inkl. Stornos/Sperrzeiten) einer Wohnung."""
        if not self.data:
            return []
        return self.data.records.get(apartment_id, [])

    def release(self, booking: dict[str, Any]):
        """Freigabezeit einer Buchung (Abreisezeit + Puffer bzw. Standard-Check-out)."""
        return booking_release(booking, self.default_checkout, self.checkout_buffer)

    # ------------------------------------------------------------------
    async def _async_update_data(self) -> SmoobuData:
        """Wohnungen (24 h gecacht) + Buchungen im Zeitfenster laden."""
        previous = self.data or SmoobuData()
        try:
            apartments = await self._async_load_apartments(previous)
            bookings = await self._async_load_bookings()
            bookings = await self._async_enrich(bookings)
            revenue_bookings = await self._async_load_revenue_bookings()
            rates = await self._async_load_rates(apartments)
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

        # Umsatz je Wohnung und Monat (anteilig nach Nächten)
        today = dt_util.now().date()
        revenue: dict[int, dict[str, float]] = {}
        earned: dict[int, dict[str, float]] = {}
        g_nights: dict[int, dict[str, int]] = {}
        b_nights: dict[int, dict[str, int]] = {}
        rows: dict[int, list] = {}
        records: dict[int, list] = {}
        # Aktuellere Daten aus dem Buchungsfenster haben Vorrang (Detaildaten
        # wie Vorname); Umsatzabfrage ergänzt Historie, Stornos und Fernes.
        merged = {int(b.get("id") or 0): b for b in revenue_bookings}
        merged.update({int(b.get("id") or 0): {**merged.get(int(b.get("id") or 0), {}), **b} for b in bookings})
        for apt_id in apartments:
            apt_all = [b for b in merged.values() if (b.get("apartment") or {}).get("id") == apt_id]
            records[apt_id] = build_records(
                apt_all, self.costs, self.payment_excluded_channels, today
            )
            # Für alle bisherigen Umsatzwerte nur gültige Buchungen (ohne Stornos)
            items = [
                b
                for b in revenue_bookings
                if (b.get("apartment") or {}).get("id") == apt_id and not is_cancelled(b)
            ]
            revenue[apt_id] = revenue_by_month(items)
            earned[apt_id] = revenue_by_month(items, until=today)
            g_nights[apt_id] = nights_by_month(items)
            b_nights[apt_id] = nights_by_month(items, blocked=True)
            # Je Gastnacht Brutto/Provision/Gebühr für Direkt-vs-Portal-Auswertung
            rows[apt_id] = night_rows(
                items, self.commissions, self.commission_other, self.direct_channels
            )

        return SmoobuData(
            apartments=apartments,
            bookings=grouped,
            pii_available=pii,
            last_update=dt_util.utcnow(),
            last_event=previous.last_event,
            revenue=revenue,
            revenue_earned=earned,
            guest_nights=g_nights,
            blocked_nights=b_nights,
            rates=rates,
            last_message=previous.last_message,
            night_rows=rows,
            records=records,
        )

    async def _async_load_rates(
        self, apartments: dict[int, dict[str, Any]]
    ) -> dict[int, dict[str, dict[str, Any]]]:
        """Tagespreise der nächsten 60 Tage (gecacht 1 h, Fehler nicht fatal)."""
        now = dt_util.utcnow()
        if (
            self._rates_loaded
            and not self.force_revenue_refresh
            and now - self._rates_loaded < RATES_REFRESH
        ):
            return self._rates
        today = dt_util.now().date()
        end = today + timedelta(days=RATES_DAYS)
        rates: dict[int, dict[str, dict[str, Any]]] = {}
        for apt_id in apartments:
            try:
                rates[apt_id] = await self.client.get_rates(
                    apt_id, today.isoformat(), end.isoformat()
                )
            except SmoobuAuthError:
                raise
            except SmoobuError as err:
                # Preise sind Zusatzdaten – ohne sie läuft der Rest weiter.
                _LOGGER.debug("Tagespreise %s nicht ladbar: %s", apt_id, err)
                rates[apt_id] = self._rates.get(apt_id, {})
        self._rates = rates
        self._rates_loaded = now
        return rates

    async def async_fetch_last_message(self, reservation_id: int, sender: str | None) -> None:
        """Neueste Nachricht einer Buchung laden (nach Webhook „newMessage“)."""
        try:
            messages = await self.client.get_messages(reservation_id, True)
        except SmoobuError as err:
            _LOGGER.debug("Nachrichten zu Buchung %s nicht ladbar: %s", reservation_id, err)
            return
        if not messages or self.data is None:
            return
        latest = max(messages, key=lambda m: int(m.get("id") or 0))
        text = strip_html(latest.get("message") or latest.get("messageHtml") or latest.get("htmlMessage") or "")
        # Gast und Wohnung aus den geladenen Buchungen ergänzen
        booking = next(
            (
                b
                for items in self.data.bookings.values()
                for b in items
                if int(b.get("id") or 0) == int(reservation_id)
            ),
            {},
        )
        self.data.last_message = {
            "text": text,
            "betreff": latest.get("subject"),
            "absender": sender,
            "nachricht_id": latest.get("id"),
            "buchungs_id": reservation_id,
            "gast": guest_name(booking) if booking else None,
            "wohnung": (booking.get("apartment") or {}).get("name") if booking else None,
            "empfangen": dt_util.now().isoformat(),
        }
        self.async_update_listeners()

    async def _async_load_revenue_bookings(self) -> list[dict[str, Any]]:
        """Alle Buchungen für Umsatz und Auswertungen. Gecacht 1 h.

        Zeitraum: ab 01.01. vor `history_years` Jahren bis zum Ende der Vorschau,
        mindestens bis Ende Januar des Folgejahres (für „Folgemonat“ im Dezember).
        Sperrzeiten und Stornos inklusive – Stornos zählen nur für die Stornoquote,
        alle Umsatzwerte filtern sie wieder heraus.
        """
        now = dt_util.utcnow()
        if (
            self._revenue_loaded
            and not self.force_revenue_refresh
            and now - self._revenue_loaded < REVENUE_REFRESH
        ):
            return self._revenue_bookings
        today = dt_util.now().date()
        year = today.year
        days_ahead = int(self.config_entry.options.get(CONF_DAYS_AHEAD, DEFAULT_DAYS_AHEAD))
        until = max(f"{year + 1}-01-31", (today + timedelta(days=days_ahead)).isoformat())
        self._revenue_bookings = await self.client.get_reservations(
            departureFrom=f"{year - self.history_years}-01-02",  # mind. eine Nacht im Startjahr
            arrivalTo=until,
            showCancellation=True,
            includePriceElements=True,  # Hunde-Erkennung in den Datensätzen
        )
        self._revenue_loaded = now
        self.force_revenue_refresh = False
        return self._revenue_bookings

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
        """Buchung, deren Zeitraum (Check-in bis Freigabe) gerade läuft."""
        now = dt_util.now()
        for booking in self.bookings_for(apartment_id):
            if guests_only and is_blocked(booking):
                continue
            start = booking_start(booking, self.default_checkin)
            end = self.release(booking)
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

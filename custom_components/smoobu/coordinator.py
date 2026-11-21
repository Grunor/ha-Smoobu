"""DataUpdateCoordinator: holt Wohnungen und Buchungen zentral von Smoobu.

Ein Coordinator je Smoobu-Konto. Alle Entitäten lesen aus demselben
Datenstand → eine API-Abfrage pro Intervall statt einer pro Entität.
Der Webhook stößt zusätzlich sofort eine Aktualisierung an.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import SmoobuAuthError, SmoobuClient, SmoobuError
from .const import (
    EVENT_SMOOBU,
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
    CONF_HISTORY_SINCE,
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
from . import energie
from .const import CONF_CLEANING_WAGES
from .deckungsbeitrag import apply as db_apply
from .deckungsbeitrag import build_table as db_build_table
from .deckungsbeitrag import config_from_options as cost_config_from_options
from .empfehlung import from_options as price_config_from_options
from . import preisaktion
from .channels import booking_costs, night_rows
from .models import (
    PET_MESSAGE_KEY,
    SmoobuData,
    pet_hint,
    pet_match,
    pet_snippet,
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
PRICE_CHANGES_MAX = 30  # gespeicherte Preisänderungen für „Rückgängig“ (v1.18.0)


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
        # Antwortstatus je Buchung (v1.13.0): {reservation_id: (geladen_um, status)}.
        # Smoobu meldet „unbeantwortet“ nicht selbst → aus dem Verlauf abgeleitet und
        # 10 min gecacht; Webhook „newMessage“ und eigenes Senden verwerfen den Eintrag.
        self._msg_status: dict[int, tuple[Any, dict[str, Any]]] = {}
        # Hund aus Gastnachrichten (v1.15.3): {reservation_id: (geladen_um, Fundstelle | None)},
        # 12 h gecacht; neue Nachricht (Webhook) oder Abruf des Antwortstatus aktualisiert.
        self._pet_msg: dict[int, tuple[Any, str | None]] = {}
        client.on_message_sent = self.invalidate_message_status
        # v1.17.0: Abonnenten für „Antwortstatus geändert“ (Zähler „Nachrichten“ auf allen Geräten)
        self._msg_listeners: list[Callable[[], None]] = []
        # „Keine Antwort erforderlich“ (v1.14.0): {reservation_id (Text): Nachrichten-ID}.
        # Gemerkt wird die Gastnachricht, die bewusst unbeantwortet bleibt – schreibt der
        # Gast danach erneut (höhere ID), ist die Buchung wieder offen. Dauerhaft in .storage.
        self._no_reply_store: Store = Store(hass, 1, f"{DOMAIN}_ohne_antwort_{entry.entry_id}")
        self._no_reply: dict[str, int] | None = None  # None = noch nicht geladen
        # KI-Assistent (assistant.py), gesetzt in __init__.async_setup_entry
        self.assistant: Any = None
        self._energy = energie.EnergyData(hass)  # v1.19.0: Stundenwerte der Zähler (im Speicher)
        self.doorcodes: Any = None  # v1.19.0: Türcodes (tuercode.DoorCodes)
        self.bills: Any = None  # v1.19.0: Nebenkostenabrechnungen (nebenkosten.UtilityBills)
        self.cleaning: Any = None  # v1.19.0: Reinigungsboard (reinigung.CleaningBoard)
        self.notifier: Any = None  # v1.17.0: Benachrichtigungen (notifications.SmoobuNotifier)
        # Statistik-Werkbank (Teilschritte 3/4):
        # 1. Preis-Historie {apt_id: {datum: [preis, mindestaufenthalt]}} – Smoobu liefert Tagespreise
        #    nicht rückwirkend, deshalb wird bei jedem Preisabruf der Stand für heute und künftige Tage
        #    gemerkt; vergangene Tage bleiben eingefroren (= letzter bekannter Stand).
        self._price_store: Store = Store(hass, 1, f"{DOMAIN}_preis_historie_{entry.entry_id}")
        self._price_hist: dict[str, dict[str, list[Any]]] | None = None
        # 2. Antwortzeiten je Buchung {reservation_id: {"minuten": [...], "geladen": datum}}: einmaliger,
        #    gedrosselter Abruf aller Buchungen ab history_start (Entscheidung Betreiber: komplett ab 2020),
        #    danach stündlich nur neue/laufende Buchungen. Erster Lauf frühestens 10 min nach dem Start,
        #    damit der HA-Start nicht mit hunderten API-Anfragen belastet wird.
        self._resp_store: Store = Store(hass, 1, f"{DOMAIN}_antwortzeiten_{entry.entry_id}")
        # v1.18.0: Preisänderungen aus der Karte (für „Rückgängig“), neueste zuerst, max. PRICE_CHANGES_MAX
        self._changes_store: Store = Store(hass, 1, f"{DOMAIN}_preis_aenderungen_{entry.entry_id}")
        self._changes: list[dict[str, Any]] | None = None
        # v1.18.0: Aufgaben-Board – erledigte/verschobene Aufgaben (gemeinsam für alle Benutzer)
        self._tasks_store: Store = Store(hass, 1, f"{DOMAIN}_aufgaben_{entry.entry_id}")
        self._tasks: dict[str, dict[str, Any]] | None = None
        self._resp: dict[str, dict[str, Any]] | None = None
        self._resp_task: Any = None
        self._resp_last: Any = None
        self._started = dt_util.utcnow()

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

    @property
    def price_config(self):
        """v1.18.0: Kanal-Aufschläge, Genius und Provisionen für Bewertung & Empfehlung."""
        return price_config_from_options(self.config_entry.options, self.commissions, self.commission_other,
                                         self.direct_channels)

    def costs(self, booking: dict[str, Any]) -> dict[str, Any]:
        """Kanalgruppe, Provision, Zahlungsgebühr und Netto einer Buchung."""
        return booking_costs(booking, self.commissions, self.commission_other, self.direct_channels)

    @property
    def history_years(self) -> int:
        """Wie viele Jahre vor dem laufenden für Auswertungen geladen werden."""
        return max(int(self.config_entry.options.get(CONF_HISTORY_YEARS, DEFAULT_HISTORY_YEARS)), 1)

    @property
    def history_start(self) -> date:
        """Erster Tag, ab dem Buchungen für Auswertungen geladen werden.

        „Daten abrufen seit“ hat Vorrang vor „Jahre Historie“. Ein Datum nach dem 01.01. des
        Vorjahres wird auf diesen vorgezogen – Jahr- und Vorjahresvergleiche brauchen beides.
        """
        year = dt_util.now().year
        latest = date(year - 1, 1, 1)
        since = self.config_entry.options.get(CONF_HISTORY_SINCE)
        if since:
            try:
                return min(date.fromisoformat(str(since)[:10]), latest)
            except ValueError:
                _LOGGER.warning("Ungültiges Datum in „Daten abrufen seit“: %s – nutze „Jahre Historie“", since)
        return date(year - self.history_years, 1, 1)

    def records(self, apartment_id: int) -> list[dict[str, Any]]:
        """Aufbereitete Buchungsdatensätze (inkl. Stornos/Sperrzeiten) einer Wohnung."""
        if not self.data:
            return []
        return self.data.records.get(apartment_id, [])

    def apartment_code(self, apartment_id: Any) -> str:
        """Kürzel einer Wohnung (v1.17.0: eigenes aus den Optionen, sonst automatisch)."""
        from .codes import all_codes  # noqa: PLC0415 – vermeidet Importzyklus

        try:
            return all_codes(self.hass).get((self.config_entry.entry_id, int(apartment_id)), "?")
        except (TypeError, ValueError):
            return "?"

    def records_all(self) -> list[dict[str, Any]]:
        """Datensätze aller Wohnungen des Kontos."""
        if not self.data:
            return []
        return [r for items in self.data.records.values() for r in items]

    def release(self, booking: dict[str, Any]):
        """Freigabezeit einer Buchung (Abreisezeit + Puffer bzw. Standard-Check-out)."""
        return booking_release(booking, self.default_checkout, self.checkout_buffer)

    # ------------------------------------------------------------------
    async def _cleaning_costs(self, records: dict[int, list], cfg: Any) -> dict[Any, float]:
        """Reinigung je Buchung = Standardzeit × Stundenlohn der Person, die (laut Board) gereinigt hat bzw.
        zugewiesen ist. Ohne Board-Eintrag oder ohne eigenen Lohn: Standard-Stundenlohn (kein Eintrag nötig)."""
        board = getattr(self, "cleaning", None)
        wages = {str(k): float(v) for k, v in (self.config_entry.options.get(CONF_CLEANING_WAGES) or {}).items() if v}
        if board is None:
            return {}
        state = await board._load()  # noqa: SLF001
        out: dict[Any, float] = {}
        for items in records.values():
            for r in items:
                s = state.get(f"{r['id']}:{r['abreise']}") or {}
                who = s.get("gereinigt_von") or s.get("zugewiesen")
                # v1.19.0: gebuchte Dauer je Reinigung (sonst Standardzeit) × Lohn der Person (sonst Standardlohn)
                if who in wages or s.get("minuten"):
                    out[r["id"]] = wages.get(who, cfg.cleaning_wage) * float(s.get("minuten") or cfg.cleaning_minutes) / 60
        return out

    async def _async_update_data(self) -> SmoobuData:
        """Wohnungen (24 h gecacht) + Buchungen im Zeitfenster laden."""
        previous = self.data or SmoobuData()
        if self._price_hist is None:
            self._price_hist = dict(await self._price_store.async_load() or {})
        if self._resp is None:
            self._resp = dict(await self._resp_store.async_load() or {})
        try:
            apartments = await self._async_load_apartments(previous)
            bookings = await self._async_load_bookings()
            bookings = await self._async_enrich(bookings)
            await self._async_pet_messages(bookings)
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
        cost_tables: dict[int, Any] = {}
        cost_cfg = cost_config_from_options(self.config_entry.options)
        # Aktuellere Daten aus dem Buchungsfenster haben Vorrang (Detaildaten
        # wie Vorname); Umsatzabfrage ergänzt Historie, Stornos und Fernes.
        merged = {int(b.get("id") or 0): b for b in revenue_bookings}
        merged.update({int(b.get("id") or 0): {**merged.get(int(b.get("id") or 0), {}), **b} for b in bookings})
        for apt_id in apartments:
            apt_all = [b for b in merged.values() if (b.get("apartment") or {}).get("id") == apt_id]
            records[apt_id] = build_records(
                apt_all, self.costs, self.payment_excluded_channels, today
            )
            # v1.18.0: variable Kosten + Deckungsbeitrag je Buchung (Heizung skaliert auf die
            # Gästenächte des Bezugsjahres dieser Wohnung)
            cost_tables[apt_id] = db_build_table(records[apt_id], cost_cfg)
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

        # v1.19.0: Strom/Wasser/Heizung gemessen (Modus „zaehler“) oder konstant – danach DB je Buchung.
        # Fehler der Messung sind nie fatal: dann gelten die konstanten Werte.
        energy: dict[int, dict[str, Any]] = {}
        try:
            energy = await energie.measure_all(self.hass, self._energy, dict(self.config_entry.options), records,
                                           cost_cfg, self.default_checkin, self.default_checkout)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Smoobu: Stromkosten aus Messwerten nicht berechnet: %s", err)
        # v1.19.0: Reinigungskosten je Buchung nach Stundenlohn der Person aus dem Reinigungsboard
        cleaning_costs = await self._cleaning_costs(records, cost_cfg)
        for apt_id in apartments:
            db_apply(records[apt_id], cost_tables[apt_id], energy.get(apt_id), cleaning_costs)

        self._maybe_start_response_job()
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
            cost_tables=cost_tables,
            energy=energy,
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
        self._record_prices(rates, today)
        return rates

    # --- Statistik-Werkbank: Preis-Historie und Antwortzeiten ----------
    def _record_prices(self, rates: dict[int, dict[str, dict[str, Any]]], today: date) -> None:
        """Tagespreis + Mindestaufenthalt für heute und künftige Tage merken (vergangene bleiben)."""
        if self._price_hist is None:
            return
        iso_today = today.isoformat()
        for apt_id, days in rates.items():
            hist = self._price_hist.setdefault(str(apt_id), {})
            for day, value in (days or {}).items():
                if day >= iso_today and isinstance(value, dict):
                    hist[day] = [value.get("price"), value.get("min_length_of_stay")]
        self._price_store.async_delay_save(lambda: self._price_hist or {}, 30)

    # --- v1.18.0: Preise übernehmen / rückgängig -------------------------
    async def async_price_changes(self) -> list[dict[str, Any]]:
        if self._changes is None:
            self._changes = list(await self._changes_store.async_load() or [])
        return self._changes

    async def async_apply_prices(self, apartment_id: int, spec: dict[str, Any], *, user: str | None,
                                 dry_run: bool = False) -> dict[str, Any]:
        """Vorgabe der Karte anwenden: frische Preise holen, je Tag planen, schreiben, prüfen, merken."""
        today = dt_util.now().date()
        days = preisaktion.days_of(spec, today)
        if not days:
            raise ValueError("Keine Tage im gewählten Zeitraum (ab heute)")
        rates = await self.client.get_rates(apartment_id, days[0].isoformat(), days[-1].isoformat())
        result = preisaktion.plan(spec, rates, today)
        result["label"] = spec.get("label") or ""
        if dry_run or not result["tage"]:
            result["gespeichert"] = False
            return result
        await self.client.set_rate_operations(apartment_id, preisaktion.operations(result["tage"]))
        after = await self.client.get_rates(apartment_id, days[0].isoformat(), days[-1].isoformat())
        result["abweichend"] = preisaktion.verify(result["tage"], after)
        entry = {
            "id": f"{int(dt_util.utcnow().timestamp() * 1000)}",
            "zeit": dt_util.now().isoformat(timespec="seconds"),
            "benutzer": user,
            "wohnung_id": apartment_id,
            "label": result["label"],
            "tage": result["tage"],
            "rueckgaengig": None,
        }
        changes = await self.async_price_changes()
        changes.insert(0, entry)
        del changes[PRICE_CHANGES_MAX:]
        await self._changes_store.async_save(changes)
        result.update(gespeichert=True, aenderung_id=entry["id"])
        self._after_price_write(apartment_id, entry, "preise_geaendert", user)
        return result

    async def async_undo_prices(self, change_id: str, *, user: str | None) -> dict[str, Any]:
        """Eine gespeicherte Änderung zurücknehmen (alte Tageswerte wieder setzen, nur künftige Tage)."""
        changes = await self.async_price_changes()
        entry = next((c for c in changes if c["id"] == change_id), None)
        if entry is None:
            raise ValueError("Änderung nicht gefunden")
        if entry.get("rueckgaengig"):
            raise ValueError("Schon rückgängig gemacht")
        today = dt_util.now().date().isoformat()
        tage = [t for t in entry["tage"] if t["datum"] >= today]
        if not tage:
            raise ValueError("Alle Tage liegen in der Vergangenheit")
        apt = entry["wohnung_id"]
        await self.client.set_rate_operations(apt, preisaktion.operations(tage, restore=True))
        after = await self.client.get_rates(apt, tage[0]["datum"], tage[-1]["datum"])
        entry["rueckgaengig"] = {"zeit": dt_util.now().isoformat(timespec="seconds"), "benutzer": user}
        await self._changes_store.async_save(changes)
        self._after_price_write(apt, entry, "preise_zurueckgesetzt", user)
        return {"tage": len(tage), "abweichend": preisaktion.verify(tage, after, restore=True)}

    async def async_task_state(self) -> dict[str, dict[str, Any]]:
        """Erledigte/verschobene Aufgaben; abgelaufene „Später“ und Einträge > 90 Tage fallen weg."""
        if self._tasks is None:
            self._tasks = dict(await self._tasks_store.async_load() or {})
        now = dt_util.now()
        cutoff = (now - timedelta(days=90)).isoformat()
        stale = [k for k, v in self._tasks.items()
                 if v.get("zeit", "") < cutoff or (v.get("status") == "spaeter" and v.get("bis", "") <= now.isoformat())]
        for key in stale:
            self._tasks.pop(key, None)
        if stale:
            self._tasks_store.async_delay_save(lambda: self._tasks or {}, 5)
        return self._tasks

    async def async_set_task(self, key: str, action: str, user: str | None, days: int = 1) -> dict[str, Any]:
        """Aufgabe erledigen, um `days` Tage verschieben oder zurücksetzen (Schlüssel bestimmt die Karte)."""
        tasks = await self.async_task_state()
        now = dt_util.now()
        if action == "zuruecksetzen":
            tasks.pop(key, None)
        else:
            entry = {"status": action, "zeit": now.isoformat(timespec="seconds"), "benutzer": user}
            if action == "spaeter":
                entry["bis"] = (now + timedelta(days=days)).isoformat(timespec="seconds")
            tasks[key] = entry
        await self._tasks_store.async_save(tasks)
        return tasks

    def _after_price_write(self, apartment_id: int, entry: dict[str, Any], kind: str, user: str | None) -> None:
        # Tagespreise beim nächsten Abruf neu laden und sofort aktualisieren; Ereignis für Logbuch/Automationen
        self._rates_loaded = None
        self.hass.bus.async_fire(EVENT_SMOOBU, {
            "typ": kind, "wohnung_id": apartment_id, "label": entry["label"], "tage": len(entry["tage"]),
            "benutzer": user, "aenderung_id": entry["id"],
        })
        self.hass.async_create_task(self.async_request_refresh())

    def price_history(self, apartment_id: int) -> dict[str, list[Any]]:
        return (self._price_hist or {}).get(str(apartment_id), {})

    def rates_now(self, apartment_id: int) -> dict[str, dict[str, Any]]:
        return self._rates.get(int(apartment_id), {})

    @property
    def responses(self) -> dict[str, dict[str, Any]]:
        return self._resp or {}

    def _maybe_start_response_job(self) -> None:
        now = dt_util.utcnow()
        if self._resp_task is not None and not self._resp_task.done():
            return
        if now - self._started < timedelta(minutes=10):
            return
        if self._resp_last and now - self._resp_last < timedelta(hours=1):
            return
        self._resp_last = now
        self._resp_task = self.config_entry.async_create_background_task(
            self.hass, self.async_update_response_times(), f"{DOMAIN}_antwortzeiten"
        )

    async def async_update_response_times(self, delay: float = 1.5, limit: int | None = None) -> int:
        """Antwortzeiten nachladen: fehlende Buchungen + laufende/kürzliche (täglich neu). Gibt Anzahl zurück.

        Gedrosselt (eine Anfrage, dann `delay` s Pause), Fehler einzelner Buchungen werden übersprungen,
        bei Anmeldefehler bricht der Lauf ab. Zwischenstand wird alle 25 Buchungen gespeichert.
        """
        from .stats import message_counts, response_times  # noqa: PLC0415

        if self._resp is None:
            self._resp = dict(await self._resp_store.async_load() or {})
        today = dt_util.now().date()
        recent = (today - timedelta(days=14)).isoformat()
        start = self.history_start.isoformat()
        todo = []
        for r in self.records_all():
            if r["blockiert"] or not r["id"] or r["anreise"] < start:
                continue
            entry = self._resp.get(str(r["id"]))
            # v1.17.1: Einträge ohne Nachrichtenzähler („gast“) einmalig nachladen (Kommunikationsaufwand je Kanal)
            if entry is None or "gast" not in entry or (r["abreise"] >= recent and entry.get("geladen") != today.isoformat()):
                todo.append(r["id"])
        done = 0
        for rid in todo[:limit] if limit else todo:
            try:
                messages = await self.client.get_messages(int(rid), False)
            except SmoobuAuthError:
                break
            except SmoobuError as err:
                _LOGGER.debug("Antwortzeiten %s nicht ladbar: %s", rid, err)
                continue
            visible = self._visible(messages)
            self._resp[str(rid)] = {"minuten": response_times(visible), **message_counts(visible), "geladen": today.isoformat()}
            done += 1
            if done % 25 == 0:
                self._resp_store.async_delay_save(lambda: self._resp or {}, 1)
            if delay:
                await asyncio.sleep(delay)
        if done:
            self._resp_store.async_delay_save(lambda: self._resp or {}, 1)
        return done

    @staticmethod
    def _visible(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Nachrichten ohne interne Notizen (zählen weder als Gastnachricht noch als Antwort)."""
        return [m for m in messages if not (m.get("internal") or m.get("isInternal"))]

    @staticmethod
    def _is_guest(m: dict[str, Any] | None) -> bool:
        """type 1 = Gast → Gastgeber (Smoobu liefert teils Text, daher int())."""
        try:
            return bool(m) and int(m.get("type") or 0) == 1
        except (TypeError, ValueError):
            return False

    async def _async_no_reply(self) -> dict[str, int]:
        if self._no_reply is None:
            self._no_reply = dict(await self._no_reply_store.async_load() or {})
        return self._no_reply

    async def async_set_no_reply(self, reservation_id: int, done: bool = True) -> dict[str, Any]:
        """Buchung als „keine Antwort erforderlich“ markieren bzw. Markierung aufheben.

        Markiert wird die aktuell neueste Gastnachricht. Ein offener KI-Vorschlag zur
        Buchung wird dabei auf „ignoriert“ gesetzt (Push wird entfernt).
        """
        rid = int(reservation_id)
        store = await self._async_no_reply()
        if done:
            messages = self._visible(await self.client.get_messages(rid, False))
            guest = [m for m in messages if self._is_guest(m)]
            if not guest:
                raise SmoobuError("Keine Gastnachricht vorhanden")
            store[str(rid)] = max(int(m.get("id") or 0) for m in guest)
            if self.assistant is not None:
                await self.assistant.dismiss(rid)
        else:
            store.pop(str(rid), None)
        self._no_reply_store.async_delay_save(lambda: self._no_reply or {}, 2)
        self.invalidate_message_status(rid)
        return (await self.async_message_status([rid]))[rid]

    def add_message_listener(self, cb: Callable[[], None]) -> Callable[[], None]:
        """Rückruf, sobald sich ein Antwortstatus ändern kann (v1.17.0)."""
        self._msg_listeners.append(cb)
        return lambda: self._msg_listeners.remove(cb)

    def invalidate_message_status(self, reservation_id: int) -> None:
        """Antwortstatus einer Buchung neu laden lassen (neue/gesendete Nachricht, abgehakt)."""
        self._msg_status.pop(int(reservation_id), None)
        self._pet_msg.pop(int(reservation_id), None)
        # Alle offenen Dashboards zählen ihre offenen Nachrichten neu (leichtgewichtig, kein Neuladen)
        for cb in list(self._msg_listeners):
            cb()

    async def async_message_status(self, reservation_ids: list[int]) -> dict[int, dict[str, Any]]:
        """Je Buchung: Ist die letzte Nachricht vom Gast und noch unbeantwortet?

        „offen“ = die neueste nicht interne Nachricht hat type 1 (Gast → Gastgeber) und
        wurde nicht als „keine Antwort erforderlich“ markiert. Nachrichten an den Gast
        (type 2, auch automatische Smoobu-Nachrichten) schließen die Buchung immer.
        v1.14.0: Verlauf mit onlyRelatedToGuest=false laden – mit „true“ fehlten
        automatische Nachrichten an den Gast, die Buchung erschien fälschlich offen.
        Interne Notizen zählen nicht als Antwort. Abruf parallel (max. 4 gleichzeitig),
        Fehler einzelner Buchungen liefern {"fehler": …} statt den ganzen Befehl abzubrechen.
        """
        now = dt_util.utcnow()
        ttl = timedelta(minutes=10)
        sem = asyncio.Semaphore(4)
        out: dict[int, dict[str, Any]] = {}
        no_reply = await self._async_no_reply()

        async def one(rid: int) -> None:
            cached = self._msg_status.get(rid)
            if cached and now - cached[0] < ttl:
                out[rid] = cached[1]
                return
            async with sem:
                try:
                    messages = await self.client.get_messages(rid, False)
                except SmoobuError as err:
                    out[rid] = {"offen": False, "fehler": str(err)}
                    return
            visible = self._visible(messages)
            self._pet_msg[rid] = (now, self._pet_from_messages(visible))
            last = max(visible, key=lambda m: int(m.get("id") or 0)) if visible else None
            done_id = no_reply.get(str(rid))
            waiting = self._is_guest(last)
            # Bewusst ohne Antwort erledigt: gilt, solange keine neuere Gastnachricht kam
            dismissed = waiting and done_id is not None and int(last.get("id") or 0) <= done_id
            status = {
                "offen": waiting and not dismissed,
                "ohne_antwort": dismissed,
                "erledigt_id": done_id,
                "anzahl": len(visible),
                "letzte_zeit": (last or {}).get("createdAt") or (last or {}).get("created_at"),
                "letzte_typ": (last or {}).get("type"),
                # v1.15.0: Anfang der offenen Gastnachricht für „Wartet auf dich“ in der Übersicht
                "letzte_text": _snippet(last) if waiting else None,
            }
            self._msg_status[rid] = (now, status)
            out[rid] = status

        await asyncio.gather(*(one(int(r)) for r in reservation_ids))
        return out

    def _pet_from_messages(self, messages: list[dict[str, Any]]) -> str | None:
        """Hund/Haustier in Nachrichten VOM Gast (neueste zuerst); eigene Vorlagen zählen nicht."""
        guest = sorted((m for m in messages if self._is_guest(m)), key=lambda m: -int(m.get("id") or 0))
        for m in guest:
            text = strip_html(m.get("message") or m.get("messageHtml") or m.get("htmlMessage") or "")
            match = pet_match(text)
            if match:
                return f"Gastnachricht: …{pet_snippet(text, match)}…"
        return None

    async def _async_pet_messages(self, bookings: list[dict[str, Any]]) -> None:
        """Laufende und kommende Gästebuchungen (180 Tage) auf Hunde in Gastnachrichten prüfen.

        Nur wo Preise/Notizen noch keinen Hund zeigen. Je Aktualisierung höchstens 12
        Abrufe (3 parallel), Ergebnis 12 h gecacht → wenige Smoobu-Anfragen. Fehler sind
        nicht fatal: dann bleibt es bei der Erkennung aus Preisen und Notizen.
        """
        now = dt_util.utcnow()
        today = dt_util.now().date().isoformat()
        horizon = (dt_util.now().date() + timedelta(days=180)).isoformat()
        ttl = timedelta(hours=12)
        todo: list[dict[str, Any]] = []
        for b in sorted(bookings, key=lambda x: x.get("arrival") or ""):
            if is_blocked(b) or "cancel" in str(b.get("type") or "") or not b.get("id"):
                continue
            if (b.get("departure") or "") < today or (b.get("arrival") or "") > horizon:
                continue
            rid = int(b["id"])
            cached = self._pet_msg.get(rid)
            if cached and cached[1]:
                b[PET_MESSAGE_KEY] = cached[1]
            if pet_hint({k: v for k, v in b.items() if k != PET_MESSAGE_KEY}):
                continue  # schon aus Preisen/Notizen bekannt
            if not cached or now - cached[0] > ttl:
                todo.append(b)
        sem = asyncio.Semaphore(3)

        async def one(b: dict[str, Any]) -> None:
            rid = int(b["id"])
            async with sem:
                try:
                    messages = await self.client.get_messages(rid, False)
                except SmoobuAuthError:
                    raise
                except Exception as err:  # noqa: BLE001 – Zusatzinfo, darf das Update nie abbrechen
                    _LOGGER.debug("Nachrichten %s für Hunde-Erkennung nicht ladbar: %s", rid, err)
                    return
            hint = self._pet_from_messages(self._visible(messages))
            self._pet_msg[rid] = (now, hint)
            if hint:
                b[PET_MESSAGE_KEY] = hint

        await asyncio.gather(*(one(b) for b in todo[:12]))

    async def async_fetch_last_message(self, reservation_id: int, sender: str | None) -> None:
        """Neueste Gästenachricht einer Buchung laden (nach Webhook „newMessage“).

        v1.14.0: nur Nachrichten VOM Gast (type 1). Eigene Nachrichten an den Gast
        (auch automatische) ändern den Sensor „Letzte Gästenachricht“ nicht mehr.
        """
        self.invalidate_message_status(reservation_id)
        if sender == "host":
            return  # Webhook meldet eine eigene Nachricht → keine Gästenachricht
        try:
            messages = await self.client.get_messages(reservation_id, False)
        except SmoobuError as err:
            _LOGGER.debug("Nachrichten zu Buchung %s nicht ladbar: %s", reservation_id, err)
            return
        guest = [m for m in self._visible(messages) if self._is_guest(m)]
        if not guest or self.data is None:
            return
        latest = max(guest, key=lambda m: int(m.get("id") or 0))
        prev = self.data.last_message or {}
        if prev.get("nachricht_id") == latest.get("id"):
            return  # unverändert (z. B. Webhook zu eigener Antwort ohne sender-Angabe)
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
            "absender": "guest",
            "nachricht_id": latest.get("id"),
            "buchungs_id": reservation_id,
            "gast": guest_name(booking) if booking else None,
            "wohnung": (booking.get("apartment") or {}).get("name") if booking else None,
            "empfangen": dt_util.now().isoformat(),
        }
        self.async_update_listeners()

    async def _async_load_revenue_bookings(self) -> list[dict[str, Any]]:
        """Alle Buchungen für Umsatz und Auswertungen. Gecacht 1 h.

        Zeitraum: ab `history_start` („Daten abrufen seit“ bzw. 01.01. vor `history_years`
        Jahren) bis zum Ende der Vorschau,
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
            # Abreise frühestens am Folgetag = mindestens eine Nacht ab dem Starttag
            departureFrom=(self.history_start + timedelta(days=1)).isoformat(),
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


def _snippet(message: dict[str, Any] | None, limit: int = 220) -> str | None:
    """Erste Zeilen einer Nachricht ohne HTML und ohne zitierten E-Mail-Verlauf (v1.15.0)."""
    if not message:
        return None
    from .models import strip_html  # spät importiert: models importiert nichts aus dem Coordinator

    text = strip_html(message.get("message") or message.get("messageHtml") or message.get("htmlMessage") or "")
    for marker in ("-----", "Am ", "On ", "Von meinem", "Sent from"):
        cut = text.find("\n" + marker)
        if cut > 20:
            text = text[:cut]
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + " …"

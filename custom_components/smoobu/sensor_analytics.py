"""Sensoren für Kanal-Auswertung, Auswahl-Filter und Jahresprognose (ab v1.7.0).

- Kanal-Sensoren: ein Sensor je Kanal (Portale UND Direktkanäle), entsteht
  automatisch, sobald ein Kanal in den Buchungen vorkommt. Zustand = Brutto
  laufendes Jahr, Attribute = alle Kennzahlen für Jahr, bis heute, Vorjahr,
  Monat … plus Monatswerte.
- Auswertungs-Sensoren: richten sich nach den drei Auswahl-Entitäten
  (select: Kanal, Zeitraum, Vergleich). So lassen sich in Lovelace Filter
  ohne Templates bauen: Auswahl ändern → Kacheln zeigen sofort die neuen Werte.
- Prognose Jahresende: gebucht + Nachbuchungen wie im Vorjahr.

Rechenaufwand: Alle Werte kommen aus `analytics.analyze()`. Ergebnisse werden
je Datenstand zwischengespeichert, damit 20+ Entitäten nicht dieselbe
Auswertung mehrfach rechnen.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import callback
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .analytics import (
    SEL_ALL,
    analyze,
    analyze_with_compare,
    change,
    channels_of,
    forecast_year,
    period_range,
)
from .coordinator import SmoobuCoordinator
from .entity import SmoobuEntity

C = SmoobuCoordinator

DEFAULT_SELECTION = {"kanal": SEL_ALL, "zeitraum": "jahr_bis_heute", "vergleich": "vorjahr"}

# Große Attribute nicht in die Datenbank schreiben (nur aktueller Zustand nötig)
_BIG = frozenset(
    {
        "jahr", "bis_heute", "vorjahr", "vorjahr_bis_heute", "monat", "vormonat", "folgemonat",
        "vorjahresmonat", "letzte_12_monate", "monate", "monate_netto", "monate_vorjahr",
        "monate_vorjahr_netto", "kanaele", "reihe", "vergleich", "auswertung",
    }
)


# ---------------------------------------------------------------------------
# Zwischenspeicher je Datenstand
# ---------------------------------------------------------------------------
def cached(c: C, key: tuple, fn: Callable[[], Any]) -> Any:
    """Ergebnis je Datenstand + Tag + Auswahl merken (neuer Abruf → neu rechnen)."""
    stamp = (id(c.data), dt_util.now().date())
    store = c.__dict__.setdefault("_analytics_cache", {})
    if store.get("_stamp") != stamp:
        store.clear()
        store["_stamp"] = stamp
    if key not in store:
        store[key] = fn()
    return store[key]


def _today() -> date:
    return dt_util.now().date()


def selection(c: C, apt: int) -> dict[str, str]:
    return {**DEFAULT_SELECTION, **c.selection.get(apt, {})}


def _strip(result: dict[str, Any]) -> dict[str, Any]:
    """Kennzahlen ohne Kanaltabelle/Reihe (für verschachtelte Attribute)."""
    return {k: v for k, v in result.items() if k not in ("kanaele", "reihe")}


# ---------------------------------------------------------------------------
# Kanal-Sensor
# ---------------------------------------------------------------------------
def channel_stats(c: C, apt: int, channel: str) -> dict[str, Any]:
    def build() -> dict[str, Any]:
        recs = c.records(apt)
        today = _today()
        out: dict[str, Any] = {}
        for key, period in (
            ("jahr", "jahr"),
            ("bis_heute", "jahr_bis_heute"),
            ("vorjahr", "vorjahr"),
            ("monat", "monat"),
            ("vormonat", "vormonat"),
            ("folgemonat", "folgemonat"),
            ("letzte_12_monate", "letzte_12_monate"),
        ):
            out[key] = _strip(analyze(recs, *period_range(period, today), channel, series=False))
        # Vorjahr bis zum gleichen Stichtag und Vorjahresmonat über den Vergleich
        ytd = analyze_with_compare(recs, *period_range("jahr_bis_heute", today), channel, "vorjahr", False)
        out["vorjahr_bis_heute"] = _strip(ytd["vergleich"])
        mon = analyze_with_compare(recs, *period_range("monat", today), channel, "vorjahr", False)
        out["vorjahresmonat"] = _strip(mon["vergleich"])
        year = analyze(recs, date(today.year, 1, 1), date(today.year + 1, 1, 1), channel)
        prev = analyze(recs, date(today.year - 1, 1, 1), date(today.year, 1, 1), channel)
        out["monate"] = dict(zip(year["reihe"]["labels"], year["reihe"]["brutto"], strict=True))
        out["monate_netto"] = dict(zip(year["reihe"]["labels"], year["reihe"]["netto"], strict=True))
        out["monate_vorjahr"] = dict(zip(prev["reihe"]["labels"], prev["reihe"]["brutto"], strict=True))
        out["monate_vorjahr_netto"] = dict(zip(prev["reihe"]["labels"], prev["reihe"]["netto"], strict=True))
        out["veraenderung_bis_heute_prozent"] = ytd["veraenderung_prozent"]
        out["prognose_jahr"] = forecast_year(recs, today, channel)
        return out

    return cached(c, ("kanal", apt, channel), build)


class SmoobuChannelSensor(SmoobuEntity, SensorEntity):
    """Umsatz und Kennzahlen eines Kanals (Portal oder Direktkanal)."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2
    _unrecorded_attributes = _BIG

    def __init__(self, coordinator: C, apartment_id: int, channel: str, group: str | None, currency: str) -> None:
        super().__init__(coordinator, apartment_id, "kanal")
        # unique_id je Kanal (Basisklasse setzt nur den Schlüssel „kanal“)
        self._attr_unique_id = f"{self._attr_unique_id}_{slugify(channel)}"
        self._attr_translation_placeholders = {"kanal": channel}
        self._attr_native_unit_of_measurement = currency
        self._channel = channel
        self._attr_icon = "mdi:home-account" if group == "Direkt" else "mdi:web"

    @property
    def last_reset(self) -> datetime:
        return dt_util.start_of_local_day().replace(month=1, day=1)

    @property
    def native_value(self) -> float:
        return channel_stats(self.coordinator, self.apartment_id, self._channel)["jahr"]["brutto"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        s = channel_stats(self.coordinator, self.apartment_id, self._channel)
        y = s["jahr"]
        flat = {
            "kanal": self._channel,
            "gruppe": next(
                (ch["gruppe"] for ch in channels_of(self.coordinator.records(self.apartment_id))
                 if ch["name"] == self._channel),
                None,
            ),
        }
        # Wichtigste Jahreswerte flach (für Kacheln: attribute: …)
        for key in (
            "netto", "kosten", "kostenquote_prozent", "provision", "zahlungsgebuehren", "naechte",
            "auslastung_prozent", "buchungen", "stornos", "stornoquote_prozent", "brutto_pro_nacht",
            "netto_pro_nacht", "aufenthalt_schnitt", "personen_schnitt", "vorlauf_schnitt",
            "preis_pro_buchung", "hunde",
        ):
            flat[key] = y.get(key)
        flat["bis_heute_brutto"] = s["bis_heute"]["brutto"]
        flat["bis_heute_netto"] = s["bis_heute"]["netto"]
        flat["vorjahr_bis_heute_brutto"] = s["vorjahr_bis_heute"]["brutto"]
        flat["veraenderung_vorjahr_bis_heute_prozent"] = s["veraenderung_bis_heute_prozent"]["brutto"]
        flat["monat_brutto"] = s["monat"]["brutto"]
        flat["prognose_jahr"] = s["prognose_jahr"]["prognose"]
        return {**flat, **{k: v for k, v in s.items() if k != "prognose_jahr"}}


@callback
def channel_entity_adder(
    coordinator: C, add: Callable[[list[SensorEntity]], None], currency: Callable[[int], str]
) -> Callable[[], None]:
    """Neue Kanäle zur Laufzeit erkennen und ihre Sensoren anlegen."""
    known: set[tuple[int, str]] = set()

    @callback
    def check() -> None:
        new: list[SensorEntity] = []
        for apt in coordinator.data.apartments if coordinator.data else {}:
            for ch in channels_of(coordinator.records(apt)):
                if (apt, ch["name"]) not in known:
                    known.add((apt, ch["name"]))
                    new.append(SmoobuChannelSensor(coordinator, apt, ch["name"], ch["gruppe"], currency(apt)))
        if new:
            add(new)

    check()
    return coordinator.async_add_listener(check)


# ---------------------------------------------------------------------------
# Auswertung nach Auswahl
# ---------------------------------------------------------------------------
def selected(c: C, apt: int) -> dict[str, Any]:
    sel = selection(c, apt)

    def build() -> dict[str, Any]:
        recs = c.records(apt)
        first = min((date.fromisoformat(r["anreise"]) for r in recs), default=None)
        start, end = period_range(sel["zeitraum"], _today(), first)
        result = analyze_with_compare(recs, start, end, sel["kanal"], sel["vergleich"])
        result["auswahl"] = dict(sel)
        return result

    return cached(c, ("auswahl", apt, sel["kanal"], sel["zeitraum"], sel["vergleich"]), build)


@dataclass(frozen=True, kw_only=True)
class SelectionSensorDescription:
    key: str
    field: str
    icon: str
    device_class: SensorDeviceClass | None = None
    unit: str | None = None  # "currency" = Währung der Wohnung
    percent_points: bool = False  # Veränderung in Prozentpunkten statt %


SELECTION_SENSORS: tuple[SelectionSensorDescription, ...] = (
    SelectionSensorDescription(key="auswertung_brutto", field="brutto", icon="mdi:cash-multiple",
                               device_class=SensorDeviceClass.MONETARY, unit="currency"),
    SelectionSensorDescription(key="auswertung_netto", field="netto", icon="mdi:cash-check",
                               device_class=SensorDeviceClass.MONETARY, unit="currency"),
    SelectionSensorDescription(key="auswertung_kosten", field="kosten", icon="mdi:hand-coin",
                               device_class=SensorDeviceClass.MONETARY, unit="currency"),
    SelectionSensorDescription(key="auswertung_kostenquote", field="kostenquote_prozent", icon="mdi:percent",
                               unit=PERCENTAGE, percent_points=True),
    SelectionSensorDescription(key="auswertung_naechte", field="naechte", icon="mdi:weather-night"),
    SelectionSensorDescription(key="auswertung_auslastung", field="auslastung_prozent", icon="mdi:calendar-check",
                               unit=PERCENTAGE, percent_points=True),
    SelectionSensorDescription(key="auswertung_buchungen", field="buchungen", icon="mdi:book-open-variant"),
    SelectionSensorDescription(key="auswertung_stornoquote", field="stornoquote_prozent", icon="mdi:book-cancel",
                               unit=PERCENTAGE, percent_points=True),
    SelectionSensorDescription(key="auswertung_netto_pro_nacht", field="netto_pro_nacht", icon="mdi:cash-clock",
                               device_class=SensorDeviceClass.MONETARY, unit="currency"),
    SelectionSensorDescription(key="auswertung_aufenthalt", field="aufenthalt_schnitt", icon="mdi:bed-clock",
                               unit=UnitOfTime.DAYS),
    SelectionSensorDescription(key="auswertung_vorlauf", field="vorlauf_schnitt", icon="mdi:calendar-arrow-right",
                               unit=UnitOfTime.DAYS),
    SelectionSensorDescription(key="auswertung_personen", field="personen_schnitt", icon="mdi:account-group"),
    SelectionSensorDescription(key="auswertung_direktanteil", field="direktanteil_prozent", icon="mdi:chart-donut",
                               unit=PERCENTAGE, percent_points=True),
)


class SmoobuSelectionSensor(SmoobuEntity, SensorEntity):
    """Eine Kennzahl für die aktuelle Auswahl (Kanal, Zeitraum, Vergleich)."""

    _unrecorded_attributes = _BIG

    def __init__(self, coordinator: C, apartment_id: int, desc: SelectionSensorDescription, currency: str) -> None:
        super().__init__(coordinator, apartment_id, desc.key)
        self._desc = desc
        self._attr_icon = desc.icon
        self._attr_device_class = desc.device_class
        self._attr_native_unit_of_measurement = currency if desc.unit == "currency" else desc.unit
        if desc.device_class == SensorDeviceClass.MONETARY:
            self._attr_suggested_display_precision = 2
        elif desc.unit in (PERCENTAGE, UnitOfTime.DAYS):
            self._attr_suggested_display_precision = 1

    @property
    def native_value(self) -> Any:
        return selected(self.coordinator, self.apartment_id).get(self._desc.field)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        r = selected(self.coordinator, self.apartment_id)
        cmp = r.get("vergleich") or {}
        field = self._desc.field
        attrs: dict[str, Any] = {
            **r["auswahl"],
            "von": r["von"],
            "bis": r["bis"],
            "vergleich_von": cmp.get("von"),
            "vergleich_bis": cmp.get("bis"),
            "vergleichswert": cmp.get(field),
        }
        if self._desc.percent_points:
            attrs["veraenderung_punkte"] = (
                round(r[field] - cmp[field], 1)
                if r.get(field) is not None and cmp.get(field) is not None else None
            )
        else:
            attrs["veraenderung_prozent"] = change(r.get(field), cmp.get(field))
        if self._desc.key == "auswertung_brutto":
            # Vollständige Auswertung einmal am Brutto-Sensor (Kanaltabelle, Reihe, Vergleich)
            attrs["auswertung"] = {k: v for k, v in r.items() if k not in ("vergleich", "auswahl")}
            attrs["vergleich"] = {k: v for k, v in cmp.items() if k != "kanaele"} if cmp else None
            attrs["kanaele"] = r["kanaele"]
        if self._desc.key == "auswertung_buchungen":
            attrs["stornos"] = r.get("stornos")
            attrs["hunde"] = r.get("hunde")
        if self._desc.key == "auswertung_vorlauf":
            attrs["median"] = r.get("vorlauf_median")
        return attrs


# ---------------------------------------------------------------------------
# Prognose Jahresende
# ---------------------------------------------------------------------------
class SmoobuForecastSensor(SmoobuEntity, SensorEntity):
    """Prognose Jahresumsatz (brutto) = gebucht + Nachbuchungen wie im Vorjahr."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = 0
    _attr_icon = "mdi:chart-timeline-variant-shimmer"

    def __init__(self, coordinator: C, apartment_id: int, currency: str) -> None:
        super().__init__(coordinator, apartment_id, "prognose_jahr")
        self._attr_native_unit_of_measurement = currency

    def _data(self) -> dict[str, Any]:
        c, apt = self.coordinator, self.apartment_id
        return cached(c, ("prognose", apt), lambda: forecast_year(c.records(apt), _today()))

    @property
    def native_value(self) -> float:
        return self._data()["prognose"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self._data()
        c, apt = self.coordinator, self.apartment_id
        today = _today()
        prev = cached(
            c, ("vorjahr_gesamt", apt),
            lambda: analyze(c.records(apt), *period_range("vorjahr", today), series=False),
        )
        return {
            **d,
            "vorjahr_gesamt": prev["brutto"],
            "veraenderung_vorjahr_prozent": change(d["prognose"], prev["brutto"]),
        }

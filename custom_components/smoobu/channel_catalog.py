"""Kanal-Auswahl für Einstellungen und Options-Dialog (v1.18.0).

Smoobu bietet keinen API-Endpunkt „angebundene Kanäle“. Die Doku enthält nur die
Tabelle aller Smoobu-Kanäle (ID → Name, Abschnitt „Channels“). Welche Kanäle ein
Konto wirklich nutzt, zeigen nur die Buchungen. Deshalb setzt sich die Auswahl aus
drei Quellen zusammen (Reihenfolge = Anzeige im Dropdown):

1. Kanäle mit Buchungen: alle geladenen Buchungen (ab „Daten abrufen seit“, inkl.
   Stornos und künftiger Buchungen), sortiert nach Anzahl
2. In den Einstellungen genutzte Kanäle: Provisionen, Direktkanäle, „Zahlung über
   das Portal“, Preisaufschläge (z. B. ein angebundenes Portal ohne bisherige Buchung)
3. Smoobu-Katalog: alle übrigen Kanäle aus der Smoobu-Doku

Namen werden ohne Groß-/Kleinschreibung abgeglichen (wie in channels.py). Ein Name
erscheint nur einmal, in der ersten zutreffenden Gruppe. Sperr-Kanäle fallen weg.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

# Smoobu-Kanaltabelle laut API-Doku (docs.smoobu.com, Abschnitt „Channels“), Stand 11/2026.
# ID = Kanaltyp (`channel.channel_id` in der Buchung). Die Namen in den Buchungen
# (`channel.name`) können abweichen, z. B. „Website“ statt „Homepage“. Deshalb haben
# Namen aus Buchungen immer Vorrang, der Katalog dient nur zum Ergänzen.
SMOOBU_CHANNEL_CATALOG: dict[int, str] = {
    1: "Airbnb iCal", 2: "Mowitania", 11: "Blocked channel", 13: "Direct booking", 14: "Booking.com",
    15: "Ferienwohnung24 Berlin", 16: "9Flats", 17: "Only Apartments", 18: "Expedia", 19: "Wimdu",
    20: "HouseTrip", 21: "Oh Berlin", 22: "Travanto Ical", 23: "FeWo-direkt / HomeAway", 24: "Tripadvisor",
    25: "Roomorama", 26: "Red Apple Apartments", 27: "Rentxpress", 28: "VRBO / HomeAway",
    29: "Traum-Ferienwohnungen (ical)", 30: "Vacation Apartments (ical)", 31: "Ferienwohnungen.de",
    32: "Waytostay", 33: "Bedandbreakfast.eu", 34: "BedyCasa", 35: "Ebab", 36: "Alterkeys", 37: "Bemate",
    38: "VacationRentals.com / HomeAway", 39: "AlwaysOnVacation", 40: "Misterbnb", 41: "RentalHouses",
    42: "HolidayRentals.com", 43: "France-Voyage.com", 44: "MorningCroissant", 45: "Flat4day / Go-fewo",
    46: "Abritel / HomeAway", 47: "Individueller iCal-Kanal 1", 48: "Individueller iCal-Kanal 2",
    49: "Individueller iCal-Kanal 3", 50: "HomeAway", 51: "e-domizil/atraveo", 52: "E-domizil Ical",
    53: "Bungalow.net", 54: "Hundeurlaub.de", 55: "BAYregio", 56: "Ferienhausmiete.de", 57: "Homelidays",
    58: "Feratel Deskline", 59: "Feries.com", 60: "Casevacanza.it", 61: "HBook Booking System",
    62: "Pinpoint Booking System", 63: "Spain Holiday", 64: "Holidaylettings", 65: "Flipkey", 66: "Intobis",
    67: "HRS Destination / ImWeb", 68: "Agoda", 69: "RoomCity", 70: "Homepage", 71: "Agriturismo.it",
    72: "Ownersdirect.co.uk", 73: "MWFerienwohnungen", 74: "Airbnb", 75: "Prodess", 76: "Bergfex",
    77: "Tourist-online.de", 78: "Bellevue Ferienhaus", 79: "Contao", 80: "Traum-Ferienwohnungen",
    81: "Ferienhausmarkt.com", 82: "Rentahouseboat.com", 83: "Bed-and-breakfast.it", 84: "Tomas",
    85: "Landreise.de", 86: "Micazu.nl", 87: "apartment.at", 88: "Pura Vida Travel / ORAmap",
    89: "Canada Stays", 90: "Blocked channel (HRS)", 91: "Feriwa.com", 93: "Motopress Booking Plugin",
    94: "Individual iCal - 4", 95: "Individual iCal - 5", 96: "Individual iCal - 6", 97: "Individual iCal - 7",
    98: "wpestate/wprentals Plugin", 99: "Beds 24", 100: "Bauernhofurlaub.de", 101: "Landsichten",
    102: "urlaub-in-florida.net", 103: "HRS Destination / ImWeb 2", 104: "HRS Destination / ImWeb 3",
    105: "Bodenseeferien", 106: "Lohospo", 107: "Bodensee.de", 108: "Optimale Präsentation",
    109: "Trip.com / Ctrip", 110: "Blocked channel auto", 111: "Open Pro", 112: "Individual iCal - 8",
    113: "Individual iCal - 9", 114: "Individual iCal - 10", 115: "Soho Hotel Plugin", 116: "Travanto",
    118: "E-domizil API", 119: "Safarinow.com", 120: "Individueller iCal-Kanal 11",
    121: "Individueller iCal-Kanal 12", 122: "Individueller iCal-Kanal 13", 123: "VRBO / HomeAway 1",
    124: "VRBO / HomeAway 2", 125: "VRBO / HomeAway 3", 126: "VRBO / HomeAway 4", 127: "VRBO / HomeAway 5",
    128: "VRBO / HomeAway 6", 129: "VRBO / HomeAway 7", 130: "VRBO / HomeAway 8", 131: "VRBO / HomeAway 9",
    132: "VRBO / HomeAway 10", 133: "HRS Destination / ImWeb 4", 134: "HRS Destination / ImWeb 5",
    135: "HRS Destination / ImWeb 6", 136: "HRS Destination / ImWeb 7", 137: "HRS Destination / ImWeb 8",
    138: "MonsieurChalets", 139: "Individueller iCal-Kanal 14", 140: "Individueller iCal-Kanal 15",
    141: "Individueller iCal-Kanal 16", 142: "Individueller iCal-Kanal 17", 143: "Individueller iCal-Kanal 18",
    144: "HomeToGo", 145: "BestFewo", 147: "HRS Destination / ImWeb 9", 148: "HRS Destination / ImWeb 10",
    149: "HRS Destination / ImWeb 11", 150: "HRS Destination / ImWeb 12", 151: "HRS Destination / ImWeb 13",
    152: "HRS Destination / ImWeb 14", 153: "HRS Destination / ImWeb 15", 154: "HRS Destination / ImWeb 16",
    155: "HRS Destination / ImWeb 17", 156: "HRS Destination / ImWeb 18", 158: "Nature House",
    169: "Casas Rurales",
}

# Gängige Namen, die in Buchungen so ankommen, auch wenn der Katalog sie anders nennt.
# Stehen in der Gruppe „Smoobu-Katalog“ ganz vorne (Bestandsliste vor v1.18.0).
COMMON_CHANNELS = ["Airbnb", "Booking.com", "FeWo-direkt", "Expedia", "Vrbo", "HomeToGo", "Direct booking", "Website"]


def is_blocked_channel(name: str) -> bool:
    """Sperr-Kanäle (Blocked channel …, Blockiert) sind keine Vertriebskanäle."""
    low = name.casefold()
    return low.startswith("blocked") or low == "blockiert"


def channel_choices(records: Iterable[dict[str, Any]], configured: Iterable[str]) -> dict[str, Any]:
    """Kanal-Auswahl in drei Gruppen, ohne Doppelte (Abgleich ohne Groß-/Kleinschreibung).

    records: aufbereitete Buchungsdatensätze aller Wohnungen (analytics, Felder kanal/blockiert/anreise)
    configured: Kanalnamen aus den Optionen (Provisionen, Direktkanäle, Portal-Zahlung, Aufschläge)
    Rückgabe: {"buchungen": [{name, buchungen, letzte}], "eingestellt": [...], "katalog": [...], "alle": [...]}
    """
    seen: set[str] = set()

    def take(name: Any) -> str | None:
        text = str(name or "").strip()
        if not text or is_blocked_channel(text) or text.casefold() in seen:
            return None
        seen.add(text.casefold())
        return text

    # 1) Buchungen: Anzahl (inkl. Stornos, ohne Sperrzeiten) und letzte Anreise je Kanal
    stats: dict[str, dict[str, Any]] = {}
    for r in records:
        if r.get("blockiert"):
            continue
        name = str(r.get("kanal") or "").strip()
        if not name or is_blocked_channel(name):
            continue
        s = stats.setdefault(name.casefold(), {"name": name, "buchungen": 0, "letzte": None})
        s["buchungen"] += 1
        if r.get("anreise") and (s["letzte"] is None or r["anreise"] > s["letzte"]):
            s["letzte"] = r["anreise"]
    booked = []
    for s in sorted(stats.values(), key=lambda s: (-s["buchungen"], s["name"].casefold())):
        if take(s["name"]):
            booked.append(s)

    # 2) In den Einstellungen genutzte Kanäle (Reihenfolge wie eingetragen)
    settings = [n for n in (take(c) for c in configured) if n]

    # 3) Katalog: gängige Namen zuerst, dann alle Smoobu-Kanäle alphabetisch
    rest = sorted(set(SMOOBU_CHANNEL_CATALOG.values()), key=str.casefold)
    catalog = [n for n in (take(c) for c in [*COMMON_CHANNELS, *rest]) if n]

    return {
        "buchungen": booked,
        "eingestellt": settings,
        "katalog": catalog,
        "alle": [s["name"] for s in booked] + settings + catalog,
    }


def configured_channels(options: dict[str, Any], *groups: Any) -> list[str]:
    """Alle Kanalnamen, die in den Optionen vorkommen (Schlüssel von dicts, Einträge von Listen)."""
    out: list[str] = []
    for group in groups:
        value = options.get(group) if isinstance(group, str) else group
        names = list(value.keys()) if isinstance(value, dict) else list(value or [])
        out.extend(str(n) for n in names)
    return out

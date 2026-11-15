"""Erfundene Demodaten für die README-Screenshots (ab v1.14.0).

Zweck: Die Screenshots sollen die echten Karten mit echten Berechnungen zeigen,
aber keinerlei echte Gäste-, Umsatz- oder Nachrichtendaten. Deshalb erzeugt
dieses Modul eine komplett erfundene Ferienwohnung („Ferienwohnung Demo“) mit
drei Jahren Buchungen und ersetzt den Smoobu-API-Client durch `DemoClient`.

- Deterministisch (fester Zufallsstartwert) → bei jedem Lauf gleiche Bilder.
- Alle Datumswerte relativ zu „heute“ → Screenshots wirken immer aktuell.
- Namen, E-Mails (example.com), Telefonnummern (Fiktivbereich) und Texte erfunden.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

APT_ID = 4711
APT = {"id": APT_ID, "name": "Ferienwohnung Demo"}
CHANNELS = {
    "Airbnb": 101,
    "Booking.com": 102,
    "Direct booking": 103,
    "Website": 104,
    "FeWo-direkt": 105,
}
BLOCKED = {"id": 199, "name": "Blocked channel"}
FIRST = ["Jana", "Lukas", "Sophie", "Felix", "Marie", "Jonas", "Lea", "Paul", "Emma", "Ben", "Clara", "Noah",
         "Hanna", "Elias", "Lina", "Moritz", "Ida", "Anton", "Greta", "Theo", "Mila", "Jakob", "Frieda", "Oskar"]
LAST = ["Winter", "Berg", "Sommer", "Brandt", "Lindner", "Vogel", "Kraus", "Hoffmann", "Seidel", "Engel",
        "Roth", "Busch", "Krüger", "Lorenz", "Haas", "Peters", "Graf", "Albrecht", "Franke", "Stein"]


# Namen des festen Szenarios (kommen in Zufallsbuchungen nicht vor)
FIXED = {"Jana Winter", "Lukas Berg", "Sophie Sommer", "Felix Brandt", "Marie Lindner", "Jonas Vogel",
         "Lea Kraus", "Paul Hoffmann", "Emma Seidel", "Ben Engel"}


def _season_price(d: date) -> int:
    """Grundpreis je Nacht nach Saison (Sommer/Weihnachten teurer)."""
    if d.month in (7, 8) or (d.month == 12 and d.day >= 20):
        return 109
    if d.month in (5, 6, 9, 10):
        return 92
    return 79


def build(today: date) -> list[dict[str, Any]]:
    """Alle Buchungen (inkl. Stornos und Sperrzeiten) im Smoobu-API-Format."""
    rnd = random.Random(2026)
    out: list[dict[str, Any]] = []
    rid = 900000

    def booking(arr: date, nights: int, channel: str, *, name: tuple[str, str] | None = None,
                cancelled: bool = False, dog: bool | None = None, created: date | None = None,
                check_in: str = "", check_out: str = "", adults: int | None = None) -> dict[str, Any]:
        nonlocal rid
        rid += 1
        fn, ln = name or (rnd.choice(FIRST), rnd.choice(LAST))
        while not name and f"{fn} {ln}" in FIXED:
            fn, ln = rnd.choice(FIRST), rnd.choice(LAST)
        dog = (rnd.random() < 0.25) if dog is None else dog
        base = sum(_season_price(arr + timedelta(days=i)) for i in range(nights))
        cleaning = 15
        elements = [{"type": "basePrice", "name": "Base price", "amount": base},
                    {"type": "cleaningFee", "name": "Cleaning fee", "amount": cleaning}]
        if dog:
            elements.append({"type": "addon", "name": "Endreinigung 1 Hund", "amount": 15})
        price = round(base + cleaning + (15 if dog else 0), 2)
        created = created or (arr - timedelta(days=rnd.choice([3, 9, 21, 35, 60, 90, 140])))
        b: dict[str, Any] = {
            "id": rid,
            "reference-id": f"DEMO{rid}",
            "type": "cancellation" if cancelled else "reservation",
            "arrival": arr.isoformat(),
            "departure": (arr + timedelta(days=nights)).isoformat(),
            "created-at": f"{created.isoformat()} 18:{rnd.randint(10, 59)}",
            "modifiedAt": f"{created.isoformat()} 19:00:00",
            "apartment": dict(APT),
            "channel": {"id": CHANNELS[channel], "name": channel},
            "guest-name": f"{fn} {ln}",
            "firstname": fn,
            "lastname": ln,
            "email": f"{fn.lower()}.{ln.lower()}@example.com".replace("ü", "ue"),
            "phone": f"+49 151 0000{rnd.randint(1000, 9999)}",
            "adults": adults or rnd.choice([1, 2, 2, 2, 3, 4]),
            "children": rnd.choice([0, 0, 0, 1, 2]),
            "check-in": check_in,
            "check-out": check_out,
            "notice": "1 Hund" if dog else "",
            "assistant-notice": "",
            "language": "de",
            "price": price,
            "price-paid": "Yes" if arr < today or channel in ("Airbnb", "Booking.com") else "No",
            "prepayment": round(price * 0.3) if channel in ("Direct booking", "Website") else None,
            "prepayment-paid": "Yes",
            "deposit": None,
            "deposit-paid": "No",
            "is-blocked-booking": False,
            "priceElements": elements,
            "guest-app-url": "https://example.com/gaeste-mappe",
        }
        if channel == "Airbnb":
            b["commission-included"] = round(price * 0.155, 2)
        elif channel == "Booking.com":
            b["commission-included"] = round(price * 0.15, 2)
            b["notice"] += "\nBOOKING NOTE : Payment charge is EUR " + f"{price * 0.014:.4f}"
        out.append(b)
        return b

    def block(arr: date, nights: int) -> None:
        nonlocal rid
        rid += 1
        out.append({"id": rid, "type": "reservation", "arrival": arr.isoformat(),
                    "departure": (arr + timedelta(days=nights)).isoformat(),
                    "created-at": f"{(arr - timedelta(days=30)).isoformat()} 10:00",
                    "modifiedAt": f"{(arr - timedelta(days=30)).isoformat()} 10:00:00",
                    "apartment": dict(APT), "channel": dict(BLOCKED), "guest-name": "", "adults": 0,
                    "children": 0, "price": 0, "is-blocked-booking": True, "priceElements": []})

    weights = [("Airbnb", 30), ("Booking.com", 22), ("Direct booking", 20), ("Website", 18), ("FeWo-direkt", 10)]
    names = [c for c, w in weights for _ in range(w)]
    # Fester Rahmen um heute: Abreise heute + Anreise heute (Gästewechsel), dann kommende Buchungen
    fixed_start = today - timedelta(days=4)
    fixed_end = today + timedelta(days=75)
    start, end = date(today.year - 2, 1, 3), date(today.year + 1, 4, 30)
    d = start
    while d < end:
        if fixed_start <= d < fixed_end:
            d = fixed_end
            continue
        # Lücken: mehr Leerstand im Winter, Zukunft dünner gebucht (realistischer Vorlauf)
        future = d > today
        gap = rnd.choice([0, 1, 2, 3, 4, 6, 9]) + (3 if d.month in (1, 2, 3, 11) else 0) + (5 if future else 0)
        d += timedelta(days=gap)
        nights = rnd.choice([1, 2, 2, 3, 3, 4, 5, 7])
        if d < fixed_end and d + timedelta(days=nights) > fixed_start:
            d = fixed_end  # keine Überschneidung mit dem festen Szenario
            continue
        if rnd.random() < 0.05:
            block(d, rnd.choice([2, 3, 5]))
        else:
            booking(d, nights, rnd.choice(names), cancelled=rnd.random() < 0.06)
        d += timedelta(days=nights)

    # Szenario rund um heute (für Übersicht, Posteingang und Assistent)
    booking(today - timedelta(days=3), 3, "Website", name=("Jana", "Winter"), dog=True, check_in="18:00")
    booking(today, 4, "Airbnb", name=("Lukas", "Berg"), dog=False, check_in="20:30", adults=2)
    booking(today + timedelta(days=5), 2, "Direct booking", name=("Sophie", "Sommer"), dog=True)
    booking(today + timedelta(days=9), 3, "Booking.com", name=("Felix", "Brandt"), dog=False)
    block(today + timedelta(days=14), 2)
    booking(today + timedelta(days=19), 5, "FeWo-direkt", name=("Marie", "Lindner"), dog=False)
    # Lücke von 1 Nacht bei Mindestaufenthalt 2 → „nicht buchbar“ in Übersicht/Belegungsplan
    booking(today + timedelta(days=25), 3, "Airbnb", name=("Jonas", "Vogel"), dog=True)
    booking(today + timedelta(days=29), 2, "Website", name=("Lea", "Kraus"), dog=False)
    booking(today + timedelta(days=38), 7, "Direct booking", name=("Paul", "Hoffmann"), dog=False)
    booking(today + timedelta(days=52), 4, "Booking.com", name=("Emma", "Seidel"), dog=True)
    booking(today + timedelta(days=63), 3, "Airbnb", name=("Ben", "Engel"), dog=False, cancelled=True)
    return out


def messages(bookings: list[dict[str, Any]], today: date) -> dict[int, list[dict[str, Any]]]:
    """Nachrichtenverläufe: Willkommen (automatisch), Fragen, Antworten; eine Frage offen."""
    def find(full: str) -> dict[str, Any]:
        cands = [b for b in bookings if b.get("guest-name") == full and b["type"] != "cancellation"]
        return min(cands, key=lambda b: abs((date.fromisoformat(b["arrival"]) - today).days))

    mid = 5000
    out: dict[int, list[dict[str, Any]]] = {}

    def add(b: dict[str, Any], typ: int, text: str, days_before: int, hh: str, subject: str = "") -> None:
        nonlocal mid
        mid += 1
        when = (date.fromisoformat(b["arrival"]) - timedelta(days=days_before)).isoformat()
        out.setdefault(b["id"], []).append(
            {"id": mid, "type": typ, "subject": subject, "message": text, "createdAt": f"{when} {hh}:00"})

    welcome = ("Hallo {n},\n\nvielen Dank für Deine Buchung! Check-in ab 16 Uhr, Check-out bis 11 Uhr. "
               "Deinen Parkplatz findest Du direkt rechts nach dem Tor.\n\nBis bald!\nDein Gastgeber-Team")
    jana, lukas, sophie, felix, marie, jonas = (find(n) for n in ("Jana Winter", "Lukas Berg", "Sophie Sommer", "Felix Brandt", "Marie Lindner", "Jonas Vogel"))
    for b in (jana, lukas, sophie, felix, marie, jonas):
        add(b, 2, welcome.format(n=b["firstname"]), 20, "09:12", "Willkommen in der Ferienwohnung")
    add(jana, 1, "Hallo, dürfen wir unseren Hund mitbringen? Er ist ruhig und stubenrein.", 18, "17:40")
    add(jana, 2, "Hallo Jana, sehr gerne! Für den Hund berechnen wir 15 € Endreinigung. Näpfe und eine Decke sind da.", 18, "19:02")
    add(jana, 1, "Super, danke! Wir freuen uns.", 18, "19:15")
    add(lukas, 1, "Hi! Wir kommen erst gegen 20:30 Uhr an – ist das in Ordnung? Und gibt es in der Nähe einen Bäcker?", 1, "16:05")
    add(sophie, 1, "Guten Morgen, gibt es ein Kinderbett? Unsere Tochter ist 2 Jahre alt.", 2, "08:31")
    add(sophie, 2, "Hallo Sophie, ja, Reisebett und Hochstuhl stellen wir gerne bereit.", 2, "09:10")
    add(felix, 1, "Vielen Dank für die schnelle Bestätigung!", 6, "21:03")
    add(marie, 1, "Hallo, kann man bei Ihnen das E-Auto laden?", 4, "12:44")
    add(marie, 2, "Hallo Marie, ja – an der Garage gibt es eine Wallbox (11 kW), Abrechnung nach Verbrauch.", 4, "13:20")
    return out


class DemoClient:
    """Ersetzt SmoobuClient: liefert die Demodaten, Schreibaktionen werden nur protokolliert."""

    def __init__(self, today: date) -> None:
        self.today = today
        self.bookings = build(today)
        self.msgs = messages(self.bookings, today)
        self.on_message_sent = None
        self.sent: list[Any] = []

    async def get_me(self) -> dict[str, Any]:
        return {"id": 1000, "firstName": "Demo", "lastName": "Gastgeber", "email": "host@example.com"}

    async def get_apartments(self) -> list[dict[str, Any]]:
        return [dict(APT)]

    async def get_apartment(self, apartment_id: int) -> dict[str, Any]:
        return {**APT, "currency": "EUR", "rooms": {"maxOccupancy": 4}}

    async def get_reservations(self, **f: Any) -> list[dict[str, Any]]:
        res = []
        for b in self.bookings:
            if f.get("departureFrom") and b["departure"] < f["departureFrom"]:
                continue
            if f.get("arrivalTo") and b["arrival"] > f["arrivalTo"]:
                continue
            if f.get("arrivalFrom") and b["arrival"] < f["arrivalFrom"]:
                continue
            if f.get("departureTo") and b["departure"] > f["departureTo"]:
                continue
            if not f.get("showCancellation") and b["type"] == "cancellation":
                continue
            res.append(dict(b))
        return res

    async def get_reservation(self, reservation_id: int) -> dict[str, Any]:
        return dict(next(b for b in self.bookings if b["id"] == int(reservation_id)))

    async def get_messages(self, reservation_id: int, only_related_to_guest: bool = True) -> list[dict[str, Any]]:
        return [dict(m) for m in self.msgs.get(int(reservation_id), [])]

    async def get_rates(self, apartment_id: int, start_date: str, end_date: str) -> dict[str, dict[str, Any]]:
        out = {}
        d, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
        busy = set()
        for b in self.bookings:
            if b["type"] == "cancellation":
                continue
            x = date.fromisoformat(b["arrival"])
            while x < date.fromisoformat(b["departure"]):
                busy.add(x)
                x += timedelta(days=1)
        while d <= end:
            out[d.isoformat()] = {"price": _season_price(d), "min_length_of_stay": 2, "available": 0 if d in busy else 1}
            d += timedelta(days=1)
        return out

    async def send_message(self, reservation_id: int, message: str, *a: Any, **k: Any) -> None:
        self.sent.append((reservation_id, message))

    async def list_webhooks(self) -> list[dict[str, Any]]:
        return []

    async def create_webhook(self, url: str) -> dict[str, Any]:
        return {"id": 1, "webhookUrl": url}

    async def delete_webhook(self, webhook_id: Any) -> None:
        return None

    async def update_reservation(self, *a: Any, **k: Any) -> dict[str, Any]:
        return {}

    async def set_rates(self, *a: Any, **k: Any) -> None:
        return None

    async def create_reservation(self, *a: Any, **k: Any) -> dict[str, Any]:
        return {}

    async def delete_reservation(self, *a: Any, **k: Any) -> None:
        return None

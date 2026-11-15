"""Auswertungen für frei wählbare Zeiträume und Kanäle (ab v1.7.0).

Grundlage ist je Buchung ein aufbereiteter Datensatz (`booking_record`).
Daraus rechnet `analyze()` für einen Zeitraum [start, end) und eine
Kanalauswahl alle Kennzahlen:

Umsatz (anteilig nach Nächten, wie die bisherigen Umsatz-Sensoren):
    brutto, provision, zahlungsgebuehren, kosten, netto, naechte,
    auslastung (Gäste-Nächte ÷ Tage im Zeitraum), €/Nacht brutto + netto
Buchungsverhalten (Buchungen mit ANREISE im Zeitraum):
    buchungen, stornos, stornoquote, Ø Aufenthalt, Ø Personen,
    Ø Vorlaufzeit (Buchung → Anreise), Ø Preis je Buchung, Hunde

Warum zwei Bezugsgrößen: Umsatz gehört zu den Nächten (eine Buchung über
den Jahreswechsel zählt anteilig in beide Jahre). Verhalten wie
Stornoquote oder Vorlaufzeit gehört zur Buchung als Ganzes – sonst würde
eine Buchung mehrfach oder in Bruchteilen gezählt.

Dieselbe Funktion bedient Sensoren, Auswahl-Filter und die Dashboard-Karten
(WebSocket), damit überall dieselben Zahlen stehen.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date, datetime, timedelta
from typing import Any

from .channels import GROUP_DIRECT, GROUP_PORTAL
from .models import (
    first_name,
    guest_count,
    guest_name,
    is_blocked,
    is_yes,
    open_amount,
    parse_date,
    parse_datetime,
    pet_hint,
    price_breakdown,
)

# --- Auswahl-Schlüssel ------------------------------------------------------
# Kanalauswahl: diese drei Sonderwerte + echte Kanalnamen aus Smoobu
SEL_ALL = "Alle Kanäle"
SEL_DIRECT = "Direkt"
SEL_PORTAL = "Portale"

# Zeiträume (Schlüssel = Optionen der Auswahl-Entität, übersetzt in strings.json)
PERIODS = [
    "monat",
    "vormonat",
    "folgemonat",
    "jahr",
    "jahr_bis_heute",
    "vorjahr",
    "letzte_12_monate",
    "naechste_12_monate",
    "gesamt",
]
# „vorjahr_stand“ (ab v1.10.2): Vorjahreszeitraum, aber nur mit den Buchungen, die am
# gleichen Kalendertag des Vorjahres schon bestanden (fairer Vergleich für laufende Monate)
COMPARES = ["vorjahr", "vorjahr_stand", "vorperiode", "kein"]

STATUS_CANCELLED = "storniert"
STATUS_BLOCKED = "blockiert"


def is_cancelled(booking: dict[str, Any]) -> bool:
    """Smoobu kennzeichnet Stornos über type = "cancellation"."""
    return str(booking.get("type") or "").casefold() == "cancellation"


def _month_start(day: date) -> date:
    return day.replace(day=1)


def _add_months(day: date, months: int) -> date:
    total = day.year * 12 + day.month - 1 + months
    return date(total // 12, total % 12 + 1, 1)


def _prev_year(day: date) -> date:
    """Gleicher Tag im Vorjahr (29.02. → 28.02.)."""
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)


def period_range(key: str, today: date, first: date | None = None) -> tuple[date, date]:
    """Zeitraum-Schlüssel → [start, end). `first` = frühester Datenstand (für „gesamt“)."""
    month = _month_start(today)
    if key == "monat":
        return month, _add_months(month, 1)
    if key == "vormonat":
        return _add_months(month, -1), month
    if key == "folgemonat":
        return _add_months(month, 1), _add_months(month, 2)
    if key == "jahr":
        return date(today.year, 1, 1), date(today.year + 1, 1, 1)
    if key == "jahr_bis_heute":
        return date(today.year, 1, 1), today
    if key == "vorjahr":
        return date(today.year - 1, 1, 1), date(today.year, 1, 1)
    if key == "letzte_12_monate":
        return _add_months(month, -12), month
    if key == "naechste_12_monate":
        return month, _add_months(month, 12)
    if key == "gesamt":
        return first or date(today.year - 2, 1, 1), _add_months(month, 13)
    raise ValueError(f"Unbekannter Zeitraum: {key}")


def compare_range(start: date, end: date, mode: str) -> tuple[date, date] | None:
    """Vergleichszeitraum: gleicher Zeitraum im Vorjahr oder direkt davor."""
    if mode in ("vorjahr", "vorjahr_stand"):
        return _prev_year(start), _prev_year(end)
    if mode == "vorperiode":
        # Ganze Monate → um dieselbe Monatszahl verschieben (Feb hat sonst andere Länge)
        if start.day == 1 and end.day == 1:
            months = (end.year - start.year) * 12 + end.month - start.month
            return _add_months(start, -months), start
        length = end - start
        return start - length, start
    return None


# ---------------------------------------------------------------------------
# Buchungsdatensatz
# ---------------------------------------------------------------------------
def booking_record(
    booking: dict[str, Any],
    costs: Callable[[dict[str, Any]], dict[str, Any]],
    payment_excluded: list[str],
    today: date,
) -> dict[str, Any] | None:
    """Eine Buchung kompakt + berechnete Werte (Kosten, Netto, Vorlauf, Status)."""
    arrival = parse_date(booking.get("arrival"))
    departure = parse_date(booking.get("departure"))
    if arrival is None or departure is None:
        return None
    nights = max((departure - arrival).days, 0)
    blocked = is_blocked(booking)
    cancelled = is_cancelled(booking)
    channel = booking.get("channel") or {}
    c = costs(booking) if not blocked else {
        "kanal": channel.get("name") or "Blockiert",
        "kanal_gruppe": None,
        "brutto": 0.0,
        "provision": 0.0,
        "provision_prozent": None,
        "provision_quelle": None,
        "zahlungsgebuehr": 0.0,
        "netto": 0.0,
        "kostenquote_prozent": None,
    }
    created = parse_datetime(booking.get("created-at"))
    lead = (arrival - created.date()).days if created else None
    if cancelled:
        status = STATUS_CANCELLED
    elif blocked:
        status = STATUS_BLOCKED
    elif departure <= today:
        status = "vergangen"
    elif arrival <= today:
        status = "laufend"
    else:
        status = "kommend"
    hint = pet_hint(booking)
    return {
        "id": booking.get("id"),
        "referenz": booking.get("reference-id"),
        "wohnung_id": (booking.get("apartment") or {}).get("id"),
        "wohnung": (booking.get("apartment") or {}).get("name"),
        "status": status,
        "storniert": cancelled,
        "blockiert": blocked,
        "gast": guest_name(booking) if not blocked else None,
        "vorname": first_name(booking) if not blocked else None,
        "email": booking.get("email"),
        "telefon": booking.get("phone"),
        "sprache": booking.get("language"),
        "kanal": c["kanal"],
        "kanal_id": channel.get("id"),
        "gruppe": c["kanal_gruppe"],
        "anreise": arrival.isoformat(),
        "abreise": departure.isoformat(),
        "check_in": booking.get("check-in"),
        "check_out": booking.get("check-out"),
        "naechte": nights,
        "erwachsene": int(booking.get("adults") or 0),
        "kinder": int(booking.get("children") or 0),
        "personen": guest_count(booking),
        "brutto": c["brutto"],
        "provision": c["provision"],
        "provision_quelle": c["provision_quelle"],
        "zahlungsgebuehr": c["zahlungsgebuehr"],
        "netto": c["netto"],
        "kostenquote_prozent": c["kostenquote_prozent"],
        "brutto_pro_nacht": round(c["brutto"] / nights, 2) if nights and c["brutto"] else None,
        "netto_pro_nacht": round(c["netto"] / nights, 2) if nights and c["brutto"] else None,
        "bezahlt": is_yes(booking.get("price-paid")),
        "anzahlung": booking.get("prepayment"),
        "anzahlung_bezahlt": is_yes(booking.get("prepayment-paid")),
        "offen": 0.0 if (blocked or cancelled) else open_amount(booking, payment_excluded),
        "kurtaxe": booking.get("city-tax"),
        "hund": hint is not None,
        "hund_hinweis": hint,
        "erstellt": created.isoformat() if created else None,
        "geaendert": booking.get("modifiedAt"),
        "vorlauf_tage": lead if lead is None or lead >= 0 else 0,
        "notiz": booking.get("notice"),
        "assistent_notiz": booking.get("assistant-notice"),
        "positionen": price_breakdown(booking),
    }


def build_records(
    bookings: Iterable[dict[str, Any]],
    costs: Callable[[dict[str, Any]], dict[str, Any]],
    payment_excluded: list[str],
    today: date,
) -> list[dict[str, Any]]:
    """Alle Buchungen (inkl. Stornos und Sperrzeiten), doppelte IDs nur einmal."""
    seen: set[Any] = set()
    out: list[dict[str, Any]] = []
    for b in bookings:
        if b.get("id") in seen:
            continue
        seen.add(b.get("id"))
        rec = booking_record(b, costs, payment_excluded, today)
        if rec is not None:
            out.append(rec)
    out.sort(key=lambda r: (r["anreise"], r["id"] or 0))
    return out


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------
def channel_filter(selection: str | Iterable[str] | None) -> Callable[[dict[str, Any]], bool]:
    """Auswahl → Prüffunktion je Datensatz.

    None/„Alle Kanäle“ → alle; „Direkt“/„Portale“ → Gruppe; sonst Kanalname(n).
    """
    if selection is None or selection == SEL_ALL:
        return lambda r: True
    if selection == SEL_DIRECT:
        return lambda r: r["gruppe"] == GROUP_DIRECT
    if selection == SEL_PORTAL:
        return lambda r: r["gruppe"] == GROUP_PORTAL
    names = {selection.casefold()} if isinstance(selection, str) else {s.casefold() for s in selection}
    if not names:
        return lambda r: True
    groups = set()
    if SEL_DIRECT.casefold() in names:
        groups.add(GROUP_DIRECT)
    if SEL_PORTAL.casefold() in names:
        groups.add(GROUP_PORTAL)
    return lambda r: (r["kanal"] or "").casefold() in names or r["gruppe"] in groups


def block_channel_id(records: list[dict[str, Any]]) -> Any:
    """ID des normalen Sperr-Kanals („Blocked channel“).

    Smoobu kennt zusätzlich „Blocked channel auto“ (automatische Sperren).
    Bevorzugt wird der Kanal ohne „auto“, sonst der häufigste Sperr-Kanal.
    """
    counts: dict[Any, int] = {}
    for r in records:
        if not r["blockiert"] or not r["kanal_id"]:
            continue
        name = (r["kanal"] or "").casefold()
        if name == "blocked channel":
            return r["kanal_id"]
        if "auto" not in name:
            counts[r["kanal_id"]] = counts.get(r["kanal_id"], 0) + 10
        counts[r["kanal_id"]] = counts.get(r["kanal_id"], 0) + 1
    return max(counts, key=counts.get) if counts else None


def channels_of(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Alle vorkommenden Kanäle mit Gruppe, sortiert nach Gesamtumsatz."""
    totals: dict[str, dict[str, Any]] = {}
    for r in records:
        if r["blockiert"]:
            continue
        t = totals.setdefault(r["kanal"], {"name": r["kanal"], "gruppe": r["gruppe"], "brutto": 0.0})
        if not r["storniert"]:
            t["brutto"] += r["brutto"]
    return sorted(totals.values(), key=lambda t: -t["brutto"])


# ---------------------------------------------------------------------------
# Kennzahlen
# ---------------------------------------------------------------------------
def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def _pct(part: float, whole: float) -> float | None:
    return round(part / whole * 100, 1) if whole else None


def _empty() -> dict[str, Any]:
    return {
        "brutto": 0.0, "provision": 0.0, "zahlungsgebuehren": 0.0, "netto": 0.0, "naechte": 0, "_pn": 0,
        "_n": [], "_p": [], "_lead": [], "_price": [], "buchungen": 0, "stornos": 0,
        "storno_brutto": 0.0, "hunde": 0,
    }


def _add_nights(acc: dict[str, Any], r: dict[str, Any], start: date, end: date) -> None:
    """Anteil einer Buchung, der in [start, end) fällt (Umsatz + Nächte)."""
    arrival, departure = date.fromisoformat(r["anreise"]), date.fromisoformat(r["abreise"])
    lo, hi = max(arrival, start), min(departure, end)
    n = (hi - lo).days
    if n <= 0 or not r["naechte"]:
        return
    share = n / r["naechte"]
    acc["brutto"] += r["brutto"] * share
    acc["provision"] += r["provision"] * share
    acc["zahlungsgebuehren"] += r["zahlungsgebuehr"] * share
    acc["netto"] += r["netto"] * share
    acc["naechte"] += n
    # Nächte mit Preis: Basis für €/Nacht (Buchungen ohne Preis zählen nur zur Auslastung)
    if r["brutto"]:
        acc["_pn"] += n


def _add_booking(acc: dict[str, Any], r: dict[str, Any]) -> None:
    """Buchungsverhalten (Anreise im Zeitraum)."""
    if r["storniert"]:
        acc["stornos"] += 1
        acc["storno_brutto"] += r["brutto"]
        return
    acc["buchungen"] += 1
    acc["_n"].append(r["naechte"])
    acc["_p"].append(r["personen"])
    if r["vorlauf_tage"] is not None:
        acc["_lead"].append(r["vorlauf_tage"])
    if r["brutto"]:
        acc["_price"].append(r["brutto"])
    if r["hund"]:
        acc["hunde"] += 1


def _finish(acc: dict[str, Any], days: int) -> dict[str, Any]:
    costs = acc["provision"] + acc["zahlungsgebuehren"]
    n = acc["naechte"]
    total = acc["buchungen"] + acc["stornos"]
    return {
        "brutto": round(acc["brutto"], 2),
        "netto": round(acc["netto"], 2),
        "provision": round(acc["provision"], 2),
        "zahlungsgebuehren": round(acc["zahlungsgebuehren"], 2),
        "kosten": round(costs, 2),
        "kostenquote_prozent": _pct(costs, acc["brutto"]) or 0.0,
        "naechte": n,
        "auslastung_prozent": round(min(n, days) / days * 100, 1) if days else None,
        "brutto_pro_nacht": round(acc["brutto"] / acc["_pn"], 2) if acc["_pn"] else None,
        "netto_pro_nacht": round(acc["netto"] / acc["_pn"], 2) if acc["_pn"] else None,
        "buchungen": acc["buchungen"],
        "stornos": acc["stornos"],
        "stornoquote_prozent": _pct(acc["stornos"], total) if total else None,
        "storno_volumen": round(acc["storno_brutto"], 2),
        "aufenthalt_schnitt": _avg(acc["_n"]),
        "personen_schnitt": _avg(acc["_p"]),
        "vorlauf_schnitt": _avg(acc["_lead"]),
        "vorlauf_median": _median(acc["_lead"]),
        "preis_pro_buchung": _avg(acc["_price"]),
        "hunde": acc["hunde"],
    }


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    mid = len(s) // 2
    return float(s[mid]) if len(s) % 2 else round((s[mid - 1] + s[mid]) / 2, 1)


def _in(r: dict[str, Any], start: date, end: date) -> bool:
    return start <= date.fromisoformat(r["anreise"]) < end


def _months(start: date, end: date) -> list[date]:
    out, m = [], _month_start(start)
    while m < end:
        out.append(m)
        m = _add_months(m, 1)
    return out


def analyze(
    records: list[dict[str, Any]],
    start: date,
    end: date,
    selection: str | Iterable[str] | None = None,
    series: bool = True,
) -> dict[str, Any]:
    """Kennzahlen gesamt, je Kanal und (optional) als Monats-/Tagesreihe."""
    match = channel_filter(selection)
    days = max((end - start).days, 0)
    total = _empty()
    per_channel: dict[str, dict[str, Any]] = {}
    groups: dict[str, str | None] = {}
    blocked_nights = 0
    for r in records:
        if r["blockiert"]:
            # Stornierte Sperrzeiten liefert Smoobu mit – sie zählen nicht als gesperrt
            if not r["storniert"]:
                arrival, departure = date.fromisoformat(r["anreise"]), date.fromisoformat(r["abreise"])
                blocked_nights += max((min(departure, end) - max(arrival, start)).days, 0)
            continue
        if not match(r):
            continue
        ch = per_channel.setdefault(r["kanal"], _empty())
        groups[r["kanal"]] = r["gruppe"]
        if not r["storniert"]:
            _add_nights(total, r, start, end)
            _add_nights(ch, r, start, end)
        if _in(r, start, end):
            _add_booking(total, r)
            _add_booking(ch, r)

    result = _finish(total, days)
    result["gesperrt_naechte"] = blocked_nights
    channels = {}
    for name, acc in per_channel.items():
        done = _finish(acc, days)
        if not (done["brutto"] or done["buchungen"] or done["stornos"]):
            continue
        done["gruppe"] = groups.get(name)
        done["anteil_prozent"] = _pct(acc["brutto"], total["brutto"]) or 0.0
        channels[name] = done
    result["kanaele"] = dict(sorted(channels.items(), key=lambda kv: -kv[1]["brutto"]))
    direct = sum(v["brutto"] for v in channels.values() if v["gruppe"] == GROUP_DIRECT)
    result["direktanteil_prozent"] = _pct(direct, result["brutto"])
    result["von"] = start.isoformat()
    result["bis"] = end.isoformat()
    result["tage"] = days
    if series:
        result["reihe"] = _series(records, start, end, match)
    return result


def _series(records, start: date, end: date, match) -> dict[str, Any]:
    """Reihe je Monat (bzw. je Tag bei Zeiträumen bis 62 Tage), aufgeteilt nach Kanal."""
    daily = (end - start).days <= 62
    if daily:
        buckets = [start + timedelta(days=i) for i in range((end - start).days)]
        step = lambda b: b + timedelta(days=1)  # noqa: E731
    else:
        buckets = _months(start, end)
        step = lambda b: _add_months(b, 1)  # noqa: E731
    labels, brutto, netto, nights, by_channel = [], [], [], [], {}
    for b in buckets:
        lo, hi = max(b, start), min(step(b), end)
        acc = _empty()
        chans: dict[str, float] = {}
        for r in records:
            if r["blockiert"] or r["storniert"] or not match(r):
                continue
            before = acc["brutto"]
            _add_nights(acc, r, lo, hi)
            if acc["brutto"] != before:
                chans[r["kanal"]] = chans.get(r["kanal"], 0.0) + acc["brutto"] - before
        labels.append(b.isoformat() if daily else b.strftime("%Y-%m"))
        brutto.append(round(acc["brutto"], 2))
        netto.append(round(acc["netto"], 2))
        nights.append(acc["naechte"])
        for name, value in chans.items():
            by_channel.setdefault(name, [0.0] * len(buckets))[len(labels) - 1] = round(value, 2)
    return {
        "einheit": "tag" if daily else "monat",
        "labels": labels,
        "brutto": brutto,
        "netto": netto,
        "naechte": nights,
        "kanaele": by_channel,
    }


def change(new: float | None, old: float | None) -> float | None:
    """Veränderung in % (None, wenn kein Vergleichswert)."""
    if new is None or not old:
        return None
    return round((new - old) / old * 100, 1)


COMPARE_KEYS = [
    "brutto", "netto", "kosten", "naechte", "auslastung_prozent", "netto_pro_nacht",
    "brutto_pro_nacht", "buchungen", "stornos", "aufenthalt_schnitt", "vorlauf_schnitt",
    "personen_schnitt", "preis_pro_buchung",
]


def as_of(records: list[dict[str, Any]], day: date) -> list[dict[str, Any]]:
    """Buchungsstand am Ende von `day` (für den Vergleich „Buchungsstand Vorjahr“).

    - Buchungen, die erst NACH `day` angelegt wurden, fallen weg.
    - Ohne Erstellungsdatum gilt die Buchung als vorher angelegt (wie bei der Prognose).
    - Stornos: Smoobu liefert kein Stornodatum. Näherung über das Änderungsdatum
      (modifiedAt): wurde die Buchung nach `day` geändert, war sie an `day` noch aktiv
      und zählt als normale Buchung. Ohne Änderungsdatum bleibt sie ein Storno.
    """
    out: list[dict[str, Any]] = []
    for r in records:
        created = datetime.fromisoformat(r["erstellt"]).date() if r["erstellt"] else None
        if created is not None and created > day:
            continue
        if r["storniert"]:
            changed = parse_datetime(r["geaendert"])
            if changed is not None and changed.date() > day:
                r = {**r, "storniert": False}
        out.append(r)
    return out


def analyze_with_compare(
    records: list[dict[str, Any]],
    start: date,
    end: date,
    selection: str | Iterable[str] | None,
    mode: str,
    series: bool = True,
    today: date | None = None,
) -> dict[str, Any]:
    """Auswertung + Vergleichszeitraum + Veränderungen je Kennzahl.

    `today` wird nur für „vorjahr_stand“ gebraucht (Stichtag = gleicher Tag im Vorjahr).
    """
    result = analyze(records, start, end, selection, series)
    rng = compare_range(start, end, mode)
    if rng is None:
        result["vergleich"] = None
        return result
    base = records
    if mode == "vorjahr_stand":
        stichtag = _prev_year(today or date.today())
        base = as_of(records, stichtag)
        result["stichtag_vergleich"] = stichtag.isoformat()
    cmp = analyze(base, rng[0], rng[1], selection, series)
    result["vergleich"] = cmp
    result["veraenderung_prozent"] = {k: change(result.get(k), cmp.get(k)) for k in COMPARE_KEYS}
    # Prozentwerte (Auslastung, Kostenquote, Stornoquote) zusätzlich als Punkte
    result["veraenderung_punkte"] = {
        k: (round(result[k] - cmp[k], 1) if result.get(k) is not None and cmp.get(k) is not None else None)
        for k in ("auslastung_prozent", "kostenquote_prozent", "stornoquote_prozent", "direktanteil_prozent")
    }
    return result


def forecast_year(records: list[dict[str, Any]], today: date, selection=None) -> dict[str, Any]:
    """Prognose Jahresende = bereits gebucht + Nachbuchungen wie im Vorjahr.

    Nachbuchungen (Pickup) im Vorjahr = Umsatz der Vorjahresnächte nach dem
    Vorjahres-Stichtag, die erst NACH diesem Stichtag gebucht wurden
    (Erstellungsdatum aus Smoobu). Buchungen ohne Erstellungsdatum gelten
    als vorher gebucht (vorsichtige Schätzung).
    """
    match = channel_filter(selection)
    y_start, y_end = date(today.year, 1, 1), date(today.year + 1, 1, 1)
    booked = analyze(records, y_start, y_end, selection, series=False)
    p_day = _prev_year(today)
    pickup = _empty()
    for r in records:
        if r["blockiert"] or r["storniert"] or not match(r) or not r["erstellt"]:
            continue
        if datetime.fromisoformat(r["erstellt"]).date() >= p_day:
            _add_nights(pickup, r, p_day, date(today.year, 1, 1))
    return {
        "gebucht": booked["brutto"],
        "gebucht_netto": booked["netto"],
        "nachbuchung_vorjahr": round(pickup["brutto"], 2),
        "nachbuchung_vorjahr_netto": round(pickup["netto"], 2),
        "prognose": round(booked["brutto"] + pickup["brutto"], 2),
        "prognose_netto": round(booked["netto"] + pickup["netto"], 2),
        "stichtag_vorjahr": p_day.isoformat(),
        "berechnung": "Gebuchter Jahresumsatz + im Vorjahr ab gleichem Stichtag nachgebuchter Umsatz",
    }

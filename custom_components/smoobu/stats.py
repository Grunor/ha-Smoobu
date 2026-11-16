"""Statistik-Werkbank (ab v1.18.0): frei kombinierbare Auswertungen und Pace-Modell.

Reine Python-Logik ohne HA, damit sie ohne Home Assistant testbar ist. Grundlage
sind die Buchungsdatensätze aus analytics.build_records.

1. query(): Baukasten-Abfrage „Kennzahl × Gruppierung × Aufteilung“.
   - Nacht-Kennzahlen (Umsatz, Netto, Nächte, Auslastung, ADR, RevPAR …) werden je
     belegter Nacht verbucht (Umsatz anteilig nach Nächten, wie überall in der Integration).
     Zeit-Dimensionen beziehen sich dann auf die NACHT.
   - Buchungs-Kennzahlen (Buchungen, Stornos, Vorlauf, Aufenthalt …) zählen je Buchung
     mit ANREISE im Zeitraum. Zeit-Dimensionen beziehen sich dann auf die Anreise.
   - Auslastung/RevPAR brauchen „verfügbare Nächte“: bei Zeit-Dimensionen die Kalendertage
     des Fachs × Wohnungen, bei allen anderen Dimensionen der ganze Zeitraum (Anteil).
   - Jede Zelle liefert `n` (Anzahl Buchungen) – die Karte blendet Werte mit n < 5 blass ein.
2. pace(): Buchungsstand eines Zieljahres über die Zeit (nach Erstellungsdatum) gegen
   die Vorjahre am gleichen relativen Tag, plus Prognose mit Bandbreite.
   Entscheidung: additive Nachbuchung (Jahresende − Stand am gleichen Tag) statt
   Faktor. Ein Faktor explodiert, wenn zum Stichtag wenig gebucht ist (Jahresanfang
   eines schwachen Vorjahres); die additive Variante bleibt stabil und entspricht der
   bisherigen Prognose „Nachbuchung wie im Vorjahr“, nur über alle verfügbaren Jahre.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Callable

from .analytics import _guest_keys, as_of, channel_filter

# ---------------------------------------------------------------------------
# Kennzahlen und Dimensionen
# ---------------------------------------------------------------------------

# Kennzahl → (Art, Bezeichnung, Einheit). Art: "nacht" oder "buchung"
MEASURES: dict[str, tuple[str, str, str]] = {
    "umsatz": ("nacht", "Umsatz brutto", "€"),
    "netto": ("nacht", "Umsatz netto", "€"),
    "kosten": ("nacht", "Provision + Gebühren", "€"),
    "naechte": ("nacht", "Belegte Nächte", "N"),
    "auslastung": ("nacht", "Auslastung", "%"),
    "adr": ("nacht", "Ø Preis je belegter Nacht (ADR)", "€"),
    "netto_pro_nacht": ("nacht", "Netto je belegter Nacht", "€"),
    "revpar": ("nacht", "Umsatz je verfügbarer Nacht (RevPAR)", "€"),
    "netto_revpar": ("nacht", "Netto je verfügbarer Nacht", "€"),
    "kostenquote": ("nacht", "Kostenquote", "%"),
    "buchungen": ("buchung", "Buchungen", ""),
    "stornos": ("buchung", "Stornos", ""),
    "stornoquote": ("buchung", "Stornoquote", "%"),
    "vorlauf": ("buchung", "Vorlauf (Median)", "T"),
    "aufenthalt": ("buchung", "Aufenthalt (Median)", "N"),
    "personen": ("buchung", "Ø Personen je Buchung", ""),
    "hund_anteil": ("buchung", "Anteil mit Hund", "%"),
    "buchungswert": ("buchung", "Ø Buchungswert brutto", "€"),
}

DIMENSIONS = (
    "gesamt", "jahr", "monat", "monat_im_jahr", "woche", "wochentag", "saison",
    "kanal", "gruppe", "wohnung", "aufenthalt", "vorlauf", "personen", "hund",
    "sprache", "stammgast", "buchungsmonat",
)
# Zeit-Dimensionen: Fach = Zeitraum im Kalender → verfügbare Nächte je Fach
TIME_DIMS = {"jahr", "monat", "monat_im_jahr", "woche", "wochentag", "saison"}

WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
SEASONS = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Frühling", 4: "Frühling", 5: "Frühling",
           6: "Sommer", 7: "Sommer", 8: "Sommer", 9: "Herbst", 10: "Herbst", 11: "Herbst"}
LEAD_BUCKETS = ((7, "0–7"), (14, "8–14"), (30, "15–30"), (60, "31–60"), (90, "61–90"), (180, "91–180"))
STAY_BUCKETS = ((1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"))
# Sortierreihenfolge für Fächer mit fester Ordnung (sonst alphabetisch bzw. nach Wert)
ORDER = {
    "wochentag": list(WEEKDAYS),
    "saison": ["Winter", "Frühling", "Sommer", "Herbst"],
    "vorlauf": [b[1] for b in LEAD_BUCKETS] + [">180", "unbekannt"],
    "aufenthalt": [b[1] for b in STAY_BUCKETS] + ["7+"],
    "hund": ["mit Hund", "ohne Hund"],
    "stammgast": ["Stammgast", "Neukunde"],
}

MIN_N = 5  # darunter gilt eine Zelle als „wenig Daten“


def _bucket(value: int | None, buckets, last: str) -> str:
    if value is None:
        return "unbekannt"
    for limit, label in buckets:
        if value <= limit:
            return label
    return last


def _repeat_guests(records: list[dict[str, Any]]) -> set[str]:
    """Gast-Merkmale, die bei mindestens 2 nicht stornierten Buchungen vorkommen."""
    count: dict[str, int] = defaultdict(int)
    for r in records:
        if r["blockiert"] or r["storniert"]:
            continue
        for k in _guest_keys(r):
            count[k] += 1
    return {k for k, c in count.items() if c >= 2}


def _key(dim: str, r: dict[str, Any], day: date, repeat: set[str]) -> str:
    """Fach einer Buchung (bzw. einer Nacht `day`) in Dimension `dim`."""
    if dim == "gesamt":
        return "Gesamt"
    if dim == "jahr":
        return str(day.year)
    if dim == "monat":
        return f"{day.year}-{day.month:02d}"
    if dim == "monat_im_jahr":
        return f"{day.month:02d}"
    if dim == "woche":
        iso = day.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    if dim == "wochentag":
        return WEEKDAYS[day.weekday()]
    if dim == "saison":
        return SEASONS[day.month]
    if dim == "kanal":
        return r["kanal"] or "unbekannt"
    if dim == "gruppe":
        return r["gruppe"] or "unbekannt"
    if dim == "wohnung":
        return r["wohnung"] or str(r["wohnung_id"])
    if dim == "aufenthalt":
        return _bucket(r["naechte"], STAY_BUCKETS, "7+")
    if dim == "vorlauf":
        return _bucket(r["vorlauf_tage"], LEAD_BUCKETS, ">180")
    if dim == "personen":
        return str(r["personen"] or 0)
    if dim == "hund":
        return "mit Hund" if r["hund"] else "ohne Hund"
    if dim == "sprache":
        return (r["sprache"] or "unbekannt").lower()
    if dim == "stammgast":
        return "Stammgast" if _guest_keys(r) & repeat else "Neukunde"
    if dim == "buchungsmonat":
        return (r["erstellt"] or "unbekannt")[:7]
    raise ValueError(f"Unbekannte Dimension: {dim}")


def _time_key_days(dim: str, start: date, end: date) -> dict[str, int]:
    """Kalendertage je Fach einer Zeit-Dimension (für verfügbare Nächte)."""
    out: dict[str, int] = defaultdict(int)
    day = start
    while day < end:
        out[_key(dim, {}, day, set())] += 1
        day += timedelta(days=1)
    return out


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    v = sorted(values)
    mid = len(v) // 2
    return float(v[mid]) if len(v) % 2 else (v[mid - 1] + v[mid]) / 2


def _value(measure: str, acc: dict[str, Any], available: float) -> float | None:
    """Kennzahl aus einem Akkumulator berechnen (None = nicht berechenbar)."""
    if measure == "umsatz":
        return round(acc["brutto"], 2)
    if measure == "netto":
        return round(acc["netto"], 2)
    if measure == "kosten":
        return round(acc["brutto"] - acc["netto"], 2)
    if measure == "naechte":
        return acc["naechte"]
    if measure == "auslastung":
        return round(acc["naechte"] / available * 100, 1) if available else None
    if measure == "adr":
        return round(acc["brutto_preis"] / acc["naechte_preis"], 2) if acc["naechte_preis"] else None
    if measure == "netto_pro_nacht":
        return round(acc["netto_preis"] / acc["naechte_preis"], 2) if acc["naechte_preis"] else None
    if measure == "revpar":
        return round(acc["brutto"] / available, 2) if available else None
    if measure == "netto_revpar":
        return round(acc["netto"] / available, 2) if available else None
    if measure == "kostenquote":
        return round((acc["brutto"] - acc["netto"]) / acc["brutto"] * 100, 1) if acc["brutto"] else None
    total = acc["buchungen"] + acc["stornos"]
    if measure == "buchungen":
        return acc["buchungen"]
    if measure == "stornos":
        return acc["stornos"]
    if measure == "stornoquote":
        return round(acc["stornos"] / total * 100, 1) if total else None
    if measure == "vorlauf":
        return _median(acc["vorlauf"])
    if measure == "aufenthalt":
        return _median(acc["aufenthalt"])
    if measure == "personen":
        return round(sum(acc["personen"]) / len(acc["personen"]), 1) if acc["personen"] else None
    if measure == "hund_anteil":
        return round(acc["hund"] / acc["buchungen"] * 100, 1) if acc["buchungen"] else None
    if measure == "buchungswert":
        return round(acc["wert"] / acc["buchungen"], 2) if acc["buchungen"] else None
    raise ValueError(f"Unbekannte Kennzahl: {measure}")


def _acc() -> dict[str, Any]:
    return {"brutto": 0.0, "netto": 0.0, "naechte": 0, "brutto_preis": 0.0, "netto_preis": 0.0,
            "naechte_preis": 0, "buchungen": 0, "stornos": 0, "vorlauf": [], "aufenthalt": [],
            "personen": [], "hund": 0, "wert": 0.0, "ids": set()}


def query(
    records: list[dict[str, Any]],
    measure: str,
    dimension: str,
    start: date,
    end: date,
    *,
    split: str | None = None,
    channels: Any = None,
    units: int = 1,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Baukasten-Abfrage. Ergebnis: Fächer (rows) × Aufteilung (series) mit Wert und n.

    filters (optional): min_naechte, max_naechte, hund (bool), sprache (Liste).
    """
    if measure not in MEASURES:
        raise ValueError(f"Unbekannte Kennzahl: {measure}")
    if dimension not in DIMENSIONS or (split and split not in DIMENSIONS):
        raise ValueError("Unbekannte Dimension")
    kind = MEASURES[measure][0]
    match = channel_filter(channels)
    f = filters or {}
    repeat = _repeat_guests(records)
    split_dim = split or "gesamt"

    def keep(r: dict[str, Any]) -> bool:
        if r["blockiert"] or not match(r):
            return False
        if f.get("min_naechte") and r["naechte"] < f["min_naechte"]:
            return False
        if f.get("max_naechte") and r["naechte"] > f["max_naechte"]:
            return False
        if f.get("hund") is not None and bool(r["hund"]) != bool(f["hund"]):
            return False
        if f.get("sprache") and (r["sprache"] or "").lower() not in {s.lower() for s in f["sprache"]}:
            return False
        return True

    cells: dict[tuple[str, str], dict[str, Any]] = defaultdict(_acc)
    s_iso, e_iso = start.isoformat(), end.isoformat()
    for r in records:
        if not keep(r):
            continue
        arrival = date.fromisoformat(r["anreise"])
        if kind == "nacht":
            if r["storniert"] or r["abreise"] <= s_iso or r["anreise"] >= e_iso or not r["naechte"]:
                continue
            per_b, per_n = r["brutto"] / r["naechte"], r["netto"] / r["naechte"]
            day = max(arrival, start)
            last = min(date.fromisoformat(r["abreise"]), end)
            while day < last:
                a = cells[(_key(dimension, r, day, repeat), _key(split_dim, r, day, repeat))]
                a["brutto"] += per_b
                a["netto"] += per_n
                a["naechte"] += 1
                if r["brutto"]:  # ADR/Netto je Nacht nur aus Nächten mit Preis (wie v1.9.2)
                    a["brutto_preis"] += per_b
                    a["netto_preis"] += per_n
                    a["naechte_preis"] += 1
                a["ids"].add(r["id"])
                day += timedelta(days=1)
        else:
            if not (s_iso <= r["anreise"] < e_iso):
                continue
            a = cells[(_key(dimension, r, arrival, repeat), _key(split_dim, r, arrival, repeat))]
            a["ids"].add(r["id"])
            if r["storniert"]:
                a["stornos"] += 1
                continue
            a["buchungen"] += 1
            a["aufenthalt"].append(r["naechte"])
            a["personen"].append(r["personen"] or 0)
            a["hund"] += 1 if r["hund"] else 0
            a["wert"] += r["brutto"]
            if r["vorlauf_tage"] is not None:
                a["vorlauf"].append(r["vorlauf_tage"])

    # Verfügbare Nächte je Fach (nur bei Zeit-Dimensionen unterschiedlich)
    total_days = (end - start).days * max(units, 1)
    days_by_key = (_time_key_days(dimension, start, end) if dimension in TIME_DIMS else {})
    split_days = (_time_key_days(split_dim, start, end) if split_dim in TIME_DIMS else {})

    def available(row: str, ser: str) -> float:
        if dimension in TIME_DIMS and split_dim in TIME_DIMS:
            # Schnittmenge zweier Zeit-Dimensionen: Tage zählen, die in beide Fächer fallen
            n, day = 0, start
            while day < end:
                if _key(dimension, {}, day, set()) == row and _key(split_dim, {}, day, set()) == ser:
                    n += 1
                day += timedelta(days=1)
            return n * max(units, 1)
        if dimension in TIME_DIMS:
            return days_by_key.get(row, 0) * max(units, 1)
        if split_dim in TIME_DIMS:
            return split_days.get(ser, 0) * max(units, 1)
        return total_days

    rows = sorted({k[0] for k in cells} | set(days_by_key), key=lambda k: _order(dimension, k))
    series = sorted({k[1] for k in cells}, key=lambda k: _order(split_dim, k))
    out_rows = []
    for row in rows:
        vals = {}
        for ser in series:
            acc = cells.get((row, ser))
            if acc is None:
                vals[ser] = {"wert": None if kind == "buchung" else _value(measure, _acc(), available(row, ser)),
                             "n": 0}
                continue
            n = len(acc["ids"])
            vals[ser] = {"wert": _value(measure, acc, available(row, ser)), "n": n, "wenig_daten": n < MIN_N}
        out_rows.append({"fach": row, "werte": vals})
    return {
        "kennzahl": measure,
        "bezeichnung": MEASURES[measure][1],
        "einheit": MEASURES[measure][2],
        "art": kind,
        "dimension": dimension,
        "aufteilung": split,
        "start": start.isoformat(),
        "ende": end.isoformat(),
        "serien": series,
        "zeilen": out_rows,
        "min_n": MIN_N,
    }


def _order(dim: str, key: str) -> tuple[int, str]:
    fixed = ORDER.get(dim)
    if fixed and key in fixed:
        return (fixed.index(key), key)
    return (len(fixed) if fixed else 0, key)


# ---------------------------------------------------------------------------
# Pace-Modell
# ---------------------------------------------------------------------------


def _booked_for_year(recs: list[dict[str, Any]], year: int, match: Callable) -> float:
    """Brutto der Nächte im Jahr `year` (anteilig), ohne Stornos und Sperren."""
    start, end = date(year, 1, 1), date(year + 1, 1, 1)
    total = 0.0
    for r in recs:
        if r["blockiert"] or r["storniert"] or not r["naechte"] or not match(r):
            continue
        a, d = date.fromisoformat(r["anreise"]), date.fromisoformat(r["abreise"])
        nights = (min(d, end) - max(a, start)).days
        if nights > 0:
            total += r["brutto"] * nights / r["naechte"]
    return total


def _shift(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year + years)
    except ValueError:  # 29.02.
        return day.replace(year=day.year + years, day=28)


def _quantile(values: list[float], q: float) -> float:
    v = sorted(values)
    if len(v) == 1:
        return v[0]
    pos = (len(v) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)


def pace(
    records: list[dict[str, Any]],
    target_year: int,
    today: date,
    *,
    channels: Any = None,
    compare_years: int = 6,
    first: date | None = None,
) -> dict[str, Any]:
    """Buchungsstand-Kurven (Monatsende ab Jan Vorjahr bis Dez Zieljahr) + Prognose.

    Kurve je Jahr y: Stand am Ende jedes Monats m (relativ: Jan y−1 … Dez y) = Brutto der
    Nächte in y, das an diesem Tag gebucht war (analytics.as_of: Stornos über das
    Änderungsdatum angenähert). Für das Zieljahr endet die Kurve heute.
    `first` = frühestes Datum mit vollständigen Daten; Vorjahre davor bleiben weg.
    """
    match = channel_filter(channels)
    years = [target_year - i for i in range(compare_years + 1)]
    if first is not None:
        years = [y for y in years if date(y - 1, 1, 1) >= first or y == target_year]

    def point(y: int, day: date) -> float:
        return round(_booked_for_year(as_of(records, day), y, match), 2)

    curves: dict[str, list[dict[str, Any]]] = {}
    for y in years:
        pts = []
        for i in range(24):
            yy, mm = y - 1 + i // 12, i % 12 + 1
            nxt = date(yy + (mm == 12), mm % 12 + 1, 1)
            day = nxt - timedelta(days=1)  # Monatsende
            if y == target_year and day > today:
                if not pts or pts[-1]["datum"] != today.isoformat():
                    pts.append({"datum": today.isoformat(), "index": i, "wert": point(y, today), "heute": True})
                break
            pts.append({"datum": day.isoformat(), "index": i, "wert": point(y, day)})
        curves[str(y)] = pts

    # Stichtag-Vergleich: Stand heute vs. Stand der Vorjahre am gleichen relativen Tag
    offset = target_year - today.year  # 0 = laufendes Jahr, 1 = nächstes Jahr …
    booked_now = point(target_year, today)
    history = []
    for y in years[1:]:
        same_day = _shift(today, y - target_year)
        if same_day > today:
            continue
        stand = point(y, same_day)
        final = point(y, date(y + 1, 3, 31))  # Endstand inkl. später erfasster Buchungen
        history.append({"jahr": y, "stand_stichtag": stand, "endstand": final,
                        "nachbuchung": round(final - stand, 2)})

    forecast = None
    if history:
        pickups = [h["nachbuchung"] for h in history]
        mid = booked_now + _median(pickups)
        lo = booked_now + max(_quantile(pickups, 0.1), 0.0)
        hi = booked_now + _quantile(pickups, 0.9)
        forecast = {
            "gebucht": booked_now,
            "erwartete_nachbuchung": round(mid - booked_now, 2),
            "wahrscheinlich": round(mid, 2),
            "unten": round(min(lo, mid), 2),
            "oben": round(max(hi, mid), 2),
            "jahre_basis": len(pickups),
            # Bandbreite ist eine Spanne über die Vorjahre (P10–P90), kein statistisches
            # Konfidenzintervall – bei wenigen Jahren bewusst als „Spanne“ bezeichnen.
            "methode": "additive Nachbuchung, Median und P10–P90 der Vorjahre",
        }
    prev = next((h for h in history if h["jahr"] == target_year - 1), None)
    return {
        "zieljahr": target_year,
        "stichtag": today.isoformat(),
        "vorlauf_jahre": offset,
        "kurven": curves,
        "vergleich": history,
        "vorjahr_stichtag": prev["stand_stichtag"] if prev else None,
        "veraenderung_prozent": (round((booked_now / prev["stand_stichtag"] - 1) * 100, 1)
                                 if prev and prev["stand_stichtag"] else None),
        "prognose": forecast,
    }


# ---------------------------------------------------------------------------
# Teilschritt 3/4: verlorene Nächte, Stornos, Antwortzeiten
# ---------------------------------------------------------------------------

GAP_MAX = 14  # längere freie Zeiträume gelten nicht als „Lücke zwischen zwei Buchungen“


def _month_adr(records: list[dict[str, Any]]) -> tuple[dict[str, float], float | None]:
    """Ø Brutto je belegter Nacht je Monat (JJJJ-MM) und über alles – Schätzpreis für Lücken
    ohne gespeicherten Tagespreis (Entscheidung Betreiber 16.11.2026: Ø-Monatspreis, als „geschätzt“
    gekennzeichnet; Smoobu liefert Tagespreise nicht rückwirkend)."""
    sums: dict[str, list[float]] = defaultdict(lambda: [0.0, 0])
    for r in records:
        if r["blockiert"] or r["storniert"] or not r["naechte"] or not r["brutto"]:
            continue
        per = r["brutto"] / r["naechte"]
        day, last = date.fromisoformat(r["anreise"]), date.fromisoformat(r["abreise"])
        while day < last:
            s = sums[f"{day.year}-{day.month:02d}"]
            s[0] += per
            s[1] += 1
            day += timedelta(days=1)
    monthly = {k: v[0] / v[1] for k, v in sums.items() if v[1]}
    total_n = sum(v[1] for v in sums.values())
    overall = sum(v[0] for v in sums.values()) / total_n if total_n else None
    return monthly, overall


def gaps(
    records: list[dict[str, Any]],
    start: date,
    end: date,
    today: date,
    *,
    rates_now: dict[str, dict[str, Any]] | None = None,
    price_history: dict[str, list[Any]] | None = None,
    max_len: int = GAP_MAX,
) -> dict[str, Any]:
    """Freie Lücken zwischen zwei Belegungen (Sperrzeiten zählen als belegt) einer Wohnung.

    Preis je Nacht: künftige Tage aus den aktuellen Smoobu-Tagespreisen, vergangene aus der
    ab v1.18 gespeicherten Preis-Historie, sonst Ø-Monatspreis (quelle „geschätzt“).
    Mindestaufenthalt ebenso (unbekannt = None). „zu_kurz“ = Lücke kürzer als der
    Mindestaufenthalt am ersten freien Tag → so nicht buchbar.
    """
    rates_now = rates_now or {}
    price_history = price_history or {}
    occ: set[date] = set()
    for r in records:
        if r["storniert"] or not r["naechte"]:
            continue
        day, last = date.fromisoformat(r["anreise"]), date.fromisoformat(r["abreise"])
        while day < last:
            occ.add(day)
            day += timedelta(days=1)
    monthly, overall = _month_adr(records)

    def info(day: date) -> tuple[float | None, int | None, str]:
        key = day.isoformat()
        if day >= today and key in rates_now:
            r = rates_now[key]
            return r.get("price"), r.get("min_length_of_stay"), "tagespreis"
        if key in price_history:
            p, m = (list(price_history[key]) + [None, None])[:2]
            return p, m, "tagespreis"
        return monthly.get(f"{day.year}-{day.month:02d}", overall), None, "geschaetzt"

    out = []
    day = start
    while day < end:
        if day in occ or (day - timedelta(days=1)) not in occ:
            day += timedelta(days=1)
            continue
        first = day
        while day not in occ and (day - first).days <= max_len:
            day += timedelta(days=1)
        length = (day - first).days
        if day not in occ or length > max_len:
            continue  # kein Ende in Sicht → keine Lücke, sondern freier Zeitraum
        prices, sources = [], set()
        for i in range(length):
            p, _m, src = info(first + timedelta(days=i))
            prices.append(p or 0.0)
            sources.add(src)
        _p, min_stay, _src = info(first)
        out.append({
            "von": first.isoformat(), "bis": day.isoformat(), "naechte": length,
            "wert": round(sum(prices), 2), "preis_nacht": round(sum(prices) / length, 2) if length else None,
            "mindestaufenthalt": min_stay, "zu_kurz": bool(min_stay and length < min_stay),
            "quelle": "geschaetzt" if "geschaetzt" in sources else "tagespreis",
            "vergangen": day <= today,
        })

    def summary(items: list[dict[str, Any]]) -> dict[str, Any]:
        return {"luecken": len(items), "naechte": sum(g["naechte"] for g in items),
                "wert": round(sum(g["wert"] for g in items), 2),
                "zu_kurz": sum(1 for g in items if g["zu_kurz"]),
                "zu_kurz_naechte": sum(g["naechte"] for g in items if g["zu_kurz"]),
                "geschaetzt": sum(1 for g in items if g["quelle"] == "geschaetzt")}

    past = [g for g in out if g["vergangen"]]
    future = [g for g in out if not g["vergangen"]]
    hints = [
        {"von": g["von"], "naechte": g["naechte"], "mindestaufenthalt": g["mindestaufenthalt"], "wert": g["wert"],
         "text": f"Mindestaufenthalt ab {g['von']} von {g['mindestaufenthalt']} auf {g['naechte']} senken"}
        for g in future if g["zu_kurz"]
    ]
    # Verteilung der Lückenlänge (1 … 7+ Nächte) für das Histogramm
    lengths: dict[str, int] = defaultdict(int)
    for g in out:
        lengths[str(g["naechte"]) if g["naechte"] < 7 else "7+"] += 1
    return {"luecken": out, "vergangen": summary(past), "kommend": summary(future), "vorschlaege": hints,
            "laengen": [{"fach": k, "anzahl": lengths.get(k, 0)} for k in ["1", "2", "3", "4", "5", "6", "7+"]]}


def _changed(r: dict[str, Any]) -> date | None:
    value = r.get("geaendert")
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


STORNO_LEAD = ((0, "am Anreisetag"), (7, "1–7"), (30, "8–30"), (90, "31–90"))


def storno(records: list[dict[str, Any]], start: date, end: date, *, channels: Any = None) -> dict[str, Any]:
    """Stornos mit Anreise im Zeitraum: Quote je Kanal, Ausfall, Wiederbelegung, Storno-Vorlauf.

    Smoobu liefert kein Stornodatum → Storno-Vorlauf = Anreise − Änderungsdatum (Näherung,
    wie bei analytics.as_of). Wiederbelegt = Nächte des Stornos, die später durch eine andere,
    nicht stornierte Gästebuchung belegt sind.
    """
    match = channel_filter(channels)
    s_iso, e_iso = start.isoformat(), end.isoformat()
    guests = [r for r in records if not r["blockiert"] and match(r)]
    in_range = [r for r in guests if s_iso <= r["anreise"] < e_iso]
    booked_nights: set[tuple[Any, date]] = set()
    for r in records:
        if r["blockiert"] or r["storniert"] or not r["naechte"]:
            continue
        day, last = date.fromisoformat(r["anreise"]), date.fromisoformat(r["abreise"])
        while day < last:
            booked_nights.add((r["wohnung_id"], day))
            day += timedelta(days=1)
    per: dict[str, dict[str, Any]] = {}
    leads, lost_nights, rebooked, lost_value = [], 0, 0, 0.0
    buckets: dict[str, int] = defaultdict(int)
    items = []
    for r in in_range:
        p = per.setdefault(r["kanal"] or "unbekannt", {"kanal": r["kanal"] or "unbekannt", "gruppe": r["gruppe"],
                                                       "buchungen": 0, "stornos": 0, "ausfall": 0.0})
        if not r["storniert"]:
            p["buchungen"] += 1
            continue
        p["stornos"] += 1
        p["ausfall"] += r["brutto"]
        lost_value += r["brutto"]
        day, last = date.fromisoformat(r["anreise"]), date.fromisoformat(r["abreise"])
        nights = re = 0
        while day < last:
            nights += 1
            re += 1 if (r["wohnung_id"], day) in booked_nights else 0
            day += timedelta(days=1)
        lost_nights += nights
        rebooked += re
        changed = _changed(r)
        lead = (date.fromisoformat(r["anreise"]) - changed).days if changed else None
        if lead is not None and lead >= 0:
            leads.append(lead)
            buckets[_bucket(lead, STORNO_LEAD, ">90")] += 1
        items.append({"id": r["id"], "kanal": r["kanal"], "anreise": r["anreise"], "naechte": nights, "brutto": r["brutto"],
                      "storno_vorlauf": lead, "wiederbelegt": re})
    for p in per.values():
        total = p["buchungen"] + p["stornos"]
        p["quote"] = round(p["stornos"] / total * 100, 1) if total else None
        p["ausfall"] = round(p["ausfall"], 2)
        p["wenig_daten"] = total < MIN_N
    stornos = sum(p["stornos"] for p in per.values())
    total = stornos + sum(p["buchungen"] for p in per.values())
    return {
        "buchungen": total, "stornos": stornos, "quote": round(stornos / total * 100, 1) if total else None,
        "ausfall": round(lost_value, 2), "naechte": lost_nights, "wiederbelegt_naechte": rebooked,
        "wiederbelegt_prozent": round(rebooked / lost_nights * 100, 1) if lost_nights else None,
        "vorlauf_median": _median(leads),
        "vorlauf": [{"fach": label, "anzahl": buckets.get(label, 0)}
                    for label in [b[1] for b in STORNO_LEAD] + [">90"]],
        "kanaele": sorted(per.values(), key=lambda p: -(p["stornos"] + p["buchungen"])),
        "liste": sorted(items, key=lambda i: i["anreise"], reverse=True),
        "min_n": MIN_N,
    }


def _parse_ts(value: Any) -> Any:
    from datetime import datetime  # noqa: PLC0415

    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace(" ", "T")[:19])
    except ValueError:
        return None


def response_times(messages: list[dict[str, Any]]) -> list[float]:
    """Antwortzeiten in Minuten: je Gastnachricht-Folge die Zeit bis zur nächsten Nachricht an den Gast.

    Erwartet sichtbare Nachrichten (ohne interne Notizen). type 1 = Gast, type 2 = an den Gast
    (auch automatische Smoobu-Nachrichten – Smoobu kennzeichnet sie nicht, sie zählen deshalb
    als Antwort). Mehrere Gastnachrichten am Stück zählen ab der ersten.
    """
    out: list[float] = []
    waiting = None
    for m in sorted(messages, key=lambda x: int(x.get("id") or 0)):
        try:
            typ = int(m.get("type") or 0)
        except (TypeError, ValueError):
            continue
        ts = _parse_ts(m.get("createdAt") or m.get("created_at"))
        if ts is None:
            continue
        if typ == 1 and waiting is None:
            waiting = ts
        elif typ == 2 and waiting is not None:
            out.append(round(max((ts - waiting).total_seconds(), 0) / 60, 1))
            waiting = None
    return out


def service(records: list[dict[str, Any]], responses: dict[str, dict[str, Any]], start: date, end: date,
            *, channels: Any = None) -> dict[str, Any]:
    """Antwortzeiten (Median, Anteil < 1 h) für Buchungen mit Anreise im Zeitraum, je Kanal und Monat."""
    match = channel_filter(channels)
    s_iso, e_iso = start.isoformat(), end.isoformat()
    allm: list[float] = []
    by_ch: dict[str, list[float]] = defaultdict(list)
    by_m: dict[str, list[float]] = defaultdict(list)
    covered = total = 0
    for r in records:
        if r["blockiert"] or not match(r) or not (s_iso <= r["anreise"] < e_iso):
            continue
        total += 1
        entry = responses.get(str(r["id"]))
        if entry is None:
            continue
        covered += 1
        mins = entry.get("minuten") or []
        allm += mins
        by_ch[r["kanal"] or "unbekannt"] += mins
        by_m[r["anreise"][:7]] += mins

    def agg(values: list[float]) -> dict[str, Any]:
        return {"median": _median(values), "unter_1h": round(sum(1 for v in values if v < 60) / len(values) * 100, 1)
                if values else None, "n": len(values), "wenig_daten": len(values) < MIN_N}

    return {"gesamt": agg(allm), "buchungen": total, "geladen": covered,
            "kanaele": [{"kanal": k, **agg(v)} for k, v in sorted(by_ch.items(), key=lambda kv: -len(kv[1]))],
            "monate": [{"fach": k, **agg(v)} for k, v in sorted(by_m.items())],
            "verteilung": [{"fach": label, "anzahl": sum(1 for v in allm if lo <= v < hi)} for label, lo, hi in
                           (("< 15 min", 0, 15), ("15–60 min", 15, 60), ("1–4 h", 60, 240), ("4–12 h", 240, 720),
                            ("12–24 h", 720, 1440), ("> 24 h", 1440, 10**9))],
            "min_n": MIN_N}

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
from .seasons import month_map as season_month_map, order as season_order

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
    "netto_pro_nacht": ("nacht", "Nach Provision je belegter Nacht", "€"),
    "revpar": ("nacht", "Umsatz je verfügbarer Nacht (RevPAR)", "€"),
    "netto_revpar": ("nacht", "Nach Provision je verfügbarer Nacht", "€"),
    "kostenquote": ("nacht", "Kostenquote", "%"),
    # v1.18.0: variable Kosten (Reinigung, Wäsche, Heizung, Warmwasser, Wasser, Strom) und
    # Deckungsbeitrag = Netto − variable Kosten (siehe deckungsbeitrag.py)
    "var_kosten": ("nacht", "Variable Kosten", "€"),
    "db": ("nacht", "Deckungsbeitrag", "€"),
    "db_pro_nacht": ("nacht", "Deckungsbeitrag je belegter Nacht", "€"),
    "db_revpar": ("nacht", "Deckungsbeitrag je verfügbarer Nacht", "€"),
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
    # Buchungszeitpunkt-Matrix (Wunsch Betreiber 16.11.2026): wann wird für welchen Zeitraum gebucht
    "vorlauf_monate", "buchungsmonat_im_jahr",
)
# Zeit-Dimensionen: Fach = Zeitraum im Kalender → verfügbare Nächte je Fach
TIME_DIMS = {"jahr", "monat", "monat_im_jahr", "woche", "wochentag", "saison"}

WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
# v1.18.0: Saisons einstellbar (seasons.py); SEASONS bleibt als Standard-Zuordnung (Abwärtskompatibilität, Tests)
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
    "vorlauf_monate": ["gleicher Monat", "1 Monat", "2 Monate", "3 Monate", "4–6 Monate", "7–12 Monate", "> 12 Monate", "unbekannt"],
}
# Monate zwischen Buchungsmonat und Aufenthaltsmonat → Klasse (0 = im selben Monat gebucht)
LEAD_MONTHS = ((0, "gleicher Monat"), (1, "1 Monat"), (2, "2 Monate"), (3, "3 Monate"), (6, "4–6 Monate"), (12, "7–12 Monate"))

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


def _key(dim: str, r: dict[str, Any], day: date, repeat: set[str], smap: dict[int, str] | None = None) -> str:
    """Fach einer Buchung (bzw. einer Nacht `day`) in Dimension `dim` (smap = Monat → Saisonname)."""
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
        return (smap or SEASONS)[day.month]
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
    if dim == "buchungsmonat_im_jahr":
        return r["erstellt"][5:7] if r.get("erstellt") else "unbekannt"
    if dim == "vorlauf_monate":
        # Bezug: Nacht-Kennzahlen die einzelne Nacht, Buchungs-Kennzahlen die Anreise (day)
        created = r.get("erstellt")
        if not created:
            return "unbekannt"
        cy, cm = int(created[:4]), int(created[5:7])
        diff = max((day.year * 12 + day.month) - (cy * 12 + cm), 0)
        return _bucket(diff, LEAD_MONTHS, "> 12 Monate")
    raise ValueError(f"Unbekannte Dimension: {dim}")


def _time_key_days(dim: str, start: date, end: date, smap: dict[int, str] | None = None) -> dict[str, int]:
    """Kalendertage je Fach einer Zeit-Dimension (für verfügbare Nächte)."""
    out: dict[str, int] = defaultdict(int)
    day = start
    while day < end:
        out[_key(dim, {}, day, set(), smap)] += 1
        day += timedelta(days=1)
    return out


def _blocked_days(records: list[dict[str, Any]], start: date, end: date) -> list[date]:
    """Gesperrte Nächte im Zeitraum als Liste von Tagen (je Wohnung einmal, daher Mehrfachnennung möglich).

    Stornierte Sperrzeiten liefert Smoobu mit – sie zählen nicht (wie analytics.analyze).
    """
    out: list[date] = []
    for r in records:
        if not r["blockiert"] or r["storniert"]:
            continue
        day = max(date.fromisoformat(r["anreise"]), start)
        last = min(date.fromisoformat(r["abreise"]), end)
        while day < last:
            out.append(day)
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
    if measure == "var_kosten":
        return round(acc["var"], 2)
    if measure == "db":
        return round(acc["netto"] - acc["var"], 2)
    if measure == "db_pro_nacht":
        return round((acc["netto_preis"] - acc["var_preis"]) / acc["naechte_preis"], 2) if acc["naechte_preis"] else None
    if measure == "db_revpar":
        return round((acc["netto"] - acc["var"]) / available, 2) if available else None
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
    return {"brutto": 0.0, "netto": 0.0, "var": 0.0, "var_preis": 0.0, "naechte": 0, "brutto_preis": 0.0, "netto_preis": 0.0,
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
    seasons: list[dict[str, Any]] | None = None,
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
    smap = season_month_map(seasons)
    sorder = season_order(seasons)

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
            var_n = r.get("var_naechte") or []  # variable Kosten je Nacht (deckungsbeitrag.apply)
            day = max(arrival, start)
            last = min(date.fromisoformat(r["abreise"]), end)
            while day < last:
                a = cells[(_key(dimension, r, day, repeat, smap), _key(split_dim, r, day, repeat, smap))]
                i = (day - arrival).days
                v = var_n[i] if i < len(var_n) else 0.0
                a["brutto"] += per_b
                a["netto"] += per_n
                a["var"] += v
                a["naechte"] += 1
                if r["brutto"]:  # ADR/Netto je Nacht nur aus Nächten mit Preis (wie v1.9.2)
                    a["brutto_preis"] += per_b
                    a["netto_preis"] += per_n
                    a["var_preis"] += v
                    a["naechte_preis"] += 1
                a["ids"].add(r["id"])
                day += timedelta(days=1)
        else:
            if not (s_iso <= r["anreise"] < e_iso):
                continue
            a = cells[(_key(dimension, r, arrival, repeat, smap), _key(split_dim, r, arrival, repeat, smap))]
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

    # Verfügbare Nächte je Fach (nur bei Zeit-Dimensionen unterschiedlich).
    # Entscheidung Betreiber 17.11.2026: gesperrte Nächte (Eigennutzung, Renovierung) sind NICHT
    # verfügbar – sie werden abgezogen und gesondert ausgewiesen („gesperrt“). So rechnen
    # Statistik und Finanzen (analytics.analyze) gleich. Gesperrt zählt unabhängig vom
    # Kanalfilter, denn die Sperre gehört der Wohnung, nicht einem Kanal.
    blocked_days = _blocked_days(records, start, end)
    units_ = max(units, 1)

    def _tally(days: list[date]) -> dict[tuple[str | None, str | None], int]:
        """Tage je (Fach, Aufteilung) vorzählen – inkl. Teilsummen (None = alle), einmal statt je Zelle."""
        out: dict[tuple[str | None, str | None], int] = defaultdict(int)
        for day in days:
            rk = _key(dimension, {}, day, set(), smap) if dimension in TIME_DIMS else None
            sk = _key(split_dim, {}, day, set(), smap) if split_dim in TIME_DIMS else None
            out[(rk, sk)] += 1
        return out

    cal_tally = _tally([start + timedelta(days=i) for i in range((end - start).days)])
    blk_tally = _tally(blocked_days)

    def _count(tally: dict[tuple[str | None, str | None], int], row: str | None, ser: str | None) -> int:
        return tally.get((row, ser), 0)

    calendar_days, blocked_days = cal_tally, blk_tally
    days_by_key = (_time_key_days(dimension, start, end, smap) if dimension in TIME_DIMS else {})

    def _scope(row: str, ser: str) -> tuple[str | None, str | None]:
        # Nur Zeit-Dimensionen begrenzen die Tage; andere Dimensionen sehen den ganzen Zeitraum
        return (row if dimension in TIME_DIMS else None, ser if split_dim in TIME_DIMS else None)

    def blocked(row: str, ser: str) -> int:
        return _count(blocked_days, *_scope(row, ser))

    def available(row: str, ser: str) -> float:
        cal = _count(calendar_days, *_scope(row, ser)) * units_
        return max(cal - blocked(row, ser), 0)

    rows = sorted({k[0] for k in cells} | set(days_by_key), key=lambda k: _order(dimension, k, sorder))
    series = sorted({k[1] for k in cells}, key=lambda k: _order(split_dim, k, sorder))
    out_rows = []
    for row in rows:
        vals = {}
        for ser in series:
            acc = cells.get((row, ser))
            if acc is None:
                vals[ser] = {"wert": None if kind == "buchung" else _value(measure, _acc(), available(row, ser)),
                             "n": 0}
                if kind == "nacht":
                    vals[ser]["verfuegbar"] = available(row, ser)
                    vals[ser]["gesperrt"] = blocked(row, ser)
                continue
            n = len(acc["ids"])
            vals[ser] = {"wert": _value(measure, acc, available(row, ser)), "n": n, "wenig_daten": n < MIN_N}
            if kind == "nacht":
                vals[ser]["verfuegbar"] = available(row, ser)
                vals[ser]["gesperrt"] = blocked(row, ser)
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


def _order(dim: str, key: str, sorder: list[str] | None = None) -> tuple[int, str]:
    fixed = sorder if dim == "saison" and sorder else ORDER.get(dim)
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


def message_counts(messages: list[dict[str, Any]]) -> dict[str, int]:
    """Kommunikationsaufwand einer Buchung (v1.17.1): Gastnachrichten und Anliegen.

    Erwartet sichtbare Nachrichten (ohne interne Notizen). Anliegen = Folge von Gastnachrichten
    (type 1) bis zur nächsten Nachricht an den Gast – drei Nachrichten am Stück sind ein Anliegen.
    Eigene Nachrichten werden bewusst nicht gezählt: Smoobu kennzeichnet automatische Vorlagen
    nicht, sie würden den Aufwand je Kanal verfälschen.
    """
    gast = anliegen = alle = 0
    waiting = False
    for m in sorted(messages, key=lambda x: int(x.get("id") or 0)):
        try:
            typ = int(m.get("type") or 0)
        except (TypeError, ValueError):
            continue
        if typ in (1, 2):
            alle += 1
        if typ == 1:
            gast += 1
            if not waiting:
                anliegen += 1
                waiting = True
        elif typ == 2:
            waiting = False
    # alle = sichtbare Nachrichten in beide Richtungen; 0 heißt meist „kein Verlauf vorhanden“
    # (Smoobu liefert für ältere Buchungen keine Nachrichten) → zählt nicht im Aufwand
    return {"gast": gast, "anliegen": anliegen, "alle": alle}


def service(records: list[dict[str, Any]], responses: dict[str, dict[str, Any]], start: date, end: date,
            *, channels: Any = None) -> dict[str, Any]:
    """Antwortzeiten (Median, Anteil < 1 h) für Buchungen mit Anreise im Zeitraum, je Kanal und Monat."""
    match = channel_filter(channels)
    s_iso, e_iso = start.isoformat(), end.isoformat()
    allm: list[float] = []
    by_ch: dict[str, list[float]] = defaultdict(list)
    by_m: dict[str, list[float]] = defaultdict(list)
    covered = total = 0
    # Kommunikationsaufwand je Kanal: nur Buchungen, deren Nachrichten schon gezählt wurden (Feld „gast“)
    effort: dict[str, dict[str, int]] = defaultdict(lambda: {"buchungen": 0, "gast": 0, "anliegen": 0, "mit": 0})
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
        # Nur Buchungen mit Nachrichtenverlauf: ohne jede Nachricht fehlt meist nur die Historie bei Smoobu
        # (sonst würden ältere Buchungen als „0 Anliegen“ den Schnitt verfälschen)
        if "gast" in entry and entry.get("alle", entry.get("gast")):
            e = effort[r["kanal"] or "unbekannt"]
            e["buchungen"] += 1
            e["gast"] += int(entry.get("gast") or 0)
            e["anliegen"] += int(entry.get("anliegen") or 0)
            e["mit"] += 1 if entry.get("gast") else 0

    def agg(values: list[float]) -> dict[str, Any]:
        return {"median": _median(values), "unter_1h": round(sum(1 for v in values if v < 60) / len(values) * 100, 1)
                if values else None, "n": len(values), "wenig_daten": len(values) < MIN_N}

    def eff(e: dict[str, int]) -> dict[str, Any]:
        n = e["buchungen"]
        return {"buchungen": n, "gastnachrichten": e["gast"], "anliegen": e["anliegen"],
                "anliegen_je_buchung": round(e["anliegen"] / n, 2) if n else None,
                "gast_je_buchung": round(e["gast"] / n, 2) if n else None,
                "anteil_mit_nachricht": round(e["mit"] / n * 100, 1) if n else None, "wenig_daten": n < MIN_N}

    tot = {"buchungen": 0, "gast": 0, "anliegen": 0, "mit": 0}
    for e in effort.values():
        for k in tot:
            tot[k] += e[k]
    eff_all = eff(tot)
    base = eff_all["anliegen_je_buchung"]
    aufwand = []
    for k, e in effort.items():
        row = {"kanal": k, **eff(e)}
        # Index: Ø aller Kanäle = 100 (über 100 = Gäste dieses Kanals brauchen mehr Kommunikation)
        row["index"] = round(row["anliegen_je_buchung"] / base * 100) if base and row["anliegen_je_buchung"] is not None else None
        aufwand.append(row)
    aufwand.sort(key=lambda x: -(x["anliegen_je_buchung"] or 0))

    return {"gesamt": agg(allm), "buchungen": total, "geladen": covered,
            "aufwand": {"gesamt": eff_all, "kanaele": aufwand},
            "kanaele": [{"kanal": k, **agg(v)} for k, v in sorted(by_ch.items(), key=lambda kv: -len(kv[1]))],
            "monate": [{"fach": k, **agg(v)} for k, v in sorted(by_m.items())],
            "verteilung": [{"fach": label, "anzahl": sum(1 for v in allm if lo <= v < hi)} for label, lo, hi in
                           (("< 15 min", 0, 15), ("15–60 min", 15, 60), ("1–4 h", 60, 240), ("4–12 h", 240, 720),
                            ("12–24 h", 720, 1440), ("> 24 h", 1440, 10**9))],
            "min_n": MIN_N}


# ---- v1.18.0b7: Ehrentafel (Fun-Statistik) -------------------------------------------------
# Zwei Ranglisten je Zeitraum: „Die Goldene Fußmatte“ (Lieblingsgäste) und „Die Rostige Klobürste“
# (sarkastischer Wanderpokal). Nur zum Spaß – nichts wird gespeichert oder verschickt.
# Wertung: je Kriterium Perzentil-Rang (0–100) innerhalb des Zeitraums, gleich gewichtet.
# Warum Perzentil-Rang statt Rohwert: Euro, Stunden und Nachrichten sind nicht vergleichbar;
# der Rang macht sie gleich schwer und ist robust gegen Ausreißer (ein 900-€-Weihnachtsgast
# erschlägt sonst alle anderen Kriterien). Fehlender Wert (keine Uhrzeit in Smoobu, Nachrichten
# noch nicht geladen) = neutral 50, damit Lücken weder belohnt noch bestraft werden.
RANK_MIN = 5          # darunter: Hinweis „zu wenig Gäste für eine faire Wertung“
RANK_TOP = 3
STAMMGAST_BONUS = 25  # Bonus statt eigenes Kriterium: sonst wöge „Stammgast ja/nein“ so viel wie der Preis

# Kriterien: id → (Richtung, Feld). Richtung +1 = hoher Wert gibt Punkte, −1 = niedriger Wert gibt Punkte
GOLD_CRITERIA = {"preis": (1, "netto_pro_nacht"), "ruhe": (-1, "anliegen"),
                 "puenktlich": (-1, "extra_stunden"), "vorlauf": (1, "vorlauf_tage")}
BRUSH_CRITERIA = {"extra": (1, "extra_stunden"), "billig": (-1, "netto_pro_nacht"),
                  "gespraechig": (1, "nachrichten_je_nacht"), "kurz": (-1, "naechte"),
                  "portal": (-1, "netto_quote")}


def _hours(t: Any) -> float | None:
    """'16:30' → 16.5; leer/ungültig → None."""
    if not t or not isinstance(t, str):
        return None
    parts = t.strip().split(":")
    try:
        return int(parts[0]) + (int(parts[1]) if len(parts) > 1 else 0) / 60
    except (ValueError, IndexError):
        return None


def _pct_rank(values: list[float], v: float | None, direction: int) -> float:
    """Perzentil-Rang 0–100 (Gleichstände halb), Richtung −1 dreht um; None → 50 (neutral)."""
    if v is None or not values:
        return 50.0
    below = sum(1 for x in values if x < v)
    equal = sum(1 for x in values if x == v)
    r = (below + 0.5 * equal) / len(values) * 100
    return round(r if direction > 0 else 100 - r, 1)


def _short_name(r: dict[str, Any]) -> str:
    """Vorname + Initial des Nachnamens („Anna M.“) – volle Namen braucht die Ehrentafel nicht."""
    full = str(r.get("gast") or "").replace(",", " ").split()
    first = str(r.get("vorname") or (full[0] if full else "")).strip()
    rest = [w for w in full if w.casefold() != first.casefold()]
    return f"{first} {rest[-1][0]}." if first and rest else (first or "Gast")


def ranking(records: list[dict[str, Any]], responses: dict[str, dict[str, Any]], start: date, end: date,
            today: date, *, checkin: float = 16.0, checkout: float = 11.0, channels: Any = None) -> dict[str, Any]:
    """Ehrentafel: Top 3 „Goldene Fußmatte“ und Top 3 „Rostige Klobürste“ für Abreisen im Zeitraum.

    Nur abgeschlossene Aufenthalte (Abreise ≤ heute), ohne Stornos, Sperren und Buchungen ohne Preis.
    checkin/checkout = Standardzeiten der Integration in Stunden (16.0 / 11.0); Extra-Stunden =
    früherer Check-in + späterer Check-out laut Smoobu-Uhrzeit.
    """
    match = channel_filter(channels)
    s_iso, e_iso, t_iso = start.isoformat(), end.isoformat(), today.isoformat()
    repeat = _repeat_guests(records)
    guests = []
    for r in records:
        if r["blockiert"] or r["storniert"] or not r["naechte"] or not r["brutto"] or not match(r):
            continue
        if not (s_iso < r["abreise"] <= e_iso) or r["abreise"] > t_iso:
            continue
        ci, co = _hours(r.get("check_in")), _hours(r.get("check_out"))
        extra = None if ci is None and co is None else round(
            max(0.0, checkin - ci if ci is not None else 0.0) + max(0.0, co - checkout if co is not None else 0.0), 2)
        entry = responses.get(str(r["id"])) or {}
        # Nachrichten nur, wenn der Verlauf gezählt wurde und überhaupt Nachrichten da sind
        # (alle = 0 heißt meist: Smoobu liefert für die Buchung keinen Verlauf) – wie im Modul Service
        has_msg = "gast" in entry and entry.get("alle", entry.get("gast"))
        guests.append({
            "id": r["id"], "name": _short_name(r), "kanal": r["kanal"], "anreise": r["anreise"], "abreise": r["abreise"],
            "naechte": r["naechte"], "brutto": r["brutto"], "netto": r["netto"],
            "netto_pro_nacht": round(r["netto"] / r["naechte"], 2),
            "netto_quote": round(r["netto"] / r["brutto"], 3) if r["brutto"] else None,
            "vorlauf_tage": r.get("vorlauf_tage"), "check_in": r.get("check_in"), "check_out": r.get("check_out"),
            "extra_stunden": extra,
            "anliegen": int(entry.get("anliegen") or 0) if has_msg else None,
            "nachrichten": int(entry.get("gast") or 0) if has_msg else None,
            "nachrichten_je_nacht": round(int(entry.get("gast") or 0) / r["naechte"], 2) if has_msg else None,
            "stammgast": bool(_guest_keys(r) & repeat), "hund": bool(r.get("hund")),
        })

    def score(criteria: dict[str, tuple[int, str]], bonus: bool) -> None:
        cols = {cid: [g[f] for g in guests if g[f] is not None] for cid, (_, f) in criteria.items()}
        key = "gold" if bonus else "buerste"
        for g in guests:
            parts = {cid: _pct_rank(cols[cid], g[f], d) for cid, (d, f) in criteria.items()}
            total = sum(parts.values()) / len(parts)
            if bonus and g["stammgast"]:
                total += STAMMGAST_BONUS
            g[key] = {"punkte": round(total, 1), "kriterien": parts,
                      "staerkstes": max(parts, key=lambda c: (parts[c], c))}

    score(GOLD_CRITERIA, True)
    score(BRUSH_CRITERIA, False)
    gold = sorted(guests, key=lambda g: (-g["gold"]["punkte"], g["abreise"]))[:RANK_TOP]
    gold_ids = {g["id"] for g in gold}
    # Wer schon die Fußmatte hat, bekommt nicht auch noch die Klobürste (bei wenigen Gästen möglich)
    brush = sorted((g for g in guests if g["id"] not in gold_ids),
                   key=lambda g: (-g["buerste"]["punkte"], g["abreise"]))[:RANK_TOP]
    return {"gaeste": len(guests), "zu_wenig": len(guests) < RANK_MIN, "min_n": RANK_MIN,
            "standard": {"check_in": checkin, "check_out": checkout},
            "abdeckung": {"uhrzeit": sum(1 for g in guests if g["extra_stunden"] is not None),
                          "nachrichten": sum(1 for g in guests if g["anliegen"] is not None)},
            "goldene_fussmatte": gold, "rostige_kloburste": brush}

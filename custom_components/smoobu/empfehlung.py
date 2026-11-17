"""Bewertung & Preisempfehlung (ab v1.18.0, Wunsch Betreiber 17.11.2026).

Reine Python-Logik ohne HA (testbar). Liefert für die Statistik-Karte:

1. Bewertung je Monat (laufender + 2 folgende): Buchungsstand heute gegen den Buchungsstand
   der Vorjahre am gleichen Tag (Pace). Maßstab ist die Auslastung auf verfügbare Nächte;
   dazu Netto- und Deckungsbeitrags-RevPAR. Einordnung über P25/Median/P75 der Vorjahre.
   Warum Pace statt „Monat gegen Vorjahresmonat“: ein Monat ist erst am Ende fertig; ein
   laufender Monat gegen einen fertigen Vorjahresmonat sieht immer schlecht aus.
2. Preisuntergrenze je Kanal und Aufenthaltsdauer: Basispreis, ab dem der Deckungsbeitrag
   positiv ist (Kanal-Aufschlag, Genius-Rabatt und tatsächliche Kostenquote des Kanals
   eingerechnet). Empfehlungen gehen nie darunter.
3. Empfehlung je Monat: senken / halten / erhöhen in festen Schritten (±10 %, deutlich
   unter P10 −15 %). Bewusst KEIN „optimaler Preis“: wie stark die Nachfrage auf den Preis
   reagiert (Preiselastizität), lässt sich erst mit einer Preis-Historie schätzen – die wird
   erst seit v1.18 gespeichert. Schrittweise Änderungen sind dafür robuster.
   Nur innerhalb des Buchungshorizonts: wird ein Monat noch kaum gebucht (weit weg), sagt
   ein niedriger Stand nichts.
4. Hinweise: einheitlicher Preis, Wochenend-Aufschlag, Einzelnacht, Feiertage, kurze Lücken.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import median
from typing import Any

from .analytics import as_of
from .deckungsbeitrag import CostTable
from .stats import query

HORIZON_DAYS = 60       # Hinweise (Feiertage, Lücken) für die nächsten 60 Tage
# Preisempfehlungen nur für Monate, die innerhalb von 31 Tagen beginnen (laufender + nächster Monat):
# beim Betreiber werden 71 % der Nächte im selben oder im Vormonat gebucht – weiter voraus sagt ein
# niedriger Stand wenig, eine Senkung käme zu früh
ACT_DAYS = 31
MIN_GAP_PP = 10         # Mindestabstand zum Median der Vorjahre (Prozentpunkte), sonst „normal“
STEP = 10               # % Preisschritt
STEP_STRONG = 15        # % Preisschritt, wenn deutlich unter allen Vorjahren
MIN_YEARS = 2           # mindestens 2 Vergleichsjahre für eine Empfehlung
GAP_MAX_NIGHTS = 2      # Lücken bis 2 Nächte gelten als „kurz“
BOOKING = "Booking.com"


@dataclass
class PriceConfig:
    """Preisaufschläge (Smoobu-Preistool) und Fallback-Provisionen aus den Optionen."""

    markups: dict[str, float] = field(default_factory=dict)       # Kanal → % auf den Basispreis
    commissions: dict[str, float] = field(default_factory=dict)   # Kanal → % (Fallback)
    commission_other: float = 15.0
    direct_channels: list[str] = field(default_factory=lambda: ["Direct booking", "Website"])
    genius_discount: float = 10.0
    genius_share: float = 100.0
    # Last-Minute (Wunsch Betreiber 17.11.2026): Fenster in Tagen vor Anreise und höchster Rabatt in %
    lastminute_days: int = 3
    lastminute_max_discount: float = 10.0


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------
def _shift_years(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year - years)
    except ValueError:  # 29.02. → 28.02.
        return day.replace(year=day.year - years, day=28)


def _month_start(day: date) -> date:
    return day.replace(day=1)


def _next_month(day: date) -> date:
    return (day.replace(day=28) + timedelta(days=4)).replace(day=1)


def _pctile(values: list[float], p: float) -> float | None:
    """Perzentil mit linearer Interpolation (p in 0–100)."""
    if not values:
        return None
    v = sorted(values)
    k = (len(v) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return round(v[lo] + (v[hi] - v[lo]) * (k - lo), 1)


def _cell(res: dict[str, Any]) -> dict[str, Any]:
    return res["zeilen"][0]["werte"].get("Gesamt", {"wert": None, "n": 0}) if res["zeilen"] else {"wert": None, "n": 0}


def easter(year: int) -> date:
    """Ostersonntag (gregorianisch, Algorithmus nach Gauß/Meeus)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = ((h + l_ - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def holidays(year: int) -> dict[date, str]:
    """Gesetzliche Feiertage Bayern + Heiligabend/Silvester (relevant für Ferienwohnungen)."""
    e = easter(year)
    return {
        date(year, 1, 1): "Neujahr", date(year, 1, 6): "Heilige Drei Könige",
        e - timedelta(days=2): "Karfreitag", e + timedelta(days=1): "Ostermontag",
        date(year, 5, 1): "Tag der Arbeit", e + timedelta(days=39): "Christi Himmelfahrt",
        e + timedelta(days=50): "Pfingstmontag", e + timedelta(days=60): "Fronleichnam",
        date(year, 8, 15): "Mariä Himmelfahrt", date(year, 10, 3): "Tag der Deutschen Einheit",
        date(year, 11, 1): "Allerheiligen", date(year, 12, 24): "Heiligabend",
        date(year, 12, 25): "1. Weihnachtstag", date(year, 12, 26): "2. Weihnachtstag",
        date(year, 12, 31): "Silvester",
    }


def holiday_nights(year: int) -> dict[date, str]:
    """Nächte mit erhöhter Nachfrage: Nacht vor einem Feiertag sowie Heiligabend/Weihnachten/Silvester."""
    out: dict[date, str] = {}
    for md in ((12, 24), (12, 25), (12, 31)):
        out[date(year, *md)] = holidays(year)[date(year, *md)]
    for day, name in holidays(year).items():
        eve = day - timedelta(days=1)
        if eve not in out:  # Heiligabend/1. Weihnachtstag sind schon eigene Feiertagsnächte
            out[eve] = f"vor {name}"
    return out


def _occupied(records: list[dict[str, Any]], with_blocked: bool = True) -> set[date]:
    occ: set[date] = set()
    for r in records:
        if r["storniert"] or not r["naechte"] or (r["blockiert"] and not with_blocked):
            continue
        day, last = date.fromisoformat(r["anreise"]), date.fromisoformat(r["abreise"])
        while day < last:
            occ.add(day)
            day += timedelta(days=1)
    return occ


# ---------------------------------------------------------------------------
# Kanalfaktor und Preisuntergrenze
# ---------------------------------------------------------------------------
def channel_cost_ratio(records: list[dict[str, Any]], channel: str, cfg: PriceConfig, today: date) -> tuple[float, str]:
    """Tatsächliche Kostenquote (Provision + Gebühren ÷ Brutto) der letzten 24 Monate, sonst Option."""
    since = _shift_years(today, 2).isoformat()
    brutto = kosten = 0.0
    for r in records:
        if r["blockiert"] or r["storniert"] or r["kanal"] != channel or r["anreise"] < since or not r["brutto"]:
            continue
        brutto += r["brutto"]
        kosten += r["brutto"] - r["netto"]
    if brutto > 0:
        return kosten / brutto, "gemessen"
    if channel in cfg.direct_channels:
        return 0.0, "direkt"
    return float(cfg.commissions.get(channel, cfg.commission_other)) / 100, "Option"


def channel_factor(channel: str, ratio: float, cfg: PriceConfig) -> float:
    """Netto je € Basispreis: (1 + Aufschlag) × (1 − Genius-Anteil × Rabatt) × (1 − Kostenquote)."""
    markup = float(cfg.markups.get(channel, 0.0)) / 100
    genius = cfg.genius_share / 100 * cfg.genius_discount / 100 if channel == BOOKING else 0.0
    return (1 + markup) * (1 - genius) * (1 - ratio)


def floor_price(table: CostTable, arrival: date, nights: int, factor: float) -> float | None:
    """Basispreis je Nacht, ab dem der Deckungsbeitrag ≥ 0 ist."""
    if factor <= 0 or nights <= 0:
        return None
    return table.stay(arrival, nights) / (nights * factor)


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------
def recommend(
    records: list[dict[str, Any]],
    rates: dict[str, dict[str, Any]],
    table: CostTable,
    cfg: PriceConfig,
    today: date,
    *,
    first: date | None = None,
    months: int = 3,
) -> dict[str, Any]:
    guests = [r for r in records if not r["blockiert"]]
    channels = sorted({r["kanal"] for r in guests if r["kanal"]} | set(cfg.markups))
    # Kanäle mit Buchungen der letzten 24 Monate oder Aufschlag (die anderen sind irrelevant)
    since = _shift_years(today, 2).isoformat()
    active = [c for c in channels if c in cfg.markups or any(r["kanal"] == c and r["anreise"] >= since for r in guests)]
    ratios = {c: channel_cost_ratio(records, c, cfg, today) for c in active}
    factors = {c: channel_factor(c, ratios[c][0], cfg) for c in active}

    # Basispreise der nächsten 60 Tage (Smoobu /api/rates)
    prices = {d: float(v["price"]) for d, v in (rates or {}).items() if v.get("price") not in (None, "")}
    min_stay = {d: v.get("min_length_of_stay") for d, v in (rates or {}).items()}
    base_now = prices.get(today.isoformat()) or (median(prices.values()) if prices else None)
    uniform = bool(prices) and len(set(prices.values())) == 1

    # Buchungshorizont aus den Daten: Anteil der Nächte, die im selben oder im Vormonat gebucht wurden
    short = query(records, "naechte", "vorlauf_monate", _shift_years(today, 3), today)
    by_lead = {z["fach"]: z["werte"].get("Gesamt", {}).get("wert") or 0 for z in short["zeilen"]}
    total = sum(by_lead.values())
    short_share = round((by_lead.get("gleicher Monat", 0) + by_lead.get("1 Monat", 0)) / total * 100) if total else None

    out_months = []
    m0 = _month_start(today)
    for i in range(months):
        start = m0
        for _ in range(i):
            start = _next_month(start)
        out_months.append(_month(records, prices, table, cfg, factors, today, start, _next_month(start), first))

    hints = _hints(records, prices, min_stay, table, factors, today, uniform, base_now)
    lm = _lastminute(records, prices, table, factors, cfg, today, {m["monat"]: m["bewertung"] for m in out_months})
    if lm:
        hints.insert(1 if hints and hints[0]["typ"] == "einheitlich" else 0, lm)
    return {
        "heute": today.isoformat(),
        "basispreis": {
            "heute": base_now,
            "min": min(prices.values()) if prices else None,
            "max": max(prices.values()) if prices else None,
            "einheitlich": uniform,
            "tage": len(prices),
        },
        "kanaele": [
            {"kanal": c, "aufschlag": cfg.markups.get(c, 0.0), "kostenquote": round(ratios[c][0] * 100, 1),
             "kostenquote_quelle": ratios[c][1], "genius": c == BOOKING and cfg.genius_share > 0,
             "netto_je_euro": round(factors[c], 3),
             "netto_je_nacht": round(base_now * factors[c], 2) if base_now else None}
            for c in active
        ],
        "kurzfristig_prozent": short_share,
        "monate": out_months,
        "hinweise": hints,
        "kosten_je_nacht": {f"{m:02d}": table.month(m, today.year) for m in range(1, 13)},
        "je_aufenthalt": round(table.cfg.per_stay, 2),
        "annahmen": [
            "Preisschritte statt „optimalem Preis“: wie stark die Nachfrage auf den Preis reagiert, ist noch unbekannt "
            "(Preis-Historie erst seit v1.18).",
            "Untergrenze = Deckungsbeitrag 0 € – darunter kostet jede Buchung Geld. Fixkosten sind nicht enthalten.",
            "Kostenquote je Kanal aus den Buchungen der letzten 24 Monate (sonst aus den Optionen).",
        ],
    }


def _month(records, prices, table: CostTable, cfg: PriceConfig, factors, today: date, start: date, end: date,
           first: date | None) -> dict[str, Any]:
    """Bewertung + Empfehlung für einen Monat [start, end)."""
    key = start.strftime("%Y-%m")
    now = as_of(records, today)
    occ = _cell(query(now, "auslastung", "gesamt", start, end))
    rev = _cell(query(now, "netto_revpar", "gesamt", start, end))
    dbr = _cell(query(now, "db_revpar", "gesamt", start, end))
    nights = _cell(query(now, "naechte", "gesamt", start, end))
    # Freie, noch buchbare Nächte ab heute
    occupied = _occupied(records)
    day, free = max(start, today), 0
    while day < end:
        free += day not in occupied
        day += timedelta(days=1)

    # Vergleich: Stand am gleichen Tag der Vorjahre + Endstand der Vorjahre
    comp = []
    for k in range(1, 8):
        s_k, e_k, t_k = _shift_years(start, k), _shift_years(end, k), _shift_years(today, k)
        if first is not None and s_k < first:
            break
        then = as_of(records, t_k)
        c_occ = _cell(query(then, "auslastung", "gesamt", s_k, e_k))
        if not c_occ.get("verfuegbar"):
            continue
        final = _cell(query(records, "auslastung", "gesamt", s_k, e_k))
        comp.append({
            "jahr": s_k.year,
            "stand": c_occ["wert"] or 0.0,
            "ende": final["wert"] or 0.0,
            "netto_revpar_ende": _cell(query(records, "netto_revpar", "gesamt", s_k, e_k))["wert"],
            "db_revpar_ende": _cell(query(records, "db_revpar", "gesamt", s_k, e_k))["wert"],
        })
    stands = [c["stand"] for c in comp]
    p10, p25, p50, p75 = (_pctile(stands, p) for p in (10, 25, 50, 75))
    cur = occ["wert"] or 0.0
    if len(comp) < MIN_YEARS:
        rating = "unbekannt"
    elif cur < (p25 or 0) and (p50 or 0) - cur >= MIN_GAP_PP:
        rating = "schwach"
    elif cur > (p75 or 0) and cur - (p50 or 0) >= MIN_GAP_PP:
        rating = "stark"
    else:
        rating = "normal"
    # Prognose Endstand: Stand heute + mittlere Nachbuchung der Vorjahre (additiv wie das Pace-Modell)
    pickup = median([c["ende"] - c["stand"] for c in comp]) if comp else None
    forecast = round(min(cur + pickup, 100.0), 1) if pickup is not None else None

    # Preisuntergrenze je Kanal für 1/2/3 Nächte (Ankunft Monatsmitte, mind. heute)
    mid = max(start.replace(day=15), today) if start.replace(day=15) < end else start
    floors = {c: {str(n): (round(fp, 2) if (fp := floor_price(table, mid, n, f)) else None) for n in (1, 2, 3)}
              for c, f in factors.items()}
    month_prices = [p for d, p in prices.items() if start.isoformat() <= d < end.isoformat()]
    base = median(month_prices) if month_prices else None
    # Maßgebliche Untergrenze für Empfehlungen: teuerster Kanal bei 2 Nächten (typischer Aufenthalt)
    floor2 = max((v["2"] for v in floors.values() if v["2"]), default=None)

    action, step, reason = "halten", 0, ""
    days_ahead = (start - today).days
    if rating == "unbekannt":
        reason = f"Zu wenig Vergleichsjahre (n = {len(comp)}) für eine Empfehlung."
    elif days_ahead > ACT_DAYS:
        reason = (f"Noch früh: beginnt in {days_ahead} Tagen, die meisten Nächte werden erst im selben oder im Vormonat "
                  "gebucht. Erneut prüfen, wenn der Vormonat läuft.")
    elif free == 0:
        reason = "Keine freien Nächte mehr."
    elif rating == "schwach":
        step = -(STEP_STRONG if p10 is not None and cur < p10 else STEP)
        action = "senken"
        reason = f"Buchungsstand {cur:.0f} % liegt unter dem üblichen Stand der Vorjahre (P25 {p25:.0f} %, Median {p50:.0f} %)."
    elif rating == "stark":
        step, action = STEP, "erhöhen"
        reason = f"Buchungsstand {cur:.0f} % liegt über dem üblichen Stand der Vorjahre (P75 {p75:.0f} %)."
    else:
        reason = f"Buchungsstand {cur:.0f} % im üblichen Bereich der Vorjahre (P25 {p25:.0f} – P75 {p75:.0f} %)."
    new_price = None
    if base and step:
        new_price = round(base * (1 + step / 100))
        if action == "senken" and floor2 and new_price < floor2:
            new_price = int(-(-floor2 // 1))  # aufrunden auf die Untergrenze
            if new_price >= base:
                action, step, new_price = "halten", 0, None
                reason += f" Senken lohnt nicht: die Untergrenze ({floor2:.0f} €) liegt schon am aktuellen Preis."
    return {
        "monat": key,
        "beginnt_in_tagen": days_ahead,
        "auslastung_stand": cur,
        "naechte_gebucht": nights["wert"] or 0,
        "verfuegbar": occ.get("verfuegbar"),
        "gesperrt": occ.get("gesperrt"),
        "frei_ab_heute": free,
        "netto_revpar_stand": rev["wert"],
        "db_revpar_stand": dbr["wert"],
        "vergleich": {"jahre": comp, "n": len(comp), "p10": p10, "p25": p25, "median": p50, "p75": p75},
        "prognose_auslastung": forecast,
        "bewertung": rating,
        "basispreis": base,
        "untergrenze": floors,
        "untergrenze_massgeblich": floor2,
        "kosten_je_nacht": table.month(start.month, start.year),
        "empfehlung": {"aktion": action, "prozent": step, "preis_neu": new_price, "grund": reason},
    }


def _hints(records, prices, min_stay, table: CostTable, factors, today: date, uniform: bool,
           base: float | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    start2 = _shift_years(today, 2)

    # 1. Einheitlicher Preis
    if uniform and base:
        out.append({"typ": "einheitlich", "titel": f"Alle {len(prices)} Tage kosten {base:.0f} €",
                    "text": "Wochenenden, Feiertage und Ferien werden nicht unterschieden. Die Hinweise unten zeigen, wo das Geld kostet."})

    # 2. Wochenende: Auslastung Fr/Sa-Nächte gegen So–Do (letzte 24 Monate, verfügbare Nächte)
    wd = query(records, "auslastung", "wochentag", start2, today)
    occ = {z["fach"]: z["werte"].get("Gesamt", {}) for z in wd["zeilen"]}
    we_av = sum(occ.get(d, {}).get("verfuegbar") or 0 for d in ("Fr", "Sa"))
    wk_av = sum(occ.get(d, {}).get("verfuegbar") or 0 for d in ("So", "Mo", "Di", "Mi", "Do"))
    nights = query(records, "naechte", "wochentag", start2, today)
    n = {z["fach"]: z["werte"].get("Gesamt", {}).get("wert") or 0 for z in nights["zeilen"]}
    we_n, wk_n = n.get("Fr", 0) + n.get("Sa", 0), sum(n.get(d, 0) for d in ("So", "Mo", "Di", "Mi", "Do"))
    if we_av and wk_av:
        we_occ, wk_occ = we_n / we_av * 100, wk_n / wk_av * 100
        gap = we_occ - wk_occ
        if gap >= 10 and base:
            pct = 15 if gap >= 20 else 10
            per_year = we_n / 2 * base * pct / 100  # Fr/Sa-Nächte pro Jahr (24 Monate ÷ 2)
            out.append({"typ": "wochenende", "titel": f"Wochenend-Aufschlag +{pct} % prüfen",
                        "text": f"Fr/Sa-Nächte sind zu {we_occ:.0f} % belegt, So–Do zu {wk_occ:.0f} % (letzte 24 Monate). "
                                f"+{pct} % auf Fr/Sa ≈ +{per_year:.0f} € im Jahr bei gleicher Belegung.",
                        "wert_eur": round(per_year), "prozent": pct, "wochentage": [4, 5]})
        elif base:
            out.append({"typ": "wochenende", "titel": "Kein deutlicher Wochenend-Effekt",
                        "text": f"Fr/Sa {we_occ:.0f} % gegen So–Do {wk_occ:.0f} % Auslastung (letzte 24 Monate) – ein Aufschlag drängt eher Gäste weg."})

    # 3. Einzelnacht: Anteil 1-Nacht-Buchungen und Deckungsbeitrag 1 vs. 2 Nächte
    recent = [r for r in records if not r["blockiert"] and not r["storniert"] and r["naechte"] and r["anreise"] >= start2.isoformat()]
    if recent and base and factors:
        ones = sum(1 for r in recent if r["naechte"] == 1)
        share = ones / len(recent) * 100
        worst = min(factors, key=factors.get)
        f = factors[worst]
        db1 = base * f - table.stay(today, 1)
        db2 = (2 * base * f - table.stay(today, 2)) / 2
        surcharge = table.cfg.per_stay / 2
        if share >= 15 or db1 < 0.6 * db2:
            out.append({"typ": "einzelnacht", "titel": f"Einzelnächte: {share:.0f} % der Buchungen",
                        "text": f"Deckungsbeitrag über {worst} heute: 1 Nacht {db1:.0f} €, bei 2 Nächten {db2:.0f} € je Nacht. "
                                f"Ein Aufschlag für 1 Nacht von ≈ {surcharge:.0f} € (halbe Reinigung + Wäsche) gleicht das aus – "
                                f"oder Mindestaufenthalt 2 Nächte in schwachen Monaten.",
                        "wert_eur": round(ones / 2 * surcharge), "mindestaufenthalt": 2})

    # 4. Feiertage in den nächsten 60 Tagen zum Normalpreis
    if prices and base:
        occupied = _occupied(records, with_blocked=False)
        earliest = min((date.fromisoformat(r["anreise"]) for r in records), default=None)
        found = []
        for y in sorted({today.year, (today + timedelta(days=HORIZON_DAYS)).year}):
            for night, name in sorted(holiday_nights(y).items()):
                iso = night.isoformat()
                if not (today <= night < today + timedelta(days=HORIZON_DAYS)) or iso not in prices:
                    continue
                if any(f["datum"] == iso for f in found):  # Silvester = „vor Neujahr“ des Folgejahres
                    continue
                if prices[iso] > base or night in occupied:
                    continue
                # Belegung derselben Feiertagsnacht in den Vorjahren
                hist = []
                for k in range(1, 6):
                    prev = {v: d for d, v in holiday_nights(y - k).items()}.get(name)
                    if prev and earliest and prev >= earliest:
                        hist.append(prev in occupied)
                found.append({"datum": iso, "name": name, "vorjahre_belegt": sum(hist), "vorjahre": len(hist)})
        if found:
            out.append({"typ": "feiertag", "titel": f"{len(found)} Feiertagsnächte zum Normalpreis",
                        "text": "Nächte vor Feiertagen und über Weihnachten/Silvester sind gefragter – Aufschlag (z. B. +20 %) "
                                "oder Mindestaufenthalt prüfen.", "tage": found, "prozent": 20})

    # 5. Kurze Lücken (1–2 Nächte zwischen zwei Belegungen) in den nächsten 60 Tagen
    occ_all = _occupied(records)
    gaps, day, end = [], today, today + timedelta(days=HORIZON_DAYS)
    while day < end:
        if day in occ_all or (day - timedelta(days=1)) not in occ_all:
            day += timedelta(days=1)
            continue
        run = 0
        while day + timedelta(days=run) not in occ_all and run <= GAP_MAX_NIGHTS:
            run += 1
        if run <= GAP_MAX_NIGHTS and (day + timedelta(days=run)) in occ_all and day + timedelta(days=run) <= end:
            ms = min_stay.get(day.isoformat())
            floor = max((fp for f in factors.values() if (fp := floor_price(table, day, run, f))), default=None)
            price = prices.get(day.isoformat())
            # Vorschlag: −15 %, aber nie unter der Untergrenze (aufgerundet)
            proposal = None
            if price:
                proposal = round(price * 0.85)
                if floor and proposal < floor:
                    proposal = int(-(-floor // 1))
                proposal = min(proposal, price)
            gaps.append({"von": day.isoformat(), "naechte": run, "mindestaufenthalt": ms,
                         "buchbar": not ms or run >= int(ms), "preis": price,
                         "untergrenze": round(floor, 2) if floor else None, "vorschlag_preis": proposal,
                         "tage": [(day + timedelta(days=i)).isoformat() for i in range(run)]})
        day += timedelta(days=max(run, 1))
    if gaps:
        out.append({"typ": "luecke", "titel": f"{len(gaps)} kurze Lücke{'n' if len(gaps) > 1 else ''} in den nächsten 60 Tagen",
                    "text": "Einzelne Nächte zwischen zwei Gästen bucht kaum jemand zum vollen Preis. Rabatt bis zur Untergrenze "
                            "(Reinigung fällt ohnehin an) oder als Verlängerung den Nachbargästen anbieten.", "luecken": gaps})
    return out


def _lead_stats(records: list[dict[str, Any]], days: int, today: date) -> dict[str, Any]:
    """Last-Minute (Vorlauf ≤ days) gegen frühere Buchungen, letzte 24 Monate.

    Roh: Anteil und Netto je Nacht. Bereinigt: Unterschied Netto/Nacht innerhalb desselben Kanals
    und derselben Saison (Monat), gewichtet nach Nächten – so verfälschen der Booking-Aufschlag
    (+45 %) oder ein teurer Sommer den Vergleich nicht. Nur Gruppen mit je ≥ 2 Buchungen zählen.
    """
    since = _shift_years(today, 2).isoformat()
    valid = [r for r in records if not r["blockiert"] and not r["storniert"] and r["naechte"] and r["brutto"]
             and r["vorlauf_tage"] is not None and since <= r["anreise"] < today.isoformat()]
    lm = [r for r in valid if r["vorlauf_tage"] <= days]
    early = [r for r in valid if r["vorlauf_tage"] > days]

    def per_night(items):
        n = sum(r["naechte"] for r in items)
        return (sum(r["netto"] for r in items) / n) if n else None

    groups: dict[tuple[str, int], dict[str, list]] = {}
    for r in valid:
        g = groups.setdefault((r["kanal"], int(r["anreise"][5:7])), {"lm": [], "fr": []})
        g["lm" if r["vorlauf_tage"] <= days else "fr"].append(r)
    diff_w = weight = 0.0
    for g in groups.values():
        if len(g["lm"]) >= 2 and len(g["fr"]) >= 2:
            a, b = per_night(g["lm"]), per_night(g["fr"])
            w = sum(r["naechte"] for r in g["lm"])
            diff_w += (a - b) / b * w
            weight += w
    return {
        "buchungen": len(lm), "anteil": round(len(lm) / len(valid) * 100) if valid else None,
        "netto_lm": round(per_night(lm), 2) if lm else None, "netto_frueh": round(per_night(early), 2) if early else None,
        "aufenthalt_lm": round(sum(r["naechte"] for r in lm) / len(lm), 1) if lm else None,
        "bereinigt_prozent": round(diff_w / weight * 100, 1) if weight else None,
        "bereinigt_naechte": int(weight),
    }


def _lastminute(records, prices, table: CostTable, factors, cfg: PriceConfig, today: date,
                ratings: dict[str, str]) -> dict[str, Any] | None:
    """Freie Nächte im Last-Minute-Fenster + Empfehlung je Nacht.

    Standard: kein Rabatt (beim Betreiber bringen Last-Minute-Buchungen netto am meisten). Rabatt (bis
    cfg.lastminute_max_discount, nie unter der Untergrenze) nur für eine Nacht, die eine Lücke
    zwischen zwei Gästen ist, oder in einem Monat mit Bewertung „schwach“. Aufschlag (+5 %) nur,
    wenn der bereinigte Vergleich (gleicher Kanal, gleicher Monat) eine Prämie ≥ 5 % auf
    mindestens 10 Nächten zeigt und der Monat nicht schwach ist.
    """
    days = max(int(cfg.lastminute_days), 1)
    stats = _lead_stats(records, days, today)
    occ = _occupied(records)
    free = []
    for i in range(days):
        night = today + timedelta(days=i)
        iso = night.isoformat()
        if night in occ or iso not in prices:
            continue
        price = prices[iso]
        # Lücke: belegt am Vortag und spätestens 2 Nächte danach wieder belegt
        gap = (night - timedelta(days=1)) in occ and any((night + timedelta(days=k)) in occ for k in (1, 2))
        weak = ratings.get(iso[:7]) == "schwach"
        floor = max((fp for f in factors.values() if (fp := floor_price(table, night, 1 if gap else 2, f))), default=None)
        proposal, why = None, ""
        if gap or weak:
            proposal = round(price * (1 - cfg.lastminute_max_discount / 100))
            if floor and proposal < floor:
                proposal = int(-(-floor // 1))
            if proposal >= price:
                proposal, why = None, "Untergrenze erreicht – kein Rabatt möglich"
            else:
                why = "Lücke zwischen zwei Gästen" if gap else "Monat schwach gebucht"
        free.append({"datum": iso, "preis": price, "luecke": gap, "monat_schwach": weak,
                     "untergrenze": round(floor, 2) if floor else None, "vorschlag_preis": proposal, "grund": why})
    premium = (stats["bereinigt_prozent"] is not None and stats["bereinigt_prozent"] >= 5
               and stats["bereinigt_naechte"] >= 10)
    if not free and not stats["buchungen"]:
        return None
    discount = [f for f in free if f["vorschlag_preis"]]
    if not free:
        title = f"Last-Minute: die nächsten {days} Tage sind belegt"
    elif discount:
        title = f"Last-Minute: {len(discount)} von {len(free)} freien Nächten gezielt günstiger"
    else:
        title = f"Last-Minute: {len(free)} freie Nächte – kein Rabatt empfohlen"
    raw = (f"{stats['anteil']} % der Buchungen kommen in den letzten {days} Tagen vor Anreise "
           f"(netto {stats['netto_lm']:.0f} € je Nacht gegen {stats['netto_frueh']:.0f} € bei früherer Buchung, "
           f"Ø {stats['aufenthalt_lm']} Nächte)." if stats["netto_lm"] and stats["netto_frueh"] else "")
    adj = (f" Bereinigt um Kanal und Monat: {stats['bereinigt_prozent']:+.0f} % netto je Nacht "
           f"({stats['bereinigt_naechte']} Nächte)." if stats["bereinigt_prozent"] is not None else
           " Für einen bereinigten Vergleich (gleicher Kanal und Monat) gibt es noch zu wenige Buchungen.")
    advice = (" Kurzfristige Gäste zahlen also eher mehr – ein Rabatt würde vor allem Geld verschenken."
              if (stats["netto_lm"] or 0) >= (stats["netto_frueh"] or 0) else
              " Kurzfristige Buchungen bringen hier weniger – ein moderater Rabatt kann freie Nächte retten.")
    return {"typ": "lastminute", "titel": title, "text": (raw + adj + advice).strip(), "tage_fenster": days,
            "naechte": free, "statistik": stats, "aufschlag_prozent": 5 if premium else None,
            "rabatt_max": cfg.lastminute_max_discount}


def from_options(options: Any, commissions: dict[str, float], commission_other: float,
                 direct: list[str]) -> PriceConfig:
    """PriceConfig aus den Optionen des Eintrags."""
    from .const import (  # noqa: PLC0415
        CONF_CHANNEL_MARKUPS, CONF_GENIUS_DISCOUNT, CONF_GENIUS_SHARE, CONF_LASTMINUTE_DAYS,
        CONF_LASTMINUTE_MAX_DISCOUNT, DEFAULT_CHANNEL_MARKUPS, DEFAULT_GENIUS_DISCOUNT, DEFAULT_GENIUS_SHARE,
        DEFAULT_LASTMINUTE_DAYS, DEFAULT_LASTMINUTE_MAX_DISCOUNT,
    )

    o = options or {}
    return PriceConfig(
        markups={str(k): float(v) for k, v in (o.get(CONF_CHANNEL_MARKUPS, DEFAULT_CHANNEL_MARKUPS)).items()},
        commissions=dict(commissions), commission_other=float(commission_other), direct_channels=list(direct),
        genius_discount=float(o.get(CONF_GENIUS_DISCOUNT, DEFAULT_GENIUS_DISCOUNT)),
        genius_share=float(o.get(CONF_GENIUS_SHARE, DEFAULT_GENIUS_SHARE)),
        lastminute_days=int(o.get(CONF_LASTMINUTE_DAYS, DEFAULT_LASTMINUTE_DAYS)),
        lastminute_max_discount=float(o.get(CONF_LASTMINUTE_MAX_DISCOUNT, DEFAULT_LASTMINUTE_MAX_DISCOUNT)),
    )


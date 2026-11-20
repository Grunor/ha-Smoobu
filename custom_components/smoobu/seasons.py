"""Saison-Definition (ab v1.18.0, Wunsch Betreiber 20.11.2026).

Die Saisons sind frei benennbar (2–6 Stück) und je durch ihren Startmonat festgelegt; jede reicht
bis zum Monat vor dem Start der nächsten, die letzte läuft über den Jahreswechsel bis zur ersten.
So decken sie das Jahr lückenlos ab, und jede Saison ist ein zusammenhängender Zeitraum – damit
funktionieren Blättern ‹ ›, Vorperiode und Vorjahr im Zeitraum-Filter wie bei Monat/Quartal.

Verworfen: taggenaue Grenzen (Monats-Auswertungen müssten Monate teilen) und feste vier
Jahreszeiten mit verschiebbaren Grenzen (zu unflexibel für Haupt-/Nebensaison).
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

# Standard = bisheriges Verhalten (meteorologische Jahreszeiten)
DEFAULT_SEASONS: list[dict[str, Any]] = [
    {"name": "Winter", "start": 12},
    {"name": "Frühling", "start": 3},
    {"name": "Sommer", "start": 6},
    {"name": "Herbst", "start": 9},
]
MIN_SEASONS, MAX_SEASONS, MAX_NAME = 2, 6, 30


def validate(value: Any) -> list[dict[str, Any]]:
    """Eingabe prüfen und normalisieren (sortiert nach Startmonat). Fehlercodes für die Einstellungs-Karte."""
    if not isinstance(value, list) or not MIN_SEASONS <= len(value) <= MAX_SEASONS:
        raise vol.Invalid("invalid_season_count")
    out, names, starts = [], set(), set()
    for item in value:
        if not isinstance(item, dict):
            raise vol.Invalid("invalid_season")
        name = " ".join(str(item.get("name") or "").split())[:MAX_NAME]
        try:
            start = int(item.get("start"))
        except (TypeError, ValueError) as err:
            raise vol.Invalid("invalid_season_start") from err
        if not name:
            raise vol.Invalid("invalid_season_name")
        if not 1 <= start <= 12:
            raise vol.Invalid("invalid_season_start")
        if name.casefold() in names:
            raise vol.Invalid("invalid_season_duplicate_name")
        if start in starts:
            raise vol.Invalid("invalid_season_duplicate_start")
        names.add(name.casefold())
        starts.add(start)
        out.append({"name": name, "start": start})
    return sorted(out, key=lambda s: s["start"])


def from_options(options: Any) -> list[dict[str, Any]]:
    """Saisons aus den Optionen; ungültige oder fehlende Werte → Standard (nie Fehler im Betrieb)."""
    raw = (options or {}).get("saisons")
    if raw:
        try:
            return validate(raw)
        except vol.Invalid:
            pass
    return sorted((dict(s) for s in DEFAULT_SEASONS), key=lambda s: s["start"])


def month_map(seasons: list[dict[str, Any]] | None) -> dict[int, str]:
    """Monat (1–12) → Saisonname."""
    ss = sorted(seasons or DEFAULT_SEASONS, key=lambda s: s["start"])
    out = {}
    for m in range(1, 13):
        cur = [s for s in ss if s["start"] <= m]
        out[m] = (cur[-1] if cur else ss[-1])["name"]  # vor dem ersten Start: letzte Saison (über den Jahreswechsel)
    return out


def order(seasons: list[dict[str, Any]] | None) -> list[str]:
    """Reihenfolge für Auswertungen: ab der Saison, in der der Januar liegt (Standard: Winter, Frühling, …)."""
    ss = sorted(seasons or DEFAULT_SEASONS, key=lambda s: s["start"])
    first = month_map(ss)[1]
    i = [s["name"] for s in ss].index(first)
    return [s["name"] for s in ss[i:] + ss[:i]]


# ---------------------------------------------------------------------------
# Automatische Erkennung aus der Vergangenheit (Wunsch Betreiber 20.11.2026)
# ---------------------------------------------------------------------------
# Kennzahl je Kalendermonat: RevPAR (Umsatz je verfügbarer Nacht) – verbindet Preis und Auslastung, genau das,
# was eine Saison ausmacht. Je abgeschlossenem Jahr auf den Jahres-Ø normiert (Niveau-Unterschiede zwischen den
# Jahren fallen raus), dann Median über die Jahre (ein Ausreißerjahr wie 2020 verschiebt nichts).
# Aufteilung: alle Kombinationen von k Startmonaten (k = 2…4, je Saison ≥ 2 Monate, über den Jahreswechsel
# möglich) durchprobieren, Maß = Summe der quadrierten Abweichungen vom Saison-Mittel (kleinste gewinnt).
# Bei 12 Monaten sind das höchstens 495 Kombinationen – exakt statt Näherung.
from datetime import date as _date, timedelta as _td
from itertools import combinations as _comb
from statistics import median as _median

LEVEL_NAMES = {2: ["Hauptsaison", "Nebensaison"], 3: ["Hauptsaison", "Zwischensaison", "Nebensaison"],
               4: ["Hauptsaison", "Mittelsaison", "Zwischensaison", "Nebensaison"]}
MIN_YEARS = 2  # weniger abgeschlossene Jahre: kein Vorschlag (zu wenig Daten)


def monthly_profile(records: list[dict[str, Any]], today: Any, units: int = 1) -> dict[str, Any]:
    """Normiertes RevPAR- und Auslastungsprofil je Kalendermonat aus abgeschlossenen Jahren."""
    rev: dict[tuple[int, int], float] = {}
    nights: dict[tuple[int, int], int] = {}
    blocked: dict[tuple[int, int], int] = {}
    for r in records:
        if r.get("storniert"):
            continue
        day, end = _date.fromisoformat(r["anreise"]), _date.fromisoformat(r["abreise"])
        per = (r.get("brutto") or 0) / r["naechte"] if r.get("naechte") else 0
        while day < end:
            k = (day.year, day.month)
            if r.get("blockiert"):
                blocked[k] = blocked.get(k, 0) + 1
            else:
                rev[k] = rev.get(k, 0.0) + per
                nights[k] = nights.get(k, 0) + 1
            day += _td(days=1)
    years = sorted({y for y, _ in nights})
    # abgeschlossene Jahre mit Buchungen in mindestens 6 Monaten (sonst Teiljahr am Anfang der Historie)
    full = [y for y in years if y < today.year and sum(1 for m in range(1, 13) if nights.get((y, m))) >= 6]
    per_year = []
    occ: dict[int, list[float]] = {m: [] for m in range(1, 13)}
    for y in full:
        vals = []
        for m in range(1, 13):
            days = ((_date(y + (m == 12), m % 12 + 1, 1)) - _date(y, m, 1)).days
            avail = max(days * units - blocked.get((y, m), 0), 0)
            vals.append(rev.get((y, m), 0.0) / avail if avail else 0.0)
            occ[m].append(nights.get((y, m), 0) / avail * 100 if avail else 0.0)
        mean = sum(vals) / 12
        if mean > 0:
            per_year.append([v / mean for v in vals])
    if len(per_year) < MIN_YEARS:
        return {"jahre": full, "profil": None, "auslastung": None}
    profile = [_median([py[m] for py in per_year]) for m in range(12)]
    return {"jahre": full, "profil": profile, "auslastung": [_median(occ[m]) if occ[m] else 0.0 for m in range(1, 13)]}


def _split(profile: list[float], k: int) -> tuple[float, list[int]] | None:
    best = None
    for starts in _comb(range(12), k):
        lens = [((starts[(i + 1) % k] - s) % 12) or 12 for i, s in enumerate(starts)]
        if min(lens) < 2:
            continue
        sse = 0.0
        for s, n in zip(starts, lens):
            vals = [profile[(s + j) % 12] for j in range(n)]
            mu = sum(vals) / n
            sse += sum((v - mu) ** 2 for v in vals)
        if best is None or sse < best[0]:
            best = (sse, list(starts))
    return best


def detect(records: list[dict[str, Any]], today: Any, units: int = 1) -> dict[str, Any]:
    """Saison-Vorschläge (2, 3, 4 Saisons) mit Kennzahlen und Empfehlung."""
    prof = monthly_profile(records, today, units)
    p = prof["profil"]
    if not p:
        return {"vorschlaege": [], "jahre": prof["jahre"], "grund": "zu_wenig_jahre", "min_jahre": MIN_YEARS}
    mu = sum(p) / 12
    total = sum((v - mu) ** 2 for v in p) or 1e-9
    out = []
    for k in (2, 3, 4):
        res = _split(p, k)
        if not res:
            continue
        sse, starts = res
        segs = []
        for i, s in enumerate(starts):
            n = ((starts[(i + 1) % k] - s) % 12) or 12
            months = [(s + j) % 12 for j in range(n)]
            segs.append({"start": s + 1, "monate": [m + 1 for m in months],
                         "index": round(sum(p[m] for m in months) / n * 100),
                         "auslastung": round(sum(prof["auslastung"][m] for m in months) / n, 1)})
        for name, seg in zip(LEVEL_NAMES[k], sorted(segs, key=lambda x: -x["index"])):
            seg["name"] = name
        out.append({"anzahl": k, "erklaert": round((1 - sse / total) * 100),
                    "saisons": sorted(segs, key=lambda x: x["start"])})
    # Empfehlung: kleinste Anzahl, die ≥ 80 % erklärt oder höchstens 5 Punkte hinter der besten liegt
    # (sonst würde bei schwacher Saisonstruktur immer die feinste Aufteilung empfohlen)
    best = max((v["erklaert"] for v in out), default=0)
    rec = next((v["anzahl"] for v in out if v["erklaert"] >= 80 or v["erklaert"] >= best - 5), None)
    return {"vorschlaege": out, "empfohlen": rec, "jahre": prof["jahre"],
            "profil": [round(v * 100) for v in p], "auslastung": [round(v, 1) for v in prof["auslastung"]]}

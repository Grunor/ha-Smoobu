"""Preise übernehmen und rückgängig machen (ab v1.18.0, Wunsch Betreiber 17.11.2026).

Reine Python-Logik ohne HA (testbar): aus einer Vorgabe der Karte (Zeitraum, Preis oder
Prozent, Mindestaufenthalt, Filter) wird je Tag „alt → neu“ berechnet; daraus entstehen
die Smoobu-Operationen (POST /api/rates, gleiche Werte zu Datumsbereichen zusammengefasst).

Entscheidungen Betreiber (17.11.2026):
- Standard-Zeitraum einer Monatsempfehlung: ab heute bis Monatsende, alle Tage.
- Beim Senken Feiertagsnächte auslassen (sonst würde eine Dezember-Senkung genau die
  gefragtesten Nächte billiger machen) – Häkchen, vorbelegt.
- Tage mit eigenem Preis (≠ Basispreis des Zeitraums) nicht überschreiben – Häkchen, vorbelegt.
  „Basispreis“ = häufigster Preis im Zeitraum (bei einheitlichem Preis = dieser).
- Vor jeder Übernahme werden die bisherigen Werte gespeichert → „Rückgängig“.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Any

from .api import date_spec
from .empfehlung import holiday_nights

MAX_DAYS = 400


def days_of(spec: dict[str, Any], today: date) -> list[date]:
    """Tage einer Vorgabe: explizite Liste `tage` oder Bereich `von`–`bis` (inklusive), ab heute."""
    if spec.get("tage"):
        out = sorted({date.fromisoformat(str(d)[:10]) for d in spec["tage"]})
    else:
        start, end = date.fromisoformat(spec["von"]), date.fromisoformat(spec["bis"])
        if end < start:
            raise ValueError("Ende liegt vor dem Beginn")
        out = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    out = [d for d in out if d >= today]
    if wd := spec.get("wochentage"):
        out = [d for d in out if d.weekday() in set(wd)]
    if len(out) > MAX_DAYS:
        raise ValueError(f"Höchstens {MAX_DAYS} Tage auf einmal")
    return out


def base_price(rates: dict[str, dict[str, Any]], days: list[date]) -> float | None:
    """Häufigster Preis der Tage (Basispreis); bei Gleichstand der niedrigere."""
    prices = [float(rates[d.isoformat()]["price"]) for d in days
              if rates.get(d.isoformat(), {}).get("price") not in (None, "")]
    if not prices:
        return None
    count = Counter(prices)
    top = max(count.values())
    return min(p for p, c in count.items() if c == top)


def plan(spec: dict[str, Any], rates: dict[str, dict[str, Any]], today: date) -> dict[str, Any]:
    """Je Tag alt → neu. Ergebnis: {"tage": [...], "uebersprungen": [...], "basispreis": x}."""
    days = days_of(spec, today)
    base = base_price(rates, days)
    price, pct, min_stay = spec.get("preis"), spec.get("prozent"), spec.get("mindestaufenthalt")
    if price is None and pct is None and min_stay is None:
        raise ValueError("Preis, Prozent oder Mindestaufenthalt angeben")
    holidays = {d for y in {x.year for x in days} for d in holiday_nights(y)} if spec.get("ohne_feiertage") else set()
    out, skipped = [], []
    for d in days:
        iso = d.isoformat()
        cur = rates.get(iso) or {}
        old_p = cur.get("price")
        old_p = float(old_p) if old_p not in (None, "") else None
        old_m = cur.get("min_length_of_stay")
        if d in holidays:
            skipped.append({"datum": iso, "grund": "Feiertag"})
            continue
        if spec.get("nur_basispreis") and base is not None and old_p is not None and old_p != base and (price is not None or pct is not None):
            skipped.append({"datum": iso, "grund": "eigener Preis", "preis": old_p})
            continue
        new_p = None
        if price is not None:
            new_p = round(float(price), 2)
        elif pct is not None and old_p is not None:
            new_p = float(round(old_p * (1 + float(pct) / 100)))
        new_m = int(min_stay) if min_stay is not None else None
        if (new_p is None or new_p == old_p) and (new_m is None or new_m == old_m):
            skipped.append({"datum": iso, "grund": "unverändert"})
            continue
        out.append({"datum": iso, "preis_alt": old_p, "preis_neu": new_p, "min_alt": old_m, "min_neu": new_m})
    return {"tage": out, "uebersprungen": skipped, "basispreis": base}


def operations(changes: list[dict[str, Any]], *, restore: bool = False) -> list[dict[str, Any]]:
    """Smoobu-Operationen: gleiche Werte → Datumsbereiche „von:bis“ (beide inklusive).

    restore=True nutzt die alten Werte (Rückgängig). Ein Tag ohne alten Wert wird beim
    Rückgängigmachen ausgelassen (unbekannt → nicht raten).
    """
    groups: dict[tuple, list[date]] = {}
    for c in changes:
        p = c["preis_alt"] if restore else c["preis_neu"]
        m = c["min_alt"] if restore else c["min_neu"]
        if restore:
            p = p if c["preis_neu"] is not None else None   # nur zurücksetzen, was geändert wurde
            m = m if c["min_neu"] is not None else None
        if p is None and m is None:
            continue
        groups.setdefault((p, m), []).append(date.fromisoformat(c["datum"]))
    ops = []
    for (p, m), days in groups.items():
        days.sort()
        ranges, start, prev = [], days[0], days[0]
        for d in days[1:]:
            if d != prev + timedelta(days=1):
                ranges.append(date_spec(start.isoformat(), prev.isoformat()))
                start = d
            prev = d
        # v1.18.0: einzelner Tag als "JJJJ-MM-TT" (Smoobu lehnt "T:T" mit 422 ab – Last-Minute für eine Nacht)
        ranges.append(date_spec(start.isoformat(), prev.isoformat()))
        op: dict[str, Any] = {"dates": ranges}
        if p is not None:
            op["daily_price"] = p
        if m is not None:
            op["min_length_of_stay"] = int(m)
        ops.append(op)
    return ops


def verify(changes: list[dict[str, Any]], rates: dict[str, dict[str, Any]], *, restore: bool = False) -> list[dict[str, Any]]:
    """Tage, deren Wert in Smoobu nach dem Schreiben nicht dem Soll entspricht."""
    wrong = []
    for c in changes:
        cur = rates.get(c["datum"]) or {}
        want_p = (c["preis_alt"] if restore else c["preis_neu"]) if c["preis_neu"] is not None else None
        want_m = (c["min_alt"] if restore else c["min_neu"]) if c["min_neu"] is not None else None
        p = cur.get("price")
        if want_p is not None and (p in (None, "") or abs(float(p) - float(want_p)) > 0.01):
            wrong.append({"datum": c["datum"], "soll": want_p, "ist": p})
        elif want_m is not None and cur.get("min_length_of_stay") != want_m:
            wrong.append({"datum": c["datum"], "soll_min": want_m, "ist_min": cur.get("min_length_of_stay")})
    return wrong

"""Kanal-Auswertung: Direktvermarktung vs. Portale, Provision und Nettoumsatz.

Logik je Buchung:
- Brutto = Buchungspreis laut Smoobu (`price`). Bei Airbnb ist das der
  Betrag vor Abzug der Gastgebergebühr, bei Booking.com inkl. Provision.
- Provision = `commission-included` aus Smoobu, wenn vorhanden (echter Wert
  des Portals). Sonst der in den Optionen eingestellte %-Satz des Kanals.
- Zahlungsgebühr = Betrag aus „Payment charge is EUR x“ in der Buchungsnotiz
  (Booking.com-Zahlungsabwicklung). Andere Portale liefern das nicht.
- Netto = Brutto − Provision − Zahlungsgebühr.
Alle Beträge werden wie der Umsatz anteilig auf die Nächte verteilt.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from .models import is_blocked, parse_date

PAYMENT_CHARGE_RE = re.compile(r"payment charge is\s*(?:EUR|€)?\s*([\d]+(?:[.,]\d+)?)", re.IGNORECASE)

GROUP_DIRECT = "Direkt"
GROUP_PORTAL = "Portal"


def _lookup(mapping: dict[str, float], channel: str) -> float | None:
    """Kanal ohne Beachtung der Groß-/Kleinschreibung suchen."""
    low = channel.casefold()
    for key, value in mapping.items():
        if key.casefold() == low:
            return float(value)
    return None


def is_direct(channel: str | None, direct_channels: list[str]) -> bool:
    return bool(channel) and channel.casefold() in {d.casefold() for d in direct_channels}


def payment_charge(booking: dict[str, Any]) -> float:
    match = PAYMENT_CHARGE_RE.search(booking.get("notice") or "")
    return float(match.group(1).replace(",", ".")) if match else 0.0


def booking_costs(
    booking: dict[str, Any],
    commissions: dict[str, float],
    other_pct: float,
    direct_channels: list[str],
) -> dict[str, Any]:
    """Brutto, Provision, Zahlungsgebühr und Netto einer Buchung."""
    channel = (booking.get("channel") or {}).get("name") or "Unbekannt"
    direct = is_direct(channel, direct_channels)
    brutto = float(booking.get("price") or 0)
    smoobu = booking.get("commission-included")
    if smoobu not in (None, "") and float(smoobu) > 0:
        provision = float(smoobu)
        source = "smoobu"
        pct = round(provision / brutto * 100, 2) if brutto else None
    else:
        pct = _lookup(commissions, channel)
        if pct is None:
            # Direktkanal ohne eigenen Eintrag → 0 %, unbekanntes Portal → Standard
            pct = 0.0 if direct else float(other_pct)
        provision = brutto * pct / 100
        source = "konfiguration"
    fee = payment_charge(booking)
    return {
        "kanal": channel,
        "kanal_gruppe": GROUP_DIRECT if direct else GROUP_PORTAL,
        "brutto": round(brutto, 2),
        "provision": round(provision, 2),
        "provision_prozent": pct,
        "provision_quelle": source,
        "zahlungsgebuehr": round(fee, 2),
        "netto": round(brutto - provision - fee, 2),
        "kostenquote_prozent": round((provision + fee) / brutto * 100, 1) if brutto else None,
    }


def night_rows(
    bookings: list[dict[str, Any]],
    commissions: dict[str, float],
    other_pct: float,
    direct_channels: list[str],
) -> list[tuple[date, Any, str, bool, float, float, float]]:
    """Je Gastnacht eine Zeile: (Datum, Buchungs-ID, Kanal, direkt, Brutto, Provision, Gebühr).

    Basis für alle Summen (Monat, Jahr, bis heute, Vorjahr) ohne erneute API-Abfrage.
    """
    rows: list[tuple[date, Any, str, bool, float, float, float]] = []
    for b in bookings:
        if is_blocked(b):
            continue
        arrival = parse_date(b.get("arrival"))
        departure = parse_date(b.get("departure"))
        if arrival is None or departure is None or departure <= arrival:
            continue
        costs = booking_costs(b, commissions, other_pct, direct_channels)
        if costs["brutto"] <= 0:
            continue
        n = (departure - arrival).days
        day = arrival
        while day < departure:
            rows.append(
                (
                    day,
                    b.get("id"),
                    costs["kanal"],
                    costs["kanal_gruppe"] == GROUP_DIRECT,
                    costs["brutto"] / n,
                    costs["provision"] / n,
                    costs["zahlungsgebuehr"] / n,
                )
            )
            day += timedelta(days=1)
    return rows


def _empty() -> dict[str, Any]:
    return {"brutto": 0.0, "provision": 0.0, "zahlungsgebuehren": 0.0, "netto": 0.0, "naechte": 0, "_ids": set()}


def _finish(s: dict[str, Any]) -> dict[str, Any]:
    costs = s["provision"] + s["zahlungsgebuehren"]
    return {
        "brutto": round(s["brutto"], 2),
        "netto": round(s["netto"], 2),
        "provision": round(s["provision"], 2),
        "zahlungsgebuehren": round(s["zahlungsgebuehren"], 2),
        "kosten": round(costs, 2),
        "kostenquote_prozent": round(costs / s["brutto"] * 100, 1) if s["brutto"] else 0.0,
        "naechte": s["naechte"],
        "buchungen": len(s["_ids"]),
        "netto_pro_nacht": round(s["netto"] / s["naechte"], 2) if s["naechte"] else None,
    }


def summarize(rows: list, start: date, end: date) -> dict[str, Any]:
    """Summen für [start, end): gesamt, Direkt, Portale und je Kanal."""
    total, direct, portal = _empty(), _empty(), _empty()
    channels: dict[str, dict[str, Any]] = {}
    for day, bid, channel, is_dir, brutto, prov, fee in rows:
        if not start <= day < end:
            continue
        targets = (total, direct if is_dir else portal, channels.setdefault(channel, _empty()))
        for t in targets:
            t["brutto"] += brutto
            t["provision"] += prov
            t["zahlungsgebuehren"] += fee
            t["netto"] += brutto - prov - fee
            t["naechte"] += 1
            t["_ids"].add(bid)
    groups = {GROUP_DIRECT: [], GROUP_PORTAL: []}
    for day, bid, channel, is_dir, *_ in rows:
        name = GROUP_DIRECT if is_dir else GROUP_PORTAL
        if channel not in groups[name]:
            groups[name].append(channel)
    result_total = _finish(total)
    per_channel = {}
    for name, stats in sorted(channels.items(), key=lambda kv: -kv[1]["brutto"]):
        done = _finish(stats)
        done["gruppe"] = GROUP_DIRECT if name in groups[GROUP_DIRECT] else GROUP_PORTAL
        done["anteil_prozent"] = (
            round(stats["brutto"] / total["brutto"] * 100, 1) if total["brutto"] else 0.0
        )
        per_channel[name] = done
    return {
        "gesamt": result_total,
        "direkt": _finish(direct),
        "portale": _finish(portal),
        "kanaele": per_channel,
        "direktanteil_prozent": round(direct["brutto"] / total["brutto"] * 100, 1) if total["brutto"] else None,
        "direktanteil_naechte_prozent": round(direct["naechte"] / total["naechte"] * 100, 1) if total["naechte"] else None,
    }


def monthly(rows: list, year: int, key: str = "gesamt", field: str = "netto") -> dict[str, float]:
    """Monatswerte eines Jahres, z. B. Netto gesamt oder Brutto Direkt."""
    out: dict[str, float] = {}
    for m in range(1, 13):
        start = date(year, m, 1)
        end = date(year + (m == 12), m % 12 + 1, 1)
        out[f"{year:04d}-{m:02d}"] = summarize(rows, start, end)[key][field]
    return out

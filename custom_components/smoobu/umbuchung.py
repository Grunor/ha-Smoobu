"""Umbuchen: Zeitraum und/oder Unterkunft einer Direktbuchung ändern (ab v1.18.0, Wunsch Betreiber 20.11.2026).

Smoobu dokumentiert beim Ändern einer Buchung (PUT /api/reservations/{id}) nur Zeiten, Preis, Gastdaten,
Personen und Sprache – nicht arrivalDate/departureDate/apartmentId. Entscheidung Betreiber: trotzdem direkt
versuchen und danach prüfen. Ablauf im Websocket `smoobu/booking/move`:
  1. Prüfen (dieses Modul): Überschneidungen in der Ziel-Unterkunft, Mindestaufenthalt, Preisvorschlag
  2. Zeitraum/Unterkunft senden, Buchung neu lesen, vergleichen (verify) – übernimmt Smoobu die Änderung nicht,
     klare Meldung statt stillem Erfolg
  3. Nur wenn 2 geklappt hat: Preis (bestätigt) in einem zweiten Aufruf – so ändert sich nie nur der Preis

Nur Direktbuchungen: Portalbuchungen (Airbnb, Booking.com …) gehören dem Portal, eine Änderung dort würde
beim nächsten Abgleich überschrieben oder führt zu Doppelbuchungen.
Verworfen: Storno + Neuanlage (neue ID, Nachrichtenverlauf/Zahlungen hängen an der alten Buchung, ggf. Storno-Mail).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def _nights(a: str, b: str) -> list[str]:
    d, end = date.fromisoformat(a), date.fromisoformat(b)
    out = []
    while d < end:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def check(record: dict[str, Any], target_records: list[dict[str, Any]], arrival: str, departure: str, apartment_id: int,
          today: date) -> list[str]:
    """Gründe, warum nicht umgebucht werden kann (leer = möglich). Codes für die Karte."""
    errs = []
    if record.get("blockiert"):
        errs.append("sperrzeit")
    if record.get("storniert"):
        errs.append("storniert")
    if record.get("gruppe") != "Direkt":
        errs.append("portal")
    if record["abreise"] < today.isoformat():
        errs.append("vergangen")
    if departure <= arrival:
        errs.append("zeitraum")
    # Anreise in der Vergangenheit nur, wenn sie gleich bleibt (laufender Aufenthalt wird verlängert/verkürzt)
    if arrival < today.isoformat() and not (arrival == record["anreise"] and apartment_id == record.get("wohnung_id")):
        errs.append("anreise_vergangen")
    if departure <= today.isoformat() and record["abreise"] > today.isoformat():
        errs.append("abreise_vergangen")
    return errs


def conflicts(record: dict[str, Any], target_records: list[dict[str, Any]], arrival: str, departure: str) -> list[dict[str, Any]]:
    """Buchungen/Sperren der Ziel-Unterkunft, die sich mit [arrival, departure) überschneiden (ohne die eigene)."""
    out = []
    for r in target_records:
        if r["id"] == record["id"] or r.get("storniert"):
            continue
        if r["anreise"] < departure and r["abreise"] > arrival:
            out.append({"id": r["id"], "anreise": r["anreise"], "abreise": r["abreise"],
                        "blockiert": bool(r.get("blockiert")), "gast": None if r.get("blockiert") else r.get("gast")})
    return out


def price_suggestion(record: dict[str, Any], arrival: str, departure: str, apartment_id: int,
                     rates_old: dict[str, Any], rates_new: dict[str, Any]) -> dict[str, Any]:
    """Preisvorschlag: alter Preis + (Tagespreise neue Nächte − Tagespreise alte Nächte).

    So bleiben Reinigung, Rabatte und Zusatzleistungen im Preis erhalten. Fehlt ein Tagespreis (z. B. alte Nächte
    in der Vergangenheit), anteilig nach Nächten. Unveränderter Zeitraum + Unterkunft → kein Vorschlag.
    """
    old_price = record.get("brutto")
    new_n, old_n = _nights(arrival, departure), _nights(record["anreise"], record["abreise"])
    if old_price is None or (arrival == record["anreise"] and departure == record["abreise"]
                             and apartment_id == record.get("wohnung_id")):
        return {"preis_alt": old_price, "preis_vorschlag": None, "basis": None}
    p = lambda rates, d: (rates.get(d) or {}).get("price")  # noqa: E731
    new_vals, old_vals = [p(rates_new, d) for d in new_n], [p(rates_old, d) for d in old_n]
    if new_vals and old_vals and all(v is not None for v in new_vals + old_vals):
        sugg = old_price + sum(new_vals) - sum(old_vals)
        basis = "tagespreise"
    else:
        sugg = old_price / max(len(old_n), 1) * len(new_n)
        basis = "anteilig"
    return {"preis_alt": old_price, "preis_vorschlag": round(max(sugg, 0), 2), "basis": basis,
            "tagespreise_neu": round(sum(v for v in new_vals if v is not None), 2) if new_vals else None}


def min_stay_hint(rates_new: dict[str, Any], arrival: str, departure: str) -> int | None:
    """Mindestaufenthalt am Anreisetag, falls die neue Dauer darunter liegt (nur Hinweis, nicht blockierend)."""
    m = (rates_new.get(arrival) or {}).get("min_length_of_stay")
    n = len(_nights(arrival, departure))
    return int(m) if m and n < int(m) else None


def verify(raw: dict[str, Any], arrival: str, departure: str, apartment_id: int) -> dict[str, Any]:
    """Hat Smoobu die Änderung übernommen? Liefert den Stand laut Smoobu (für eine klare Fehlermeldung)."""
    got = {"anreise": str(raw.get("arrival") or raw.get("arrivalDate") or "")[:10],
           "abreise": str(raw.get("departure") or raw.get("departureDate") or "")[:10],
           "wohnung_id": (raw.get("apartment") or {}).get("id") if isinstance(raw.get("apartment"), dict) else raw.get("apartmentId")}
    ok = got["anreise"] == arrival and got["abreise"] == departure and (got["wohnung_id"] in (None, apartment_id))
    return {"ok": ok, "smoobu": got}

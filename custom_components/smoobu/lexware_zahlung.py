"""Lexware Office: Zahlungsstand, Hinweise und Smoobu-Haken (BETA, ab v1.20.0). Reine Logik.

Entscheidungen Betreiber (22./27.11.2026):
- Eine Rechnung je Buchung; die Anzahlung ordnet der Betreiber in Lexware als Teilzahlung zu.
- Soll-Anzahlung = Anzahlung aus Smoobu, sonst 50 % (Option) des Gesamtbetrags.
- Anzahlung 7 Tage (Option) nach Erstellung der Rechnung nicht (vollständig) da → Hinweis + Push
  „Storno möglich“. HA storniert nie selbst (nicht umkehrbar).
- Rest am Anreisetag offen → Hinweis + Push. Entwurf nach n Tagen nicht finalisiert → Hinweis.
- Portal-Buchungen: keine Zahlungsüberwachung (Portal kassiert), nur „Rechnung vorhanden?“.
- Bedeutung des Smoobu-Hakens „bezahlt“ je Kanalgruppe (Direkt/Portal):
    zahlung           Haken = Zahlung erhalten (von Hand)
    rechnung          Haken = Rechnung gestellt, Zahlung woanders (von Hand)
    lexware_zahlung   Haken und Anzahlung kommen aus Lexware (nur Lexware → Smoobu, von Hand gesperrt)
    lexware_rechnung  Haken, sobald die Rechnung in Lexware finalisiert ist
  Vorbelegung: Direkt = lexware_zahlung, Portal = lexware_rechnung. Ohne Lexware gelten die
  lexware_*-Werte wie zahlung bzw. rechnung.
"""

from __future__ import annotations

from datetime import date
from typing import Any

PAID_MEANINGS = ("zahlung", "rechnung", "lexware_zahlung", "lexware_rechnung")
DEFAULT_PAID_MEANING = {"direkt": "lexware_zahlung", "portal": "lexware_rechnung"}
# Status für Anzeige und Aufgaben
STATES = ("keine", "entwurf", "offen", "anzahlung_teilweise", "anzahlung", "bezahlt", "storniert")


def effective_meaning(meaning: str | None, group: str, lexware_on: bool) -> str:
    m = meaning if meaning in PAID_MEANINGS else DEFAULT_PAID_MEANING.get(group, "zahlung")
    if not lexware_on and m.startswith("lexware_"):
        return m.removeprefix("lexware_")
    return m


def soll_anzahlung(total: float, smoobu_prepayment: float, pct: float) -> float:
    if smoobu_prepayment and smoobu_prepayment > 0:
        return round(min(smoobu_prepayment, total) if total else smoobu_prepayment, 2)
    return round(total * pct / 100, 2)


def _d(v: Any) -> date | None:
    try:
        return date.fromisoformat(str(v)[:10]) if v else None
    except ValueError:
        return None


def evaluate(rec: dict[str, Any] | None, pay: dict[str, Any] | None, *, group: str, total: float,
             smoobu_prepayment: float, arrival: date | None, today: date,
             deposit_pct: float = 50.0, deposit_days: int = 7, draft_days: int = 2) -> dict[str, Any]:
    """Zahlungsstand einer Buchung aus gespeicherter Rechnung (`rec`) und Lexware-Zahlung (`pay`)."""
    soll = soll_anzahlung(total, smoobu_prepayment, deposit_pct)
    out: dict[str, Any] = {"status": "keine", "summe": total, "soll_anzahlung": soll, "gezahlt": 0.0, "offen": total,
                           "hinweise": [], "nummer": None, "faellig": None}
    if not rec:
        return out
    total = float(rec.get("summe") or total)
    vstatus = str(rec.get("status") or "draft")
    out.update({"summe": total, "nummer": rec.get("nummer"), "faellig": rec.get("faellig"), "offen": total,
                "soll_anzahlung": soll_anzahlung(total, smoobu_prepayment, deposit_pct)})
    soll = out["soll_anzahlung"]
    created = _d(rec.get("erstellt"))
    if vstatus == "draft":
        out["status"] = "entwurf"
        if created and (today - created).days >= draft_days:
            out["hinweise"].append("entwurf_offen")
        return out
    if vstatus == "voided" or (pay or {}).get("voucherStatus") == "voided":
        out.update({"status": "storniert", "offen": 0.0})
        return out
    if pay:
        open_amount = round(float(pay.get("openAmount") or 0), 2)
        if pay.get("voucherStatus") in ("paid", "paidoff"):
            open_amount = 0.0
        out["offen"], out["gezahlt"] = open_amount, round(max(total - open_amount, 0), 2)
    gez = out["gezahlt"]
    if out["offen"] <= 0.005:
        out["status"] = "bezahlt"
    elif gez >= soll - 0.005 and gez > 0:
        out["status"] = "anzahlung"
    elif gez > 0:
        out["status"] = "anzahlung_teilweise"
    else:
        out["status"] = "offen"
    if group == "portal":
        return out  # Portal kassiert – keine Zahlungshinweise
    if out["status"] in ("offen", "anzahlung_teilweise") and created and (today - created).days >= deposit_days:
        out["hinweise"].append("anzahlung_fehlt")
    if out["status"] != "bezahlt" and arrival and today >= arrival:
        out["hinweise"].append("rest_offen")
    return out


def smoobu_flags(meaning: str, ev: dict[str, Any]) -> dict[str, bool]:
    """Soll-Zustand der Smoobu-Haken (leer = von Hand, HA schreibt nichts)."""
    if meaning == "lexware_zahlung":
        if ev["status"] in ("keine", "entwurf", "storniert"):
            return {}
        return {"price_paid": ev["status"] == "bezahlt",
                "prepayment_paid": ev["status"] in ("anzahlung", "bezahlt")}
    if meaning == "lexware_rechnung":
        if ev["status"] == "keine":
            return {}
        return {"price_paid": ev["status"] not in ("entwurf", "storniert")}
    return {}

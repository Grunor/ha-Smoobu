"""Lexware Office: Regelwerk für Rechnungsentwürfe (BETA, ab v1.20.0, Wunsch Betreiber 22./27.11.2026).

Reine Logik ohne Home Assistant – getestet mit zwei echten Rechnungen des Betreibers als Sollwerten
(Direktbuchung 236,00 € brutto, Booking.com-Buchung 330,41 € = 308,79 € netto + 7 %).

Ablauf
------
1. `facts(booking)` liest aus der Smoobu-Buchung Nächte, Erwachsene, Kinder, Hunde, Kanal und Preis.
2. `build(...)` wertet die Regelzeilen der Kanalgruppe (Direkt / Portal) aus. Jede Regelzeile verweist auf
   einen **Lexware-Artikel** (Bezeichnung, Einheit, Steuersatz kommen aus dem Artikel) und legt fest,
   wie die Menge entsteht (je Nacht, je Zusatzperson und Nacht, je Hund …), wann die Zeile gilt
   (z. B. nur bis 14 Nächte) und woher der Preis kommt:
   - „artikel“: Preis aus dem Lexware-Artikel (z. B. Endreinigung 10 €)
   - „rest“: Rest aus dem Smoobu-Buchungspreis (genau eine Zeile je Gruppe, z. B. die Übernachtung).
     So stimmt die Summe immer mit Smoobu überein, auch bei Saisonpreisen – Entscheidung Betreiber.
3. Gesamtrabatt (Entscheidung Betreiber: Rabatte als Gesamtrabatt): Die Rest-Zeile wird so berechnet, dass
   die Summe NACH Rabatt dem Smoobu-Preis entspricht.
4. Firmen bekommen eine Nettorechnung, Privatgäste eine Bruttorechnung (einstellbar). Bei netto wird der
   Einzelpreis der Rest-Zeile auf den Cent so gewählt, dass der Bruttobetrag möglichst genau stimmt.
5. Rechnungsdatum = heute, fällig zum Anreisetag (`paymentTermDuration` = Tage bis Anreise). Lexware zeigt
   die Rechnung damit bis zur Anreise als „offen“, nicht als „überfällig“ – laut API-Doku ist „overdue“ =
   offen UND Fälligkeit vorbei. Alternative „anreise“ (altes Verfahren: Rechnungsdatum = Anreisetag) bleibt
   wählbar, bekommt aber einen Hinweis.

Platzhalter in Artikeltexten und Zahlungstexten (ersetzt HA selbst – Lexware kennt per API nur seine eigenen):
`[Portal]` Kanalname · `[n]` Personen · `[Nächte]` Nächte · `[Fällig]` Fälligkeitsdatum · `[Betrag]` Gesamtbetrag ·
`[Anzahlung]` Soll-Anzahlung.

Ergebnis ist eine Vorschau (Positionen, Summen, Warnungen) und – ohne Fehler – die Nutzlast für
`POST /v1/invoices` (immer als Entwurf, finalisiert wird in Lexware).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from .models import is_yes, parse_date, pet_match

# Kanalgruppen
GROUPS = ("direkt", "portal")
# Mengenarten einer Regelzeile
QUANTITIES = ("pauschal", "nacht", "person", "person_nacht", "zusatzperson", "zusatzperson_nacht",
              "kind", "kind_nacht", "hund", "hund_nacht", "fest")
# Bedingungen (optional) – „wert“ ist die Schwelle
CONDITIONS = ("", "naechte_max", "naechte_min", "hund", "kein_hund", "personen_min", "kinder")
PRICES = ("artikel", "rest")
TAX_TYPES = ("gross", "net")
INVOICE_DATES = ("erstellung", "anreise")

DEFAULT_PAYMENT_TEXT = {
    "direkt": "Zahlbar bis [Fällig].",
    "portal": "Die vollständige Zahlung haben wir bereits dankend erhalten.",
}

# Vorlage ohne Artikel (Artikel-IDs gibt es erst nach dem Verbinden mit Lexware). Entspricht der
# Rechnung des Betreibers: Übernachtung (Rest) · Aufpreis ab 2. Person je Nacht · Kinder je Nacht ·
# Sonderreinigung je Hund (max. 2) · Endreinigung bis/ab 14 Nächte · Portal = eine Pauschale (Rest).
TEMPLATE: dict[str, list[dict[str, Any]]] = {
    "direkt": [
        {"artikel": None, "hinweis": "Übernachtung", "menge": "nacht", "preis": "rest"},
        {"artikel": None, "hinweis": "Aufpreis 2. Person", "menge": "zusatzperson_nacht", "ab": 2, "preis": "artikel"},
        {"artikel": None, "hinweis": "Aufpreis Kind", "menge": "kind_nacht", "preis": "artikel"},
        {"artikel": None, "hinweis": "Sonderreinigung Hund", "menge": "hund", "max": 2, "preis": "artikel"},
        {"artikel": None, "hinweis": "Endreinigung Kurzzeit", "menge": "pauschal", "bedingung": "naechte_max", "wert": 14, "preis": "artikel"},
        {"artikel": None, "hinweis": "Endreinigung Langzeit", "menge": "pauschal", "bedingung": "naechte_min", "wert": 15, "preis": "artikel"},
    ],
    "portal": [
        {"artikel": None, "hinweis": "Übernachtung [n] Person(en) (Portal)", "menge": "pauschal", "preis": "rest"},
    ],
}

_PH = re.compile(r"\[(Portal|n|N[äa]e?chte|F[äa]e?llig|Betrag|Anzahlung)\]", re.IGNORECASE)


def _r2(x: float) -> float:
    return round(x + (1e-9 if x >= 0 else -1e-9), 2)


def _num(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _int(v: Any, default: int = 0) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def de_date(d: date) -> str:
    return d.strftime("%d.%m.%Y")


def euro(x: float) -> str:
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
# Buchungsdaten
# ---------------------------------------------------------------------------
def dogs_from_booking(booking: dict[str, Any]) -> tuple[int | None, str]:
    """Hundeanzahl aus Smoobu. Ergebnis (Anzahl, Quelle).

    - Zusatzleistung mit Hund/Haustier im Namen (Betrag ≠ 0): Menge der Leistung (`quantity`), sonst 1
    - Hund nur in Notiz/Nachricht erwähnt: Anzahl unbekannt (None) → Pflichteingabe in der Vorschau
    - sonst 0
    Entscheidung Betreiber 22.11.2026: Hundeanzahl steht oft, aber nicht immer in Smoobu (v. a. Portale).
    """
    count = 0
    for e in booking.get("priceElements") or []:
        name = str(e.get("name") or "").replace("_", " ")
        if _num(e.get("amount")) and pet_match(name):
            q = _int(e.get("quantity"), 0)
            count += q if q > 0 else 1
    if count:
        return count, "smoobu"
    from .models import pet_hint  # noqa: PLC0415

    if pet_hint(booking):
        return None, "hinweis"
    return 0, ""


def facts(booking: dict[str, Any], portal_channels: list[str]) -> dict[str, Any]:
    """Kennzahlen einer Smoobu-Buchung für das Regelwerk."""
    arrival = parse_date(booking.get("arrival"))
    departure = parse_date(booking.get("departure"))
    nights = (departure - arrival).days if arrival and departure else 0
    channel = str((booking.get("channel") or {}).get("name") or "")
    dogs, dog_src = dogs_from_booking(booking)
    adults, children = _int(booking.get("adults")), _int(booking.get("children"))
    portal = channel.lower() in {c.lower() for c in portal_channels}
    return {
        "anreise": arrival, "abreise": departure, "naechte": max(nights, 0),
        "erwachsene": adults, "kinder": children, "personen": adults + children,
        "hunde": dogs, "hunde_quelle": dog_src,
        "kanal": channel, "gruppe": "portal" if portal else "direkt",
        "preis": _r2(_num(booking.get("price"))),
        "anzahlung_smoobu": _r2(_num(booking.get("prepayment"))),
        "anzahlung_bezahlt": is_yes(booking.get("prepayment-paid")),
    }


# ---------------------------------------------------------------------------
# Artikel
# ---------------------------------------------------------------------------
def article_info(article: dict[str, Any]) -> dict[str, Any]:
    """Lexware-Artikel → Bezeichnung, Einheit, Steuersatz, Brutto-/Nettopreis, Positionstyp."""
    price = article.get("price") or {}
    rate = _num(price.get("taxRate"), 0.0)
    lead = str(price.get("leadingPrice") or "NET").upper()
    if lead == "GROSS" and price.get("grossPrice") is not None:
        gross = _num(price.get("grossPrice"))
        net = _num(price.get("netPrice"), gross / (1 + rate / 100))
    else:
        net = _num(price.get("netPrice"))
        gross = _num(price.get("grossPrice"), net * (1 + rate / 100))
    return {
        "id": article.get("id"),
        "name": str(article.get("title") or ""),
        "beschreibung": str(article.get("description") or ""),
        "einheit": str(article.get("unitName") or "Stück"),
        "steuersatz": rate,
        "brutto": _r2(gross), "netto": round(net, 4),
        # Lexware-Positionstyp: Dienstleistung → service, Produkt → material
        "typ": "material" if str(article.get("type") or "").upper() == "PRODUCT" else "service",
    }


def fill(text: str, values: dict[str, str]) -> str:
    """Platzhalter ersetzen (Groß/Klein und ä/ae egal). Unbekannte bleiben stehen."""
    def rep(m: re.Match) -> str:
        key = m.group(1).lower().replace("ä", "ae")
        key = {"naechte": "naechte", "nachte": "naechte", "faellig": "faellig", "fallig": "faellig"}.get(key, key)
        return values.get(key, m.group(0))
    return _PH.sub(rep, text or "")


# ---------------------------------------------------------------------------
# Regelzeilen
# ---------------------------------------------------------------------------
def rule_applies(rule: dict[str, Any], f: dict[str, Any], dogs: int) -> bool:
    cond, val = rule.get("bedingung") or "", _num(rule.get("wert"))
    if cond == "naechte_max":
        return f["naechte"] <= val
    if cond == "naechte_min":
        return f["naechte"] >= val
    if cond == "hund":
        return dogs > 0
    if cond == "kein_hund":
        return dogs == 0
    if cond == "personen_min":
        return f["personen"] >= val
    if cond == "kinder":
        return f["kinder"] > 0
    return True


def quantity(rule: dict[str, Any], f: dict[str, Any], dogs: int) -> float:
    m, n = rule.get("menge") or "pauschal", f["naechte"]
    extra = max(f["erwachsene"] - max(_int(rule.get("ab"), 2), 1) + 1, 0)
    dmax = _int(rule.get("max"), 0)
    d = min(dogs, dmax) if dmax > 0 else dogs
    return {
        "pauschal": 1, "nacht": n, "person": f["personen"], "person_nacht": f["personen"] * n,
        "zusatzperson": extra, "zusatzperson_nacht": extra * n,
        "kind": f["kinder"], "kind_nacht": f["kinder"] * n,
        "hund": d, "hund_nacht": d * n, "fest": _num(rule.get("anzahl"), 1),
    }.get(m, 0)


def validate_rules(rules: Any, articles: dict[str, dict[str, Any]] | None = None) -> list[str]:
    """Fehlercodes einer Regelliste (eine Gruppe). Leere Liste = in Ordnung."""
    errs: list[str] = []
    if not isinstance(rules, list):
        return ["invalid_rules"]
    if sum(1 for r in rules if (r or {}).get("preis") == "rest") > 1:
        errs.append("multiple_rest")
    for r in rules:
        if not isinstance(r, dict) or r.get("menge") not in QUANTITIES or (r.get("bedingung") or "") not in CONDITIONS \
                or (r.get("preis") or "artikel") not in PRICES:
            errs.append("invalid_rule")
        elif articles is not None and r.get("artikel") and r["artikel"] not in articles:
            errs.append("unknown_article")
    return sorted(set(errs))


# ---------------------------------------------------------------------------
# Summen (Näherung der Lexware-Rechnung)
# ---------------------------------------------------------------------------
def totals(lines: list[dict[str, Any]], tax_type: str, discount_pct: float = 0.0) -> dict[str, Any]:
    """Netto, Steuer je Satz und Brutto wie auf der Rechnung (Cent-gerundet je Position und je Steuersatz)."""
    f = 1 - discount_pct / 100
    by_rate: dict[float, float] = {}
    if tax_type == "gross":
        for ln in lines:
            by_rate[ln["steuersatz"]] = by_rate.get(ln["steuersatz"], 0.0) + _r2(ln["einzel_brutto"] * ln["menge"])
        gross_by = {r: _r2(v * f) for r, v in by_rate.items()}
        tax_by = {r: _r2(g - g / (1 + r / 100)) for r, g in gross_by.items()}
        gross = _r2(sum(gross_by.values()))
        tax = _r2(sum(tax_by.values()))
        return {"brutto": gross, "netto": _r2(gross - tax), "steuer": tax, "steuer_je_satz": tax_by}
    for ln in lines:
        by_rate[ln["steuersatz"]] = by_rate.get(ln["steuersatz"], 0.0) + _r2(ln["einzel_netto"] * ln["menge"])
    net_by = {r: _r2(v * f) for r, v in by_rate.items()}
    tax_by = {r: _r2(n * r / 100) for r, n in net_by.items()}
    net, tax = _r2(sum(net_by.values())), _r2(sum(tax_by.values()))
    return {"brutto": _r2(net + tax), "netto": net, "steuer": tax, "steuer_je_satz": tax_by}


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------
def build(
    booking: dict[str, Any],
    rules: dict[str, list[dict[str, Any]]],
    articles: dict[str, dict[str, Any]],
    *,
    today: date,
    portal_channels: list[str],
    company: bool = False,
    tax_company: str = "net",
    tax_private: str = "gross",
    invoice_date: str = "erstellung",
    payment_text: dict[str, str] | None = None,
    deposit: float = 0.0,
    overrides: dict[str, Any] | None = None,
    tz_suffix: str = "+01:00",
) -> dict[str, Any]:
    """Vorschau + Lexware-Nutzlast. `overrides` aus der Vorschau: hunde, rabatt (%), mengen/preise je Zeile.

    Rückgabe: {gruppe, positionen, summen, warnungen, fehler, faellig, rechnungsdatum, payload (ohne address)}.
    """
    ov = overrides or {}
    f = facts(booking, portal_channels)
    group = ov.get("gruppe") if ov.get("gruppe") in GROUPS else f["gruppe"]
    warnings: list[str] = []
    errors: list[str] = []

    dogs = f["hunde"]
    if ov.get("hunde") is not None:
        dogs = max(_int(ov.get("hunde")), 0)
    elif dogs is None:
        errors.append("hunde_unbekannt")  # Hund erkannt, Anzahl unbekannt → Pflichteingabe
        dogs = 0
    discount = min(max(_num(ov.get("rabatt")), 0.0), 99.0)
    tax_type = tax_company if company else tax_private
    tax_type = tax_type if tax_type in TAX_TYPES else "gross"

    group_rules = list(rules.get(group) or [])
    if not group_rules:
        errors.append("keine_regeln")
    elif not any(r.get("artikel") for r in group_rules):
        errors.append("keine_artikel")
    rest_rules = [i for i, r in enumerate(group_rules) if r.get("preis") == "rest"]
    if len(rest_rules) > 1:
        errors.append("mehrere_rest")

    values = {"portal": f["kanal"] or "", "n": str(f["personen"]), "naechte": str(f["naechte"])}
    lines: list[dict[str, Any]] = []
    rest_idx: int | None = None
    line_ov = {int(k): v for k, v in (ov.get("zeilen") or {}).items() if str(k).lstrip("-").isdigit()}
    for i, rule in enumerate(group_rules):
        art = articles.get(rule.get("artikel") or "")
        if not art:
            if rule.get("artikel"):
                errors.append("artikel_fehlt")
            continue
        if not rule_applies(rule, f, dogs):
            continue
        info = article_info(art)
        qty = quantity(rule, f, dogs)
        if i in line_ov and line_ov[i].get("menge") is not None:
            qty = max(_num(line_ov[i]["menge"]), 0)
        if qty <= 0:
            continue
        price_from = rule.get("preis") or "artikel"
        unit_gross = info["brutto"]
        if i in line_ov and line_ov[i].get("einzel") is not None and price_from != "rest":
            unit_gross = _r2(_num(line_ov[i]["einzel"]))
        lines.append({
            "regel": i, "artikel_id": info["id"], "typ": info["typ"], "name": fill(info["name"], values),
            "beschreibung": fill(info["beschreibung"], values), "menge": qty, "einheit": info["einheit"],
            "steuersatz": info["steuersatz"], "einzel_brutto": unit_gross,
            "einzel_netto": round(unit_gross / (1 + info["steuersatz"] / 100), 2),
            "artikelpreis": info["brutto"], "preisquelle": price_from,
        })
        if price_from == "rest":
            rest_idx = len(lines) - 1

    target = f["preis"]
    pre_discount = target / (1 - discount / 100) if discount else target
    if rest_idx is not None:
        rest = lines[rest_idx]
        others = sum(_r2(ln["einzel_brutto"] * ln["menge"]) for j, ln in enumerate(lines) if j != rest_idx)
        unit = (pre_discount - others) / rest["menge"]
        rest["einzel_brutto"] = _r2(unit)
        rest["einzel_netto"] = round(unit / (1 + rest["steuersatz"] / 100), 2)
        if unit < 0:
            errors.append("rest_negativ")
        elif rest["artikelpreis"] and abs(unit - rest["artikelpreis"]) / rest["artikelpreis"] > 0.25:
            warnings.append("rest_abweichung")  # z. B. Rabatt in Smoobu, Saisonpreis
        if tax_type == "net":
            # Cent-genau: Netto-Einzelpreis so wählen, dass der Bruttobetrag möglichst genau stimmt
            base = rest["einzel_netto"]
            best = min((round(base + d / 100, 2) for d in range(-3, 4)),
                       key=lambda x: (abs(totals([*lines[:rest_idx], {**rest, "einzel_netto": x}, *lines[rest_idx + 1:]],
                                                 "net", discount)["brutto"] - target), abs(x - base)))
            rest["einzel_netto"] = best
    sums = totals(lines, tax_type, discount) if lines else {"brutto": 0.0, "netto": 0.0, "steuer": 0.0, "steuer_je_satz": {}}
    diff = _r2(sums["brutto"] - target)
    if lines and abs(diff) >= 0.01:
        warnings.append("summe_abweichung")
    if not lines and not errors:
        errors.append("keine_positionen")

    # Rechnungsdatum und Fälligkeit
    arrival = f["anreise"] or today
    if invoice_date == "anreise":
        vdate, due_days = arrival, 0
        if arrival > today:
            warnings.append("rechnungsdatum_zukunft")  # vordatiert – Hinweis § 14 Abs. 4 Nr. 3 UStG
    else:
        vdate = today
        due_days = 0 if group == "portal" else max((arrival - today).days, 0)
    due = date.fromordinal(vdate.toordinal() + due_days)
    values.update({"faellig": de_date(due), "betrag": euro(sums["brutto"]), "anzahlung": euro(deposit)})
    label = fill((payment_text or {}).get(group) or DEFAULT_PAYMENT_TEXT[group], values)

    payload = {
        "voucherDate": f"{vdate.isoformat()}T00:00:00.000{tz_suffix}",
        "lineItems": [{
            "id": ln["artikel_id"], "type": ln["typ"], "name": ln["name"],
            **({"description": ln["beschreibung"]} if ln["beschreibung"] else {}),
            "quantity": ln["menge"], "unitName": ln["einheit"],
            "unitPrice": {"currency": "EUR", "taxRatePercentage": ln["steuersatz"],
                          **({"grossAmount": ln["einzel_brutto"]} if tax_type == "gross" else {"netAmount": ln["einzel_netto"]})},
        } for ln in lines],
        "totalPrice": {"currency": "EUR", **({"totalDiscountPercentage": discount} if discount else {})},
        "taxConditions": {"taxType": tax_type},
        "paymentConditions": {"paymentTermLabel": label, "paymentTermDuration": due_days},
        "shippingConditions": {"shippingType": "serviceperiod",
                               "shippingDate": f"{(f['anreise'] or vdate).isoformat()}T00:00:00.000{tz_suffix}",
                               "shippingEndDate": f"{(f['abreise'] or f['anreise'] or vdate).isoformat()}T00:00:00.000{tz_suffix}"},
    }
    return {
        "gruppe": group, "kanal": f["kanal"], "steuerart": tax_type, "firma": company,
        "fakten": {**{k: v for k, v in f.items() if k not in ("anreise", "abreise")},
                   "anreise": f["anreise"].isoformat() if f["anreise"] else None,
                   "abreise": f["abreise"].isoformat() if f["abreise"] else None, "hunde": dogs if f["hunde"] is not None or ov.get("hunde") is not None else None},
        "positionen": lines, "rabatt": discount, "summen": sums, "soll": target, "differenz": diff,
        "rechnungsdatum": vdate.isoformat(), "faellig": due.isoformat(), "zahlungstext": label,
        "warnungen": sorted(set(warnings)), "fehler": sorted(set(errors)), "payload": payload,
    }

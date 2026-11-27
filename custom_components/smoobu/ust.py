"""Umsatzsteuer (optional, ab v1.20.0, Wunsch Betreiber 27.11.2026). Reine Logik ohne Home Assistant.

Entscheidungen Betreiber (27.11.2026):
- Kein eigener Artikel-/Preiskatalog: Preise bleiben in Smoobu (bzw. Lexware). Hier gibt es nur die
  Zuordnung Smoobu-Preisbestandteil → Steuerart (ermäßigt / regulär / steuerfrei); nicht zugeordnet = ermäßigt
  (Beherbergung). Portal-Buchungen komplett mit einer Steuerart (Standard ermäßigt, wie die Portal-Rechnung).
- Grundschalter: aus (Standard, bisheriges Verhalten) / Kleinunternehmer / Regelbesteuerung, dazu
  **„USt-pflichtig seit“** (beim Betreiber 01.01.2026). Nächte VOR diesem Datum haben keine USt.
- Sätze mit Gültigkeit (deutsche Werte voreingetragen, u. a. 07–12/2020 5 %/16 %); maßgeblich ist das Datum
  der Übernachtung (Leistungsdatum).
- Mit Lexware optional: gibt es zur Buchung eine (nicht stornierte) Rechnung, gilt deren Nettobetrag
  → Rechnung und Statistik rechnen gleich.
- Wirkung überall (Finanzen, Statistik, Umsatz-Sensoren); Ansicht „brutto“ oder „ohne USt“ (Standard bei
  Regelbesteuerung: ohne USt), in Finanzen/Statistik umschaltbar.
- Provisionen der Portale: Reverse Charge (§ 13b UStG) → Provision wie berechnet (netto); die USt darauf ist
  zugleich Vorsteuer, also kostenneutral.
- Kosten ohne USt (Vorsteuerabzug): Kostenwerte gelten als brutto, je Kostenart wird mit ihrer Steuerart
  herausgerechnet (Strom/Heizung/Warmwasser/Wäsche regulär, Wasser ermäßigt, Reinigung/Lohn steuerfrei).

Die Smoobu-Daten bleiben unverändert; die USt wird bei der Auswertung berechnet (Zuordnung änderbar, wirkt sofort).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

CONF_UST_MODE = "ust_mode"            # aus | kleinunternehmer | regel
CONF_UST_SINCE = "ust_since"          # YYYY-MM-DD (leer = immer)
CONF_UST_VIEW = "ust_view"            # brutto | ohne (Standardansicht)
CONF_UST_RATES = "ust_rates"          # [{"ab": "YYYY-MM-DD", "ermaessigt": 7, "regel": 19}]
CONF_UST_MAP = "ust_map"              # {Preisbestandteil: Steuerart}
CONF_UST_PORTAL = "ust_portal"        # Steuerart der Portal-Buchungen
CONF_UST_DEFAULT = "ust_default"      # Steuerart nicht zugeordneter Bestandteile
CONF_UST_COSTS = "ust_costs"          # {Kostenart: Steuerart}
CONF_UST_LEXWARE = "ust_lexware"      # Nettobetrag aus der Lexware-Rechnung übernehmen

MODES = ("aus", "kleinunternehmer", "regel")
VIEWS = ("brutto", "ohne")
KINDS = ("ermaessigt", "regel", "frei")
COST_KINDS = ("strom", "heizung", "warmwasser", "wasser", "reinigung", "waesche")
DEFAULT_RATES = [
    {"ab": "2007-01-01", "ermaessigt": 7.0, "regel": 19.0},
    {"ab": "2020-07-01", "ermaessigt": 5.0, "regel": 16.0},   # befristete Senkung 2. Halbjahr 2020
    {"ab": "2021-01-01", "ermaessigt": 7.0, "regel": 19.0},
]
DEFAULT_COSTS = {"strom": "regel", "heizung": "regel", "warmwasser": "regel", "wasser": "ermaessigt",
                 "reinigung": "frei", "waesche": "regel"}
# Smoobu-Preisbestandteile ohne Namen werden über ihren Typ zugeordnet
TYPE_KEYS = {"basePrice": "Grundpreis", "cleaningFee": "Reinigungsgebühr", "longStayDiscount": "Rabatt", "coupon": "Rabatt",
             "addon": None, "cityTax": "Kurtaxe", "deposit": "Kaution"}


def _d(v: Any) -> date | None:
    try:
        return date.fromisoformat(str(v)[:10]) if v else None
    except ValueError:
        return None


def opts_of(o: dict[str, Any]) -> dict[str, Any]:
    """Optionen mit Standardwerten."""
    mode = o.get(CONF_UST_MODE) if o.get(CONF_UST_MODE) in MODES else "aus"
    return {
        "modus": mode,
        "seit": _d(o.get(CONF_UST_SINCE)),
        "ansicht": o.get(CONF_UST_VIEW) if o.get(CONF_UST_VIEW) in VIEWS else ("ohne" if mode == "regel" else "brutto"),
        "saetze": sorted(o.get(CONF_UST_RATES) or DEFAULT_RATES, key=lambda x: str(x.get("ab"))),
        "zuordnung": dict(o.get(CONF_UST_MAP) or {}),
        "portal": o.get(CONF_UST_PORTAL) if o.get(CONF_UST_PORTAL) in KINDS else "ermaessigt",
        "standard": o.get(CONF_UST_DEFAULT) if o.get(CONF_UST_DEFAULT) in KINDS else "ermaessigt",
        "kosten": {**DEFAULT_COSTS, **{k: v for k, v in (o.get(CONF_UST_COSTS) or {}).items() if v in KINDS}},
        "lexware": bool(o.get(CONF_UST_LEXWARE, True)),
    }


def active(o: dict[str, Any]) -> bool:
    return opts_of(o)["modus"] == "regel"


def rate(kind: str, day: date, cfg: dict[str, Any]) -> float:
    """Steuersatz in % für Steuerart und Tag (0 vor „USt-pflichtig seit“, ohne Regelbesteuerung, steuerfrei)."""
    if cfg["modus"] != "regel" or kind == "frei" or (cfg["seit"] and day < cfg["seit"]):
        return 0.0
    cur = None
    for r in cfg["saetze"]:
        ab = _d(r.get("ab"))
        if ab and ab <= day:
            cur = r
    if cur is None:
        return 0.0
    return float(cur.get(kind) or 0.0)


def element_key(e: dict[str, Any]) -> str:
    """Schlüssel eines Smoobu-Preisbestandteils für die Zuordnung (Name, sonst Typ)."""
    name = str(e.get("name") or "").strip()
    if name:
        return name
    return TYPE_KEYS.get(str(e.get("typ") or e.get("type") or ""), None) or str(e.get("typ") or e.get("type") or "Sonstiges")


def elements_seen(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Alle Preisbestandteile der Buchungen (für die Zuordnung in den Einstellungen), häufigste zuerst."""
    seen: dict[str, int] = {}
    for r in records:
        if r.get("blockiert") or r.get("storniert"):
            continue
        for e in r.get("positionen") or []:
            if not float(e.get("betrag") or 0):
                continue
            k = element_key(e)
            seen[k] = seen.get(k, 0) + 1
    return [{"name": k, "anzahl": n} for k, n in sorted(seen.items(), key=lambda x: (-x[1], x[0].casefold()))]


def _shares(r: dict[str, Any], cfg: dict[str, Any]) -> dict[str, float]:
    """Bruttobetrag der Buchung je Steuerart. Bestandteile werden auf den Buchungspreis skaliert (Smoobu-Summe
    weicht teils ab, z. B. Kurtaxe); ohne Bestandteile bzw. bei Portalen alles in einer Steuerart."""
    total = float(r.get("brutto") or 0)
    if r.get("gruppe") == "Portal":
        return {cfg["portal"]: total}
    parts: dict[str, float] = {}
    for e in r.get("positionen") or []:
        amount = float(e.get("betrag") or 0)
        if not amount:
            continue
        kind = cfg["zuordnung"].get(element_key(e)) or cfg["standard"]
        parts[kind] = parts.get(kind, 0.0) + amount
    s = sum(parts.values())
    if not parts or s <= 0:
        return {cfg["standard"]: total}
    return {k: total * v / s for k, v in parts.items()}


def split(r: dict[str, Any], cfg: dict[str, Any], lex_net: float | None = None) -> dict[str, Any]:
    """USt einer Buchung. Ergebnis: ust, je_satz {Satz: Betrag}, ohne_ust und je Nacht der Betrag ohne USt."""
    total = float(r.get("brutto") or 0)
    nights = int(r.get("naechte") or 0)
    arrival = _d(r.get("anreise"))
    if not total or not nights or not arrival or r.get("blockiert") or r.get("storniert") or cfg["modus"] != "regel":
        per = [round(total / nights, 4)] * nights if nights else []
        return {"ust": 0.0, "je_satz": {}, "ohne_ust": round(total, 2), "naechte_ohne_ust": per}
    days = [arrival + timedelta(days=i) for i in range(nights)]
    shares = _shares(r, cfg)
    per_night: list[float] = []
    by_rate: dict[float, float] = {}
    for day in days:
        net = 0.0
        for kind, amount in shares.items():
            gross = amount / nights
            p = rate(kind, day, cfg)
            vat = gross * p / (100 + p)
            net += gross - vat
            if vat:
                by_rate[p] = by_rate.get(p, 0.0) + vat
        per_night.append(net)
    # Lexware: Nettobetrag der Rechnung übernehmen, wenn er nur um Rundung/Positionsaufteilung (≤ 2 %) von der
    # Berechnung abweicht – sonst passt die Rechnung nicht (mehr) zur Buchung und die Berechnung gilt
    computed = sum(per_night)
    taxed = [i for i, d in enumerate(days) if any(rate(k, d, cfg) for k in shares)]
    if lex_net is not None and taxed and total and abs(computed - lex_net) <= 0.02 * total:
        diff = (computed - lex_net) / len(taxed)
        for i in taxed:
            per_night[i] -= diff
        vat_calc = sum(by_rate.values())
        target = total - lex_net
        by_rate = {k: v * target / vat_calc for k, v in by_rate.items()} if vat_calc else by_rate
    ust = round(total - sum(per_night), 2)
    return {"ust": ust, "je_satz": {k: round(v, 2) for k, v in by_rate.items() if round(v, 2)},
            "ohne_ust": round(total - ust, 2), "naechte_ohne_ust": [round(x, 4) for x in per_night]}


def cost_net(kind: str, amount: float, day: date, cfg: dict[str, Any]) -> float:
    """Kostenbetrag ohne Vorsteuer (Kostenwerte gelten als brutto)."""
    p = rate(cfg["kosten"].get(kind, "regel"), day, cfg)
    return amount / (1 + p / 100) if p else amount


def enrich(records: list[dict[str, Any]], cfg: dict[str, Any], lex_nets: dict[Any, float] | None = None) -> None:
    """Je Buchung USt-Felder ergänzen (in place): ust, ust_je_satz, brutto_ohne_ust, netto_ohne_ust,
    *_pro_nacht_ohne_ust, db_ohne_ust. Variable Kosten ohne USt setzt deckungsbeitrag.apply."""
    for r in records:
        s = split(r, cfg, (lex_nets or {}).get(r.get("id")) if cfg["lexware"] else None)
        r["ust"], r["ust_je_satz"] = s["ust"], s["je_satz"]
        r["brutto_ohne_ust"] = s["ohne_ust"]
        r["naechte_ohne_ust"] = s["naechte_ohne_ust"]
        # Provision/Gebühr bleiben (Reverse Charge, kostenneutral) → „nach Provision“ ohne USt = netto − USt
        r["netto_ohne_ust"] = round(float(r.get("netto") or 0) - s["ust"], 2)
        n = r.get("naechte") or 0
        r["brutto_pro_nacht_ohne_ust"] = round(r["brutto_ohne_ust"] / n, 2) if n and r.get("brutto") else None
        r["netto_pro_nacht_ohne_ust"] = round(r["netto_ohne_ust"] / n, 2) if n and r.get("brutto") else None
        if "var_kosten_ohne_ust" in r:
            r["db_ohne_ust"] = round(r["netto_ohne_ust"] - r["var_kosten_ohne_ust"], 2)


SWAP = (("brutto", "brutto_ohne_ust"), ("netto", "netto_ohne_ust"), ("brutto_pro_nacht", "brutto_pro_nacht_ohne_ust"),
        ("netto_pro_nacht", "netto_pro_nacht_ohne_ust"), ("var_kosten", "var_kosten_ohne_ust"),
        ("var_naechte", "var_naechte_ohne_ust"), ("db", "db_ohne_ust"))


def view(records: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    """Datensätze für Auswertungen in der gewünschten Ansicht („ohne“ = Beträge ohne USt). Originale bleiben."""
    if mode != "ohne":
        return records
    out = []
    for r in records:
        if "brutto_ohne_ust" not in r:
            out.append(r)
            continue
        x = dict(r)
        for a, b in SWAP:
            if b in r:
                x[a] = r[b]
        x["ansicht"] = "ohne_ust"
        out.append(x)
    return out


def night_rows_net(rows: list[tuple], by_id: dict[Any, list[float]]) -> list[tuple]:
    """Nacht-Zeilen (channels.night_rows) mit Brutto ohne USt; Reihenfolge je Buchung = Nächte ab Anreise."""
    idx: dict[Any, int] = {}
    out = []
    for row in rows:
        bid = row[1]
        nets = by_id.get(bid)
        if not nets:
            out.append(row)
            continue
        i = idx.get(bid, 0)
        idx[bid] = i + 1
        out.append((*row[:4], nets[i] if i < len(nets) else row[4], *row[5:]))
    return out


def revenue_by_month_net(records: list[dict[str, Any]], until: date | None = None) -> dict[str, float]:
    """Wie models.revenue_by_month, aber je Nacht ohne USt (aus `naechte_ohne_ust`)."""
    out: dict[str, float] = {}
    for r in records:
        if r.get("blockiert") or r.get("storniert") or not r.get("brutto") or not r.get("naechte_ohne_ust"):
            continue
        a = _d(r["anreise"])
        for i, v in enumerate(r["naechte_ohne_ust"]):
            day = a + timedelta(days=i)
            if until and day >= until:
                break
            k = f"{day.year:04d}-{day.month:02d}"
            out[k] = round(out.get(k, 0.0) + v, 2)
    return out


def vat_by_month(records: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, dict[str, float]]:
    """USt je Monat (Leistungsdatum) und Satz: {"2026-01": {"7.0": 12.34}}."""
    out: dict[str, dict[str, float]] = {}
    for r in records:
        if r.get("blockiert") or r.get("storniert") or not r.get("ust"):
            continue
        a = _d(r["anreise"])
        n = r.get("naechte") or 0
        for i in range(n):
            day = a + timedelta(days=i)
            k = f"{day.year:04d}-{day.month:02d}"
            for p, v in (r.get("ust_je_satz") or {}).items():
                m = out.setdefault(k, {})
                m[str(p)] = round(m.get(str(p), 0.0) + v / n, 2)
    return out

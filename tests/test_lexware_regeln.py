"""Regelwerk Lexware (BETA): Sollwerte aus zwei echten Rechnungen des Betreibers (anonymisiert)."""

from datetime import date

from custom_components.smoobu import lexware_regeln as lr

PORTALE = ["Airbnb", "Booking.com"]

ART = {
    "a-uebern": {"id": "a-uebern", "title": "Übernachtung 1 Person o. Verpflegung", "description": "Nachtpreis für das Appartement",
                 "type": "SERVICE", "unitName": "Nächte", "price": {"leadingPrice": "GROSS", "grossPrice": 62.0, "netPrice": 57.94, "taxRate": 7}},
    "a-person": {"id": "a-person", "title": "Aufpreis 2. Person o. Verpflegung", "type": "SERVICE", "unitName": "Nächte",
                 "price": {"leadingPrice": "GROSS", "grossPrice": 10.0, "taxRate": 7}},
    "a-kind": {"id": "a-kind", "title": "Aufpreis Kind", "type": "SERVICE", "unitName": "Nächte",
               "price": {"leadingPrice": "GROSS", "grossPrice": 5.0, "taxRate": 7}},
    "a-hund": {"id": "a-hund", "title": "Sonderreinigung 1 Hund", "type": "SERVICE", "unitName": "Pauschal",
               "price": {"leadingPrice": "GROSS", "grossPrice": 10.0, "taxRate": 7}},
    "a-kurz": {"id": "a-kurz", "title": "Endreinigung Kurzzeit", "type": "SERVICE", "unitName": "Pauschal",
               "price": {"leadingPrice": "GROSS", "grossPrice": 10.0, "taxRate": 7}},
    "a-lang": {"id": "a-lang", "title": "Endreinigung Langzeit", "type": "SERVICE", "unitName": "Pauschal",
               "price": {"leadingPrice": "GROSS", "grossPrice": 30.0, "taxRate": 7}},
    "a-portal": {"id": "a-portal", "title": "Übernachtung [n] Person(en) o. Verpflegung",
                 "description": "Ferienwohnung\nGebucht und bezahlt über [Portal]", "type": "SERVICE", "unitName": "Pauschal",
                 "price": {"leadingPrice": "NET", "netPrice": 50.0, "taxRate": 7}},
}
IDS = {"Übernachtung": "a-uebern", "Aufpreis 2. Person": "a-person", "Aufpreis Kind": "a-kind",
       "Sonderreinigung Hund": "a-hund", "Endreinigung Kurzzeit": "a-kurz", "Endreinigung Langzeit": "a-lang"}
RULES = {
    "direkt": [{**r, "artikel": IDS[r["hinweis"]]} for r in lr.TEMPLATE["direkt"]],
    "portal": [{**lr.TEMPLATE["portal"][0], "artikel": "a-portal"}],
}


def _direct(**kw):
    b = {"id": 1, "arrival": "2026-10-22", "departure": "2026-10-25", "adults": 2, "children": 0, "price": 236.0,
         "channel": {"name": "Direct booking"},
         "priceElements": [{"type": "addon", "name": "Sonderreinigung 1 Hund", "amount": 10, "quantity": 1}]}
    b.update(kw)
    return b


def test_direktbuchung_wie_re2026_073():
    out = lr.build(_direct(), RULES, ART, today=date(2026, 10, 1), portal_channels=PORTALE)
    assert out["fehler"] == [] and out["warnungen"] == []
    pos = [(p["name"], p["menge"], p["einzel_brutto"]) for p in out["positionen"]]
    assert pos == [("Übernachtung 1 Person o. Verpflegung", 3, 62.0), ("Aufpreis 2. Person o. Verpflegung", 3, 10.0),
                   ("Sonderreinigung 1 Hund", 1, 10.0), ("Endreinigung Kurzzeit", 1, 10.0)]
    assert out["summen"]["brutto"] == 236.0 and out["summen"]["steuer"] == 15.44 and out["summen"]["netto"] == 220.56
    assert out["steuerart"] == "gross"
    # Rechnungsdatum heute, fällig zum Anreisetag
    assert out["rechnungsdatum"] == "2026-10-01" and out["faellig"] == "2026-10-22"
    pc = out["payload"]["paymentConditions"]
    assert pc == {"paymentTermLabel": "Zahlbar bis 22.10.2026.", "paymentTermDuration": 21}
    assert out["payload"]["shippingConditions"]["shippingType"] == "serviceperiod"
    assert out["payload"]["lineItems"][0]["unitPrice"] == {"currency": "EUR", "taxRatePercentage": 7.0, "grossAmount": 62.0}


def test_portal_firma_netto_wie_re2026_080():
    b = {"id": 2, "arrival": "2026-10-26", "departure": "2026-10-30", "adults": 1, "children": 0, "price": 330.41,
         "channel": {"name": "Booking.com"}}
    out = lr.build(b, RULES, ART, today=date(2026, 10, 26), portal_channels=PORTALE, company=True)
    assert out["gruppe"] == "portal" and out["steuerart"] == "net"
    (p,) = out["positionen"]
    assert p["name"] == "Übernachtung 1 Person(en) o. Verpflegung"
    assert p["beschreibung"].endswith("Gebucht und bezahlt über Booking.com")
    assert p["einzel_netto"] == 308.79
    assert out["summen"] == {"brutto": 330.41, "netto": 308.79, "steuer": 21.62, "steuer_je_satz": {7.0: 21.62}}
    assert out["payload"]["paymentConditions"]["paymentTermDuration"] == 0
    assert out["zahlungstext"] == "Die vollständige Zahlung haben wir bereits dankend erhalten."


def test_langzeit_kinder_zwei_hunde():
    b = _direct(departure="2026-11-12", adults=3, children=1, price=0,
                priceElements=[{"name": "Hund", "amount": 20, "quantity": 3}])
    # 21 Nächte: Aufpreis 2 Zusatzpersonen × 21, Kind × 21, Hunde max. 2, Langzeit-Reinigung
    b["price"] = 21 * 62 + 42 * 10 + 21 * 5 + 2 * 10 + 30
    out = lr.build(b, RULES, ART, today=date(2026, 10, 1), portal_channels=PORTALE)
    names = {p["name"]: p["menge"] for p in out["positionen"]}
    assert names["Aufpreis 2. Person o. Verpflegung"] == 42 and names["Aufpreis Kind"] == 21
    assert names["Sonderreinigung 1 Hund"] == 2 and "Endreinigung Langzeit" in names and "Endreinigung Kurzzeit" not in names
    assert out["positionen"][0]["einzel_brutto"] == 62.0 and out["summen"]["brutto"] == b["price"]


def test_gesamtrabatt_rest_vor_rabatt():
    b = _direct(price=224.2)  # 236 € − 5 %
    out = lr.build(b, RULES, ART, today=date(2026, 10, 1), portal_channels=PORTALE, overrides={"rabatt": 5})
    assert out["positionen"][0]["einzel_brutto"] == 62.0
    assert out["summen"]["brutto"] == 224.2 and out["payload"]["totalPrice"]["totalDiscountPercentage"] == 5


def test_hund_nur_als_hinweis_braucht_anzahl():
    b = _direct(priceElements=[], notice="Wir bringen unseren Hund mit", price=226)
    out = lr.build(b, RULES, ART, today=date(2026, 10, 1), portal_channels=PORTALE)
    assert "hunde_unbekannt" in out["fehler"]
    out = lr.build({**b, "price": 236}, RULES, ART, today=date(2026, 10, 1), portal_channels=PORTALE, overrides={"hunde": 1})
    assert out["fehler"] == [] and out["summen"]["brutto"] == 236


def test_saisonpreis_warnt_und_vordatierung():
    out = lr.build(_direct(price=400), RULES, ART, today=date(2026, 10, 1), portal_channels=PORTALE, invoice_date="anreise")
    assert "rest_abweichung" in out["warnungen"] and "rechnungsdatum_zukunft" in out["warnungen"]
    assert out["rechnungsdatum"] == "2026-10-22" and out["payload"]["paymentConditions"]["paymentTermDuration"] == 0


def test_platzhalter_und_regelpruefung():
    assert lr.fill("[Portal] · [n] · [Nächte] · [Faellig]", {"portal": "Airbnb", "n": "2", "naechte": "3", "faellig": "01.01.2027"}) \
        == "Airbnb · 2 · 3 · 01.01.2027"
    assert lr.validate_rules([{"menge": "nacht", "preis": "rest"}, {"menge": "pauschal", "preis": "rest"}]) == ["multiple_rest"]
    assert lr.validate_rules([{"menge": "quatsch"}]) == ["invalid_rule"]
    assert lr.validate_rules([{"menge": "nacht", "artikel": "x"}], {"a": {}}) == ["unknown_article"]


def test_ohne_artikel_fehler():
    out = lr.build(_direct(), {"direkt": lr.TEMPLATE["direkt"]}, ART, today=date(2026, 10, 1), portal_channels=PORTALE)
    assert "keine_artikel" in out["fehler"]

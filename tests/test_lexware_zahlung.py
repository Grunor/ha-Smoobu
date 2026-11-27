"""Lexware (BETA): Kontakte, Zahlungsstand, Smoobu-Haken, Testmodus-Client, Rate-Limit."""

import asyncio
from datetime import date

from custom_components.smoobu import lexware_client as lc
from custom_components.smoobu import lexware_kontakt as lk
from custom_components.smoobu import lexware_zahlung as lz

TODAY = date(2026, 11, 27)


def _ev(rec, pay, group="direkt", arrival=date(2026, 12, 20), today=TODAY, prepay=0.0):
    return lz.evaluate(rec, pay, group=group, total=236.0, smoobu_prepayment=prepay, arrival=arrival, today=today)


def test_status_und_hinweise():
    assert _ev(None, None)["status"] == "keine"
    draft = {"status": "draft", "erstellt": "2026-11-24", "summe": 236}
    assert _ev(draft, None)["hinweise"] == ["entwurf_offen"]
    rec = {"status": "open", "erstellt": "2026-11-19", "summe": 236}
    ev = _ev(rec, {"openAmount": 236, "voucherStatus": "open"})
    assert ev["status"] == "offen" and ev["soll_anzahlung"] == 118 and ev["hinweise"] == ["anzahlung_fehlt"]
    ev = _ev(rec, {"openAmount": 186, "voucherStatus": "open"})
    assert ev["status"] == "anzahlung_teilweise" and ev["gezahlt"] == 50 and "anzahlung_fehlt" in ev["hinweise"]
    ev = _ev(rec, {"openAmount": 118, "voucherStatus": "open"})
    assert ev["status"] == "anzahlung" and ev["hinweise"] == []
    # Anreisetag mit Rest offen
    ev = _ev(rec, {"openAmount": 118, "voucherStatus": "open"}, arrival=TODAY)
    assert ev["hinweise"] == ["rest_offen"]
    assert _ev(rec, {"openAmount": 0, "voucherStatus": "paid"})["status"] == "bezahlt"
    # Smoobu-Anzahlung hat Vorrang vor 50 %
    assert _ev(rec, {"openAmount": 136, "voucherStatus": "open"}, prepay=100)["status"] == "anzahlung"
    # Portal: keine Zahlungshinweise
    assert _ev(rec, {"openAmount": 236, "voucherStatus": "open"}, group="portal")["hinweise"] == []
    assert _ev({"status": "voided", "summe": 236}, None)["status"] == "storniert"


def test_bedeutung_bezahlt_haken():
    assert lz.effective_meaning(None, "direkt", True) == "lexware_zahlung"
    assert lz.effective_meaning(None, "portal", True) == "lexware_rechnung"
    assert lz.effective_meaning("lexware_rechnung", "portal", False) == "rechnung"
    ev = {"status": "anzahlung"}
    assert lz.smoobu_flags("lexware_zahlung", ev) == {"price_paid": False, "prepayment_paid": True}
    assert lz.smoobu_flags("lexware_zahlung", {"status": "bezahlt"}) == {"price_paid": True, "prepayment_paid": True}
    assert lz.smoobu_flags("lexware_zahlung", {"status": "entwurf"}) == {}
    assert lz.smoobu_flags("lexware_rechnung", {"status": "offen"}) == {"price_paid": True}
    assert lz.smoobu_flags("lexware_rechnung", {"status": "entwurf"}) == {"price_paid": False}
    assert lz.smoobu_flags("zahlung", ev) == {}


def test_kontakt_exakt_und_firma():
    results = [{"id": "1", "person": {"firstName": "Anna", "lastName": "Muster"}},
               {"id": "2", "person": {"firstName": "Anna", "lastName": "Muster-Beispiel"}},
               {"id": "3", "company": {"name": "Beispiel Bahn GmbH", "contactPersons": []}}]
    assert [c["id"] for c in lk.matches(results, name="anna  MUSTER")] == ["1"]
    assert [c["id"] for c in lk.matches(results, name="Beispiel Bahn GmbH", company=True)] == ["3"]
    g = lk.guest({"firstname": "Max", "lastname": "Probe", "email": "m@example.com",
                  "address": {"street": "Weg 1", "postalCode": "12345", "location": "Ort", "country": "Deutschland"}})
    c = lk.new_contact(g, company="Beispiel Bahn GmbH", salutation="herr")
    assert c["company"]["contactPersons"][0] == {"salutation": "Herr", "firstName": "Max", "lastName": "Probe",
                                                 "primary": True, "emailAddress": "m@example.com"}
    assert c["addresses"]["billing"][0]["countryCode"] == "DE" and "person" not in c
    assert lk.invoice_address("id-3", None, g, company=True, salutation="herr")["supplement"] == "z. Hd. Herrn Max Probe"
    # vorhandene Firma bekommt den Gast als weiteren Ansprechpartner …
    upd = lk.with_contact_person({"id": "3", "version": 2, "company": {"name": "X", "contactPersons": [{"lastName": "Alt"}]}}, g)
    assert [p["lastName"] for p in upd["company"]["contactPersons"]] == ["Alt", "Probe"]
    # … aber nicht, wenn Lexware den Kontakt sperrt (mehrere Einträge)
    assert lk.with_contact_person({"id": "3", "company": {"name": "X", "contactPersons": [{"lastName": "A"}, {"lastName": "B"}]}}, g) is None


def test_mock_client_ablauf():
    async def run():
        m = lc.MockLexware()
        assert len(await m.articles()) == 7
        cid = (await m.create_contact({"person": {"firstName": "Max", "lastName": "Probe"}}))["id"]
        assert (await m.contacts(name="Probe"))[0]["id"] == cid
        iid = (await m.create_invoice_draft({"lineItems": []}))["id"]
        assert await m.payments(iid) is None  # Entwurf hat keine Zahlung
        m.finalize(iid, 236.0)
        m.pay(iid, 118.0)
        p = await m.payments(iid)
        assert p["openAmount"] == 118.0 and p["voucherStatus"] == "open"
        m.pay(iid, 118.0)
        assert (await m.payments(iid))["voucherStatus"] == "paid"
    asyncio.run(run())


def test_token_bucket_bremst():
    clock = {"t": 0.0}
    waits = []

    async def sleep(s):
        waits.append(s)
        clock["t"] += s

    async def run():
        b = lc.TokenBucket(2.0, monotonic=lambda: clock["t"], sleep=sleep)
        for _ in range(5):
            await b.take()
    asyncio.run(run())
    assert round(sum(waits), 2) == 1.5  # 2 sofort, dann je 0,5 s

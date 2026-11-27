"""Lexware Office: Kontakte für Rechnungen (BETA, ab v1.20.0). Reine Logik ohne Home Assistant.

Entscheidungen Betreiber:
- 22.11.2026: Kontakt über den **Namen** suchen (Portale liefern oft maskierte Weiterleitungsadressen).
  Suchart in den Optionen wählbar (Name / E-Mail / beides), Standard Name.
- Lexware sucht Teilstrings ab 3 Zeichen → hier nur **exakte** Namenstreffer übernehmen (sonst landet
  „Müller-Lüdenscheidt“ auf der Rechnung von Herrn Müller). Genau 1 Treffer → verwenden; mehrere → Auswahl
  in der Vorschau; keiner → neuer Kunde.
- 27.11.2026: **Firmen** immer mit Firmenname; der Gast wird **Ansprechpartner** und steht auf der Rechnung.
  Grenze laut Lexware-Doku: Kontakte mit mehreren Einträgen bei Adressen, E-Mail, Telefon oder
  Ansprechpartnern lassen sich per API nicht ändern → dann wird der Gast nicht nachgetragen, die Vorschau
  weist darauf hin.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

SEARCH_MODES = ("name", "email", "beide")

COUNTRIES = {
    "deutschland": "DE", "germany": "DE", "allemagne": "DE", "duitsland": "DE", "niemcy": "DE",
    "österreich": "AT", "oesterreich": "AT", "austria": "AT", "schweiz": "CH", "switzerland": "CH", "suisse": "CH",
    "niederlande": "NL", "netherlands": "NL", "nederland": "NL", "holland": "NL", "belgien": "BE", "belgium": "BE",
    "frankreich": "FR", "france": "FR", "polen": "PL", "poland": "PL", "polska": "PL", "italien": "IT", "italy": "IT",
    "tschechien": "CZ", "czechia": "CZ", "czech republic": "CZ", "dänemark": "DK", "denmark": "DK",
    "luxemburg": "LU", "luxembourg": "LU", "spanien": "ES", "spain": "ES", "vereinigtes königreich": "GB",
    "united kingdom": "GB", "großbritannien": "GB", "usa": "US", "united states": "US",
}


def norm(text: Any) -> str:
    """Vergleichsform: klein, ß → ss, ohne Akzente/Satzzeichen, Leerraum zusammengefasst."""
    t = unicodedata.normalize("NFKD", str(text or "").lower().replace("ß", "ss")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t)).strip()


def guest(booking: dict[str, Any]) -> dict[str, str]:
    """Vor-/Nachname, E-Mail, Telefon und Adresse aus der Smoobu-Buchung."""
    first, last = str(booking.get("firstname") or "").strip(), str(booking.get("lastname") or "").strip()
    if not (first or last):
        parts = str(booking.get("guest-name") or "").strip().split()
        first, last = (" ".join(parts[:-1]), parts[-1]) if len(parts) > 1 else ("", parts[0] if parts else "")
    addr = booking.get("address") if isinstance(booking.get("address"), dict) else {}
    pick = lambda *keys: next((str(src.get(k)).strip() for src in (addr, booking) for k in keys if src.get(k)), "")  # noqa: E731
    return {"vorname": first, "nachname": last, "name": f"{first} {last}".strip(),
            "email": str(booking.get("email") or "").strip(), "telefon": str(booking.get("phone") or "").strip(),
            "strasse": pick("street"), "plz": pick("postalCode", "zip"), "ort": pick("location", "city"),
            "land": pick("country", "countryCode")}


def country_code(value: str, default: str = "DE") -> str:
    v = (value or "").strip()
    if re.fullmatch(r"[A-Za-z]{2}", v):
        return v.upper()
    return COUNTRIES.get(v.lower(), default)


def contact_name(c: dict[str, Any]) -> str:
    if c.get("company"):
        return str(c["company"].get("name") or "")
    p = c.get("person") or {}
    return " ".join(filter(None, [p.get("firstName"), p.get("lastName")]))


def contact_emails(c: dict[str, Any]) -> list[str]:
    return [m.lower() for v in (c.get("emailAddresses") or {}).values() for m in (v or [])]


def matches(results: list[dict[str, Any]], *, name: str, email: str = "", mode: str = "name", company: bool = False) -> list[dict[str, Any]]:
    """Exakte Treffer aus der (Teilstring-)Suche von Lexware. Firmen nur bei Firmen, Personen nur bei Privat."""
    out = []
    for c in results:
        if c.get("archived"):
            continue
        if bool(c.get("company")) != company:
            continue
        ok_name = norm(contact_name(c)) == norm(name)
        ok_mail = bool(email) and email.lower() in contact_emails(c)
        if (mode == "name" and ok_name) or (mode == "email" and ok_mail) or (mode == "beide" and ok_name and ok_mail):
            out.append(c)
    return out


def summary(c: dict[str, Any]) -> dict[str, Any]:
    """Kurzform für die Auswahl in der Vorschau (Adresse, Kundennummer)."""
    billing = ((c.get("addresses") or {}).get("billing") or [{}])[0] or {}
    return {"id": c.get("id"), "name": contact_name(c), "firma": bool(c.get("company")),
            "kundennummer": ((c.get("roles") or {}).get("customer") or {}).get("number"),
            "adresse": ", ".join(filter(None, [billing.get("street"), " ".join(filter(None, [billing.get("zip"), billing.get("city")]))])),
            "ansprechpartner": [" ".join(filter(None, [p.get("firstName"), p.get("lastName")]))
                                for p in (c.get("company") or {}).get("contactPersons") or []]}


def _salutation(value: str) -> str:
    return {"herr": "Herr", "frau": "Frau"}.get((value or "").lower(), "")


def new_contact(g: dict[str, str], *, company: str = "", salutation: str = "", default_country: str = "DE") -> dict[str, Any]:
    """Nutzlast für POST /v1/contacts (Rolle Kunde). Firma → Gast als primärer Ansprechpartner."""
    data: dict[str, Any] = {"version": 0, "roles": {"customer": {}}}
    person = {**({"salutation": _salutation(salutation)} if _salutation(salutation) else {}),
              **({"firstName": g["vorname"]} if g["vorname"] else {}), "lastName": g["nachname"] or g["name"] or "Gast"}
    if company:
        data["company"] = {"name": company, "contactPersons": [{
            **person, "primary": True,
            **({"emailAddress": g["email"]} if g["email"] else {}), **({"phoneNumber": g["telefon"]} if g["telefon"] else {})}]}
    else:
        data["person"] = person
    if g["strasse"] or g["ort"]:
        data["addresses"] = {"billing": [{**({"street": g["strasse"]} if g["strasse"] else {}),
                                          **({"zip": g["plz"]} if g["plz"] else {}), **({"city": g["ort"]} if g["ort"] else {}),
                                          "countryCode": country_code(g["land"], default_country)}]}
    if g["email"]:
        data["emailAddresses"] = {"business" if company else "private": [g["email"]]}
    if g["telefon"]:
        data["phoneNumbers"] = {"business" if company else "private": [g["telefon"]]}
    return data


def multi_entries(c: dict[str, Any]) -> bool:
    """Lexware sperrt Updates bei mehreren Einträgen in Adressen, E-Mail, Telefon oder Ansprechpartnern."""
    lists = [*((c.get("addresses") or {}).values()), *((c.get("emailAddresses") or {}).values()),
             *((c.get("phoneNumbers") or {}).values()), (c.get("company") or {}).get("contactPersons") or []]
    return any(len(v or []) > 1 for v in lists)


def with_contact_person(c: dict[str, Any], g: dict[str, str], salutation: str = "") -> dict[str, Any] | None:
    """Firmenkontakt mit dem Gast als Ansprechpartner (Nutzlast für PUT). None = schon vorhanden oder gesperrt."""
    persons = list((c.get("company") or {}).get("contactPersons") or [])
    if any(norm(" ".join(filter(None, [p.get("firstName"), p.get("lastName")]))) == norm(g["name"]) for p in persons):
        return None
    if multi_entries(c):
        return None  # laut Doku per API nicht änderbar → Gast nur auf der Rechnung (Adresszusatz)
    data = {k: v for k, v in c.items() if k not in ("id", "organizationId", "archived")}
    guest_person = {**({"salutation": _salutation(salutation)} if _salutation(salutation) else {}),
                    **({"firstName": g["vorname"]} if g["vorname"] else {}), "lastName": g["nachname"] or g["name"],
                    "primary": not persons}
    data["company"] = {**c["company"], "contactPersons": [*persons, guest_person]}
    return data


def invoice_address(contact_id: str, contact: dict[str, Any] | None, g: dict[str, str], *, company: bool,
                    salutation: str = "") -> dict[str, Any]:
    """Rechnungsadresse: Verweis auf den Kontakt. Bei Firmen zusätzlich der Gast als Ansprechpartner
    (Adresszusatz „z. Hd. …“, damit er auf der Rechnung steht – ob Lexware dafür das primäre
    Kontakt-Ansprechpartnerfeld nutzt, ist live zu prüfen)."""
    addr: dict[str, Any] = {"contactId": contact_id}
    if company and g["name"]:
        anrede = {"Herr": "Herrn", "Frau": "Frau"}.get(_salutation(salutation), "")
        addr["supplement"] = " ".join(filter(None, ["z. Hd.", anrede, g["name"]]))
    return addr

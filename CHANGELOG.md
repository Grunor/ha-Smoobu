# Changelog

Format je Version: deutsch, dann englisch. Versionierung nach [SemVer](https://semver.org/lang/de/): MAJOR = inkompatible Änderung (z. B. Entitäts-IDs), MINOR = neue Funktion, PATCH = Korrektur.
Format per version: German, then English. Versioning follows [SemVer](https://semver.org/): MAJOR = breaking change (e.g. entity IDs), MINOR = new feature, PATCH = fix.

Ein Release wird automatisch erstellt, sobald die Version in `custom_components/smoobu/manifest.json` erhöht wird.
A release is created automatically as soon as the version in `custom_components/smoobu/manifest.json` is increased.

## 1.3.0 – 2026-11-15

**Deutsch**
- Neue Sensoren „Preis aktueller Gast“ / „Preis nächster Gast“ mit Aufschlüsselung (Preiselemente), Preis pro Nacht, Anzahlung, offenem Betrag, Kurtaxe
- Neue Sensoren „Umsatz Monat“, „Umsatz Jahr“, „Umsatz Vorjahr“: Buchungspreis anteilig nach Nächten auf die Monate verteilt (Vorjahr + laufendes Jahr, stündlich bzw. nach Webhook neu geladen); Attribute mit Monatswerten und „davon bis heute“

**English**
- New sensors "Price current guest" / "Price next guest" with breakdown (price elements), price per night, prepayment, open amount, city tax
- New sensors "Revenue month", "Revenue year", "Revenue previous year": booking price split by nights across months (previous + current year, reloaded hourly or after webhook); attributes with monthly values and "so far"

## 1.2.0 – 2026-11-15

**Deutsch**
- Hunde-/Haustier-Erkennung aus Zusatzleistungen (z. B. „Endreinigung 1 Hund“) und Notizen: neue Binärsensoren „Hund aktueller Gast“ und „Hund nächster Gast“, Attribute `hund`/`hund_hinweis`, 🐕 im Kalendertitel und in der Beschreibung
- „Offene Zahlungen“ korrigiert: offener Betrag = Preis − bezahlte Anzahlung; neue Option „Kanäle mit Zahlung über das Portal“ (Standard Airbnb, Booking.com) – diese zählen nicht als offen

**English**
- Dog/pet detection from add-ons (e.g. "final cleaning 1 dog") and notes: new binary sensors "Dog current guest" and "Dog next guest", attributes `hund`/`hund_hinweis`, 🐕 in calendar title and description
- "Unpaid bookings" fixed: open amount = price − paid prepayment; new option "Channels paid via the portal" (default Airbnb, Booking.com) – these do not count as unpaid

## 1.1.0 – 2026-11-15

**Deutsch**
- Neue Option „Puffer nach Smoobu-Abreisezeit“: Steht in der Buchung eine Abreisezeit, gilt die Wohnung erst nach dieser Zeit + Puffer als frei; ohne Abreisezeit gilt der Standard-Check-out
- „Belegt“, „Aktueller Gast“ und „Nächste Abreise“ nutzen diese Freigabezeit; neues Attribut `freigabe`
- Kalender und Attribut `abreise` zeigen weiter die echte Abreisezeit

**English**
- New option "Buffer after Smoobu departure time": if the booking has a departure time, the apartment counts as vacant only after that time + buffer; without one the default check-out applies
- "Occupied", "Current guest" and "Next departure" use this release time; new attribute `freigabe`
- Calendar and attribute `abreise` still show the real departure time

## 1.0.2 – 2026-11-15

**Deutsch**
- Einrichtung und README: Zuordnung der Smoobu-Felder klargestellt (API-Schlüssel = Spalte „Schlüssel“ in der Liste, nicht das Label; Secret aus dem Fenster nach dem Erstellen)

**English**
- Setup and README: clarified mapping of Smoobu fields (API key = "Key" column in the list, not the label; secret from the window after creation)

## 1.0.1 – 2026-11-15

**Deutsch**
- Eigenes Integrations-Symbol (`brand/icon.png`, `brand/icon@2x.png`), wird ab Home Assistant 2026.3 in der Oberfläche angezeigt

**English**
- Own integration icon (`brand/icon.png`, `brand/icon@2x.png`), shown in the UI from Home Assistant 2026.3

## 1.0.0 – 2026-11-15

**Deutsch**
- Erstveröffentlichung
- HMAC-SHA256-signierter API-Client nach aktueller Smoobu-Spezifikation
- Einrichtung über die Oberfläche mit Neu-Anmeldung und Optionen (Abfrageintervall, Webhook, Standard-Check-in/-out, Zeitfenster, Detaildaten)
- Belegungskalender je Wohnung mit vollem Gastnamen
- 12 Sensoren und 4 Binärsensoren je Wohnung, Diagnose-Entitäten fürs Konto
- Entitäts-IDs mit Präfix `smoobu_` (`<domain>.smoobu_<wohnung>_<entität>`)
- Echtzeit-Webhook (Nabu Casa oder externe HTTPS-URL) mit automatischer Registrierung bei Smoobu
- Event `smoobu_event`, Aktionen `refresh`, `get_reservations`, `get_reservation`, `get_messages`, `send_message`
- Diagnose-Download mit geschwärzten Gästedaten, Übersetzungen Deutsch/Englisch

**English**
- Initial release
- HMAC-SHA256 signed API client according to the current Smoobu specification
- UI setup with re-authentication and options (polling interval, webhook, default check-in/-out, time window, details)
- Occupancy calendar per apartment with full guest name
- 12 sensors and 4 binary sensors per apartment, diagnostic entities for the account
- Entity IDs prefixed with `smoobu_` (`<domain>.smoobu_<apartment>_<entity>`)
- Real-time webhook (Nabu Casa or external HTTPS URL) with automatic registration at Smoobu
- Event `smoobu_event`, actions `refresh`, `get_reservations`, `get_reservation`, `get_messages`, `send_message`
- Diagnostics download with redacted guest data, German/English translations

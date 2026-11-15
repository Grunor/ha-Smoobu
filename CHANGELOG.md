# Changelog

Format je Version: deutsch, dann englisch. Versionierung nach [SemVer](https://semver.org/lang/de/): MAJOR = inkompatible Änderung (z. B. Entitäts-IDs), MINOR = neue Funktion, PATCH = Korrektur.
Format per version: German, then English. Versioning follows [SemVer](https://semver.org/): MAJOR = breaking change (e.g. entity IDs), MINOR = new feature, PATCH = fix.

Ein Release wird automatisch erstellt, sobald die Version in `custom_components/smoobu/manifest.json` erhöht wird.
A release is created automatically as soon as the version in `custom_components/smoobu/manifest.json` is increased.

## 1.9.0 – 2026-11-15

Enthält / includes 1.7.0 (Daten), 1.8.0 (Karten), 1.9.0 (Aktionen).

**Deutsch**
- Kanal-Sensoren: ein Sensor je Kanal (Portale und Direktkanäle), automatisch für neue Kanäle; Umsatz, Netto, Kosten, Nächte, Auslastung, Buchungen, Stornos/Stornoquote, Ø Aufenthalt, Ø Personen, Ø Vorlaufzeit für Monat, Jahr, bis heute, Vorjahr u. a., Monatswerte
- Filter ohne Templates: Auswahl-Entitäten Kanal, Zeitraum, Vergleich + 13 Auswertungs-Sensoren mit Vergleichswert und Veränderung
- Prognose Jahresende (gebucht + Nachbuchungen wie im Vorjahr)
- Stornos werden geladen (nur für Stornoquote, nie im Umsatz); neue Option „Auswertung: Jahre Historie“ (Standard 2)
- Eigene Dashboard-Karten (automatisch geladen): Übersicht, Belegungsplan mit Preisen, Buchungsliste mit CSV-Export, Finanzen mit Filtern und Vergleich, Posteingang; gemeinsame Buchungs-Detailansicht
- WebSocket-Befehle `smoobu/info`, `analytics`, `bookings`, `booking`, `rates`, `subscribe`
- Neue Aktionen: `block_period`, `delete_reservation` (Portalbuchungen geschützt), `set_rates`, `update_reservation`

**English**
- Channel sensors: one per channel (portals and direct channels), created automatically for new channels; revenue, net, costs, nights, occupancy, bookings, cancellations/rate, avg. stay, avg. guests, avg. lead time for month, year, year to date, previous year and more, monthly values
- Filters without templates: select entities channel, period, comparison + 13 analysis sensors with comparison value and change
- Year-end forecast (booked + pickup like last year)
- Cancellations are loaded (only for the cancellation rate, never as revenue); new option "Analysis: years of history" (default 2)
- Own dashboard cards (loaded automatically): overview, occupancy plan with prices, booking list with CSV export, finance with filters and comparison, inbox; shared booking detail view
- WebSocket commands `smoobu/info`, `analytics`, `bookings`, `booking`, `rates`, `subscribe`
- New actions: `block_period`, `delete_reservation` (portal bookings protected), `set_rates`, `update_reservation`

## 1.6.0 – 2026-11-15

**Deutsch**
- Direktvermarktung vs. Portale: Umsatz Direkt/Portale Jahr, Direktanteil (inkl. Ersparnis), Vergleich Vorjahr gesamt und bis heute, Aufschlüsselung je Kanal
- Nettoumsatz Monat/Jahr und „Provision & Gebühren Jahr“: echte Provision aus Smoobu, sonst konfigurierter %-Satz; Booking.com-Zahlungsgebühr wird aus der Buchung gelesen
- Neuer Optionsschritt „Provisionen“ mit Standardwerten je Kanal und Direktkanälen
- Je Gast: Kanalgruppe, Provision, Nettopreis

**English**
- Direct marketing vs. portals: direct/portal revenue, direct share (incl. savings), comparison with previous year (total and year-to-date), per-channel breakdown
- Net revenue month/year and "Commission & fees year": actual commission from Smoobu, otherwise configured percentage; Booking.com payment charge read from the booking
- New options step "Commissions" with defaults per channel and direct channels
- Per guest: channel group, commission, net price

## 1.5.0 – 2026-11-15

**Deutsch**
- Alle Buchungsfelder des aktuellen und nächsten Gastes als eigene Entitäten (29 je Gast: Kanal, Sprache, E-Mail, Telefon, Personen, Zeiten, Beträge, Zahlungsstatus, Notizen, IDs …); selten genutzte sind deaktiviert
- Preise & Verfügbarkeit über `/api/rates` (60 Tage): Preis heute/morgen, Mindestaufenthalt, nächster freier Tag, freie Nächte 30 Tage, nächste Lücke zwischen Belegungen
- Sensor „Letzte Gästenachricht“: Text wird bei Webhook `newMessage` geladen, übersteht Neustarts

**English**
- All booking fields of the current and next guest as individual entities (29 per guest: channel, language, email, phone, guests, times, amounts, payment status, notes, IDs …); rarely used ones are disabled
- Prices & availability via `/api/rates` (60 days): price today/tomorrow, minimum stay, next free day, free nights 30 days, next gap between stays
- Sensor "Last guest message": text is loaded on webhook `newMessage`, survives restarts

## 1.4.0 – 2026-11-15

**Deutsch**
- Neue Sensoren „Umsatz Vormonat“ und „Umsatz Folgemonat“ mit Vorjahresvergleich (absolut und in %), Auslastung und Nächten
- Neuer Sensor „Auslastung Monat“ (nur Gäste-Nächte) mit Monatswerten für Jahr und Vorjahr
- Neuer Sensor „Gesperrte Nächte Monat“ – Sperrzeiten separat, mit Monatswerten (Nächte und %)
- „Umsatz Monat“: zusätzlich Folgemonat und Veränderung zu Vormonat/Vorjahresmonat in %
- Umsatzdaten reichen bis Januar des Folgejahres (für den Folgemonat im Dezember)

**English**
- New sensors "Revenue previous month" and "Revenue next month" with year-over-year comparison (absolute and %), occupancy and nights
- New sensor "Occupancy rate month" (guest nights only) with monthly values for current and previous year
- New sensor "Blocked nights month" – blocked periods separately, with monthly values (nights and %)
- "Revenue month": additionally next month and change vs. previous month/previous year in %
- Revenue data now extends to January of the next year (for the next month in December)

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

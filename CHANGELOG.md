# Changelog

Format je Version: deutsch, dann englisch. Versionierung nach [SemVer](https://semver.org/lang/de/): MAJOR = inkompatible Änderung (z. B. Entitäts-IDs), MINOR = neue Funktion, PATCH = Korrektur.
Format per version: German, then English. Versioning follows [SemVer](https://semver.org/): MAJOR = breaking change (e.g. entity IDs), MINOR = new feature, PATCH = fix.

Ein Release wird automatisch erstellt, sobald die Version in `custom_components/smoobu/manifest.json` erhöht wird.
A release is created automatically as soon as the version in `custom_components/smoobu/manifest.json` is increased.

## 1.15.0 – 2026-11-15

**Deutsch**
- **Neues Design der Dashboard-Karten** („Moos & Schiefer“): eigene, aufeinander abgestimmte Farben für hell und dunkel (Kanäle, Zustände, Flächen), Schrift *Schibsted Grotesk* (SIL OFL 1.1, lokal unter `www/fonts/`, kein externer Server), ruhigere Tabellen, Knöpfe und Chips
- **Hell / Dunkel / System** je Gerät (gespeichert im Browser); „System“ folgt dem Dunkelmodus von Home Assistant. Gilt für alle Karten, die Buchungsdetails, Bestätigungen und Meldungen
- Neue Karte **`custom:smoobu-header-card`**: Seiten-Navigation (Zähler offener Nachrichten), Wohnungsauswahl, Hell/Dunkel/System; färbt den Seitenhintergrund passend zum Modus
- **Übersicht neu aufgebaut:** Status heute als kurzer, präziser Satz (Belegt bis / Abreise / Anreise / Gästewechsel / Frei bis) plus Monatsstand; aktueller und nächster Gast; Belegungsband der nächsten 6 Wochen (Balken von Tagesmitte zu Tagesmitte, Preise unter freien Nächten); Kennzahlenleiste mit 12-Monats-Verlauf (Monat, Auslastung, Jahr bis heute, Prognose ggü. Vorjahr gesamt, Netto je Nacht, Direktanteil mit gesparter Provision); nächste Anreisen, freie Zeiträume mit Preisspanne, **„Wartet auf dich“** (offene Gastnachrichten mit Textanfang, offene Zahlungen der nächsten 30 Tage)
- **Mehrere Wohnungen:** Auswahl „Alle / Wohnung …“ (ab 2 Wohnungen, je Gerät). „Alle“: Kennzahlen summiert, Auslastung über alle verfügbaren Nächte, Status je Wohnung, Belegung mit einer Zeile je Wohnung, Buchungsliste mit Spalte Wohnung, Finanzen mit Wohnungsvergleich, Posteingang gemischt. Automatische Wohnungskürzel (`kuerzel` in `smoobu/info`). Karten mit `apartment_id` bleiben fest
- WebSocket: `apartment_id: "alle"` für `bookings`, `analytics`, `booking`, `message_status`, `message_done` und den Assistenten; `analytics` liefert `einheiten`; `rates` lehnt „alle“ ab (Preise gehören zu einer Wohnung); `message_status` liefert `letzte_text` (Anfang der offenen Gastnachricht)
- Dashboard-Vorlage auf die Kopfleiste umgestellt; Seiten-Screenshots hell/dunkel und mit 3 Wohnungen (`tools/screenshots/render_pages.py`)

**English**
- **New card design** ("Moss & Slate"): dedicated, matched colours for light and dark (channels, states, surfaces), *Schibsted Grotesk* typeface (SIL OFL 1.1, local in `www/fonts/`, no external server), calmer tables, buttons and chips
- **Light / Dark / System** per device (stored in the browser); "System" follows Home Assistant's dark mode. Applies to all cards, booking details, confirmations and toasts
- New card **`custom:smoobu-header-card`**: page navigation (open-message counter), property selector, light/dark/system; colours the page background to match
- **Overview rebuilt:** today's status as a short, precise sentence plus month status; current and next guest; occupancy band for the next 6 weeks with prices; key-figure strip with 12-month trend; upcoming arrivals, free periods with price range, **"Waiting for you"** (open guest messages with text preview, open payments of the next 30 days)
- **Several properties:** selector "All / property …" (from 2 properties, per device). "All": figures summed, occupancy over all available nights, status per property, one occupancy row per property, booking list with property column, finance with property comparison, combined inbox. Automatic property codes (`kuerzel` in `smoobu/info`). Cards with `apartment_id` stay fixed
- WebSocket: `apartment_id: "alle"` for `bookings`, `analytics`, `booking`, `message_status`, `message_done` and the assistant; `analytics` returns `einheiten`; `rates` rejects "alle"; `message_status` returns `letzte_text`
- Dashboard template switched to the header card; page screenshots light/dark and with 3 properties

## 1.14.0 – 2026-11-15

**Deutsch**
- Neue Option **„KI-Funktionen erlauben“** (Optionen → KI-Assistent): Hauptschalter für alle KI-Funktionen. Aus = KI **explizit gesperrt** – jeder Aufruf von `ai_task` wird zentral abgelehnt (Karten, Aktionen `assistant_suggest`/`assistant_build_knowledge`, WebSocket, Push-Buttons, Webhook), es gehen keine Daten an einen KI-Anbieter. Die Karten grauen ✨ Vorschlag, Anlass-Auswahl und 📚 Wissen erzeugen aus und zeigen „🔒 KI gesperrt“. Wissensdatenbank, Lernen, Import, Tagesbriefing und Lücken-Meldung funktionieren weiter
- Standard: bestehende Installationen mit gewählter KI-Entität bleiben erlaubt (keine Verhaltensänderung), neue Installationen starten ohne KI. „KI erlauben“ ohne KI-Entität wird im Formular abgelehnt
- „Assistent aktivieren“ heißt jetzt **„Automatische Antwortvorschläge“** und wirkt nur bei erlaubter KI; ✨ Vorschlag auf Abruf geht auch ohne diese Option
- Posteingang: neuer Button **„Keine Antwort nötig“** (in der Liste und im Verlauf) – hakt die offene Gastnachricht ohne Antwort ab, bis der Gast erneut schreibt; rückgängig machbar; ein offener KI-Vorschlag wird dabei verworfen. Neuer WebSocket-Befehl `smoobu/message_done`, Status `ohne_antwort`/`erledigt_id` in `smoobu/message_status`
- Korrektur: **„Antwort offen“ nur bei Nachrichten VOM Gast.** Der Status wurde mit `onlyRelatedToGuest=true` ermittelt – dabei fehlten automatische Nachrichten an den Gast (z. B. Willkommensnachricht), die Buchung erschien fälschlich offen. Jetzt werden alle Nachrichten (ohne interne Notizen) ausgewertet; `type` wird auch als Text erkannt
- Korrektur: Sensor **„Letzte Gästenachricht“** zeigt nur noch Nachrichten vom Gast; eigene Nachrichten an den Gast überschreiben ihn nicht mehr (auch ein so gespeicherter alter Stand wird nach dem Neustart nicht übernommen)
- Nachrichtenverlauf: Richtung eindeutig beschriftet („← Vom Gast“ / „→ An den Gast“)
- README: **Screenshots** aller Karten mit erfundenen Demodaten, **Dashboard-Vorlage** `docs/dashboard-vorlage.yaml`, Optionen des KI-Assistenten dokumentiert. Screenshots reproduzierbar über `tools/screenshots/render_screenshots.py` (echte Integration + Demodaten + Chrome headless)

**English**
- New option **"Allow AI features"** (Options → AI assistant): master switch for all AI features. Off = AI **explicitly locked** – every `ai_task` call is rejected centrally (cards, actions `assistant_suggest`/`assistant_build_knowledge`, WebSocket, push buttons, webhook), no data is sent to an AI provider. The cards grey out ✨ Suggestion, occasion selector and 📚 Build knowledge and show "🔒 AI locked". Knowledge base, learning, import, daily briefing and gap report keep working
- Default: existing installations with an AI entity stay allowed (no behaviour change), new installations start without AI. "Allow AI" without an AI entity is rejected in the form
- "Enable assistant" is now **"Automatic reply suggestions"** and only works with AI allowed; on-demand ✨ suggestions work without it
- Inbox: new **"No reply needed"** button (list and thread) – marks the open guest message as done without replying until the guest writes again; can be undone; an open AI suggestion is discarded. New WebSocket command `smoobu/message_done`, status `ohne_antwort`/`erledigt_id` in `smoobu/message_status`
- Fix: **"Reply pending" only for messages FROM the guest.** The status used `onlyRelatedToGuest=true`, which left out automatic messages to the guest (e.g. welcome message), so bookings wrongly showed as open. All messages (without internal notes) are now evaluated; `type` is also recognised as text
- Fix: sensor **"Last guest message"** only shows messages from the guest; your own messages to the guest no longer overwrite it (an old state stored that way is not restored after a restart)
- Message thread: direction clearly labelled ("← From guest" / "→ To guest")
- README: **screenshots** of all cards with fictional demo data, **dashboard template** `docs/dashboard-vorlage.yaml`, AI assistant options documented. Screenshots reproducible via `tools/screenshots/render_screenshots.py` (real integration + demo data + headless Chrome)

## 1.13.0 – 2026-11-15

**Deutsch**
- Posteingang: Gäste mit **offener Nachricht** (neueste Nachricht vom Gast, noch nicht beantwortet) werden deutlich markiert – roter Rand, rote Tönung, Badge „💬 Antwort offen“ – und stehen oben in der Liste; in der Kopfzeile steht die Anzahl
- Neuer WebSocket-Befehl `smoobu/message_status` (Antwortstatus je Buchung, 10 min Cache; neue Nachricht per Webhook und eigenes Senden aktualisieren sofort). Interne Notizen zählen nicht als Antwort

**English**
- Inbox: guests with an **open message** (latest message from the guest, not yet answered) are clearly highlighted – red edge, red tint, "💬 Reply pending" badge – and listed first; the header shows the count
- New WebSocket command `smoobu/message_status` (reply status per booking, 10 min cache; new messages via webhook and own replies refresh immediately). Internal notes do not count as a reply

## 1.12.1 – 2026-11-15

**Deutsch**
- Nachrichtenverlauf (Posteingang und Buchungsdetails) zeigt die neueste Nachricht jetzt oben

**English**
- Message history (inbox and booking details) now shows the newest message on top

## 1.12.0 – 2026-11-15

**Deutsch**
- Neuer Binärsensor „Anreise morgen“ (`binary_sensor.…_anreise_morgen`): an, wenn morgen ein Gast anreist; Attribute wie „Anreise heute“ (u. a. `gastname`, `anreise`, `hund`, `hund_hinweis`). Ermöglicht Vorabend-Automationen ohne Datums-Templates

**English**
- New binary sensor "Arrival tomorrow" (`binary_sensor.…_anreise_morgen`): on when a guest arrives tomorrow; same attributes as "Arrival today" (incl. `gastname`, `anreise`, `hund`, `hund_hinweis`). Enables evening-before automations without date templates

## 1.11.0 – 2026-11-15

**Deutsch**
- Option „Puffer nach Smoobu-Abreisezeit“ heißt jetzt „Wartezeit nach Check-out“ und gilt **immer**: Freigabe (tatsächlicher Check-out, „Belegt“ aus, Sensor „Nächste Abreise“, Attribut `freigabe`) = Abreisezeit aus Smoobu bzw. Standard-Check-out + Wartezeit, z. B. 11:00 + 30 min = 11:30
- Standard-Check-out ist damit die offizielle Check-out-Zeit für Gäste (Attribut `abreise`, Kalender, Assistent)
- Achtung: Wer bisher einen Puffer > 0 und einen späteren Standard-Check-out eingestellt hatte, sollte den Standard-Check-out auf die echte Gästezeit zurücksetzen

**English**
- Option "Buffer after Smoobu departure time" is now "Waiting time after check-out" and **always** applies: release (actual check-out, "Occupied" off, "Next departure" sensor, `freigabe` attribute) = departure time from Smoobu or default check-out + waiting time, e.g. 11:00 + 30 min = 11:30
- The default check-out is now the official guest check-out time (attribute `abreise`, calendar, assistant)
- Note: if you used a buffer > 0 with a later default check-out, set the default check-out back to the real guest time

## 1.10.3 – 2026-11-15

**Deutsch**
- Assistent: Vorlagenerkennung zusätzlich über den Text ohne Anrede (gleicher Text ≥ 3-mal in ≥ 2 Buchungen) und über Betreffe ohne Nummern („Rechnung RE2026-045 …“)
- Automatische Portal-Antworten („Request approved“, „Confirm for free“) werden nicht gelernt
- Airbnb-Zitate („Reply to: …“) und Mail-Köpfe („Gesendet: …“) werden abgeschnitten

**English**
- Assistant: template detection also by text without greeting (same text ≥ 3 times in ≥ 2 bookings) and by subjects without numbers
- Automatic portal replies ("Request approved", "Confirm for free") are not learned
- Airbnb quotes ("Reply to: …") and mail headers ("Gesendet: …") are cut off

## 1.10.2 – 2026-11-15

**Deutsch**
- Übersicht: Abstand nach oben (Panel-Ansicht), Chip-Zeile zeigt nur noch Ereignisse von heute (Anreise mit 🐕/Ankunftszeit, Abreise, 🧹 Reinigung heute, Gästewechsel); Hunde-Chips künftiger Gäste entfernt (🐕 steht am Namen)
- Neuer Vergleich „Buchungsstand Vorjahr“ (`vorjahr_stand`): Vorjahreszeitraum nur mit Buchungen, die am gleichen Kalendertag schon bestanden (Stornos über Änderungsdatum angenähert); auch in der Auswahl „Auswertung Vergleich“
- Übersicht: Monatskacheln vergleichen mit dem Buchungsstand Vorjahr; Hinweiszeile erklärt Vergleichszeiträume und PP (Prozentpunkte)

**English**
- Overview: top spacing (panel view), chip row shows only today's events (arrival with 🐕/check-in time, departure, 🧹 cleaning today, changeover); dog chips for future guests removed (🐕 shown at the name)
- New comparison "previous year booking status" (`vorjahr_stand`): previous-year period limited to bookings that existed on the same calendar day (cancellations approximated via modification date); also in the "Analysis comparison" select
- Overview: month tiles compare against the previous year's booking status; note line explains comparison periods and PP (percentage points)

## 1.10.1 – 2026-11-15

**Deutsch**
- Assistent: Vorlagen (automatische Smoobu-Nachrichten, gleicher Betreff in ≥ 3 Buchungen) werden erkannt und nicht mehr als Antwort auf die Gästenachricht davor gelernt
- Bereinigung aller Lerntexte und KI-Eingaben: HTML/Entities, Zitate, Mail-Köpfe, Signaturen („Gesendet von Outlook …“), Airbnb-Reaktionen
- Schwärzung vor dem Speichern und vor dem Senden an die KI: IBAN, E-Mail, Telefonnummern, Zugangs-Codes, persönliche Links
- Erneuter Import ersetzt frühere Import-Beispiele

**English**
- Assistant: templates (automatic Smoobu messages, same subject in ≥ 3 bookings) are detected and no longer learned as reply to the preceding guest message
- Cleaning of all learning texts and AI input: HTML/entities, quotes, mail headers, signatures, Airbnb reactions
- Redaction before storing and before sending to the AI: IBAN, e-mail, phone numbers, access codes, personal links
- Re-import replaces earlier import examples

## 1.10.0 – 2026-11-15

**Deutsch**
- KI-Assistent: Antwortvorschläge bei neuen Gästenachrichten per `ai_task` (Anbieter wählbar), Push mit Senden/Bearbeiten/Ignorieren und „Ankunft übernehmen“; keine Erfindungen ([OFFEN: …] + Wissenslücke)
- Wissensdatenbank (aktiv/Vorschlag/aus, vertraulich), Lernen aus allen gesendeten Antworten, Import des Verlaufs, Wissensvorschläge aus Vorlagen
- Dringende Probleme mit HA-Status, Tagesbriefing, nicht buchbare Lücken mit Button
- Neuer Optionsschritt „KI-Assistent“, Sensor „Assistent offene Vorschläge“, Aktionen `assistant_suggest`, `assistant_import`, `assistant_build_knowledge`, Karte `smoobu-assistant-card`, ✨ Vorschlag im Posteingang
- Senden aus Karten läuft über den Assistenten (Lernbeispiel); Signaturen „Von meinem … gesendet“ werden erkannt

**English**
- AI assistant: reply suggestions for new guest messages via `ai_task` (any provider), push with send/edit/ignore and "apply arrival"; no invention ([OFFEN: …] + knowledge gap)
- Knowledge base (active/suggestion/off, confidential), learning from all sent replies, history import, knowledge suggestions from templates
- Urgent problems with HA state, daily briefing, unbookable gaps with button
- New options step "AI assistant", sensor "Assistant open suggestions", actions `assistant_suggest`, `assistant_import`, `assistant_build_knowledge`, card `smoobu-assistant-card`, ✨ suggestion in the inbox
- Sending from cards goes through the assistant (learning example); "Sent from my …" signatures are detected

## 1.9.2 – 2026-11-15

**Deutsch**
- €/Nacht nur aus Nächten mit Preis (Buchungen ohne Preis zählen weiter zur Auslastung)
- Übersicht: „Heute abgereist“ statt „Aktueller Gast“ nach der Freigabe, „morgen“ statt „in 1 Tage“; Erkenntnis „Höchste Stornoquote“ erst ab 3 Buchungen
- Sperren: `block_period` nutzt gezielt den Kanal „Blocked channel“ (nicht „Blocked channel auto“)
- Buchungsliste: stornierte (automatische) Sperrzeiten ausgeblendet, außer „storniert“ + „blockiert“ sind gewählt; Posteingang: letzte Nachricht ohne Leerraum, Zitat eingeklappt

**English**
- €/night only from nights with a price (bookings without price still count for occupancy)
- Overview: "Departed today" instead of "Current guest" after release, "tomorrow"; insight "highest cancellation rate" only from 3 bookings
- Blocking: `block_period` uses the "Blocked channel" (not "Blocked channel auto")
- Booking list: cancelled (automatic) blocks hidden unless "cancelled" + "blocked" are selected; inbox: last message without extra whitespace, quote collapsed

## 1.9.1 – 2026-11-15

**Deutsch**
- Stornierte Sperrzeiten zählen nicht mehr als gesperrte Nächte in der Auswertung
- Karten: Datumsangaben aus Smoobu auch in Safari/iOS lesbar; zitierter E-Mail-Verlauf in Gastantworten wird eingeklappt

**English**
- Cancelled blocks no longer count as blocked nights in the analysis
- Cards: Smoobu timestamps readable in Safari/iOS; quoted e-mail history in guest replies is collapsed

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

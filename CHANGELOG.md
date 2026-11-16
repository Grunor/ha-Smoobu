# Changelog

Format je Version: deutsch, dann englisch. Versionierung nach [SemVer](https://semver.org/lang/de/): MAJOR = inkompatible Änderung (z. B. Entitäts-IDs), MINOR = neue Funktion, PATCH = Korrektur.
Format per version: German, then English. Versioning follows [SemVer](https://semver.org/): MAJOR = breaking change (e.g. entity IDs), MINOR = new feature, PATCH = fix.

Änderungen werden auf dem Branch `develop` unter „Unveröffentlicht“ gesammelt. Ein Release entsteht, sobald die Version in `custom_components/smoobu/manifest.json` erhöht und nach `main` übernommen wird. Beta-Versionen (z. B. `1.17.0b1`) werden direkt von `develop` als Pre-Release veröffentlicht.
Changes are collected on the `develop` branch under "Unreleased". A release is created as soon as the version in `custom_components/smoobu/manifest.json` is increased and merged into `main`. Beta versions (e.g. `1.17.0b1`) are published from `develop` as pre-releases.

## Unveröffentlicht / Unreleased

**Deutsch**
- **Buchungszeitpunkt – Ansicht „Gebucht im → für“:** zusätzliche Matrix Buchungsmonat × Aufenthaltsmonat (Zeile = 100 %), Diagonale = gleicher Monat umrandet, Spalte „vor allem für“ (Top 3) und Hinweise auf auffällige Vorausbuchungen (z. B. „Im Juni wird schon für August gebucht“); Tooltip zusätzlich mit Anteil am Aufenthaltsmonat

**English**
- **Booking timing – view "Booked in → for":** additional matrix booking month × stay month (row = 100 %), diagonal (same month) outlined, column "mainly for" (top 3) and hints on notable advance bookings (e.g. "In June bookings are already made for August"); tooltip also shows the share of the stay month


## 1.17.0b5 – 2026-11-16

> Beta / Pre-release

**Deutsch**
- **Statistik: neues Modul „Buchungszeitpunkt“:** Matrix Aufenthaltsmonat (Jan–Dez) × Abstand zum Buchungsmonat (> 12, 7–12, 4–6, 3, 2, 1 Monat vorher, gleicher Monat) als Anteil je Zeile, umschaltbar Nächte/Buchungen/Umsatz und Basis „alle Jahre“ (abgeschlossene Monate, ohne ausgenommene Jahre wie 2020) oder gewählter Zeitraum; Spalte „Hälfte gebucht bis“ und Kernaussage (Anteil kurzfristig/langfristig gebucht). Neue Baukasten-Dimensionen `vorlauf_monate` und `buchungsmonat_im_jahr`

**English**
- **Statistics: new module "Booking timing":** matrix stay month (Jan–Dec) × distance to the booking month (> 12, 7–12, 4–6, 3, 2, 1 month before, same month) as share per row, switchable nights/bookings/revenue and basis "all years" (completed months, excluding years such as 2020) or the selected period; column "half booked by" and key statement (share booked short-term/long-term). New builder dimensions `vorlauf_monate` and `buchungsmonat_im_jahr`


## 1.17.0b4 – 2026-11-16

> Beta / Pre-release

**Deutsch**
- **Zahlungseingang im Dashboard markieren:** In „Wartet auf dich“ (Übersicht) stehen bei offenen Zahlungen jetzt die Buttons „✓ Erhalten“ und – bei offener Anzahlung – „✓ Anzahlung“ (Betrag der Anzahlung in der Zeile); „Buchung öffnen“ ist dort ein Textlink. In den Buchungsdetails zeigt der Preisbereich den Restbetrag und die Buttons „✓ Anzahlung erhalten“ / „✓ Zahlung erhalten“ sowie als Rückweg „↶ Anzahlung offen“ / „↶ Als offen markieren“. Jede Änderung wird vorher bestätigt und über `smoobu.update_reservation` direkt in Smoobu gespeichert; „Zahlung erhalten“ setzt eine offene Anzahlung mit auf bezahlt
- **Portal-Buchungen als erhalten markieren:** Auch Buchungen über Portale (Airbnb, Booking.com, HomeToGo, Expedia …) lassen sich jetzt als „erhalten“ markieren (z. B. sobald die Rechnung an den Gast geschrieben ist); maßgeblich ist der Smoobu-Status „bezahlt“. Buchungsdetails: „✓ Zahlung erhalten“ bzw. „↶ Als offen markieren“; der Kopf zeigt ohne Markierung neutral „Bezahlt über <Kanal>“, danach „✓ bezahlt“. „Wartet auf dich“: Portal-Buchungen ohne Markierung erscheinen ab dem Anreisetag (bis 60 Tage zurück) als „Zahlung offen“ mit Kanalname, Bruttobetrag gedämpft und „✓ Erhalten“; höchstens drei, der Rest als Zeile „Weitere ohne Markierung“. Sensoren und offene Zahlungen im Backend bleiben unverändert (Portal kassiert)
- **Statistik-Werkbank, Teil 1 (Backend):** neuer WebSocket-Befehl `smoobu/stats` als Grundlage der kommenden Statistikseite. `mode: "query"` = Baukasten-Abfrage Kennzahl × Gruppierung × Aufteilung (18 Kennzahlen inkl. ADR, RevPAR, Netto-RevPAR, Stornoquote, Median-Vorlauf/-Aufenthalt; 17 Dimensionen inkl. Wochentag, Saison, Kanal, Vorlauf-/Aufenthaltsklassen, Hund, Sprache, Stammgast, Buchungsmonat; Filter Nächte/Hund/Sprache). Jede Zelle mit Anzahl Buchungen `n` und Kennzeichen „wenig Daten“ (n < 5). `mode: "pace"` = Buchungstempo des Zieljahres gegen die Vorjahre am gleichen Tag und Prognose aus der Nachbuchung aller verfügbaren Vorjahre (Median, Spanne P10–P90). `mode: "meta"` = Liste der Kennzahlen und Dimensionen
- **Statistik-Werkbank, Teil 2 (neue Karte `custom:smoobu-stats-card`):** Kopf mit Aussage-Satz (Ergebnis ggü. Vergleich, Treiber Auslastung oder Preis je Nacht, größter Hebel in €); Filterleiste bleibt beim Scrollen stehen (Zeitraum Monat/Quartal/Saison/Jahr/frei mit ‹ ›, Vergleich Stichtag Vorjahr/ganzes Vorjahr/Vorperiode, Raster, Wohnung, Kanäle); Umschalter **Werkbank / Einfach** je Gerät (am Handy Standard Einfach). Modul 1 Kennzahlenleiste: Umsatz, Auslastung, ADR, RevPAR, Netto-RevPAR, Vorlauf (Median), Stornoquote mit Δ, Sparkline samt blasser Vergleichslinie und Anzahl Buchungen n; ein Klick macht die Kennzahl zur Fokus-Kennzahl mit großem Verlauf. Modul 2 Buchungstempo: Buchungsstand nach Buchungsdatum gegen die Vorjahre, Prognosekarte (wahrscheinlich, Spanne P10–P90, gebucht, erwartete Nachbuchung, Vorjahr am gleichen Tag, freie Nächte). Modul 3 Saison-Matrix Monate × Jahre (Auslastung/Umsatz/ADR/RevPAR/Netto) mit Ø nur abgeschlossener Monate, ohne 2020 (Option `matrix_exclude_years`). Werte mit weniger als 5 Buchungen werden als „wenig Daten“ gekennzeichnet; Tooltips beim Überfahren. Kopfleiste: Reiter „Statistik“ (`smoobu-statistik`) erscheint, sobald das Dashboard eine Ansicht mit diesem Pfad hat
- **`smoobu/stats`:** neuer Parameter `as_of` (Buchungsstand an einem Stichtag, für den Vergleich „Stichtag Vorjahr“)
- **Statistik-Werkbank, Teil 3–4:** sieben weitere Module – Belegung nach Wochentag (Heatmap Wochentag × Kalenderwoche, Auslastung je Wochentag), Kanal-Wirtschaftlichkeit (Netto + schraffierte Provision/Gebühren je Kanal, Kanal-Matrix Netto je Nacht × Anteil Nächte, Blase = Buchungen), Buchungsfenster & Aufenthalt (Histogramme mit Median), **verlorene Nächte** (freie Lücken zwischen zwei Belegungen bis 14 Nächte, bewertet mit Tagespreis bzw. – wo keiner gespeichert ist – Ø-Monatspreis „≈ geschätzt“, Hinweis bei Lücken unter dem Mindestaufenthalt mit Vorschlag zum Senken), Stornos (Quote je Kanal, Ausfall, Wiederbelegung, Storno-Vorlauf), Gäste (Personen, Hund, Stammgäste, Sprache), **Service** (Antwortzeit Median, Anteil unter 1 h, je Kanal, Verteilung) und Datentabelle aller Buchungen im Filter mit CSV-Export. **Baukasten „＋ Modul“:** eigene Module aus Kennzahl × Gruppierung × Aufteilung, Darstellung Balken/Linie/Heatmap/Tabelle/Kennzahl. **„Anordnen“:** Module verschieben, aus- und einblenden, eigene löschen – gespeichert je Gerät. Diagramme passen sich der tatsächlichen Breite an (am Handy lesbare Schrift)
- **Preis-Historie:** Die Integration merkt sich bei jedem Preisabruf Tagespreis und Mindestaufenthalt für heute und die kommenden Tage (Smoobu liefert sie nicht rückwirkend); Grundlage für die Bewertung verlorener Nächte
- **Antwortzeiten:** einmaliger, gedrosselter Hintergrundabruf der Nachrichten aller Buchungen ab „Daten abrufen seit“ (frühestens 10 Minuten nach dem Start, eine Anfrage je 1,5 s), danach stündlich nur neue und laufende Buchungen; Ergebnis dauerhaft gespeichert. Automatische Smoobu-Nachrichten an den Gast zählen als Antwort (Smoobu kennzeichnet sie nicht)
- **`smoobu/stats`:** neue Modi `gaps` (verlorene Nächte), `storno` und `service`

**English**
- **Mark payments as received in the dashboard:** "Waiting for you" (overview) now offers "✓ Received" for open payments and, if the prepayment is still open, "✓ Prepayment" (prepayment amount shown in the line); "Open booking" is a text link there. In the booking details the price section shows the balance and the buttons "✓ Prepayment received" / "✓ Payment received", plus "↶ Prepayment open" / "↶ Mark as open" to undo. Every change is confirmed first and saved straight to Smoobu via `smoobu.update_reservation`; "Payment received" also marks an open prepayment as paid
- **Mark portal bookings as received:** bookings via portals (Airbnb, Booking.com, HomeToGo, Expedia …) can now be marked as "received" too (e.g. once the invoice has been sent to the guest); the Smoobu "paid" status is used. Booking details: "✓ Payment received" or "↶ Mark as open"; without the mark the header shows a neutral "Paid via <channel>", afterwards "✓ paid". "Waiting for you": unmarked portal bookings appear from the arrival day on (up to 60 days back) as "Payment open" with the channel name, the gross amount muted and "✓ Received"; at most three, the rest as a "More not yet marked" line. Sensors and open payments in the backend are unchanged (collected by the portal)
- **Statistics workbench, part 1 (backend):** new WebSocket command `smoobu/stats` as the basis of the upcoming statistics page. `mode: "query"` = builder query measure × grouping × split (18 measures incl. ADR, RevPAR, net RevPAR, cancellation rate, median lead time/stay; 17 dimensions incl. weekday, season, channel, lead-time/stay classes, dog, language, repeat guest, booking month; filters nights/dog/language). Every cell carries the booking count `n` and a "low data" flag (n < 5). `mode: "pace"` = booking pace of the target year versus previous years on the same day, plus a forecast from the pick-up of all available previous years (median, P10–P90 range). `mode: "meta"` = list of measures and dimensions
- **Statistics workbench, part 2 (new card `custom:smoobu-stats-card`):** header sentence (result vs. comparison, driver occupancy or price per night, biggest lever in €); sticky filter bar (period month/quarter/season/year/custom with ‹ ›, comparison same day last year/full previous year/previous period, grid, apartment, channels); **Workbench / Simple** switch per device (simple by default on phones). Module 1 KPI bar: revenue, occupancy, ADR, RevPAR, net RevPAR, lead time (median), cancellation rate with Δ, sparkline with faded comparison line and booking count n; a click makes it the focus KPI with a large trend chart. Module 2 booking pace: booked revenue by booking date versus previous years, forecast card (likely, P10–P90 range, booked, expected pick-up, previous year on the same day, free nights). Module 3 season matrix months × years (occupancy/revenue/ADR/RevPAR/net) with an average over completed months only, excluding 2020 (option `matrix_exclude_years`). Values based on fewer than 5 bookings are flagged as "low data"; hover tooltips. Header card: tab "Statistik" (`smoobu-statistik`) appears as soon as the dashboard has a view with that path
- **`smoobu/stats`:** new parameter `as_of` (booking status on a given day, for the "same day last year" comparison)
- **Statistics workbench, parts 3–4:** seven more modules – occupancy by weekday (heatmap weekday × calendar week, occupancy per weekday), channel economics (net + hatched commission/fees per channel, channel matrix net per night × share of nights, bubble = bookings), booking window & length of stay (histograms with median), **lost nights** (free gaps between two stays up to 14 nights, valued at the daily rate or – where none was stored – the monthly average rate "≈ estimated", flag for gaps below the minimum stay with a suggestion to lower it), cancellations (rate per channel, lost revenue, re-booking, cancellation lead time), guests (party size, dog, repeat guests, language), **service** (median response time, share under 1 h, per channel, distribution) and a data table of all bookings in the filter with CSV export. **Builder "＋ Module":** custom modules from measure × grouping × split, shown as bars/line/heatmap/table/KPI. **"Arrange":** move, hide and show modules, delete custom ones – stored per device. Charts adapt to the actual width (readable text on phones)
- **Rate history:** on every rate fetch the integration stores the daily rate and minimum stay for today and the coming days (Smoobu does not provide them retroactively); basis for valuing lost nights
- **Response times:** one-off, throttled background fetch of the messages of all bookings since "load data since" (at the earliest 10 minutes after start-up, one request every 1.5 s), afterwards hourly only new and current bookings; result stored permanently. Automatic Smoobu messages to the guest count as a reply (Smoobu does not flag them)
- **`smoobu/stats`:** new modes `gaps` (lost nights), `storno` and `service`

## 1.17.0b3 – 2026-11-16

> Beta / Pre-release

**Deutsch**
- **Option „Auswertung: Daten abrufen seit“:** fester Startpunkt für Auswertungen und Vergleiche als Alternative zu „Jahre Historie“ (hat Vorrang; leer = Jahre gelten). Wird höchstens auf den 01.01. des Vorjahres gesetzt, damit Vorjahresvergleiche immer Daten haben
- **Absicherung Buchungsabruf:** Seitenlimit von 2.000 auf 10.000 Einträge je Abfrage angehoben; wird es trotzdem erreicht, steht eine Warnung im Log statt stillem Abschneiden
- **Datumsanzeige mit Jahr:** Buchungsliste (Anreise/Abreise), Buchungsdetails, Belegungsplan-Auswahl, freie Zeiträume und Status-Satz der Übersicht zeigen das Jahr jetzt zweistellig (z. B. „Di., 17.08.27“); Kopfzeile der Übersicht mit vollem Jahr; Zeitstempel von Nachrichten und Antwortvorschlägen ebenfalls mit Jahr. Achsenbeschriftungen der Tagesdiagramme bleiben kurz (Jahr im Tooltip)

**English**
- **Option "Analysis: load data since":** fixed start date for analyses and comparisons as an alternative to "Years of history" (takes precedence; empty = years apply). Never later than 1 January of the previous year, so year-on-year comparisons always have data
- **Booking fetch safeguard:** page limit raised from 2,000 to 10,000 entries per query; if it is still reached, a warning is logged instead of silently truncating
- **Dates with year:** booking list (arrival/departure), booking details, occupancy plan selection, free periods and the overview status sentence now show a two-digit year (e.g. "Tue, 17/08/27"); overview header with full year; message and reply suggestion timestamps include the year as well. Daily chart axis labels stay short (year in tooltip)

## 1.17.0b2 – 2026-11-16

> Beta / Pre-release

**Deutsch**
- **Aktion `smoobu.update_reservation`:** neue Felder `price_paid`, `prepayment_paid`, `deposit_paid` – Zahlungsstatus in Smoobu als bezahlt/offen setzen (Smoobu `priceStatus`/`prepaymentStatus`/`depositStatus`)

**English**
- **Action `smoobu.update_reservation`:** new fields `price_paid`, `prepayment_paid`, `deposit_paid` – set the payment status in Smoobu to paid/open

## 1.17.0b1 – 2026-11-16

> Beta / Pre-release

**Deutsch**
- Release-Ablauf: Änderungen werden auf `develop` gesammelt; Beta-Versionen als Pre-Release
- **Buchungsliste:** Standard-Sortierung jetzt Anreise **absteigend** (neueste zuerst); Datumsspalten starten beim Anklicken immer absteigend, übrige Spalten aufsteigend. Sortierbar nach jeder Spalte; Status in logischer Reihenfolge (laufend, kommend, vergangen, gesperrt, storniert), leere Werte immer am Ende, Gleichstand nach Anreise
- **Buchungsliste:** Trennung in **Anstehend / Aktuell / Vergangen** mit Trennzeile je Gruppe (Anzahl Buchungen und Nächte); Reihenfolge der Gruppen folgt der Datumsrichtung. CSV-Export übernimmt die angezeigte Reihenfolge
- **Finanzen – 8 neue Kacheln:** Erlös je verfügbare Nacht (netto ÷ nicht gesperrte Nächte), Freie Nächte (buchbar + Potenzial, vergangen + entgangen, je × Ø Netto/Nacht), Storno-Volumen, Offene Zahlungen (inkl. überfällig), Teuerstes/günstigstes Portal, Bester/schwächster Kanal je Nacht, Stammgäste (wiedererkannt an Smoobu-Gast-ID, E-Mail oder vollem Namen), Wochenende Fr/Sa mit Verteilung je Wochentag
- **Finanzen – Diagramm:** Legende mit Farbe, Kanal, Summe und Anteil (plus Vergleichslinie); Netto und Nächte jetzt ebenfalls je Kanal gestapelt; neue Ansicht **Provisionen** (Provision + Zahlungsgebühren je Portal und Monat, Ring mit Kostenverteilung und Kostenquote); Ring folgt der gewählten Kennzahl
- **Finanzen – Kanaltabelle:** neue Spalte **Provision & Gebühren** (€, Gebühren separat ausgewiesen, Aufteilung im Tooltip), bisherige Spalte „Kosten“ heißt jetzt „Kostenquote“
- **Finanzen – Mehrfachvergleich:** neben „Vergleich“ lässt sich die Anzahl der Vergleichszeiträume wählen (1–5 oder 10 Jahre bzw. Perioden; Standard 1 = wie bisher, Karten-Option `compare_count`). Ab 2 zeigt das Diagramm zusätzliche, mit dem Alter blasser werdende Vergleichslinien samt Legende, und die Tabelle „Mehrfachvergleich“ listet je Zeitraum Brutto, Δ zum nächstälteren Zeitraum, Netto, Provision & Gebühren, Kostenquote, Nächte, Auslastung, Netto/Nacht, Buchungen und Direktanteil. Kacheln und Veränderungen beziehen sich weiter auf den ersten Vergleichszeitraum; Zeiträume vor dem ältesten geladenen Datensatz erscheinen als „Keine Daten“ (Option „Historie (Jahre)“). WebSocket `smoobu/analytics`: neuer Parameter `compare_count`, Ergebnis `vergleiche`
- **Zähler „Nachrichten“ im Reiter aktualisiert sich sofort:** bei neuer Gastnachricht (Webhook), eigener Antwort, „Keine Antwort nötig“/Rückgängig – auch wenn die Änderung auf einem anderen Gerät passiert – und bei Rückkehr in die App. Vorher kam der Antwortstatus aus dem Seiten-Cache und blieb bis zum Neuladen stehen. Der Zähler zählt jetzt dieselben Gäste wie der Posteingang (inkl. kürzlich abgereister), beide zeigen dieselbe Zahl. Intern: `smoobu/subscribe` sendet bei geändertem Antwortstatus ein leichtes Ereignis `art: "nachrichten"` (kein Neuladen aller Karten)
- **Einstellungen – Benachrichtigungen (neuer Schritt):** je Push-Art an/aus und eigene Empfänger: Neue Buchung, Storno/Änderung (Vorher → Nachher), Neue Gästenachricht (wenn kein KI-Vorschlag kommt), KI-Antwortvorschlag, Zahlungserinnerung (X Tage vor und am Anreisetag, Uhrzeit), Tagesbriefing (Uhrzeit), Nicht buchbare Lücken (Uhrzeit, vorher fest 09:05). **Ruhezeit** (z. B. 21:00–07:00): nicht dringende Pushes werden gesammelt und zum Ende zugestellt (je Buchung nur der neueste Stand, übersteht Neustarts); dringende KI-Vorschläge, Bestätigungen und – wählbar – Gästenachrichten kommen sofort. Neue Buchungen/Stornos/Änderungen werden aus dem Datenabgleich erkannt (Webhook oder Abfrage), nur echte Neuanlagen der letzten 2 Tage. Bisherige Einstellungen gelten weiter (Empfänger, Tagesbriefing, Lücken); die Felder sind aus dem Schritt „KI-Assistent“ hierher umgezogen
- **Einstellungen – Wohnungskürzel (neuer Schritt):** eigenes Kürzel je Wohnung (bis 4 Zeichen, Prüfung auf Eindeutigkeit über alle Konten), leer = automatisch; wirkt im Dashboard und in Pushes ([Kürzel] bei mehreren Wohnungen)
- **Assistent – Vorschläge verwalten:** im Reiter „✨ Vorschläge“ lassen sich offene Vorschläge jetzt direkt bearbeiten und senden oder ignorieren, und jeder Vorschlag kann gelöscht werden (vorher nur Anzeige – ein Vorschlag ohne offene Gästenachricht, z. B. ein Testvorschlag, blieb hängen). WebSocket `smoobu/assistant/delete`: neue Arten `vorschlag` und `ignorieren`
- **Automatische Antwortvorschläge standardmäßig an:** Option ist neu vorausgewählt und gilt als an, solange sie nie gespeichert wurde – wirksam nur, wenn die KI erlaubt ist. Wer sie bewusst ausgeschaltet hat, behält „aus“. Hinweis: Installationen mit erlaubter KI, die die Option nie gespeichert haben, schicken neue Gästenachrichten damit automatisch an den KI-Anbieter
- **Wartezeit nach Check-out:** Standard jetzt **30 min** (vorher 0). Wer die Option nie gespeichert hat, bekommt die Freigabe dadurch 30 min später; eigene Einstellungen bleiben unverändert
- Intern: WebSocket `smoobu/analytics` liefert zusätzlich Reihen je Kanal für Netto/Nächte/Kosten und die neuen Kennzahlen; Sensor-Attribute bleiben unverändert

**English**
- Release process: changes are collected on `develop`; beta versions as pre-releases
- **Booking list:** default sort is now arrival **descending** (newest first); date columns always start descending when clicked, other columns ascending. Sortable by every column; status in logical order, empty values always last, ties by arrival
- **Booking list:** split into **Upcoming / Current / Past** with a separator row per group (bookings and nights); group order follows the date direction. CSV export keeps the displayed order
- **Finance – 8 new tiles:** revenue per available night, free nights (bookable + potential, past + lost), cancelled volume, open payments (incl. overdue), most expensive/cheapest portal, best/weakest channel per night, returning guests (guest ID, e-mail or full name), weekend Fri/Sat with per-weekday distribution
- **Finance – chart:** legend with colour, channel, total and share (plus comparison line); net and nights now stacked per channel too; new **Commissions** view (commission + payment fees per portal and month, donut with cost split and cost ratio)
- **Finance – channel table:** new **Commission & fees** column (€, fees shown separately); former "Costs" column is now "Cost ratio"
- **Finance – multi-period comparison:** next to "Comparison" you can choose the number of comparison periods (1–5 or 10 years/periods; default 1 = as before, card option `compare_count`). From 2 on the chart shows extra, increasingly faded comparison lines with legend and a "Multi-period comparison" table. Tiles and changes still refer to the first comparison period; periods before the oldest loaded record show "No data". WebSocket `smoobu/analytics`: new `compare_count` parameter, result `vergleiche`
- **"Messages" tab counter updates immediately:** on a new guest message (webhook), own reply, "No reply needed"/undo – also when done on another device – and when returning to the app. Previously the reply status came from the page cache until reload. The counter now counts the same guests as the inbox (incl. recently departed), so both show the same number. Internal: `smoobu/subscribe` sends a light `art: "nachrichten"` event when a reply status changes
- **Settings – notifications (new step):** per push type on/off and own recipients: new booking, cancellation/change (before → after), new guest message (when no AI suggestion is sent), AI reply suggestion, payment reminder (X days before and on arrival day, time), daily briefing (time), unbookable gaps (time, previously fixed 09:05). **Quiet hours**: non-urgent pushes are collected and delivered at the end (latest state per booking, survives restarts); urgent AI suggestions, confirmations and – optionally – guest messages arrive immediately. Existing settings keep working; the fields moved here from the "AI assistant" step
- **Settings – property codes (new step):** own code per property (up to 4 characters, unique across accounts), empty = automatic; used in dashboard and pushes
- **Assistant – manage suggestions:** in the "✨ Suggestions" tab open suggestions can now be edited and sent or ignored directly, and any suggestion can be deleted (previously display only – a suggestion without an open guest message, e.g. a test suggestion, got stuck). WebSocket `smoobu/assistant/delete`: new kinds `vorschlag` and `ignorieren`
- **Automatic reply suggestions on by default:** preselected and treated as on as long as never saved – only effective when AI is allowed. A saved "off" is kept. Note: installations with AI allowed that never saved the option will now send new guest messages to the AI provider automatically
- **Waiting time after check-out:** default is now **30 min** (was 0). Installations that never saved this option get the release 30 min later; saved settings are kept
- Internal: `smoobu/analytics` additionally returns per-channel series for net/nights/costs and the new figures; sensor attributes unchanged

## 1.16.0 – 2026-11-16

**Deutsch**
- **Buchungsdetails:** Im Nachrichtenbereich gibt es jetzt wie im Posteingang **„✨ Vorschlag“** (KI-Antwortvorschlag mit Anlass-Auswahl, offener automatischer Vorschlag wird vorbefüllt) und **„✓ Keine Antwort nötig“** inkl. Status „Antwort offen“ / „Ohne Antwort erledigt“ und Rückgängig. Bei gesperrter KI ausgegraut (🔒)
- Senden aus den Buchungsdetails prüft wie der Posteingang auf nicht ergänzte Stellen `[OFFEN: …]`; der Entwurf bleibt beim Neuzeichnen erhalten
- Intern: Antwortstatus- und KI-Bausteine von Posteingang und Buchungsdetails gemeinsam genutzt

**English**
- **Booking details:** the messages section now offers, like the inbox, **"✨ Suggestion"** (AI reply suggestion with occasion selector, an open automatic suggestion is prefilled) and **"✓ No reply needed"** incl. status "Reply pending" / "Done without reply" and undo. Greyed out (🔒) when AI is locked
- Sending from booking details checks for unfilled `[OFFEN: …]` placeholders like the inbox; the draft survives re-rendering
- Internal: reply-status and AI building blocks shared between inbox and booking details

## 1.15.3 – 2026-11-15

**Deutsch**
- **Hunde-Erkennung verbessert:** Airbnb liefert die Haustiergebühr als `PASS_THROUGH_PET_FEE` – das wurde bisher nicht erkannt (Unterstrich galt als Teil des Wortes). Jetzt zählen Preiselemente mit Betrag ≠ 0, die Preisdetails der Portale, Notizen und **Nachrichten des Gastes** (nur Nachrichten VOM Gast; laufende und kommende Buchungen der nächsten 180 Tage, höchstens 12 Abrufe je Aktualisierung, 12 h zwischengespeichert, neue Nachricht per Webhook prüft neu). Verneinungen („ohne Hund“, „no pets“) zählen nicht; zusätzliche Wörter: Hundes, Welpen, petfee, hond, cane, perro
- Fundstelle bleibt im Attribut `hund_hinweis` sichtbar (z. B. „Zusatzleistung: Pass Through Pet Fee“, „Gastnachricht: …“)

**English**
- **Better dog detection:** Airbnb sends the pet fee as `PASS_THROUGH_PET_FEE`, which was not recognised. Price elements with an amount ≠ 0, portal price details, notes and **guest messages** (only messages FROM the guest; current and upcoming bookings within 180 days, at most 12 requests per update, cached 12 h, re-checked on a new-message webhook) now count. Negations ("without dog", "no pets") are ignored

## 1.15.2 – 2026-11-15

**Deutsch**
- Übersicht: Jede Kennzahl-Grafik zeigt zusätzlich eine **blasse Vergleichslinie** (Vorjahr): Monat brutto, Auslastung, Netto je Nacht und Direktanteil je Monat der letzten 12 Monate gegen dieselben Monate im Vorjahr; „Jahr bis heute“ kumuliert gegen den gleichen Zeitraum im Vorjahr; „Prognose“ gegen den kumulierten Verlauf des ganzen Vorjahres. Gemeinsame Skala, Erklärung in der Fußzeile

**English**
- Overview: every key-figure chart now shows a **faint comparison line** (previous year) on a shared scale; "year to date" against the same period last year, "forecast" against the whole previous year

## 1.15.1 – 2026-11-15

**Deutsch**
- Karten in Panel-Ansichten bekommen einen eigenen Seitenrand (vorher lagen Text und Rahmen direkt am Fensterrand)

**English**
- Cards in panel views get their own side margin (text and borders previously touched the window edge)

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

/*
 * Smoobu-Karten für Home Assistant (ab v1.8.0)
 * ============================================
 * Wird von der Integration automatisch geladen (frontend.py). Keine externen
 * Abhängigkeiten, kein Build-Schritt: reine Web Components mit Shadow DOM,
 * Farben aus dem HA-Theme (CSS-Variablen), Diagramme als eigenes SVG.
 *
 * Karten (im Karten-Auswahldialog unter „Smoobu …“):
 *   custom:smoobu-overview-card   Heute: Status, An-/Abreisen, Kennzahlen, Lücken, offene Zahlungen
 *   custom:smoobu-timeline-card   Belegungsplan mit Preisen, Mindestaufenthalt, Lücken; Bereich
 *                                 markieren → sperren oder Preise setzen
 *   custom:smoobu-bookings-card   Buchungsliste: Suche, Filter, Sortierung, Summen, CSV-Export
 *   custom:smoobu-analytics-card  Finanzen & Kanäle: frei filterbar, Vergleich, Diagramm, Prognose
 *   custom:smoobu-stats-card      Statistik-Werkbank: Kennzahlenleiste, Buchungstempo/Prognose, Saison-Matrix
 *   custom:smoobu-inbox-card      Nachrichten der laufenden/kommenden Buchungen, antworten
 * Ein Klick auf eine Buchung öffnet überall dieselbe Detailansicht
 * (Gast, Preis, Kosten, Notiz, Zeiten ändern, Nachrichten, Sperre löschen).
 *
 * Datenquelle: WebSocket-Befehle smoobu/* (websocket_api.py), Aktionen über
 * die Smoobu-Aktionen (smoobu.block_period, set_rates, …).
 * Sicherheit: Alle Texte aus Smoobu (Namen, Nachrichten, Notizen) werden vor
 * der Ausgabe maskiert (esc), damit kein fremdes HTML ausgeführt wird.
 */

const SMOOBU_CARDS_VERSION = "1.18.0b1";

// ---------------------------------------------------------------------------
// Texte (Deutsch; Englisch für HA-Oberflächen in anderer Sprache)
// ---------------------------------------------------------------------------
const EN = {
  // v1.18.0: Kosten & Preise, Bewertung & Empfehlung
  "Übernehmen …": "Apply …", "Preis anpassen …": "Adjust price …", "Preis anpassen": "Adjust price", "Übernehmen": "Apply", "Vorschau": "Preview",
  "Neuer Basispreis je Nacht": "New base price per night", "Änderung zum bisherigen Tagespreis": "Change to the current daily price",
  "unverändert": "unchanged", "Bis (inklusive)": "To (inclusive)", "Feiertagsnächte auslassen": "Skip holiday nights",
  "Tage mit eigenem Preis nicht überschreiben": "Don't overwrite days with their own price", "Letzte Preisänderungen": "Recent price changes",
  "rückgängig gemacht": "undone", "Benutzer & Rechte": "Users & permissions", "Deine Rolle": "Your role",
  "Rollen der Benutzer": "User roles", "Standardrolle": "Default role", "Was darf welche Rolle?": "What can each role do?",
  "Recht": "Permission", "Verwalter": "Manager", "Betrieb": "Operations", "Mitarbeiter": "Staff", "Nur lesen": "Read only",
  "Kein Zugriff": "No access", "Tage übernommen und in Smoobu geprüft": "days applied and verified in Smoobu",
  "Tage zurückgesetzt": "days reset", "Keine Änderung nötig": "No change needed", "ausgelassen": "skipped",
  "Feiertag": "holiday", "eigener Preis": "own price", "Last-Minute": "Last minute", "Fenster": "Window", "max. Rabatt": "max. discount",
  "kein Rabatt empfohlen": "no discount recommended", "Smoobu liefert": "Smoobu provides", "teilweise": "partly",
  "Wert hier wird genutzt": "value here is used", "Genius-Check": "Genius check", "Gemessenen Anteil übernehmen": "Use measured share",
  "passt zur Einstellung": "matches the setting", "Rechnungen": "Invoices",
  "Erledigt": "Done", "Später": "Later", "Morgen wieder da": "Back tomorrow", "weitere": "more", "erledigt bzw. später – ausgeblendet": "done or later – hidden",
  "Als erledigt ausblenden": "Hide as done", "Morgen wieder zeigen": "Show again tomorrow", "Preis senken": "Lower price", "Preis erhöhen": "Raise price",
  "Aufgaben-Board „Wartet auf dich“": "Task board \"Waiting for you\"", "Anpassen …": "Adjust …", "übernehmen": "apply", "Direktkanal": "direct channel", "keine Buchungen": "no bookings",
  "Provision von Smoobu (24 Monate)": "Commission from Smoobu (24 months)", "Weitere Kanäle mit Buchungen": "Other channels with bookings", "auf die freien Nächte": "on the free nights", "Lücke": "Gap", "Kanalpreise bei": "Channel prices at",
  "Kosten & Preise": "Costs & prices", "Bewertung & Empfehlung": "Assessment & recommendation", "Basispreis heute": "Base price today",
  "Basispreis": "Base price", "netto je Nacht": "net per night", "Schwach": "Weak", "Normal": "Normal", "Stark": "Strong",
  "Zu wenig Daten": "Not enough data", "↓ Preis senken": "↓ Lower price", "↑ Preis erhöhen": "↑ Raise price", "→ Preis halten": "→ Keep price",
  "auf": "to", "Untergrenze": "Floor", "teuerster Kanal": "most expensive channel", "Untergrenze je Kanal": "Floor per channel",
  "Variable Kosten je Nacht": "Variable costs per night", "Heizung": "Heating", "Warmwasser": "Hot water", "Strom": "Electricity",
  "Wasser": "Water", "je Aufenthalt": "per stay", "Nächte frei": "nights free", "Hinweise": "Notes",
  "Vorjahre": "Previous years", "Vorjahre am gleichen Tag": "Previous years on the same day",   "In den Vorjahren belegt": "Booked in previous years", "so nicht buchbar": "not bookable this way",   "Aufschlag": "Markup", "Netto je € Basispreis": "Net per € base price", "gemessen": "measured",
  "Option": "option", "direkt": "direct", "gleich an allen": "same on all",   "der Nächte werden im selben oder im Vormonat gebucht": "of nights are booked in the same or the previous month",
  "Buchungsstand gegen die Vorjahre am gleichen Tag · Preisuntergrenzen aus den variablen Kosten": "Bookings on hand vs. previous years on the same day · price floors from variable costs",
  "Je Aufenthalt": "Per stay", "Wäsche": "Laundry", "Heizung & Warmwasser": "Heating & hot water",
  "Heizkosten im Abrechnungsjahr": "Heating costs in billing year", "Warmwasser im Abrechnungsjahr": "Hot water in billing year",
  "Abrechnungsjahr": "Billing year", "Wasser & Strom je Nacht": "Water & electricity per night", "Wasser/Abwasser": "Water/sewage",
  "Netzstrompreis": "Grid price", "Wert PV-Strom": "Value of PV power", "Netzanteil je Monat": "Grid share per month",
  "Aufschläge je Kanal": "Markups per channel", "Booking.com Genius-Rabatt": "Booking.com Genius discount",
  "Anteil Genius-Buchungen": "Share of Genius bookings", "Kosten je Nacht relativ zum Januar": "Cost per night relative to January",
  "Datenschutz": "Privacy", "Standard (empfohlen)": "Standard (recommended)", "Streng": "Strict", "Maximal": "Maximum",
  "Individuell": "Custom", "Einbuße": "Loss", "keine": "none", "gering": "small", "mittel": "medium", "hoch": "high",
  "Letzte KI-Anfrage": "Last AI request", "Probelauf nächste Buchung": "Dry run next booking", "Was geht an die KI?": "What goes to the AI?",
  "Eigene Namen": "Own names", "Nachrichten aus dem Verlauf": "Messages from the history",
  "Einstellungen": "Settings", "Benachrichtigungen": "Notifications", "KI-Assistent": "AI assistant",
  "Provisionen & Kanäle": "Commissions & channels", "Allgemein & Abruf": "General & polling", "Speichern": "Save",
  // v1.18.0: Ruhezeit je Push-Art
  "Hält Ruhezeit ein": "Respects quiet hours", "Wird in der Ruhezeit gesammelt und zum Ende zugestellt.": "Held during quiet hours and delivered when they end.",
  "Kommt auch in der Ruhezeit sofort.": "Arrives immediately, even during quiet hours.", "Ruhezeit ist aus – wirkt erst, wenn sie eingeschaltet ist.": "Quiet hours are off – takes effect once they are on.",
  "Warten in der Ruhezeit": "Held during quiet hours", "keine – alle kommen sofort": "none – all arrive immediately",
  "Einstellbar je Push-Art („Hält Ruhezeit ein“). Dringende Vorschläge und Bestätigungen kommen immer sofort.": "Set per push type (\"Respects quiet hours\"). Urgent suggestions and confirmations always arrive immediately.",
  "Pushes mit „Hält Ruhezeit ein“ werden gesammelt und zum Ende der Ruhezeit zugestellt.": "Pushes with \"Respects quiet hours\" are collected and delivered when quiet hours end.",
  // v1.18.0: Kanal-Dropdown in den Einstellungen
  "Kanal hinzufügen": "Add channel", "＋ Kanal hinzufügen …": "＋ Add channel …", "＋ Weiteren Kanal wählen …": "＋ Choose another channel …",
  "Kanäle mit Buchungen": "Channels with bookings", "In den Einstellungen genutzt": "Used in the settings",
  "Weitere Smoobu-Kanäle": "Other Smoobu channels", "In die Tabelle übernehmen": "Add to the table", "Buchung": "Booking",
  "Verwerfen": "Discard", "Alles gespeichert.": "All saved.", "ungespeicherte Änderung": "unsaved change",
  "ungespeicherte Änderungen": "unsaved changes", "Empfänger": "Recipients", "Uhrzeit": "Time", "Ruhezeit": "Quiet hours",
  "Einstellungen gespeichert.": "Settings saved.", "Bitte die markierten Felder prüfen.": "Please check the marked fields.",
  "Keine Berechtigung für die Smoobu-Einstellungen.": "No permission for the Smoobu settings.",
  "Speichere … die Integration lädt danach neu.": "Saving … the integration reloads afterwards.",
  "Übersicht": "Overview", "Belegt": "Occupied", "Frei": "Vacant", "frei ab": "free from",
  "Anreise heute": "Arrival today", "Abreise heute": "Departure today", "Gästewechsel heute": "Changeover today",
  "Reinigung heute": "Cleaning today", "Buchungsstand Vorjahr": "Previous year booking status",
  "Vergleich": "Comparison", "Monat ggü. Buchungsstand am": "Month vs. booking status on", "Jahr ggü.": "Year vs.",
  "PP = Prozentpunkte": "PP = percentage points",
  "Aktueller Gast": "Current guest", "Nächster Gast": "Next guest", "Nächste Anreisen": "Upcoming arrivals",
  "Lücken": "Gaps", "Offene Zahlungen": "Open payments", "keine": "none", "Nächte": "nights",
  "Nacht": "night", "Personen": "guests", "Brutto": "Gross", "Netto": "Net", "Kosten": "Costs",
  "Auslastung": "Occupancy", "Buchungen": "Bookings", "Stornos": "Cancellations", "Stornoquote": "Cancellation rate",
  "Ø Aufenthalt": "Avg. stay", "Ø Vorlauf": "Avg. lead time", "Ø Personen": "Avg. guests", "Direktanteil": "Direct share",
  "Prognose Jahr": "Forecast year", "Netto/Nacht": "Net/night", "Brutto/Nacht": "Gross/night", "Tage": "days",
  "Monat": "Month", "Jahr bis heute": "Year to date", "Kanal": "Channel", "Kanäle": "Channels", "Zeitraum": "Period",
  "Vergleich": "Comparison", "Alle": "All", "Direkt": "Direct", "Portale": "Portals", "Suche": "Search",
  "Provisionen": "Commissions", "Provision & Gebühren": "Commission & fees", "Kostenquote": "Cost ratio",
  "Zahlungsgebühren": "Payment fees", "davon Gebühren": "incl. fees",
  "Erlös je verfügbare Nacht": "Revenue per available night", "verfügbar": "available", "Freie Nächte": "Free nights",
  "Potenzial": "Potential", "buchbar": "bookable", "entgangen": "lost", "Storno-Volumen": "Cancelled volume", "überfällig": "overdue",
  "Teuerstes Portal": "Most expensive portal", "günstigstes": "cheapest", "Bester Kanal je Nacht": "Best channel per night",
  "schwächster": "weakest", "Stammgäste": "Returning guests", "Wochenende Fr/Sa": "Weekend Fri/Sat",
  "So–Do": "Sun–Thu", "Mo": "Mo", "Di": "Tu", "Mi": "We", "Do": "Th", "Fr": "Fr", "Sa": "Sa", "So": "Su",
  "Anzahl Vergleichszeiträume": "Number of comparison periods", "Periode": "period", "Perioden": "periods",
  "Jahr": "year", "Jahre": "years", "Mehrfachvergleich": "Multi-period comparison", "Stand": "as of",
  "Keine Daten – Historie in den Integrationsoptionen erhöhen": "No data – increase history in the integration options",
  "Veränderung zum nächstälteren Zeitraum": "Change vs. the next older period",
  "Bearbeiten & senden": "Edit & send", "Vorschlag löschen": "Delete suggestion", "Löschen": "Delete",
  "Anstehend": "Upcoming", "Aktuell": "Current", "Vergangen": "Past",
  "Status": "Status", "kommend": "upcoming", "laufend": "current", "vergangen": "past", "storniert": "cancelled",
  "blockiert": "blocked", "Anreise": "Arrival", "Abreise": "Departure", "Gast": "Guest", "Offen": "Open",
  "Summe": "Total", "Export CSV": "Export CSV", "Belegungsplan": "Occupancy plan", "Preise": "Prices",
  "Mindestaufenthalt": "Minimum stay", "Sperren": "Block", "Preis setzen": "Set price", "Abbrechen": "Cancel",
  "Speichern": "Save", "Auswahl": "Selection", "Sperre löschen": "Delete block", "Stornieren": "Cancel booking",
  "Nachrichten": "Messages", "Antworten": "Reply", "Senden": "Send", "Notiz": "Note", "Preis": "Price",
  "Provision": "Commission", "Zahlungsgebühr": "Payment fee", "bezahlt": "paid", "Anzahlung": "Prepayment",
  "Kurtaxe": "City tax", "Positionen": "Line items", "Ankunftszeit": "Arrival time", "Abreisezeit": "Departure time",
  "Laden …": "Loading …", "Keine Daten": "No data", "Vorjahr": "Previous year", "Vorperiode": "Previous period",
  "Kein Vergleich": "No comparison", "Laufender Monat": "Current month", "Vormonat": "Previous month",
  "Folgemonat": "Next month", "Laufendes Jahr": "Current year", "Letzte 12 Monate": "Last 12 months",
  "Nächste 12 Monate": "Next 12 months", "Gesamter Zeitraum": "All data", "Benutzerdefiniert": "Custom",
  "von": "from", "bis": "to", "Hund": "Dog", "Posteingang": "Inbox", "Antwort offen": "Reply pending", "warten auf Antwort": "awaiting reply", "Finanzen": "Finance",
  "Erkenntnisse": "Insights", "Anteil": "Share", "nicht buchbar": "not bookable", "Mindestaufenthalt zu hoch": "minimum stay too long",
  "Vorlauf": "Lead time", "Erstellt": "Created", "Sprache": "Language", "Telefon": "Phone", "E-Mail": "Email",
  "Gespeichert": "Saved", "Fehler": "Error", "Wirklich?": "Are you sure?", "Ja": "Yes", "Nein": "No",
  "an den Gast": "to guest", "Gesendet": "Sent", "Aktualisiert": "Updated", "Nachbuchung wie Vorjahr": "Pickup like last year",
  "gebucht": "booked", "Gesperrt": "Blocked", "Monate": "months", "Diagramm": "Chart", "Sperrzeit": "Block",
  "Preis/Nacht": "Price/night", "Ersparnis Direkt": "Direct savings", "Kanaltabelle": "Channel table",
  "Neu laden": "Reload", "morgen": "tomorrow", "Heute abgereist": "Departed today", "Heute": "Today", "Ankunft": "Check-in", "Abfahrt": "Check-out", "Gäste": "Guests",
  "Details": "Details", "In Smoobu öffnen": "Open in Smoobu", "Smoobu öffnen": "Open Smoobu", "Kommunikationsaufwand je Kanal": "Communication effort per channel",
  "Anliegen je Buchung": "Requests per booking", "Gastnachrichten je Buchung": "Guest messages per booking",
  "Buchungen mit Nachricht": "Bookings with message", "Alle Kanäle": "All channels", "Anliegen": "Request",
  "Am meisten Kommunikation": "Most communication", "Ø aller Kanäle": "avg. of all channels",
  "Gastnachrichten bis zur nächsten Antwort, mehrere am Stück zählen einmal": "guest messages until the next reply, several in a row count once",
  "Anliegen je Buchung im Verhältnis zum Ø aller Kanäle (100 = Durchschnitt, 150 = 1,5-fach)": "requests per booking relative to the average of all channels (100 = average, 150 = 1.5×)",
  "ausgewertete Buchungen mit Anreise im Zeitraum": "evaluated bookings arriving in the period",
  "Nur Nachrichten, die über Smoobu laufen; eigene und automatische Nachrichten zählen nicht; Buchungen ganz ohne Verlauf (bei Smoobu oft vor 2024) fehlen": "Only messages that go through Smoobu; own and automatic messages are not counted; bookings without any message history (often before 2024 at Smoobu) are left out", "Zurück zu": "Back to", "Anpassen": "Adjust",
  "Im Belegungsplan Mindestaufenthalt oder Preis setzen": "Set minimum stay or price in the occupancy plan",
  "Smoobu-Anmeldung öffnen – Buchung dort über die ID suchen": "Opens the Smoobu login – search the booking there by ID",
  "in Smoobu speichern": "save in Smoobu", "Nicht als erhalten markiert": "Not marked as received", "DRINGEND": "URGENT",
  "Antwort": "Reply", "Willkommen": "Welcome", "Anreisetag": "Arrival day", "Abreisetag": "Departure day", "Bitte um Bewertung": "Review request",
  "aus dem Verlauf": "from history", "aus Smoobu-Vorlage": "from Smoobu template", "gesendet": "sent", "KI-Vorschlag": "AI suggestion",
  "bearbeitet": "edited", "Wissenslücke": "knowledge gap", "manuell": "manual", "aktiv": "active", "zur Freigabe": "awaiting approval",
  "ausgeschaltet": "off", "ignoriert": "ignored", "keine KI": "no AI",
  "Frage": "Question", "Späte Anreise": "Late arrival", "Früher Check-in": "Early check-in", "Später Check-out": "Late check-out",
  "Problem": "Problem", "Dank": "Thanks", "Buchungsanfrage": "Booking request", "Stornierung": "Cancellation", "Sonstiges": "Other", "Grund (optional)": "Reason (optional)",
  "Tage markieren: erst ersten, dann letzten Tag antippen": "Mark days: tap first day, then last day",
  // v1.14.0
  "Keine Antwort nötig": "No reply needed", "Ohne Antwort erledigt": "Done without reply", "Rückgängig": "Undo",
  "KI gesperrt": "AI locked", "KI in den Integrationsoptionen deaktiviert": "AI disabled in the integration options",
  "Vorschlag": "Suggestion", "Vom Gast": "From guest", "An den Gast": "To guest", "KI denkt …": "AI thinking …",
  // v1.15.0
  "Alle Wohnungen": "All properties", "Wohnung": "Property", "Gästewechsel": "Changeover", "Abreise heute": "Departure today",
  "Belegt bis": "Occupied until", "Frei bis": "Vacant until", "Abreise bis": "Check-out by", "Bezahlt über": "Paid via",
  "Hund dabei": "Dog included", "Person": "guest", "Tagen": "days", "Die nächsten": "Next", "Wochen": "weeks", "brutto": "gross",
  "ggü. Buchungsstand": "vs. booking status", "Nächten": "nights", "netto": "net", "Prognose": "Forecast", "schon gebucht": "already booked",
  "Netto je Nacht": "Net per night", "spart rund": "saves about", "Anteil am Umsatz": "Share of revenue", "Freie Zeiträume": "Free periods",
  "nächste": "next", "Wartet auf dich": "Waiting for you", "wartet auf Antwort": "awaits reply", "Zahlung offen": "Payment open",
  "Buchung öffnen": "Open booking", "Alles erledigt.": "All done.", "Keine Anreisen geplant.": "No arrivals planned.", "Keine Lücken.": "No gaps.",
  "Reinigung": "Cleaning", "ab": "from", "Heute keine An- oder Abreise": "No arrival or departure today", "Nachricht": "message",
  "unbeantwortet": "unanswered", "gerade eben": "just now", "Reist heute ab": "Leaves today", "Wohnungen im Vergleich": "Properties compared",
  "Darstellung": "Appearance", "Hell": "Light", "Dunkel": "Dark", "System": "System", "Belegung": "Occupancy", "Kalender": "Calendar", "Assistent": "Assistant",
  "Zurück": "Back", "Weiter": "Next", "Zahl unten = Preis/Nacht": "Number below = price/night",
  "Keine Buchung in den nächsten 6 Monaten.": "No booking in the next 6 months.", "Danach keine Buchung in den nächsten 6 Monaten.": "No booking afterwards in the next 6 months.",
  "gebucht + Nachbuchungen wie im Vorjahr": "booked + pickup like last year", "Nachrichten": "Messages",
  // v1.17.0: Zahlungseingang markieren
  "Zahlung erhalten": "Payment received", "Anzahlung erhalten": "Prepayment received", "Erhalten": "Received",
  "Als offen markieren": "Mark as open", "Anzahlung offen": "Prepayment open", "Restbetrag": "Balance",
  "Zahlung": "Payment", "als erhalten markieren": "mark as received", "wieder als offen markieren": "mark as open again",
  "In Smoobu gespeichert": "Saved in Smoobu", "offen": "open",
  // v1.17.0: Portal-Buchungen als erhalten markieren
  "über": "via", "Portal": "Portal", "Weitere ohne Markierung": "More not yet marked",
  // Statistik-Werkbank (Teilschritt 2)
  "Statistik": "Statistics", "Werkbank": "Workbench", "Einfach": "Simple", "Quartal": "Quarter", "Saison": "Season",
  "Raster": "Grid", "Woche": "Week", "Tag": "Day", "Schnellwahl": "Quick select", "Stichtag Vorjahr": "Same day last year", "Ganzes Vorjahr": "Full previous year",
  "Buchungstempo": "Booking pace", "Saison-Matrix": "Season matrix", "Prognose": "Forecast", "Spanne": "Range",
  "wahrscheinlich": "likely", "wenig Daten": "low data", "Treiber": "Driver", "Größter Hebel": "Biggest lever", "gesperrt": "blocked",
  "Vorlauf": "Lead time", "Umsatz": "Revenue", "Verlauf": "Trend",
  // v1.18.0b7: Endstand neben dem Stichtag-Vergleich
  "Anteil der Buchungen (Anreise im Zeitraum) und der Nächte im Zeitraum": "Share of bookings (arrival in period) and of nights in period",
  // v1.18.0b7: Ehrentafel
  "Ehrentafel": "Hall of fame",
  "Nur zum Spaß – keine Gästebewertung": "Just for fun – not a guest rating",
  "Die Goldene Fußmatte": "The Golden Doormat",
  "Die Rostige Klobürste": "The Rusty Toilet Brush",
  "Gäste, die man gern wieder sieht": "Guests you'd love to see again",
  "Wanderpokal für besonderen Einsatz": "Challenge trophy for special effort",
  "netto/Nacht": "net/night",
  "je Nacht": "per night",
  "Abzug": "deducted",
  "Ruhe": "Calm",
  "Pünktlichkeit": "Punctuality",
  "Extra-Stunden": "Extra hours",
  "Billigpreis": "Bargain price",
  "Gesprächigkeit": "Chattiness",
  "Kurzaufenthalt": "Short stay",
  "Portal-Abzug": "Portal deduction",
  "Zahlt": "Pays",
  "Respekt": "respect",
  "Schweigsam wie ein Mönch: 0 Anliegen": "Silent as a monk: 0 requests",
  "Pflegeleicht": "Low-maintenance",
  "Pünktlich wie ein Schweizer Uhrwerk": "Punctual like Swiss clockwork",
  "Fast pünktlich": "Almost on time",
  "Plant voraus": "Plans ahead",
  "Tage vorher gebucht": "days in advance",
  "Frühaufsteher und Langschläfer": "Early bird and late riser",
  "Frühaufsteher": "Early bird",
  "Langschläfer": "Late riser",
  "Check-in": "Check-in",
  "Check-out": "Check-out",
  "Schnäppchenjäger": "Bargain hunter",
  "Brieffreund": "Pen pal",
  "Eine Nacht, volle Reinigung": "One night, full cleaning",
  "Kurz und schmutzig": "Short and messy",
  "Das Portal isst mit": "The portal eats along",
  "weg": "gone",
  "Stammgast – gehört fast zur Familie": "Regular – practically family",
  "Punkte": "Points",
  "inkl. Stammgast-Bonus": "incl. regular bonus",
  "keine Daten (neutral)": "no data (neutral)",
  "Pkt.": "pts",
  "Keine abgeschlossenen Aufenthalte im Zeitraum": "No completed stays in this period",
  "Gewertet": "Rated",
  "Aufenthalte mit Abreise im Zeitraum": "stays departing in the period",
  "Uhrzeit bekannt": "time known",
  "Nachrichten geladen": "messages loaded",
  "Standard": "Default",
  "Zu wenig Gäste für eine faire Wertung": "Too few guests for a fair ranking",
  "Zeitraum vergrößern": "widen the period",
  "Stand": "as of", "Endstand": "Final", "Endstand Vergleichszeitraum": "Final value of comparison period",
  "Pfeil und Farbe vergleichen mit dem Stand am Stichtag, nicht mit dem Endstand.": "Arrow and colour compare with the status on the reference day, not with the final value.",
};
let LANG = "de";
const t = (s) => (LANG === "de" ? s : EN[s] || s);
// v1.17.1: Anzeigenamen statt Smoobu-/Programmschlüsseln (nur Anzeige – Filter, Farben und Sensoren
// arbeiten weiter mit den Originalnamen aus Smoobu, z. B. „Direct booking“)
const CH_DE = { "Direct booking": "Direktbuchung", "Blocked channel": "Sperre", "Blocked channel auto": "Sperre (automatisch)" };
const chn = (name) => (LANG === "de" && CH_DE[name]) || name || "";
// Preiselemente: Smoobu liefert Standardnamen englisch; eigene Zusatzleistungen behalten ihren Namen
const PRICE_DE = { basePrice: ["Base price", "Grundpreis"], cleaningFee: ["Cleaning fee", "Endreinigung"],
  longStayDiscount: ["Long stay discount", "Langzeitrabatt"], extraGuestFee: ["Extra guest fee", "Zusatzgast"],
  discount: ["Discount", "Rabatt"], cityTax: ["City tax", "Kurtaxe"] };
const priceName = (p) => { const m = PRICE_DE[p.typ]; return LANG === "de" && m && (!p.name || p.name === m[0]) ? m[1] : p.name || p.typ || ""; };
// v1.17.1: Abkürzungen kurz erklärt – als Legendenzeile unter Kennzahlen/Diagrammen (gloss([...]))
const GLOSSARY = {
  ADR: "Ø Preis je belegter Nacht (brutto)",
  RevPAR: "Umsatz je verfügbarer Nacht = ADR × Auslastung",
  "Netto-RevPAR": "Netto (nach Provision und Gebühren) je verfügbarer Nacht",
  DB: "Deckungsbeitrag = Netto − variable Kosten (Reinigung, Wäsche, Heizung, Warmwasser, Wasser, Strom)",
  "DB-RevPAR": "Deckungsbeitrag je verfügbarer Nacht",
  Untergrenze: "Basispreis, ab dem eine Buchung über diesen Kanal noch einen positiven Deckungsbeitrag bringt",
  PP: "Prozentpunkte – Veränderung einer Quote",
  n: "Anzahl Buchungen, auf denen der Wert beruht",
  "Vgl.": "Vergleichszeitraum",
  "Ø": "Durchschnitt",
  N: "Nächte",
  "Δ": "Veränderung zum Vergleich",
  Pace: "Buchungstempo: Buchungsstand am gleichen Tag vor dem Aufenthalt",
  "P10–P90": "Spanne, in der 80 % der Vorjahres-Nachbuchungen lagen",
  KW: "Kalenderwoche",
};
const GLOSSARY_EN = {
  ADR: "average price per occupied night (gross)", RevPAR: "revenue per available night = ADR × occupancy",
  "Netto-RevPAR": "net (after commission and fees) per available night", PP: "percentage points – change of a rate",
  n: "number of bookings the value is based on", "Vgl.": "comparison period", "Ø": "average", N: "nights",
  "Δ": "change vs. comparison", Pace: "booking pace: bookings on hand the same day before the stay",
  "P10–P90": "range covering 80 % of prior years' late bookings", KW: "calendar week",
};
const gloss = (keys) => `<div class="legend gloss">${keys.filter((k) => GLOSSARY[k]).map((k) =>
  `<span><b>${esc(k)}</b> = ${esc(LANG === "de" ? GLOSSARY[k] : GLOSSARY_EN[k])}</span>`).join("")}</div>`;
const OCCASION_LABEL = { antwort: "Antwort", willkommen: "Willkommen", anreise: "Anreisetag", abreise: "Abreisetag", bewertung: "Bitte um Bewertung" };
const SOURCE_LABEL = { verlauf: "aus dem Verlauf", smoobu: "aus Smoobu-Vorlage", gesendet: "gesendet", vorschlag: "KI-Vorschlag",
  bearbeitet: "bearbeitet", wissensluecke: "Wissenslücke", manuell: "manuell" };
const KSTATUS_LABEL = { aktiv: "aktiv", vorschlag: "zur Freigabe", aus: "ausgeschaltet" };
const SSTATUS_LABEL = { offen: "offen", gesendet: "gesendet", ignoriert: "ignoriert", bearbeitet: "bearbeitet" };

// ---------------------------------------------------------------------------
// Hilfsfunktionen
// ---------------------------------------------------------------------------
const esc = (v) =>
  String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const locale = () => (LANG === "de" ? "de-DE" : "en-GB");
function money(v, cur = "EUR", digits = 0) {
  if (v === null || v === undefined || isNaN(v)) return "–";
  return new Intl.NumberFormat(locale(), { style: "currency", currency: cur, maximumFractionDigits: digits, minimumFractionDigits: digits }).format(v);
}
function num(v, digits = 0) {
  if (v === null || v === undefined || isNaN(v)) return "–";
  return new Intl.NumberFormat(locale(), { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(v);
}
const pct = (v, d = 1) => (v === null || v === undefined ? "–" : `${num(v, d)} %`);
function delta(v, unit = "%", invert = false) {
  // Veränderung als farbiges Kästchen; invert = höher ist schlecht (Kosten, Stornos)
  if (v === null || v === undefined || isNaN(v)) return "";
  const good = invert ? v < 0 : v > 0;
  const cls = v === 0 ? "flat" : good ? "up" : "down";
  const arrow = v > 0 ? "▲" : v < 0 ? "▼" : "■";
  return `<span class="delta ${cls}">${arrow} ${num(Math.abs(v), 1)}${unit === "pp" ? " PP" : " %"}</span>`;
}
const D = (s) => new Date(`${s}T00:00:00`);
const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const addDays = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
const addMonths = (d, n) => new Date(d.getFullYear(), d.getMonth() + n, 1);
function fdate(s, opts = { day: "2-digit", month: "2-digit", year: "2-digit" }) {
  if (!s) return "–";
  // Smoobu liefert „YYYY-MM-DD HH:MM:SS“ – Safari/iOS braucht das „T“
  const d = s.length > 10 ? new Date(String(s).replace(" ", "T")) : D(s);
  return d.toLocaleDateString(locale(), opts);
}
// Wochentag + Datum immer mit Jahr (zweistellig), da Listen über den Jahreswechsel reichen – sonst ist
// „17.08.“ nicht von „27.12.“ des Vorjahres zu unterscheiden (Wunsch Betreiber 16.11.2026)
const fdow = (s) => fdate(s, { weekday: "short", day: "2-digit", month: "2-digit", year: "2-digit" });
// Datum + Uhrzeit (Nachrichten, Vorschläge) ebenfalls mit Jahr
const DT_FMT = { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" };
const nightsBetween = (a, b) => Math.round((D(b) - D(a)) / 86400000);
const PERIOD_LABEL = {
  monat: "Laufender Monat", vormonat: "Vormonat", folgemonat: "Folgemonat", jahr: "Laufendes Jahr",
  jahr_bis_heute: "Jahr bis heute", vorjahr: "Vorjahr", letzte_12_monate: "Letzte 12 Monate",
  naechste_12_monate: "Nächste 12 Monate", gesamt: "Gesamter Zeitraum",
};
const COMPARE_LABEL = { vorjahr: "Vorjahr", vorjahr_stand: "Buchungsstand Vorjahr", vorperiode: "Vorperiode", kein: "Kein Vergleich" };
const STATUS_ICON = { kommend: "mdi:calendar-arrow-right", laufend: "mdi:home-account", vergangen: "mdi:check",
  storniert: "mdi:cancel", blockiert: "mdi:lock" };

// ---------------------------------------------------------------------------
// Design-System „Moos & Schiefer“ (v1.15.0)
// ---------------------------------------------------------------------------
// Farben sind fest je Modus (hell/dunkel) statt aus dem HA-Theme, damit Kanäle,
// Zustände und Flächen in beiden Modi gleich gut lesbar sind. Der Modus gilt je
// Gerät (localStorage): „hell“, „dunkel“ oder „system“ (= Dunkelmodus von HA).
const THEME_KEY = "smoobu-theme";
const APT_KEY = "smoobu-wohnung";
const ALL = "alle";
const PAL = {
  light: { bg: "#EEF1EF", surf: "#FFFFFF", surf2: "#F5F7F6", ink: "#17211D", mut: "#5B6964", line: "#DCE3E0",
    acc: "#2F6B4F", accInk: "#FFFFFF", good: "#2F7D52", bad: "#C2413B", warn: "#B7791F", block: "#9AA6A1" },
  dark: { bg: "#0F1513", surf: "#18201D", surf2: "#1F2925", ink: "#E5ECE8", mut: "#8E9D97", line: "#2A3530",
    acc: "#74C69D", accInk: "#0F1513", good: "#74C69D", bad: "#F08A80", warn: "#E9B65A", block: "#56625D" },
};
// Kanalfarben: an die Marken angelehnt, aber auf die Palette abgestimmt [hell, dunkel]
const CH_COLORS = {
  "booking.com": ["#2D64B3", "#6E9CE6"], airbnb: ["#E05A5F", "#F07F83"], "direct booking": ["#2F6B4F", "#74C69D"],
  direkt: ["#2F6B4F", "#74C69D"], "fewo-direkt": ["#D69A2D", "#E9B65A"], vrbo: ["#D69A2D", "#E9B65A"],
  website: ["#7A5CC8", "#A58CF0"], hometogo: ["#C8643B", "#E79A73"], "hundeurlaub.de": ["#3F8F86", "#7CCBBE"],
  expedia: ["#8A4FB0", "#C08CE0"],
};
const CH_FALLBACK = [["#3F8F86", "#7CCBBE"], ["#A0527A", "#E58AC0"], ["#6B7A2E", "#B9C66A"], ["#4A62A8", "#8FA5EC"],
  ["#8C6A3F", "#D2AE7E"], ["#2E7D8F", "#73C0D2"]];
const CSS_VARS = (p) => `--sm-bg:${p.bg};--sm-surf:${p.surf};--sm-surf2:${p.surf2};--sm-ink:${p.ink};--sm-muted:${p.mut};
  --sm-line:${p.line};--sm-accent:${p.acc};--sm-acc-ink:${p.accInk};--sm-good:${p.good};--sm-bad:${p.bad};--sm-warn:${p.warn};
  --sm-block:${p.block};`;

// v1.17.1: Übergabe Übersicht → Belegungsplan (nur für diesen Tab, wird beim Lesen gelöscht)
const Preselect = {
  set(v) { try { sessionStorage.setItem("smoobu-preselect", JSON.stringify(v)); } catch (e) { /* privat/gesperrt */ } },
  take() {
    try { const v = JSON.parse(sessionStorage.getItem("smoobu-preselect") || "null"); sessionStorage.removeItem("smoobu-preselect"); return v; }
    catch (e) { return null; }
  },
};
function lsGet(k, d) { try { return localStorage.getItem(k) ?? d; } catch (e) { return d; } }
function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* privates Fenster o. Ä. */ } }

const Theme = {
  listeners: new Set(),
  get mode() { const m = lsGet(THEME_KEY, "system"); return ["hell", "dunkel", "system"].includes(m) ? m : "system"; },
  set mode(m) { lsSet(THEME_KEY, m); this.listeners.forEach((l) => l()); },
  dark(hass) {
    const m = this.mode;
    if (m === "dunkel") return true;
    if (m === "hell") return false;
    if (hass?.themes && typeof hass.themes.darkMode === "boolean") return hass.themes.darkMode;
    return !!window.matchMedia?.("(prefers-color-scheme: dark)").matches;
  },
  pal(hass) { return PAL[this.dark(hass) ? "dark" : "light"]; },
};
let DARK = false; // aktueller Modus für Farbfunktionen (wird bei jedem Rendern gesetzt)

function chColor(name, i = 0) {
  const key = String(name || "").toLowerCase();
  const pair = CH_COLORS[key] || CH_FALLBACK[Math.abs([...key].reduce((a, c) => a * 31 + c.charCodeAt(0), 7) + i) % CH_FALLBACK.length];
  return pair[DARK ? 1 : 0];
}
function colorOf(apt, name, blocked = false) {
  if (blocked) return PAL[DARK ? "dark" : "light"].block;
  return chColor(name);
}

// Schrift lokal (Schibsted Grotesk, SIL OFL 1.1) – @font-face muss im Dokument stehen, nicht im Shadow DOM
(function loadFont() {
  if (document.getElementById("smoobu-font")) return;
  const st = document.createElement("style");
  st.id = "smoobu-font";
  // Pfad aus dem eigenen <script> ableiten (Standard: /smoobu_static/, siehe frontend.py)
  const own = [...document.querySelectorAll("script[src]")].find((x) => x.src.includes("smoobu-cards.js"));
  const base = own ? own.src.replace(/smoobu-cards\.js.*$/, "") : "/smoobu_static/";
  st.textContent = `@font-face { font-family: "Smoobu Schibsted"; font-weight: 400 900; font-display: swap;
    src: url("${base}fonts/schibsted-grotesk.woff2") format("woff2"); }`;
  document.head.appendChild(st);
})();
const FONT = `"Smoobu Schibsted", var(--ha-font-family-body, Roboto), system-ui, sans-serif`;
// Für style="…"-Attribute: doppelte Anführungszeichen würden das Attribut beenden (v1.18.0: Dialoge waren ungestylt)
const FONT_ATTR = FONT.replace(/"/g, "'");

// Gewählte Wohnung je Gerät: „alle“ oder apartment_id (nur relevant ab 2 Wohnungen)
const AptSel = {
  listeners: new Set(),
  get value() { const v = lsGet(APT_KEY, ALL); return v === ALL ? ALL : Number(v) || ALL; },
  set value(v) { lsSet(APT_KEY, String(v)); this.listeners.forEach((l) => l()); },
};

// v1.17.1: Zeigt eine Kopfzeile auf dieser Seite schon die Wohnungsauswahl? Dann blendet die
// Statistik ihre eigene (gleiche Einstellung AptSel) aus – keine doppelte Auswahl auf einer Seite
const HeaderApts = {
  n: 0, listeners: new Set(),
  add() { this.n++; this.listeners.forEach((l) => l()); },
  remove() { this.n = Math.max(0, this.n - 1); this.listeners.forEach((l) => l()); },
};
// Virtuelle „Wohnung“ für die Gesamtansicht: Kanäle aller Wohnungen, Währung der ersten
// v1.18.0: Benutzerrollen – Rechte des angemeldeten Benutzers je Wohnung (Backend prüft zusätzlich)
const ALL_RIGHTS = ["finanzen", "gaeste", "nachrichten", "antworten", "belegung", "preise", "einstellungen"];
const rightsOf = (apt) => new Set(apt?.zugriff?.rechte ?? ALL_RIGHTS);
// v1.18.0: Kategorien des Aufgaben-Boards (gleiche Schlüssel wie const.TASK_CATEGORIES)
const TASK_CATS = [["nachrichten", "Nachrichten"], ["rechnungen", "Rechnungen"], ["preise", "Preise"], ["lastminute", "Last-Minute"], ["luecken", "Lücken"]];
// Seite (Pfad) → nötiges Recht; Seiten ohne Eintrag sind für jede Rolle außer „Kein Zugriff“ sichtbar
const PAGE_RIGHT = { finanzen: "finanzen", statistik: "finanzen", nachrichten: "nachrichten", assistent: "nachrichten",
  einstellungen: "einstellungen", buchungen: "gaeste", belegung: "gaeste", kalender: "gaeste" };
// Darf der Benutzer `right` für Wohnung aptId (undefined = erste, „alle“ = alle)? Aus dem gecachten smoobu/info
function can(right, aptId) {
  const info = window.__smoobuStore?.info;
  if (!info) return true; // noch keine Info → nicht vorab sperren, das Backend prüft ohnehin
  const apt = aptId === ALL ? allApartment(info) : info.wohnungen.find((w) => w.apartment_id === aptId) || info.wohnungen[0];
  return rightsOf(apt).has(right);
}
const pageRight = (path) => Object.entries(PAGE_RIGHT).find(([k]) => String(path).includes(k))?.[1] || "gaeste";
function allApartment(info) {
  const ws = info.wohnungen;
  const seen = new Map();
  for (const w of ws) for (const k of w.kanaele) if (!seen.has(k.name)) seen.set(k.name, k);
  return { apartment_id: ALL, name: t("Alle Wohnungen"), kuerzel: "", currency: ws[0]?.currency || "EUR",
    kanaele: [...seen.values()], direktkanaele: ws[0]?.direktkanaele, check_in: ws[0]?.check_in, check_out: ws[0]?.check_out,
    erster_tag: ws.map((w) => w.erster_tag).filter(Boolean).sort()[0] || null, alle: true,
    // Rechte über alle Wohnungen: nur, was in jeder Wohnung erlaubt ist
    zugriff: { rechte: ALL_RIGHTS.filter((r) => ws.every((w) => rightsOf(w).has(r))) } };
}
const aptCode = (info, id) => info?.wohnungen.find((w) => w.apartment_id === id)?.kuerzel || "";
const codeTag = (code) => (code ? `<em class="ak">${esc(code)}</em>` : "");

// ---------------------------------------------------------------------------
// Gemeinsamer Datenspeicher: eine Verbindung, ein Abo für alle Karten
// ---------------------------------------------------------------------------
class SmoobuStore {
  constructor(hass) {
    this.hass = hass;
    this.listeners = new Set();
    this.msgListeners = new Set();
    this.info = null;
    this._sub = null;
    this._cache = new Map();
  }
  static get(hass) {
    if (!window.__smoobuStore || window.__smoobuStore.hass.connection !== hass.connection) {
      window.__smoobuStore = new SmoobuStore(hass);
    }
    window.__smoobuStore.hass = hass;
    return window.__smoobuStore;
  }
  async ws(type, params = {}, { cache = true } = {}) {
    const key = JSON.stringify([type, params]);
    if (cache && this._cache.has(key)) return this._cache.get(key);
    const p = this.hass.callWS({ type, ...params });
    if (cache) this._cache.set(key, p);
    try {
      return await p;
    } catch (e) {
      this._cache.delete(key);
      throw e;
    }
  }
  async getInfo() {
    if (!this.info) this.info = await this.ws("smoobu/info");
    return this.info;
  }
  subscribe(cb) {
    this.listeners.add(cb);
    if (!this._sub) this._openSub();
    return () => this.listeners.delete(cb);
  }
  // v1.18.0: nach Speichern der Einstellungen lädt die Integration neu – das alte Abo hängt am alten
  // Coordinator und meldet nichts mehr → schließen, neu öffnen und alle Karten neu laden
  resubscribe() {
    const old = this._sub;
    this._sub = null;
    old?.then((unsub) => unsub?.()).catch(() => { /* Verbindung schon zu */ });
    if (this.listeners.size) this._openSub();
    this.invalidate();
  }
  _openSub() {
    this._sub = this.hass.connection.subscribeMessage((ev) => {
      // v1.17.0: nur Antwortstatus geändert (auch von anderem Gerät) → Zähler neu zählen
      if (ev?.art === "nachrichten") { this.messagesChanged(); return; }
      // Neuer Datenstand → alle Zwischenergebnisse verwerfen und Karten neu laden
      this._cache.clear();
      this.info = null;
      this.listeners.forEach((l) => l());
    }, { type: "smoobu/subscribe" });
  }
  invalidate() {
    this._cache.clear();
    this.info = null;
    this.listeners.forEach((l) => l());
  }
  // v1.17.0: Antwortstatus geändert (keine Antwort nötig / rückgängig) → nur Zähler neu zählen,
  // ohne alle Karten neu zu laden (Posteingang behält Auswahl und Entwurf)
  onMessages(cb) {
    this.msgListeners.add(cb);
    return () => this.msgListeners.delete(cb);
  }
  messagesChanged() { this.msgListeners.forEach((l) => l()); }
  async service(service, data, returnResponse = false) {
    const r = await this.hass.callService("smoobu", service, data, undefined, true, returnResponse);
    this.invalidate();
    return r;
  }
}

// ---------------------------------------------------------------------------
// Gemeinsames Aussehen
// ---------------------------------------------------------------------------
const BASE_CSS = `
  :host([panel]) { padding-left: clamp(8px, 2vw, 28px); padding-right: clamp(8px, 2vw, 28px); }
  :host([panel]:last-child) { padding-bottom: 24px; }
  :host { display: block; --sm-gap: 14px; --sm-r: 14px; --sm-rs: 10px; color: var(--sm-ink);
    font-family: ${FONT}; font-size: 15px; line-height: 1.45; -webkit-font-smoothing: antialiased; }
  * { box-sizing: border-box; }
  ha-card { padding: 18px 20px; overflow: hidden; background: var(--sm-surf); color: var(--sm-ink);
    border: 1px solid var(--sm-line); border-radius: var(--sm-r); box-shadow: none; font-family: ${FONT}; }
  h2 { margin: 0; font-size: 1.05rem; font-weight: 650; display: flex; align-items: center; gap: 8px; letter-spacing: -.005em; }
  h3 { margin: 18px 0 8px; font-size: .95rem; font-weight: 650; color: var(--sm-ink); }
  .sub { color: var(--sm-muted); font-size: .84rem; }
  .row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
  .legend.gloss { margin-top: 6px; font-size: .78rem; color: var(--sm-muted); gap: 4px 14px; }
  .legend.gloss b { color: var(--sm-ink); font-weight: 600; }
  .grow { flex: 1 1 auto; min-width: 0; }
  .head { display: flex; gap: 12px; flex-wrap: wrap; align-items: baseline; margin-bottom: 12px; }
  .head h2 { flex: 1 1 auto; }
  .grid { display: grid; gap: 0; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
    border: 1px solid var(--sm-line); border-radius: var(--sm-r); overflow: hidden; }
  .tile { padding: 12px 16px; min-width: 0; border-right: 1px solid var(--sm-line); border-bottom: 1px solid var(--sm-line); margin: 0 -1px -1px 0; }
  .tile .l { font-size: .82rem; color: var(--sm-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .tile .v { font-size: 1.45rem; font-weight: 650; margin-top: 2px; white-space: nowrap; letter-spacing: -.02em;
    display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
  .tile .s { font-size: .8rem; color: var(--sm-muted); margin-top: 2px; }
  .delta { font-size: .74rem; font-weight: 650; padding: 1px 6px; border-radius: 6px; white-space: nowrap; letter-spacing: 0; }
  .delta.up { color: var(--sm-good); background: color-mix(in srgb, var(--sm-good) 14%, transparent); }
  .delta.down { color: var(--sm-bad); background: color-mix(in srgb, var(--sm-bad) 14%, transparent); }
  .delta.flat { color: var(--sm-muted); }
  .chip { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 999px;
    border: 1px solid var(--sm-line); background: var(--sm-surf); color: var(--sm-ink); cursor: pointer; font: inherit; font-size: .84rem; }
  .chip:hover { border-color: color-mix(in srgb, var(--sm-ink) 30%, transparent); }
  .chip[aria-pressed="true"] { background: var(--sm-ink); border-color: var(--sm-ink); color: var(--sm-surf); }
  .dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; flex: none; }
  .badge { display: inline-flex; align-items: center; gap: 5px; font-size: .78rem; font-weight: 600; padding: 2px 9px; border-radius: 999px;
    background: var(--sm-surf2); border: 1px solid var(--sm-line); white-space: nowrap; }
  .badge.good { background: color-mix(in srgb, var(--sm-good) 13%, transparent); color: var(--sm-good); border-color: transparent; }
  .badge.bad { background: color-mix(in srgb, var(--sm-bad) 13%, transparent); color: var(--sm-bad); border-color: transparent; }
  .badge.warn { background: color-mix(in srgb, var(--sm-warn) 16%, transparent); color: var(--sm-warn); border-color: transparent; }
  .ak { display: inline-grid; place-items: center; min-width: 26px; height: 19px; padding: 0 5px; border-radius: 5px; font-size: .68rem;
    font-weight: 700; font-style: normal; background: var(--sm-surf2); border: 1px solid var(--sm-line); color: var(--sm-ink);
    letter-spacing: .02em; margin-left: 7px; vertical-align: 1px; }
  select, input, textarea { font: inherit; font-size: .9rem; color: var(--sm-ink); background: var(--sm-surf);
    border: 1px solid var(--sm-line); border-radius: var(--sm-rs); padding: 7px 10px; }
  select:focus, input:focus, textarea:focus { outline: 2px solid color-mix(in srgb, var(--sm-accent) 45%, transparent); outline-offset: 0; }
  input[type=date], input[type=time] { color-scheme: var(--sm-scheme); }
  textarea { width: 100%; min-height: 76px; resize: vertical; line-height: 1.45; }
  button.btn, a.btn { font: inherit; font-size: .86rem; font-weight: 600; border: 1px solid transparent; border-radius: 999px; padding: 7px 15px;
    cursor: pointer; background: var(--sm-accent); color: var(--sm-acc-ink); display: inline-flex; align-items: center; gap: 6px; }
  button.btn.flat, a.btn.flat { background: none; color: var(--sm-accent); border-color: var(--sm-line); }
  button.btn.flat:hover, a.btn.flat:hover { border-color: var(--sm-accent); }
  button.btn.danger { background: var(--sm-bad); color: #fff; }
  button.btn:disabled { opacity: .5; cursor: default; }
  button:focus-visible, .chip:focus-visible { outline: 2px solid var(--sm-accent); outline-offset: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: .86rem; }
  th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--sm-line); white-space: nowrap; }
  th { font-weight: 600; color: var(--sm-muted); font-size: .78rem; cursor: pointer; user-select: none; background: var(--sm-surf2); }
  th:first-child { border-top-left-radius: var(--sm-rs); } th:last-child { border-top-right-radius: var(--sm-rs); }
  td.n, th.n { text-align: right; } /* Schibsted: Tabellenziffern hätten breite Satzzeichen */
  tr.click { cursor: pointer; } tr.click:hover td { background: var(--sm-surf2); }
  tfoot td { font-weight: 650; border-bottom: none; border-top: 2px solid var(--sm-line); }
  .scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .empty { color: var(--sm-muted); padding: 18px 0; text-align: center; }
  .err { color: var(--sm-bad); padding: 8px 0; }
  .list > div { padding: 10px 0; border-bottom: 1px solid var(--sm-line); display: flex; gap: 12px; align-items: center; }
  .list > div:last-child { border-bottom: none; }
  .list .click { cursor: pointer; } .list .click:hover b { color: var(--sm-accent); }
  .muted { color: var(--sm-muted); }
  a { color: var(--sm-accent); }
  ha-icon { --mdc-icon-size: 18px; }
  .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 4px 0 12px; }
  .seg { display: inline-flex; border: 1px solid var(--sm-line); border-radius: 999px; padding: 3px; background: var(--sm-surf); }
  .seg button { border: none; background: none; padding: 5px 12px; font: inherit; font-size: .84rem; cursor: pointer; color: var(--sm-muted); border-radius: 999px; }
  .seg button[aria-pressed="true"] { background: var(--sm-ink); color: var(--sm-surf); font-weight: 600; }
  .lnk { color: var(--sm-accent); font-size: .86rem; font-weight: 500; cursor: pointer; background: none; border: 0; font-family: inherit; padding: 0; }
  .lnk:hover { text-decoration: underline; }
`;

function toast(msg) {
  const el = document.createElement("div");
  const p = PAL[DARK ? "dark" : "light"];
  el.style.cssText = `position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:${p.ink};color:${p.surf};` +
    `padding:10px 18px;border-radius:999px;z-index:10003;font:500 14px ${FONT};box-shadow:0 6px 24px rgba(0,0,0,.25)`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ---------------------------------------------------------------------------
// Basisklasse aller Karten
// ---------------------------------------------------------------------------
class SmoobuCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._state = {};
    this._data = null;
    this._error = null;
    this._loading = false;
  }
  setConfig(config) {
    this._config = { ...(this.constructor.defaults || {}), ...(config || {}) };
    this._state = { ...this._state, ...(this.constructor.initialState?.(this._config) || {}) };
    if (this._hass) this._reload();
  }
  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    LANG = (hass.locale?.language || hass.language || "de").startsWith("de") ? "de" : "en";
    this.store = SmoobuStore.get(hass);
    if (first) {
      this._listen();
      this._reload();
    } else {
      // „System“: HA-Dunkelmodus hat gewechselt → neu zeichnen
      if (this._data && Theme.dark(hass) !== this.hasAttribute("dark")) this.render();
      this.onHass?.();
    }
  }
  get hass() { return this._hass; }
  // Daten, Hell/Dunkel und Wohnungsauswahl abonnieren (v1.15.0: Modus + Wohnung je Gerät)
  _listen() {
    const offData = this.store.subscribe(() => this._reload());
    const onTheme = () => this.render();
    const onApt = () => { if (!this._config?.apartment_id) { this._data = null; this._reload(); } };
    Theme.listeners.add(onTheme);
    AptSel.listeners.add(onApt);
    this._unsub = () => { offData(); Theme.listeners.delete(onTheme); AptSel.listeners.delete(onApt); };
  }
  disconnectedCallback() { this._unsub?.(); this._unsub = null; this._hass && (this._rebind = true); }
  connectedCallback() {
    if (this._rebind && this._hass) { this._rebind = false; this._listen(); this._reload(); }
  }
  // Ziel der Abfragen: feste Wohnung aus der Kartenkonfig, sonst (ab 2 Wohnungen) die Auswahl
  // im Kopf („alle“ oder eine Wohnung), sonst die erste Wohnung (Verhalten bis v1.14).
  get target() {
    const t = {};
    if (this._config?.entry_id) t.entry_id = this._config.entry_id;
    if (this._config?.apartment_id) { t.apartment_id = Number(this._config.apartment_id); return t; }
    const ws = this.store?.info?.wohnungen || [];
    if (ws.length > 1) {
      const v = AptSel.value;
      t.apartment_id = v === ALL || !ws.some((w) => w.apartment_id === v) ? ALL : v;
    }
    return t;
  }
  get multi() { return this.target.apartment_id === ALL; }
  async apartment() {
    const info = await this.store.getInfo();
    const id = this.target.apartment_id;
    if (id === ALL) return allApartment(info);
    return info.wohnungen.find((w) => id === undefined || w.apartment_id === id) || info.wohnungen[0];
  }
  async _reload() {
    if (!this._hass || !this._config) return;
    const token = (this._token = Symbol());
    this._loading = true;
    if (!this._data) this.render();
    try {
      const data = await this.load();
      if (token !== this._token) return;
      this._data = data;
      this._error = null;
    } catch (e) {
      if (token !== this._token) return;
      this._error = e?.message || String(e);
    }
    this._loading = false;
    this.render();
  }
  setState(patch, reload = false) {
    this._state = { ...this._state, ...patch };
    reload ? this._reload() : this.render();
  }
  render() {
    const body = this._error
      ? (/Keine Berechtigung/.test(this._error) ? `<div class="empty">🔒 ${esc(t(this._error))}</div>` : `<div class="err">${t("Fehler")}: ${esc(this._error)}</div>`)
      : this._data ? this.body(this._data) : `<div class="empty">${t("Laden …")}</div>`;
    const scroll = this.shadowRoot.querySelector(".scroll")?.scrollLeft;
    DARK = Theme.dark(this._hass);
    this.toggleAttribute("dark", DARK);
    this.toggleAttribute("panel", this.inPanelView());
    const vars = `:host { ${CSS_VARS(PAL[DARK ? "dark" : "light"])} --sm-scheme: ${DARK ? "dark" : "light"}; }`;
    this.shadowRoot.innerHTML = `<style>${vars}${BASE_CSS}${this.constructor.css || ""}</style><ha-card>${body}</ha-card>`;
    if (scroll) { const s = this.shadowRoot.querySelector(".scroll"); if (s) s.scrollLeft = scroll; }
    this.bind?.(this.shadowRoot);
  }
  // v1.15.1: In Panel-Ansichten liegen die Karten ohne Rand am Fensterrand → Seitenabstand selbst setzen
  inPanelView() {
    if (this._panel !== undefined) return this._panel;
    let n = this;
    for (let i = 0; i < 40 && n; i++) {
      n = n.parentNode || n.host;
      if (n?.localName === "hui-panel-view") return (this._panel = true);
      if (n?.localName === "hui-sections-view" || n?.localName === "hui-masonry-view") return (this._panel = false);
    }
    return false; // noch nicht eingehängt: beim nächsten Rendern erneut prüfen
  }
  $(sel) { return this.shadowRoot.querySelector(sel); }
  $$(sel) { return [...this.shadowRoot.querySelectorAll(sel)]; }
  openBooking(id) { SmoobuBookingDialog.open(this._hass, id, this.target); }
  // Wohnungskürzel nur in der Gesamtansicht zeigen
  code(b) { return this.multi ? codeTag(aptCode(this.store.info, b.wohnung_id)) : ""; }
  getCardSize() { return 6; }
  getGridOptions() { return { columns: 12, min_columns: 6 }; }
}

// Kleine Bausteine
// Richtung einer Nachricht eindeutig beschriften (v1.14.0): typ 1 = vom Gast, 2 = an den Gast
function dirLabel(m) {
  const typ = Number(m.typ);
  return typ === 1 ? `← ${t("Vom Gast")}` : typ === 2 ? `→ ${t("An den Gast")}` : "•";
}
function tile(label, value, sub = "", extra = "") {
  return `<div class="tile">${extra}<div class="l">${esc(label)}</div><div class="v">${value}</div>${sub ? `<div class="s">${sub}</div>` : ""}</div>`;
}
function periodSelect(value, custom = true) {
  const opts = Object.entries(PERIOD_LABEL).map(([k, v]) => `<option value="${k}" ${k === value ? "selected" : ""}>${t(v)}</option>`).join("");
  return `<select data-k="period">${opts}${custom ? `<option value="custom" ${value === "custom" ? "selected" : ""}>${t("Benutzerdefiniert")}</option>` : ""}</select>`;
}
function channelChips(apt, selected, colors = {}) {
  const sel = new Set(selected || []);
  const all = !sel.size;
  const chips = [`<button class="chip" data-ch="" aria-pressed="${all}">${t("Alle")}</button>`,
    `<button class="chip" data-ch="Direkt" aria-pressed="${sel.has("Direkt")}">${t("Direkt")}</button>`,
    `<button class="chip" data-ch="Portale" aria-pressed="${sel.has("Portale")}">${t("Portale")}</button>`];
  for (const ch of apt.kanaele) {
    chips.push(`<button class="chip" data-ch="${esc(ch.name)}" aria-pressed="${sel.has(ch.name)}"><span class="dot" style="background:${chColor(ch.name)}"></span>${esc(chn(ch.name))}</button>`);
  }
  return chips.join("");
}
function toggleChannel(list, ch) {
  if (!ch) return [];
  const s = new Set(list || []);
  s.has(ch) ? s.delete(ch) : s.add(ch);
  return [...s];
}

// Zitierten E-Mail-Verlauf in Gastantworten abschneiden (bleibt per Klick sichtbar)
// Nachrichten neueste zuerst (v1.12.1): Das Backend liefert den Verlauf nach
// Smoobu-Nachrichten-ID aufsteigend (= chronologisch). Sortiert wird nach ID absteigend
// statt nach Zeitstempel, weil Safari/iOS Smoobus Format „JJJJ-MM-TT hh:mm:ss“ nicht
// sicher parst. Ohne ID entscheidet die umgekehrte Lieferreihenfolge (stabil).
const newestFirst = (list) => (list || []).map((m, i) => [m, i])
  .sort((a, b) => ((Number(b[0].id) || 0) - (Number(a[0].id) || 0)) || (b[1] - a[1]))
  .map((x) => x[0]);
const QUOTE_RE = /(\n|^)\s*-{3,}\s*(Ursprüngliche Nachricht|Original Message|Original-Nachricht)|Von meinem(\/meiner)? [^\n]{0,40}gesendet|Sent from my|(\n|^)\s*(Am .{6,60} schrieb |On .{6,80} wrote:)/i;
function msgHtml(text) {
  const s = String(text || "");
  const m = s.match(QUOTE_RE);
  if (!m || m.index < 3) return esc(s.trim());
  return `${esc(s.slice(0, m.index).trim())}<details><summary class="muted">…</summary>${esc(s.slice(m.index).trim())}</details>`;
}

// Freie Lücken zwischen Belegungen (inkl. Sperrzeiten) + Prüfung gegen Mindestaufenthalt
function findGaps(bookings, rates, startIso, days, maxLen = 21) {
  const occ = new Set();
  for (const b of bookings) {
    if (b.storniert) continue;
    for (let d = D(b.anreise); d < D(b.abreise); d = addDays(d, 1)) occ.add(iso(d));
  }
  const gaps = [];
  const start = D(startIso);
  let d = start;
  const end = addDays(start, days);
  while (d < end) {
    if (occ.has(iso(d))) { d = addDays(d, 1); continue; }
    const from = d;
    while (d < addDays(end, maxLen) && !occ.has(iso(d))) d = addDays(d, 1);
    const len = Math.round((d - from) / 86400000);
    // Nur echte Lücken: danach folgt wieder eine Belegung, nicht zu lang
    if (occ.has(iso(d)) && len <= maxLen) {
      const r = rates?.[iso(from)] || {};
      const minStay = r.min_length_of_stay ?? null;
      gaps.push({ von: iso(from), bis: iso(d), naechte: len, min: minStay, preis: r.price ?? null,
        buchbar: minStay === null || minStay <= len });
    }
  }
  return gaps;
}

// Uhrzeit „16:00“ → „16 Uhr“, „16:30“ → „16:30 Uhr“
function uhr(s) {
  if (!s) return "";
  const [h, m] = String(s).slice(0, 5).split(":");
  if (LANG !== "de") return `${Number(h)}:${m || "00"}`;
  return m && m !== "00" ? `${Number(h)}:${m} Uhr` : `${Number(h)} Uhr`;
}
// „Sa, 21.11.26“ – deutsche Wochentage ohne Punkt (toLocaleDateString liefert „Sa.,“), Jahr zweistellig
const WD_DE = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
const fdowLong = (s) => {
  if (!s) return "–";
  const d = D(String(s).slice(0, 10));
  return LANG === "de" ? `${WD_DE[d.getDay()]}, ${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getFullYear()).slice(-2)}`
    : fdate(s, { weekday: "short", day: "2-digit", month: "2-digit", year: "2-digit" });
};
const monthName = (iso10) => D(iso10).toLocaleDateString(locale(), { month: "long" });
const plural = (n, one, many) => `${num(n)} ${n === 1 ? one : many}`;
const daysWord = (n) => (n === 0 ? t("heute") : n === 1 ? t("morgen") : `in ${n} ${t("Tagen")}`);

// Verlauf als kleine Linie (12 Werte); leer bei zu wenig Daten
// Verlauf als kleine Linie (v1.15.2: optional mit blasser Vergleichslinie, z. B. Vorjahr).
// Beide Linien teilen sich Skala und Zeitachse (Länge = längere Reihe), damit die Lage vergleichbar ist.
function sparkline(values, compare = null) {
  const clean = (a) => (a || []).map((x) => (x === null || x === undefined || isNaN(x) ? null : Number(x)));
  const v = clean(values), c = clean(compare);
  const n = Math.max(v.length, c.length);
  const all = [...v, ...c].filter((x) => x !== null);
  if (v.filter((x) => x !== null).length < 2 || n < 2) return `<div class="spark"></div>`;
  const W = 120, H = 30;
  const lo = Math.min(...all), hi = Math.max(...all);
  const pt = (x, i) => [(i / (n - 1)) * W, H - 3 - ((x - lo) / (hi - lo || 1)) * (H - 6)];
  const line = (a) => a.map((x, i) => (x === null ? null : pt(x, i))).filter(Boolean).map((p) => p.map((q) => q.toFixed(1)).join(",")).join(" ");
  const last = v.map((x, i) => [x, i]).filter(([x]) => x !== null).pop();
  const [lx, ly] = pt(last[0], last[1]);
  const cmp = c.filter((x) => x !== null).length >= 2 ? `<polyline class="cmp" points="${line(c)}"/>` : "";
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">${cmp}
    <polyline points="${line(v)}"/><circle cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="2.6"/></svg>`;
}

// „9:00“ / „17:30:00“ → „09:00“ (vergleichbar als Text); leer → Ersatzwert
const hm = (s, dflt) => {
  const [h, m] = String(s || dflt || "00:00").slice(0, 5).split(":");
  return `${String(Number(h) || 0).padStart(2, "0")}:${String(Number(m) || 0).padStart(2, "0")}`;
};
// Aktuelle Uhrzeit „HH:MM“ in der Zeitzone von Home Assistant (nicht der des Browsers – Handy auf Reisen)
function nowHM(hass) {
  try {
    return new Intl.DateTimeFormat("de-DE", { hour: "2-digit", minute: "2-digit", hour12: false,
      timeZone: hass?.config?.time_zone || undefined }).format(new Date());
  } catch (e) { const d = new Date(); return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`; }
}

// Status einer Wohnung heute → kurze, präzise Sätze für den Kopf
// v1.17.1: uhrzeitgenau wie die Sensoren – ab Check-in-Zeit ist der anreisende Gast „aktuell“,
// ab Check-out-Zeit ist der abreisende Gast weg (vorher nur nach Datum: am Anreisetag blieb der Gast
// bis Mitternacht „Nächster Gast, heute“, Fall Olaf König 16.11.2026, Anreise 17:30)
function stayStatus(apt, bookings, today, now = "00:00") {
  const guests = bookings.filter((b) => !b.blockiert && !b.storniert).sort((a, b) => a.anreise.localeCompare(b.anreise));
  const staying = guests.find((b) => b.anreise < today && b.abreise > today);
  const arr = guests.find((b) => b.anreise === today);
  const dep = guests.find((b) => b.abreise === today);
  const next = guests.find((b) => b.anreise > today);
  const co = (b) => uhr(b?.check_out || apt.check_out || "11:00");
  const ci = (b) => uhr(b?.check_in || apt.check_in || "16:00");
  const gap = (from, b) => (b ? nightsBetween(from, b.anreise) : null);
  const after = (from, b) => {
    if (!b) return t("Danach keine Buchung in den nächsten 6 Monaten.");
    const n = gap(from, b);
    return n === 0 ? `Direkt danach kommt ${esc(b.gast)}.`
      : `Danach ${plural(n, "Nacht", "Nächte")} frei, nächste Anreise ${fdowLong(b.anreise)} (${esc(b.gast)}).`;
  };
  // Uhrzeit-Grenzen (Standard wie oben: Check-in 16:00, Check-out 11:00)
  const arrived = arr && now >= hm(arr.check_in || apt.check_in, "16:00");
  const departed = dep && now >= hm(dep.check_out || apt.check_out, "11:00");
  const stay = (b) => `${plural(b.naechte, "Nacht", "Nächte")} bis ${fdowLong(b.abreise)}`;
  const ev = { arr, dep, arrived: !!arrived, departed: !!departed }; // für die Kurztexte der Mehr-Wohnungen-Ansicht
  if (arr && dep) return { key: "chg", ev, pill: t("Gästewechsel"), title: t("Gästewechsel heute"),
    current: arrived ? arr : departed ? null : dep, next: arrived ? next : arr,
    text: arrived ? `${esc(dep.gast)} ist abgereist, ${esc(arr.gast)}${arr.hund ? " 🐕" : ""} ist seit ${ci(arr)} da, ${stay(arr)}.`
      : departed ? `${esc(dep.gast)} ist abgereist, ${esc(arr.gast)}${arr.hund ? " 🐕" : ""} kommt um ${ci(arr)}. Reinigung dazwischen.`
      : `${esc(dep.gast)} reist bis ${co(dep)} ab, ${esc(arr.gast)}${arr.hund ? " 🐕" : ""} kommt um ${ci(arr)}. Reinigung dazwischen.` };
  if (dep) return { key: "dep", ev, pill: t("Abreise"), title: t("Abreise heute"), current: departed ? null : dep, next,
    text: `${esc(dep.gast)} ${departed ? "ist abgereist" : `reist bis ${co(dep)} ab`}. ${after(today, next)}` };
  if (arr) return { key: "arr", ev, pill: t("Anreise"), title: t("Anreise heute"), current: arrived ? arr : null, next: arrived ? next : arr,
    text: arrived ? `${esc(arr.gast)}${arr.hund ? " 🐕" : ""} ist seit ${ci(arr)} da, ${stay(arr)}.`
      : `${esc(arr.gast)}${arr.hund ? " 🐕" : ""} kommt um ${ci(arr)}, ${stay(arr)}.` };
  if (staying) return { key: "occ", pill: t("Belegt"), title: `${t("Belegt bis")} ${fdowLong(staying.abreise)}`, current: staying, next,
    text: `${esc(staying.gast)} reist am ${fdowLong(staying.abreise)} bis ${co(staying)} ab. ${after(staying.abreise, next)}` };
  if (next) return { key: "free", pill: t("Frei"), title: `${t("Frei bis")} ${fdowLong(next.anreise)}`, current: null, next,
    text: `${esc(next.gast)}${next.hund ? " 🐕" : ""} kommt ${daysWord(nightsBetween(today, next.anreise))} um ${ci(next)}, ${plural(next.naechte, "Nacht", "Nächte")}. Bis dahin ${plural(gap(today, next), "Nacht", "Nächte")} frei.` };
  return { key: "free", pill: t("Frei"), title: t("Frei"), current: null, next: null, text: t("Keine Buchung in den nächsten 6 Monaten.") };
}

// ===========================================================================
// Übersicht (v1.15.0 neu gestaltet)
// ===========================================================================
class SmoobuOverviewCard extends SmoobuCard {
  // kalender_path (v1.18.0b8, vorher belegung_path ab v1.17.1): Seite mit dem Kalender für „Anpassen“ bei
  // nicht buchbaren Lücken; "" = kein Button. Eine alte Option belegung_path gilt weiter (siehe kalenderPath)
  static defaults = { title: "", entities: [], upcoming: 5, gap_days: 60, band_days: 42 };
  // Pfad der Kalender-Seite: neue Option vor alter; ohne beide Standard „smoobu-kalender“
  get kalenderPath() {
    const c = this._config;
    return c.kalender_path ?? c.belegung_path ?? "smoobu-kalender";
  }
  // v1.17.1: Status hängt jetzt an der Uhrzeit (Check-in/-out). Ohne neue Daten zeichnet die Karte nicht neu –
  // ein offenes Tablet bliebe sonst bis zum nächsten Datenabruf auf „Anreise um 17:30“ stehen. Daher jede
  // Minute prüfen und nur neu zeichnen, wenn sich aktueller/nächster Gast einer Wohnung tatsächlich ändert.
  _statusSig() {
    const d = this._data;
    if (!d?.apts) return "";
    const now = nowHM(this._hass);
    return d.apts.map((w) => {
      const s = stayStatus(w, (d.bookings || []).filter((b) => !d.apts[1] || b.wohnung_id === w.apartment_id), d.today, now);
      return `${s.key}:${s.current?.id || ""}:${s.next?.id || ""}:${!!s.text && s.text.length}`;
    }).join("|");
  }
  _listen() {
    super._listen();
    let last = this._statusSig();
    const timer = setInterval(() => {
      const sig = this._statusSig();
      if (sig && sig !== last) { last = sig; this.render(); }
    }, 60000);
    const base = this._unsub;
    this._unsub = () => { base?.(); clearInterval(timer); };
  }
  static css = `
    /* v1.18.0: Aufgaben-Board „Wartet auf dich“ */
    .tchips { display: flex; gap: 4px; flex-wrap: wrap; margin: 0 0 10px; }
    .tchips button { border: 1px solid var(--sm-line); background: none; font: inherit; font-size: .8rem; padding: 4px 10px; border-radius: 999px; cursor: pointer; color: var(--sm-muted); }
    .tchips button[aria-pressed="true"] { background: var(--sm-accent); border-color: var(--sm-accent); color: var(--sm-acc-ink); }
    .tchips button b { font-weight: 700; margin-left: 2px; }
    .todo .tcat { display: inline-block; font-size: .68rem; font-weight: 650; text-transform: uppercase; letter-spacing: .04em; color: var(--sm-muted); margin-bottom: 2px; }
    .todo .tact { display: inline-flex; gap: 10px; margin-left: auto; font-size: .78rem; }
    .todo .tact .lnk { color: var(--sm-muted); }

    :host { padding-top: 4px; }
    ha-card { background: none; border: 0; padding: 0; overflow: visible; }
    .panel { background: var(--sm-surf); border: 1px solid var(--sm-line); border-radius: var(--sm-r); padding: 18px 20px; min-width: 0; }
    .ph { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
    /* Kopf: Aussage links, Gäste bzw. Wohnungen rechts */
    .hero { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr); gap: 26px; margin-bottom: var(--sm-gap); }
    @media (max-width: 1000px) { .hero { grid-template-columns: 1fr; } }
    .h-state { display: flex; gap: 12px; align-items: center; color: var(--sm-muted); font-size: .92rem; margin-bottom: 8px; }
    .pill { font-weight: 650; font-size: .8rem; padding: 3px 10px; border-radius: 999px; white-space: nowrap; }
    .pill.occ, .pill.dep { background: color-mix(in srgb, var(--sm-warn) 17%, transparent); color: var(--sm-warn); }
    .pill.chg, .pill.arr { background: color-mix(in srgb, var(--sm-bad) 14%, transparent); color: var(--sm-bad); }
    .pill.free { background: color-mix(in srgb, var(--sm-good) 14%, transparent); color: var(--sm-good); }
    .hero h1 { margin: 0; font-size: clamp(30px, 3.4vw, 44px); line-height: 1.06; font-weight: 650; letter-spacing: -.025em; }
    .lead { margin: 12px 0 0; font-size: 1.12rem; line-height: 1.45; max-width: 46ch; }
    .lead2 { margin: 6px 0 0; font-size: .98rem; color: var(--sm-muted); max-width: 52ch; }
    .events { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
    .ev { display: inline-flex; gap: 6px; align-items: center; font-size: .84rem; padding: 5px 12px; border-radius: 999px;
      background: var(--sm-surf); border: 1px solid var(--sm-line); cursor: default; }
    .ev.click { cursor: pointer; } .ev.click:hover { border-color: var(--sm-accent); }
    .ev.bad { border-color: color-mix(in srgb, var(--sm-bad) 45%, transparent); color: var(--sm-bad); font-weight: 650; }
    .ev ha-icon { --mdc-icon-size: 16px; color: var(--sm-muted); }
    .guests { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sm-gap); }
    @media (max-width: 640px) { .guests { grid-template-columns: 1fr; } }
    .guest { background: var(--sm-surf); border: 1px solid var(--sm-line); border-radius: var(--sm-r); padding: 16px 18px 14px;
      display: flex; flex-direction: column; position: relative; overflow: hidden; cursor: pointer; min-width: 0; }
    .guest::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--c); }
    .guest:hover { border-color: color-mix(in srgb, var(--c) 60%, var(--sm-line)); }
    .guest.none { cursor: default; color: var(--sm-muted); justify-content: center; }
    .guest.none::before { background: var(--sm-line); }
    .gl { font-size: .8rem; color: var(--sm-muted); }
    .gn { font-size: 1.25rem; font-weight: 650; margin: 3px 0 6px; letter-spacing: -.01em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .gm { font-size: .86rem; color: var(--sm-muted); flex: 1; }
    .note { font-size: .82rem; margin-top: 8px; }
    .note.bad { color: var(--sm-bad); font-weight: 600; }
    .gf { display: flex; align-items: center; gap: 8px; font-size: .84rem; margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--sm-line); }
    .gf b { margin-left: auto; font-size: .98rem; }
    .apts { padding: 4px 18px; }
    .aptrow { display: flex; gap: 14px; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--sm-line); cursor: pointer; }
    .aptrow:last-child { border-bottom: 0; }
    .aptrow:hover b { color: var(--sm-accent); }
    .aptrow .ak { margin: 0; height: 24px; min-width: 32px; font-size: .74rem; }
    .aptrow .an { flex: 1; min-width: 0; display: flex; flex-direction: column; }
    .aptrow .an span { font-size: .84rem; color: var(--sm-muted); }
    /* Belegungsband: Balken von Tagesmitte (Anreise) bis Tagesmitte (Abreise) */
    .band { margin-bottom: var(--sm-gap); }
    .legend { display: flex; gap: 14px; flex-wrap: wrap; font-size: .8rem; color: var(--sm-muted); }
    .legend span { display: inline-flex; gap: 6px; align-items: center; }
    .hatch { background: repeating-linear-gradient(135deg, var(--sm-block) 0 2px, transparent 2px 5px); outline: 1px solid var(--sm-block); }
    .rib { min-width: 760px; }
    .rrow { display: grid; grid-template-columns: var(--lab, 0px) minmax(0, 1fr); align-items: center; }
    .rlab { display: flex; gap: 8px; align-items: center; font-size: .86rem; font-weight: 600; padding-right: 10px; white-space: nowrap; overflow: hidden; }
    .rlab .ak { margin: 0; }
    .rlab .nm { overflow: hidden; text-overflow: ellipsis; min-width: 0; }
    .cols { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); }
    .bars { display: grid; grid-template-columns: repeat(calc(var(--n) * 2), minmax(0, 1fr)); height: 52px; align-items: center; position: relative;
      background: repeating-linear-gradient(90deg, transparent 0 calc(100% / var(--n) - 1px), color-mix(in srgb, var(--sm-line) 75%, transparent) calc(100% / var(--n) - 1px) calc(100% / var(--n))); }
    .multi .bars { height: 44px; border-bottom: 1px solid var(--sm-line); }
    .mon { font-size: .76rem; font-weight: 650; color: var(--sm-muted); border-left: 1px solid var(--sm-line); padding-left: 5px; white-space: nowrap; height: 18px; }
    .day { text-align: center; padding: 4px 0 6px; display: flex; flex-direction: column; font-size: .74rem; line-height: 1.2; border-bottom: 1px solid var(--sm-line); }
    .day .w { color: var(--sm-muted); font-size: .66rem; }
    .day.we { background: var(--sm-surf2); }
    .day.today { color: var(--sm-accent); font-weight: 700; }
    .now { grid-row: 1; grid-column: 2 / 3; width: 2px; height: 100%; background: var(--sm-accent); z-index: 2; justify-self: start; margin-left: -1px; }
    .bar { grid-row: 1; height: 38px; margin: 0 1px; border-radius: var(--sm-rs); background: color-mix(in srgb, var(--c) 15%, var(--sm-surf));
      border: 1px solid color-mix(in srgb, var(--c) 55%, transparent); border-left: 4px solid var(--c); padding: 2px 8px; display: flex;
      flex-direction: column; justify-content: center; overflow: hidden; min-width: 0; cursor: pointer; }
    .multi .bar { height: 32px; }
    .bar:hover { background: color-mix(in srgb, var(--c) 26%, var(--sm-surf)); }
    .bar.cut { border-left-style: dashed; border-top-left-radius: 0; border-bottom-left-radius: 0; margin-left: 0; padding-left: 12px; }
    .bar.cr { border-top-right-radius: 0; border-bottom-right-radius: 0; margin-right: 0; }
    .bar.blk { background: repeating-linear-gradient(135deg, color-mix(in srgb, var(--sm-block) 35%, transparent) 0 3px, transparent 3px 8px);
      border-color: var(--sm-block); align-items: center; }
    .bn { font-size: .8rem; font-weight: 650; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .bs { font-size: .7rem; color: var(--sm-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .pr { font-size: .68rem; color: var(--sm-muted); text-align: center; padding-top: 4px; min-height: 18px; }
    .pr.bad { color: var(--sm-bad); }
    /* Kennzahlen als eine Leiste */
    .kpis { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); background: var(--sm-surf); border: 1px solid var(--sm-line);
      border-radius: var(--sm-r); padding: 6px 0; margin-bottom: var(--sm-gap); }
    @media (max-width: 1100px) { .kpis { grid-template-columns: repeat(3, minmax(0, 1fr)); } .kpi:nth-child(4) { border-left: 0; } }
    @media (max-width: 640px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } .kpi:nth-child(odd) { border-left: 0; } .kpi:nth-child(4) { border-left: 1px solid var(--sm-line); } }
    .kpi { padding: 12px 20px; border-left: 1px solid var(--sm-line); min-width: 0; }
    .kpi:first-child { border-left: 0; }
    .kl { font-size: .84rem; color: var(--sm-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .kv { font-size: 1.65rem; font-weight: 650; letter-spacing: -.025em; margin: 3px 0 2px; display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
    .ks { font-size: .8rem; color: var(--sm-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .spark { width: 100%; height: 28px; margin-top: 8px; display: block; }
    .spark polyline { fill: none; stroke: var(--sm-accent); stroke-width: 1.7; vector-effect: non-scaling-stroke; stroke-linejoin: round; }
    .spark circle { fill: var(--sm-accent); }
    .spark polyline.cmp { stroke: var(--sm-muted); stroke-opacity: .45; stroke-width: 1.4; stroke-dasharray: 3 2; }
    .three { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--sm-gap); }
    @media (max-width: 1100px) { .three { grid-template-columns: 1fr 1fr; } }
    @media (max-width: 700px) { .three { grid-template-columns: 1fr; } }
    .li { display: flex; gap: 12px; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--sm-line); }
    .li:last-child { border-bottom: 0; }
    .li.click { cursor: pointer; } .li.click:hover b { color: var(--sm-accent); }
    .li .st { width: 4px; height: 34px; border-radius: 2px; background: var(--c); flex: none; }
    .li .m { flex: 1; min-width: 0; display: flex; flex-direction: column; }
    .li .m span, .li .r span { font-size: .82rem; color: var(--sm-muted); }
    .li .m span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .li .r { text-align: right; display: flex; flex-direction: column; white-space: nowrap; }
    .todo { border-radius: var(--sm-rs); padding: 13px 14px; margin-bottom: 10px; background: var(--sm-surf2); }
    .todo.msg { background: color-mix(in srgb, var(--sm-bad) 7%, var(--sm-surf)); border: 1px solid color-mix(in srgb, var(--sm-bad) 30%, transparent); }
    .todo .tt { font-weight: 650; font-size: .92rem; display: flex; align-items: center; }
    .todo p { margin: 4px 0 10px; font-size: .9rem; color: var(--sm-muted); }
    .todo .ta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .todo .ago { margin-left: auto; font-size: .78rem; color: var(--sm-muted); }
    .todo .amt { font-size: 1.15rem; font-weight: 650; margin-right: auto; }
    /* v1.17.0 (Portal): Brutto nur zur Orientierung – gedämpft, da beim Portal kein Geld offen ist */
    .todo .amt.muted { color: var(--sm-muted); font-weight: 500; font-size: 1rem; }
    .todo p .dot { width: 8px; height: 8px; vertical-align: 1px; }
    .done { color: var(--sm-muted); padding: 14px 0; }
    .foot { font-size: .76rem; color: var(--sm-muted); margin: 10px 2px 0; }
  `;
  async load() {
    const apt = await this.apartment();
    const info = await this.store.getInfo();
    const today = info.heute;
    const tg = this.target;
    const m0 = D(today.slice(0, 8) + "01");
    const apts = this.multi ? info.wohnungen.filter((w) => !tg.entry_id || w.entry_id === tg.entry_id) : [apt];
    const rateEnd = iso(addDays(D(today), Math.max(this._config.gap_days, this._config.band_days) + 21));
    // v1.17.0 (Portal): eigener Abruf nur für „Wartet auf dich“ – Portal-Buchungen ohne price-paid ab dem Anreisetag.
    // Das normale Fenster (ab gestern) enthält schon abgereiste Gäste nicht mehr; es zu verlängern würde Band,
    // Status-Satz, Lücken und Antwortstatus mitverändern. Daher separat: 60 Tage zurück bis morgen, nur Portale
    // (Backend-Filter „portale“ = Kanalgruppe Portal). 60 Tage = genug Puffer für Rechnungen, ohne Altlasten
    // aus Jahren vor der Einführung der Markierung anzuzeigen.
    // v1.18.0: Finanzen nur mit Recht „finanzen“ (sonst bleibt die Übersicht ohne Umsatz-Kacheln nutzbar)
    const fin = can("finanzen", tg.apartment_id);
    const none = Promise.resolve(null);
    const [month, ytd, last12, prevYear, list, portalList, taskState, emp, ...rates] = await Promise.all([
      fin ? this.store.ws("smoobu/analytics", { ...tg, period: "monat", compare: "vorjahr_stand" }) : none,
      fin ? this.store.ws("smoobu/analytics", { ...tg, period: "jahr_bis_heute", compare: "vorjahr" }) : none,
      fin ? this.store.ws("smoobu/analytics", { ...tg, start: iso(addMonths(m0, -11)), end: iso(addMonths(m0, 1)), compare: "vorjahr" }) : none,
      fin ? this.store.ws("smoobu/analytics", { ...tg, period: "vorjahr", compare: "kein" }).catch(() => null) : none,
      this.store.ws("smoobu/bookings", { ...tg, start: iso(addDays(D(today), -1)), end: iso(addDays(D(today), 180)) }),
      this.store.ws("smoobu/bookings", { ...tg, start: iso(addDays(D(today), -60)), end: iso(addDays(D(today), 1)), channels: ["portale"] })
        .then((r) => r.buchungen).catch(() => []),
      // v1.18.0: Aufgaben-Board – erledigt/später (Backend) und Preis-/Last-Minute-/Lücken-Aufgaben aus der Empfehlung
      this.store.ws("smoobu/tasks/get", tg, { cache: false }).catch(() => ({ zustand: {}, kategorien: [] })),
      fin ? this.store.ws("smoobu/stats", { ...tg, mode: "empfehlung" }).catch(() => null) : none,
      ...apts.map((w) => this.store.ws("smoobu/rates", { ...tg, apartment_id: w.apartment_id, start: today, end: rateEnd })
        .then((r) => r.preise).catch(() => ({}))),
    ]);
    const bookings = list.buchungen.filter((b) => !(b.storniert));
    // Wer wartet auf eine Antwort? (laufende + kommende Gäste, Backend cacht 10 min)
    const ids = bookings.filter((b) => !b.blockiert && (b.status === "laufend" || b.status === "kommend")).slice(0, 60).map((b) => b.id);
    let status = {};
    if (ids.length) {
      try { status = (await this.store.ws("smoobu/message_status", { ...tg, reservation_ids: ids }, { cache: false })).status || {}; }
      catch (e) { status = {}; }
    }
    const ratesBy = Object.fromEntries(apts.map((w, i) => [w.apartment_id, rates[i] || {}]));
    // Anreise ≤ heute, nicht storniert/gesperrt, ohne offenen Betrag (sonst normaler Weg) und noch nicht markiert
    const portalOpen = portalList.filter((b) => !b.storniert && !b.blockiert && portalPay(b) && !b.bezahlt && b.anreise <= today);
    return { apt, apts, info, today, month, ytd, last12, prevYear, bookings, status, ratesBy, portalOpen, taskState, emp, fin };
  }

  // ---- Kopf ----------------------------------------------------------------
  heroSingle(d) {
    const { apt, today, bookings, month, status } = d;
    const cur = apt.currency;
    const s = stayStatus(apt, bookings, today, nowHM(this._hass));
    const open = bookings.filter((b) => status[b.id]?.offen);
    const dm = month?.veraenderung_prozent?.brutto;
    const lead2 = !month ? "" : `${monthName(today)}: ${money(month.brutto, cur)} gebucht${dm !== null && dm !== undefined ? `, ${dm >= 0 ? "+" : "−"}${num(Math.abs(dm), 0)} % ggü. dem Buchungsstand des Vorjahres` : ""}. Auslastung ${pct(month.auslastung_prozent, 0)}.`;
    const guestCard = (b, label) => {
      if (!b) return `<div class="guest none"><div class="gl">${t(label)}</div><div class="gm">${t("keine")}</div></div>`;
      const portal = b.gruppe === "Portal";
      const note = b.hund ? `<div class="note">🐕 ${esc(b.hund_hinweis || t("Hund dabei"))}</div>`
        : b.offen > 0 && !portal ? `<div class="note bad">${t("Offen")} ${money(b.offen, cur, 2)}</div>`
        : portal ? `<div class="note">${t("Bezahlt über")} ${esc(chn(b.kanal))}</div>` : "";
      const isNext = label === "Nächster Gast";
      const when = isNext ? `, ${daysWord(nightsBetween(today, b.anreise))}` : "";
      return `<div class="guest" data-id="${b.id}" style="--c:${colorOf(apt, b.kanal)}">
        <div class="gl">${t(label)}${when}</div><div class="gn">${esc(b.gast || "–")}${b.hund ? " 🐕" : ""}</div>
        <div class="gm">${fdowLong(b.anreise)} bis ${fdowLong(b.abreise)}<br>${plural(b.naechte, t("Nacht"), t("Nächte"))}, ${plural(b.personen, t("Person"), t("Personen"))}<br>
          ${isNext ? `${t("Ankunft")} ${uhr(b.check_in || apt.check_in) || "–"}` : `${t("Abreise bis")} ${uhr(b.check_out || apt.check_out || "11:00")}`}</div>${note}
        <div class="gf"><span class="dot" style="background:${colorOf(apt, b.kanal)}"></span>${esc(chn(b.kanal))}<b>${money(b.brutto, cur)}</b></div></div>`;
    };
    const curLabel = s.current && s.current.abreise === today ? "Reist heute ab" : "Aktueller Gast";
    return `<section class="hero">
      <div><div class="h-state"><span class="pill ${s.key}">${s.pill}</span><span>${fdate(today, { weekday: "long", day: "numeric", month: "long", year: "numeric" })}</span></div>
        <h1>${s.title}</h1><p class="lead">${s.text}</p><p class="lead2">${lead2}</p>
        <div class="events">${this.events(d, open)}</div></div>
      <div class="guests">${guestCard(s.current, curLabel)}${guestCard(s.next, "Nächster Gast")}</div></section>`;
  }
  heroMulti(d) {
    const { apts, today, bookings, status } = d;
    const per = apts.map((w) => ({ w, s: stayStatus(w, bookings.filter((b) => b.wohnung_id === w.apartment_id), today, nowHM(this._hass)) }));
    // „belegt“ = für die kommende Nacht ist ein Gast da (bleibt, reist an oder Wechsel)
    const busy = per.filter((p) => ["occ", "arr", "chg"].includes(p.s.key)).length;
    const arrN = bookings.filter((b) => !b.blockiert && b.anreise === today).length;
    const depN = bookings.filter((b) => !b.blockiert && b.abreise === today).length;
    const open = bookings.filter((b) => status[b.id]?.offen);
    const parts = [];
    if (arrN) parts.push(plural(arrN, "Anreise", "Anreisen"));
    if (depN) parts.push(plural(depN, "Abreise", "Abreisen"));
    const lead = `${parts.length ? `Heute ${parts.join(" und ")}.` : "Heute keine An- oder Abreise."}${open.length ? ` ${plural(open.length, "Nachricht", "Nachrichten")} unbeantwortet.` : ""}`;
    const short = (p) => {
      // v1.17.1: uhrzeitgenau über s.ev (current/next ändern sich mit Check-in/-out, können also leer sein)
      const s = p.s, c = s.current, n = s.next, e = s.ev || {};
      const ci = (b) => uhr(b.check_in || p.w.check_in || "16:00");
      if (s.key === "chg") return e.arrived ? `${esc(e.dep.gast)} abgereist, ${esc(e.arr.gast)} seit ${ci(e.arr)} da`
        : `${esc(e.dep.gast)} ${e.departed ? "abgereist" : "reist ab"}, ${esc(e.arr.gast)} kommt um ${ci(e.arr)}`;
      if (s.key === "dep") return `${esc(e.dep.gast)} ${e.departed ? "abgereist" : "reist heute ab"}${n ? `, nächste Anreise ${fdowLong(n.anreise)}` : ""}`;
      if (s.key === "arr") return e.arrived ? `${esc(e.arr.gast)} seit ${ci(e.arr)} da, bis ${fdowLong(e.arr.abreise)}` : `${esc(e.arr.gast)} kommt um ${ci(e.arr)}`;
      if (s.key === "occ") return `${esc(c.gast)} bis ${fdowLong(c.abreise)}`;
      return n ? `Frei bis ${fdowLong(n.anreise)}, dann ${esc(n.gast)}` : t("Keine Buchung in den nächsten 6 Monaten.");
    };
    return `<section class="hero">
      <div><div class="h-state"><span>${fdate(today, { weekday: "long", day: "numeric", month: "long", year: "numeric" })}</span></div>
        <h1>${busy} von ${apts.length} belegt</h1><p class="lead">${lead}</p>
        <div class="events">${this.events(d, open)}</div></div>
      <div class="panel apts">${per.map((p) => `<div class="aptrow" data-apt="${p.w.apartment_id}"><span class="ak">${esc(p.w.kuerzel)}</span>
        <div class="an"><b>${esc(p.w.name)}</b><span>${short(p)}</span></div><span class="pill ${p.s.key}">${p.s.pill}</span></div>`).join("")}</div></section>`;
  }
  events({ apt, today, bookings }, open) {
    const guests = bookings.filter((b) => !b.blockiert);
    const arr = guests.filter((b) => b.anreise === today), dep = guests.filter((b) => b.abreise === today);
    const out = [];
    for (const b of dep) out.push(`<span class="ev click" data-id="${b.id}"><ha-icon icon="mdi:airplane-takeoff"></ha-icon>${t("Abreise")} ${esc(b.gast)} ${t("bis")} ${uhr(b.check_out || apt.check_out || "11:00")}${this.code(b)}</span>`);
    for (const b of arr) out.push(`<span class="ev click" data-id="${b.id}"><ha-icon icon="mdi:airplane-landing"></ha-icon>${t("Anreise")} ${esc(b.gast)}${b.hund ? " 🐕" : ""} ${uhr(b.check_in || apt.check_in || "16:00")}${this.code(b)}</span>`);
    if (!this.multi) {
      const nextDep = guests.find((b) => b.abreise > today);
      if (!dep.length && nextDep) out.push(`<span class="ev"><ha-icon icon="mdi:broom"></ha-icon>${t("Reinigung")} ${fdowLong(nextDep.abreise)} ${t("ab")} ${uhr(nextDep.check_out || apt.check_out || "11:00")}</span>`);
    }
    if (!arr.length && !dep.length) out.unshift(`<span class="ev muted">${t("Heute keine An- oder Abreise")}</span>`);
    if (open.length) out.push(`<span class="ev bad click" data-id="${open[0].id}">💬 ${plural(open.length, t("Nachricht"), t("Nachrichten"))} ${t("unbeantwortet")}</span>`);
    for (const e of this._config.entities || []) {
      const id = typeof e === "string" ? e : e.entity;
      const st = this._hass.states[id];
      if (!st) continue;
      const name = (typeof e === "object" && e.name) || st.attributes.friendly_name || id;
      const val = this._hass.formatEntityState ? this._hass.formatEntityState(st) : st.state;
      out.push(`<span class="ev click" data-entity="${esc(id)}"><ha-icon icon="${esc(st.attributes.icon || "mdi:information-outline")}"></ha-icon>${esc(name)}: <b>${esc(val)}</b></span>`);
    }
    return out.join("");
  }

  // ---- Belegungsband -------------------------------------------------------
  band(d) {
    const { apts, today, bookings, ratesBy } = d;
    const n = Number(this._config.band_days) || 42;
    const start = D(today);
    const end = addDays(start, n);
    let months = "", days = "";
    for (let i = 0; i < n; i++) {
      const day = addDays(start, i);
      if (i === 0 || day.getDate() === 1) months += `<div class="mon" style="grid-column:${i + 1} / span ${Math.min(6, n - i)}">${day.toLocaleDateString(locale(), { month: "short", year: "numeric" })}</div>`;
      days += `<div class="day ${day.getDay() % 6 === 0 ? "we" : ""} ${i === 0 ? "today" : ""}" style="grid-column:${i + 1}"><span>${day.getDate()}</span>
        <span class="w">${day.toLocaleDateString(locale(), { weekday: "narrow" })}</span></div>`;
    }
    const barsFor = (apt, list) => list.filter((b) => b.abreise > today && D(b.anreise) < end).map((b) => {
      const s = Math.max(nightsBetween(today, b.anreise), 0), e = Math.min(nightsBetween(today, b.abreise), n);
      const cut = b.anreise < today, cr = D(b.abreise) > end;
      const cs = cut ? 1 : 2 * s + 2, ce = cr ? 2 * n + 1 : 2 * e + 2;
      if (b.blockiert) return `<div class="bar blk ${cut ? "cut" : ""} ${cr ? "cr" : ""}" data-id="${b.id}" style="grid-column:${cs} / ${ce}" title="${esc(b.notiz || t("Gesperrt"))}"><span class="bn">🔒</span></div>`;
      const sub = this.multi ? "" : `<span class="bs">${plural(b.naechte, t("Nacht"), t("Nächte"))}, ${money(b.brutto, apt.currency)}</span>`;
      return `<div class="bar ${cut ? "cut" : ""} ${cr ? "cr" : ""}" data-id="${b.id}" style="grid-column:${cs} / ${ce};--c:${colorOf(apt, b.kanal)}"
        title="${esc(`${b.gast} · ${chn(b.kanal)} · ${fdate(b.anreise)} – ${fdate(b.abreise)}`)}"><span class="bn">${esc(b.gast)}${b.hund ? " 🐕" : ""}</span>${sub}</div>`;
    }).join("");
    const prices = (apt, list) => {
      const occ = new Set();
      for (const b of list) for (let x = D(b.anreise); x < D(b.abreise); x = addDays(x, 1)) occ.add(iso(x));
      let out = "";
      for (let i = 0; i < n; i++) {
        const ds = iso(addDays(start, i));
        const r = ratesBy[apt.apartment_id]?.[ds];
        if (occ.has(ds) || !r?.price) continue;
        out += `<div class="pr ${r.available === 0 ? "bad" : ""}" style="grid-column:${i + 1}" title="${esc(`${fdate(ds)}: ${money(r.price, apt.currency)}${r.min_length_of_stay > 1 ? ` · min. ${r.min_length_of_stay}` : ""}`)}">${num(r.price)}</div>`;
      }
      return out;
    };
    const legend = (this.multi ? d.info.wohnungen.flatMap((w) => w.kanaele) : apts[0].kanaele)
      .filter((c, i, a) => a.findIndex((x) => x.name === c.name) === i)
      .map((c) => `<span><i class="dot" style="background:${chColor(c.name)}"></i>${esc(chn(c.name))}</span>`).join("")
      + `<span><i class="dot hatch"></i>${t("Gesperrt")}</span>`;
    const rows = apts.map((w) => {
      const list = bookings.filter((b) => !this.multi || b.wohnung_id === w.apartment_id);
      return `<div class="rrow"><div class="rlab" title="${esc(w.name)}">${this.multi ? `<span class="ak">${esc(w.kuerzel)}</span><span class="nm">${esc(w.name)}</span>` : ""}</div>
        <div class="bars" style="--n:${n}"><div class="now"></div>${barsFor(w, list)}</div></div>
        ${this.multi ? "" : `<div class="rrow"><div></div><div class="cols" style="--n:${n}">${prices(w, list)}</div></div>`}`;
    }).join("");
    return `<section class="panel band"><div class="ph"><h2>${t("Die nächsten")} ${Math.round(n / 7)} ${t("Wochen")}</h2><div class="legend">${legend}</div></div>
      <div class="scroll"><div class="rib ${this.multi ? "multi" : ""}" style="--lab:${this.multi ? "170px" : "0px"}">
        <div class="rrow"><div></div><div class="cols" style="--n:${n}">${months}</div></div>
        <div class="rrow"><div></div><div class="cols" style="--n:${n}">${days}</div></div>${rows}</div></div></section>`;
  }

  // ---- Kennzahlen ----------------------------------------------------------
  kpis({ apt, apts, today, month, ytd, last12, prevYear }) {
    const cur = apt.currency;
    const units = apts.length;
    const empty = { labels: [], brutto: [], netto: [], naechte: [], kanaele: {} };
    const dim = (lab) => { const [y, m] = lab.split("-").map(Number); return new Date(y, m, 0).getDate(); };
    const groups = Object.fromEntries([...Object.entries(last12.vergleich?.kanaele || {}), ...Object.entries(last12.kanaele || {})]
      .map(([k, v]) => [k, v.gruppe]));
    // Monatsreihe → Auslastung, Netto je Nacht, Direktanteil (gleiche Rechnung für Ist und Vorjahr)
    const derive = (r) => ({
      brutto: r.brutto,
      occ: r.labels.map((lab, i) => (r.naechte[i] / (dim(lab) * units)) * 100),
      npn: r.labels.map((_, i) => (r.naechte[i] ? r.netto[i] / r.naechte[i] : null)),
      direct: r.labels.map((_, i) => {
        const tot = r.brutto[i];
        if (!tot) return null;
        return (Object.entries(r.kanaele).reduce((a, [k, vals]) => a + (groups[k] === "Direkt" ? vals[i] || 0 : 0), 0) / tot) * 100;
      }),
    });
    const cumul = (a) => { let s = 0; return (a || []).map((v) => (s += v || 0)); };
    const now = derive(last12.reihe || empty);
    const prev = derive(last12.vergleich?.reihe || empty);
    // Jahr bis heute: kumuliert ggü. gleichem Zeitraum Vorjahr; Prognose: ggü. ganzem Vorjahr (wohin es lief)
    const cum = cumul(ytd.reihe?.brutto);
    const cumPrev = cumul(ytd.vergleich?.reihe?.brutto);
    const cumPrevYear = cumul(prevYear?.reihe?.brutto);
    const monthly = (ytd.reihe?.einheit || "monat") === "monat";
    const chans = Object.values(ytd.kanaele || {});
    const portals = chans.filter((v) => v.gruppe === "Portal");
    const pb = portals.reduce((a, v) => a + v.brutto, 0), pk = portals.reduce((a, v) => a + v.kosten, 0);
    const db = chans.filter((v) => v.gruppe === "Direkt").reduce((a, v) => a + v.brutto, 0);
    const saved = pb ? (db * pk) / pb : null;
    const prog = ytd.prognose || {};
    const pyTotal = prevYear?.brutto;
    const progDelta = pyTotal ? ((prog.prognose - pyTotal) / pyTotal) * 100 : null;
    const year = today.slice(0, 4);
    const k = (l, v, dlt, s, sp, cmp) => `<div class="kpi"><div class="kl">${l}</div><div class="kv">${v}${dlt}</div><div class="ks">${s}</div>${sparkline(sp, cmp)}</div>`;
    return `<section class="kpis">
      ${k(`${monthName(today)} ${t("brutto")}`, money(month.brutto, cur), delta(month.veraenderung_prozent?.brutto),
        `${t("ggü. Buchungsstand")} ${fdate(month.stichtag_vergleich, { day: "2-digit", month: "2-digit", year: "numeric" })}`, now.brutto, prev.brutto)}
      ${k(`${t("Auslastung")} ${monthName(today)}`, pct(month.auslastung_prozent, 0), delta(month.veraenderung_punkte?.auslastung_prozent, "pp"),
        `${num(month.naechte)} von ${num((month.tage || 30) * units)} ${t("Nächten")}`, now.occ, prev.occ)}
      ${k(t("Jahr bis heute"), money(ytd.brutto, cur), delta(ytd.veraenderung_prozent?.brutto), `${t("netto")} ${money(ytd.netto, cur)}`, cum, cumPrev)}
      ${k(`${t("Prognose")} ${year}`, money(prog.prognose, cur), delta(progDelta), `${money(prog.gebucht, cur)} ${t("schon gebucht")}`, cum, monthly ? cumPrevYear : null)}
      ${k(t("Netto je Nacht"), money(ytd.netto_pro_nacht, cur), delta(ytd.veraenderung_prozent?.netto_pro_nacht),
        `${t("Vorjahr")} ${money(ytd.vergleich?.netto_pro_nacht, cur)}`, now.npn, prev.npn)}
      ${k(t("Direktanteil"), pct(ytd.direktanteil_prozent, 0), delta(ytd.veraenderung_punkte?.direktanteil_prozent, "pp"),
        saved ? `${t("spart rund")} ${money(saved, cur)} ${t("Provision")}` : t("Anteil am Umsatz"), now.direct, prev.direct)}
    </section>`;
  }

  // ---- Listen --------------------------------------------------------------
  lists(d) {
    const { apt, apts, today, bookings, status, ratesBy, portalOpen = [] } = d;
    const cur = apt.currency;
    const guests = bookings.filter((b) => !b.blockiert);
    const next = guests.filter((b) => b.anreise >= today && b.anreise > (this.multi ? "" : today)).slice(0, this._config.upcoming);
    const arrivals = next.map((b) => `<div class="li click" data-id="${b.id}" style="--c:${colorOf(apt, b.kanal)}"><span class="st"></span>
      <div class="m"><b>${esc(b.gast)}${b.hund ? " 🐕" : ""}${this.code(b)}</b><span>${fdowLong(b.anreise)} bis ${fdowLong(b.abreise)}, ${plural(b.naechte, t("Nacht"), t("Nächte"))}, ${plural(b.personen, t("Person"), t("Personen"))}</span></div>
      <div class="r"><b>${money(b.brutto, cur)}</b><span>${daysWord(nightsBetween(today, b.anreise))}</span></div></div>`).join("");
    const gaps = apts.flatMap((w) => findGaps(bookings.filter((b) => !this.multi || b.wohnung_id === w.apartment_id), ratesBy[w.apartment_id], today, this._config.gap_days)
      .map((g) => ({ ...g, w })))
      .sort((a, b) => a.von.localeCompare(b.von)).slice(0, 6);
    const gapRows = gaps.map((g) => {
      const prices = [];
      for (let x = D(g.von); x < D(g.bis); x = addDays(x, 1)) { const p = ratesBy[g.w.apartment_id]?.[iso(x)]?.price; if (p) prices.push(p); }
      const lo = Math.min(...prices), hi = Math.max(...prices);
      const pr = prices.length ? (lo === hi ? money(lo, cur) : `${num(lo)}–${money(hi, cur)}`) : "";
      return `<div class="li"><div class="m"><b>${fdowLong(g.von)} bis ${fdowLong(g.bis)}${this.multi ? codeTag(g.w.kuerzel) : ""}</b>
        <span>${plural(g.naechte, t("Nacht"), t("Nächte"))} frei${g.buchbar ? (pr ? `, ${pr}` : "") : `, ${t("Mindestaufenthalt")} ${g.min}`}</span></div>
        ${g.buchbar || !this.kalenderPath ? "" : `<button class="lnk" data-fix="${g.w.apartment_id}|${g.von}|${iso(addDays(D(g.bis), -1))}|${g.naechte}"
          title="${t("Im Belegungsplan Mindestaufenthalt oder Preis setzen")}">${t("Anpassen")}</button>`}
        <span class="badge ${g.buchbar ? "good" : "bad"}">${t(g.buchbar ? "buchbar" : "nicht buchbar")}</span></div>`;
    }).join("");
    const open = guests.filter((b) => status[b.id]?.offen);
    // Offene Zahlungen: laufende und Anreisen der nächsten 30 Tage zuerst (max. 3), Rest als Summe
    const unpaidAll = guests.filter((b) => b.offen > 0 && b.gruppe !== "Portal" && b.status !== "vergangen");
    const soon = iso(addDays(D(today), 30));
    const unpaid = unpaidAll.filter((b) => b.anreise <= soon).slice(0, 3);
    // v1.17.0 (Portal): Portal-Buchungen ohne Markierung ab dem Anreisetag, älteste zuerst (Rechnung am längsten
    // fällig), max. 3 – Rest als Anzahl/Summe-Zeile wie „Später fällig“
    const portalAll = [...portalOpen].sort((a, b) => a.anreise.localeCompare(b.anreise) || a.id - b.id);
    // v1.17.0: für die Buttons „✓ Erhalten“ / „✓ Anzahlung“ (bind sucht die Buchung per ID)
    this._payBookings = new Map([...unpaid, ...portalAll].map((b) => [b.id, b]));
    this._payCur = cur;
    const later = unpaidAll.filter((b) => !unpaid.includes(b));
    const ago = (s) => {
      if (!s) return "";
      const ms = Date.now() - new Date(String(s).replace(" ", "T")).getTime();
      if (isNaN(ms)) return "";
      if (ms < 0) return fdowLong(s);
      const h = Math.round(ms / 3600000);
      const dd = Math.round(h / 24);
      if (LANG !== "de") return h < 1 ? t("gerade eben") : h < 24 ? `${h} h ago` : `${dd} ${dd === 1 ? "day" : "days"} ago`;
      return h < 1 ? t("gerade eben") : h < 24 ? `vor ${h} Std.` : `vor ${dd} ${dd === 1 ? "Tag" : "Tagen"}`;
    };
    // v1.18.0: Aufgaben-Board „Wartet auf dich“ (Wunsch Betreiber 17.11.2026): Reiter mit Zählern je Kategorie,
    // „✓ Erledigt“ / „Später“ je Aufgabe (im Backend gespeichert, für alle Benutzer gleich). Der Schlüssel
    // enthält, was die Aufgabe ausmacht (z. B. Zeitpunkt der letzten Gastnachricht, empfohlener Preis) –
    // ändert sich das, erscheint die Aufgabe wieder. Kategorien sind in den Einstellungen wählbar.
    const tasks = [];
    const add = (cat, key, html, sort) => tasks.push({ cat, key, html, sort: sort || "9" });
    open.forEach((b) => add("nachrichten", `msg:${b.id}:${status[b.id].letzte_zeit || ""}`, `<div class="tt">${esc(b.gast)} ${t("wartet auf Antwort")}${this.code(b)}</div>
        ${status[b.id].letzte_text ? `<p>„${esc(status[b.id].letzte_text)}“</p>` : "<p></p>"}
        <div class="ta"><button class="btn" data-id="${b.id}">${t("Antworten")}</button><span class="ago">${ago(status[b.id].letzte_zeit)}</span>`, "0"));
    // Portal-Rechnung noch nicht als erhalten markiert (Anreise erreicht) – älteste zuerst
    portalAll.forEach((b) => add("rechnungen", `rechnung:${b.id}`, `<div class="tt">${t("Nicht als erhalten markiert")}${this.code(b)}
        <button class="lnk" style="margin-left:auto" data-id="${b.id}">${t("Buchung öffnen")}</button></div>
        <p>${esc(b.gast)}, ${t("Anreise")} ${fdowLong(b.anreise)} · <span class="dot" style="background:${colorOf(apt, b.kanal)}"></span> ${esc(chn(b.kanal))}</p>
        <div class="ta"><span class="amt muted">${money(b.brutto, cur, 2)}</span>
          <button class="btn" data-pay="zahlung" data-pid="${b.id}">✓ ${t("Erhalten")}</button>`, `1${b.anreise}`));
    unpaid.forEach((b) => { const p = payInfo(b); add("rechnungen", `zahlung:${b.id}`, `<div class="tt">${t("Zahlung offen")}${this.code(b)}
        <button class="lnk" style="margin-left:auto" data-id="${b.id}">${t("Buchung öffnen")}</button></div>
        <p>${esc(b.gast)}, ${t("Anreise")} ${fdowLong(b.anreise)}${p.canPre ? ` · ${t("Anzahlung")} ${money(p.pre, cur, 2)} ${t("offen")}` : ""}</p>
        <div class="ta"><span class="amt">${money(b.offen, cur, 2)}</span>
          ${p.canPre ? `<button class="btn flat" data-pay="anzahlung" data-pid="${b.id}">✓ ${t("Anzahlung")}</button>` : ""}
          <button class="btn" data-pay="zahlung" data-pid="${b.id}">✓ ${t("Erhalten")}</button>`, `2${b.anreise}`); });
    // Preise, Last-Minute, Lücken aus der Empfehlung (nur mit Recht „preise“: ohne lassen sie sich nicht erledigen)
    this._taskApplies = [];
    const applyBtn = (label, cfg, primary = true) => {
      this._taskApplies.push(cfg);
      return `<button class="btn ${primary ? "" : "flat"}" data-tapply="${this._taskApplies.length - 1}">${esc(t(label))}</button>`;
    };
    for (const w of d.emp?.wohnungen || []) {
      if (!w.darf_aendern) continue;
      const ctx = { apt: w.apartment_id, cur, kanaele: w.kanaele, basis: w.basispreis?.heute };
      const tag = this.multi ? codeTag(aptCode(d.info, w.apartment_id)) : "";
      for (const mo of w.monate || []) {
        const e = mo.empfehlung || {};
        if (!e.preis_neu || e.aktion === "halten") continue;
        const label = D(`${mo.monat}-01`).toLocaleDateString(locale(), { month: "long", year: "numeric" });
        const von = mo.monat + "-01" < today ? today : mo.monat + "-01";
        const bis = iso(addDays(new Date(Number(mo.monat.slice(0, 4)), Number(mo.monat.slice(5, 7)), 1), -1));
        const floors = Object.fromEntries(Object.entries(mo.untergrenze || {}).map(([k, f]) => [k, f["2"]]));
        add("preise", `preis:${w.apartment_id}:${mo.monat}:${e.aktion}:${e.preis_neu}`, `<div class="tt">${esc(label)}: ${e.aktion === "senken" ? t("Preis senken") : t("Preis erhöhen")}${tag}</div>
          <p>${esc(t(e.grund || ""))}</p>
          <div class="ta"><span class="amt">${money(mo.basispreis, cur)} → ${money(e.preis_neu, cur)}</span>
            ${applyBtn("Übernehmen …", { ...ctx, title: `${label}: ${e.aktion === "senken" ? t("Preis senken") : t("Preis erhöhen")}`, grund: e.grund, untergrenze: floors,
              vorgabe: { von, bis, preis: e.preis_neu, ohne_feiertage: e.aktion === "senken", nur_basispreis: true, label: `${label}: ${e.aktion}` } })}`, `3${mo.monat}`);
      }
      for (const h of w.hinweise || []) {
        if (h.typ === "feiertag" && h.tage?.length) add("preise", `feiertag:${w.apartment_id}:${h.tage.map((x) => x.datum).join(",")}`,
          `<div class="tt">${esc(t(h.titel))}${tag}</div><p>${h.tage.map((x) => `${fdate(x.datum)} ${esc(t(x.name))}`).join(" · ")}</p>
          <div class="ta">${applyBtn(`+${h.prozent} % ${t("übernehmen")} …`, { ...ctx, title: h.titel, grund: h.text,
            vorgabe: { tage: h.tage.map((x) => x.datum), prozent: h.prozent, label: h.titel } })}`, `4${h.tage[0].datum}`);
        if (h.typ === "wochenende" && h.prozent) add("preise", `wochenende:${w.apartment_id}:${h.prozent}`,
          `<div class="tt">${esc(t(h.titel))}${tag}</div><p>${esc(t(h.text))}</p>
          <div class="ta">${applyBtn(`Fr/Sa +${h.prozent} % …`, { ...ctx, title: h.titel, grund: h.text,
            vorgabe: { von: today, bis: iso(addDays(D(today), 59)), wochentage: h.wochentage, prozent: h.prozent, nur_basispreis: true, label: h.titel } })}`, "5");
        if (h.typ === "lastminute") for (const x of h.naechte || []) {
          if (!x.vorschlag_preis) continue;
          add("lastminute", `lm:${w.apartment_id}:${x.datum}:${x.vorschlag_preis}`, `<div class="tt">${t("Last-Minute")} ${fdowLong(x.datum)}${tag}</div>
            <p>${esc(t(x.grund))} · ${t("Untergrenze")} ${money(x.untergrenze, cur)}</p>
            <div class="ta"><span class="amt">${money(x.preis, cur)} → ${money(x.vorschlag_preis, cur)}</span>
              ${applyBtn("Übernehmen …", { ...ctx, title: `${t("Last-Minute")} ${fdate(x.datum)}`, grund: x.grund,
                untergrenze: Object.fromEntries((w.kanaele || []).map((k) => [k.kanal, x.untergrenze])),
                vorgabe: { tage: [x.datum], preis: x.vorschlag_preis, label: `Last-Minute ${x.datum}` } })}`, `0${x.datum}`);
        }
        if (h.typ === "luecke") for (const x of h.luecken || []) {
          add("luecken", `luecke:${w.apartment_id}:${x.von}:${x.naechte}`, `<div class="tt">${t("Lücke")} ${fdowLong(x.von)} · ${plural(x.naechte, t("Nacht"), t("Nächte"))}${tag}</div>
            <p>${x.buchbar ? t("Einzelne Nächte zwischen zwei Gästen bucht kaum jemand zum vollen Preis.") : `${t("Mindestaufenthalt")} ${x.mindestaufenthalt} – ${t("so nicht buchbar")}`}</p>
            <div class="ta"><span class="amt">${money(x.preis, cur)}${x.vorschlag_preis ? ` → ${money(x.vorschlag_preis, cur)}` : ""}</span>
              ${applyBtn("Anpassen …", { ...ctx, title: `${t("Lücke")} ${fdate(x.von)}`, grund: "",
                untergrenze: Object.fromEntries((w.kanaele || []).map((k) => [k.kanal, x.untergrenze])),
                vorgabe: { tage: x.tage, preis: x.vorschlag_preis, mindestaufenthalt: x.buchbar ? null : x.naechte, label: `Lücke ${x.von}` } })}`, `6${x.von}`);
        }
      }
    }
    const zustand = d.taskState?.zustand || {};
    const cats = (d.taskState?.kategorien?.length ? d.taskState.kategorien : TASK_CATS.map(([k]) => k));
    const visible = tasks.filter((x) => cats.includes(x.cat) && !zustand[x.key]).sort((a, b) => a.sort.localeCompare(b.sort));
    const hidden = tasks.filter((x) => cats.includes(x.cat) && zustand[x.key]).length;
    const sel = cats.includes(this._state.taskTab) ? this._state.taskTab : "alle";
    const count = (c) => visible.filter((x) => x.cat === c).length;
    const chipsHtml = `<div class="tchips"><button data-ttab="alle" aria-pressed="${sel === "alle"}">${t("Alle")} <b>${visible.length}</b></button>${TASK_CATS
      .filter(([k]) => cats.includes(k)).map(([k, l]) => `<button data-ttab="${k}" aria-pressed="${sel === k}">${t(l)}${count(k) ? ` <b>${count(k)}</b>` : ""}</button>`).join("")}</div>`;
    // „Alle“: je Kategorie höchstens 2 (Spalte bleibt kurz), dann Hinweis auf den Reiter
    let shown = visible.filter((x) => sel === "alle" || x.cat === sel);
    const more = [];
    if (sel === "alle") {
      const per = {};
      shown = shown.filter((x) => { per[x.cat] = (per[x.cat] || 0) + 1; return per[x.cat] <= 2; });
      for (const [k, l] of TASK_CATS) if (count(k) > 2) more.push(`<button class="lnk" data-ttab="${k}">${t(l)}: ${t("weitere")} ${count(k) - 2}</button>`);
    }
    const catLabel = Object.fromEntries(TASK_CATS);
    const todo = shown.map((x) => `<div class="todo ${x.cat === "nachrichten" ? "msg" : ""}" data-cat="${x.cat}">${sel === "alle" ? `<span class="tcat">${t(catLabel[x.cat])}</span>` : ""}${x.html}
        <span class="tact"><button class="lnk" data-tdone="${esc(x.key)}" data-tcat="${x.cat}" title="${t("Als erledigt ausblenden")}">✓ ${t("Erledigt")}</button>
        <button class="lnk" data-tlater="${esc(x.key)}" data-tcat="${x.cat}" title="${t("Morgen wieder zeigen")}">${t("Später")}</button></span></div></div>`).join("")
      + (sel === "alle" || sel === "rechnungen" ? (later.length ? `<div class="sub" style="padding:4px 2px">${t("Später fällig")}: ${plural(later.length, t("Buchung"), t("Buchungen"))}, ${money(later.reduce((a, b) => a + b.offen, 0), cur, 2)}</div>` : "") : "")
      + (more.length ? `<div class="sub" style="padding:4px 2px">${more.join(" · ")}</div>` : "")
      + (hidden ? `<div class="sub" style="padding:4px 2px">${hidden} ${t("erledigt bzw. später – ausgeblendet")}</div>` : "");
    return `<section class="three">
      <div class="panel"><div class="ph"><h2>${t("Nächste Anreisen")}</h2></div>${arrivals || `<div class="done">${t("Keine Anreisen geplant.")}</div>`}</div>
      <div class="panel"><div class="ph"><h2>${t("Freie Zeiträume")}</h2><span class="sub">${t("nächste")} ${this._config.gap_days} ${t("Tage")}</span></div>${gapRows || `<div class="done">${t("Keine Lücken.")}</div>`}</div>
      <div class="panel"><div class="ph"><h2>${t("Wartet auf dich")}</h2></div>${chipsHtml}${todo || `<div class="done">✓ ${t("Alles erledigt.")}</div>`}</div></section>`;
  }

  body(d) {
    const { month, ytd, today } = d;
    if (!d.fin) return `${this.multi ? this.heroMulti(d) : this.heroSingle(d)}${this.band(d)}${this.lists(d)}`;
    return `${this.multi ? this.heroMulti(d) : this.heroSingle(d)}${this.band(d)}${this.kpis(d)}${this.lists(d)}
      <p class="foot">${t("Vergleich")}: ${monthName(today)} ${t("ggü. Buchungsstand am")} ${fdate(month.stichtag_vergleich)},
        ${t("Jahr ggü.")} ${fdate(ytd.vergleich?.von)}–${fdate(iso(addDays(D(ytd.vergleich?.bis || today), -1)))}. ${t("PP = Prozentpunkte")}.
        ${t("Prognose")} = ${t("gebucht + Nachbuchungen wie im Vorjahr")}. ${t("Verläufe: kräftige Linie = letzte 12 Monate bzw. dieses Jahr, blasse Linie = Vorjahr.")}</p>`;
  }
  bind(root) {
    root.querySelectorAll("[data-id]").forEach((el) => el.addEventListener("click", (e) => { e.stopPropagation(); this.openBooking(Number(el.dataset.id)); }));
    // v1.18.0: Aufgaben-Board – Reiter, Übernehmen, Erledigt/Später (gespeichert im Backend)
    root.querySelectorAll("[data-ttab]").forEach((el) => el.addEventListener("click", () => this.setState({ taskTab: el.dataset.ttab })));
    root.querySelectorAll("[data-tapply]").forEach((el) => el.addEventListener("click", async () => {
      const cfg = this._taskApplies?.[Number(el.dataset.tapply)];
      if (cfg && (await priceDialog(this, cfg))) this._reload();
    }));
    const taskSet = async (el, aktion) => {
      el.disabled = true;
      try {
        await this.store.ws("smoobu/tasks/set", { ...this.target, key: el.dataset.tdone || el.dataset.tlater, kategorie: el.dataset.tcat, aktion }, { cache: false });
        toast(aktion === "erledigt" ? `✓ ${t("Erledigt")}` : t("Morgen wieder da"));
        this._reload();
      } catch (e) { el.disabled = false; toast(`${t("Fehler")}: ${e?.message || e}`); }
    };
    root.querySelectorAll("[data-tdone]").forEach((el) => el.addEventListener("click", (e) => { e.stopPropagation(); taskSet(el, "erledigt"); }));
    root.querySelectorAll("[data-tlater]").forEach((el) => el.addEventListener("click", (e) => { e.stopPropagation(); taskSet(el, "spaeter"); }));
    // v1.17.0: Zahlung/Anzahlung direkt als erhalten markieren (Neuladen übernimmt store.service)
    root.querySelectorAll("[data-pay]").forEach((el) => el.addEventListener("click", async (e) => {
      e.stopPropagation();
      const b = this._payBookings?.get(Number(el.dataset.pid));
      if (!b || el.disabled) return;
      el.disabled = true;
      if (!(await markPayment(this.store, b, el.dataset.pay, true, this._payCur))) el.disabled = false;
    }));
    root.querySelectorAll("[data-apt]").forEach((el) => el.addEventListener("click", () => { AptSel.value = Number(el.dataset.apt); }));
    // v1.17.1: nicht buchbare Lücke → Belegungsplan mit markierten Tagen und vorausgefülltem Mindestaufenthalt
    root.querySelectorAll("[data-fix]").forEach((el) => el.addEventListener("click", () => {
      const [apt, von, bis, n] = el.dataset.fix.split("|");
      Preselect.set({ apt: Number(apt), von, bis, min: Number(n) });
      const path = this.kalenderPath;
      const parts = location.pathname.split("/").filter(Boolean);
      history.pushState(null, "", path.startsWith("/") ? path : `/${parts[0] || "lovelace"}/${path}`);
      window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));
    }));
    root.querySelectorAll("[data-entity]").forEach((el) => el.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId: el.dataset.entity }, bubbles: true, composed: true }));
    }));
  }
}

// ===========================================================================
// Belegungsplan mit Preisen
// ===========================================================================
const MONTH_FMT = { month: "short", year: "2-digit" };
class SmoobuTimelineCard extends SmoobuCard {
  static defaults = { title: "", months: 3, show_prices: true, actions: true };
  static initialState = () => ({ offset: 0, selStart: null, selEnd: null, selApt: null, panel: null });
  static css = `
    .months { min-width: 920px; }
    .month { display: grid; grid-template-columns: 78px 1fr; align-items: stretch; border-bottom: 1px solid var(--sm-line); }
    .month:last-child { border-bottom: 0; }
    .ml { font-weight: 650; font-size: .86rem; padding: 8px 8px 0 0; text-transform: capitalize; display: flex; flex-direction: column; gap: 4px; }
    .ml .ak { margin: 0; align-self: flex-start; }
    .arow { display: grid; grid-template-columns: 78px 1fr; }
    .arow + .arow { border-top: 1px dashed var(--sm-line); }
    .days { position: relative; display: grid; grid-template-columns: repeat(31, 1fr); }
    .c { height: 66px; border-left: 1px solid var(--sm-line); font-size: .7rem; padding: 3px 3px 0; cursor: pointer; position: relative;
      color: var(--sm-muted); user-select: none; }
    .multi .c { height: 54px; }
    .c.we { background: var(--sm-surf2); }
    .c.today { box-shadow: inset 0 0 0 2px var(--sm-accent); border-radius: 4px; }
    .c.today .d { color: var(--sm-accent); }
    .c.past { opacity: .5; }
    .c.sel { background: color-mix(in srgb, var(--sm-accent) 22%, transparent); }
    .c.badgap { background: repeating-linear-gradient(45deg, color-mix(in srgb, var(--sm-bad) 14%, transparent) 0 4px, transparent 4px 8px); }
    .c.none { cursor: default; background: none; border-left-color: transparent; }
    .c .d { font-weight: 650; color: var(--sm-ink); }
    .c .p { position: absolute; bottom: 3px; left: 2px; right: 2px; text-align: center; }
    .c .ms { position: absolute; bottom: 16px; left: 2px; right: 2px; text-align: center; font-size: .62rem; }
    .bar { position: absolute; top: 22px; height: 24px; border-radius: 7px; font-size: .74rem; font-weight: 650; line-height: 22px;
      padding: 0 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; color: var(--sm-ink);
      background: color-mix(in srgb, var(--c) 18%, var(--sm-surf)); border: 1px solid color-mix(in srgb, var(--c) 55%, transparent); border-left: 4px solid var(--c); }
    .multi .bar { top: 18px; height: 22px; line-height: 20px; }
    .bar:hover { background: color-mix(in srgb, var(--c) 30%, var(--sm-surf)); }
    .bar.cl { border-top-left-radius: 0; border-bottom-left-radius: 0; border-left-style: dashed; }
    .bar.cr { border-top-right-radius: 0; border-bottom-right-radius: 0; }
    .bar.blocked { background: repeating-linear-gradient(135deg, color-mix(in srgb, var(--sm-block) 35%, transparent) 0 3px, transparent 3px 8px);
      border-color: var(--sm-block); color: var(--sm-muted); }
    .legend { display: flex; flex-wrap: wrap; gap: 14px; font-size: .8rem; color: var(--sm-muted); margin-top: 12px; }
    .legend span { display: inline-flex; gap: 6px; align-items: center; }
    .hatch { background: repeating-linear-gradient(135deg, var(--sm-block) 0 2px, transparent 2px 5px); outline: 1px solid var(--sm-block); }
    .panel { margin-top: 14px; padding: 12px 14px; border-radius: var(--sm-rs); border: 1px solid var(--sm-accent);
      background: color-mix(in srgb, var(--sm-accent) 6%, var(--sm-surf)); display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .panel input { width: 110px; }
  `;
  async load() {
    const apt = await this.apartment();
    const info = await this.store.getInfo();
    const today = info.heute;
    const start = addMonths(D(today.slice(0, 8) + "01"), this._state.offset);
    const end = addMonths(start, Number(this._config.months) || 3);
    const tg = this.target;
    const rs = D(today) > start ? D(today) : start;
    const apts = this.multi ? info.wohnungen.filter((w) => !tg.entry_id || w.entry_id === tg.entry_id) : [apt];
    const [list, ...rates] = await Promise.all([
      this.store.ws("smoobu/bookings", { ...tg, start: iso(start), end: iso(end) }),
      ...apts.map((w) => this._config.show_prices && rs < end
        ? this.store.ws("smoobu/rates", { ...tg, apartment_id: w.apartment_id, start: iso(rs), end: iso(addDays(end, 21)) }).then((r) => r.preise).catch(() => ({}))
        : Promise.resolve({})),
    ]);
    return { apt, apts, today, start, end, bookings: list.buchungen.filter((b) => !b.storniert),
      ratesBy: Object.fromEntries(apts.map((w, i) => [w.apartment_id, rates[i] || {}])) };
  }
  body({ apt, apts, today, start, end, bookings, ratesBy }) {
    const cur = apt.currency;
    // v1.17.1: Vorauswahl aus der Übersicht („Anpassen“ bei nicht buchbarer Lücke) einmalig übernehmen
    const pre = this._config.actions ? Preselect.take() : null;
    if (pre && apts.some((w) => w.apartment_id === pre.apt || !this.multi)) {
      Object.assign(this._state, { selStart: pre.von, selEnd: pre.bis, selApt: this.multi ? pre.apt : null, panel: "rate", preMin: pre.min });
      if (pre.von < iso(start) || pre.von >= iso(end)) Preselect.set(pre); // außerhalb der angezeigten Monate: nicht verbrauchen
    }
    const { selStart, selEnd, selApt } = this._state;
    const lo = selStart && selEnd ? (selStart < selEnd ? selStart : selEnd) : selStart;
    const hi = selStart && selEnd ? (selStart < selEnd ? selEnd : selStart) : selStart;
    const own = (w) => bookings.filter((b) => !this.multi || b.wohnung_id === w.apartment_id);
    // Nächte in Lücken, die wegen Mindestaufenthalt nicht buchbar sind (je Wohnung)
    const bad = {};
    for (const w of apts) {
      bad[w.apartment_id] = new Set();
      for (const g of findGaps(own(w), ratesBy[w.apartment_id], iso(D(today) > start ? D(today) : start), Math.max(nightsBetween(iso(start), iso(end)), 1))) {
        if (!g.buchbar) for (let d = D(g.von); d < D(g.bis); d = addDays(d, 1)) bad[w.apartment_id].add(iso(d));
      }
    }
    const rows = [];
    for (let m = new Date(start); m < end; m = addMonths(m, 1)) {
      const dim = new Date(m.getFullYear(), m.getMonth() + 1, 0).getDate();
      const mStart = iso(m), mEnd = iso(addMonths(m, 1));
      const aptRows = apts.map((w, wi) => {
        const rates = ratesBy[w.apartment_id] || {};
        let cells = "";
        for (let i = 1; i <= 31; i++) {
          if (i > dim) { cells += `<div class="c none"></div>`; continue; }
          const day = new Date(m.getFullYear(), m.getMonth(), i);
          const ds = iso(day);
          const r = rates[ds];
          const isSel = lo && selApt === w.apartment_id && ds >= lo && ds <= (hi || lo);
          const cls = ["c", day.getDay() % 6 === 0 ? "we" : "", ds === today ? "today" : "", ds < today ? "past" : "",
            isSel ? "sel" : "", bad[w.apartment_id].has(ds) ? "badgap" : ""].join(" ");
          const wd = day.toLocaleDateString(locale(), { weekday: "narrow" });
          cells += `<div class="${cls}" data-day="${ds}" data-apt="${w.apartment_id}"><span class="d">${i}</span> ${wd}
            ${r && r.min_length_of_stay > 1 ? `<div class="ms">☾${r.min_length_of_stay}</div>` : ""}
            ${r && r.price ? `<div class="p">${num(r.price)}</div>` : ""}</div>`;
        }
        let bars = "";
        for (const b of own(w)) {
          if (b.abreise <= mStart || b.anreise >= mEnd) continue;
          const a = D(b.anreise), d = D(b.abreise);
          const cutL = b.anreise < mStart, cutR = b.abreise > mEnd;
          const left = cutL ? 0 : (a.getDate() - 1 + 0.55) / 31;
          const right = cutR ? dim / 31 : Math.min((b.abreise === mEnd ? dim + 0.45 : d.getDate() - 1 + 0.45) / 31, 1);
          const label = b.blockiert ? `🔒 ${t("Gesperrt")}${b.notiz ? ", " + esc(b.notiz) : ""}` : `${esc(b.gast || "")}${b.hund ? " 🐕" : ""}`;
          bars += `<div class="bar ${b.blockiert ? "blocked" : ""} ${cutL ? "cl" : ""} ${cutR ? "cr" : ""}" data-id="${b.id}"
            title="${esc(b.blockiert ? t("Sperrzeit") : `${b.gast}, ${b.personen} P., ${chn(b.kanal)}, ${money(b.brutto, cur)}`)}"
            style="left:calc(${(left * 100).toFixed(3)}%);width:calc(${((right - left) * 100).toFixed(3)}%);--c:${colorOf(apt, b.kanal)}">${label}</div>`;
        }
        const lab = `${wi === 0 ? `<span>${m.toLocaleDateString(locale(), MONTH_FMT)}</span>` : ""}${this.multi ? `<span class="ak" title="${esc(w.name)}">${esc(w.kuerzel)}</span>` : ""}`;
        return `<div class="arow"><div class="ml">${lab}</div><div class="days">${cells}${bars}</div></div>`;
      }).join("");
      rows.push(`<div class="month" style="grid-template-columns:1fr">${aptRows}</div>`);
    }
    const nights = lo ? nightsBetween(lo, hi || lo) + 1 : 0;
    const p = this._state.panel;
    const selName = this.multi ? apts.find((w) => w.apartment_id === selApt)?.name : "";
    const panel = !this._config.actions ? "" : lo ? `<div class="panel">
        <b>${selName ? `${esc(selName)}: ` : ""}${fdow(lo)} – ${fdow(hi || lo)} (${plural(nights, t("Nacht"), t("Nächte"))})</b>
        ${p === "block" ? `<input data-k="notice" placeholder="${t("Grund (optional)")}" style="width:180px">
            <button class="btn" data-act="do-block">${t("Sperren")}</button>`
          : p === "rate" ? `<label>${t("Preis/Nacht")} <input data-k="price" type="number" min="1" step="1"></label>
            <label>${t("Mindestaufenthalt")} <input data-k="min" type="number" min="1" max="90" style="width:70px" value="${this._state.preMin || ""}"></label>
            <button class="btn" data-act="do-rate">${t("Speichern")}</button>`
          : `${can("belegung", this.target.apartment_id) ? `<button class="btn" data-act="block">🔒 ${t("Sperren")}</button>` : ""}${can("preise", this.target.apartment_id) ? `<button class="btn" data-act="rate">€ ${t("Preis setzen")}</button>` : ""}`}
        <button class="btn flat" data-act="clear">${t("Abbrechen")}</button></div>`
      : `<div class="legend">${t("Tage markieren: erst ersten, dann letzten Tag antippen")}</div>`;
    const chans = apts.flatMap((w) => w.kanaele).filter((c, i, a) => a.findIndex((x) => x.name === c.name) === i);
    return `
      <div class="head"><h2>${esc(this._config.title || t("Belegungsplan"))}</h2>
        <button class="btn flat" data-act="prev" aria-label="${t("Zurück")}">◀</button><button class="btn flat" data-act="now">${t("Heute")}</button>
        <button class="btn flat" data-act="next" aria-label="${t("Weiter")}">▶</button></div>
      <div class="scroll"><div class="months ${this.multi ? "multi" : ""}">${rows.join("")}</div></div>
      <div class="legend">${chans.map((c) => `<span><span class="dot" style="background:${chColor(c.name)}"></span>${esc(chn(c.name))}</span>`).join("")}
        <span><span class="dot hatch"></span>${t("Gesperrt")}</span>
        <span><span class="dot" style="background:var(--sm-bad)"></span>${t("nicht buchbar")} (${t("Mindestaufenthalt zu hoch")})</span>
        ${this._config.show_prices ? `<span>${t("Zahl unten = Preis/Nacht")}, ☾ = ${t("Mindestaufenthalt")}</span>` : ""}
        ${this.multi ? apts.map((w) => `<span>${codeTag(w.kuerzel)} ${esc(w.name)}</span>`).join("") : ""}</div>
      ${panel}`;
  }
  bind(root) {
    root.querySelectorAll(".bar").forEach((el) => el.addEventListener("click", (e) => { e.stopPropagation(); this.openBooking(Number(el.dataset.id)); }));
    if (this._config.actions) root.querySelectorAll(".c[data-day]").forEach((el) => el.addEventListener("click", () => {
      const d = el.dataset.day, a = Number(el.dataset.apt);
      const { selStart, selEnd, selApt } = this._state;
      if (!selStart || selEnd || selApt !== a) this.setState({ selStart: d, selEnd: null, selApt: a, panel: null });
      else this.setState({ selEnd: d });
    }));
    root.querySelectorAll("[data-act]").forEach((el) => el.addEventListener("click", () => this.act(el.dataset.act)));
  }
  range() {
    const { selStart: a, selEnd: b } = this._state;
    const end = b || a;
    return a <= end ? [a, end] : [end, a];
  }
  async act(a) {
    const off = this._state.offset;
    if (a === "prev") return this.setState({ offset: off - 1 }, true);
    if (a === "next") return this.setState({ offset: off + 1 }, true);
    if (a === "now") return this.setState({ offset: 0 }, true);
    if (a === "clear") return this.setState({ selStart: null, selEnd: null, panel: null, preMin: null });
    if (a === "block" || a === "rate") return this.setState({ panel: a });
    const [lo, hi] = this.range();
    // Aktionen gehören immer zu genau einer Wohnung: der markierten Zeile
    const aptId = this._state.selApt || (await this.apartment()).apartment_id;
    try {
      if (a === "do-block") {
        const notice = this.$('[data-k="notice"]')?.value || undefined;
        if (!(await confirmDialog(`${t("Sperren")}: ${fdate(lo)} – ${fdate(hi)}?`))) return;
        await this.store.service("block_period", { apartment_id: aptId, start_date: lo, end_date: iso(addDays(D(hi), 1)), ...(notice ? { notice } : {}) });
      } else if (a === "do-rate") {
        const price = this.$('[data-k="price"]')?.value, min = this.$('[data-k="min"]')?.value;
        if (!price && !min) return;
        if (!(await confirmDialog(`${t("Preis setzen")}: ${fdate(lo)} – ${fdate(hi)}${price ? `, ${price} €` : ""}${min ? `, ☾${min}` : ""}?`))) return;
        await this.store.service("set_rates", { apartment_id: aptId, start_date: lo, end_date: hi,
          ...(price ? { price: Number(price) } : {}), ...(min ? { min_stay: Number(min) } : {}) });
      }
      toast(t("Gespeichert"));
      this.setState({ selStart: null, selEnd: null, selApt: null, panel: null, preMin: null }, true);
    } catch (e) {
      toast(`${t("Fehler")}: ${e.message || e}`);
    }
  }
}

// Bestätigungsdialog (eigener, damit er über allen HA-Dialogen liegt)
function confirmDialog(text) {
  return new Promise((resolve) => {
    const wrap = document.createElement("div");
    const p = PAL[DARK ? "dark" : "light"];
    wrap.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10002;display:flex;align-items:center;justify-content:center";
    wrap.innerHTML = `<div style="background:${p.surf};color:${p.ink};padding:22px;border-radius:16px;max-width:380px;font:15px/1.45 ${FONT_ATTR};border:1px solid ${p.line};box-shadow:0 12px 40px rgba(0,0,0,.3)">
      <div style="margin-bottom:18px">${esc(text)}</div><div style="display:flex;gap:8px;justify-content:flex-end">
      <button data-v="0" style="font:600 14px ${FONT_ATTR};padding:8px 16px;border-radius:999px;border:1px solid ${p.line};background:none;color:${p.acc};cursor:pointer">${t("Nein")}</button>
      <button data-v="1" style="font:600 14px ${FONT_ATTR};padding:8px 16px;border-radius:999px;border:none;background:${p.acc};color:${p.accInk};cursor:pointer">${t("Ja")}</button></div></div>`;
    wrap.addEventListener("click", (e) => {
      const v = e.target?.dataset?.v;
      if (v !== undefined || e.target === wrap) { wrap.remove(); resolve(v === "1"); }
    });
    document.body.appendChild(wrap);
  });
}

// ---------------------------------------------------------------------------
// v1.18.0: Preis übernehmen (Empfehlung/Hinweis) – Dialog mit änderbaren Werten, Vorschau, Bestätigung
// Entscheidungen Betreiber 17.11.2026: Standard ab heute bis Monatsende; beim Senken Feiertagsnächte
// auslassen und Tage mit eigenem Preis nicht überschreiben (beides Häkchen, vorbelegt); alles
// änderbar („angepasst übernehmen“). Geschrieben wird der Smoobu-Basispreis – Smoobu überträgt ihn
// mit den Aufschlägen an alle Portale. Prüfung der Berechtigung im Backend (Recht „preise“).
// ---------------------------------------------------------------------------
function priceDialog(card, d) {
  return new Promise((resolve) => {
    const p = PAL[DARK ? "dark" : "light"];
    const v = { ...d.vorgabe };
    const mode = v.prozent !== undefined && v.prozent !== null ? "prozent" : v.preis !== undefined && v.preis !== null ? "preis" : "min";
    const wrap = document.createElement("div");
    wrap.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10002;display:flex;align-items:center;justify-content:center;padding:12px";
    const inp = `font:15px ${FONT_ATTR};padding:7px 10px;border-radius:10px;border:1px solid ${p.line};background:${p.surf2};color:${p.ink};box-sizing:border-box`;
    const btn = (primary) => `font:600 14px ${FONT_ATTR};padding:8px 16px;border-radius:999px;cursor:pointer;${primary ? `border:none;background:${p.acc};color:${p.accInk}` : `border:1px solid ${p.line};background:none;color:${p.acc}`}`;
    const days = v.tage ? `<div style="font-size:13px;color:${p.mut}">${v.tage.length} ${t(v.tage.length === 1 ? "Nacht" : "Nächte")}: ${v.tage.slice(0, 8).map((x) => fdate(x)).join(", ")}${v.tage.length > 8 ? " …" : ""}</div>`
      : `<label style="display:grid;gap:4px;font-size:13px">${t("Von")}<input type="date" data-f="von" value="${esc(v.von)}" style="${inp}"></label>
         <label style="display:grid;gap:4px;font-size:13px">${t("Bis (inklusive)")}<input type="date" data-f="bis" value="${esc(v.bis)}" style="${inp}"></label>`;
    const wd = v.wochentage ? `<div style="font-size:13px;color:${p.mut}">${t("Nur")}: ${v.wochentage.map((i) => t(["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][i])).join(", ")}</div>` : "";
    const priceField = mode === "prozent"
      ? `<label style="display:grid;gap:4px;font-size:13px">${t("Änderung zum bisherigen Tagespreis")}<span style="display:flex;gap:6px;align-items:center"><input type="number" data-f="prozent" step="1" min="-80" max="300" value="${esc(v.prozent)}" style="${inp};width:100px">%</span></label>`
      : `<label style="display:grid;gap:4px;font-size:13px">${t("Neuer Basispreis je Nacht")}<span style="display:flex;gap:6px;align-items:center"><input type="number" data-f="preis" step="1" min="1" value="${esc(v.preis ?? "")}" placeholder="${t("unverändert")}" style="${inp};width:150px">${esc(d.cur === "EUR" ? "€" : d.cur)}</span></label>`;
    const chk = (k, label) => `<label style="display:flex;gap:8px;align-items:center;font-size:14px"><input type="checkbox" data-c="${k}" ${v[k] ? "checked" : ""}>${esc(t(label))}</label>`;
    wrap.innerHTML = `<div style="background:${p.surf};color:${p.ink};padding:20px 22px;border-radius:16px;width:min(460px,100%);max-height:92vh;overflow:auto;font:15px/1.45 ${FONT_ATTR};border:1px solid ${p.line};box-shadow:0 12px 40px rgba(0,0,0,.3);display:grid;gap:12px">
      <div><b style="font-size:17px">${esc(t(d.title))}</b>${d.grund ? `<div style="font-size:13px;color:${p.mut};margin-top:4px">${esc(t(d.grund))}</div>` : ""}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">${days}</div>${wd}
      ${priceField}
      <label style="display:grid;gap:4px;font-size:13px">${t("Mindestaufenthalt")}<span style="display:flex;gap:6px;align-items:center"><input type="number" data-f="mindestaufenthalt" step="1" min="1" max="90" value="${esc(v.mindestaufenthalt ?? "")}" placeholder="${t("unverändert")}" style="${inp};width:150px">${t("Nächte")}</span></label>
      ${v.tage ? "" : chk("ohne_feiertage", "Feiertagsnächte auslassen")}
      ${chk("nur_basispreis", "Tage mit eigenem Preis nicht überschreiben")}
      <div data-x="kanal" style="font-size:13px;background:${p.surf2};border-radius:10px;padding:8px 10px"></div>
      <div data-x="vorschau" style="font-size:13px;color:${p.mut}"></div>
      <div style="display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap">
        <button data-a="abbrechen" style="${btn(false)}">${t("Abbrechen")}</button>
        <button data-a="vorschau" style="${btn(false)}">${t("Vorschau")}</button>
        <button data-a="ok" style="${btn(true)}">${t("Übernehmen")}</button></div></div>`;
    const $ = (sel) => wrap.querySelector(sel);
    const read = () => {
      const o = { ...v };
      wrap.querySelectorAll("[data-f]").forEach((el) => {
        const k = el.dataset.f;
        if (k === "von" || k === "bis") o[k] = el.value;
        else o[k] = el.value === "" ? null : Number(el.value);
      });
      wrap.querySelectorAll("[data-c]").forEach((el) => { o[el.dataset.c] = el.checked; });
      return o;
    };
    // Kanalpreise live: Basispreis × (1 + Aufschlag), netto ≈ Basispreis × Netto-Faktor; Warnung unter der Untergrenze
    const channels = () => {
      const o = read();
      const base = o.preis ?? (o.prozent !== null && o.prozent !== undefined && d.basis ? Math.round(d.basis * (1 + o.prozent / 100)) : null);
      if (!base || !d.kanaele?.length) { $('[data-x="kanal"]').style.display = "none"; return; }
      $('[data-x="kanal"]').style.display = "";
      $('[data-x="kanal"]').innerHTML = `<div style="color:${p.mut};margin-bottom:4px">${o.preis ? t("Kanalpreise bei") : t("Kanalpreise am Basispreis-Tag bei")} ${money(base, d.cur)}</div>` + d.kanaele.map((k) => {
        const floor = d.untergrenze?.[k.kanal];
        const low = floor && base < floor;
        return `<div style="display:flex;gap:8px"><span style="flex:1">${esc(chn(k.kanal))}${k.aufschlag ? ` (+${num(k.aufschlag)} %)` : ""}</span>
          <b>${money(base * (1 + (k.aufschlag || 0) / 100), d.cur)}</b><span style="width:110px;text-align:right;color:${low ? p.bad : p.mut}">${t("netto")} ≈ ${money(base * k.netto_je_euro, d.cur)}${low ? " ⚠" : ""}</span></div>`;
      }).join("") + (d.kanaele.some((k) => d.untergrenze?.[k.kanal] && base < d.untergrenze[k.kanal]) ? `<div style="color:${p.bad};margin-top:4px">⚠ ${t("Unter der Untergrenze: diese Kanäle bringen bei 2 Nächten keinen Deckungsbeitrag mehr.")}</div>` : "");
    };
    const run = async (dry) => {
      const o = read();
      const body = { ...card.target, apartment_id: d.apt, vorgabe: o, dry_run: dry };
      return card.store.ws("smoobu/rates/apply", body, { cache: false });
    };
    const summary = (r) => {
      const why = {};
      for (const x of r.uebersprungen || []) why[x.grund] = (why[x.grund] || 0) + 1;
      const first = (r.tage || []).slice(0, 4).map((x) => `${fdate(x.datum)} ${x.preis_neu !== null ? `${money(x.preis_alt, d.cur)} → ${money(x.preis_neu, d.cur)}` : ""}${x.min_neu ? ` · ☾${x.min_neu}` : ""}`).join("<br>");
      return `<b>${r.tage.length} ${t(r.tage.length === 1 ? "Tag wird geändert" : "Tage werden geändert")}</b>${Object.keys(why).length ? ` · ${t("ausgelassen")}: ${Object.entries(why).map(([k, n]) => `${n} ${t(k)}`).join(", ")}` : ""}<br>${first}${r.tage.length > 4 ? "<br>…" : ""}`;
    };
    wrap.addEventListener("input", channels);
    wrap.addEventListener("click", async (e) => {
      const a = e.target?.dataset?.a;
      if (e.target === wrap || a === "abbrechen") { wrap.remove(); resolve(null); return; }
      if (a === "vorschau") {
        try { $('[data-x="vorschau"]').innerHTML = summary(await run(true)); }
        catch (err) { $('[data-x="vorschau"]').innerHTML = `<span style="color:${p.bad}">${esc(err?.message || err)}</span>`; }
      }
      if (a === "ok") {
        let prev;
        try { prev = await run(true); } catch (err) { $('[data-x="vorschau"]').innerHTML = `<span style="color:${p.bad}">${esc(err?.message || err)}</span>`; return; }
        if (!prev.tage.length) { $('[data-x="vorschau"]').innerHTML = `${t("Keine Änderung nötig")} – ${summary(prev)}`; return; }
        if (!(await confirmDialog(`${prev.tage.length} ${t("Tage in Smoobu ändern? Smoobu überträgt den Basispreis mit den Aufschlägen an alle Portale.")}`))) return;
        try {
          const r = await run(false);
          wrap.remove();
          toast(r.abweichend?.length ? `${t("Übernommen, aber")} ${r.abweichend.length} ${t("Tage weichen in Smoobu ab – bitte prüfen")}`
            : `✓ ${r.tage.length} ${t("Tage übernommen und in Smoobu geprüft")}`);
          card.store.invalidate();
          resolve(r);
        } catch (err) { $('[data-x="vorschau"]').innerHTML = `<span style="color:${p.bad}">${esc(err?.message || err)}</span>`; }
      }
    });
    document.body.appendChild(wrap);
    channels();
  });
}

// ---------------------------------------------------------------------------
// v1.17.0: Zahlungseingang markieren – gemeinsam für Übersicht und Buchungsdetails
// Schreibt den Zahlungsstatus über die vorhandene Aktion smoobu.update_reservation nach Smoobu
// (price_paid → priceStatus, prepayment_paid → prepaymentStatus). Danach lädt store.service()
// alle Karten neu; der offene Betrag kommt wie bisher aus dem Backend (Preis − bezahlte Anzahlung).
// Entscheidung: Bestätigung vor jedem Schreiben (wirkt direkt in Smoobu, auch für Mitbetreiber sichtbar)
// und immer ein Rückweg („Als offen markieren“), falls versehentlich getippt.
// ---------------------------------------------------------------------------
// v1.17.0 (Portal): Portal-Buchungen (Airbnb, Booking.com, HomeToGo, Expedia …) haben im Backend immer
// offen = 0, weil das Portal kassiert (Sensoren „Offene Zahlungen“ bleiben bewusst so). der Betreiber markiert sie
// trotzdem als „erhalten“, sobald er die Rechnung an den Gast geschrieben hat → Status kommt hier allein aus
// Smoobu „price-paid“ (b.bezahlt). portalPay = Portal-Buchung ohne offenen Betrag (Portal-Kanäle mit offenem
// Betrag, z. B. FeWo-direkt ohne Ausnahme in den Optionen, laufen weiter über den normalen Weg mit Betrag).
const portalPay = (b) => !!b && b.gruppe === "Portal" && !(b.offen > 0);
const payInfo = (b) => {
  const live = b && !b.blockiert && !b.storniert;
  const pre = Number(b?.anzahlung) || 0;
  return {
    // Gesamtzahlung offen: Backend meldet einen offenen Betrag – oder Portal-Buchung ohne price-paid
    canPay: live && (b.offen > 0 || (portalPay(b) && !b.bezahlt)),
    portal: portalPay(b),
    // Anzahlung separat nur, solange weder Anzahlung noch Gesamtbetrag bezahlt sind (Portal: keine neue Logik –
    // ohne offenen Betrag gibt es dort auch keinen Anzahlungs-Button, Rückweg canUnpre bleibt wie bisher)
    canPre: live && b.offen > 0 && pre > 0 && !b.anzahlung_bezahlt && !b.bezahlt,
    // Rückwege: in Smoobu als bezahlt markiert → wieder öffnen
    canUnpay: live && !!b.bezahlt,
    canUnpre: live && pre > 0 && !!b.anzahlung_bezahlt && !b.bezahlt,
    pre,
  };
};
async function markPayment(store, b, kind, paid, cur) {
  const pre = Number(b.anzahlung) || 0;
  // Portal-Buchung ohne offenen Betrag: Brutto + Kanal nennen („Zahlung 412,00 € über Airbnb“), damit klar ist,
  // dass hier kein Geld offen war, sondern nur der Status in Smoobu gesetzt wird
  const what = kind === "anzahlung" ? `${t("Anzahlung")} ${money(pre, cur, 2)}`
    : b.offen > 0 ? `${t("Zahlung")} ${money(b.offen, cur, 2)}`
    : portalPay(b) ? `${t("Zahlung")}${b.brutto ? " " + money(b.brutto, cur, 2) : ""} ${t("über")} ${b.kanal || t("Portal")}`
    : t("Zahlung");
  const how = paid ? t("als erhalten markieren") : t("wieder als offen markieren");
  if (!(await confirmDialog(`${b.gast}: ${what} ${how}?`))) return false;
  const data = { reservation_id: b.id };
  if (kind === "anzahlung") data.prepayment_paid = paid;
  else {
    data.price_paid = paid;
    // Gesamtbetrag erhalten schließt die Anzahlung ein → beide auf bezahlt (sonst bliebe Smoobu inkonsistent).
    // Beim Zurücksetzen bleibt der Anzahlungsstatus bewusst unverändert.
    if (paid && pre > 0 && !b.anzahlung_bezahlt) data.prepayment_paid = true;
  }
  try {
    await store.service("update_reservation", data);
    toast(t("In Smoobu gespeichert"));
    return true;
  } catch (e) {
    toast(`${t("Fehler")}: ${e.message || e}`);
    return false;
  }
}

// Zeiträume wie in analytics.py (für Karten ohne Server-Auswertung)
function periodRange(key, todayIso, first) {
  const today = D(todayIso);
  const m = new Date(today.getFullYear(), today.getMonth(), 1);
  const y = today.getFullYear();
  switch (key) {
    case "monat": return [m, addMonths(m, 1)];
    case "vormonat": return [addMonths(m, -1), m];
    case "folgemonat": return [addMonths(m, 1), addMonths(m, 2)];
    case "jahr": return [new Date(y, 0, 1), new Date(y + 1, 0, 1)];
    case "jahr_bis_heute": return [new Date(y, 0, 1), today];
    case "vorjahr": return [new Date(y - 1, 0, 1), new Date(y, 0, 1)];
    case "letzte_12_monate": return [addMonths(m, -12), m];
    case "naechste_12_monate": return [m, addMonths(m, 12)];
    default: return [first ? D(first) : new Date(y - 2, 0, 1), addMonths(m, 13)];
  }
}

function downloadCsv(name, rows) {
  const csv = rows.map((r) => r.map((v) => {
    const s = v === null || v === undefined ? "" : typeof v === "number" ? String(v).replace(".", LANG === "de" ? "," : ".") : String(v);
    return /[;"\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  }).join(";")).join("\r\n");
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

// ===========================================================================
// Buchungsliste
// ===========================================================================
const BOOKING_COLS = [
  ["status", "Status"], ["anreise", "Anreise"], ["abreise", "Abreise"], ["naechte", "Nächte", "n"], ["gast", "Gast"],
  ["personen", "Personen", "n"], ["kanal", "Kanal"], ["brutto", "Brutto", "n"], ["kosten", "Kosten", "n"],
  ["netto", "Netto", "n"], ["netto_pro_nacht", "Netto/Nacht", "n"], ["offen", "Offen", "n"], ["vorlauf_tage", "Vorlauf", "n"],
];
// Datumsspalten starten beim Sortieren immer absteigend (neueste zuerst), alle übrigen aufsteigend
const BOOKING_DATE_COLS = new Set(["anreise", "abreise"]);
// Logische Reihenfolge für die Status-Spalte (statt alphabetisch)
const BOOKING_STATUS_ORDER = { laufend: 0, kommend: 1, vergangen: 2, blockiert: 3, storniert: 4 };
// Zeitliche Gruppen der Buchungsliste. Einteilung nach Datum wie im Backend (analytics.py):
// Abreise ≤ heute → vergangen, Anreise ≤ heute → aktuell, sonst anstehend – gilt auch für Sperren/Stornos
const BOOKING_GROUPS = [["anstehend", "Anstehend", "mdi:calendar-arrow-right"], ["aktuell", "Aktuell", "mdi:home-account"],
  ["vergangen", "Vergangen", "mdi:check"]];
const bookingGroup = (b, today) => (b.abreise <= today ? "vergangen" : b.anreise <= today ? "aktuell" : "anstehend");
class SmoobuBookingsCard extends SmoobuCard {
  static defaults = { title: "", period: "jahr", status: [] };
  // Standard: nach Anreise, absteigend (dir −1)
  static initialState = (c) => ({ period: c.period || "jahr", from: null, to: null, channels: [], status: c.status || [],
    search: "", sort: "anreise", dir: -1 });
  static css = `.toolbar input[type=search] { min-width: 180px; flex: 1 1 180px; }
    td .dot { margin-right: 6px; } td.st ha-icon { color: var(--sm-muted); } tr.cx td { text-decoration: line-through; opacity: .6; }
    tr.bl td { color: var(--sm-muted); font-style: italic; }
    tr.grp td { background: var(--sm-surf2); color: var(--sm-ink); font-weight: 600; font-size: .8rem; letter-spacing: .02em;
      border-top: 2px solid var(--sm-line); padding-top: 10px; cursor: default; }
    tr.grp td ha-icon { --mdc-icon-size: 16px; color: var(--sm-accent); margin-right: 6px; vertical-align: -2px; }
    tr.grp td .cnt { color: var(--sm-muted); font-weight: 400; margin-left: 6px; }`;
  async load() {
    const apt = await this.apartment();
    const info = await this.store.getInfo();
    const s = this._state;
    let [start, end] = periodRange(s.period, info.heute, apt.erster_tag);
    if (s.period === "custom") { start = s.from ? D(s.from) : start; end = s.to ? addDays(D(s.to), 1) : end; }
    const list = await this.store.ws("smoobu/bookings", { ...this.target, start: iso(start), end: iso(end) });
    return { apt, start, end, bookings: list.buchungen };
  }
  filtered({ apt, bookings }) {
    const s = this._state;
    const q = s.search.trim().toLowerCase();
    const chans = new Set(s.channels);
    let rows = bookings.filter((b) => {
      // Stornierte Sperrzeiten (Smoobu legt viele automatisch an) nur auf ausdrücklichen Wunsch
      if (b.storniert && b.blockiert && !(s.status.includes("storniert") && s.status.includes("blockiert"))) return false;
      if (s.status.length && !s.status.includes(b.status) && !(b.blockiert && s.status.includes("blockiert"))) return false;
      if (chans.size && !(chans.has(b.kanal) || (chans.has("Direkt") && b.gruppe === "Direkt") || (chans.has("Portale") && b.gruppe === "Portal"))) return false;
      if (q && ![b.gast, b.email, b.telefon, b.referenz, b.notiz, b.kanal, b.id].join(" ").toLowerCase().includes(q)) return false;
      return true;
    });
    const k = s.sort;
    rows = rows.map((b) => ({ ...b, kosten: Math.round((b.provision + b.zahlungsgebuehr) * 100) / 100, wohnung: aptCode(this.store.info, b.wohnung_id) }));
    const val = (r) => (k === "status" ? BOOKING_STATUS_ORDER[r.status] ?? 9 : k === "gast" ? (r.blockiert ? r.notiz || "" : r.gast || "") : r[k]);
    rows.sort((a, b) => {
      const x = val(a), y = val(b);
      // Leere Werte immer ans Ende, unabhängig von der Richtung
      const ex = x === null || x === undefined || x === "", ey = y === null || y === undefined || y === "";
      if (ex || ey) return ex === ey ? b.anreise.localeCompare(a.anreise) : ex ? 1 : -1;
      const c = typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true });
      // Gleichstand: nach Anreise absteigend als stabiler Zweitschlüssel
      return c * s.dir || b.anreise.localeCompare(a.anreise);
    });
    // Trennung vergangen / aktuell / anstehend. Gruppenreihenfolge folgt der Zeitrichtung:
    // absteigend (Standard) und bei Nicht-Datumsspalten Anstehend → Aktuell → Vergangen, bei Datum aufsteigend umgekehrt
    const today = this.store.info?.heute || iso(new Date());
    const order = BOOKING_DATE_COLS.has(k) && s.dir > 0 ? [...BOOKING_GROUPS].reverse() : BOOKING_GROUPS;
    const groups = order.map(([key, label, icon]) => ({ key, label, icon, rows: rows.filter((r) => bookingGroup(r, today) === key) }))
      .filter((g) => g.rows.length);
    this._groups = groups;
    return groups.flatMap((g) => g.rows);
  }
  body(data) {
    const { apt } = data;
    const cur = apt.currency;
    const s = this._state;
    const rows = this.filtered(data);
    this._rows = rows;
    const valid = rows.filter((b) => !b.storniert && !b.blockiert);
    const sum = (k) => valid.reduce((a, b) => a + (b[k] || 0), 0);
    const statusChips = ["kommend", "laufend", "vergangen", "storniert", "blockiert"].map((st) =>
      `<button class="chip" data-st="${st}" aria-pressed="${s.status.includes(st)}"><ha-icon icon="${STATUS_ICON[st]}"></ha-icon>${t(st)}</button>`).join("");
    const cols = this.multi ? [BOOKING_COLS[0], ["wohnung", "Wohnung"], ...BOOKING_COLS.slice(1)] : BOOKING_COLS;
    const head = cols.map(([k, l, n]) => `<th class="${n || ""}" data-sort="${k}">${t(l)}${s.sort === k ? (s.dir > 0 ? " ▲" : " ▼") : ""}</th>`).join("");
    const row = (b) => `<tr class="click ${b.storniert ? "cx" : ""} ${b.blockiert ? "bl" : ""}" data-id="${b.id}">
      <td class="st"><ha-icon icon="${STATUS_ICON[b.status]}" title="${t(b.status)}"></ha-icon></td>
      ${this.multi ? `<td>${codeTag(b.wohnung)}</td>` : ""}<td>${fdow(b.anreise)}</td><td>${fdow(b.abreise)}</td><td class="n">${b.naechte}</td>
      <td>${b.blockiert ? `🔒 ${esc(b.notiz || t("Gesperrt"))}` : esc(b.gast)}${b.hund ? " 🐕" : ""}</td>
      <td class="n">${b.blockiert ? "" : b.personen}</td>
      <td><span class="dot" style="background:${colorOf(apt, b.kanal, b.blockiert)}"></span>${esc(chn(b.kanal))}</td>
      <td class="n">${b.blockiert ? "" : money(b.brutto, cur, 2)}</td><td class="n">${b.blockiert ? "" : money(b.kosten, cur, 2)}</td>
      <td class="n">${b.blockiert ? "" : money(b.netto, cur, 2)}</td><td class="n">${b.netto_pro_nacht ? money(b.netto_pro_nacht, cur) : ""}</td>
      <td class="n">${b.offen > 0 ? `<span class="badge bad">${money(b.offen, cur, 2)}</span>` : ""}</td>
      <td class="n">${b.vorlauf_tage ?? ""}</td></tr>`;
    // Je Gruppe eine Trennzeile mit Anzahl gültiger Buchungen (ohne Sperren/Stornos) und Nächten
    const body = (this._groups || []).map((g) => {
      const ok = g.rows.filter((b) => !b.storniert && !b.blockiert);
      const n = ok.reduce((a, b) => a + (b.naechte || 0), 0);
      return `<tr class="grp"><td colspan="${cols.length}"><ha-icon icon="${g.icon}"></ha-icon>${t(g.label)}`
        + `<span class="cnt">${ok.length} ${t("Buchungen")} · ${num(n)} ${t("Nächte")}</span></td></tr>${g.rows.map(row).join("")}`;
    }).join("");
    return `
      <div class="head"><h2>${esc(this._config.title || t("Buchungen"))}</h2>
        <button class="btn flat" data-act="csv">⬇ ${t("Export CSV")}</button></div>
      <div class="toolbar">
        <input type="search" data-k="search" placeholder="${t("Suche")} (Name, E-Mail, Telefon, Notiz …)" value="${esc(s.search)}">
        ${periodSelect(s.period)}
        ${s.period === "custom" ? `<input type="date" data-k="from" value="${s.from || ""}"> – <input type="date" data-k="to" value="${s.to || ""}">` : ""}
      </div>
      <div class="toolbar">${channelChips(apt, s.channels)}</div>
      <div class="toolbar">${statusChips}</div>
      <div class="scroll"><table><thead><tr>${head}</tr></thead><tbody>${body || `<tr><td colspan="14" class="empty">${t("Keine Daten")}</td></tr>`}</tbody>
      <tfoot><tr><td colspan="${this.multi ? 4 : 3}">${t("Summe")}: ${valid.length} ${t("Buchungen")}</td><td class="n">${num(sum("naechte"))}</td><td></td>
        <td class="n">${num(sum("personen"))}</td><td></td><td class="n">${money(sum("brutto"), cur)}</td><td class="n">${money(sum("kosten"), cur)}</td>
        <td class="n">${money(sum("netto"), cur)}</td><td class="n">${sum("naechte") ? money(sum("netto") / sum("naechte"), cur) : ""}</td>
        <td class="n">${money(sum("offen"), cur)}</td><td></td></tr></tfoot></table></div>`;
  }
  bind(root) {
    const s = this._state;
    root.querySelectorAll("tr[data-id]").forEach((el) => el.addEventListener("click", () => this.openBooking(Number(el.dataset.id))));
    root.querySelectorAll("th[data-sort]").forEach((el) => el.addEventListener("click", () => {
      const k = el.dataset.sort;
      // gleiche Spalte: Richtung umkehren; neue Spalte: Datum absteigend, sonst aufsteigend
      this.setState({ sort: k, dir: s.sort === k ? -s.dir : BOOKING_DATE_COLS.has(k) ? -1 : 1 });
    }));
    root.querySelectorAll("[data-st]").forEach((el) => el.addEventListener("click", () => this.setState({ status: toggleChannel(s.status, el.dataset.st) })));
    root.querySelectorAll("[data-ch]").forEach((el) => el.addEventListener("click", () => this.setState({ channels: toggleChannel(s.channels, el.dataset.ch) })));
    const search = root.querySelector('[data-k="search"]');
    search?.addEventListener("input", () => {
      const pos = search.selectionStart;
      this.setState({ search: search.value });
      const n = this.$('[data-k="search"]');
      n.focus();
      n.setSelectionRange(pos, pos);
    });
    root.querySelector('[data-k="period"]')?.addEventListener("change", (e) => this.setState({ period: e.target.value }, true));
    root.querySelector('[data-k="from"]')?.addEventListener("change", (e) => this.setState({ from: e.target.value }, true));
    root.querySelector('[data-k="to"]')?.addEventListener("change", (e) => this.setState({ to: e.target.value }, true));
    root.querySelector('[data-act="csv"]')?.addEventListener("click", () => {
      const csvCols = ["id", "wohnung", "status", "anreise", "abreise", "naechte", "gast", "email", "telefon", "personen", "erwachsene", "kinder",
        "kanal", "gruppe", "brutto", "provision", "zahlungsgebuehr", "netto", "netto_pro_nacht", "offen", "bezahlt", "vorlauf_tage",
        "erstellt", "hund", "notiz"];
      downloadCsv(`smoobu-buchungen-${iso(new Date())}.csv`, [csvCols, ...(this._rows || []).map((b) => csvCols.map((c) => b[c]))]);
    });
  }
}

// ---------------------------------------------------------------------------
// Diagramme (SVG, ohne Bibliothek)
// ---------------------------------------------------------------------------
function niceMax(v) {
  if (!v || v <= 0) return 1;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  return [1, 2, 2.5, 5, 10].map((m) => m * p).find((m) => m >= v);
}
// extra (v1.17.0): weitere Vergleichslinien (ältere Jahre/Perioden), je blasser, je älter
// unit (v1.18.0b8): "tag" | "woche" | "monat" (Raster der Reihe); starts = erster Tag je Woche (Beschriftung)
function barChart({ labels, stacks, line, fmt, unit, daily, extra = [], starts = [] }) {
  daily = daily || unit === "tag";
  const weekly = unit === "woche";
  const W = 800, H = 260, L = 56, R = 8, T = 10, B = 28;
  const n = labels.length || 1;
  const sums = labels.map((_, i) => stacks.reduce((a, s) => a + (s.values[i] || 0), 0));
  const max = niceMax(Math.max(...sums, ...(line?.values || [0]), ...extra.flatMap((e) => e.values || [0])) * 1.05);
  const y = (v) => T + (H - T - B) * (1 - v / max);
  const bw = (W - L - R) / n;
  let svg = "";
  for (let g = 0; g <= 4; g++) {
    const v = (max / 4) * g;
    svg += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" stroke-opacity=".12"/>
      <text x="${L - 6}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="currentColor" fill-opacity=".6">${fmt(v)}</text>`;
  }
  const step = daily || weekly ? Math.ceil(n / 15) : 1;
  labels.forEach((lab, i) => {
    const x = L + i * bw;
    let acc = 0;
    const parts = [];
    for (const s of stacks) {
      const v = s.values[i] || 0;
      if (v <= 0) continue;
      const y1 = y(acc + v), y0 = y(acc);
      svg += `<rect x="${x + bw * 0.16}" y="${y1}" width="${bw * 0.68}" height="${Math.max(y0 - y1, 0)}" fill="${s.color}" rx="3"/>`;
      parts.push(`${s.name}: ${fmt(v)}`);
      acc += v;
    }
    const lbl = weekly ? `${t("KW")} ${Number(lab.slice(6))}` : daily ? fdate(lab, { day: "2-digit", month: "2-digit" }) : D(`${lab}-01`).toLocaleDateString(locale(), { month: "short" });
    if (i % step === 0) svg += `<text x="${x + bw / 2}" y="${H - 8}" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity=".7">${lbl}</text>`;
    const tip = `${weekly ? `${t("KW")} ${Number(lab.slice(6))} ${lab.slice(0, 4)}${starts[i] ? ` (${t("ab")} ${fdate(starts[i])})` : ""}` : daily ? fdate(lab) : D(`${lab}-01`).toLocaleDateString(locale(), { month: "long", year: "numeric" })}: ${fmt(sums[i])}` +
      (parts.length > 1 ? ` (${parts.join(", ")})` : "") + (line ? ` · ${line.label}: ${fmt(line.values[i] || 0)}` : "")
      + extra.map((e) => ` · ${e.label}: ${fmt(e.values[i] || 0)}`).join("");
    svg += `<rect class="hit" data-tip="${esc(tip)}" x="${x}" y="${T}" width="${bw}" height="${H - T - B}" fill="transparent"><title>${esc(tip)}</title></rect>`;
  });
  // ältere Vergleichslinien zuerst zeichnen, damit die erste Vergleichslinie obenauf liegt
  extra.forEach((e) => {
    const pts = (e.values || []).slice(0, n).map((v, i) => `${L + i * bw + bw / 2},${y(v || 0)}`).join(" ");
    svg += `<polyline points="${pts}" fill="none" stroke="currentColor" stroke-opacity="${e.op}" stroke-width="1.5" stroke-dasharray="${e.dash}"/>`;
  });
  if (line && line.values.length) {
    const pts = line.values.slice(0, n).map((v, i) => `${L + i * bw + bw / 2},${y(v || 0)}`).join(" ");
    svg += `<polyline points="${pts}" fill="none" stroke="currentColor" stroke-opacity=".55" stroke-width="2" stroke-dasharray="5 4"/>`;
    line.values.slice(0, n).forEach((v, i) => { svg += `<circle cx="${L + i * bw + bw / 2}" cy="${y(v || 0)}" r="2.5" fill="currentColor" fill-opacity=".6"/>`; });
  }
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block;color:var(--sm-ink);font-family:inherit" role="img">${svg}</svg>`;
}
function donut(parts, center = "") {
  const total = parts.reduce((a, p) => a + p.value, 0) || 1;
  const r = 60, c = 2 * Math.PI * r;
  let off = 0, segs = "";
  for (const p of parts) {
    const len = (p.value / total) * c;
    segs += `<circle r="${r}" cx="80" cy="80" fill="none" stroke="${p.color}" stroke-width="26" stroke-dasharray="${len} ${c - len}"
      stroke-dashoffset="${-off}" transform="rotate(-90 80 80)"><title>${esc(p.name)}: ${num((p.value / total) * 100, 1)} %</title></circle>`;
    off += len;
  }
  return `<svg viewBox="0 0 160 160" width="160" height="160">${segs}<text x="80" y="86" text-anchor="middle" font-size="18" font-weight="600" fill="currentColor">${esc(center)}</text></svg>`;
}

// ===========================================================================
// Finanzen & Kanäle
// ===========================================================================
// Auswahl „Anzahl Vergleichszeiträume“ (v1.17.0)
const COMPARE_COUNTS = [1, 2, 3, 4, 5, 10];
// Kurzname eines Zeitraums [von, bis): ganzes Jahr „2025“, ganze Monate „Nov 2025“ / „Jan–Jun 2025“, sonst Datum–Datum
function periodName(von, bis) {
  const a = D(von), b = addDays(D(bis), -1);
  const wholeMonths = a.getDate() === 1 && D(bis).getDate() === 1;
  if (wholeMonths && a.getMonth() === 0 && b.getMonth() === 11 && a.getFullYear() === b.getFullYear()) return String(a.getFullYear());
  const mon = (d) => d.toLocaleDateString(locale(), { month: "short" });
  if (wholeMonths && a.getFullYear() === b.getFullYear()) {
    return a.getMonth() === b.getMonth() ? `${mon(a)} ${a.getFullYear()}` : `${mon(a)}–${mon(b)} ${a.getFullYear()}`;
  }
  return `${fdate(von)} – ${fdate(iso(b))}`;
}
// Diagramm-Kennzahlen der Finanzen-Karte (v1.17.0: + Provisionen & Gebühren je Portal)
const METRIC_LABEL = { brutto: "Brutto", netto: "Netto", naechte: "Nächte", kosten: "Provisionen" };
// ===========================================================================
// Gemeinsame Filterleiste Statistik + Finanzen (v1.18.0b8)
// ===========================================================================
// Wunsch Betreiber 17.11.2026: Finanzen bekommt dieselben Filter und Vergleichsmöglichkeiten wie die
// Statistik. Damit beide nicht auseinanderlaufen, erzeugen filterBarHtml/bindFilterBar die Leiste für
// beide Karten. Kartenzustand: ptype, anchor, from, to, compare, raster, channels (+ quick in Finanzen).
const FBAR_CSS = `
    /* Filterleiste: bleibt beim Scrollen oben (unter der HA-Kopfzeile) */
    .fbar { position: sticky; top: var(--header-height, 0px); z-index: 4; display: flex; flex-wrap: wrap; gap: 8px 10px; align-items: center;
      padding: 10px 12px; margin: 0 0 var(--sm-gap); background: color-mix(in srgb, var(--sm-surf) 94%, transparent);
      border: 1px solid var(--sm-line); border-radius: var(--sm-r); backdrop-filter: blur(6px); }
    .fbar .grp { display: inline-flex; align-items: center; gap: 6px; }
    .fbar .lbl { font-size: .74rem; color: var(--sm-muted); font-weight: 600; text-transform: uppercase; letter-spacing: .05em; }
    .fbar .sep { width: 1px; align-self: stretch; background: var(--sm-line); }
    .fbar .chips { display: flex; flex-wrap: wrap; gap: 6px; }
    .fbar .chip { padding: 4px 10px; font-size: .8rem; }
    .step { border: 1px solid var(--sm-line); background: var(--sm-surf); color: var(--sm-ink); border-radius: 999px; width: 30px; height: 30px;
      cursor: pointer; font: inherit; font-size: 1rem; line-height: 1; }
    .step:hover { border-color: var(--sm-accent); }
    .plabel { font-weight: 650; min-width: 9ch; text-align: center; white-space: nowrap; }
    @media (max-width: 700px) {
      /* am Handy nicht mitlaufen lassen: die Leiste wäre höher als ein Drittel des Bildschirms */
      .fbar { padding: 8px 10px; gap: 6px 8px; position: static; }
      .fbar .sep { display: none; }
    }
`;
// Finanzen: Vergleich wie Statistik plus „Kein Vergleich“ (gibt es nur hier); Schlüssel → smoobu/analytics
const FIN_COMPARE = [["stichtag", "Stichtag Vorjahr"], ["vorjahr", "Ganzes Vorjahr"], ["vorperiode", "Vorperiode"], ["kein", "Kein Vergleich"]];
const FIN_COMPARE_API = { stichtag: "vorjahr_stand", vorjahr: "vorjahr", vorperiode: "vorperiode", kein: "kein" };
// alte Kartenoption compare: vorjahr_stand (bis v1.18.0b7) = heute „Stichtag Vorjahr“
const FIN_COMPARE_ALIAS = { vorjahr_stand: "stichtag" };
// Finanzen: Raster mit „Tag“ (Statistik: Auto/Woche/Monat); Auto = bis 62 Tage je Tag, sonst je Monat
const FIN_RASTER = [["auto", "Auto"], ["tag", "Tag"], ["woche", "Woche"], ["monat", "Monat"]];
// Schnellwahl (Entscheidung Betreiber 17.11.2026: bisherige Zeiträume der Finanzen bleiben zusätzlich erhalten)
const QUICK_PERIODS = ["vormonat", "folgemonat", "vorjahr", "jahr_bis_heute", "letzte_12_monate", "naechste_12_monate", "gesamt"];
// Schnellwahl → Kartenzustand: Vormonat/Folgemonat/Vorjahr werden echte Monats-/Jahreszeiträume (dann geht ‹ ›),
// die übrigen ein freier Zeitraum mit Merker quick (für die Anzeige im Auswahlfeld)
function quickState(key, todayIso, first) {
  const today = D(todayIso);
  const m = new Date(today.getFullYear(), today.getMonth(), 1);
  if (key === "vormonat") return { ptype: "monat", anchor: iso(addMonths(m, -1)), quick: null };
  if (key === "folgemonat") return { ptype: "monat", anchor: iso(addMonths(m, 1)), quick: null };
  if (key === "vorjahr") return { ptype: "jahr", anchor: iso(new Date(today.getFullYear() - 1, 0, 1)), quick: null };
  const [a, b] = periodRange(key, todayIso, first);
  return { ptype: "frei", from: iso(a), to: iso(addDays(b, -1)), quick: key };
}
// opts: simple (Handy-Ansicht Statistik), compares, rasters, quick (Schnellwahl zeigen), afterCmp (HTML nach dem
// Vergleich, z. B. Anzahl Vergleichsjahre), tools (HTML am rechten Rand)
function filterBarHtml(card, d, { simple = false, compares = STATS_COMPARE, rasters = RASTER, quick = false, afterCmp = "", tools = "" } = {}) {
  const s = card._state;
  const ptypes = PERIOD_TYPES.filter(([k]) => !simple || k !== "frei");
  const period = `<div class="seg" role="group" aria-label="${t("Zeitraum")}">${ptypes.map(([k, l]) =>
    `<button data-ptype="${k}" aria-pressed="${s.ptype === k}">${k === "frei" && LANG !== "de" ? "Custom" : t(l)}</button>`).join("")}</div>`;
  const qsel = quick ? `<select data-k="quick" aria-label="${t("Schnellwahl")}"><option value="">${t("Schnellwahl")} …</option>${QUICK_PERIODS.map((k) =>
    `<option value="${k}" ${s.quick === k ? "selected" : ""}>${t(PERIOD_LABEL[k])}</option>`).join("")}</select>` : "";
  const anchor = s.ptype === "frei"
    ? `<span class="grp"><input type="date" data-k="from" value="${iso(d.range[0])}"> – <input type="date" data-k="to" value="${iso(addDays(d.range[1], -1))}"></span>`
    : `<span class="grp"><button class="step" data-step="-1" aria-label="${t("Zurück")}">‹</button><span class="plabel">${esc(statsLabel(s.ptype, d.range))}</span>
        <button class="step" data-step="1" aria-label="${t("Weiter")}">›</button></span>`;
  const cmp = `<select data-k="compare" aria-label="${t("Vergleich")}">${compares.map(([k, l]) =>
    `<option value="${k}" ${k === s.compare ? "selected" : ""}>${t("Vergleich")}: ${t(l)}</option>`).join("")}</select>`;
  if (simple) return `<div class="fbar">${period}${anchor}${cmp}</div>`;
  const ws = d.info.wohnungen;
  const sel = card.target.apartment_id;
  const apts = ws.length > 1 && !card._config.apartment_id && !HeaderApts.n
    ? `<span class="sep"></span><span class="grp"><span class="lbl">${t("Wohnung")}</span><div class="seg">
        <button data-apt="${ALL}" aria-pressed="${sel === ALL}">${t("Alle")}</button>${ws.map((w) =>
        `<button data-apt="${w.apartment_id}" aria-pressed="${sel === w.apartment_id}" title="${esc(w.name)}">${esc(w.kuerzel || w.name)}</button>`).join("")}</div></span>` : "";
  const raster = `<span class="grp"><span class="lbl">${t("Raster")}</span><div class="seg">${rasters.map(([k, l]) =>
    `<button data-raster="${k}" aria-pressed="${s.raster === k}">${t(l)}</button>`).join("")}</div></span>`;
  return `<div class="fbar">${period}${qsel}${anchor}${cmp}${afterCmp}<span class="sep"></span>${raster}${apts}
    <span class="sep"></span><div class="chips">${channelChips(d.apt, s.channels)}</div>${tools}</div>`;
}
// Ereignisse der Leiste; shiftPatch = zusätzlicher Zustand beim Blättern (Statistik: Pace-Jahr zurücksetzen).
// Heute/erster Datentag werden erst beim Klick aus card._data gelesen: bind() läuft auch beim Zeichnen
// des Lade-/Fehlerzustands, dann gibt es noch keine Daten
function bindFilterBar(card, root, shiftPatch = {}) {
  const s = card._state;
  const todayOf = () => card._data?.today;
  root.querySelectorAll("[data-ptype]").forEach((el) => el.addEventListener("click", () => {
    const todayIso = todayOf();
    const [a, b] = statsRange(s, todayIso);
    const p = el.dataset.ptype;
    // Beim Wechsel auf „Frei“ den bisherigen Zeitraum übernehmen; sonst den Zeitraum, der heute bzw. den bisherigen Beginn enthält
    if (p === "frei") card.setState({ ptype: p, from: iso(a), to: iso(addDays(b, -1)), quick: null }, true);
    else card.setState({ ptype: p, anchor: iso(s.anchor ? a : D(todayIso)), quick: null }, true);
  }));
  root.querySelectorAll("[data-step]").forEach((el) => el.addEventListener("click", () => {
    const [a] = statsRange(s, todayOf());
    card.setState({ anchor: iso(addMonths(a, Number(el.dataset.step) * PERIOD_MONTHS[s.ptype])), ...shiftPatch }, true);
  }));
  root.querySelector('[data-k="quick"]')?.addEventListener("change", (e) => {
    if (e.target.value) card.setState(quickState(e.target.value, todayOf(), card._data?.apt?.erster_tag), true);
  });
  root.querySelector('[data-k="compare"]')?.addEventListener("change", (e) => card.setState({ compare: e.target.value }, true));
  // Datum von Hand geändert → keine Schnellwahl mehr
  root.querySelector('[data-k="from"]')?.addEventListener("change", (e) => card.setState({ from: e.target.value, quick: null }, true));
  root.querySelector('[data-k="to"]')?.addEventListener("change", (e) => card.setState({ to: e.target.value, quick: null }, true));
  root.querySelectorAll("[data-raster]").forEach((el) => el.addEventListener("click", () => card.setState({ raster: el.dataset.raster }, true)));
  root.querySelectorAll("[data-ch]").forEach((el) => el.addEventListener("click", () => card.setState({ channels: toggleChannel(s.channels, el.dataset.ch) }, true)));
  root.querySelectorAll("[data-apt]").forEach((el) => el.addEventListener("click", () => {
    AptSel.value = el.dataset.apt === ALL ? ALL : Number(el.dataset.apt);
  }));
}
// Veränderung als schlichter Text ohne Bewertungsfarbe (Endstand-Hinweis); pp = Prozentpunkte
function chgText(a, b, pp = false) {
  if (a === null || a === undefined || b === null || b === undefined) return "";
  const v = pp ? Math.round((a - b) * 10) / 10 : b ? ((a - b) / Math.abs(b)) * 100 : null;
  if (v === null) return "";
  return `${v > 0 ? "+" : v < 0 ? "−" : "±"}${num(Math.abs(v), 1)}${pp ? " PP" : " %"}`;
}

class SmoobuAnalyticsCard extends SmoobuCard {
  // compare_count (v1.17.0): Anzahl Vergleichszeiträume, Standard 1 = wie bisher
  // v1.18.0b8: Filterleiste wie Statistik. period: monat|quartal|saison|jahr|custom oder ein Schnellwahl-Schlüssel
  // (vormonat, jahr_bis_heute, letzte_12_monate …, wie bis v1.18.0b7); compare: stichtag (Standard, Entscheidung
  // Betreiber 17.11.2026) | vorjahr | vorperiode | kein (alt: vorjahr_stand = stichtag); raster: auto|tag|woche|monat
  static defaults = { title: "", period: "jahr", compare: "stichtag", compare_count: 1, raster: "auto" };
  static initialState = (c) => {
    const p = c.period === "custom" ? "frei" : c.period;
    const typed = PERIOD_TYPES.some(([k]) => k === p);
    return { ptype: typed ? p : "jahr", anchor: null, from: null, to: null,
      // Schnellwahl aus der Kartenoption wird beim ersten Laden aufgelöst (braucht das heutige Datum)
      quick: null, pendingQuick: typed || !QUICK_PERIODS.includes(p) ? null : p,
      compare: FIN_COMPARE_ALIAS[c.compare] || (FIN_COMPARE_API[c.compare] ? c.compare : "stichtag"),
      compareCount: Number(c.compare_count) || 1, raster: FIN_RASTER.some(([k]) => k === c.raster) ? c.raster : "auto",
      channels: [], metric: "brutto" };
  };
  static css = `
    .split { display: grid; grid-template-columns: minmax(0, 1fr) 200px; gap: 16px; align-items: center; }
    @media (max-width: 700px) { .split { grid-template-columns: 1fr; } }
    .share { display: flex; flex-direction: column; align-items: center; gap: 6px; font-size: .8rem; }
    .bar-in { height: 5px; border-radius: 3px; background: var(--sm-accent); margin-top: 3px; }
    .grid { margin-bottom: 4px; }
    .tip { min-height: 1.2em; font-size: .82rem; color: var(--sm-muted); margin-top: 4px; }
    .ins li { margin: 4px 0; } .ins { padding-left: 18px; margin: 4px 0; }
    /* v1.17.0: Legende unter dem Balkendiagramm */
    .legend { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: .8rem; margin-top: 6px; }
    .legend span { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
    .legend i { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
    .legend .ln { width: 16px; height: 0; border-top: 2px dashed currentColor; opacity: .55; border-radius: 0; }
    .legend b { font-weight: 600; } .legend em { font-style: normal; color: var(--sm-muted); }
    /* v1.17.0: Mini-Balken Wochentage in der Kachel */
    .wk { display: flex; gap: 3px; align-items: flex-end; height: 26px; margin-top: 6px; }
    .wk div { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 1px; font-size: .62rem; color: var(--sm-muted); }
    .wk div i { display: block; width: 100%; border-radius: 2px; background: var(--sm-accent); opacity: .45; min-height: 2px; }
    .wk div.we i { opacity: 1; }
    td .sub2 { display: block; font-size: .72rem; color: var(--sm-muted); }
    /* v1.18.0b8: Filterleiste wie Statistik; mitlaufen geht nur, wenn die Karte nicht abschneidet
       (breite Tabellen liegen ohnehin in eigenen .scroll-Bereichen) */
    ha-card { overflow: visible; }
    ${FBAR_CSS}
    .fin { display: block; font-size: .74rem; color: var(--sm-muted); margin-top: 2px; }
  `;
  // v1.18.0b8: wie Statistik neu zeichnen, wenn eine Kopfzeile mit Wohnungsauswahl erscheint/verschwindet
  _listen() {
    super._listen();
    const onHdr = () => { if (this._data) this.render(); };
    HeaderApts.listeners.add(onHdr);
    const base = this._unsub;
    this._unsub = () => { base?.(); HeaderApts.listeners.delete(onHdr); };
  }
  async load() {
    const info = await this.store.getInfo();
    const apt = await this.apartment();
    const today = info.heute;
    if (this._state.pendingQuick) this._state = { ...this._state, ...quickState(this._state.pendingQuick, today, apt.erster_tag), pendingQuick: null };
    const s = this._state;
    const range = statsRange(s, today);
    const params = { ...this.target, compare: FIN_COMPARE_API[s.compare] || "vorjahr_stand", start: iso(range[0]), end: iso(range[1]), raster: s.raster };
    if (s.compareCount > 1 && s.compare !== "kein") params.compare_count = s.compareCount;
    if (s.channels.length) params.channels = s.channels;
    const r = await this.store.ws("smoobu/analytics", params);
    // Endstand des Vergleichszeitraums (wie Statistik, v1.18.0b7): nur bei „Stichtag Vorjahr“ und wenn der
    // Vergleichszeitraum am Stichtag noch lief – sonst sind Stand und Endstand gleich. Bewertung (Pfeil/Farbe)
    // bleibt beim Stichtag, der Endstand steht nur als Zusatzzeile daneben.
    let fin = null;
    const st = r.stichtag_vergleich;
    if (s.compare === "stichtag" && st && r.vergleich && D(r.vergleich.bis) > addDays(D(st), 1)) {
      fin = await this.store.ws("smoobu/analytics", { ...params, compare: "vorjahr", compare_count: 1 })
        .then((x) => x.vergleich).catch(() => null);
    }
    // Gesamtansicht: dieselbe Auswertung je Wohnung für den Wohnungsvergleich
    let per = [];
    if (this.multi) {
      per = await Promise.all(info.wohnungen.filter((w) => !params.entry_id || w.entry_id === params.entry_id)
        .map((w) => this.store.ws("smoobu/analytics", { ...params, apartment_id: w.apartment_id }).then((x) => ({ w, x })).catch(() => null)));
      per = per.filter(Boolean);
    }
    return { info, apt, today, range, r, per, fin };
  }
  insights(apt, r) {
    const cur = apt.currency;
    const out = [];
    const chans = Object.entries(r.kanaele);
    const portals = chans.filter(([, v]) => v.gruppe === "Portal" && v.brutto > 0);
    if (portals.length) {
      const [n, v] = portals.reduce((a, b) => (b[1].kostenquote_prozent > a[1].kostenquote_prozent ? b : a));
      out.push(`Teuerstes Portal: <b>${esc(chn(n))}</b> mit ${pct(v.kostenquote_prozent)} Kosten (${money(v.kosten, cur)}).`);
      const pb = portals.reduce((a, [, v]) => a + v.brutto, 0), pk = portals.reduce((a, [, v]) => a + v.kosten, 0);
      const direct = chans.filter(([, v]) => v.gruppe === "Direkt").reduce((a, [, v]) => a + v.brutto, 0);
      if (direct && pb) out.push(`Direktbuchungen sparten rund <b>${money((direct * pk) / pb, cur)}</b> Portalkosten (Ø ${pct((pk / pb) * 100)}).`);
    }
    const best = chans.filter(([, v]) => v.netto_pro_nacht).sort((a, b) => b[1].netto_pro_nacht - a[1].netto_pro_nacht);
    if (best.length > 1) out.push(`Bester Erlös je Nacht: <b>${esc(chn(best[0][0]))}</b> ${money(best[0][1].netto_pro_nacht, cur)} netto, schwächster: ${esc(chn(best.at(-1)[0]))} ${money(best.at(-1)[1].netto_pro_nacht, cur)}.`);
    const storno = chans.filter(([, v]) => v.stornos > 0 && v.buchungen + v.stornos >= 3).sort((a, b) => b[1].stornoquote_prozent - a[1].stornoquote_prozent);
    if (storno.length) out.push(`Höchste Stornoquote: <b>${esc(chn(storno[0][0]))}</b> ${pct(storno[0][1].stornoquote_prozent)} (${storno[0][1].stornos} von ${storno[0][1].stornos + storno[0][1].buchungen}, ${money(storno[0][1].storno_volumen, cur)}).`);
    const lead = chans.filter(([, v]) => v.vorlauf_schnitt !== null && v.buchungen >= 2).sort((a, b) => a[1].vorlauf_schnitt - b[1].vorlauf_schnitt);
    if (lead.length > 1) out.push(`Kurzfristigste Gäste: <b>${esc(chn(lead[0][0]))}</b> (Ø ${num(lead[0][1].vorlauf_schnitt)} Tage Vorlauf), langfristigste: ${esc(chn(lead.at(-1)[0]))} (Ø ${num(lead.at(-1)[1].vorlauf_schnitt)} Tage).`);
    if (r.vergleich && r.veraenderung_prozent?.brutto !== null && r.veraenderung_prozent?.brutto !== undefined) {
      const ch = r.veraenderung_prozent.brutto;
      out.push(`Umsatz ${ch >= 0 ? "über" : "unter"} dem Vergleichszeitraum: ${delta(ch)} (${money(r.brutto - r.vergleich.brutto, cur)}).`);
    }
    if (r.prognose) out.push(`Prognose ${new Date().getFullYear()}: <b>${money(r.prognose.prognose, cur)}</b> brutto (gebucht ${money(r.prognose.gebucht, cur)} + ${t("Nachbuchung wie Vorjahr")} ${money(r.prognose.nachbuchung_vorjahr, cur)}).`);
    return out;
  }
  // v1.17.0: Mehrjahres-/Mehrperiodenvergleich als Tabelle (aktueller Zeitraum + alle Vergleiche).
  // Δ je Zeile = Veränderung zum nächstälteren Zeitraum (Wachstumskette), letzte Zeile ohne Δ
  multiTable(apt, r) {
    const list = r.vergleiche || [];
    if (list.length < 2) return "";
    const cur = apt.currency;
    const rows = [{ ...r, aktuell: true }, ...list];
    const chg = (a, b, k) => (b && !b.keine_daten && b[k] ? ((a[k] - b[k]) / b[k]) * 100 : null);
    const body = rows.map((x, i) => {
      const prev = rows[i + 1];
      if (x.keine_daten) return `<tr><td>${esc(periodName(x.von, x.bis))}</td><td colspan="10" class="empty" style="padding:6px 0">${t("Keine Daten – Historie in den Integrationsoptionen erhöhen")}</td></tr>`;
      return `<tr${x.aktuell ? ' style="font-weight:600"' : ""}><td>${esc(periodName(x.von, x.bis))}${x.stichtag ? ` <span class="sub">${t("Stand")} ${fdate(x.stichtag)}</span>` : ""}</td>
        <td class="n">${money(x.brutto, cur)}</td><td class="n">${delta(chg(x, prev, "brutto"))}</td>
        <td class="n">${money(x.netto, cur)}</td><td class="n">${money(x.kosten, cur)}</td><td class="n">${pct(x.kostenquote_prozent)}</td>
        <td class="n">${x.naechte}</td><td class="n">${pct(x.auslastung_prozent, 0)}</td><td class="n">${money(x.netto_pro_nacht, cur)}</td>
        <td class="n">${x.buchungen}</td><td class="n">${pct(x.direktanteil_prozent, 0)}</td></tr>`;
    }).join("");
    return `<h3>${t("Mehrfachvergleich")}</h3>
      <div class="scroll"><table><thead><tr><th>${t("Zeitraum")}</th><th class="n">${t("Brutto")}</th><th class="n" title="${t("Veränderung zum nächstälteren Zeitraum")}">Δ</th>
        <th class="n">${t("Netto")}</th><th class="n">${t("Provision & Gebühren")}</th><th class="n">${t("Kostenquote")}</th><th class="n">${t("Nächte")}</th>
        <th class="n">${t("Auslastung")}</th><th class="n">${t("Netto/Nacht")}</th><th class="n">${t("Buchungen")}</th><th class="n">${t("Direktanteil")}</th></tr></thead>
        <tbody>${body}</tbody></table></div>`;
  }
  // v1.17.0: acht Zusatzkacheln
  extraTiles(apt, r) {
    const cur = apt.currency;
    const c = r.vergleich;
    const dp = r.veraenderung_prozent || {}, dpp = r.veraenderung_punkte || {};
    if (r.frei_naechte === undefined) return ""; // älteres Backend ohne Zusatzkennzahlen
    const chans = Object.entries(r.kanaele);
    const portals = chans.filter(([, v]) => v.gruppe === "Portal" && v.brutto > 0).sort((a, b) => b[1].kostenquote_prozent - a[1].kostenquote_prozent);
    const perNight = chans.filter(([, v]) => v.netto_pro_nacht).sort((a, b) => b[1].netto_pro_nacht - a[1].netto_pro_nacht);
    const days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
    const wmax = Math.max(1, ...(r.wochentage || []).map((w) => w.naechte));
    // Mini-Balken je Wochentag (Nacht von … auf …); Fr/Sa kräftig = Wochenende
    const wk = `<div class="wk">${(r.wochentage || []).map((w, i) => `<div class="${i === 4 || i === 5 ? "we" : ""}"
      title="${t(days[i])}: ${w.naechte} ${t("Nächte")}${w.netto_pro_nacht ? ` · ${money(w.netto_pro_nacht, cur)}/${t("Nacht")}` : ""}">
      <i style="height:${Math.round((w.naechte / wmax) * 18)}px"></i>${t(days[i])}</div>`).join("")}</div>`;
    return [
      tile(t("Erlös je verfügbare Nacht"), money(r.erloes_verfuegbare_nacht, cur),
        `${t("netto")} · ${num(r.verfuegbare_naechte)} ${t("verfügbar")} ${delta(dp.erloes_verfuegbare_nacht)}`),
      // Potenzial = noch buchbare freie Nächte × Ø Netto/Nacht; entgangen = vergangene freie Nächte × Ø Netto/Nacht
      tile(t("Freie Nächte"), num(r.frei_naechte),
        `${r.frei_kommend} ${t("buchbar")} · ${t("Potenzial")} ${money(r.frei_potenzial_netto, cur)}`
        + (r.frei_vergangen ? `<br>${r.frei_vergangen} ${t("vergangen")} · ${t("entgangen")} ${money(r.frei_entgangen_netto, cur)}` : "")),
      tile(t("Storno-Volumen"), money(r.storno_volumen, cur),
        `${r.stornos} ${t("Stornos")} ${c ? `· ${t("Vergleich")} ${money(c.storno_volumen, cur)}` : ""} ${delta(dp.storno_volumen, "%", true)}`),
      tile(t("Offene Zahlungen"), money(r.offen_betrag, cur),
        `${r.offen_buchungen} ${t("Buchungen")}${r.offen_ueberfaellig ? ` · <span class="badge bad">${r.offen_ueberfaellig} ${t("überfällig")}</span>` : ""}`),
      // Kanalname in die Unterzeile, damit lange Namen die Kachel nicht sprengen
      tile(t("Teuerstes Portal"), portals.length ? pct(portals[0][1].kostenquote_prozent) : "–",
        portals.length ? `<b>${esc(portals[0][0])}</b>${portals.length > 1 ? `<br>${t("günstigstes")}: ${esc(portals.at(-1)[0])} ${pct(portals.at(-1)[1].kostenquote_prozent)}` : ""}` : ""),
      tile(t("Bester Kanal je Nacht"), perNight.length ? money(perNight[0][1].netto_pro_nacht, cur) : "–",
        perNight.length ? `<b>${esc(perNight[0][0])}</b> ${t("netto")}${perNight.length > 1 ? `<br>${t("schwächster")}: ${esc(perNight.at(-1)[0])} ${money(perNight.at(-1)[1].netto_pro_nacht, cur)}` : ""}` : ""),
      tile(t("Stammgäste"), pct(r.stammgaeste_prozent, 0),
        `${r.stammgaeste} / ${r.buchungen} ${t("Buchungen")} ${delta(dpp.stammgaeste_prozent ?? null, "pp")}`),
      tile(t("Wochenende Fr/Sa"), pct(r.wochenende_anteil_prozent, 0),
        `Ø ${money(r.wochenende_netto_pro_nacht, cur)} · ${t("So–Do")} ${money(r.wochentag_netto_pro_nacht, cur)}${wk}`),
    ].join("");
  }
  body(d) {
    const { apt, r, per = [], fin } = d;
    const cur = apt.currency;
    const s = this._state;
    const c = r.vergleich;
    const dp = r.veraenderung_prozent || {}, dpp = r.veraenderung_punkte || {};
    const cmpTxt = (k, f) => (c ? `${t("Vergleich")} ${f(c[k])}` : "");
    // Zusatzzeile „Endstand X (±%)“ ohne Bewertungsfarbe; nur wenn er sich vom Stand am Stichtag unterscheidet
    const endTxt = (k, f, pp = false) => {
      if (!fin || fin[k] === null || fin[k] === undefined) return "";
      const same = c && f(c[k]) === f(fin[k]);
      return `<span class="fin" title="${t("Endstand Vergleichszeitraum")} · ${t("Pfeil und Farbe vergleichen mit dem Stand am Stichtag, nicht mit dem Endstand.")}">${t("Endstand")} ${f(fin[k])}${same ? "" : ` (${chgText(r[k], fin[k], pp)})`}</span>`;
    };
    const cmpLabel = Object.fromEntries(FIN_COMPARE)[s.compare] || "";
    const m = s.metric;
    const reihe = r.reihe;
    const colors = Object.fromEntries(Object.keys(r.farben || {}).map((n) => [n, chColor(n)]));
    // v1.17.0: alle Kennzahlen gestapelt je Kanal (Brutto, Netto, Nächte, Provisionen/Gebühren);
    // ältere Backends ohne Kanalreihe → eine Gesamtreihe in Akzentfarbe
    const SERIES_KEY = { brutto: "kanaele", netto: "kanaele_netto", naechte: "kanaele_naechte", kosten: "kanaele_kosten" };
    const byCh = reihe[SERIES_KEY[m]];
    const stacks = byCh
      ? Object.entries(byCh).map(([name, values]) => ({ name, values, color: colors[name] || colorOf(apt, name) }))
        .filter((st) => st.values.some((v) => v > 0))
        .sort((a, b) => b.values.reduce((x, y) => x + y, 0) - a.values.reduce((x, y) => x + y, 0))
      : [{ name: t(METRIC_LABEL[m]), values: reihe[m] || [], color: PAL[DARK ? "dark" : "light"].acc }];
    const fmt = m === "naechte" ? (v) => num(v) : (v) => money(v, cur);
    // Legende: Farbe, Kanal, Summe im Zeitraum, Anteil; dazu die gestrichelte Vergleichslinie
    const stackTotal = stacks.reduce((a, st) => a + st.values.reduce((x, y) => x + y, 0), 0);
    const legendHtml = `<div class="legend">${stacks.map((st) => {
      const v = st.values.reduce((x, y) => x + y, 0);
      return `<span><i style="background:${st.color}"></i>${esc(st.name)} <b>${fmt(v)}</b><em>${stackTotal ? pct((v / stackTotal) * 100, 0) : ""}</em></span>`;
    }).join("")}</div>`;
    const many = (r.vergleiche || []).length > 1;
    const line = c?.reihe?.[m] ? { values: c.reihe[m], label: many ? periodName(c.von, c.bis) : t(cmpLabel) } : null;
    // Weitere Vergleichszeiträume: nur mit Daten, Deckkraft und Strichmuster nehmen mit dem Alter ab
    const extra = (r.vergleiche || []).slice(1).filter((v) => !v.keine_daten && v.reihe?.[m])
      .map((v, i) => ({ values: v.reihe[m], label: periodName(v.von, v.bis), op: Math.max(0.12, 0.4 - i * 0.08), dash: i % 2 ? "2 3" : "8 4" }));
    const chans = Object.entries(r.kanaele);
    const cmpCh = c?.kanaele || {};
    const table = chans.map(([n, v]) => `<tr><td><span class="dot" style="background:${colors[n] || colorOf(apt, n)}"></span> ${esc(chn(n))}</td>
      <td class="n">${money(v.brutto, cur)}</td><td class="n" style="min-width:90px">${pct(v.anteil_prozent, 0)}
        <div class="bar-in" style="width:${v.anteil_prozent}%;background:${colors[n] || colorOf(apt, n)}"></div></td>
      <td class="n">${cmpCh[n] ? delta(((v.brutto - cmpCh[n].brutto) / (cmpCh[n].brutto || 1)) * 100) : c ? `<span class="badge">neu</span>` : ""}</td>
      <td class="n">${money(v.netto, cur)}</td>
      <td class="n" title="${t("Provision")} ${money(v.provision, cur, 2)} · ${t("Zahlungsgebühren")} ${money(v.zahlungsgebuehren, cur, 2)}">${v.kosten ? money(v.kosten, cur) : "–"}${v.zahlungsgebuehren ? `<span class="sub2">${t("davon Gebühren")} ${money(v.zahlungsgebuehren, cur)}</span>` : ""}</td>
      <td class="n">${pct(v.kostenquote_prozent)}</td><td class="n">${v.naechte}</td>
      <td class="n">${money(v.netto_pro_nacht, cur)}</td><td class="n">${v.buchungen}</td><td class="n">${v.stornos ? pct(v.stornoquote_prozent, 0) : "–"}</td>
      <td class="n">${num(v.aufenthalt_schnitt, 1)}</td><td class="n">${num(v.vorlauf_schnitt)}</td><td class="n">${num(v.personen_schnitt, 1)}</td></tr>`).join("");
    const ins = this.insights(apt, r);
    return `
      <div class="head"><h2>${esc(this._config.title || t("Finanzen"))}${this.multi ? ` <span class="sub">${t("Alle Wohnungen")}</span>` : ""}</h2>
        <span class="sub">${fdate(r.von)} – ${fdate(iso(addDays(D(r.bis), -1)))}${c ? `, ${t("Vergleich")} ${fdate(c.von)} – ${fdate(iso(addDays(D(c.bis), -1)))}${r.stichtag_vergleich ? ` (${t("Stand")} ${fdate(r.stichtag_vergleich)})` : ""}` : ""}</span></div>
      ${filterBarHtml(this, d, { compares: FIN_COMPARE, rasters: FIN_RASTER, quick: true,
        // Mehrfachvergleich (nur Finanzen): Anzahl Vergleichsjahre bzw. -perioden
        afterCmp: s.compare !== "kein" ? `<select data-k="ccount" title="${t("Anzahl Vergleichszeiträume")}">${COMPARE_COUNTS.map((n) =>
          `<option value="${n}" ${n === s.compareCount ? "selected" : ""}>${n} ${t(s.compare === "vorperiode" ? (n === 1 ? "Periode" : "Perioden") : (n === 1 ? "Jahr" : "Jahre"))}</option>`).join("")}</select>` : "" })}
      <div class="grid">
        ${tile(t("Brutto"), money(r.brutto, cur), `${cmpTxt("brutto", (v) => money(v, cur))} ${delta(dp.brutto)}${endTxt("brutto", (v) => money(v, cur))}`)}
        ${tile(t("Netto"), money(r.netto, cur), `${cmpTxt("netto", (v) => money(v, cur))} ${delta(dp.netto)}${endTxt("netto", (v) => money(v, cur))}`)}
        ${tile(t("Kosten"), money(r.kosten, cur), `${pct(r.kostenquote_prozent)} ${delta(dpp.kostenquote_prozent, "pp", true)}`)}
        ${tile(t("Auslastung"), pct(r.auslastung_prozent, 0), `${r.naechte} ${t("Nächte")} · ${r.gesperrt_naechte} ${t("Gesperrt")} ${delta(dpp.auslastung_prozent, "pp")}${endTxt("auslastung_prozent", (v) => pct(v, 0), true)}`)}
        ${tile(t("Netto/Nacht"), money(r.netto_pro_nacht, cur), `${t("Brutto/Nacht")} ${money(r.brutto_pro_nacht, cur)} ${delta(dp.netto_pro_nacht)}${endTxt("netto_pro_nacht", (v) => money(v, cur))}`)}
        ${tile(t("Buchungen"), num(r.buchungen), `${r.stornos} ${t("Stornos")} (${pct(r.stornoquote_prozent, 0)}) ${delta(dp.buchungen)}${endTxt("buchungen", (v) => num(v))}`)}
        ${tile(t("Ø Aufenthalt"), `${num(r.aufenthalt_schnitt, 1)} N`, `${cmpTxt("aufenthalt_schnitt", (v) => num(v, 1))} ${delta(dp.aufenthalt_schnitt)}`)}
        ${tile(t("Ø Vorlauf"), `${num(r.vorlauf_schnitt)} ${t("Tage")}`, `Median ${num(r.vorlauf_median)} · ${cmpTxt("vorlauf_schnitt", (v) => num(v))}`)}
        ${tile(t("Ø Personen"), num(r.personen_schnitt, 1), `${r.hunde} × 🐕 · ${money(r.preis_pro_buchung, cur)} je Buchung`)}
        ${tile(t("Direktanteil"), pct(r.direktanteil_prozent, 0), delta(dpp.direktanteil_prozent, "pp"))}
        ${r.prognose ? tile(t("Prognose Jahr"), money(r.prognose.prognose, cur), `${t("Netto")} ${money(r.prognose.prognose_netto, cur)}`) : ""}
        ${this.extraTiles(apt, r)}
      </div>
      <h3>${t("Diagramm")}</h3>
      <div class="row"><div class="seg">${Object.keys(METRIC_LABEL).map((k) => `<button data-metric="${k}" aria-pressed="${m === k}">${t(METRIC_LABEL[k])}</button>`).join("")}</div>
        ${line ? `<span class="sub">┄ ${esc(line.label)}</span>` : ""}</div>
      <div class="split"><div>${barChart({ labels: reihe.labels, stacks, line, fmt, unit: reihe.einheit, daily: reihe.einheit === "tag", extra, starts: reihe.starts })}
          ${legendHtml.replace("</div>", (line ? `<span><i class="ln"></i><em>${esc(line.label)} ${fmt((line.values || []).reduce((x, y) => x + (y || 0), 0))}</em></span>` : "")
            + extra.map((e) => `<span><i class="ln" style="opacity:${e.op};border-top-style:${e.dash === "2 3" ? "dotted" : "dashed"}"></i><em>${esc(e.label)} ${fmt(e.values.reduce((x, y) => x + (y || 0), 0))}</em></span>`).join("") + "</div>")}
          <div class="tip" data-k="tip"></div></div>
        ${m === "kosten"
          // Provisionen: Verteilung der Kosten je Portal, in der Mitte die Kostenquote gesamt
          ? `<div class="share">${donut(chans.filter(([, v]) => v.kosten > 0).map(([n, v]) => ({ name: chn(n), value: v.kosten, color: colors[n] || colorOf(apt, n) })), pct(r.kostenquote_prozent, 1))}
              <span class="sub">${t("Kostenquote")} · ${money(r.kosten, cur)}</span></div>`
          : `<div class="share">${donut(chans.map(([n, v]) => ({ name: chn(n), value: m === "naechte" ? v.naechte : v[m], color: colors[n] || colorOf(apt, n) })).filter((p) => p.value > 0), pct(r.direktanteil_prozent, 0))}
              <span class="sub">${t("Direktanteil")}</span></div>`}</div>
      ${this.multiTable(apt, r)}
      ${per.length > 1 ? `<h3>${t("Wohnungen im Vergleich")}</h3>
      <div class="scroll"><table><thead><tr><th>${t("Wohnung")}</th><th class="n">${t("Brutto")}</th><th class="n">${t("Anteil")}</th><th class="n">Δ</th>
        <th class="n">${t("Netto")}</th><th class="n">${t("Auslastung")}</th><th class="n">${t("Nächte")}</th><th class="n">${t("Netto/Nacht")}</th>
        <th class="n">${t("Buchungen")}</th><th class="n">${t("Direktanteil")}</th></tr></thead><tbody>
        ${per.map(({ w, x }) => `<tr><td>${codeTag(w.kuerzel)} ${esc(w.name)}</td><td class="n">${money(x.brutto, cur)}</td>
          <td class="n">${pct(r.brutto ? (x.brutto / r.brutto) * 100 : null, 0)}</td><td class="n">${delta(x.veraenderung_prozent?.brutto)}</td>
          <td class="n">${money(x.netto, cur)}</td><td class="n">${pct(x.auslastung_prozent, 0)} ${delta(x.veraenderung_punkte?.auslastung_prozent, "pp")}</td>
          <td class="n">${x.naechte}</td><td class="n">${money(x.netto_pro_nacht, cur)}</td><td class="n">${x.buchungen}</td>
          <td class="n">${pct(x.direktanteil_prozent, 0)}</td></tr>`).join("")}</tbody></table></div>` : ""}
      ${ins.length ? `<h3>${t("Erkenntnisse")}</h3><ul class="ins">${ins.map((i) => `<li>${i}</li>`).join("")}</ul>` : ""}
      <h3>${t("Kanaltabelle")}</h3>
      <div class="scroll"><table><thead><tr><th>${t("Kanal")}</th><th class="n">${t("Brutto")}</th><th class="n">${t("Anteil")}</th><th class="n">Δ</th>
        <th class="n">${t("Netto")}</th><th class="n">${t("Provision & Gebühren")}</th><th class="n">${t("Kostenquote")}</th><th class="n">${t("Nächte")}</th><th class="n">${t("Netto/Nacht")}</th>
        <th class="n">${t("Buchungen")}</th><th class="n">${t("Stornoquote")}</th><th class="n">${t("Ø Aufenthalt")}</th><th class="n">${t("Ø Vorlauf")}</th><th class="n">${t("Ø Personen")}</th></tr></thead>
        <tbody>${table || `<tr><td colspan="14" class="empty">${t("Keine Daten")}</td></tr>`}</tbody>
        <tfoot><tr><td>${t("Summe")}</td><td class="n">${money(r.brutto, cur)}</td><td class="n">100 %</td><td class="n">${delta(dp.brutto)}</td>
          <td class="n">${money(r.netto, cur)}</td><td class="n">${money(r.kosten, cur)} ${delta(dp.kosten, "%", true)}</td><td class="n">${pct(r.kostenquote_prozent)}</td><td class="n">${r.naechte}</td>
          <td class="n">${money(r.netto_pro_nacht, cur)}</td><td class="n">${r.buchungen}</td><td class="n">${pct(r.stornoquote_prozent, 0)}</td>
          <td class="n">${num(r.aufenthalt_schnitt, 1)}</td><td class="n">${num(r.vorlauf_schnitt)}</td><td class="n">${num(r.personen_schnitt, 1)}</td></tr></tfoot></table></div>
      ${gloss(["PP", "Δ", "Ø", "N"])}`;
  }
  bind(root) {
    // Filterleiste wie Statistik (v1.18.0b8)
    bindFilterBar(this, root);
    root.querySelector('[data-k="ccount"]')?.addEventListener("change", (e) => this.setState({ compareCount: Number(e.target.value) }, true));
    root.querySelectorAll("[data-metric]").forEach((el) => el.addEventListener("click", () => this.setState({ metric: el.dataset.metric })));
    const tip = root.querySelector('[data-k="tip"]');
    root.querySelectorAll("rect.hit").forEach((el) => {
      const show = () => { if (tip) tip.textContent = el.dataset.tip; };
      el.addEventListener("mouseenter", show);
      el.addEventListener("click", show);
    });
  }
}

// ===========================================================================
// Buchungsdetail (Overlay, von allen Karten geöffnet)
// ===========================================================================
// v1.16.0: Antwortstatus + KI-Vorschlag – gemeinsam für Posteingang und Buchungsdialog
const REPLY_CSS = `
  .pending { display: inline-block; margin-top: 2px; padding: 1px 8px; border-radius: 999px; font-size: .75rem; font-weight: 600;
    background: var(--sm-bad); color: #fff; }
  .done { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: .75rem; font-weight: 600;
    background: color-mix(in srgb, var(--sm-good) 18%, transparent); color: var(--sm-good); }
  .noreply { display: flex; gap: 8px; align-items: center; margin: 4px 0 8px; flex-wrap: wrap; }
  .btn[disabled].locked { opacity: .45; cursor: not-allowed; }
  .sugbox { margin-top: 8px; padding: 8px 12px; border-radius: 10px; font-size: .85rem;
    background: color-mix(in srgb, var(--sm-accent) 10%, transparent); border-left: 4px solid var(--sm-accent); }
  .sugbox.urgent { border-left-color: var(--sm-bad); background: color-mix(in srgb, var(--sm-bad) 12%, transparent); }
`;
// Antwortstatus aus dem frischen Verlauf: offen nur, wenn die neueste sichtbare Nachricht VOM Gast ist (typ 1)
// und nicht als „keine Antwort nötig“ markiert wurde (erledigt_id = abgehakte Gastnachricht, v1.14.0)
function threadStatus(d, prev = {}) {
  const last = newestFirst((d?.nachrichten || []).filter((m) => !m.intern))[0];
  const guest = !!last && Number(last.typ) === 1;
  const doneId = prev?.erledigt_id;
  const dismissed = guest && doneId != null && Number(last.id) <= Number(doneId);
  return { ...prev, offen: guest && !dismissed, ohne_antwort: dismissed, letzte_zeit: last?.zeit };
}
// Statuszeile über dem Verlauf (data-noreply / data-undo tragen die Buchungs-ID)
const noReplyHtml = (st, id) => st?.offen ? `<div class="noreply"><span class="pending">💬 ${t("Antwort offen")}</span>
    <button class="btn flat" data-noreply="${id}">✓ ${t("Keine Antwort nötig")}</button></div>`
  : st?.ohne_antwort ? `<div class="noreply"><span class="done">✓ ${t("Ohne Antwort erledigt")}</span>
    <button class="btn flat" data-undo="${id}">↶ ${t("Rückgängig")}</button></div>` : "";
// Hinweisbox zum KI-Vorschlag (Absicht, Hinweise, Wissenslücke, offene Stellen)
const sugHtml = (sug) => sug ? `<div class="sugbox ${sug.dringend ? "urgent" : ""}"><b>✨ ${sug.dringend ? `${t("DRINGEND")} · ` : ""}${esc(t(INTENT_LABEL[sug.absicht] || sug.absicht))}</b>
    ${sug.zusammenfassung ? ` · ${esc(sug.zusammenfassung)}` : ""}
    ${sug.hinweis ? `<div>ℹ️ ${esc(sug.hinweis)}</div>` : ""}
    ${sug.wissensluecke ? `<div>❓ Wissenslücke: ${esc(sug.wissensluecke)}</div>` : ""}
    ${sug.offen ? `<div>✏️ Bitte die Stellen [OFFEN: …] ergänzen.</div>` : ""}</div>` : "";
// Anlass-Auswahl + ✨-Knopf. KI gesperrt → ausgegraut mit Tooltip (eigentliche Sperre liegt im Backend)
const aiCtlHtml = (ai, allowed, reason, thinking) => {
  if (!ai) return "";
  const lock = !allowed;
  const tip = esc(reason || t("KI in den Integrationsoptionen deaktiviert"));
  return `<select data-k="anlass" ${lock ? `disabled title="${tip}"` : ""}>${["antwort", "willkommen", "anreise", "abreise", "bewertung"].map((a) => `<option value="${a}">${esc(t(OCCASION_LABEL[a] || a))}</option>`).join("")}</select>
    <button class="btn flat ${lock ? "locked" : ""}" data-act="ai" ${thinking || lock ? "disabled" : ""} ${lock ? `title="${tip}"` : ""}>${lock ? `🔒 ${t("KI gesperrt")}` : thinking ? `⏳ ${t("KI denkt …")}` : `✨ ${t("Vorschlag")}`}</button>`;
};
const DIALOG_CSS = `
  .back { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 10000; font-family: ${FONT}; display: flex; justify-content: center; align-items: flex-start;
    overflow-y: auto; padding: 24px 8px; box-sizing: border-box; }
  .dlg { background: var(--sm-surf); color: var(--sm-ink); border-radius: 18px; width: min(780px, 100%); border: 1px solid var(--sm-line);
    padding: 22px 24px; box-sizing: border-box; box-shadow: 0 16px 48px rgba(0,0,0,.35); font-family: ${FONT}; }
  .dlg h2 { font-size: 1.4rem; letter-spacing: -.015em; }
  .top { display: flex; gap: 10px; align-items: flex-start; } .top h2 { flex: 1; }
  .x { background: none; border: none; font-size: 1.6rem; cursor: pointer; color: var(--sm-muted); line-height: 1; }
  .kv { display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; font-size: .9rem; }
  .kv dt { color: var(--sm-muted); } .kv dd { margin: 0; }
  .sec { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 8px 24px; }
  .msgs { display: flex; flex-direction: column; gap: 8px; max-height: 360px; overflow-y: auto; padding: 4px; }
  .msg { max-width: 85%; padding: 9px 13px; border-radius: 14px; font-size: .9rem; white-space: pre-wrap; word-break: break-word;
    background: var(--sm-surf2); border: 1px solid var(--sm-line); align-self: flex-start; }
  .msg.out { align-self: flex-end; background: color-mix(in srgb, var(--sm-accent) 18%, transparent); }
  .msg .h { font-size: .72rem; color: var(--sm-muted); margin-bottom: 2px; }
  .acts { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--sm-line); }
  a { color: var(--sm-accent); }
`;
class SmoobuBookingDialog extends HTMLElement {
  static open(hass, id, target = {}) {
    document.querySelector("smoobu-booking-dialog")?.remove();
    const el = document.createElement("smoobu-booking-dialog");
    el.hass = hass;
    el.store = SmoobuStore.get(hass);
    el.target = target;
    el.rid = id;
    document.body.appendChild(el);
    return el;
  }
  // v1.16.0: Antwortstatus (st), KI-Vorschlag (sug), Assistent vorhanden/erlaubt, Entwurf bleibt beim Neuzeichnen erhalten
  constructor() { super(); this.attachShadow({ mode: "open" }); this.data = null; this.err = null;
    this.st = null; this.sug = null; this.ai = false; this.aiAllowed = false; this.aiReason = ""; this.thinking = false; this.draft = null; }
  connectedCallback() {
    this._esc = (e) => e.key === "Escape" && this.remove();
    window.addEventListener("keydown", this._esc);
    this.render();
    this.load();
  }
  disconnectedCallback() { window.removeEventListener("keydown", this._esc); }
  async load() {
    try {
      const [info, d, ms, a] = await Promise.all([this.store.getInfo(),
        this.store.ws("smoobu/booking", { ...this.target, reservation_id: this.rid }, { cache: false }),
        // Antwortstatus + Assistent sind optional: schlägt einer fehl, bleibt der Dialog ohne diese Teile nutzbar
        this.store.ws("smoobu/message_status", { ...this.target, reservation_ids: [this.rid] }, { cache: false }).catch(() => null),
        this.store.ws("smoobu/assistant/state", this.target, { cache: false }).catch(() => null)]);
      this.apt = info.wohnungen.find((w) => w.apartment_id === (d.buchung?.wohnung_id ?? this.target.apartment_id)) || info.wohnungen[0];
      this.data = d;
      // Status aus dem frischen Verlauf ableiten (erledigt_id kommt aus message_status)
      this.st = threadStatus(d, ms?.status?.[String(this.rid)] || {});
      this.ai = !!a; this.aiAllowed = !!a?.ki_erlaubt; this.aiReason = a?.ki_sperre || "";
      // Offenen automatischen Vorschlag übernehmen – nur wenn noch nichts getippt wurde
      if (!this.sug) this.sug = a?.vorschlaege?.find((v) => v.buchung_id === this.rid && v.status === "offen") || null;
      if (this.draft === null) this.draft = this.sug?.antwort || "";
    } catch (e) { this.err = e.message || String(e); }
    this.render();
  }
  render() {
    const d = this.data;
    let inner;
    if (this.err) inner = `<div class="err">${t("Fehler")}: ${esc(this.err)}</div>`;
    else if (!d) inner = `<div class="empty">${t("Laden …")}</div>`;
    else inner = this.content(d);
    DARK = Theme.dark(this.hass);
    const vars = `:host { ${CSS_VARS(PAL[DARK ? "dark" : "light"])} --sm-scheme: ${DARK ? "dark" : "light"}; }`;
    const multi = (this.store.info?.wohnungen || []).length > 1;
    const code = multi && d?.buchung ? codeTag(aptCode(this.store.info, d.buchung.wohnung_id)) : "";
    this.shadowRoot.innerHTML = `<style>${vars}${BASE_CSS}${DIALOG_CSS}${REPLY_CSS}</style><div class="back"><div class="dlg">
      <div class="top"><h2>${d?.buchung ? (d.buchung.blockiert ? `🔒 ${t("Sperrzeit")}` : esc(d.buchung.gast)) + (d.buchung.hund ? " 🐕" : "") + code : t("Details")}</h2>
      <button class="x" data-act="close" aria-label="close">×</button></div>${inner}</div></div>`;
    this.bind();
  }
  content(d) {
    const b = d.buchung || {};
    const raw = d.smoobu || {};
    const cur = this.apt?.currency || "EUR";
    const color = colorOf(this.apt, b.kanal, b.blockiert);
    const kv = (rows) => `<dl class="kv">${rows.filter(Boolean).map(([k, v]) => `<dt>${t(k)}</dt><dd>${v}</dd>`).join("")}</dl>`;
    const positions = (b.positionen || []).filter((p) => Number(p.betrag) !== 0 || p.typ === "basePrice").map((p) => `<div class="row"><span class="grow">${esc(priceName(p))}</span><span>${money(p.betrag, cur, 2)}</span></div>`).join("");
    const msgs = newestFirst(d.nachrichten).map((m) => `<div class="msg ${Number(m.typ) === 2 ? "out" : ""}"><div class="h">${dirLabel(m)}${m.zeit ? " · " + esc(fdate(m.zeit, DT_FMT)) : ""}${m.betreff ? " · " + esc(m.betreff) : ""}</div>${msgHtml(m.text)}</div>`).join("");
    const canCancel = !b.blockiert && b.gruppe === "Direkt" && !b.storniert && b.status !== "vergangen";
    return `
      <div class="row" style="margin-bottom:12px"><span class="badge"><span class="dot" style="background:${color}"></span> ${esc(chn(b.kanal))}</span>
        <span class="badge"><ha-icon icon="${STATUS_ICON[b.status] || "mdi:help"}"></ha-icon> ${t(b.status || "")}</span>
        ${b.referenz ? `<span class="badge">#${esc(b.referenz)}</span>` : ""}<span class="badge">ID ${esc(b.id)}</span>
        ${b.offen > 0 ? `<span class="badge bad">${t("Offen")} ${money(b.offen, cur, 2)}</span>` : b.blockiert ? ""
          // v1.17.0 (Portal): ohne Markierung neutral „Bezahlt über <Kanal>“ – Geld ist beim Portal, aber noch nicht
          // als erhalten markiert (kein Rot: nichts überfällig; kein Grün: der Betreiber hat es noch nicht abgehakt)
          : portalPay(b) && !b.bezahlt ? `<span class="badge">${t("Bezahlt über")} ${esc(chn(b.kanal))}</span>`
          : `<span class="badge good">✓ ${t("bezahlt")}</span>`}</div>
      ${d.fehler ? `<div class="err">${esc(d.fehler)}</div>` : ""}
      <div class="sec">
        <div><h3>${t("Aufenthalt")}</h3>${kv([
          ["Anreise", `${fdow(b.anreise)}${b.check_in ? " · " + esc(b.check_in) : ""}`],
          ["Abreise", `${fdow(b.abreise)}${b.check_out ? " · " + esc(b.check_out) : ""}`],
          ["Nächte", b.naechte],
          !b.blockiert && ["Gäste", `${b.erwachsene} + ${b.kinder} (${b.personen})`],
          b.hund_hinweis && ["Hund", esc(b.hund_hinweis)],
          b.vorlauf_tage !== null && b.vorlauf_tage !== undefined && ["Vorlauf", `${b.vorlauf_tage} ${t("Tage")}`],
          b.erstellt && ["Erstellt", fdate(b.erstellt)],
        ])}
        ${!b.blockiert ? `<div class="row" style="margin-top:8px">
          <label>${t("Ankunftszeit")} <input type="time" data-k="ci" value="${esc((b.check_in || "").slice(0, 5))}"></label>
          <label>${t("Abreisezeit")} <input type="time" data-k="co" value="${esc((b.check_out || "").slice(0, 5))}"></label>
          <button class="btn flat" data-act="times">${t("Speichern")}</button></div>` : ""}</div>
        ${!b.blockiert ? `<div><h3>${t("Gast")}</h3>${kv([
          ["Gast", esc(b.gast)],
          b.email && ["E-Mail", `<a href="mailto:${esc(b.email)}">${esc(b.email)}</a>`],
          b.telefon && ["Telefon", `<a href="tel:${esc(b.telefon)}">${esc(b.telefon)}</a>`],
          b.sprache && ["Sprache", esc(b.sprache)],
          raw.address && (raw.address.street || raw.address.city) && ["Adresse", esc([raw.address.street, raw.address.postalCode, raw.address.location || raw.address.city, raw.address.country].filter(Boolean).join(", "))],
        ])}</div>
        <div><h3>${t("Preis")}</h3>${positions}${kv([
          ["Brutto", `<b>${money(b.brutto, cur, 2)}</b>${b.naechte ? ` · ${money(b.brutto_pro_nacht, cur, 2)}/${t("Nacht")}` : ""}`],
          ["Provision", `${money(b.provision, cur, 2)}${b.provision_quelle === "konfiguration" ? " (geschätzt)" : ""}`],
          b.zahlungsgebuehr && ["Zahlungsgebühr", money(b.zahlungsgebuehr, cur, 2)],
          ["Netto", `<b>${money(b.netto, cur, 2)}</b> · ${money(b.netto_pro_nacht, cur, 2)}/${t("Nacht")}`],
          b.anzahlung && ["Anzahlung", `${money(b.anzahlung, cur, 2)} ${b.anzahlung_bezahlt || b.bezahlt ? "✓" : "✗"}`],
          b.offen > 0 && ["Restbetrag", `<b style="color:var(--sm-bad)">${money(b.offen, cur, 2)}</b>`],
          b.kurtaxe && ["Kurtaxe", money(b.kurtaxe, cur, 2)],
        ])}${this.payHtml(b)}</div>` : ""}
        <div><h3>${t("Notiz")}</h3><textarea data-k="notice">${esc(b.notiz || "")}</textarea>
          <div class="row"><button class="btn flat" data-act="notice">${t("Speichern")}</button></div>
          ${b.assistent_notiz ? `<div class="sub" style="margin-top:8px;white-space:pre-wrap">${esc(b.assistent_notiz)}</div>` : ""}</div>
      </div>
      ${!b.blockiert ? `<h3>${t("Nachrichten")} (${(d.nachrichten || []).length})</h3>${noReplyHtml(this.st, this.rid)}
        <div class="msgs">${msgs || `<div class="muted">${t("keine")}</div>`}</div>
        ${sugHtml(this.sug)}
        ${can("antworten", b.wohnung_id) ? `<textarea data-k="msg" placeholder="${t("Antworten")} ${t("an den Gast")} …" style="margin-top:8px;min-height:110px">${esc(this.draft || "")}</textarea>
        <div class="row">${aiCtlHtml(this.ai, this.aiAllowed, this.aiReason, this.thinking)}<span class="grow"></span><button class="btn" data-act="send">✉ ${t("Senden")}</button></div>` : ""}` : ""}
      <div class="acts">
        ${b.blockiert && can("belegung", b.wohnung_id) ? `<button class="btn danger" data-act="unblock">🔓 ${t("Sperre löschen")}</button>` : ""}
        ${canCancel && can("belegung", b.wohnung_id) ? `<button class="btn danger" data-act="cancel">${t("Stornieren")}</button>` : ""}
        <span class="grow"></span>
        <a class="btn flat" href="https://login.smoobu.com/" target="_blank" rel="noopener" style="text-decoration:none"
          title="${esc(`${t("Smoobu-Anmeldung öffnen – Buchung dort über die ID suchen")}: ${b.id}`)}">${t("Smoobu öffnen")} ↗</a>
      </div>`;
  }
  // v1.17.0: Zahlungseingang markieren (Logik gemeinsam mit der Übersicht: payInfo/markPayment)
  payHtml(b) {
    const p = payInfo(b);
    const btns = [
      p.canPre && `<button class="btn flat" data-act="pre">✓ ${t("Anzahlung erhalten")}</button>`,
      p.canPay && `<button class="btn" data-act="paid">✓ ${t("Zahlung erhalten")}</button>`,
      p.canUnpre && `<button class="btn flat" data-act="unpre">↶ ${t("Anzahlung offen")}</button>`,
      p.canUnpay && `<button class="btn flat" data-act="unpaid">↶ ${t("Als offen markieren")}</button>`,
    ].filter(Boolean);
    return btns.length ? `<div class="row" style="margin-top:8px;flex-wrap:wrap;gap:8px">${btns.join("")}</div>` : "";
  }
  bind() {
    const r = this.shadowRoot;
    r.querySelector(".back")?.addEventListener("click", (e) => { if (e.target.classList.contains("back")) this.remove(); });
    r.querySelectorAll("[data-act]").forEach((el) => el.addEventListener("click", () => this.act(el.dataset.act)));
    // Entwurf mitschreiben, damit er beim Neuzeichnen (z. B. nach „Keine Antwort nötig“) nicht verloren geht
    r.querySelector('[data-k="msg"]')?.addEventListener("input", (e) => { this.draft = e.target.value; });
    r.querySelector("[data-noreply]")?.addEventListener("click", () => this.noReply(true));
    r.querySelector("[data-undo]")?.addEventListener("click", () => this.noReply(false));
  }
  // v1.16.0: „Keine Antwort nötig“ / Rückgängig – gleicher Backend-Aufruf wie im Posteingang
  async noReply(done) {
    try {
      const r = await this.store.ws("smoobu/message_done", { ...this.target, reservation_id: this.rid, done }, { cache: false });
      this.st = threadStatus(this.data, r.status || {});
      if (done) {                         // offener KI-Vorschlag gilt im Backend als „ignoriert“
        if (this.sug && this.draft === this.sug.antwort) this.draft = "";   // unveränderten Entwurf mit entfernen
        this.sug = null;
      }
      this.store.invalidate();            // Zähler in Kopfleiste/Übersicht/Posteingang neu laden
      toast(t(done ? "Ohne Antwort erledigt" : "Gespeichert"));
      this.render();
    } catch (e) { toast(`${t("Fehler")}: ${e.message || e}`); }
  }
  // v1.16.0: KI-Antwortvorschlag – füllt das Eingabefeld, gesendet wird erst nach Klick auf „Senden“
  async aiSuggest() {
    if (!this.aiAllowed) { toast(this.aiReason || t("KI in den Integrationsoptionen deaktiviert")); return; }
    const anlass = this.shadowRoot.querySelector('[data-k="anlass"]')?.value || "antwort";
    this.thinking = true; this.render();
    try {
      this.sug = await this.store.ws("smoobu/assistant/suggest", { ...this.target, reservation_id: this.rid, anlass }, { cache: false });
      this.draft = this.sug.antwort || "";
    } catch (e) { toast(`${t("Fehler")}: ${e.message || e}`); }
    this.thinking = false; this.render();
  }
  async act(a) {
    if (a === "close") return this.remove();
    if (a === "ai") return this.aiSuggest();
    const v = (k) => this.shadowRoot.querySelector(`[data-k="${k}"]`)?.value;
    const id = this.rid;
    // v1.17.0: Zahlungsstatus – markPayment fragt nach, schreibt und meldet selbst
    const pay = { paid: ["zahlung", true], unpaid: ["zahlung", false], pre: ["anzahlung", true], unpre: ["anzahlung", false] }[a];
    if (pay) {
      if (await markPayment(this.store, this.data?.buchung || {}, pay[0], pay[1], this.apt?.currency || "EUR")) this.load();
      return;
    }
    try {
      if (a === "times") {
        // v1.17.1: wie alle Schreibaktionen erst nach Bestätigung (wirkt direkt in Smoobu)
        const data = { reservation_id: id };
        if (v("ci")) data.arrival_time = v("ci");
        if (v("co")) data.departure_time = v("co");
        if (!data.arrival_time && !data.departure_time) return;
        const what = [data.arrival_time && `${t("Ankunftszeit")} ${data.arrival_time}`, data.departure_time && `${t("Abreisezeit")} ${data.departure_time}`].filter(Boolean).join(", ");
        if (!(await confirmDialog(`${this.data?.buchung?.gast || ""}: ${what} ${t("in Smoobu speichern")}?`))) return;
        await this.store.service("update_reservation", data);
      } else if (a === "notice") {
        if (!(await confirmDialog(`${t("Notiz")} ${t("in Smoobu speichern")}?`))) return;
        await this.store.service("update_reservation", { reservation_id: id, notice: v("notice") || "" });
      } else if (a === "send") {
        const text = (v("msg") || "").trim();
        if (!text) return;
        if (/\[OFFEN/i.test(text)) { toast("Bitte zuerst die Stellen [OFFEN: …] ergänzen"); return; }
        if (!(await confirmDialog(`${t("Senden")} ${t("an den Gast")}?`))) return;
        // Über den Assistenten senden → Antwort wird als Lernbeispiel gespeichert
        await this.store.ws("smoobu/assistant/send", { ...this.target, reservation_id: id, text }, { cache: false });
        this.store.invalidate();
        this.draft = ""; this.sug = null;
        toast(t("Gesendet"));
        return this.load();
      } else if (a === "unblock") {
        if (!(await confirmDialog(`${t("Sperre löschen")}?`))) return;
        await this.store.service("delete_reservation", { reservation_id: id });
        toast(t("Gespeichert"));
        return this.remove();
      } else if (a === "cancel") {
        if (!(await confirmDialog(`${t("Stornieren")}: ${this.data?.buchung?.gast}? ${t("Wirklich?")}`))) return;
        await this.store.service("delete_reservation", { reservation_id: id, allow_booking: true });
        toast(t("Gespeichert"));
        return this.remove();
      }
      toast(t("Gespeichert"));
      this.load();
    } catch (e) {
      toast(`${t("Fehler")}: ${e.message || e}`);
    }
  }
}

// ===========================================================================
// Posteingang
// ===========================================================================
class SmoobuInboxCard extends SmoobuCard {
  static defaults = { title: "", days_back: 14, days_ahead: 60, message_entity: "" };
  // ai = Assistent vorhanden (✨ anzeigen), aiAllowed = KI erlaubt (sonst ausgegraut), aiReason = Tooltip (v1.14.0)
  static initialState = () => ({ sel: null, thread: null, loadingThread: false, draft: "", sug: null, thinking: false,
    ai: false, aiAllowed: false, aiReason: "" });
  static css = `
    .wrap { display: grid; grid-template-columns: 280px minmax(0, 1fr); gap: 16px; }
    @media (max-width: 700px) { .wrap { grid-template-columns: 1fr; } }
    .item { padding: 10px 12px; border-radius: var(--sm-rs); cursor: pointer; display: flex; gap: 10px; align-items: center; margin-bottom: 2px; }
    .item:hover, .item.on { background: color-mix(in srgb, var(--sm-accent) 12%, transparent); }
    /* v1.13.0: Gast wartet auf Antwort → roter Rand links, rote Tönung, Badge */
    .item.open { border-left: 4px solid var(--sm-bad); padding-left: 6px;
      background: color-mix(in srgb, var(--sm-bad) 10%, transparent); }
    .item.open.on, .item.open:hover { background: color-mix(in srgb, var(--sm-bad) 18%, transparent); }
    .item.open b { color: var(--sm-bad); }
    /* v1.14.0: „Keine Antwort nötig“ – klein in der Liste, normal im Verlauf (gemeinsam: REPLY_CSS) */
    .btn.mini { padding: 2px 8px; font-size: .75rem; min-height: 0; margin: 2px 0 0 6px; }
    ${REPLY_CSS}
    .opencount { padding: 2px 10px; border-radius: 999px; font-size: .85rem; font-weight: 600; background: var(--sm-bad); color: #fff; }
    .last { padding: 12px 14px; border-radius: var(--sm-rs); border-left: 4px solid var(--sm-accent); margin-bottom: 14px;
      background: var(--sm-surf2); cursor: pointer; white-space: pre-wrap; }
    ${DIALOG_CSS.replace(/\.back[^}]+}|\.dlg[^}]+}/g, "")}
  `;
  async load() {
    const apt = await this.apartment();
    const info = await this.store.getInfo();
    const list = await this.store.ws("smoobu/bookings", { ...this.target,
      start: iso(addDays(D(info.heute), -this._config.days_back)), end: iso(addDays(D(info.heute), this._config.days_ahead)) });
    const guests = list.buchungen.filter((b) => !b.blockiert && !b.storniert);
    // Laufende zuerst, dann kommende, dann vergangene
    const order = { laufend: 0, kommend: 1, vergangen: 2 };
    guests.sort((a, b) => order[a.status] - order[b.status] || (a.status === "vergangen" ? b.anreise.localeCompare(a.anreise) : a.anreise.localeCompare(b.anreise)));
    // v1.13.0: Antwortstatus je Gast (Backend cacht 10 min). Schlägt der Abruf fehl,
    // bleibt die Liste ohne Markierung nutzbar.
    let status = {};
    try {
      status = (await this.store.ws("smoobu/message_status", { ...this.target, reservation_ids: guests.slice(0, 60).map((b) => b.id) }, { cache: false })).status || {};
    } catch (e) { status = {}; }
    // Offene Gäste nach oben (stabil: innerhalb bleibt die Reihenfolge laufend/kommend/vergangen)
    guests.sort((a, b) => (status[b.id]?.offen ? 1 : 0) - (status[a.id]?.offen ? 1 : 0));
    return { apt, guests, status };
  }
  async select(id) {
    this.setState({ sel: id, thread: null, loadingThread: true, draft: "", sug: null });
    try {
      const [d, a] = await Promise.all([
        this.store.ws("smoobu/booking", { ...this.target, reservation_id: id }, { cache: false }),
        this.store.ws("smoobu/assistant/state", this.target, { cache: false }).catch(() => null),
      ]);
      const sug = a?.vorschlaege?.find((v) => v.buchung_id === id && v.status === "offen") || null;
      // Status aus dem frischen Verlauf übernehmen: offen nur, wenn die neueste sichtbare Nachricht
      // VOM Gast ist (typ 1) und nicht als „keine Antwort nötig“ markiert wurde (erledigt_id, v1.14.0)
      if (this._data?.status) this._data.status[id] = threadStatus(d, this._data.status[id]);
      if (this._state.sel === id) this.setState({ thread: d, loadingThread: false, sug, draft: sug?.antwort || "",
        ai: !!a, aiAllowed: !!a?.ki_erlaubt, aiReason: a?.ki_sperre || "" });
    } catch (e) { this.setState({ thread: { fehler: e.message || String(e), nachrichten: [] }, loadingThread: false }); }
  }
  async noReply(id, done = true) {
    try {
      const r = await this.store.ws("smoobu/message_done", { ...this.target, reservation_id: id, done }, { cache: false });
      if (this._data?.status) this._data.status[id] = r.status;
      this.store.messagesChanged(); // Zähler am Reiter „Nachrichten“ sofort mitziehen
      if (this._state.sel === id && done) this.setState({ sug: null });
      toast(t(done ? "Ohne Antwort erledigt" : "Gespeichert"));
      this.render();
    } catch (e) { toast(`${t("Fehler")}: ${e.message || e}`); }
  }
  async aiSuggest() {
    if (!this._state.aiAllowed) { toast(this._state.aiReason || t("KI in den Integrationsoptionen deaktiviert")); return; }
    const anlass = this.$('[data-k="anlass"]')?.value || "antwort";
    this.setState({ thinking: true });
    try {
      const sug = await this.store.ws("smoobu/assistant/suggest", { ...this.target, reservation_id: this._state.sel, anlass }, { cache: false });
      this.setState({ sug, draft: sug.antwort, thinking: false });
    } catch (e) { this.setState({ thinking: false }); toast(`${t("Fehler")}: ${e.message || e}`); }
  }
  body({ apt, guests, status = {} }) {
    const s = this._state;
    const entityId = this._config.message_entity || Object.keys(this._hass.states).find((e) => e.startsWith("sensor.") && e.endsWith("letzte_gastenachricht"));
    const last = entityId ? this._hass.states[entityId] : null;
    // Ohne Leerraum zwischen den Tags: .last nutzt white-space: pre-wrap
    // Nur echte Gästenachrichten zeigen (alte Stände mit absender „host“ ausblenden, v1.14.0)
    const lastHtml = last && last.attributes.text && last.attributes.absender !== "host" ? `<div class="last" data-rid="${esc(last.attributes.buchungs_id || "")}">` +
      `<div class="sub">${t("Nachrichten")} · ${esc(last.attributes.gast || "")} · ${fdate(last.attributes.empfangen, DT_FMT)}</div>` +
      `${msgHtml(String(last.attributes.text).slice(0, 2000))}</div>` : "";
    const openCount = guests.filter((b) => status[b.id]?.offen).length;
    const items = guests.map((b) => { const op = !!status[b.id]?.offen;
      return `<div class="item ${s.sel === b.id ? "on" : ""} ${op ? "open" : ""}" data-rid="${b.id}">
      <span class="dot" style="background:${colorOf(apt, b.kanal)}"></span><div class="grow"><b>${esc(b.gast)}</b>${b.hund ? " 🐕" : ""}${this.code(b)}
      <div class="sub">${fdate(b.anreise)} – ${fdate(b.abreise)} · ${t(b.status)}</div>
      ${op ? `<span class="pending">💬 ${t("Antwort offen")}</span><button class="btn flat mini" data-noreply="${b.id}" title="${t("Keine Antwort nötig")}">✓ ${t("Keine Antwort nötig")}</button>` : ""}</div></div>`; }).join("");
    const th = s.thread;
    const msgs = th ? newestFirst(th.nachrichten).map((m) => `<div class="msg ${Number(m.typ) === 2 ? "out" : ""}"><div class="h">${dirLabel(m)} ${m.zeit ? esc(fdate(m.zeit, DT_FMT)) : ""} ${m.betreff ? "· " + esc(m.betreff) : ""}</div>${msgHtml(m.text)}</div>`).join("") : "";
    const right = !s.sel ? `<div class="empty">← ${t("Gast")}</div>`
      : s.loadingThread ? `<div class="empty">${t("Laden …")}</div>`
      : `${th?.fehler ? `<div class="err">${esc(th.fehler)}</div>` : ""}
        <div class="row"><b class="grow">${esc(th?.buchung?.gast || "")}</b><button class="btn flat" data-act="detail">${t("Details")}</button></div>
        ${noReplyHtml(status[s.sel], s.sel)}
        <div class="msgs">${msgs || `<div class="muted">${t("keine")}</div>`}</div>
        ${sugHtml(s.sug)}
        ${can("antworten", this.target.apartment_id) ? `<textarea data-k="msg" placeholder="${t("Antworten")} …" style="margin-top:8px;min-height:140px">${esc(s.draft || "")}</textarea>
        <div class="row">${aiCtlHtml(s.ai, s.aiAllowed, s.aiReason, s.thinking)}
          <span class="grow"></span><button class="btn" data-act="send">✉ ${t("Senden")}</button></div>` : `<div class="sub">🔒 ${t("Antworten nur mit dem Recht „Antworten“")}</div>`}`;
    return `<div class="head"><h2>${esc(this._config.title || t("Posteingang"))}</h2>${openCount ? `<span class="opencount">💬 ${openCount} ${t("warten auf Antwort")}</span>` : ""}</div>${lastHtml}
      <div class="wrap"><div>${items || `<div class="empty">${t("Keine Daten")}</div>`}</div><div>${right}</div></div>`;
  }
  bind(root) {
    root.querySelectorAll("[data-rid]").forEach((el) => el.addEventListener("click", () => el.dataset.rid && this.select(Number(el.dataset.rid))));
    // „Keine Antwort nötig“ / Rückgängig – stopPropagation, damit der Klick nicht zusätzlich den Gast auswählt
    root.querySelectorAll("[data-noreply]").forEach((el) => el.addEventListener("click", (e) => { e.stopPropagation(); this.noReply(Number(el.dataset.noreply), true); }));
    root.querySelectorAll("[data-undo]").forEach((el) => el.addEventListener("click", (e) => { e.stopPropagation(); this.noReply(Number(el.dataset.undo), false); }));
    root.querySelector('[data-act="detail"]')?.addEventListener("click", () => this.openBooking(this._state.sel));
    root.querySelector('[data-act="ai"]')?.addEventListener("click", () => this.aiSuggest());
    root.querySelector('[data-k="msg"]')?.addEventListener("input", (e) => { this._state.draft = e.target.value; });
    root.querySelector('[data-act="send"]')?.addEventListener("click", async () => {
      const text = (this.$('[data-k="msg"]')?.value || "").trim();
      if (!text) return;
      if (/\[OFFEN/i.test(text)) { toast("Bitte zuerst die Stellen [OFFEN: …] ergänzen"); return; }
      if (!(await confirmDialog(`${t("Senden")} ${t("an den Gast")}?`))) return;
      try {
        // Über den Assistenten senden → Antwort wird als Lernbeispiel gespeichert
        await this.store.ws("smoobu/assistant/send", { ...this.target, reservation_id: this._state.sel, text }, { cache: false });
        this.store.invalidate();
        toast(t("Gesendet"));
        this.select(this._state.sel);
      } catch (e) { toast(`${t("Fehler")}: ${e.message || e}`); }
    });
  }
  onHass() {
    // Neue Gästenachricht (Sensor) → Anzeige oben aktualisieren, ohne Neuladen der Liste
    const id = this._config.message_entity || "";
    const st = id ? this._hass.states[id] : null;
    const stamp = st?.last_changed;
    if (stamp && stamp !== this._lastMsg) { this._lastMsg = stamp; if (this._data) this.render(); }
  }
}


// ===========================================================================
// KI-Assistent: Wissensdatenbank, Lernbeispiele, offene Vorschläge
// ===========================================================================
const INTENT_LABEL = { frage: "Frage", spaete_anreise: "Späte Anreise", frueher_checkin: "Früher Check-in",
  spaeter_checkout: "Später Check-out", problem_dringend: "Problem", dank: "Dank", buchungsanfrage: "Buchungsanfrage",
  stornierung: "Stornierung", sonstiges: "Sonstiges" };
class SmoobuAssistantCard extends SmoobuCard {
  static defaults = { title: "" };
  static initialState = () => ({ tab: "wissen", edit: null, filter: "", editSug: null });
  static css = `
    .tabs { display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0 12px; }
    .kn { border: 1px solid var(--sm-line); border-radius: var(--sm-rs); padding: 12px 14px; margin-bottom: 8px; }
    .kn.vorschlag { border-color: var(--sm-warn); background: color-mix(in srgb, var(--sm-warn) 8%, transparent); }
    .kn.aus { opacity: .55; }
    .kn .t { font-weight: 600; } .kn .x { white-space: pre-wrap; font-size: .88rem; margin-top: 4px; }
    .kn input[data-f="thema"] { width: 100%; box-sizing: border-box; margin-bottom: 6px; }
    .ex { border-bottom: 1px solid var(--sm-line); padding: 8px 0; font-size: .85rem; }
    .ex .g { color: var(--sm-muted); white-space: pre-wrap; } .ex .a { white-space: pre-wrap; margin-top: 4px; }
    .prog { height: 6px; border-radius: 3px; background: var(--sm-line); overflow: hidden; margin-top: 6px; }
    .prog > div { height: 100%; background: var(--sm-accent); }
    .btn[disabled].locked { opacity: .45; cursor: not-allowed; }
    .lockinfo { margin-top: 8px; padding: 10px 14px; border-radius: var(--sm-rs); font-size: .86rem;
      background: var(--sm-surf2); border-left: 4px solid var(--sm-muted); }
  `;
  async load() {
    const st = await this.store.ws("smoobu/assistant/state", this.target, { cache: false });
    // Import läuft im Hintergrund → Fortschritt alle 3 s nachladen
    clearTimeout(this._poll);
    if (st.import?.laeuft) this._poll = setTimeout(() => this._reload(), 3000);
    return { st };
  }
  disconnectedCallback() { clearTimeout(this._poll); super.disconnectedCallback(); }
  knowledge(st) {
    const f = this._state.filter.toLowerCase();
    const order = { vorschlag: 0, aktiv: 1, aus: 2 };
    const items = st.wissen.filter((w) => !f || `${w.thema} ${w.text}`.toLowerCase().includes(f))
      .sort((a, b) => order[a.status] - order[b.status] || a.thema.localeCompare(b.thema));
    const ed = this._state.edit;
    const row = (w) => ed === w.id ? `<div class="kn" data-id="${w.id}">
        <input data-f="thema" value="${esc(w.thema)}" placeholder="Thema">
        <textarea data-f="text" placeholder="Fakt / Antwortbaustein">${esc(w.text)}</textarea>
        <div class="row"><label><input type="checkbox" data-f="vertraulich" ${w.vertraulich ? "checked" : ""}> vertraulich (nicht an die KI)</label>
          <select data-f="status">${["aktiv", "vorschlag", "aus"].map((x) => `<option value="${x}" ${x === w.status ? "selected" : ""}>${t(KSTATUS_LABEL[x])}</option>`).join("")}</select>
          <span class="grow"></span><button class="btn flat" data-a="cancel">${t("Abbrechen")}</button><button class="btn" data-a="save">${t("Speichern")}</button></div></div>`
      : `<div class="kn ${w.status}" data-id="${w.id}"><div class="row"><span class="t grow">${esc(w.thema)}${w.vertraulich ? " 🔒" : ""}</span>
          ${w.status === "vorschlag" ? `<span class="badge warn">${t("Vorschlag")} · ${esc(t(SOURCE_LABEL[w.quelle] || w.quelle))}</span><button class="btn" data-a="ok">✓ Freigeben</button>` : `<span class="badge">${t(KSTATUS_LABEL[w.status] || w.status)}</span>`}
          <button class="btn flat" data-a="edit">✎</button><button class="btn flat" data-a="del">🗑</button></div>
          <div class="x">${esc(w.text) || '<span class="muted">(noch kein Text – bitte ergänzen)</span>'}</div></div>`;
    return `<div class="toolbar"><input type="search" data-k="filter" placeholder="${t("Suche")}" value="${esc(this._state.filter)}" style="flex:1">
      <button class="btn" data-a="new">+ Eintrag</button></div>${ed === "neu" ? row({ id: "neu", thema: "", text: "", status: "aktiv" }) : ""}
      ${items.map(row).join("") || `<div class="empty">${t("Keine Daten")}</div>`}`;
  }
  body({ st }) {
    const tab = this._state.tab;
    const imp = st.import || {};
    const pct = imp.buchungen ? Math.round((imp.fertig / imp.buchungen) * 100) : 0;
    const head = `<div class="head"><h2>${esc(this._config.title || "Assistent")}</h2>
        ${st.ki_erlaubt === false ? `<span class="badge bad" title="${esc(st.ki_sperre || "")}">🔒 ${t("KI gesperrt")}</span>`
          : `<span class="badge ${st.aktiv ? "good" : "bad"}" title="Automatische Antwortvorschläge">${st.aktiv ? "aktiv" : "aus"}</span>`}
        <span class="badge" title="${esc(st.ki || "")}">${esc((st.ki && this._hass?.states[st.ki]?.attributes?.friendly_name) || st.ki || t("keine KI"))}</span></div>
      ${st.ki_erlaubt === false ? `<div class="lockinfo">🔒 ${esc(st.ki_sperre || t("KI in den Integrationsoptionen deaktiviert"))}.
        Wissensdatenbank, Lernen, Import und Tagesbriefing funktionieren weiter – es gehen keine Daten an einen KI-Anbieter.</div>` : ""}
      ${st.fehler && st.ki_erlaubt !== false ? `<div class="err">Letzter Fehler: ${esc(st.fehler)}</div>` : ""}
      <div class="grid" style="margin-top:8px">
        ${tile("Offene Vorschläge", num(st.offen.length))}
        ${tile("Wissen", num(st.wissen.filter((w) => w.status === "aktiv").length), `${st.wissen.filter((w) => w.status === "vorschlag").length} zur Freigabe`)}
        ${tile("Lernbeispiele", num(st.beispiele_anzahl))}
      </div>
      <div class="tabs">${[["wissen", "📚 Wissen"], ["vorschlaege", "✨ Vorschläge"], ["beispiele", "🎓 Gelernt"], ["import", "⬇ Import"]]
        .map(([k, l]) => `<button class="chip" data-tab="${k}" aria-pressed="${tab === k}">${l}</button>`).join("")}</div>`;
    let body = "";
    if (tab === "wissen") body = this.knowledge(st);
    if (tab === "vorschlaege") body = st.vorschlaege.map((v) => `<div class="ex click" data-bid="${v.buchung_id}">
        <div class="row"><b class="grow">${esc(v.gast || v.buchung_id)}</b>${v.dringend ? '<span class="badge bad">dringend</span>' : ""}
        <span class="badge">${esc(INTENT_LABEL[v.absicht] || v.absicht)}</span><span class="badge ${v.status === "offen" ? "warn" : ""}">${esc(t(SSTATUS_LABEL[v.status] || v.status))}</span>
        <span class="sub">${fdate(v.erstellt, DT_FMT)}</span></div>
        ${v.gastnachricht ? `<div class="g">„${esc(v.gastnachricht.slice(0, 300))}“</div>` : ""}
        ${this._state.editSug === v.buchung_id
          // v1.17.0: Vorschlag direkt hier bearbeiten und senden
          ? `<textarea data-k="sugtext" rows="8" style="width:100%;box-sizing:border-box">${esc(v.antwort)}</textarea>
             <div class="row" style="margin-top:6px"><button class="btn" data-sa="send" data-rid="${v.buchung_id}">📤 ${t("Senden")}</button>
             <button class="btn flat" data-sa="cancel" data-rid="${v.buchung_id}">${t("Abbrechen")}</button></div>`
          : `<div class="a">➜ ${esc(v.antwort)}</div>`}
        <div class="row" style="margin-top:6px;gap:6px">
          ${v.status === "offen" && this._state.editSug !== v.buchung_id ? `<button class="btn" data-sa="edit" data-rid="${v.buchung_id}">✏️ ${t("Bearbeiten & senden")}</button>
            <button class="btn flat" data-sa="ignore" data-rid="${v.buchung_id}">${t("Ignorieren")}</button>` : ""}
          <span class="grow"></span><button class="btn flat" data-sa="delete" data-rid="${v.buchung_id}" title="${t("Löschen")}">🗑</button></div></div>`).join("")
      || `<div class="empty">${t("Keine Daten")}</div>`;
    if (tab === "beispiele") body = st.beispiele.slice(0, 60).map((b) => `<div class="ex"><div class="row"><span class="badge">${esc(t(SOURCE_LABEL[b.quelle] || b.quelle))}</span>
        <span class="sub grow">${esc(chn(b.kanal))} · ${esc(b.sprache || "")}</span><button class="btn flat" data-del-ex="${b.id}">🗑</button></div>
        ${b.gast ? `<div class="g">Gast: ${esc(b.gast.slice(0, 300))}</div>` : ""}<div class="a">Ihr: ${esc(b.antwort.slice(0, 500))}</div></div>`).join("")
      || `<div class="empty">Noch nichts gelernt – Verlauf importieren oder Antworten senden.</div>`;
    if (tab === "luecken") body = st.luecken.map((g) => `<div class="ex"><b>${fdow(g.von)} – ${fdow(g.bis)}</b> · ${g.naechte} N. frei,
        Mindestaufenthalt ${g.mindestaufenthalt} → nicht buchbar${g.preis_vorschlag ? ` · Last-Minute-Vorschlag ${g.preis} → ${g.preis_vorschlag} €` : ""}
        <div class="sub">Im Belegungsplan markieren und „Preis setzen“ (Mindestaufenthalt ${g.naechte}).</div></div>`).join("")
      || `<div class="empty">Keine nicht buchbaren Lücken in den nächsten 30 Tagen.</div>`;
    if (tab === "import") body = `<p class="sub">1. Verlauf importieren: lädt die Nachrichten eurer Gästebuchungen (2 Jahre) und speichert jede eurer Antworten
        mit der Gästenachricht davor als Lernbeispiel. 2. Wissen erzeugen: die KI liest eure Vorlagen und Antworten und schlägt
        Wissenseinträge vor (Status „Vorschlag“, ihr gebt sie frei). Zugangscodes werden dabei nicht übernommen.</p>
      <div class="row"><button class="btn" data-a="import" ${imp.laeuft ? "disabled" : ""}>⬇ Verlauf importieren</button>
        ${st.ki_erlaubt === false
          ? `<button class="btn locked" disabled title="${esc(st.ki_sperre || t("KI in den Integrationsoptionen deaktiviert"))}">🔒 📚 Wissen erzeugen</button>`
          : `<button class="btn" data-a="wissen" ${this._state.busy ? "disabled" : ""}>${this._state.busy ? "⏳ KI arbeitet …" : "📚 Wissen erzeugen"}</button>`}</div>
      ${imp.buchungen ? `<div class="sub" style="margin-top:8px">${imp.laeuft ? "Läuft" : "Fertig"}: ${imp.fertig}/${imp.buchungen} Buchungen ·
        ${imp.beispiele} neue Beispiele${imp.fehler ? ` · ${imp.fehler} Fehler` : ""}${st.vorlagen?.length ? ` · ${st.vorlagen.length} Vorlagen erkannt` : ""}</div>
        <div class="prog"><div style="width:${pct}%"></div></div>` : ""}`;
    return head + body;
  }
  bind(root) {
    root.querySelectorAll("[data-tab]").forEach((el) => el.addEventListener("click", () => this.setState({ tab: el.dataset.tab, edit: null })));
    const f = root.querySelector('[data-k="filter"]');
    f?.addEventListener("input", () => { const p = f.selectionStart; this.setState({ filter: f.value }); const n = this.$('[data-k="filter"]'); n.focus(); n.setSelectionRange(p, p); });
    root.querySelectorAll("[data-bid]").forEach((el) => el.addEventListener("click", (e) => {
      // Klicks auf Buttons/Textfeld im Vorschlag öffnen nicht die Buchung
      if (e.target.closest("button, textarea")) return;
      this.openBooking(Number(el.dataset.bid));
    }));
    // v1.17.0: Vorschläge bearbeiten & senden, ignorieren, löschen
    root.querySelectorAll("[data-sa]").forEach((el) => el.addEventListener("click", async (e) => {
      e.stopPropagation();
      const rid = Number(el.dataset.rid), act = el.dataset.sa;
      try {
        if (act === "edit") return this.setState({ editSug: rid });
        if (act === "cancel") return this.setState({ editSug: null });
        if (act === "send") {
          const text = (this.$('[data-k="sugtext"]')?.value || "").trim();
          if (!text) return;
          if (/\[OFFEN/i.test(text)) { toast("Bitte zuerst die Stellen [OFFEN: …] ergänzen"); return; }
          if (!(await confirmDialog(`${t("Senden")} ${t("an den Gast")}?`))) return;
          await this.store.ws("smoobu/assistant/send", { ...this.target, reservation_id: rid, text }, { cache: false });
          toast(t("Gesendet"));
        } else if (act === "ignore") {
          await this.store.ws("smoobu/assistant/delete", { ...this.target, kind: "ignorieren", item_id: String(rid) }, { cache: false });
        } else if (act === "delete") {
          if (!(await confirmDialog(`${t("Vorschlag löschen")}?`))) return;
          await this.store.ws("smoobu/assistant/delete", { ...this.target, kind: "vorschlag", item_id: String(rid) }, { cache: false });
        }
        this._state.editSug = null;
        this.store.messagesChanged();
        this._reload();
      } catch (err) { toast(`${t("Fehler")}: ${err.message || err}`); }
    }));
    root.querySelectorAll("[data-del-ex]").forEach((el) => el.addEventListener("click", async () => {
      await this.store.ws("smoobu/assistant/delete", { ...this.target, kind: "beispiel", item_id: el.dataset.delEx }, { cache: false });
      this._reload();
    }));
    root.querySelectorAll("[data-a]").forEach((el) => el.addEventListener("click", () => this.act(el.dataset.a, el.closest("[data-id]"))));
  }
  async act(a, box) {
    const id = box?.dataset.id;
    const save = (item) => this.store.ws("smoobu/assistant/knowledge", { ...this.target, item }, { cache: false });
    try {
      if (a === "new") return this.setState({ edit: "neu" });
      if (a === "edit") return this.setState({ edit: id });
      if (a === "cancel") return this.setState({ edit: null });
      if (a === "save") {
        const v = (k) => box.querySelector(`[data-f="${k}"]`);
        const item = { thema: v("thema").value.trim(), text: v("text").value.trim(), status: v("status").value, vertraulich: v("vertraulich").checked };
        if (!item.thema) return toast("Thema fehlt");
        await save(id === "neu" ? item : { ...item, id });
        this._state.edit = null;
      } else if (a === "ok") await save({ id, status: "aktiv" });
      else if (a === "del") {
        if (!(await confirmDialog("Eintrag löschen?"))) return;
        await this.store.ws("smoobu/assistant/delete", { ...this.target, kind: "wissen", item_id: id }, { cache: false });
      } else if (a === "import") {
        await this.store.ws("smoobu/assistant/job", { ...this.target, job: "import" }, { cache: false });
        toast("Import gestartet");
      } else if (a === "wissen") {
        this.setState({ busy: true });
        const r = await this.store.ws("smoobu/assistant/job", { ...this.target, job: "wissen" }, { cache: false });
        this._state.busy = false;
        toast(`${r.neu} Wissensvorschläge erzeugt`);
        this._state.tab = "wissen";
      }
      this._reload();
    } catch (e) { this._state.busy = false; toast(`${t("Fehler")}: ${e.message || e}`); this.render(); }
  }
}

// ===========================================================================
// Statistik-Werkbank (Teilschritt 2): custom:smoobu-stats-card
// ===========================================================================
// Eine Karte für die Seite „smoobu-statistik“. Daten aus smoobu/stats (Baukasten-
// Abfrage + Pace-Modell, stats.py) und für freie Nächte aus smoobu/analytics.
// Aufbau: Aussage-Satz → Filterleiste (sticky) → Modul 1 Kennzahlenleiste (+ Fokus-
// Verlauf) → Modul 2 Buchungstempo/Prognose → Modul 3 Saison-Matrix.
// Weitere Module (4–11, Baukasten) folgen in den Teilschritten 3 und 4.
//
// Statistik-Regeln (Konzept 16.11.2026): Median für Vorlauf, n bei jeder Zahl,
// n < 5 blass („wenig Daten“), Prognose als Spanne, eine y-Achse je Diagramm,
// immer Legende oder Direktbeschriftung.
//
// Entscheidungen:
// - Eigene SVG-Grafiken statt ApexCharts (wie alle Smoobu-Karten: kein Build, keine
//   Abhängigkeit, Farben aus dem Design A).
// - Werkbank/Einfach je Gerät (localStorage), Standard nach Fensterbreite: < 700 px Einfach.
// - Vergleich „Stichtag Vorjahr“ rechnet mit dem Buchungsstand vor genau einem Jahr
//   (smoobu/stats `as_of`), sonst wäre ein laufender Zeitraum gegen ein fertiges Vorjahr
//   immer schlechter.
// - Die Pace-Kurve arbeitet mit Umsatz brutto (Pace-Modell im Backend). Die Fokus-Kennzahl
//   aus der Kennzahlenleiste steuert den großen Verlauf direkt unter der Leiste und – wo
//   möglich – die Saison-Matrix.
const STATS_MODE_KEY = "smoobu-statistik-modus";
// Kennzahlenleiste: id = Kennzahl aus stats.MEASURES; pp = Veränderung in Prozentpunkten;
// invert = höher ist schlecht
const STATS_KPIS = [
  { id: "umsatz", label: "Umsatz", hint: "Umsatz brutto, anteilig nach Nächten" },
  { id: "auslastung", label: "Auslastung", pp: true, hint: "Belegte Nächte ÷ verfügbare Nächte (gesperrte Nächte zählen nicht als verfügbar)" },
  { id: "adr", label: "ADR", hint: "Ø Preis je belegter Nacht (brutto)" },
  { id: "revpar", label: "RevPAR", hint: "Umsatz je verfügbarer Nacht = ADR × Auslastung" },
  { id: "netto_revpar", label: "Netto-RevPAR", hint: "Netto (nach Provision und Gebühren) je verfügbarer Nacht" },
  { id: "vorlauf", label: "Vorlauf", hint: "Median der Tage zwischen Buchung und Anreise (Anreisen im Zeitraum)" },
  { id: "stornoquote", label: "Stornoquote", pp: true, invert: true, hint: "Stornos ÷ alle Buchungen mit Anreise im Zeitraum" },
];
const STATS_EINFACH = ["umsatz", "auslastung", "adr", "stornoquote"];
const MATRIX_MEASURES = [["auslastung", "Auslastung"], ["umsatz", "Umsatz"], ["adr", "ADR"], ["revpar", "RevPAR"], ["netto", "Netto"]];
const PERIOD_TYPES = [["monat", "Monat"], ["quartal", "Quartal"], ["saison", "Saison"], ["jahr", "Jahr"], ["frei", "Frei"]];
const PERIOD_MONTHS = { monat: 1, quartal: 3, saison: 3, jahr: 12 };
const STATS_COMPARE = [["stichtag", "Stichtag Vorjahr"], ["vorjahr", "Ganzes Vorjahr"], ["vorperiode", "Vorperiode"]];
const RASTER = [["auto", "Auto"], ["woche", "Woche"], ["monat", "Monat"]];
// Schlüssel = Startmonat 0-basiert wie Date.getMonth() (11 = Dez, 2 = März, 5 = Juni, 8 = Sep)
const SEASON_NAME = { 11: "Winter", 2: "Frühling", 5: "Sommer", 8: "Herbst" };
const MONTHS_SHORT = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];

// Beginn des Zeitraums, der `d` enthält (Saison wie stats.SEASONS: Winter = Dez–Feb)
function statsStart(type, d) {
  const y = d.getFullYear(), m = d.getMonth();
  if (type === "monat") return new Date(y, m, 1);
  if (type === "quartal") return new Date(y, m - (m % 3), 1);
  if (type === "saison") return m === 11 ? new Date(y, 11, 1) : m < 2 ? new Date(y - 1, 11, 1) : new Date(y, m - ((m - 2) % 3), 1);
  return new Date(y, 0, 1);
}
// Zeitraum [start, ende) aus dem Kartenzustand
function statsRange(s, todayIso) {
  if (s.ptype === "frei") {
    const a = s.from ? D(s.from) : new Date(D(todayIso).getFullYear(), 0, 1);
    const b = s.to ? addDays(D(s.to), 1) : addDays(D(todayIso), 1);
    return b > a ? [a, b] : [a, addDays(a, 1)];
  }
  const a = statsStart(s.ptype, D(s.anchor || todayIso));
  return [a, addMonths(a, PERIOD_MONTHS[s.ptype])];
}
// Vergleichszeitraum + Stichtag (nur „Stichtag Vorjahr“)
function statsCompare(s, [a, b], todayIso) {
  const yearBack = (d) => new Date(d.getFullYear() - 1, d.getMonth(), d.getDate());
  if (s.compare === "vorperiode") {
    if (s.ptype === "frei") { const n = Math.round((b - a) / 86400000); return { range: [addDays(a, -n), a], asOf: null }; }
    return { range: [addMonths(a, -PERIOD_MONTHS[s.ptype]), a], asOf: null };
  }
  return { range: [yearBack(a), yearBack(b)], asOf: s.compare === "stichtag" ? iso(yearBack(D(todayIso))) : null };
}
// Kurzname: „November 2026“, „Q4 2026“, „Winter 2025/26“, „2026“, „01.03.26 – 31.03.26“
function statsLabel(type, [a, b]) {
  const y = a.getFullYear();
  if (type === "monat") return a.toLocaleDateString(locale(), { month: "long", year: "numeric" });
  if (type === "quartal") return `Q${Math.floor(a.getMonth() / 3) + 1} ${y}`;
  if (type === "saison") return a.getMonth() === 11 ? `${t("Winter")} ${y}/${String(y + 1).slice(-2)}` : `${t(SEASON_NAME[a.getMonth()])} ${y}`;
  if (type === "jahr") return String(y);
  return `${fdate(iso(a))} – ${fdate(iso(addDays(b, -1)))}`;
}
// Wert einer Zelle aus einer stats-Abfrage (eine Zeile „Gesamt“)
const statCell = (res, row = 0) => res?.zeilen?.[row]?.werte?.Gesamt || { wert: null, n: 0 };
const statSeries = (res) => (res?.zeilen || []).map((z) => ({ fach: z.fach, ...(z.werte?.Gesamt || { wert: null, n: 0 }) }));
// Fach-Beschriftung einer Zeit-Dimension: „2026-03“ → „Mär 26“, „2026-W45“ → „KW 45“
function binLabel(fach, long = false) {
  if (/^\d{4}-W\d{2}$/.test(fach)) return `${t("KW")} ${Number(fach.slice(6))}${long ? ` ${fach.slice(0, 4)}` : ""}`;
  if (/^\d{4}-\d{2}$/.test(fach)) return long ? D(`${fach}-01`).toLocaleDateString(locale(), { month: "long", year: "numeric" })
    : `${t(MONTHS_SHORT[Number(fach.slice(5)) - 1])} ${fach.slice(2, 4)}`;
  return fach;
}

// ---- Teilschritte 3/4: Module 4–11, Baukasten, Anordnung je Gerät -------------------------
// Anordnung (Reihenfolge, ausgeblendete Module, eigene Baukasten-Module) je Gerät in localStorage –
// Entscheidung Betreiber: „speichern je Gerät“ (kein Server-Speicher, kein Abgleich zwischen Geräten).
const STATS_LAYOUT_KEY = "smoobu-statistik-layout";
const STATS_BUILTIN = ["kennzahlen", "empfehlung", "tempo", "saison", "belegung", "kanaele", "fenster", "buchungszeit", "luecken", "stornos", "gaeste", "ehrentafel", "service", "tabelle"];
const STATS_TITLES = {
  kennzahlen: "Kennzahlen", empfehlung: "Bewertung & Empfehlung", tempo: "Buchungstempo & Prognose", saison: "Saison-Matrix", belegung: "Belegung nach Wochentag",
  kanaele: "Kanal-Wirtschaftlichkeit", fenster: "Buchungsfenster & Aufenthalt", buchungszeit: "Buchungszeitpunkt", luecken: "Verlorene Nächte", stornos: "Stornos",
  gaeste: "Gäste", ehrentafel: "Ehrentafel", service: "Service", tabelle: "Datentabelle",
};
// Dimensionen des Baukastens (stats.DIMENSIONS) mit Anzeigenamen
const DIM_LABEL = {
  gesamt: "Gesamt", jahr: "Jahr", monat: "Monat", monat_im_jahr: "Monat im Jahr", woche: "Kalenderwoche", wochentag: "Wochentag",
  saison: "Saison", kanal: "Kanal", gruppe: "Direkt/Portal", wohnung: "Wohnung", aufenthalt: "Aufenthalt (Nächte)",
  vorlauf: "Vorlauf (Tage)", personen: "Personen", hund: "Hund", sprache: "Sprache", stammgast: "Stammgast", buchungsmonat: "Buchungsmonat",
  vorlauf_monate: "Vorlauf (Monate)", buchungsmonat_im_jahr: "Buchungsmonat im Jahr",
};
// Summierbare Kennzahlen (Legende zeigt die Summe; bei Quoten/Medianen/Durchschnitten wäre sie sinnlos)
const ADDITIVE = new Set(["umsatz", "netto", "kosten", "naechte", "buchungen", "stornos"]);
const VIEWS = [["balken", "Balken"], ["linie", "Linie"], ["heatmap", "Heatmap"], ["tabelle", "Tabelle"], ["kennzahl", "Kennzahl"]];
// Farben für Aufteilungen ohne feste Kanalfarbe: Akzent + Ersatzpalette (fest je Name)
const seriesColor = (name, dim, i) => (dim === "kanal" ? chColor(name) : i === 0 && dim !== "gruppe"
  ? PAL[DARK ? "dark" : "light"].acc : name === "Direkt" ? chColor("direkt") : name === "Portal" ? chColor("booking.com")
    : CH_FALLBACK[i % CH_FALLBACK.length][DARK ? 1 : 0]);

function statsLayout() {
  let l = {};
  try { l = JSON.parse(lsGet(STATS_LAYOUT_KEY, "{}")) || {}; } catch (e) { l = {}; }
  const custom = Array.isArray(l.custom) ? l.custom.filter((c) => c && c.id && c.measure && c.dimension) : [];
  const known = [...STATS_BUILTIN, ...custom.map((c) => c.id)];
  const order = (Array.isArray(l.order) ? l.order : []).filter((id) => known.includes(id));
  // v1.18.0: „Bewertung & Empfehlung“ direkt nach den Kennzahlen einfügen (statt hinten), auch in gespeicherten Layouts
  if (order.length && !order.includes("empfehlung")) order.splice(order.indexOf("kennzahlen") + 1, 0, "empfehlung");
  // v1.18.0b7: „Ehrentafel“ direkt nach „Gäste“ einfügen, auch in gespeicherten Layouts
  if (order.length && !order.includes("ehrentafel") && order.includes("gaeste")) order.splice(order.indexOf("gaeste") + 1, 0, "ehrentafel");
  for (const id of known) if (!order.includes(id)) order.push(id); // neue Module hinten anhängen
  const hidden = (Array.isArray(l.hidden) ? l.hidden : []).filter((id) => known.includes(id));
  // v1.17.1: Datentabelle doppelt die Seite „Buchungen“ (inkl. CSV) → einmalig ausblenden; über ↺ wieder einblendbar
  if ((l.defaults || 0) < 2) {
    if (!hidden.includes("tabelle")) hidden.push("tabelle");
    try { lsSet(STATS_LAYOUT_KEY, JSON.stringify({ ...l, order, hidden, custom, defaults: 2 })); } catch (e) { /* egal */ }
  }
  // defaults mitgeben, sonst blendet ein späteres saveLayout() die bewusst eingeblendete Tabelle wieder aus
  return { order, hidden, custom, defaults: 2 };
}
const saveLayout = (l) => lsSet(STATS_LAYOUT_KEY, JSON.stringify(l));

// Wert je Einheit eines stats-Ergebnisses formatieren (Baukasten)
function fmtUnit(unit, v, cur, long = false) {
  if (v === null || v === undefined) return "–";
  if (unit === "€") return money(v, cur, long && Math.abs(v) < 1000 ? 2 : 0);
  if (unit === "%") return pct(v, long ? 1 : 0);
  if (unit === "T") return `${num(v)} ${t("Tage")}`;
  if (unit === "N") return `${num(v, v % 1 ? 1 : 0)} ${t("N.")}`;
  return num(v, v % 1 ? 1 : 0);
}

// Waagerechte Balkenliste (HTML): Beschriftung, Balken, Wert, n; n < 5 blass
function hbars(items, { fmt, max = null, note = "" } = {}) {
  const top = max ?? Math.max(1e-9, ...items.map((i) => Math.abs(i.value || 0)));
  return `<div class="hb">${items.map((i) => {
    const w = Math.max(0, Math.min(100, ((i.value || 0) / top) * 100));
    const low = i.n !== undefined && i.n < 5;
    return `<div class="hr${low ? " low" : ""}" data-tip="${esc(i.tip || `${i.label}: ${fmt(i.value)}${i.n !== undefined ? ` · n = ${i.n}` : ""}${low ? ` (${t("wenig Daten")})` : ""}`)}">
      <span class="hl">${i.dot ? `<span class="dot" style="background:${i.dot}"></span>` : ""}${esc(i.label)}</span>
      <span class="ht"><i style="width:${w.toFixed(1)}%;background:${i.color || "var(--sm-accent)"}${i.hatch ? `;background-image:repeating-linear-gradient(135deg, transparent 0 3px, var(--sm-surf) 3px 5px)` : ""}"></i></span>
      <span class="hv">${fmt(i.value)}${i.n !== undefined ? `<em>n = ${i.n}</em>` : ""}</span></div>`;
  }).join("")}${note ? `<div class="sub" style="margin-top:6px">${note}</div>` : ""}</div>`;
}

// Senkrechtes Histogramm (SVG) mit Anzahl über dem Balken, eine y-Achse
function vbars(items, { W = 420, H = 190, fmt = (v) => num(v), color = "var(--sm-accent)", unit = "" } = {}) {
  const L = 34, R = 6, T = 18, B = 26;
  const max = niceMax(Math.max(1, ...items.map((i) => i.value || 0)) * 1.1);
  const n = Math.max(items.length, 1);
  const bw = (W - L - R) / n;
  const y = (v) => T + (H - T - B) * (1 - (v || 0) / max);
  let svg = "";
  for (let g = 0; g <= 2; g++) {
    const v = (max / 2) * g;
    svg += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" stroke-opacity=".1"/>
      <text x="${L - 5}" y="${y(v) + 4}" text-anchor="end" font-size="10.5" fill="currentColor" fill-opacity=".55">${fmt(v)}</text>`;
  }
  items.forEach((it, i) => {
    const x = L + i * bw;
    const h = Math.max(y(0) - y(it.value), 0);
    svg += `<rect x="${x + bw * 0.14}" y="${y(it.value)}" width="${bw * 0.72}" height="${h}" rx="3" fill="${it.color || color}" fill-opacity="${it.faint ? 0.4 : 0.9}"/>
      <text x="${x + bw / 2}" y="${y(it.value) - 5}" text-anchor="middle" font-size="10.5" font-weight="600" fill="currentColor">${it.value ? fmt(it.value) : ""}</text>
      <text x="${x + bw / 2}" y="${H - 8}" text-anchor="middle" font-size="10.5" fill="currentColor" fill-opacity=".7">${esc(it.label)}</text>
      <rect data-tip="${esc(it.tip || `${it.label}${unit}: ${fmt(it.value)}`)}" x="${x}" y="${T}" width="${bw}" height="${H - T - B}" fill="transparent"/>`;
  });
  return `<svg class="ch" viewBox="0 0 ${W} ${H}" role="img">${svg}</svg>`;
}

// Mehrreihen-Diagramm für den Baukasten: Balken (gestapelt bei Aufteilung) oder Linien, eine y-Achse
function seriesChart({ labels, series, kind, fmt, W = 800, H = 240 }) {
  const L = 60, R = 10, T = 12, B = 28;
  const n = Math.max(labels.length, 1);
  const stacked = kind === "balken";
  const sums = labels.map((_, i) => series.reduce((a, s) => a + Math.max(s.values[i] || 0, 0), 0));
  const max = niceMax(Math.max(1e-9, ...(stacked ? sums : series.flatMap((s) => s.values.map((v) => v || 0)))) * 1.08);
  const y = (v) => T + (H - T - B) * (1 - (v || 0) / max);
  const bw = (W - L - R) / n;
  let svg = "";
  for (let g = 0; g <= 4; g++) {
    const v = (max / 4) * g;
    svg += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" stroke-opacity=".1"/>
      <text x="${L - 6}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="currentColor" fill-opacity=".6">${fmt(v)}</text>`;
  }
  const step = Math.ceil(n / Math.max(4, Math.floor(W / 60)));
  const binN = labels.map((_, i) => series.reduce((a, s) => a + (s.n?.[i] ?? 9), 0));
  labels.forEach((lab, i) => {
    const x = L + i * bw;
    if (stacked) {
      let acc = 0;
      for (const s of series) {
        const v = Math.max(s.values[i] || 0, 0);
        if (!v) continue;
        // blass nur, wenn das ganze Fach weniger als 5 Buchungen hat (sonst wären bei Aufteilung fast alle Teile blass)
        svg += `<rect x="${x + bw * 0.16}" y="${y(acc + v)}" width="${bw * 0.68}" height="${Math.max(y(acc) - y(acc + v), 0)}" rx="2"
          fill="${s.color}" fill-opacity="${binN[i] < 5 ? 0.4 : 0.92}"/>`;
        acc += v;
      }
    }
    if (i % step === 0) svg += `<text x="${x + bw / 2}" y="${H - 8}" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity=".7">${esc(lab)}</text>`;
    const tip = `${lab}\n${series.map((s) => `${s.name}: ${fmt(s.values[i])}${s.n ? ` · n = ${s.n[i] ?? 0}` : ""}`).join("\n")}`;
    svg += `<rect data-tip="${esc(tip)}" x="${x}" y="${T}" width="${bw}" height="${H - T - B}" fill="transparent"/>`;
  });
  if (!stacked) {
    for (const s of series) {
      const pts = s.values.map((v, i) => (v === null || v === undefined ? null : `${L + i * bw + bw / 2},${y(v)}`)).filter(Boolean);
      svg += `<polyline points="${pts.join(" ")}" fill="none" stroke="${s.color}" stroke-width="2.2" stroke-linejoin="round" pointer-events="none"/>`;
      s.values.forEach((v, i) => { if (v !== null && v !== undefined) svg += `<circle cx="${L + i * bw + bw / 2}" cy="${y(v)}" r="2.6" fill="${s.color}" pointer-events="none"/>`; });
    }
  }
  svg += `<line x1="${L}" x2="${W - R}" y1="${y(0)}" y2="${y(0)}" stroke="currentColor" stroke-opacity=".3"/>`;
  return `<svg class="ch" viewBox="0 0 ${W} ${H}" role="img">${svg}</svg>`;
}
const legendOf = (series, fmtTotal) => `<div class="legend">${series.map((s) =>
  `<span><i style="background:${s.color}"></i><b>${esc(s.name)}</b>${fmtTotal ? ` ${fmtTotal(s)}` : ""}</span>`).join("")}</div>`;
const tilesRow = (items) => `<div class="mt">${items.map(([l, v, s, tip, low]) =>
  `<div class="mtile${low ? " low" : ""}"${tip ? ` data-tip="${esc(tip)}"` : ""}><div class="kl">${l}</div><div class="kv">${v}</div>${s ? `<div class="ks">${s}</div>` : ""}</div>`).join("")}</div>`;
const panel = (title, sub, inner, extra = "") => `<div class="panel"><div class="ph"><h2>${title}</h2>${sub ? `<span class="sub">${sub}</span>` : ""}${extra}</div>${inner}</div>`;

// Buchungszeitpunkt, Ansicht „Gebucht im → für“: Zeile = Monat, in dem gebucht wurde; Spalte = Monat des Aufenthalts.
// Zelle = Anteil an allem, was in diesem Monat gebucht wurde (Zeile = 100 %); Tooltip zusätzlich mit dem Anteil am
// Aufenthaltsmonat (Spalte). Diagonale (gleicher Monat) umrandet; Hinweise listen auffällige Vorausbuchungen
// (mindestens 2 Monate voraus, ≥ 12 % der Zeile), z. B. „Im Oktober wird schon für August gebucht“.
function bookingCalendar(card, d, m, controls) {
  const cur = d.apt.currency;
  const unitWord = { naechte: "Nächte", buchungen: "Buchungen", umsatz: "Umsatz" }[m.measure];
  const fmtV = (v) => (m.measure === "umsatz" ? money(v, cur) : num(v));
  const months = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, "0"));
  const MON_LONG = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];
  const byRow = new Map((m.cal.zeilen || []).map((z) => [z.fach, z.werte]));
  const val = (r, c) => byRow.get(r)?.[c]?.wert || 0;
  const nOf = (r, c) => byRow.get(r)?.[c]?.n || 0;
  const rowSum = Object.fromEntries(months.map((r) => [r, months.reduce((a, c) => a + val(r, c), 0)]));
  const colSum = Object.fromEntries(months.map((c) => [c, months.reduce((a, r) => a + val(r, c), 0)]));
  const all = months.reduce((a, r) => a + rowSum[r], 0);
  const ahead = (r, c) => (Number(c) - Number(r) + 12) % 12; // Monate voraus (über den Jahreswechsel)
  let html = `<div class="h" style="text-align:left">${t("gebucht im")} ↓ / ${t("für")} →</div>${months.map((c, i) => `<div class="h">${t(MONTHS_SHORT[i])}</div>`).join("")}
    <div class="h">Σ ${esc(t(unitWord))}</div><div class="h">${t("vor allem für")}</div>`;
  const hints = [];
  months.forEach((r, ri) => {
    html += `<div class="rl">${t(MONTHS_SHORT[ri])}</div>`;
    months.forEach((c, ci) => {
      const v = val(r, c);
      const share = rowSum[r] ? (v / rowSum[r]) * 100 : null;
      const colShare = colSum[c] ? (v / colSum[c]) * 100 : null;
      const diag = r === c ? " sel" : "";
      if (!v) { html += `<div class="c none${diag}">–</div>`; return; }
      const a = 0.06 + 0.84 * Math.min(1, share / 50);
      const dist = ahead(r, c);
      if (dist >= 2 && share >= 12 && nOf(r, c) >= 2) hints.push({ r: ri, c: ci, share, dist, colShare });
      html += `<div class="c${nOf(r, c) < 5 ? " low" : ""}${diag}" style="background:color-mix(in srgb, var(--sm-accent) ${Math.round(a * 100)}%, var(--sm-surf));${a > 0.55 ? "color:var(--sm-acc-ink);" : ""}"
        data-tip="${esc(`${t("Gebucht im")} ${t(MON_LONG[ri])} ${t("für")} ${t(MON_LONG[ci])}${dist ? ` (${dist} ${dist === 1 ? t("Monat") : t("Monate")} ${t("voraus")})` : ` (${t("gleicher Monat")})`}\n${fmtV(v)} ${t(unitWord)} · n = ${nOf(r, c)}\n= ${pct(share, 0)} ${t("von allem, was im")} ${t(MON_LONG[ri])} ${t("gebucht wird")}\n= ${pct(colShare, 0)} ${t("aller")} ${t(unitWord)} ${t("im")} ${t(MON_LONG[ci])}`)}">${pct(share, 0)}</div>`;
    });
    const top = months.map((c, ci) => [ci, val(r, c)]).filter(([, v]) => v).sort((x, y) => y[1] - x[1]).slice(0, 3)
      .map(([ci, v]) => `${t(MONTHS_SHORT[ci])} ${pct((v / rowSum[r]) * 100, 0)}`).join(", ");
    html += `<div class="c avg">${fmtV(rowSum[r])}</div><div class="c avg" style="font-weight:500;white-space:normal">${top || "–"}</div>`;
  });
  html += `<div class="gap"></div><div class="rl" style="color:var(--sm-ink)">Σ</div>${months.map((c) => `<div class="c avg tot">${fmtV(colSum[c])}</div>`).join("")}
    <div class="c avg tot">${fmtV(all)}</div><div></div>`;
  hints.sort((x, y) => y.share - x.share);
  const lede = hints.length
    ? `<ul class="ins">${hints.slice(0, 4).map((h) => `<li>${t("Im")} <b>${t(MON_LONG[h.r])}</b> ${t("wird schon für")} <b>${t(MON_LONG[h.c])}</b> ${t("gebucht")}: ${pct(h.share, 0)} ${t("der dort gebuchten")} ${t(unitWord)} (${h.dist} ${t("Monate voraus")}, ${pct(h.colShare, 0)} ${t("aller")} ${t(MON_LONG[h.c])}-${t(unitWord)})</li>`).join("")}</ul>`
    : `<p class="sub" style="margin:0 0 8px">${t("Keine auffälligen Vorausbuchungen (≥ 2 Monate voraus, mindestens 12 % eines Buchungsmonats).")}</p>`;
  const grid = `grid-template-columns: 96px repeat(12, minmax(46px, 1fr)) minmax(70px, 1fr) minmax(150px, 1.6fr)`;
  return panel(t("Buchungszeitpunkt"), `${t("In welchem Monat wird für welchen Monat gebucht?")} · ${t("Aufenthalte")} ${fdate(iso(m.range[0]))} – ${fdate(iso(addDays(m.range[1], -1)))}`,
    `${lede}<div class="scroll"><div class="mx" style="${grid};min-width:900px">${html}</div></div>
      <div class="legend"><span>${t("Zeile = Buchungsmonat (100 %)")}</span><span>${t("Spalte = Aufenthaltsmonat")}</span>
      <span><i style="box-shadow:inset 0 0 0 1.5px var(--sm-ink);background:none"></i>${t("gleicher Monat")}</span>
      <span>${t("Tooltip: Anteil am Aufenthaltsmonat")}</span>
      <span><i style="background:var(--sm-warn);width:6px;height:6px;border-radius:50%"></i><em>${t("kursiv")}</em> = ${t("weniger als 5 Buchungen")}</span></div>`,
    controls);
}

// Module 4–11: load(ctx) holt die Daten (parallel), render(card, d, data) baut das HTML
const RATING = { schwach: ["bad", "Schwach"], normal: ["", "Normal"], stark: ["good", "Stark"], unbekannt: ["", "Zu wenig Daten"] };
const ACTION = { senken: ["warn", "↓ Preis senken"], erhoehen: ["good", "↑ Preis erhöhen"], "erhöhen": ["good", "↑ Preis erhöhen"], halten: ["", "→ Preis halten"] };
const STATS_MODULES = {
  // v1.18.0: Bewertung & Empfehlung – Pace je Monat, Preisuntergrenzen, Hinweise (Backend: empfehlung.py)
  empfehlung: {
    load: (c) => c.card.store.ws("smoobu/stats", { ...c.target, mode: "empfehlung" }),
    render: (card, d, m) => {
      const cur = d.apt.currency;
      card._applies = []; // Dialog-Vorgaben der Übernehmen-Buttons (Index = data-apply)
      const blocks = (m.wohnungen || []).map((w) => {
        const bp = w.basispreis || {};
        // Übernehmen-Button: Vorgabe + Kontext (Kanäle, Untergrenzen) für priceDialog
        const floors2 = (mo) => Object.fromEntries(Object.entries(mo?.untergrenze || {}).map(([k, f]) => [k, f["2"]]));
        const applyBtn = (label, cfg, primary = true) => {
          if (!w.darf_aendern) return "";
          card._applies.push({ apt: w.apartment_id, cur, kanaele: w.kanaele, basis: bp.heute, ...cfg });
          return `<button class="btn ${primary ? "" : "flat"} sm" data-apply="${card._applies.length - 1}">${esc(t(label))}</button>`;
        };
        const monthEnd = (key) => iso(addDays(new Date(Number(key.slice(0, 4)), Number(key.slice(5, 7)), 1), -1));
        const head = `<div class="emp-head"><div><div class="kl">${t("Basispreis heute")}</div><div class="kv">${money(bp.heute, cur)}</div>
            <div class="ks">${bp.einheitlich ? t("gleich an allen") + ` ${num(bp.tage)} ` + t("Tagen") : `${money(bp.min, cur)} – ${money(bp.max, cur)}`}</div></div>
          ${(w.kanaele || []).map((k) => `<div data-tip="${esc(`${k.kanal}: ${t("Aufschlag")} ${num(k.aufschlag)} %${k.genius ? ` · Genius` : ""} · ${t("Kostenquote")} ${pct(k.kostenquote, 1)} (${t(k.kostenquote_quelle)})
${t("Netto je € Basispreis")}: ${num(k.netto_je_euro, 2)}`)}">
            <div class="kl"><span class="dot" style="background:${chColor(k.kanal)}"></span> ${esc(chn(k.kanal))}</div><div class="kv sm">${money(k.netto_je_nacht, cur)}</div>
            <div class="ks">${t("netto je Nacht")}${k.aufschlag ? ` · +${num(k.aufschlag)} %` : ""}${k.genius ? " · Genius" : ""}</div></div>`).join("")}</div>`;
        const months = (w.monate || []).map((mo) => {
          const [rc, rl] = RATING[mo.bewertung] || ["", mo.bewertung];
          const e = mo.empfehlung || {};
          const [ac, al] = ACTION[e.aktion] || ["", e.aktion];
          const v = mo.vergleich || {};
          // Spanne P25–P75 der Vorjahre als Band, Punkt = Stand heute, Strich = Median
          const band = v.n ? `<div class="band" data-tip="${esc(`${t("Vorjahre am gleichen Tag")}: ${(v.jahre || []).map((j) => `${j.jahr} ${pct(j.stand, 0)} → ${pct(j.ende, 0)}`).join(" · ")}`)}">
              <span class="b" style="left:${v.p25}%;width:${Math.max(v.p75 - v.p25, 1)}%"></span><span class="md" style="left:${v.median}%"></span>
              <span class="pt ${rc}" style="left:${Math.min(mo.auslastung_stand, 100)}%"></span></div>
            <div class="ks">${t("Stand")} ${pct(mo.auslastung_stand, 0)} · ${t("Vorjahre")} P25–P75 ${pct(v.p25, 0)}–${pct(v.p75, 0)} (Median ${pct(v.median, 0)}, n = ${v.n} ${t("Jahre")})</div>` : "";
          const floors = Object.entries(mo.untergrenze || {});
          const ftab = floors.length ? `<details><summary>${t("Untergrenze je Kanal")} (${t("Basispreis")})</summary><table class="mini"><thead><tr><th>${t("Kanal")}</th><th class="n">1 N.</th><th class="n">2 N.</th><th class="n">3 N.</th></tr></thead>
            <tbody>${floors.map(([k, f]) => `<tr><td>${esc(chn(k))}</td>${["1", "2", "3"].map((n) => `<td class="n${mo.basispreis && f[n] > mo.basispreis ? " neg" : ""}">${money(f[n], cur)}</td>`).join("")}</tr>`).join("")}</tbody></table>
            <div class="ks">${t("Variable Kosten je Nacht")}: ${money(mo.kosten_je_nacht?.summe, cur, 2)} (${t("Heizung")} ${money(mo.kosten_je_nacht?.heizung, cur, 2)}, ${t("Warmwasser")} ${money(mo.kosten_je_nacht?.warmwasser, cur, 2)}, ${t("Strom")} ${money(mo.kosten_je_nacht?.strom, cur, 2)}, ${t("Wasser")} ${money(mo.kosten_je_nacht?.wasser, cur, 2)}) + ${money(w.je_aufenthalt, cur)} ${t("je Aufenthalt")}</div></details>` : "";
          const label = D(`${mo.monat}-01`).toLocaleDateString(locale(), { month: "long", year: "numeric" });
          return `<div class="emp-m"><div class="row"><b class="grow">${esc(label)}</b><span class="badge ${rc}">${t(rl)}</span></div>
            ${band}
            <div class="ks">${t("Netto-RevPAR")} ${money(mo.netto_revpar_stand, cur, 2)} · DB-RevPAR ${money(mo.db_revpar_stand, cur, 2)} · ${num(mo.frei_ab_heute)} ${t("Nächte frei")}${mo.gesperrt ? ` · ${num(mo.gesperrt)} ${t("gesperrt")}` : ""}
              ${mo.prognose_auslastung !== null && mo.prognose_auslastung !== undefined ? ` · ${t("Prognose")} ${pct(mo.prognose_auslastung, 0)}` : ""}</div>
            <div class="emp-r ${ac}"><b>${t(al)}${e.preis_neu ? ` ${t("auf")} ${money(e.preis_neu, cur)} (${e.prozent > 0 ? "+" : ""}${num(e.prozent)} %)` : ""}</b><span>${esc(t(e.grund || ""))}</span>
              ${mo.untergrenze_massgeblich ? `<span class="ks">${t("Untergrenze")} (2 N., ${t("teuerster Kanal")}): ${money(mo.untergrenze_massgeblich, cur)}</span>` : ""}
              ${(() => {
                const von = mo.monat + "-01" < d.today ? d.today : mo.monat + "-01";
                const base = { von, bis: monthEnd(mo.monat), nur_basispreis: true, label: `${label}: ${t(al)}` };
                const cfg = (vorgabe, title) => ({ title, grund: e.grund, untergrenze: floors2(mo), vorgabe: { ...base, ...vorgabe } });
                const acts = e.preis_neu
                  ? applyBtn("Übernehmen …", cfg({ preis: e.preis_neu, ohne_feiertage: e.aktion === "senken" }, `${label}: ${t(al)}`))
                  : "";
                return `<div class="row" style="gap:6px;margin-top:4px">${acts}${applyBtn("Preis anpassen …", cfg({ preis: mo.basispreis || bp.heute, ohne_feiertage: false }, `${label}: ${t("Preis anpassen")}`), !acts)}</div>`;
              })()}</div>
            ${ftab}</div>`;
        }).join("");
        const hints = (w.hinweise || []).map((h) => {
          let extra = "";
          const end60 = iso(addDays(D(d.today), 59));
          if (h.typ === "wochenende" && h.prozent) extra += `<div class="row" style="margin-top:5px">${applyBtn(`Fr/Sa +${h.prozent} % übernehmen …`, {
            title: h.titel, grund: h.text, vorgabe: { von: d.today, bis: end60, wochentage: h.wochentage, prozent: h.prozent, nur_basispreis: true, label: h.titel } })}</div>`;
          if (h.typ === "feiertag" && h.tage?.length) extra += `<div class="row" style="margin-top:5px">${applyBtn(`Feiertagsnächte +${h.prozent} % …`, {
            title: h.titel, grund: h.text, vorgabe: { tage: h.tage.map((x) => x.datum), prozent: h.prozent, label: h.titel } })}</div>`;
          // v1.18.0: Last-Minute – freie Nächte im Fenster; Rabatt nur gezielt (Lücke/schwacher Monat), Aufschlag nur bei belegter Prämie
          if (h.typ === "lastminute") {
            const st = h.statistik || {};
            extra += `<div class="chips">${(h.naechte || []).map((x) => {
              const tip = `${t("Preis")} ${money(x.preis, cur)} · ${t("Untergrenze")} ${money(x.untergrenze, cur)}${x.grund ? ` · ${t(x.grund)}` : ` · ${t("kein Rabatt empfohlen")}`}`;
              const b = x.vorschlag_preis ? applyBtn(`${fdate(x.datum)} → ${money(x.vorschlag_preis, cur)}`, {
                title: `${t("Last-Minute")} ${fdate(x.datum)}`, grund: tip,
                untergrenze: Object.fromEntries((w.kanaele || []).map((k) => [k.kanal, x.untergrenze])),
                vorgabe: { tage: [x.datum], preis: x.vorschlag_preis, label: `Last-Minute ${x.datum}` } }, false) : "";
              return b || `<span class="chip" data-tip="${esc(tip)}">${fdate(x.datum)} · ${money(x.preis, cur)}</span>`;
            }).join("")}</div>`;
            const free = (h.naechte || []).map((x) => x.datum);
            if (h.aufschlag_prozent && free.length) extra += `<div class="row" style="margin-top:5px">${applyBtn(`+${h.aufschlag_prozent} % ${t("auf die freien Nächte")} …`, {
              title: h.titel, grund: h.text, vorgabe: { tage: free, prozent: h.aufschlag_prozent, label: `Last-Minute +${h.aufschlag_prozent} %` } }, false)}</div>`;
            extra += `<div class="ks" style="white-space:normal">${t("Fenster")}: ${num(h.tage_fenster)} ${t("Tage")} · ${t("max. Rabatt")} ${num(h.rabatt_max)} % · ${t("einstellbar unter Einstellungen → Kosten & Preise")}${st.buchungen ? ` · n = ${num(st.buchungen)}` : ""}</div>`;
          }
          if (h.typ === "einzelnacht" && h.mindestaufenthalt) extra += `<div class="row" style="margin-top:5px">${applyBtn(`Mindestaufenthalt ${h.mindestaufenthalt} setzen …`, {
            title: h.titel, grund: h.text, vorgabe: { von: d.today, bis: iso(addDays(D(d.today), 29)), mindestaufenthalt: h.mindestaufenthalt, label: `Mindestaufenthalt ${h.mindestaufenthalt}` } }, false)}</div>`;
          if (h.typ === "feiertag") extra = extra + `<div class="chips">${h.tage.map((x) => `<span class="chip" data-tip="${esc(`${t("In den Vorjahren belegt")}: ${x.vorjahre_belegt} ${t("von")} ${x.vorjahre}`)}">${fdate(x.datum)} · ${esc(t(x.name))}</span>`).join("")}</div>`;
          if (h.typ === "luecke") extra += `<div class="chips">${h.luecken.map((x) => {
            const tip = `${t("Preis")} ${money(x.preis, cur)} · ${t("Untergrenze")} ${money(x.untergrenze, cur)}${x.buchbar ? "" : ` · ${t("Mindestaufenthalt")} ${x.mindestaufenthalt} – ${t("so nicht buchbar")}`}`;
            const btn = applyBtn(`${fdate(x.von)} · ${num(x.naechte)} N.${x.vorschlag_preis ? ` → ${money(x.vorschlag_preis, cur)}` : ""}`, {
              title: `${t("Lücke")} ${fdate(x.von)} (${num(x.naechte)} N.)`, grund: tip,
              untergrenze: Object.fromEntries((w.kanaele || []).map((k) => [k.kanal, x.untergrenze])),
              vorgabe: { tage: x.tage, preis: x.vorschlag_preis, mindestaufenthalt: x.buchbar ? null : x.naechte, label: `Lücke ${x.von}` } }, false);
            return btn || `<span class="chip ${x.buchbar ? "" : "warn"}" data-tip="${esc(tip)}">${fdate(x.von)} · ${num(x.naechte)} N.</span>`;
          }).join("")}</div>`;
          return `<li><b>${esc(t(h.titel))}</b>${h.wert_eur ? ` <span class="badge good">≈ +${money(h.wert_eur, cur)}/${t("Jahr")}</span>` : ""}<div class="sub">${esc(t(h.text))}</div>${extra}</li>`;
        }).join("");
        // Letzte Preisänderungen aus der Karte mit „Rückgängig“
        const changes = (w.aenderungen || []).map((c) => `<li><span class="grow">${esc(c.label || t("Preisänderung"))} · ${num(c.tage.length)} ${t("Tage")}
            <span class="sub">${new Date(c.zeit).toLocaleString(locale(), { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}${c.benutzer ? ` · ${esc(c.benutzer)}` : ""}</span></span>
          ${c.rueckgaengig ? `<span class="badge">${t("rückgängig gemacht")}</span>` : w.darf_aendern ? `<button class="btn flat sm" data-undo="${esc(c.id)}" data-apt="${w.apartment_id}">↶ ${t("Rückgängig")}</button>` : ""}</li>`).join("");
        const title = w.wohnung ? `<h3 class="emp-apt">${esc(w.wohnung_name || w.wohnung)}</h3>` : "";
        return `${title}${head}<div class="emp-grid">${months}</div>
          ${hints ? `<div class="kl" style="margin:14px 0 6px">${t("Hinweise")}</div><ul class="emp-h">${hints}</ul>` : ""}
          ${changes ? `<div class="kl" style="margin:14px 0 6px">${t("Letzte Preisänderungen")}</div><ul class="emp-c">${changes}</ul>` : ""}
          <div class="ks emp-foot" style="margin-top:10px">${(w.annahmen || []).map((a) => esc(t(a))).join(" · ")}${w.kurzfristig_prozent !== null && w.kurzfristig_prozent !== undefined ? ` · ${num(w.kurzfristig_prozent)} % ${t("der Nächte werden im selben oder im Vormonat gebucht")}` : ""}</div>`;
      }).join("") || `<div class="empty">${t("Keine Daten")}</div>`;
      return panel(t("Bewertung & Empfehlung"), t("Buchungsstand gegen die Vorjahre am gleichen Tag · Preisuntergrenzen aus den variablen Kosten"),
        `${blocks}${gloss(["Netto-RevPAR", "DB-RevPAR", "Untergrenze", "Pace", "n"])}`);
    },
  },
  // 4: Belegungs-Heatmap Wochentag × KW + Auslastung/ADR je Wochentag
  belegung: {
    load: async (c) => {
      const [grid, wd, adr] = await Promise.all([c.q("auslastung", "woche", c.range, { split: "wochentag" }),
        c.q("auslastung", "wochentag", c.range), c.q("adr", "wochentag", c.range)]);
      return { grid, wd, adr };
    },
    render: (card, d, m) => {
      const days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
      const weeks = m.grid.zeilen || [];
      const cols = `grid-template-columns: 30px repeat(${weeks.length}, minmax(${weeks.length > 30 ? 14 : 22}px, 1fr))`;
      let html = `<div></div>${weeks.map((w, i) => `<div class="h">${i % (weeks.length > 30 ? 4 : 1) === 0 ? Number(w.fach.slice(6)) : ""}</div>`).join("")}`;
      for (const day of days) {
        html += `<div class="rl">${t(day)}</div>`;
        for (const w of weeks) {
          const c = w.werte[day];
          if (!c || c.wert === null || c.wert === undefined) { html += `<div class="hc none"></div>`; continue; }
          const a = 0.06 + 0.86 * (c.wert / 100);
          html += `<div class="hc" style="background:color-mix(in srgb, var(--sm-accent) ${Math.round(a * 100)}%, var(--sm-surf2))"
            data-tip="${esc(`${t(day)}, ${binLabel(w.fach, true)}: ${pct(c.wert, 0)} ${t("belegt")}`)}"></div>`;
        }
      }
      const wdRows = statSeries(m.wd), adrRows = new Map(statSeries(m.adr).map((x) => [x.fach, x]));
      const bars = hbars(wdRows.map((x) => ({ label: t(x.fach), value: x.wert, n: x.n,
        tip: `${t(x.fach)}: ${pct(x.wert, 1)} ${t("Auslastung")} · ADR ${money(adrRows.get(x.fach)?.wert, d.apt.currency)} · n = ${x.n}` })),
      { fmt: (v) => pct(v, 0), max: 100 });
      return panel(t("Belegung nach Wochentag"), `${t("Nacht von … auf …, je Kalenderwoche")}`,
        `<div class="split2"><div class="scroll"><div class="hm" style="${cols}">${html}</div>
          <div class="legend"><span class="scale"><i style="background:linear-gradient(90deg, color-mix(in srgb, var(--sm-accent) 6%, var(--sm-surf2)), var(--sm-accent))"></i>0 – 100 %</span>
          <span>${t("Zahlen oben = Kalenderwoche")}</span></div>${gloss(["ADR", "n"])}</div>
          <div><div class="kl" style="margin-bottom:6px">${t("Auslastung je Wochentag")}</div>${bars}</div></div>`);
    },
  },
  // 5: Kanal-Wirtschaftlichkeit (Netto + schraffierte Kosten) + Kanal-Matrix (Netto/Nacht × Anteil Nächte, Blase = Buchungen)
  kanaele: {
    load: async (c) => {
      const ms = ["netto", "kosten", "naechte", "buchungen", "netto_pro_nacht"];
      const res = await Promise.all(ms.map((m) => c.q(m, "kanal", c.range)));
      return Object.fromEntries(ms.map((m, i) => [m, new Map(statSeries(res[i]).map((x) => [x.fach, x]))]));
    },
    render: (card, d, m) => {
      const cur = d.apt.currency;
      const names = [...m.netto.keys()].filter((k) => (m.naechte.get(k)?.wert || 0) > 0 || (m.netto.get(k)?.wert || 0) > 0)
        .sort((a, b) => ((m.netto.get(b)?.wert || 0) + (m.kosten.get(b)?.wert || 0)) - ((m.netto.get(a)?.wert || 0) + (m.kosten.get(a)?.wert || 0)));
      if (!names.length) return panel(t("Kanal-Wirtschaftlichkeit"), "", `<div class="empty">${t("Keine Daten")}</div>`);
      const max = Math.max(...names.map((k) => (m.netto.get(k)?.wert || 0) + (m.kosten.get(k)?.wert || 0)), 1);
      const rows = names.map((k) => {
        const net = m.netto.get(k)?.wert || 0, cost = m.kosten.get(k)?.wert || 0, n = m.buchungen.get(k)?.wert || 0;
        const col = chColor(k);
        const tip = `${k}\n${t("Netto")} ${money(net, cur)} · ${t("Provision & Gebühren")} ${money(cost, cur)} (${pct(net + cost ? (cost / (net + cost)) * 100 : null, 1)})\n${t("Netto/Nacht")} ${money(m.netto_pro_nacht.get(k)?.wert, cur)} · ${num(m.naechte.get(k)?.wert)} ${t("Nächte")} · n = ${n}`;
        return `<div class="hr${n < 5 ? " low" : ""}" data-tip="${esc(tip)}"><span class="hl"><span class="dot" style="background:${col}"></span>${esc(k)}</span>
          <span class="ht"><i style="width:${((net / max) * 100).toFixed(1)}%;background:${col}"></i><i style="width:${((cost / max) * 100).toFixed(1)}%;background:${col};opacity:.5;
            background-image:repeating-linear-gradient(135deg, transparent 0 3px, var(--sm-surf) 3px 5px)"></i></span>
          <span class="hv">${money(net, cur)}<em>+ ${money(cost, cur)}</em></span></div>`;
      }).join("");
      // Kanal-Matrix
      const W = card.chartW(0.42, 360), H = 250, L = 52, R = 14, T = 14, B = 34;
      const total = names.reduce((a, k) => a + (m.naechte.get(k)?.wert || 0), 0) || 1;
      const pts = names.map((k) => ({ k, x: ((m.naechte.get(k)?.wert || 0) / total) * 100, y: m.netto_pro_nacht.get(k)?.wert || 0, n: m.buchungen.get(k)?.wert || 0 }));
      const xmax = niceMax(Math.max(10, ...pts.map((p) => p.x)) * 1.1), ymax = niceMax(Math.max(10, ...pts.map((p) => p.y)) * 1.15);
      const nmax = Math.max(...pts.map((p) => p.n), 1);
      const X = (v) => L + (W - L - R) * (v / xmax), Y = (v) => T + (H - T - B) * (1 - v / ymax);
      let svg = "";
      for (let g = 0; g <= 4; g++) {
        svg += `<line x1="${L}" x2="${W - R}" y1="${Y((ymax / 4) * g)}" y2="${Y((ymax / 4) * g)}" stroke="currentColor" stroke-opacity=".1"/>
          <text x="${L - 6}" y="${Y((ymax / 4) * g) + 4}" text-anchor="end" font-size="10.5" fill="currentColor" fill-opacity=".55">${money((ymax / 4) * g, cur)}</text>
          <text x="${X((xmax / 4) * g)}" y="${H - 16}" text-anchor="middle" font-size="10.5" fill="currentColor" fill-opacity=".55">${num((xmax / 4) * g)} %</text>`;
      }
      svg += `<text x="${(L + W - R) / 2}" y="${H - 2}" text-anchor="middle" font-size="10.5" font-weight="600" fill="currentColor" fill-opacity=".6">${t("Anteil Nächte")}</text>`;
      // Blasen groß → klein (kleine liegen oben); Beschriftung mit einfacher Kollisionsvermeidung
      const placed = [];
      let labels = "";
      for (const p of pts.sort((a, b) => b.n - a.n)) {
        const r = 6 + 16 * Math.sqrt(p.n / nmax);
        svg += `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="${r}" fill="${chColor(p.k)}" fill-opacity="${p.n < 5 ? 0.25 : 0.55}" stroke="${chColor(p.k)}" stroke-width="1.5"
          data-tip="${esc(`${p.k}: ${money(p.y, cur)} ${t("netto je Nacht")} · ${pct(p.x, 0)} ${t("der Nächte")} · n = ${p.n}`)}"/>`;
        const w = p.k.length * 6.2;
        let lx = X(p.x) + r + 4;
        if (lx + w > W - 2) lx = X(p.x) - r - 4 - w;
        let ly = Y(p.y) + 4;
        for (const off of [0, -14, 14, -28, 28, -42, 42]) {
          const yy = Y(p.y) + 4 + off;
          if (!placed.some((q) => lx < q.x + q.w && lx + w > q.x && Math.abs(yy - q.y) < 13)) { ly = yy; break; }
        }
        placed.push({ x: lx, y: ly, w });
        labels += `<text x="${lx}" y="${ly}" font-size="10.5" font-weight="600" fill="currentColor" pointer-events="none">${esc(p.k)}</text>`;
      }
      svg += labels;
      return panel(t("Kanal-Wirtschaftlichkeit"), t("Netto und Provision/Gebühren (schraffiert) je Kanal"),
        `<div class="split2"><div><div class="hb">${rows}</div>
          <div class="legend"><span><i style="background:var(--sm-ink)"></i>${t("Netto")}</span>
          <span><i style="background:var(--sm-ink);opacity:.5;background-image:repeating-linear-gradient(135deg, transparent 0 3px, var(--sm-surf) 3px 5px)"></i>${t("Provision & Gebühren")}</span>
          <span>${t("blass = weniger als 5 Buchungen")}</span></div></div>
          <div><div class="kl">${t("Kanal-Matrix: Netto je Nacht × Anteil Nächte, Blase = Buchungen")}</div>
          <svg class="ch" viewBox="0 0 ${W} ${H}" role="img">${svg}</svg></div></div>`);
    },
  },
  // 6: Buchungsfenster- und Aufenthalts-Histogramme
  fenster: {
    load: async (c) => {
      const [lead, stay, leadM, stayM] = await Promise.all([c.q("buchungen", "vorlauf", c.range), c.q("buchungen", "aufenthalt", c.range),
        c.q("vorlauf", "gesamt", c.range), c.q("aufenthalt", "gesamt", c.range)]);
      return { lead, stay, leadM: statCell(leadM), stayM: statCell(stayM) };
    },
    render: (card, d, m) => {
      const W = card.chartW(0.48, 340);
      const lead = statSeries(m.lead).filter((x) => x.fach !== "unbekannt");
      const stay = statSeries(m.stay);
      const nl = lead.reduce((a, x) => a + (x.wert || 0), 0), ns = stay.reduce((a, x) => a + (x.wert || 0), 0);
      const items = (rows, n, unit) => rows.map((x) => ({ label: x.fach, value: x.wert || 0,
        tip: `${x.fach} ${unit}: ${num(x.wert || 0)} ${t("Buchungen")} (${pct(n ? ((x.wert || 0) / n) * 100 : null, 0)})` }));
      return panel(t("Buchungsfenster & Aufenthalt"), t("Buchungen mit Anreise im Zeitraum"),
        `<div class="split2 even"><div><div class="kl">${t("Vorlauf (Tage zwischen Buchung und Anreise)")} · Median <b>${num(m.leadM.wert)} ${t("Tage")}</b> · n = ${nl}${nl < 5 ? ` · <span class="lowtag">${t("wenig Daten")}</span>` : ""}</div>
          ${vbars(items(lead, nl, t("Tage")), { W })}</div>
          <div><div class="kl">${t("Aufenthalt (Nächte)")} · Median <b>${num(m.stayM.wert, 1)} ${t("N.")}</b> · n = ${ns}${ns < 5 ? ` · <span class="lowtag">${t("wenig Daten")}</span>` : ""}</div>
          ${vbars(items(stay, ns, t("Nächte")), { W })}</div></div>`);
    },
  },
  // Buchungszeitpunkt (Wunsch Betreiber 16.11.2026): Aufenthaltsmonat × „wie viele Monate vorher gebucht“.
  // Zeile = Monat des Aufenthalts (Jan–Dez über mehrere Jahre), Spalte = Abstand Buchungsmonat → Aufenthaltsmonat,
  // Zelle = Anteil der Zeile; Tooltip mit Anzahl und kumuliertem Anteil („bis dahin gebucht“).
  // Basis standardmäßig alle abgeschlossenen Monate ab dem ersten nicht ausgenommenen Jahr (ohne 2020), weil
  // laufende/künftige Monate noch Kurzfrist-Buchungen fehlen und das Bild Richtung „früh gebucht“ verzerren würden.
  buchungszeit: {
    load: async (c) => {
      const s = c.s;
      const ty = D(c.today).getFullYear();
      const ex = (c.card._config.matrix_exclude_years || []).map(Number);
      let from = Math.max(Number((c.apt.erster_tag || c.today).slice(0, 4)), ty - 6);
      while (ex.includes(from) && from < ty) from += 1;
      const range = s.bzBasis === "filter" ? c.range : [new Date(from, 0, 1), new Date(D(c.today).getFullYear(), D(c.today).getMonth(), 1)];
      const m = s.bzMeasure || "naechte";
      if (s.bzView === "kalender") {
        // Ansicht „Buchungsmonat → Aufenthaltsmonat“ (Wunsch Betreiber: „im Oktober wird für August gebucht“)
        const cal = await c.q(m, "buchungsmonat_im_jahr", range, { split: "monat_im_jahr" });
        return { cal, range, measure: m, view: "kalender" };
      }
      const [rows, total] = await Promise.all([c.q(m, "monat_im_jahr", range, { split: "vorlauf_monate" }), c.q(m, "gesamt", range, { split: "vorlauf_monate" })]);
      return { rows, total, range, measure: m, view: "vorlauf" };
    },
    render: (card, d, m) => {
      const s = card._state;
      const cur = d.apt.currency;
      const seg = (key, opts, val) => `<div class="seg">${opts.map(([k, l]) => `<button data-bz="${key}:${k}" aria-pressed="${val === k}">${t(l)}</button>`).join("")}</div>`;
      const controls = `${seg("v", [["kalender", "Gebucht im → für"], ["vorlauf", "Monate vorher"]], m.view)}
        ${seg("m", [["naechte", "Nächte"], ["buchungen", "Buchungen"], ["umsatz", "Umsatz"]], s.bzMeasure || "naechte")}
        ${seg("b", [["alle", "Alle Jahre"], ["filter", "Zeitraum"]], s.bzBasis || "alle")}`;
      if (m.view === "kalender") return bookingCalendar(card, d, m, controls);
      // früh → kurzfristig, damit die Zeile von links nach rechts „bis dahin gebucht“ liest
      const order = ["> 12 Monate", "7–12 Monate", "4–6 Monate", "3 Monate", "2 Monate", "1 Monat", "gleicher Monat", "unbekannt"];
      const cols = order.filter((k) => (m.total.serien || []).includes(k) && (k !== "unbekannt" || m.total.zeilen?.[0]?.werte?.[k]?.wert));
      const fmtV = (v) => (m.measure === "umsatz" ? money(v, cur) : num(v));
      const unitWord = { naechte: "Nächte", buchungen: "Buchungen", umsatz: "Umsatz" }[m.measure];
      const line = (label, werte, bold = false) => {
        const vals = cols.map((k) => werte?.[k]?.wert || 0);
        const sum = vals.reduce((a, b) => a + b, 0);
        const n = cols.reduce((a, k) => a + (werte?.[k]?.n || 0), 0);
        let cum = 0, half = null;
        const cells = cols.map((k, i) => {
          const share = sum ? (vals[i] / sum) * 100 : null;
          cum += vals[i];
          const cumShare = sum ? (cum / sum) * 100 : null;
          if (half === null && cumShare !== null && cumShare >= 50) half = k;
          if (share === null) return `<div class="c none">–</div>`;
          const a = 0.06 + 0.84 * Math.min(1, share / 60);
          return `<div class="c${n < 5 ? " low" : ""}${bold ? " tot" : ""}" style="background:color-mix(in srgb, var(--sm-accent) ${Math.round(a * 100)}%, var(--sm-surf));${a > 0.55 ? "color:var(--sm-acc-ink);" : ""}"
            data-tip="${esc(`${label} · ${t(k)} ${k === "gleicher Monat" || k === "unbekannt" ? "" : t("vorher")}\n${fmtV(vals[i])} ${t(unitWord)} = ${pct(share, 1)} ${t("der Zeile")}\n${t("bis dahin gebucht")}: ${pct(cumShare, 0)}`)}">${pct(share, 0)}</div>`;
        }).join("");
        return `<div class="rl"${bold ? ' style="color:var(--sm-ink)"' : ""}>${esc(label)}</div>${cells}
          <div class="c avg${bold ? " tot" : ""}" data-tip="${esc(`${label}: ${fmtV(sum)} ${t(unitWord)} · n = ${n} ${t("Buchungen")}`)}">${fmtV(sum)}</div>
          <div class="c avg${bold ? " tot" : ""}">${half ? esc(t(half)) : "–"}</div>`;
      };
      const byMonth = new Map((m.rows.zeilen || []).map((z) => [z.fach, z.werte]));
      let html = `<div></div>${cols.map((k) => `<div class="h">${esc(t(k))}</div>`).join("")}<div class="h">Σ ${esc(t(unitWord))}</div><div class="h">${t("Hälfte gebucht bis")}</div>`;
      for (let mo = 1; mo <= 12; mo++) html += line(t(MONTHS_SHORT[mo - 1]), byMonth.get(String(mo).padStart(2, "0")));
      html += `<div class="gap"></div>${line(t("Alle"), m.total.zeilen?.[0]?.werte, true)}`;
      // Kernaussage: Anteil kurzfristig (gleicher Monat + 1 Monat vorher)
      const tw = m.total.zeilen?.[0]?.werte || {};
      const all = cols.reduce((a, k) => a + (tw[k]?.wert || 0), 0);
      const short = (tw["gleicher Monat"]?.wert || 0) + (tw["1 Monat"]?.wert || 0);
      const early = (tw["> 12 Monate"]?.wert || 0) + (tw["7–12 Monate"]?.wert || 0) + (tw["4–6 Monate"]?.wert || 0);
      const lede = all ? `<b>${pct((short / all) * 100, 0)}</b> ${t("der")} ${t(unitWord)} ${t("werden im selben oder im Vormonat gebucht")}, <b>${pct((early / all) * 100, 0)}</b> ${t("mindestens 4 Monate vorher")}.` : "";
      const grid = `grid-template-columns: 44px repeat(${cols.length}, minmax(58px, 1fr)) minmax(80px, 1fr) minmax(96px, 1fr)`;
      return panel(t("Buchungszeitpunkt"), `${t("Wann wird für welchen Aufenthaltsmonat gebucht?")} · ${fdate(iso(m.range[0]))} – ${fdate(iso(addDays(m.range[1], -1)))}`,
        `${lede ? `<p style="margin:0 0 10px">${lede}</p>` : ""}<div class="scroll"><div class="mx" style="${grid}">${html}</div></div>
          <div class="legend"><span class="scale"><i style="background:linear-gradient(90deg, color-mix(in srgb, var(--sm-accent) 6%, var(--sm-surf)), var(--sm-accent))"></i>${t("Anteil der Zeile")} 0 – 60 %+</span>
          <span>${t("Spalte = Abstand Buchungsmonat → Aufenthaltsmonat")}</span><span>${t("Nächte: je Nacht im jeweiligen Monat")}</span>
          <span><i style="background:var(--sm-warn);width:6px;height:6px;border-radius:50%"></i><em>${t("kursiv")}</em> = ${t("weniger als 5 Buchungen")}</span></div>`,
        controls);
    },
  },
  // 7: Verlorene Nächte (Lücken zwischen Buchungen) + Vorschläge
  luecken: {
    load: (c) => c.ws("gaps"),
    render: (card, d, m) => {
      const cur = d.apt.currency;
      const p = m.vergangen, f = m.kommend;
      const tiles = tilesRow([
        [t("Entgangen (vergangen)"), money(p.wert, cur), `${num(p.naechte)} ${t("Nächte")} in ${p.luecken} ${t("Lücken")}${p.geschaetzt ? ` · ${p.geschaetzt} ${t("geschätzt")}` : ""}`,
          t("Vergangene freie Nächte zwischen zwei Belegungen × Tagespreis (gespeichert) bzw. Ø-Monatspreis (geschätzt)")],
        [t("Offen (kommend)"), money(f.wert, cur), `${num(f.naechte)} ${t("Nächte")} in ${f.luecken} ${t("Lücken")}`, t("Kommende Lücken × aktueller Tagespreis")],
        [t("Unter Mindestaufenthalt"), num(f.zu_kurz + p.zu_kurz), `${num(f.zu_kurz_naechte + p.zu_kurz_naechte)} ${t("Nächte so nicht buchbar")}`,
          t("Lücke kürzer als der Mindestaufenthalt am ersten freien Tag (nur wo der Mindestaufenthalt bekannt ist)")],
      ]);
      const hist = vbars(m.laengen.map((x) => ({ label: x.fach, value: x.anzahl, tip: `${x.fach} ${t("Nächte")}: ${x.anzahl} ${t("Lücken")}` })), { W: card.chartW(0.36, 300), H: 170 });
      const list = m.luecken.slice().sort((a, b) => b.von.localeCompare(a.von)).slice(0, 14).map((g) => `<tr>
        <td>${fdowLong(g.von)}${g.wohnung ? codeTag(g.wohnung) : ""}</td><td class="n">${g.naechte}</td>
        <td class="n">${money(g.wert, cur)}${g.quelle === "geschaetzt" ? ` <span class="badge" title="${t("Ø-Monatspreis, kein gespeicherter Tagespreis")}">≈</span>` : ""}</td>
        <td class="n">${g.mindestaufenthalt ?? "–"}</td>
        <td>${g.zu_kurz ? `<span class="badge bad">${t("zu kurz")}</span>` : g.vergangen ? `<span class="badge">${t("vergangen")}</span>` : `<span class="badge good">${t("buchbar")}</span>`}</td></tr>`).join("");
      const hints = m.vorschlaege.length ? `<ul class="ins">${m.vorschlaege.slice(0, 6).map((h) =>
        `<li>${h.wohnung ? codeTag(h.wohnung) + " " : ""}${t("Mindestaufenthalt ab")} <b>${fdowLong(h.von)}</b> ${t("von")} ${h.mindestaufenthalt} ${t("auf")} <b>${h.naechte}</b> ${t("senken")} – ${money(h.wert, cur)} ${t("möglich")}</li>`).join("")}</ul>`
        : `<div class="sub">${t("Keine kommende Lücke unter dem Mindestaufenthalt.")}</div>`;
      return panel(t("Verlorene Nächte"), t("Freie Nächte zwischen zwei Belegungen (bis 14 Nächte), Sperrzeiten zählen als belegt"),
        `${tiles}<div class="split2"><div><div class="kl">${t("Letzte Lücken")}</div><div class="scroll"><table><thead><tr><th>${t("Ab")}</th><th class="n">${t("Nächte")}</th>
          <th class="n">${t("Wert")}</th><th class="n">${t("Mindestaufenthalt")}</th><th>${t("Status")}</th></tr></thead><tbody>${list || `<tr><td colspan="5" class="empty">${t("Keine Lücken im Zeitraum")}</td></tr>`}</tbody></table></div></div>
          <div><div class="kl">${t("Lückenlänge (Nächte)")}</div>${hist}<div class="kl" style="margin-top:10px">${t("Vorschlag")}</div>${hints}</div></div>
          <div class="sub" style="margin-top:8px">≈ = ${t("geschätzt mit Ø-Monatspreis (Smoobu liefert Tagespreise nicht rückwirkend; ab jetzt speichert die Integration sie täglich)")}</div>`);
    },
  },
  // 8: Stornos
  stornos: {
    load: (c) => c.ws("storno"),
    render: (card, d, m) => {
      const cur = d.apt.currency;
      const low = m.buchungen < 5;
      const tiles = tilesRow([
        [t("Stornoquote"), pct(m.quote, 1), `${m.stornos} ${t("von")} ${m.buchungen} ${t("Buchungen")}`, "", low],
        [t("Ausfall"), money(m.ausfall, cur), `${num(m.naechte)} ${t("Nächte")}`, t("Brutto der stornierten Buchungen")],
        [t("Wiederbelegt"), pct(m.wiederbelegt_prozent, 0), `${num(m.wiederbelegt_naechte)} ${t("von")} ${num(m.naechte)} ${t("Nächten")}`,
          t("Nächte stornierter Buchungen, die später von einer anderen Buchung belegt sind")],
        [t("Storno-Vorlauf"), m.vorlauf_median === null ? "–" : `${num(m.vorlauf_median)} ${t("Tage")}`, t("Median vor Anreise"),
          t("Anreise − Änderungsdatum (Smoobu liefert kein Stornodatum, Näherung)")],
      ]);
      const ch = hbars(m.kanaele.filter((k) => k.buchungen + k.stornos > 0).map((k) => ({ label: chn(k.kanal), dot: chColor(k.kanal), color: chColor(k.kanal),
        value: k.quote || 0, n: k.buchungen + k.stornos, tip: `${chn(k.kanal)}: ${pct(k.quote, 1)} (${k.stornos} ${t("von")} ${k.buchungen + k.stornos}) · ${t("Ausfall")} ${money(k.ausfall, cur)}` })),
      { fmt: (v) => pct(v, 0), max: 100 });
      const hist = vbars(m.vorlauf.map((x) => ({ label: x.fach, value: x.anzahl, color: "var(--sm-bad)", tip: `${x.fach} ${t("Tage vor Anreise")}: ${x.anzahl} ${t("Stornos")}` })),
        { W: card.chartW(0.4, 300), H: 170 });
      return panel(t("Stornos"), t("Buchungen mit Anreise im Zeitraum"),
        `${tiles}<div class="split2"><div><div class="kl">${t("Stornoquote je Kanal")}</div>${ch}</div>
          <div><div class="kl">${t("Storno-Vorlauf (Tage vor Anreise)")}</div>${hist}</div></div>`);
    },
  },
  // 9: Gäste (Personen, Hund, Stammgäste, Sprache)
  gaeste: {
    load: async (c) => {
      // v1.18.0b7: je Merkmal Buchungen UND Nächte (Wunsch Betreiber 17.11.2026). Bezug wie überall:
      // Buchungen nach Anreise im Zeitraum, Nächte = belegte Nächte, die in den Zeitraum fallen.
      // Alternative verworfen: Umschalter Buchungen/Nächte – dann sieht man den Unterschied nie gleichzeitig
      // (z. B. Hundegäste: wenige Buchungen, aber lange Aufenthalte).
      const dims = ["personen", "hund", "stammgast", "sprache"];
      const [res, resN, npn] = await Promise.all([Promise.all(dims.map((x) => c.q("buchungen", x, c.range))),
        Promise.all(dims.map((x) => c.q("naechte", x, c.range))), c.q("netto_pro_nacht", "stammgast", c.range)]);
      return { ...Object.fromEntries(dims.map((x, i) => [x, { b: statSeries(res[i]), n: statSeries(resN[i]) }])), npn: statSeries(npn) };
    },
    render: (card, d, m) => {
      const LANGS = { de: "Deutsch", en: "Englisch", nl: "Niederländisch", fr: "Französisch", it: "Italienisch", pl: "Polnisch", cs: "Tschechisch", es: "Spanisch", da: "Dänisch" };
      // Doppelbalken je Ausprägung: oben Anteil Buchungen (kräftig), darunter Anteil Nächte (hell)
      const block = (title, data, label = (x) => x) => {
        const nb = data.b.reduce((a, x) => a + (x.wert || 0), 0);
        const nn = data.n.reduce((a, x) => a + (x.wert || 0), 0);
        const byN = new Map(data.n.map((x) => [x.fach, x.wert || 0]));
        const byB = new Map(data.b.map((x) => [x.fach, x.wert || 0]));
        // Ausprägungen aus beiden Abfragen (eine Buchung mit Anreise vor dem Zeitraum hat nur Nächte darin)
        const keys = [...new Set([...byB.keys(), ...byN.keys()])].filter((k) => byB.get(k) || byN.get(k))
          .sort((a, b) => (byB.get(b) || 0) - (byB.get(a) || 0) || (byN.get(b) || 0) - (byN.get(a) || 0)).slice(0, 7);
        const share = (v, tot) => (tot ? (v / tot) * 100 : 0);
        const rows = keys.map((k) => {
          const b = byB.get(k) || 0, nt = byN.get(k) || 0, pb = share(b, nb), pn = share(nt, nn);
          const tip = `${label(k)}: ${num(b)} ${t("Buchungen")} (${pct(pb, 0)}) · ${num(nt)} ${t("Nächte")} (${pct(pn, 0)})`;
          return `<div class="hr" data-tip="${esc(tip)}"><span class="hl">${esc(label(k))}</span>
            <span class="ht dual"><i style="width:${pb.toFixed(1)}%"></i><i class="n" style="width:${pn.toFixed(1)}%"></i></span>
            <span class="hv">${pct(pb, 0)}<em>${pct(pn, 0)}</em></span></div>`;
        }).join("");
        return `<div><div class="kl">${title} · n = ${num(nb)} ${t("Buchungen")} · ${num(nn)} ${t("Nächte")}${nb < 5 ? ` · <span class="lowtag">${t("wenig Daten")}</span>` : ""}</div><div class="hb">${rows}</div></div>`;
      };
      const npn = new Map(m.npn.map((x) => [x.fach, x]));
      const sg = npn.get("Stammgast"), nk = npn.get("Neukunde");
      return panel(t("Gäste"), t("Anteil der Buchungen (Anreise im Zeitraum) und der Nächte im Zeitraum"),
        `<div class="quad">${block(t("Personen"), m.personen, (f) => `${f} ${f === "1" ? t("Person") : t("Personen")}`)}
          ${block(t("Hund"), m.hund, (f) => t(f))}
          ${block(t("Stammgäste"), m.stammgast, (f) => t(f))}
          ${block(t("Sprache"), m.sprache, (f) => t(LANGS[f] || f))}</div>
          <div class="legend" style="margin-top:8px"><span><i style="background:var(--sm-accent)"></i>${t("Buchungen")}</span>
            <span><i style="background:color-mix(in srgb, var(--sm-accent) 40%, var(--sm-surf2))"></i>${t("Nächte")}</span></div>
          ${sg?.wert && nk?.wert ? `<div class="sub" style="margin-top:8px">${t("Netto je Nacht")}: ${t("Stammgast")} ${money(sg.wert, d.apt.currency)} (n = ${sg.n}) · ${t("Neukunde")} ${money(nk.wert, d.apt.currency)} (n = ${nk.n})</div>` : ""}`);
    },
  },
  // v1.18.0b7: Ehrentafel (Fun-Statistik) – Backend stats.ranking. Zwei Spalten mit je Top 3:
  // „Die Goldene Fußmatte“ (Lieblingsgäste) und „Die Rostige Klobürste“ (sarkastischer Wanderpokal).
  // Je Platz die zwei stärksten Kriterien als Spruch; Tooltip zeigt alle Kriterien mit Rohwert und Punkten.
  ehrentafel: {
    load: (c) => c.ws("ranking"),
    render: (card, d, m) => {
      const cur = d.apt.currency;
      const std = m.standard || { check_in: 16, check_out: 11 };
      const hrs = (v) => `${num(v, v % 1 ? 1 : 0)} h`;
      const hm = (v) => { const h = Math.floor(v), mi = Math.round((v - h) * 60); return `${h}:${String(mi).padStart(2, "0")}`; };
      const hOf = (s) => { if (!s) return null; const [h, mi] = String(s).split(":").map(Number); return isNaN(h) ? null : h + (mi || 0) / 60; };
      const nights = (n) => `${num(n)} ${n === 1 ? t("Nacht") : t("Nächte")}`;
      // Rohwert je Kriterium (für Tooltip) – null = fehlt (zählt neutral 50)
      const raw = {
        preis: (g) => `${money(g.netto_pro_nacht, cur)} ${t("netto/Nacht")}`,
        billig: (g) => `${money(g.netto_pro_nacht, cur)} ${t("netto/Nacht")}`,
        ruhe: (g) => (g.anliegen === null ? null : `${num(g.anliegen)} ${t("Anliegen")}`),
        gespraechig: (g) => (g.nachrichten === null ? null : `${num(g.nachrichten)} ${t("Nachrichten")} (${num(g.nachrichten_je_nacht, 1)} ${t("je Nacht")})`),
        puenktlich: (g) => (g.extra_stunden === null ? null : `+${hrs(g.extra_stunden)}`),
        extra: (g) => (g.extra_stunden === null ? null : `+${hrs(g.extra_stunden)}`),
        vorlauf: (g) => (g.vorlauf_tage === null || g.vorlauf_tage === undefined ? null : `${num(g.vorlauf_tage)} ${t("Tage")}`),
        kurz: (g) => nights(g.naechte),
        portal: (g) => (g.netto_quote === null ? null : `${pct(100 - g.netto_quote * 100, 0)} ${t("Abzug")}`),
      };
      const NAMES = { preis: "Preis", ruhe: "Ruhe", puenktlich: "Pünktlichkeit", vorlauf: "Vorlauf", extra: "Extra-Stunden",
        billig: "Billigpreis", gespraechig: "Gesprächigkeit", kurz: "Kurzaufenthalt", portal: "Portal-Abzug" };
      // Sprüche: nur für Kriterien mit echtem Wert (ein neutrales 50 ist keine Begründung)
      const quip = {
        preis: (g) => `💶 ${t("Zahlt")} ${money(g.netto_pro_nacht, cur)}/${t("Nacht")} – ${t("Respekt")}`,
        ruhe: (g) => (g.anliegen === 0 ? `🤫 ${t("Schweigsam wie ein Mönch: 0 Anliegen")}` : `🧘 ${t("Pflegeleicht")}: ${num(g.anliegen)} ${t("Anliegen")}`),
        puenktlich: (g) => (g.extra_stunden === 0 ? `⏰ ${t("Pünktlich wie ein Schweizer Uhrwerk")}` : `⏰ ${t("Fast pünktlich")}: +${hrs(g.extra_stunden)}`),
        vorlauf: (g) => `🗓️ ${t("Plant voraus")}: ${num(g.vorlauf_tage)} ${t("Tage vorher gebucht")}`,
        extra: (g) => {
          const ci = hOf(g.check_in), co = hOf(g.check_out);
          const early = ci !== null ? Math.max(0, std.check_in - ci) : 0, late = co !== null ? Math.max(0, co - std.check_out) : 0;
          if (early && late) return `🛏️ ${t("Frühaufsteher und Langschläfer")}: ${hm(ci)} – ${hm(co)} (+${hrs(g.extra_stunden)})`;
          return early ? `🐓 ${t("Frühaufsteher")}: ${t("Check-in")} ${hm(ci)} (+${hrs(early)})` : `😴 ${t("Langschläfer")}: ${t("Check-out")} ${hm(co)} (+${hrs(late)})`;
        },
        billig: (g) => `🏷️ ${t("Schnäppchenjäger")}: ${money(g.netto_pro_nacht, cur)}/${t("Nacht")}`,
        gespraechig: (g) => `✉️ ${t("Brieffreund")}: ${num(g.nachrichten)} ${t("Nachrichten")}`,
        kurz: (g) => (g.naechte === 1 ? `🧽 ${t("Eine Nacht, volle Reinigung")}` : `🧽 ${t("Kurz und schmutzig")}: ${nights(g.naechte)}`),
        portal: (g) => `🍽️ ${t("Das Portal isst mit")}: ${pct(100 - g.netto_quote * 100, 0)} ${t("weg")}`,
      };
      const MEDALS = ["🥇", "🥈", "🥉"];
      const place = (g, i, key) => {
        const sc = g[key];
        const crit = Object.entries(sc.kriterien).filter(([c]) => raw[c](g) !== null).sort((a, b) => b[1] - a[1]);
        const lines = crit.slice(0, 2).map(([c]) => quip[c](g));
        if (key === "gold" && g.stammgast) lines.push(`🏠 ${t("Stammgast – gehört fast zur Familie")}`);
        const tip = `${g.name} · ${fdate(g.anreise)} – ${fdate(g.abreise)} · ${chn(g.kanal)}\n${t("Punkte")}: ${num(sc.punkte, 1)}${key === "gold" && g.stammgast ? ` (${t("inkl. Stammgast-Bonus")})` : ""}\n`
          + Object.entries(sc.kriterien).map(([c, p]) => `${t(NAMES[c])}: ${raw[c](g) ?? t("keine Daten (neutral)")} → ${num(p)}`).join("\n");
        return `<div class="rk click" data-open="${g.id}" data-tip="${esc(tip)}">
          <div class="rm">${MEDALS[i]}</div>
          <div class="rb"><div class="rn"><b>${esc(g.name)}</b><span class="dot" style="background:${chColor(g.kanal)}"></span><span class="sub">${fdate(g.anreise)} – ${fdate(g.abreise)}</span></div>
            ${lines.map((l) => `<div class="rq">${esc(l)}</div>`).join("")}</div>
          <div class="rp">${num(sc.punkte)}<em>${t("Pkt.")}</em></div></div>`;
      };
      const col = (title, sub, list, key) => `<div class="rcol ${key}"><div class="rh">${title}</div><div class="sub">${sub}</div>
        ${list.length ? list.map((g, i) => place(g, i, key)).join("") : `<div class="empty">${t("Keine abgeschlossenen Aufenthalte im Zeitraum")}</div>`}</div>`;
      const cov = m.abdeckung || {};
      const note = `${t("Gewertet")}: ${num(m.gaeste)} ${t("Aufenthalte mit Abreise im Zeitraum")} · ${t("Uhrzeit bekannt")}: ${num(cov.uhrzeit)} · ${t("Nachrichten geladen")}: ${num(cov.nachrichten)}`
        + ` · ${t("Standard")} ${hm(std.check_in)} / ${hm(std.check_out)}`;
      return panel(`🏆 ${t("Ehrentafel")}`, t("Nur zum Spaß – keine Gästebewertung"),
        `${m.zu_wenig ? `<div class="hint">${t("Zu wenig Gäste für eine faire Wertung")} (n = ${num(m.gaeste)} < ${m.min_n}) – ${t("Zeitraum vergrößern")}.</div>` : ""}
        <div class="split2 even">${col(`🏆 ${t("Die Goldene Fußmatte")}`, t("Gäste, die man gern wieder sieht"), m.goldene_fussmatte || [], "gold")}
          ${col(`🪠 ${t("Die Rostige Klobürste")}`, t("Wanderpokal für besonderen Einsatz"), m.rostige_kloburste || [], "buerste")}</div>
        <div class="sub" style="margin-top:10px">${note}</div>`);
    },
  },
  // 10: Service (Antwortzeit)
  service: {
    load: (c) => c.ws("service"),
    render: (card, d, m) => {
      const g = m.gesamt;
      const dur = (v) => (v === null || v === undefined ? "–" : v < 60 ? `${num(v)} min` : v < 1440 ? `${num(v / 60, 1)} h` : `${num(v / 1440, 1)} ${t("Tage")}`);
      const tiles = tilesRow([
        [t("Antwortzeit (Median)"), dur(g.median), `n = ${g.n} ${t("Antworten")}`, t("Zeit von der ersten Gastnachricht bis zur nächsten Nachricht an den Gast (auch automatische)"), g.wenig_daten],
        [t("Antwort unter 1 h"), pct(g.unter_1h, 0), "", "", g.wenig_daten],
        [t("Ausgewertet"), `${num(m.geladen)} / ${num(m.buchungen)}`, m.abruf_laeuft ? t("Abruf läuft …") : t("Buchungen mit Nachrichten-Verlauf"),
          t("Nachrichten werden im Hintergrund gedrosselt nachgeladen (einmalig ab 2020, danach stündlich neue)")],
      ]);
      if (!g.n) return panel(t("Service"), t("Antwortzeit auf Gästenachrichten"), `${tiles}${effortHtml(m.aufwand)}<div class="empty">${m.geladen ? t("Keine Gastnachrichten im Zeitraum") : t("Noch keine Nachrichten ausgewertet – der Abruf startet etwa 10 Minuten nach dem Start von Home Assistant.")}</div>`);
      const hist = vbars(m.verteilung.map((x) => ({ label: x.fach, value: x.anzahl })), { W: card.chartW(0.48, 340), H: 180 });
      const ch = hbars(m.kanaele.map((k) => ({ label: chn(k.kanal), dot: chColor(k.kanal), color: chColor(k.kanal), value: k.median, n: k.n,
        tip: `${chn(k.kanal)}: Median ${dur(k.median)} · ${pct(k.unter_1h, 0)} < 1 h · n = ${k.n}` })), { fmt: dur });
      return panel(t("Service"), t("Antwortzeit auf Gästenachrichten, Buchungen mit Anreise im Zeitraum"),
        `${tiles}<div class="split2 even"><div><div class="kl">${t("Verteilung der Antwortzeiten")}</div>${hist}</div>
          <div><div class="kl">${t("Median je Kanal")}</div>${ch}</div></div>${effortHtml(m.aufwand)}`);
    },
  },
  // 11: Datentabelle aller Buchungen im Filter + CSV
  tabelle: {
    load: (c) => c.card.store.ws("smoobu/bookings", { ...c.target, start: iso(c.range[0]), end: iso(c.range[1]), ...(c.channels.length ? { channels: c.channels } : {}) }),
    render: (card, d, m) => {
      const cur = d.apt.currency;
      const rows = (m.buchungen || []).filter((b) => !b.blockiert).sort((a, b) => b.anreise.localeCompare(a.anreise));
      const shown = card._state.tableAll ? rows : rows.slice(0, 25);
      const body = shown.map((b) => `<tr class="click${b.storniert ? " muted" : ""}" data-open="${b.id}"><td>${fdate(b.anreise)}</td><td>${fdate(b.abreise)}</td>
        <td>${esc(b.gast || "–")}${card.code(b)}${b.hund ? " 🐕" : ""}</td><td><span class="dot" style="background:${chColor(b.kanal)}"></span> ${esc(chn(b.kanal))}</td>
        <td class="n">${b.naechte}</td><td class="n">${b.personen ?? "–"}</td><td class="n">${money(b.brutto, cur)}</td><td class="n">${money(b.netto, cur)}</td>
        <td class="n">${b.vorlauf_tage ?? "–"}</td><td>${b.storniert ? `<span class="badge bad">${t("storniert")}</span>` : esc(t(b.status || ""))}</td></tr>`).join("");
      const more = rows.length > 25 ? `<button class="lnk" data-k="tableall">${card._state.tableAll ? t("Weniger anzeigen") : `${t("Alle")} ${rows.length} ${t("anzeigen")}`}</button>` : "";
      return panel(t("Datentabelle"), `${rows.length} ${t("Buchungen im Filter (inkl. Stornos)")}`,
        `<div class="scroll"><table><thead><tr><th>${t("Anreise")}</th><th>${t("Abreise")}</th><th>${t("Gast")}</th><th>${t("Kanal")}</th><th class="n">${t("Nächte")}</th>
          <th class="n">${t("Personen")}</th><th class="n">${t("Brutto")}</th><th class="n">${t("Netto")}</th><th class="n">${t("Vorlauf")}</th><th>${t("Status")}</th></tr></thead>
          <tbody>${body || `<tr><td colspan="10" class="empty">${t("Keine Buchungen")}</td></tr>`}</tbody></table></div>
          <div class="row" style="margin-top:8px">${more}<span class="grow"></span></div>`,
        `<button class="btn flat" data-k="csv">${t("CSV exportieren")}</button>`);
    },
  },
};
// v1.17.1: Kommunikationsaufwand je Kanal (Wunsch Betreiber 16.11.2026): Welche Portal-Gäste brauchen generell
// die meiste Kommunikation? Je Kanal, nicht je Gast. Hauptwert = Anliegen je Buchung (Folge von
// Gastnachrichten bis zur Antwort), dazu Gastnachrichten je Buchung, Anteil mit Nachricht, Index (Ø = 100).
// Eigene Nachrichten zählen nicht (automatische Smoobu-Vorlagen sind nicht erkennbar).
function effortHtml(a) {
  if (!a || !a.kanaele?.length) return "";
  const g = a.gesamt;
  const max = Math.max(...a.kanaele.map((k) => k.anliegen_je_buchung || 0), 0.01);
  const rows = a.kanaele.map((k) => {
    const w = ((k.anliegen_je_buchung || 0) / max) * 100;
    const idx = k.index === null || k.index === undefined ? "–" : num(k.index);
    const cls = k.index > 115 ? "bad" : k.index < 85 ? "good" : "";
    return `<tr class="${k.wenig_daten ? "low" : ""}"><td><span class="dot" style="background:${chColor(k.kanal)}"></span> ${esc(chn(k.kanal))}</td>
      <td class="n" style="min-width:140px"><b>${num(k.anliegen_je_buchung, 2)}</b>
        <div class="bar-in" style="width:${w}%;background:${chColor(k.kanal)}"></div></td>
      <td class="n">${num(k.gast_je_buchung, 1)}</td><td class="n">${pct(k.anteil_mit_nachricht, 0)}</td>
      <td class="n"><span class="badge ${cls}">${idx}</span></td><td class="n">${num(k.buchungen)}${k.wenig_daten ? ` <span class="lowtag">${t("wenig Daten")}</span>` : ""}</td></tr>`;
  }).join("");
  const top = a.kanaele.find((k) => !k.wenig_daten && k.index > 100);
  const lead = top ? `<p class="sub" style="margin:4px 0 8px">${t("Am meisten Kommunikation")}: <b>${esc(chn(top.kanal))}</b> –
      ${num(top.anliegen_je_buchung, 1)} ${t("Anliegen je Buchung")} (${t("Ø aller Kanäle")} ${num(g.anliegen_je_buchung, 1)}, Index ${num(top.index)}).</p>` : "";
  return `<div class="kl" style="margin-top:18px">${t("Kommunikationsaufwand je Kanal")}</div>${lead}
    <div class="scroll"><table><thead><tr><th>${t("Kanal")}</th><th class="n">${t("Anliegen je Buchung")}</th><th class="n">${t("Gastnachrichten je Buchung")}</th>
      <th class="n">${t("Buchungen mit Nachricht")}</th><th class="n">Index</th><th class="n">n</th></tr></thead><tbody>${rows}</tbody>
      <tfoot><tr><td>${t("Alle Kanäle")}</td><td class="n">${num(g.anliegen_je_buchung, 2)}</td><td class="n">${num(g.gast_je_buchung, 1)}</td>
        <td class="n">${pct(g.anteil_mit_nachricht, 0)}</td><td class="n">100</td><td class="n">${num(g.buchungen)}</td></tr></tfoot></table></div>
    <div class="legend gloss"><span><b>${t("Anliegen")}</b> = ${t("Gastnachrichten bis zur nächsten Antwort, mehrere am Stück zählen einmal")}</span>
      <span><b>Index</b> = ${t("Anliegen je Buchung im Verhältnis zum Ø aller Kanäle (100 = Durchschnitt, 150 = 1,5-fach)")}</span>
      <span><b>n</b> = ${t("ausgewertete Buchungen mit Anreise im Zeitraum")}</span>
      <span>${t("Nur Nachrichten, die über Smoobu laufen; eigene und automatische Nachrichten zählen nicht; Buchungen ganz ohne Verlauf (bei Smoobu oft vor 2024) fehlen")}</span></div>`;
}
// Baukasten-Modul: Kennzahl × Gruppierung (× Aufteilung) in der gewählten Darstellung
const CUSTOM_MODULE = {
  load: (c, def) => c.q(def.measure, def.view === "kennzahl" ? "gesamt" : def.dimension, c.range, def.split && def.view !== "kennzahl" ? { split: def.split } : {}),
  render: (card, d, res, def) => {
    const cur = d.apt.currency;
    const unit = res.einheit;
    const f = (v, long) => fmtUnit(unit, v, cur, long);
    const sub = `${esc(res.bezeichnung)} × ${t(DIM_LABEL[def.dimension] || def.dimension)}${def.split ? ` × ${t(DIM_LABEL[def.split] || def.split)}` : ""}`;
    const title = esc(def.title || res.bezeichnung);
    if (def.view === "kennzahl") {
      const c = statCell(res);
      return panel(title, sub, `<div class="mtile big${c.n < 5 ? " low" : ""}"><div class="kv">${f(c.wert)}</div><div class="ks">n = ${c.n}${c.n < 5 ? ` · ${t("wenig Daten")}` : ""}</div></div>`);
    }
    const rows = res.zeilen || [];
    const labels = rows.map((z) => (["monat", "woche", "buchungsmonat"].includes(def.dimension) ? binLabel(z.fach) : t(z.fach)));
    const series = (res.serien || []).map((name, i) => ({ name: name === "Gesamt" ? res.bezeichnung : t(name), color: seriesColor(name, def.split, i),
      values: rows.map((z) => z.werte[name]?.wert ?? null), n: rows.map((z) => z.werte[name]?.n ?? 0) }));
    if (!rows.length) return panel(title, sub, `<div class="empty">${t("Keine Daten")}</div>`);
    if (def.view === "tabelle") {
      return panel(title, sub, `<div class="scroll"><table><thead><tr><th>${t(DIM_LABEL[def.dimension])}</th>${series.map((s) => `<th class="n">${esc(s.name)}</th>`).join("")}</tr></thead>
        <tbody>${rows.map((z, i) => `<tr><td>${esc(labels[i])}</td>${series.map((s) => `<td class="n${s.n[i] < 5 ? " muted" : ""}" title="n = ${s.n[i]}">${f(s.values[i])}<span class="sub2">n = ${s.n[i]}</span></td>`).join("")}</tr>`).join("")}</tbody></table></div>`);
    }
    if (def.view === "heatmap") {
      const vals = series.flatMap((s) => s.values).filter((v) => v !== null);
      const lo = Math.min(...vals, 0), hi = Math.max(...vals, 1e-9);
      const cols = `grid-template-columns: minmax(70px, auto) repeat(${series.length}, minmax(56px, 1fr))`;
      let html = `<div></div>${series.map((s) => `<div class="h">${esc(s.name)}</div>`).join("")}`;
      rows.forEach((z, i) => {
        html += `<div class="rl">${esc(labels[i])}</div>`;
        for (const s of series) {
          const v = s.values[i];
          const a = v === null ? 0 : 0.08 + 0.8 * ((v - lo) / (hi - lo || 1));
          html += `<div class="c${s.n[i] < 5 ? " low" : ""}${v === null ? " none" : ""}" style="${v === null ? "" : `background:color-mix(in srgb, var(--sm-accent) ${Math.round(a * 100)}%, var(--sm-surf));${a > 0.55 ? "color:var(--sm-acc-ink);" : ""}`}"
            data-tip="${esc(`${labels[i]} · ${s.name}: ${f(v, true)} · n = ${s.n[i]}`)}">${f(v)}</div>`;
        }
      });
      return panel(title, sub, `<div class="scroll"><div class="mx" style="${cols};min-width:0">${html}</div></div>`);
    }
    return panel(title, sub, `${seriesChart({ labels, series, kind: def.view, fmt: (v) => f(v), W: card.chartW(1, 360) })}
      ${legendOf(series, (s) => (ADDITIVE.has(def.measure) ? f(s.values.reduce((a, v) => a + (v || 0), 0)) : ""))}`);
  },
};

class SmoobuStatsCard extends SmoobuCard {
  // Optionen: period (monat|quartal|saison|jahr), compare (stichtag|vorjahr|vorperiode),
  // matrix_exclude_years (aus dem Ø der Saison-Matrix ausgenommene Jahre, Standard 2020 = Lockdown),
  // matrix_since (erstes Jahr der Matrix, Standard = erste Anreise in den Daten)
  static defaults = { title: "", period: "jahr", compare: "stichtag", matrix_exclude_years: [2020], matrix_since: null, simple_users: [] };
  static initialState = (c) => ({ ptype: c.period, anchor: null, from: null, to: null, compare: c.compare, channels: [],
    raster: "auto", focus: "umsatz", matrix: "auslastung", paceYear: null, edit: false, builder: false, tableAll: false,
    bzMeasure: "naechte", bzBasis: "alle", bzView: "kalender", // Standard „Gebucht im → für“ (Wunsch Betreiber 16.11.2026)
    draft: { title: "", measure: "umsatz", dimension: "monat", split: "", view: "balken" } });
  static css = `
    ha-card { background: none; border: 0; padding: 0; overflow: visible; position: relative; }
    .panel { background: var(--sm-surf); border: 1px solid var(--sm-line); border-radius: var(--sm-r); padding: 18px 20px; min-width: 0; }
    .panel + .panel, .two { margin-top: var(--sm-gap); }
    .ph { display: flex; justify-content: space-between; align-items: baseline; gap: 10px 14px; margin-bottom: 10px; flex-wrap: wrap; }
    .ph h2 { font-size: 1rem; }
    .ph .sub { flex: 1 1 auto; }
    .ph .seg { max-width: 100%; overflow-x: auto; scrollbar-width: none; }
    /* Kopf: Aussage-Satz */
    .lede { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; margin: 4px 2px 14px; }
    .lede h1 { margin: 0; font-size: clamp(24px, 2.6vw, 34px); line-height: 1.12; font-weight: 650; letter-spacing: -.022em; max-width: 30ch; }
    .lede p { margin: 8px 0 0; font-size: 1.02rem; line-height: 1.5; max-width: 72ch; color: var(--sm-ink); }
    .lede p.m { color: var(--sm-muted); font-size: .92rem; margin-top: 4px; }
    .kick { font-size: .8rem; font-weight: 650; letter-spacing: .06em; text-transform: uppercase; color: var(--sm-accent); margin-bottom: 6px; }
    /* Filterleiste: gemeinsam mit Finanzen (FBAR_CSS, v1.18.0b8) */
    ${FBAR_CSS}
    .seg button { white-space: nowrap; }
    /* Modul 1: Kennzahlenleiste */
    .kpis { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); background: var(--sm-surf); border: 1px solid var(--sm-line);
      border-radius: var(--sm-r); overflow: hidden; }
    @media (max-width: 1250px) { .kpis { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
    @media (max-width: 700px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
    .kpi { padding: 12px 16px 10px; border-right: 1px solid var(--sm-line); border-bottom: 1px solid var(--sm-line); margin: 0 -1px -1px 0;
      min-width: 0; cursor: pointer; background: none; text-align: left; font: inherit; color: inherit; border-top: 0; border-left: 0;
      position: relative; }
    .kpi:hover { background: var(--sm-surf2); }
    .kpi[aria-pressed="true"] { background: color-mix(in srgb, var(--sm-accent) 9%, var(--sm-surf)); }
    .kpi[aria-pressed="true"]::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 3px; background: var(--sm-accent); }
    .kpi.low .kv, .kpi.low .spark { opacity: .45; }
    .kl { font-size: .82rem; color: var(--sm-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .kv { font-size: 1.5rem; font-weight: 650; letter-spacing: -.025em; margin: 3px 0 1px; display: flex; align-items: baseline; gap: 6px 8px; flex-wrap: wrap; }
    .ks { font-size: .76rem; color: var(--sm-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .spark { width: 100%; height: 28px; margin-top: 6px; display: block; }
    .spark polyline { fill: none; stroke: var(--sm-accent); stroke-width: 1.7; vector-effect: non-scaling-stroke; stroke-linejoin: round; }
    .spark circle { fill: var(--sm-accent); }
    .spark polyline.cmp { stroke: var(--sm-muted); stroke-opacity: .5; stroke-width: 1.4; stroke-dasharray: 3 2; }
    .lowtag { font-size: .68rem; font-weight: 650; color: var(--sm-warn); }
    .bar-in { height: 5px; border-radius: 3px; background: var(--sm-accent); margin: 3px 0 0 auto; max-width: 100%; }
    tr.low td { opacity: .72; }
    .focus { margin-top: var(--sm-gap); }
    /* Diagramme */
    svg.ch { display: block; width: 100%; height: auto; color: var(--sm-ink); font-family: inherit; overflow: visible; }
    .legend { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: .8rem; margin-top: 8px; color: var(--sm-muted); }
    .legend span { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
    .legend i { width: 12px; height: 10px; border-radius: 3px; display: inline-block; }
    .legend i.ln { height: 0; border-top: 2px dashed currentColor; border-radius: 0; width: 18px; }
    .legend i.ln.solid { border-top-style: solid; border-top-width: 3px; }
    .legend b { color: var(--sm-ink); font-weight: 600; }
    /* Modul 2: Pace + Prognose */
    .two { display: grid; grid-template-columns: minmax(0, 2fr) minmax(260px, 1fr); gap: var(--sm-gap); }
    @media (max-width: 1000px) { .two { grid-template-columns: 1fr; } }
    .two > .panel { margin-top: 0; }
    .fc .big { font-size: 2.1rem; font-weight: 650; letter-spacing: -.03em; margin: 4px 0 0; }
    .fc .range { font-size: .92rem; color: var(--sm-muted); margin-bottom: 12px; }
    .fc .bandbar { position: relative; height: 10px; border-radius: 5px; background: var(--sm-surf2); margin: 6px 0 16px; border: 1px solid var(--sm-line); }
    .fc .bandbar .b { position: absolute; top: -1px; bottom: -1px; border-radius: 5px; background: color-mix(in srgb, var(--sm-accent) 30%, transparent); }
    .fc .bandbar .g { position: absolute; top: -1px; bottom: -1px; left: 0; border-radius: 5px 0 0 5px; background: var(--sm-accent); }
    .fc .bandbar .m { position: absolute; top: -5px; width: 3px; height: 18px; border-radius: 2px; background: var(--sm-ink); transform: translateX(-1px); }
    .fc dl { display: grid; grid-template-columns: 1fr auto; gap: 7px 12px; margin: 0; font-size: .9rem; }
    .fc dt { color: var(--sm-muted); } .fc dd { margin: 0; text-align: right; font-weight: 600; white-space: nowrap; }
    .fc .note { font-size: .78rem; color: var(--sm-muted); margin-top: 12px; line-height: 1.4; }
    .fc.low .big { opacity: .5; }
    /* v1.18.0: Bewertung & Empfehlung */
    .emp-head { display: flex; flex-wrap: wrap; gap: 10px 26px; margin-bottom: 14px; }
    .emp-head .kv.sm { font-size: 1.15rem; }
    .emp-head .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
    .emp-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(270px, 1fr)); gap: var(--sm-gap); }
    .emp-m { border: 1px solid var(--sm-line); border-radius: var(--sm-r); padding: 12px 14px; display: grid; gap: 8px; align-content: start; }
    .emp-m .ks, .emp-r .ks, .emp-foot { white-space: normal; overflow: visible; }
    .emp-m .row { display: flex; gap: 8px; align-items: center; }
    .band { position: relative; height: 10px; border-radius: 5px; background: var(--sm-surf2); border: 1px solid var(--sm-line); margin-top: 4px; }
    .band .b { position: absolute; top: -1px; bottom: -1px; border-radius: 5px; background: color-mix(in srgb, var(--sm-accent) 28%, transparent); }
    .band .md { position: absolute; top: -4px; width: 2px; height: 16px; background: var(--sm-muted); transform: translateX(-1px); }
    .band .pt { position: absolute; top: -4px; width: 14px; height: 14px; border-radius: 50%; background: var(--sm-ink); border: 2px solid var(--sm-surf); transform: translateX(-7px); }
    .band .pt.bad { background: var(--sm-bad); } .band .pt.good { background: var(--sm-good); }
    .emp-r { display: grid; gap: 3px; padding: 9px 11px; border-radius: var(--sm-rs); background: var(--sm-surf2); border-left: 4px solid var(--sm-line); font-size: .88rem; }
    .emp-r.warn { border-left-color: var(--sm-warn); } .emp-r.good { border-left-color: var(--sm-good); }
    .emp-m details summary { cursor: pointer; font-size: .84rem; color: var(--sm-muted); }
    table.mini { width: 100%; font-size: .84rem; margin: 6px 0; } table.mini td.neg { color: var(--sm-bad); font-weight: 600; }
    ul.emp-h { margin: 0; padding-left: 18px; display: grid; gap: 10px; font-size: .9rem; }
    ul.emp-h .chips { margin-top: 5px; } .chip.warn { border-color: var(--sm-warn); }
    .emp-apt { margin: 16px 0 8px; font-size: 1rem; }
    ul.emp-c { margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; font-size: .88rem; }
    ul.emp-c li { display: flex; gap: 8px; align-items: center; } ul.emp-c .sub { display: block; }
    .emp-r .row .btn.sm, ul.emp-h .btn.sm { padding: 5px 12px; font-size: .84rem; }
    /* Modul 3: Saison-Matrix */
    .mx { display: grid; gap: 3px; font-size: .8rem; min-width: 560px; }
    .mx .h { color: var(--sm-muted); font-weight: 600; text-align: center; padding: 2px 0 4px; font-size: .76rem; }
    .mx .rl { color: var(--sm-muted); font-weight: 600; display: flex; align-items: center; font-size: .78rem; }
    .mx .c { border-radius: 6px; padding: 7px 4px; text-align: center; white-space: nowrap; font-variant-numeric: tabular-nums; cursor: default;
      border: 1px solid transparent; }
    /* wenig Daten: Farbe bleibt lesbar (sonst wäre die Matrix bei ~4 Buchungen/Monat fast ganz blass), Zahl kursiv + Punkt */
    .mx .c.low { font-style: italic; position: relative; }
    .mx .c.low::after { content: ""; position: absolute; top: 4px; right: 4px; width: 5px; height: 5px; border-radius: 50%; background: var(--sm-warn); }
    .mx .c.open { border: 1px dashed color-mix(in srgb, var(--sm-ink) 45%, transparent); }
    .mx .c.sel { box-shadow: inset 0 0 0 1.5px var(--sm-ink); }
    .mx .c.none { color: var(--sm-muted); background: var(--sm-surf2); }
    .mx .avg { background: var(--sm-surf2); font-weight: 650; }
    .mx .tot { font-weight: 650; }
    .mx .gap { grid-column: 1 / -1; height: 4px; }
    .scale { display: inline-flex; align-items: center; gap: 6px; }
    .scale i { width: 84px; height: 10px; border-radius: 3px; display: inline-block; }
    /* Tooltip */
    .tt { position: absolute; z-index: 9; pointer-events: none; background: var(--sm-ink); color: var(--sm-surf); font-size: .8rem; line-height: 1.4;
      padding: 7px 10px; border-radius: 8px; white-space: pre-line; max-width: 300px; box-shadow: 0 6px 20px rgba(0,0,0,.22); }
    .tt[hidden] { display: none; }
    .hint { margin-top: var(--sm-gap); text-align: center; font-size: .86rem; color: var(--sm-muted); }
    /* Teilschritte 3/4: Module, Anordnen, Baukasten */
    .mod + .mod { margin-top: var(--sm-gap); }
    .mod > .panel + .panel, .mod > .panel.focus { margin-top: var(--sm-gap); }
    .mbar { display: flex; align-items: center; gap: 8px; padding: 6px 10px; margin-bottom: 6px; border: 1px dashed var(--sm-accent);
      border-radius: var(--sm-rs); background: color-mix(in srgb, var(--sm-accent) 6%, transparent); font-size: .86rem; }
    .mbar.off { opacity: .6; }
    .step:disabled { opacity: .35; cursor: default; }
    .btn.sm { padding: 4px 11px; font-size: .8rem; }
    .btn[aria-pressed="true"] { background: var(--sm-accent); color: var(--sm-acc-ink); }
    .grow { flex: 1 1 auto; }
    .builder .bform { display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: flex-end; }
    .builder label { display: flex; flex-direction: column; gap: 4px; font-size: .76rem; color: var(--sm-muted); font-weight: 600; }
    .split2 { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 20px; align-items: start; }
    .split2.even { grid-template-columns: 1fr 1fr; }
    .quad { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; }
    @media (max-width: 1250px) { .quad { grid-template-columns: 1fr 1fr; } }
    @media (max-width: 1000px) { .split2, .split2.even { grid-template-columns: minmax(0, 1fr); } }
    @media (max-width: 700px) { .quad { grid-template-columns: 1fr; } }
    .hb { display: flex; flex-direction: column; gap: 6px; }
    .hr { display: grid; grid-template-columns: minmax(70px, 34%) 1fr auto; gap: 10px; align-items: center; font-size: .84rem; }
    .hr.low { opacity: .5; }
    .hl { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 6px; }
    .ht { height: 12px; background: var(--sm-surf2); border-radius: 4px; display: flex; overflow: hidden; }
    .ht i { display: block; height: 100%; }
    /* Doppelbalken (Gäste): oben Buchungen, darunter Nächte */
    .ht.dual { height: 14px; flex-direction: column; gap: 2px; background: none; }
    .ht.dual i { height: 6px; border-radius: 3px; background: var(--sm-accent); min-width: 0; }
    .ht.dual i.n { background: color-mix(in srgb, var(--sm-accent) 40%, var(--sm-surf2)); }
    .hv { white-space: nowrap; font-weight: 600; text-align: right; }
    .hv em { font-style: normal; font-weight: 400; color: var(--sm-muted); margin-left: 6px; font-size: .76rem; }
    .hm { display: grid; gap: 2px; font-size: .7rem; min-width: 0; }
    .hm .h { color: var(--sm-muted); text-align: center; font-size: .66rem; }
    .hm .rl { color: var(--sm-muted); font-weight: 600; font-size: .74rem; display: flex; align-items: center; }
    .hc { height: 18px; border-radius: 3px; }
    .hc.none { background: transparent; }
    .mt { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 14px; }
    /* Ehrentafel (v1.18.0b7) */
    .rcol { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
    .rcol .rh { font-weight: 700; font-size: 1rem; }
    .rk { display: grid; grid-template-columns: 34px 1fr auto; gap: 10px; align-items: center; padding: 8px 10px; border-radius: 10px;
      background: var(--sm-surf2); cursor: pointer; }
    .rk:hover { outline: 1px solid var(--sm-line); }
    .rcol.gold .rk { border-left: 4px solid #C9A227; }
    .rcol.buerste .rk { border-left: 4px solid #8B5A2B; }
    .rm { font-size: 1.6rem; text-align: center; }
    .rn { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
    .rq { font-size: .82rem; color: var(--sm-muted); margin-top: 2px; }
    .rp { font-weight: 700; font-size: 1.1rem; text-align: right; white-space: nowrap; }
    .rp em { font-style: normal; font-weight: 400; font-size: .72rem; color: var(--sm-muted); margin-left: 3px; }
    .mtile { background: var(--sm-surf2); border-radius: var(--sm-rs); padding: 10px 14px; }
    .mtile.low .kv { opacity: .5; }
    .mtile .kv { font-size: 1.35rem; }
    .mtile.big .kv { font-size: 2.2rem; }
    .ins { padding-left: 18px; margin: 4px 0; font-size: .86rem; } .ins li { margin: 4px 0; }
    td .sub2 { display: block; font-size: .7rem; color: var(--sm-muted); }
    @media (max-width: 700px) {
      .panel { padding: 14px 14px; }
      .kpi { padding: 10px 12px 8px; }
      .kv { font-size: 1.3rem; }
      .fc .big { font-size: 1.8rem; }
    }
  `;
  // Werkbank oder Einfach (je Gerät; ohne gespeicherte Wahl: Nutzer aus simple_users oder schmale Fenster = Einfach)
  // v1.17.1: simple_users = Liste von HA-Benutzernamen oder -IDs, die ohne eigene Wahl mit „Einfach“ starten
  get mode() {
    const m = lsGet(STATS_MODE_KEY, "");
    if (m === "werkbank" || m === "einfach") return m;
    const u = this._hass?.user || {};
    const su = (this._config.simple_users || []).map((x) => String(x).toLowerCase());
    if (su.includes(String(u.name || "").toLowerCase()) || su.includes(String(u.id || "").toLowerCase())) return "einfach";
    return (window.innerWidth || 1200) < 700 ? "einfach" : "werkbank";
  }
  // v1.17.1: neu zeichnen, wenn eine Kopfzeile mit Wohnungsauswahl erscheint/verschwindet
  _listen() {
    super._listen();
    const onHdr = () => { if (this._data) this.render(); };
    HeaderApts.listeners.add(onHdr);
    const base = this._unsub;
    this._unsub = () => { base?.(); HeaderApts.listeners.delete(onHdr); };
  }
  async load() {
    const info = await this.store.getInfo();
    const apt = await this.apartment();
    const s = this._state;
    const today = info.heute;
    const range = statsRange(s, today);
    const cmp = statsCompare(s, range, today);
    const simple = this.mode === "einfach";
    const base = { ...this.target, mode: "query" };
    if (s.channels.length) base.channels = s.channels;
    const q = (measure, dimension, [a, b], extra = {}) =>
      this.store.ws("smoobu/stats", { ...base, measure, dimension, start: iso(a), end: iso(b), ...extra });
    const days = Math.round((range[1] - range[0]) / 86400000);
    const raster = s.raster === "auto" ? (days <= 100 ? "woche" : "monat") : s.raster;
    const cmpExtra = cmp.asOf ? { as_of: cmp.asOf } : {};
    // Modul 1: je Kennzahl Gesamtwert (Zeitraum + Vergleich) und Verlauf im Raster (Zeitraum + Vergleich)
    const kpiIds = simple ? STATS_EINFACH : STATS_KPIS.map((k) => k.id);
    // v1.18.0b7: Bei „Stichtag Vorjahr“ zusätzlich den Endstand des Vergleichszeitraums laden – aber nur,
    // wenn der Vergleichszeitraum am Stichtag noch nicht vorbei war (sonst sind Stand und Endstand gleich).
    // Grund: Die Bewertung (Pfeil/Farbe) misst gegen den Stand am Stichtag; ohne den Endstand daneben
    // wirkt z. B. RevPAR 49 € „▲ 0,6 %“ falsch, wenn das fertige Vorjahr 50 € hatte (Rückmeldung Betreiber 17.11.2026).
    // Die Bewertung selbst bleibt beim Stichtag: ein laufender Zeitraum gegen ein fertiges Vorjahr sähe immer schlechter aus.
    const withFinal = !!cmp.asOf && cmp.range[1] > addDays(D(cmp.asOf), 1);
    const kpis = Object.fromEntries(await Promise.all(kpiIds.map(async (id) => {
      const [tot, totC, ser, serC, fin] = await Promise.all([q(id, "gesamt", range), q(id, "gesamt", cmp.range, cmpExtra),
        q(id, raster, range), q(id, raster, cmp.range, cmpExtra), withFinal ? q(id, "gesamt", cmp.range) : null]);
      return [id, { tot: statCell(tot), cmp: statCell(totC), fin: fin ? statCell(fin) : null,
        ser: statSeries(ser), serC: statSeries(serC), unit: tot.einheit }];
    })));
    // Modul 2: Pace für das Jahr des Zeitraums (zwischen erstem Vergleichsjahr und nächstem Jahr)
    const ty = D(today).getFullYear();
    const firstYear = Number((apt.erster_tag || today).slice(0, 4));
    const paceYear = s.paceYear || Math.min(Math.max(range[0].getFullYear(), firstYear + 1), ty + 1);
    const pace = await this.store.ws("smoobu/stats", { ...this.target, mode: "pace", year: paceYear,
      ...(s.channels.length ? { channels: s.channels } : {}) });
    // Freie Nächte von heute bis Jahresende (Zieljahr) – smoobu/analytics zieht Sperrzeiten ab
    let free = null;
    const yEnd = new Date(paceYear + 1, 0, 1);
    const fStart = new Date(Math.max(D(today), new Date(paceYear, 0, 1)));
    if (yEnd > fStart) {
      free = await this.store.ws("smoobu/analytics", { ...this.target, start: iso(fStart), end: iso(yEnd), compare: "kein",
        ...(s.channels.length ? { channels: s.channels } : {}) }).catch(() => null);
    }
    // Offene Nächte im gewählten Zeitraum (für den „größten Hebel“ im Aussage-Satz)
    let freePeriod = null;
    if (range[1] > D(today)) {
      const a = new Date(Math.max(D(today), range[0]));
      freePeriod = await this.store.ws("smoobu/analytics", { ...this.target, start: iso(a), end: iso(range[1]), compare: "kein",
        ...(s.channels.length ? { channels: s.channels } : {}) }).catch(() => null);
    }
    // Modul 3: Saison-Matrix Monate × Jahre (nur Werkbank)
    const layout = statsLayout();
    // v1.18.0: „Bewertung & Empfehlung“ auch in „Einfach“ (am Handy die wichtigste Handlungsanweisung)
    const visible = simple ? (layout.hidden.includes("empfehlung") ? [] : ["empfehlung"]) : layout.order.filter((id) => !layout.hidden.includes(id));
    let matrix = null;
    if (visible.includes("saison")) {
      const since = Math.max(Number(this._config.matrix_since) || firstYear, ty - 10);
      const mRange = [new Date(since, 0, 1), new Date(ty + 2, 0, 1)];
      const [months, years] = await Promise.all([q(s.matrix, "monat", mRange), q(s.matrix, "jahr", mRange)]);
      matrix = { since, months, years };
    }
    // Module 4–11 und eigene Baukasten-Module: parallel laden, Fehler je Modul statt für die ganze Karte
    const ctx = { card: this, s, info, apt, today, range, q, target: this.target, channels: s.channels,
      ws: (mode) => this.store.ws("smoobu/stats", { ...this.target, mode, start: iso(range[0]), end: iso(range[1]),
        ...(s.channels.length ? { channels: s.channels } : {}) }) };
    const mods = {};
    await Promise.all(visible.filter((id) => STATS_MODULES[id] || id.startsWith("c_")).map(async (id) => {
      const def = layout.custom.find((c) => c.id === id);
      try { mods[id] = def ? await CUSTOM_MODULE.load(ctx, def) : await STATS_MODULES[id].load(ctx); }
      catch (e) { mods[id] = { __error: e?.message || String(e) }; }
    }));
    const meta = s.builder || layout.custom.length ? await this.store.ws("smoobu/stats", { mode: "meta" }).catch(() => null) : null;
    return { info, apt, today, range, cmp, raster, kpis, pace, paceYear, firstYear, free, freePeriod, matrix, simple, layout, mods, meta };
  }

  // Breite der Diagramme in SVG-Einheiten = tatsächliche Pixelbreite (Handy-Feinschliff): so bleiben
  // Schriftgrößen in allen Breiten gleich lesbar, statt am Handy auf 5 px zu schrumpfen.
  // frac = Anteil an der Kartenbreite in zweispaltigen Bereichen (ab 1000 px Fensterbreite)
  chartW(frac = 1, min = 320) {
    const narrow = (window.innerWidth || 1200) <= 700;
    const w = (this._cw || 1100) - (narrow ? 30 : 44); // Innenabstand der Module (am Handy kleiner)
    const two = (window.innerWidth || 1200) > 1000;
    return Math.round(Math.max(narrow ? Math.min(min, w) : min, Math.min(1200, two ? w * frac : w)));
  }

  // ---- Formatierung je Kennzahl ----
  fmt(id, v, cur, long = false) {
    if (v === null || v === undefined) return "–";
    if (["auslastung", "stornoquote", "kostenquote", "hund_anteil"].includes(id)) return pct(v, long ? 1 : 0);
    if (id === "vorlauf") return `${num(v)} ${t("Tage")}`;
    if (id === "naechte") return `${num(v)} ${t("N.")}`;
    return money(v, cur, long && v < 1000 ? 2 : 0);
  }
  // Veränderung als schlichter Text ohne Bewertungsfarbe (für den Endstand-Hinweis)
  dltText(k, a, b) {
    if (a === null || a === undefined || b === null || b === undefined) return "";
    const v = k.pp ? Math.round((a - b) * 10) / 10 : b ? ((a - b) / Math.abs(b)) * 100 : null;
    if (v === null) return "";
    return `${v > 0 ? "+" : v < 0 ? "−" : "±"}${num(Math.abs(v), 1)}${k.pp ? " PP" : " %"}`;
  }
  dlt(k, a, b) {
    if (a === null || a === undefined || b === null || b === undefined) return "";
    if (k.pp) return delta(Math.round((a - b) * 10) / 10, "pp", !!k.invert);
    if (!b) return "";
    return delta(((a - b) / Math.abs(b)) * 100, "%", !!k.invert);
  }

  // ---- Kopf: Aussage-Satz (Ergebnis + Treiber + größter Hebel) ----
  sentence(d) {
    const cur = d.apt.currency;
    const k = d.kpis;
    const plabel = statsLabel(this._state.ptype, d.range);
    const cmpName = this.cmpName(d);
    const u = k.umsatz?.tot.wert, uc = k.umsatz?.cmp.wert;
    if (!u && !uc) return { h: `${plabel}: ${t("noch keine Umsätze")}`, p: t("Für diesen Zeitraum liegen keine Buchungen vor."), m: "" };
    const ch = uc ? ((u - uc) / uc) * 100 : null;
    const dir = ch === null ? "" : Math.abs(ch) < 1 ? t("auf Vorjahresniveau") : ch > 0 ? `${num(ch, 0)} % ${LANG === "de" ? "über" : "above"}` : `${num(-ch, 0)} % ${LANG === "de" ? "unter" : "below"}`;
    const h = `${plabel}: ${money(u, cur)} ${t("Umsatz")}${dir ? `, ${dir}${Math.abs(ch) < 1 ? "" : ` ${cmpName}`}` : ""}.`;
    const parts = [];
    // Treiber: RevPAR = ADR × Auslastung → welcher Faktor hat sich relativ stärker verändert?
    const occ = k.auslastung?.tot.wert, occC = k.auslastung?.cmp.wert, adr = k.adr?.tot.wert, adrC = k.adr?.cmp.wert;
    if (occ !== null && occC && adr && adrC) {
      const rOcc = occ / occC - 1, rAdr = adr / adrC - 1;
      const main = Math.abs(rOcc) >= Math.abs(rAdr)
        ? `${t("Auslastung")} ${pct(occ, 0)} (${t("Vergleich")} ${pct(occC, 0)})`
        : `${t("Preis je Nacht")} ${money(adr, cur)} (${t("Vergleich")} ${money(adrC, cur)})`;
      const other = Math.abs(rOcc) >= Math.abs(rAdr)
        ? `${t("Preis je Nacht")} ${rAdr >= 0 ? "+" : "−"}${num(Math.abs(rAdr) * 100, 0)} %`
        : `${t("Auslastung")} ${occ - occC >= 0 ? "+" : "−"}${num(Math.abs(occ - occC), 0)} PP`;
      parts.push(`${t("Treiber")}: <b>${main}</b>; ${other}.`);
    }
    // Größter Hebel in Euro: verlorene Auslastung × ADR, verlorener Preis × Nächte, offene Nächte im Zeitraum
    const levers = [];
    const rev = k.revpar?.tot.wert;
    const avail = rev ? u / rev : null;
    if (occ !== null && occC && occ < occC && avail && adr) levers.push([((occC - occ) / 100) * avail * adr,
      `${t("Auslastung auf Vergleichsniveau")} ≈ +${money(((occC - occ) / 100) * avail * adr, cur)}`]);
    if (adr && adrC && adr < adrC) levers.push([(adrC - adr) * (u / adr),
      `${t("Preis je Nacht auf Vergleichsniveau")} ≈ +${money((adrC - adr) * (u / adr), cur)}`]);
    const fp = d.freePeriod;
    if (fp && fp.frei_kommend > 0 && fp.frei_potenzial_netto > 0) levers.push([fp.frei_potenzial_netto,
      `${num(fp.frei_kommend)} ${t("freie Nächte im Zeitraum")} ≈ ${money(fp.frei_potenzial_netto, cur)} ${t("netto")}`]);
    if (levers.length) parts.push(`${t("Größter Hebel")}: <b>${levers.sort((a, b) => b[0] - a[0])[0][1]}</b>.`);
    const n = k.umsatz?.tot.n || 0;
    return { h, p: parts.join(" "), m: `${t("Basis")}: ${num(n)} ${t("Buchungen")}${n < 5 ? ` · ${t("wenig Daten")}` : ""}` };
  }
  cmpName(d) {
    const s = this._state;
    if (s.compare === "stichtag") return `${t("Buchungsstand Vorjahr")} (${fdate(d.cmp.asOf)})`;
    if (s.compare === "vorjahr") return `${t("Vorjahr")} ${statsLabel(s.ptype, d.cmp.range)}`;
    return `${t("Vorperiode")} ${statsLabel(s.ptype, d.cmp.range)}`;
  }

  // ---- Filterleiste (v1.18.0b8: gemeinsam mit Finanzen, filterBarHtml) ----
  filterBar(d) {
    const s = this._state;
    const tools = `<span class="grow"></span><button class="btn flat sm" data-k="builder" aria-pressed="${s.builder}">＋ ${t("Modul")}</button>
      <button class="btn flat sm" data-k="edit" aria-pressed="${s.edit}">${s.edit ? t("Fertig") : t("Anordnen")}</button>`;
    return filterBarHtml(this, d, { simple: d.simple, tools });
  }

  // ---- Modul 1: Kennzahlenleiste ----
  kpiBar(d) {
    const cur = d.apt.currency;
    const list = STATS_KPIS.filter((k) => d.kpis[k.id]);
    return `<section class="kpis" aria-label="${t("Kennzahlen")}">${list.map((k) => {
      const x = d.kpis[k.id];
      const v = x.tot.wert, c = x.cmp.wert;
      const n = x.tot.n || 0;
      const low = n < 5;
      // Endstand des Vergleichszeitraums (nur „Stichtag Vorjahr“ mit damals noch offenem Zeitraum, s. Loader)
      const fin = x.fin ? x.fin.wert : null;
      const asOf = d.cmp.asOf ? fdate(d.cmp.asOf) : "";
      const tip = `${t(k.label)}: ${this.fmt(k.id, v, cur, true)} · n = ${n}\n${t("Vergleich")}${asOf ? ` (${t("Stand")} ${asOf})` : ""}: ${this.fmt(k.id, c, cur, true)} · n = ${x.cmp.n || 0}`
        + (x.fin ? `\n${t("Endstand Vergleichszeitraum")}: ${this.fmt(k.id, fin, cur, true)} · n = ${x.fin.n || 0}`
          + `\n${t("Pfeil und Farbe vergleichen mit dem Stand am Stichtag, nicht mit dem Endstand.")}` : "")
        + `\n${t(k.hint)}`;
      return `<button class="kpi${low ? " low" : ""}" data-focus="${k.id}" aria-pressed="${this._state.focus === k.id}" data-tip="${esc(tip)}">
        <div class="kl">${esc(t(k.label))}</div><div class="kv">${this.fmt(k.id, v, cur)}${this.dlt(k, v, c)}</div>
        <div class="ks">${t("Vgl.")} ${this.fmt(k.id, c, cur)}${asOf && x.fin ? ` (${t("Stand")} ${asOf})` : ""} · n = ${num(n)}${low ? ` · <span class="lowtag">${t("wenig Daten")}</span>` : ""}</div>
        ${x.fin ? `<div class="ks">${t("Endstand")} ${this.fmt(k.id, fin, cur)}${fin !== null && c !== null && this.fmt(k.id, fin, cur) !== this.fmt(k.id, c, cur) ? ` (${this.dltText(k, v, fin)})` : ""}</div>` : ""}
        ${k.id === "auslastung" && x.tot.gesperrt ? `<div class="ks">${num(x.tot.verfuegbar)} ${t("verfügbar")} · ${num(x.tot.gesperrt)} ${t("gesperrt")}</div>` : ""}
        ${sparkline(x.ser.map((p) => p.wert), x.serC.map((p) => p.wert))}</button>`;
    }).join("")}</section>${gloss([...list.map((k) => k.label).filter((l) => GLOSSARY[l]), ...(list.some((k) => k.pp) ? ["PP"] : []), "Vgl.", "n"])}`;
  }
  // Großer Verlauf der Fokus-Kennzahl: Balken = Zeitraum, gestrichelte Linie = Vergleich (gleiche Achse)
  focusChart(d) {
    const s = this._state;
    const k = STATS_KPIS.find((x) => x.id === s.focus) || STATS_KPIS[0];
    const x = d.kpis[k.id];
    if (!x) return "";
    const cur = d.apt.currency;
    const cur_ = x.ser, cmp = x.serC;
    const n = Math.max(cur_.length, 1);
    const W = this.chartW(1), H = 230, L = 58, R = 10, T = 12, B = 26;
    const vals = [...cur_.map((p) => p.wert), ...cmp.map((p) => p.wert)].filter((v) => v !== null && v !== undefined);
    const max = niceMax(Math.max(0, ...vals) * 1.08);
    const y = (v) => T + (H - T - B) * (1 - (v || 0) / max);
    const bw = (W - L - R) / n;
    let svg = "";
    for (let g = 0; g <= 4; g++) {
      const v = (max / 4) * g;
      svg += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" stroke-opacity=".1"/>
        <text x="${L - 6}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="currentColor" fill-opacity=".6">${this.fmt(k.id, v, cur)}</text>`;
    }
    const step = Math.ceil(n / Math.max(4, Math.floor(W / 60)));
    cur_.forEach((p, i) => {
      const x0 = L + i * bw;
      const low = (p.n || 0) < 5;
      if (p.wert) svg += `<rect x="${x0 + bw * 0.18}" y="${y(p.wert)}" width="${bw * 0.64}" height="${Math.max(y(0) - y(p.wert), 0)}" rx="3"
        fill="var(--sm-accent)" fill-opacity="${low ? 0.38 : 0.9}"/>`;
      if (i % step === 0) svg += `<text x="${x0 + bw / 2}" y="${H - 8}" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity=".7">${esc(binLabel(p.fach))}</text>`;
      const c = cmp[i];
      const tip = `${binLabel(p.fach, true)}: ${this.fmt(k.id, p.wert, cur, true)} · n = ${p.n || 0}${low ? ` (${t("wenig Daten")})` : ""}` +
        (c ? `\n${t("Vergleich")} ${binLabel(c.fach, true)}: ${this.fmt(k.id, c.wert, cur, true)} · n = ${c.n || 0}` : "");
      svg += `<rect data-tip="${esc(tip)}" x="${x0}" y="${T}" width="${bw}" height="${H - T - B}" fill="transparent"/>`;
    });
    const pts = cmp.slice(0, n).map((p, i) => (p.wert === null || p.wert === undefined ? null : `${L + i * bw + bw / 2},${y(p.wert)}`)).filter(Boolean);
    if (pts.length > 1) svg += `<polyline points="${pts.join(" ")}" fill="none" stroke="currentColor" stroke-opacity=".55" stroke-width="2" stroke-dasharray="5 4" pointer-events="none"/>`;
    svg += `<line x1="${L}" x2="${W - R}" y1="${y(0)}" y2="${y(0)}" stroke="currentColor" stroke-opacity=".3"/>`;
    const rLabel = d.raster === "woche" ? t("je Kalenderwoche") : t("je Monat");
    return `<div class="panel focus"><div class="ph"><h2>${t("Verlauf")}: ${esc(t(k.label))}</h2><span class="sub">${rLabel} · ${t("Kennzahl oben anklicken zum Wechseln")}</span></div>
      <svg class="ch" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(t(k.label))}">${svg}</svg>
      <div class="legend"><span><i style="background:var(--sm-accent)"></i><b>${esc(statsLabel(this._state.ptype, d.range))}</b> ${this.fmt(k.id, x.tot.wert, cur)}</span>
        <span><i class="ln"></i>${esc(this.cmpName(d))} ${this.fmt(k.id, x.cmp.wert, cur)}</span>
        <span><i style="background:var(--sm-accent);opacity:.38"></i>${t("blass = weniger als 5 Buchungen")}</span></div>
      ${GLOSSARY[k.label] ? gloss([k.label]) : ""}</div>`;
  }

  // ---- Modul 2: Buchungstempo (Pace) ----
  paceChart(d) {
    const p = d.pace;
    const cur = d.apt.currency;
    const target = String(p.zieljahr);
    const years = Object.keys(p.kurven).sort().reverse(); // Zieljahr zuerst
    const W = this.chartW(0.64, 340), H = 290, L = 62, R = 74, T = 14, B = 34;
    const all = years.flatMap((y) => p.kurven[y].map((q) => q.wert));
    if (p.prognose) all.push(p.prognose.oben);
    const max = niceMax(Math.max(1, ...all) * 1.05);
    const x = (i) => L + (i / 23) * (W - L - R);
    const y = (v) => T + (H - T - B) * (1 - v / max);
    let svg = "";
    for (let g = 0; g <= 4; g++) {
      const v = (max / 4) * g;
      svg += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" stroke-opacity=".1"/>
        <text x="${L - 6}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="currentColor" fill-opacity=".6">${money(v, cur)}</text>`;
    }
    // x-Achse: Buchungsdatum, Jan Vorjahr … Dez Zieljahr; Jahreswechsel markiert
    for (let i = 0; i < 24; i += W < 560 ? 4 : 2) svg += `<text x="${x(i)}" y="${H - 16}" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity=".65">${t(MONTHS_SHORT[i % 12])}</text>`;
    svg += `<line x1="${x(11.5)}" x2="${x(11.5)}" y1="${T}" y2="${H - B}" stroke="currentColor" stroke-opacity=".25" stroke-dasharray="2 3"/>
      <text x="${x(5.5)}" y="${H - 2}" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor" fill-opacity=".55">${W < 560 ? t("Vorjahr") : t("gebucht im Vorjahr")}</text>
      <text x="${x(17.5)}" y="${H - 2}" text-anchor="middle" font-size="11" font-weight="600" fill="currentColor" fill-opacity=".55">${W < 560 ? t("Aufenthaltsjahr") : t("gebucht im Aufenthaltsjahr")}</text>`;
    // Linien: Zieljahr kräftig (Akzent), Vorjahr mittel, ältere Jahre blasser
    const style = (yr, idx) => (yr === target ? { c: "var(--sm-accent)", w: 3, o: 1, dash: "" }
      : idx === 1 ? { c: "currentColor", w: 2, o: 0.6, dash: "" } : { c: "currentColor", w: 1.4, o: Math.max(0.14, 0.38 - (idx - 2) * 0.06), dash: "4 3" });
    const labels = [];
    [...years].reverse().forEach((yr) => {
      const idx = years.indexOf(yr);
      const st = style(yr, idx);
      const pts = p.kurven[yr];
      if (!pts.length) return;
      svg += `<polyline points="${pts.map((q) => `${x(q.index)},${y(q.wert)}`).join(" ")}" fill="none" stroke="${st.c}" stroke-opacity="${st.o}"
        stroke-width="${st.w}" stroke-dasharray="${st.dash}" stroke-linejoin="round" pointer-events="none"/>`;
      const last = pts[pts.length - 1];
      if (idx <= 1) labels.push({ yr, x: x(last.index), y: y(last.wert), c: st.c, o: st.o, heute: !!last.heute, wert: last.wert });
    });
    // Prognose-Spanne am Jahresende des Zieljahres
    if (p.prognose) {
      const f = p.prognose;
      const px = x(23);
      svg += `<line x1="${px}" x2="${px}" y1="${y(f.oben)}" y2="${y(f.unten)}" stroke="var(--sm-accent)" stroke-width="10" stroke-opacity=".25" stroke-linecap="round"/>
        <circle cx="${px}" cy="${y(f.wahrscheinlich)}" r="5" fill="var(--sm-surf)" stroke="var(--sm-accent)" stroke-width="2.5"/>`;
      const today = p.kurven[target]?.at(-1);
      if (today && today.heute) svg += `<line x1="${x(today.index)}" x2="${px}" y1="${y(today.wert)}" y2="${y(f.wahrscheinlich)}" stroke="var(--sm-accent)"
        stroke-width="2" stroke-dasharray="3 3" stroke-opacity=".8"/>`;
      labels.push({ yr: t("Prognose"), x: px, y: y(f.wahrscheinlich), c: "var(--sm-accent)", o: 1, prog: true, wert: f.wahrscheinlich });
    }
    // „heute“-Markierung
    const tp = p.kurven[target]?.find((q) => q.heute);
    if (tp) svg += `<circle cx="${x(tp.index)}" cy="${y(tp.wert)}" r="4.5" fill="var(--sm-accent)"/>
      <text x="${x(tp.index)}" y="${y(tp.wert) + 18}" text-anchor="middle" font-size="11" font-weight="650" fill="var(--sm-accent)">${t("heute")}</text>`;
    // Direktbeschriftung rechts (Zieljahr, Vorjahr, Prognose), gegen Überlappung gestaffelt
    labels.sort((a, b) => a.y - b.y);
    let lastY = -99;
    for (const l of labels) {
      const ly = Math.max(l.y, lastY + 26);
      lastY = ly;
      svg += `<text x="${W - R + 8}" y="${ly}" font-size="11.5" font-weight="650" fill="${l.c}" fill-opacity="${Math.max(l.o, 0.75)}">${esc(l.yr)}</text>
        <text x="${W - R + 8}" y="${ly + 12}" font-size="10.5" fill="currentColor" fill-opacity=".6">${money(l.wert, cur)}</text>`;
    }
    // Hover je Monat: Stand aller Jahre
    for (let i = 0; i < 24; i++) {
      const rows = years.map((yr) => {
        const q = p.kurven[yr].find((z) => z.index === i);
        return q ? `${yr}: ${money(q.wert, cur)}${q.heute ? ` (${t("heute")})` : ""}` : null;
      }).filter(Boolean);
      const tip = `${t("Buchungsstand Ende")} ${t(MONTHS_SHORT[i % 12])} ${t("des")} ${i < 12 ? t("Vorjahres") : t("Aufenthaltsjahres")}\n${rows.join("\n")}`;
      svg += `<rect data-tip="${esc(tip)}" x="${x(i) - (W - L - R) / 46}" y="${T}" width="${(W - L - R) / 23}" height="${H - T - B}" fill="transparent"/>`;
    }
    const older = years.slice(2);
    return `<div class="panel"><div class="ph"><h2>${t("Buchungstempo")} ${esc(target)}</h2>
        <span class="sub">${t("Umsatz brutto der Nächte im Jahr nach Buchungsdatum, gleicher Tag wie in den Vorjahren")}</span>
        ${this.paceYearSel(d)}</div>
      <svg class="ch" viewBox="0 0 ${W} ${H}" role="img" aria-label="${t("Buchungstempo")}">${svg}</svg>
      <div class="legend"><span><i class="ln solid" style="color:var(--sm-accent)"></i><b>${esc(target)}</b></span>
        ${years[1] ? `<span><i class="ln solid" style="opacity:.6"></i>${esc(years[1])}</span>` : ""}
        ${older.length ? `<span><i class="ln" style="opacity:.4"></i>${esc(older.join(", "))}</span>` : ""}
        ${p.prognose ? `<span><i style="background:var(--sm-accent);opacity:.3"></i>${t("Prognose-Spanne")} P10–P90</span>` : ""}</div>
      ${gloss(p.prognose ? ["Pace", "P10–P90"] : ["Pace"])}</div>`;
  }
  paceYearSel(d) {
    const ty = D(d.today).getFullYear();
    const ys = [];
    for (let y = ty + 1; y >= Math.max(d.firstYear + 1, ty - 8); y--) ys.push(y);
    return `<select data-k="paceyear" aria-label="${t("Zieljahr")}">${ys.map((y) => `<option value="${y}" ${y === d.paceYear ? "selected" : ""}>${y}</option>`).join("")}</select>`;
  }
  forecastCard(d) {
    const p = d.pace;
    const cur = d.apt.currency;
    const f = p.prognose;
    const fr = d.free;
    const freeRow = fr ? `<dt>${t("Freie Nächte bis 31.12.")}</dt><dd>${num(fr.frei_kommend ?? fr.frei_naechte)}</dd>` : "";
    const vj = p.vorjahr_stichtag !== null && p.vorjahr_stichtag !== undefined
      ? `<dt>${t("Vorjahr am gleichen Tag")}</dt><dd>${money(p.vorjahr_stichtag, cur)} ${delta(p.veraenderung_prozent)}</dd>` : "";
    if (!f) {
      const last = p.kurven[String(p.zieljahr)]?.at(-1);
      return `<div class="panel fc"><div class="ph"><h2>${t("Prognose")} ${p.zieljahr}</h2></div>
        <div class="big">${money(last?.wert, cur)}</div><div class="range">${t("Endstand bzw. Buchungsstand – für eine Prognose fehlen Vorjahre")}</div>
        <dl>${vj}${freeRow}</dl></div>`;
    }
    const low = f.jahre_basis < 5;
    const span = Math.max(f.oben, 1);
    const pos = (v) => `${Math.min(100, Math.max(0, (v / span) * 100)).toFixed(1)}%`;
    return `<div class="panel fc${low ? " low" : ""}"><div class="ph"><h2>${t("Prognose")} ${p.zieljahr}</h2><span class="sub">${t("Umsatz brutto")}</span></div>
      <div class="kl">${t("wahrscheinlich")}</div>
      <div class="big" data-tip="${esc(`${t("Median der Nachbuchung aus")} ${f.jahre_basis} ${t("Vorjahren")}`)}">${money(f.wahrscheinlich, cur)}</div>
      <div class="range">${f.oben > f.unten ? `${t("Spanne")} ${money(f.unten, cur)} – ${money(f.oben, cur)}` : t("Keine Spanne – zu wenige Vorjahre")}</div>
      <div class="bandbar" data-tip="${esc(`${t("gebucht")} ${money(f.gebucht, cur)}\n${t("Spanne")} ${money(f.unten, cur)} – ${money(f.oben, cur)}\n${t("wahrscheinlich")} ${money(f.wahrscheinlich, cur)}`)}">
        <div class="b" style="left:${pos(f.unten)};width:calc(${pos(f.oben)} - ${pos(f.unten)})"></div>
        <div class="g" style="width:${pos(f.gebucht)}"></div><div class="m" style="left:${pos(f.wahrscheinlich)}"></div></div>
      <dl><dt>${t("Gebucht (Stand heute)")}</dt><dd>${money(f.gebucht, cur)}</dd>
        <dt>${t("Erwartete Nachbuchung")}</dt><dd>+${money(f.erwartete_nachbuchung, cur)}</dd>
        ${vj}${freeRow}
        <dt>${t("Basis")}</dt><dd>${f.jahre_basis} ${t(f.jahre_basis === 1 ? "Vorjahr" : "Vorjahre")}${low ? ` · <span class="lowtag">${t("wenig Daten")}</span>` : ""}</dd></dl>
      <div class="note">${t("Spanne = 10.–90. Perzentil der Nachbuchung (Endstand − Stand am gleichen Tag) der Vorjahre, kein Konfidenzintervall.")}</div></div>`;
  }

  // ---- Modul 3: Saison-Matrix ----
  seasonMatrix(d) {
    const m = d.matrix;
    if (!m) return "";
    const s = this._state;
    const cur = d.apt.currency;
    const id = s.matrix;
    const today = D(d.today);
    const ty = today.getFullYear();
    const cells = new Map(statSeries(m.months).map((c) => [c.fach, c]));
    const yearCells = new Map(statSeries(m.years).map((c) => [c.fach, c]));
    // Jahre: ab erstem Jahr bis laufendes Jahr, nächstes Jahr nur mit Buchungen
    const years = [];
    for (let y = m.since; y <= ty + 1; y++) {
      if (y === ty + 1 && !(yearCells.get(String(y))?.n > 0)) continue;
      years.push(y);
    }
    // Aus dem Ø ausgenommene Jahre (Standard 2020 = Lockdown); Hinweis nur, wenn das Jahr in der Matrix steht
    const exclude = new Set((this._config.matrix_exclude_years || []).map(Number).filter((y) => years.includes(y)));
    const exShown = [...exclude];
    const done = (y, mo) => new Date(y, mo, 1) <= today; // Monat abgeschlossen (Monatsende vor heute)
    const vals = [...cells.values()].filter((c) => Number(c.fach.slice(0, 4)) >= m.since && c.wert !== null).map((c) => c.wert);
    const lo = Math.min(...vals, 0), hi = Math.max(...vals, 1);
    const [selA, selB] = d.range;
    const shade = (v) => {
      if (v === null || v === undefined) return "";
      const a = 0.08 + 0.8 * ((v - lo) / (hi - lo || 1));
      return `background:color-mix(in srgb, var(--sm-accent) ${Math.round(a * 100)}%, var(--sm-surf));${a > 0.55 ? "color:var(--sm-acc-ink);" : ""}`;
    };
    const cell = (c, y, mo) => {
      const key = `${y}-${String(mo + 1).padStart(2, "0")}`;
      const open = !done(y, mo + 1);
      const inSel = new Date(y, mo, 1) >= selA && new Date(y, mo, 1) < selB;
      if (!c || (c.wert === null && !c.n)) return `<div class="c none${inSel ? " sel" : ""}" data-tip="${esc(`${binLabel(key, true)}: ${t("keine Daten")}`)}">–</div>`;
      const low = (c.n || 0) < 5;
      const tip = `${binLabel(key, true)}: ${this.fmt(id, c.wert, cur, true)} · n = ${c.n || 0}${low ? ` (${t("wenig Daten")})` : ""}${open ? `\n${t("noch nicht abgeschlossen – Buchungsstand heute")}` : ""}`;
      return `<div class="c${low ? " low" : ""}${open ? " open" : ""}${inSel ? " sel" : ""}" style="${shade(c.wert)}" data-tip="${esc(tip)}">${this.fmt(id, c.wert, cur)}</div>`;
    };
    // v1.17.1: Ø ganz links, danach die Jahre absteigend (aktuelles/kommendes Jahr vorne) – Wunsch Betreiber 16.11.2026;
    // am Handy ist so das Wichtigste ohne Wischen sichtbar
    const yearsDesc = [...years].reverse();
    const cols = `grid-template-columns: 44px minmax(62px, 1fr) repeat(${years.length}, minmax(52px, 1fr))`;
    let html = `<div></div><div class="h">Ø${exclude.size ? "*" : ""}</div>${yearsDesc.map((y) => `<div class="h">${y}${exclude.has(y) ? "*" : ""}</div>`).join("")}`;
    for (let mo = 0; mo < 12; mo++) {
      html += `<div class="rl">${t(MONTHS_SHORT[mo])}</div>`;
      const avgVals = [];
      let row = "";
      for (const y of yearsDesc) {
        const c = cells.get(`${y}-${String(mo + 1).padStart(2, "0")}`);
        row += cell(c, y, mo);
        if (!exclude.has(y) && done(y, mo + 1) && c && c.wert !== null) avgVals.push(c.wert);
      }
      const avg = avgVals.length ? avgVals.reduce((a, b) => a + b, 0) / avgVals.length : null;
      html += `<div class="c avg" data-tip="${esc(`Ø ${t(MONTHS_SHORT[mo])}: ${this.fmt(id, avg, cur, true)}\n${t("aus")} ${avgVals.length} ${t("abgeschlossenen Jahren")}${exclude.size ? ` (${t("ohne")} ${[...exclude].join(", ")})` : ""}`)}">${this.fmt(id, avg, cur)}</div>${row}`;
    }
    // Jahreszeile (eigene Abfrage je Jahr: Auslastung/ADR sind keine Summe der Monate)
    html += `<div class="gap"></div><div class="rl">${t("Jahr")}</div>`;
    const yAvg = [];
    let yRow = "";
    for (const y of yearsDesc) {
      const c = yearCells.get(String(y));
      const open = y >= ty;
      if (!exclude.has(y) && !open && c?.wert !== null && c?.wert !== undefined) yAvg.push(c.wert);
      yRow += `<div class="c tot${open ? " open" : ""}${(c?.n || 0) < 5 ? " low" : ""}" data-tip="${esc(`${y}: ${this.fmt(id, c?.wert, cur, true)} · n = ${c?.n || 0}${open ? `\n${t("noch nicht abgeschlossen – Buchungsstand heute")}` : ""}`)}">${this.fmt(id, c?.wert, cur)}</div>`;
    }
    html += `<div class="c avg tot">${this.fmt(id, yAvg.length ? yAvg.reduce((a, b) => a + b, 0) / yAvg.length : null, cur)}</div>${yRow}`;
    const seg = `<div class="seg" role="group" aria-label="${t("Kennzahl")}">${MATRIX_MEASURES.map(([k, l]) =>
      `<button data-matrix="${k}" aria-pressed="${id === k}">${t(l)}</button>`).join("")}</div>`;
    return `<div class="panel"><div class="ph"><h2>${t("Saison-Matrix")}</h2><span class="sub">${t("Monate × Jahre seit")} ${m.since}</span>${seg}</div>
      <div class="scroll"><div class="mx" style="${cols}">${html}</div></div>
      <div class="legend"><span class="scale"><i style="background:linear-gradient(90deg, color-mix(in srgb, var(--sm-accent) 8%, var(--sm-surf)), var(--sm-accent))"></i>
          ${this.fmt(id, lo, cur)} – ${this.fmt(id, hi, cur)}</span>
        <span><i style="border:1px dashed currentColor;background:none"></i>${t("noch nicht abgeschlossen")}</span>
        <span><i style="box-shadow:inset 0 0 0 2px var(--sm-ink);background:none"></i>${t("gewählter Zeitraum")}</span>
        <span><i style="background:var(--sm-warn);width:6px;height:6px;border-radius:50%"></i><em>${t("kursiv")}</em> = ${t("weniger als 5 Buchungen")}</span>
        <span>${exShown.length ? `* Ø ${t("ohne")} ${exShown.join(", ")}, ` : "Ø "}${t("nur abgeschlossene Monate")}</span></div>
      ${gloss(["ADR", "RevPAR", "Ø"])}</div>`; /* immer alle: die Umschalter oben nennen ADR/RevPAR auch, wenn sie nicht gewählt sind */
  }

  body(d) {
    this._cw = this.getBoundingClientRect().width || this._cw || 1100;
    const s = this._state;
    const simple = d.simple;
    const sen = this.sentence(d);
    const modeSeg = `<div class="seg" role="group" aria-label="${t("Ansicht")}">${[["werkbank", "Werkbank"], ["einfach", "Einfach"]].map(([k, l]) =>
      `<button data-mode="${k}" aria-pressed="${d.simple === (k === "einfach")}">${t(l)}</button>`).join("")}</div>`;
    const head = `<div class="lede"><div><div class="kick">${esc(this._config.title || t("Statistik"))}${this.multi ? ` · ${t("Alle Wohnungen")}` : ""}</div>
      <h1>${esc(sen.h)}</h1>${sen.p ? `<p>${sen.p}</p>` : ""}<p class="m">${esc(sen.m)} · ${t("Vergleich")}: ${esc(this.cmpName(d))}</p></div>${modeSeg}</div>`;
    const tt = `<div class="tt" hidden></div>`;
    if (simple) {
      return `${head}${this.filterBar(d)}${this.kpiBar(d)}${d.mods.empfehlung ? `<section class="mod">${this.module("empfehlung", d)}</section>` : ""}<div class="two">${this.forecastCard(d)}</div>
        <div class="hint">${t("Buchungstempo, Verlauf und Saison-Matrix:")} <button class="lnk" data-mode="werkbank">${t("Werkbank öffnen")}</button></div>${tt}`;
    }
    const L = d.layout;
    const parts = L.order.filter((id) => s.edit || !L.hidden.includes(id)).map((id, i, arr) => {
      const def = L.custom.find((c) => c.id === id);
      const hidden = L.hidden.includes(id);
      const name = def ? def.title || t("Eigenes Modul") : t(STATS_TITLES[id]);
      const bar = s.edit ? `<div class="mbar${hidden ? " off" : ""}"><b>${esc(name)}</b>${hidden ? `<span class="sub">${t("ausgeblendet")}</span>` : ""}<span class="grow"></span>
        <button class="step" data-mv="${id}" data-dir="-1" ${i === 0 ? "disabled" : ""} aria-label="${t("nach oben")}">↑</button>
        <button class="step" data-mv="${id}" data-dir="1" ${i === arr.length - 1 ? "disabled" : ""} aria-label="${t("nach unten")}">↓</button>
        <button class="btn flat sm" data-hide="${id}">${hidden ? t("Einblenden") : t("Ausblenden")}</button>
        ${def ? `<button class="btn flat sm" data-del="${id}">${t("Löschen")}</button>` : ""}</div>` : "";
      if (hidden) return `<section class="mod">${bar}</section>`;
      return `<section class="mod">${bar}${this.module(id, d, def)}</section>`;
    }).join("");
    return `${head}${this.filterBar(d)}${s.builder ? this.builder(d) : ""}${parts}${tt}`;
  }
  // Ein Modul der Werkbank (1–3 eingebaut, 4–11 aus STATS_MODULES, sonst Baukasten)
  module(id, d, def) {
    if (id === "kennzahlen") return `${this.kpiBar(d)}${this.focusChart(d)}`;
    if (id === "tempo") return `<div class="two">${this.paceChart(d)}${this.forecastCard(d)}</div>`;
    if (id === "saison") return this.seasonMatrix(d);
    const data = d.mods[id];
    if (!data) return "";
    if (data.__error) return panel(esc(def?.title || t(STATS_TITLES[id] || "Modul")), "", `<div class="err">${t("Fehler")}: ${esc(data.__error)}</div>`);
    try { return def ? CUSTOM_MODULE.render(this, d, data, def) : STATS_MODULES[id].render(this, d, data); }
    catch (e) { return panel(esc(t(STATS_TITLES[id] || "Modul")), "", `<div class="err">${t("Fehler")}: ${esc(e.message)}</div>`); }
  }
  // Baukasten: neues Modul zusammenstellen (Kennzahl × Gruppierung × Aufteilung × Darstellung)
  builder(d) {
    const s = this._state;
    const dr = s.draft;
    const ms = d.meta?.kennzahlen || [];
    const dims = (d.meta?.dimensionen || Object.keys(DIM_LABEL)).filter((x) => x !== "gesamt");
    const opt = (list, val) => list.map(([k, l]) => `<option value="${k}" ${k === val ? "selected" : ""}>${esc(l)}</option>`).join("");
    const hidden = d.layout.hidden;
    return `<div class="panel builder"><div class="ph"><h2>＋ ${t("Eigenes Modul")}</h2><span class="sub">${t("Wird auf diesem Gerät gespeichert und erscheint unten in der Werkbank")}</span></div>
      <div class="bform">
        <label>${t("Kennzahl")}<select data-b="measure">${opt(ms.map((m) => [m.id, m.name]), dr.measure)}</select></label>
        <label>${t("Gruppierung")}<select data-b="dimension">${opt(dims.map((k) => [k, t(DIM_LABEL[k] || k)]), dr.dimension)}</select></label>
        <label>${t("Aufteilung")}<select data-b="split"><option value="">${t("keine")}</option>${opt(dims.filter((k) => k !== dr.dimension).map((k) => [k, t(DIM_LABEL[k] || k)]), dr.split)}</select></label>
        <label>${t("Darstellung")}<div class="seg">${VIEWS.map(([k, l]) => `<button data-bview="${k}" aria-pressed="${dr.view === k}">${t(l)}</button>`).join("")}</div></label>
        <label>${t("Titel")}<input data-b="title" value="${esc(dr.title)}" placeholder="${t("optional")}"></label>
        <div class="row"><button class="btn" data-k="bsave">${t("Speichern")}</button><button class="btn flat" data-k="builder">${t("Abbrechen")}</button></div>
      </div>
      ${hidden.length ? `<div class="sub" style="margin-top:10px">${t("Ausgeblendet")}: ${hidden.map((id) => {
        const def = d.layout.custom.find((c) => c.id === id);
        return `<button class="chip" data-hide="${id}">↺ ${esc(def ? def.title || t("Eigenes Modul") : t(STATS_TITLES[id]))}</button>`;
      }).join(" ")}</div>` : ""}</div>`;
  }
  bind(root) {
    const s = this._state;
    // v1.18.0: Empfehlung/Hinweis übernehmen bzw. Preisänderung rückgängig machen
    root.querySelectorAll("[data-apply]").forEach((el) => el.addEventListener("click", async () => {
      const cfg = this._applies?.[Number(el.dataset.apply)];
      if (cfg && (await priceDialog(this, cfg))) this._reload();
    }));
    root.querySelectorAll("[data-undo]").forEach((el) => el.addEventListener("click", async () => {
      if (!(await confirmDialog(t("Diese Preisänderung rückgängig machen? Die vorherigen Tagespreise werden in Smoobu wieder gesetzt.")))) return;
      try {
        const r = await this.store.ws("smoobu/rates/undo", { ...this.target, apartment_id: Number(el.dataset.apt), aenderung_id: el.dataset.undo }, { cache: false });
        toast(r.abweichend?.length ? `${t("Zurückgesetzt, aber")} ${r.abweichend.length} ${t("Tage weichen ab – bitte prüfen")}` : `✓ ${r.tage} ${t("Tage zurückgesetzt")}`);
        this.store.invalidate();
        this._reload();
      } catch (e) { toast(`${t("Fehler")}: ${e?.message || e}`); }
    }));
    // Filterleiste (gemeinsam mit Finanzen); Blättern setzt das Pace-Jahr zurück auf „folgt dem Zeitraum“
    bindFilterBar(this, root, { paceYear: null });
    root.querySelector('[data-k="paceyear"]')?.addEventListener("change", (e) => this.setState({ paceYear: Number(e.target.value) }, true));
    root.querySelectorAll("[data-matrix]").forEach((el) => el.addEventListener("click", () => this.setState({ matrix: el.dataset.matrix }, true)));
    // Fokus-Kennzahl: Verlauf darunter; Matrix folgt, wenn sie die Kennzahl kennt
    root.querySelectorAll("[data-focus]").forEach((el) => el.addEventListener("click", () => {
      const f = el.dataset.focus;
      const mx = MATRIX_MEASURES.some(([k]) => k === f) ? f : s.matrix;
      if (this._data.simple) { this.setState({ focus: f }); return; }
      this.setState({ focus: f, matrix: mx }, mx !== s.matrix);
    }));
    root.querySelectorAll("[data-mode]").forEach((el) => el.addEventListener("click", () => {
      lsSet(STATS_MODE_KEY, el.dataset.mode);
      this._data = null; // anderes Datenpaket (Einfach lädt weniger)
      this._reload();
    }));
    // Teilschritte 3/4: Tabelle, CSV, Anordnen, Baukasten
    root.querySelectorAll("[data-open]").forEach((el) => el.addEventListener("click", () => this.openBooking(Number(el.dataset.open))));
    root.querySelectorAll("[data-bz]").forEach((el) => el.addEventListener("click", () => {
      const [key, val] = el.dataset.bz.split(":");
      this.setState(key === "m" ? { bzMeasure: val } : key === "v" ? { bzView: val } : { bzBasis: val }, true);
    }));
    root.querySelector('[data-k="tableall"]')?.addEventListener("click", () => this.setState({ tableAll: !s.tableAll }));
    root.querySelector('[data-k="csv"]')?.addEventListener("click", () => this.exportCsv());
    root.querySelectorAll('[data-k="edit"]').forEach((el) => el.addEventListener("click", () => this.setState({ edit: !s.edit }, true)));
    root.querySelectorAll('[data-k="builder"]').forEach((el) => el.addEventListener("click", () => this.setState({ builder: !s.builder }, true)));
    const layoutChange = (fn) => { const l = statsLayout(); fn(l); saveLayout(l); this._reload(); };
    root.querySelectorAll("[data-mv]").forEach((el) => el.addEventListener("click", () => layoutChange((l) => {
      const i = l.order.indexOf(el.dataset.mv), j = i + Number(el.dataset.dir);
      if (i < 0 || j < 0 || j >= l.order.length) return;
      [l.order[i], l.order[j]] = [l.order[j], l.order[i]];
    })));
    root.querySelectorAll("[data-hide]").forEach((el) => el.addEventListener("click", () => layoutChange((l) => {
      const id = el.dataset.hide;
      l.hidden = l.hidden.includes(id) ? l.hidden.filter((x) => x !== id) : [...l.hidden, id];
    })));
    root.querySelectorAll("[data-del]").forEach((el) => el.addEventListener("click", async () => {
      if (!(await confirmDialog(t("Eigenes Modul löschen?")))) return;
      layoutChange((l) => { const id = el.dataset.del; l.custom = l.custom.filter((c) => c.id !== id); l.order = l.order.filter((x) => x !== id); l.hidden = l.hidden.filter((x) => x !== id); });
    }));
    root.querySelectorAll("[data-b]").forEach((el) => el.addEventListener("change", () => {
      const draft = { ...s.draft, [el.dataset.b]: el.value };
      if (draft.split === draft.dimension) draft.split = "";
      this._state.draft = draft;
      if (el.dataset.b !== "title") this.render();
    }));
    root.querySelectorAll("[data-bview]").forEach((el) => el.addEventListener("click", () => { this._state.draft = { ...s.draft, view: el.dataset.bview }; this.render(); }));
    root.querySelector('[data-k="bsave"]')?.addEventListener("click", () => {
      const title = root.querySelector('[data-b="title"]')?.value || "";
      const def = { ...s.draft, title, id: `c_${Date.now().toString(36)}`, split: s.draft.split || null };
      const l = statsLayout();
      l.custom.push(def);
      l.order.push(def.id);
      saveLayout(l);
      this._state.builder = false;
      this._reload();
    });
    // Breite merken und bei deutlicher Größenänderung neu zeichnen (Diagramme passen sich an)
    if (!this._ro && window.ResizeObserver) {
      this._ro = new ResizeObserver(() => {
        const w = this.getBoundingClientRect().width;
        if (this._data && w && Math.abs(w - (this._cw || 0)) > 40) this.render();
      });
      this._ro.observe(this);
    }
    // Tooltips: ein schwebendes Kästchen für alle Elemente mit data-tip (Maus: Hover, Touch: Tippen)
    const card = root.querySelector("ha-card");
    const tt = root.querySelector(".tt");
    if (!card || !tt) return;
    const show = (e) => {
      const el = e.target.closest?.("[data-tip]");
      if (!el) { tt.hidden = true; return; }
      tt.textContent = el.dataset.tip;
      tt.hidden = false;
      const r = card.getBoundingClientRect();
      const w = tt.offsetWidth, h = tt.offsetHeight;
      let x = e.clientX - r.left + 14, y = e.clientY - r.top + 14;
      if (x + w > r.width) x = Math.max(0, e.clientX - r.left - w - 14);
      if (y + h > r.height) y = Math.max(0, e.clientY - r.top - h - 14);
      tt.style.left = `${x}px`;
      tt.style.top = `${y}px`;
    };
    card.addEventListener("pointermove", show);
    card.addEventListener("pointerdown", show);
    card.addEventListener("pointerleave", () => { tt.hidden = true; });
  }
  // CSV der Datentabelle (alle Buchungen im Filter, gleiche Spalten wie die Buchungsliste)
  exportCsv() {
    const m = this._data?.mods?.tabelle;
    if (!m?.buchungen) return;
    const cols = BOOKING_COLS;
    const rows = m.buchungen.filter((b) => !b.blockiert).sort((a, b) => b.anreise.localeCompare(a.anreise));
    const [a, b] = this._data.range;
    downloadCsv(`smoobu_statistik_${iso(a)}_${iso(addDays(b, -1))}.csv`,
      [cols.map((c) => t(c[1])), ...rows.map((r) => cols.map((c) => r[c[0]] ?? ""))]);
  }
  getCardSize() { return 14; }
}

// ===========================================================================
// Kopfleiste (v1.15.0): Seiten-Navigation, Wohnungsauswahl, Hell/Dunkel/System
// ===========================================================================
// Eine Karte oben auf jeder Smoobu-Seite. Die Seitenpfade sind relativ zum
// aktuellen Dashboard (z. B. „smoobu-belegung“ → /dashboard-x/smoobu-belegung).
// Zusätzlich färbt sie den Seitenhintergrund passend zum gewählten Modus,
// damit zwischen den Karten keine helle HA-Fläche im Dunkelmodus bleibt.
const DEFAULT_PAGES = [
  // v1.18.0b8: Seite „Belegung“ heißt jetzt „Kalender“, auch im Pfad (Wunsch Betreiber 17.11.2026).
  // legacy: hat das Dashboard noch die alte Ansicht „smoobu-belegung“ (und keine neue), zeigt der Reiter
  // dorthin – so bleiben bestehende Dashboards anderer Nutzer ohne Anpassung funktionsfähig
  { name: "Übersicht", path: "smoobu" }, { name: "Kalender", path: "smoobu-kalender", legacy: "smoobu-belegung" },
  { name: "Buchungen", path: "smoobu-buchungen" }, { name: "Finanzen", path: "smoobu-finanzen" },
  // Statistik-Werkbank (Teilschritt 2): optional = Reiter erscheint nur, wenn das Dashboard eine Ansicht
  // mit diesem Pfad hat (die Seite selbst kommt in Teilschritt 5) – so entsteht vorher kein toter Link
  { name: "Statistik", path: "smoobu-statistik", optional: true },
  { name: "Nachrichten", path: "smoobu-nachrichten", badge: "nachrichten" }, { name: "Assistent", path: "smoobu-assistent" },
  // v1.18.0: nur sichtbar, wenn das Dashboard eine Ansicht „smoobu-einstellungen“ hat; Zahnrad statt Text am Handy
  { name: "Einstellungen", path: "smoobu-einstellungen", optional: true, icon: "gear" },
];
const ICON_SVG = {
  hell: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>`,
  dunkel: `<svg viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>`,
  system: `<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg>`,
  gear: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>`,
};
class SmoobuHeaderCard extends SmoobuCard {
  // home (v1.17.1): optionaler Rücksprung vor den Reitern, z. B. { name: "Host", path: "/dashboard-ferienwohnung/host" }
  static defaults = { pages: DEFAULT_PAGES, show_apartments: true, page_background: true, home: null };
  static css = `
    ha-card { background: none; border: 0; padding: 14px 0 2px; overflow: visible; } /* Abstand zur HA-Kopfzeile */
    .bar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
    .tabs { display: flex; gap: 4px; flex-wrap: wrap; }
    .tabs a { padding: 8px 15px; border-radius: 999px; color: var(--sm-muted); font-weight: 500; text-decoration: none; cursor: pointer;
      display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
    .tabs a:hover { color: var(--sm-ink); background: color-mix(in srgb, var(--sm-ink) 6%, transparent); }
    .tabs a.on { background: var(--sm-accent); color: var(--sm-acc-ink); font-weight: 600; }
    .tabs a.home { color: var(--sm-ink); font-weight: 600; }
    .tabs .hsep { width: 1px; align-self: stretch; margin: 6px 4px; background: var(--sm-line); }
    .tabs i { font-style: normal; font-size: .7rem; font-weight: 700; background: var(--sm-bad); color: #fff; border-radius: 9px; padding: 0 6px; line-height: 1.5; }
    .right { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .seg button { display: inline-flex; gap: 6px; align-items: center; }
    .seg.theme button[aria-pressed="true"] { background: var(--sm-accent); color: var(--sm-acc-ink); }
    .tabs svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
    @media (max-width: 700px) { .tabs .lbl { display: none; } }
    .seg svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
    .seg .n { opacity: .7; margin-left: 2px; }
    @media (max-width: 700px) { .seg .lbl { display: none; } }
  `;
  async load() {
    const info = await this.store.getInfo();
    return { info, open: await this.countOpen(info) };
  }
  // Offene Gästenachrichten zählen. v1.17.0: Antwortstatus immer frisch (cache: false) – vorher kam er
  // aus dem Seiten-Cache und blieb bis zum Neuladen der Seite stehen (das Backend cacht selbst 10 min
  // und verwirft den Eintrag bei neuer Nachricht, eigenem Senden und „keine Antwort nötig“)
  async countOpen(info) {
    if (!(this._config.pages || []).some((p) => p.badge === "nachrichten")) return 0;
    if (!rightsOf(allApartment(info)).has("nachrichten")) return 0; // v1.18.0: ohne Recht kein Abruf
    try {
      const list = await this.store.ws("smoobu/bookings", { ...this.target, start: iso(addDays(D(info.heute), -14)), end: iso(addDays(D(info.heute), 60)) });
      // Gleiche Auswahl wie der Posteingang (Standard 14 Tage zurück / 60 voraus, inkl. abgereister Gäste,
      // Reihenfolge laufend → kommend → vergangen, höchstens 60), damit Badge und Posteingang dieselbe Zahl zeigen
      const order = { laufend: 0, kommend: 1, vergangen: 2 };
      const ids = list.buchungen.filter((b) => !b.blockiert && !b.storniert)
        .sort((a, b) => order[a.status] - order[b.status] || (a.status === "vergangen" ? b.anreise.localeCompare(a.anreise) : a.anreise.localeCompare(b.anreise)))
        .slice(0, 60).map((b) => b.id);
      if (!ids.length) return 0;
      const st = (await this.store.ws("smoobu/message_status", { ...this.target, reservation_ids: ids }, { cache: false })).status || {};
      return Object.values(st).filter((x) => x.offen).length;
    } catch (e) { return this._data?.open || 0; } // Fehler → letzten Stand behalten statt Badge zu verlieren
  }
  async recount() {
    if (!this._data) return;
    const open = await this.countOpen(this._data.info);
    if (this._data && open !== this._data.open) { this._data.open = open; this.render(); }
  }
  // Zusätzlich zum Datenabo: Statusänderungen aus Posteingang/Buchungsdialog und Rückkehr in die App
  _listen() {
    super._listen();
    const offMsg = this.store.onMessages(() => this.recount());
    const onVis = () => { if (document.visibilityState === "visible") this.recount(); };
    document.addEventListener("visibilitychange", onVis);
    const base = this._unsub;
    this._unsub = () => { base?.(); offMsg(); document.removeEventListener("visibilitychange", onVis); };
  }
  href(path) {
    if (path.startsWith("/")) return path;
    const parts = location.pathname.split("/").filter(Boolean);
    return `/${parts[0] || "lovelace"}/${path}`;
  }
  // Pfade der Ansichten des aktuellen Dashboards (aus hui-root/hui-view); null = unbekannt (dann alle Reiter zeigen)
  viewPaths() {
    let n = this;
    for (let i = 0; i < 80 && n; i++) {
      n = n.parentNode || n.host;
      const views = n?.lovelace?.config?.views;
      if (Array.isArray(views)) return new Set(views.map((v, j) => String(v.path ?? j)));
    }
    return null;
  }
  body({ info, open }) {
    const here = location.pathname.split("/").filter(Boolean).pop();
    const known = this.viewPaths();
    // v1.18.0: Seiten ohne Recht ausblenden (Rechte über alle Wohnungen des Kontos)
    const rights = rightsOf(allApartment(info));
    // Alte Pfade auflösen (z. B. smoobu-belegung → smoobu-kalender, v1.18.0b8), nur wenn das Dashboard
    // die neue Ansicht nicht kennt, die alte aber schon
    const pages = (this._config.pages || []).map((p) => (p.legacy && known && !known.has(p.path) && known.has(p.legacy) ? { ...p, path: p.legacy } : p)).filter((p) => (!p.optional || !known || known.has(p.path))
      && (p.path === "smoobu" ? rights.has("gaeste") : rights.has(pageRight(p.path))));
    const home = this._config.home?.path ? `<a class="home" data-href="${esc(this.href(this._config.home.path))}" title="${esc(t("Zurück zu"))} ${esc(this._config.home.name || "")}">← ${esc(t(this._config.home.name || "Zurück"))}</a><span class="hsep"></span>` : "";
    const tabs = home + pages.map((p) => `<a class="${p.path === here ? "on" : ""}" data-href="${esc(this.href(p.path))}">${p.icon && ICON_SVG[p.icon] ? `${ICON_SVG[p.icon]}<span class="lbl">${esc(t(p.name))}</span>` : esc(t(p.name))}${p.badge === "nachrichten" && open ? `<i>${open}</i>` : ""}</a>`).join("");
    const ws = info.wohnungen;
    const sel = this.target.apartment_id;
    const showApts = this._config.show_apartments && ws.length > 1 && !this._config.apartment_id;
    if (showApts !== !!this._aptReg) { this._aptReg = showApts; showApts ? HeaderApts.add() : HeaderApts.remove(); }
    const apts = showApts
      ? `<div class="seg" role="group" aria-label="${t("Wohnung")}"><button data-apt="${ALL}" aria-pressed="${sel === ALL}">${t("Alle")}<span class="n">${ws.length}</span></button>
        ${ws.map((w) => `<button data-apt="${w.apartment_id}" aria-pressed="${sel === w.apartment_id}" title="${esc(w.name)}">${esc(w.name)}</button>`).join("")}</div>` : "";
    const mode = Theme.mode;
    const theme = `<div class="seg theme" role="group" aria-label="${t("Darstellung")}">${[["hell", "Hell"], ["dunkel", "Dunkel"], ["system", "System"]]
      .map(([k, l]) => `<button data-theme="${k}" aria-pressed="${mode === k}" title="${t(l)}">${ICON_SVG[k]}<span class="lbl">${t(l)}</span></button>`).join("")}</div>`;
    return `<div class="bar"><nav class="tabs">${tabs}</nav><div class="right">${apts}${theme}</div></div>`;
  }
  render() {
    super.render();
    this.pageBackground();
  }
  // Hintergrund der Dashboard-Ansicht an den Modus anpassen (beim Verlassen wiederherstellen)
  pageBackground() {
    if (!this._config?.page_background) return;
    let n = this, view = null;
    for (let i = 0; i < 60 && n; i++) {
      n = n.parentNode || n.host;
      if (n?.localName === "hui-view" || n?.localName === "hui-panel-view" || n?.localName === "hui-sections-view") view = n;
    }
    if (!view) return;
    if (this._view !== view) { this._restoreBg(); this._view = view; this._prevBg = view.style.background; }
    view.style.background = PAL[DARK ? "dark" : "light"].bg;
  }
  _restoreBg() { if (this._view) { this._view.style.background = this._prevBg || ""; this._view = null; } }
  disconnectedCallback() {
    if (this._aptReg) { this._aptReg = false; HeaderApts.remove(); }
    this._restoreBg(); super.disconnectedCallback();
  }
  bind(root) {
    root.querySelectorAll("[data-href]").forEach((el) => el.addEventListener("click", () => {
      history.pushState(null, "", el.dataset.href);
      window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));
    }));
    root.querySelectorAll("[data-theme]").forEach((el) => el.addEventListener("click", () => { Theme.mode = el.dataset.theme; }));
    root.querySelectorAll("[data-apt]").forEach((el) => el.addEventListener("click", () => {
      AptSel.value = el.dataset.apt === ALL ? ALL : Number(el.dataset.apt);
    }));
  }
  getCardSize() { return 1; }
}

// ===========================================================================
// v1.18.0: Einstellungen im Dashboard (custom:smoobu-settings-card)
// Liest/schreibt dieselben Optionen wie der Options-Dialog über smoobu/settings/get|set.
// Berechtigung prüft das Backend (Admins + Option „Einstellungen im Dashboard erlauben für“).
// Entwurf (draft) bleibt lokal, bis „Speichern“ gedrückt wird; Eingaben in Textfeldern
// zeichnen die Karte bewusst NICHT neu (Fokus/Cursor bleiben), nur Schalter/Chips/Reiter.
// ===========================================================================
const SET_TABS = [
  ["benachrichtigungen", "Benachrichtigungen"], ["assistent", "KI-Assistent"],
  ["provisionen", "Provisionen & Kanäle"], ["kosten", "Kosten & Preise"], ["rechte", "Benutzer & Rechte"], ["allgemein", "Allgemein & Abruf"],
];
const PUSH_INFO = {
  buchung: ["Neue Buchung", "Sobald eine neue Buchung eingeht (keine Sperrzeiten)."],
  storno: ["Storno & Änderung", "Storniert oder geändert (Zeitraum, Personen, Ankunft, Preis) – mit Vorher → Nachher."],
  nachricht: ["Gästenachricht", "Neue Nachricht eines Gastes. Mit KI-Vorschlag kommt stattdessen der Vorschlag."],
  vorschlag: ["KI-Antwortvorschlag", "Vorschlag mit Buttons Senden / Bearbeiten / Ignorieren."],
  zahlung: ["Zahlungserinnerung", "Offene Zahlung einige Tage vor Anreise (ohne Kanäle mit Zahlung über das Portal)."],
  briefing: ["Tagesbriefing", "Zusammenfassung des Tages zur festen Uhrzeit."],
  luecken: ["Nicht buchbare Lücken", "Lücken, die der Mindestaufenthalt sperrt – zur festen Uhrzeit."],
};
const PUSH_TIME = { zahlung: "notify_zahlung_time", briefing: "assist_briefing_time", luecken: "notify_luecken_time" };
// Feld → Reiter (für Fehler: der Reiter mit dem ersten Fehler wird geöffnet)
const SET_FIELD_TAB = (key) => {
  if (key.startsWith("notify_") || key === "assist_briefing_time") return "benachrichtigungen";
  if (["ai_enabled", "assistant", "ai_entity", "assist_status", "assist_path"].includes(key) || key.startsWith("ai_")) return "assistent";
  if (["commissions", "commission_other", "direct_channels", "payment_excluded_channels"].includes(key)) return "provisionen";
  if (key.startsWith("cost_") || key.startsWith("lastminute_") || ["channel_markups", "genius_discount", "genius_share"].includes(key)) return "kosten";
  if (["user_roles", "default_role", "settings_users"].includes(key)) return "rechte";
  return "allgemein";
};
const SET_ERR = {
  invalid: "Ungültiger Wert", invalid_time: "Uhrzeit als HH:MM", invalid_percent: "0–50 %", invalid_date: "Ungültiges Datum",
  invalid_entity: "Ungültige Entität", invalid_list: "Ungültige Liste", invalid_code: "Nur Buchstaben und Ziffern",
  duplicate_code: "Kürzel schon vergeben", ai_entity_required: "Bitte eine KI wählen oder „KI erlauben“ ausschalten",
  admin_only: "Nur Admins können das ändern", unknown_field: "Unbekanntes Feld",
  invalid_number: "Ungültige Zahl oder außerhalb des erlaubten Bereichs", invalid_role: "Unbekannte Rolle", invalid_grid_share: "12 Werte zwischen 0 und 100",
};
// Gradtagszahlen (Promille je Monat) – gleiche Tabelle wie deckungsbeitrag.HEAT_PROMILLE (nur für die Vorschau)
const HEAT_PROMILLE = [170, 150, 130, 80, 40, 13.33, 13.33, 13.34, 30, 80, 120, 160];
const clone = (v) => JSON.parse(JSON.stringify(v));
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const phoneName = (svc) => svc.replace(/^notify\.mobile_app_/, "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

// v1.18.0b6: Datenschutz für die KI – Stufen und Einzelschalter mit Einbuße (Texte wie im Options-Dialog)
const PRIVACY_LEVELS = [
  ["standard", "Standard (empfohlen)", "Gastnamen → Platzhalter (vor dem Senden wieder eingesetzt), Adresse/Kennzeichen/Geburtsdatum/Ausweis geschwärzt, Daten relativ. Einbuße: praktisch keine."],
  ["streng", "Streng", "Wie Standard, dazu nur 2 Nachrichten Verlauf und ohne Kanal/Bezahlstatus. Einbuße: gering – Rückbezüge und Zahlungsfragen bleiben eher offen."],
  ["maximal", "Maximal", "Nur Gästenachricht (geschützt) und Wissensdatenbank. Keine Buchungsdaten, kein Verlauf, keine Beispiele, keine Status-Entitäten. Einbuße: hoch – Antworten allgemeiner, Ton nicht mehr eurer, Zeiten und Probleme bleiben offen."],
  ["individuell", "Individuell", "Jeder Schalter einzeln (unten)."],
];
const PRIVACY_FLAGS = [
  ["ai_pseudonym", "Gastnamen durch Platzhalter ersetzen", "keine", "Die KI schreibt [GAST_VORNAME], die Integration setzt den Namen ein. Aus = Name geht an die KI."],
  ["ai_redact_extended", "Erweitert schwärzen", "gering", "Adresse, PLZ/Ort, Kennzeichen, Geburtsdatum, Ausweisnummer. Musterbasiert, kein Garant."],
  ["ai_dates_relative", "Daten relativ", "gering", "„Fr., in 3 Tagen“ statt Kalenderdatum; im Entwurf wird das Datum eingesetzt."],
  ["ai_send_dates", "Reisedaten und Belegung senden", "mittel", "Aus: kein früher Check-in/später Check-out, keine Antworten zu Zeiten."],
  ["ai_send_guests", "Personen, Kinder, Hund senden", "gering", "Aus: Fragen zu Kinderbett, Hund, Personenzahl bleiben offen."],
  ["ai_send_payment", "Kanal und Bezahlstatus senden", "gering", "Aus: Fragen zu Zahlung und Portal bleiben offen."],
  ["ai_examples", "Frühere Antworten als Stilvorlage", "hoch", "Aus: Anrede, Ton und Gruß sind nicht mehr eure."],
  ["ai_status", "Status-Entitäten senden", "mittel", "Aus: keine Hinweise bei Problemen (Heizung, Tür)."],
];
// Vorschau-Fenster: zeigt den Text genau so, wie er an die KI geht (bzw. gehen würde)
function promptDialog(title, res) {
  const p = PAL[DARK ? "dark" : "light"];
  const wrap = document.createElement("div");
  wrap.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10002;display:flex;align-items:center;justify-content:center;padding:16px";
  const when = res.zeit ? new Date(res.zeit).toLocaleString(locale()) : "";
  const body = res.text ? `<pre style="white-space:pre-wrap;word-break:break-word;font:12.5px/1.45 ui-monospace,Menlo,monospace;margin:0;max-height:60vh;overflow:auto;background:${p.surf2};padding:12px;border-radius:10px">${esc(res.text)}</pre>`
    : `<div>${t("Seit dem letzten Neustart ging noch keine Anfrage an die KI.")}</div>`;
  wrap.innerHTML = `<div style="background:${p.surf};color:${p.ink};padding:20px;border-radius:16px;width:min(760px,100%);font:14px/1.45 ${FONT_ATTR};border:1px solid ${p.line};box-shadow:0 12px 40px rgba(0,0,0,.3)">
    <div style="font-weight:650;font-size:16px;margin-bottom:4px">${esc(t(title))}</div>
    <div style="color:${p.mut};font-size:12.5px;margin-bottom:12px">${esc(t("Datenschutz-Stufe"))}: ${esc(t((PRIVACY_LEVELS.find((l) => l[0] === res.stufe) || [0, res.stufe])[1]))}${when ? ` · ${esc(when)}` : ""}${res.ki ? ` · ${esc(res.ki)}` : ""}
      ${res.quelle === "vorschau" ? ` · ${t("Probelauf mit den gespeicherten Einstellungen – nichts wurde gesendet.")}` : ""}</div>
    ${body}<div style="display:flex;justify-content:flex-end;margin-top:14px"><button data-v="1" style="font:600 14px ${FONT_ATTR};padding:8px 16px;border-radius:999px;border:none;background:${p.acc};color:${p.accInk};cursor:pointer">${t("Schließen")}</button></div></div>`;
  wrap.addEventListener("click", (e) => { if (e.target?.dataset?.v || e.target === wrap) wrap.remove(); });
  document.body.appendChild(wrap);
}

class SmoobuSettingsCard extends SmoobuCard {
  // tab: Start-Reiter (benachrichtigungen | assistent | provisionen | kosten | allgemein)
  static defaults = { title: "Einstellungen", entry_id: null, tab: "benachrichtigungen" };
  static initialState = (c) => ({ tab: c.tab || "benachrichtigungen", errors: {}, saving: false });
  static css = `
    .stabs { display: flex; gap: 4px; flex-wrap: wrap; margin: 4px 0 16px; border-bottom: 1px solid var(--sm-line); padding-bottom: 10px; }
    .stabs button { border: 0; background: none; font: inherit; font-size: .9rem; padding: 7px 14px; border-radius: 999px; cursor: pointer; color: var(--sm-muted); }
    .stabs button[aria-pressed="true"] { background: var(--sm-accent); color: var(--sm-acc-ink); font-weight: 600; }
    .stabs button .e { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--sm-bad); margin-left: 6px; vertical-align: 1px; }
    .grp { border: 1px solid var(--sm-line); border-radius: var(--sm-r); margin-bottom: 12px; overflow: hidden; }
    .grp > .gh { display: flex; gap: 12px; align-items: flex-start; padding: 14px 16px; }
    .grp > .gh .grow b { display: block; font-weight: 650; }
    .grp > .gb { padding: 0 16px 14px; display: grid; gap: 12px; }
    .grp.off > .gb { display: none; }
    .fld { display: grid; grid-template-columns: minmax(150px, 230px) 1fr; gap: 6px 14px; align-items: center; }
    .fld > label { font-size: .88rem; font-weight: 550; }
    .fld .hint { grid-column: 2; font-size: .78rem; color: var(--sm-muted); margin-top: -2px; }
    .fld .ferr, .ferr { grid-column: 2; font-size: .8rem; color: var(--sm-bad); font-weight: 600; }
    .fld input[type=number] { width: 110px; } .fld input[type=text] { width: min(100%, 360px); }
    .fld select { max-width: 360px; } select.chadd { max-width: 300px; }
    .inline { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .unit { color: var(--sm-muted); font-size: .84rem; }
    .chips { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
    .chip .x { opacity: .6; margin-left: 2px; }
    .sw { flex: none; width: 44px; height: 26px; border-radius: 999px; border: 0; background: var(--sm-line); position: relative; cursor: pointer; padding: 0; transition: background .15s; }
    .sw::after { content: ""; position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 50%; background: var(--sm-surf); box-shadow: 0 1px 3px rgba(0,0,0,.25); transition: left .15s; }
    .sw[aria-checked="true"] { background: var(--sm-accent); } .sw[aria-checked="true"]::after { left: 21px; }
    .sw:focus-visible { outline: 2px solid var(--sm-accent); outline-offset: 2px; }
    table.prov td { white-space: normal; } table.prov input { width: 90px; } table.prov input.name { width: 180px; }
    .foot { position: sticky; bottom: 0; margin: 16px -20px -18px; padding: 12px 20px; background: var(--sm-surf2); border-top: 1px solid var(--sm-line);
      display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .foot .grow { font-size: .86rem; color: var(--sm-muted); }
    .foot .grow.dirty { color: var(--sm-warn); font-weight: 600; }
    .note { padding: 10px 14px; border-radius: var(--sm-rs); background: var(--sm-surf2); border-left: 4px solid var(--sm-accent); font-size: .86rem; margin-bottom: 12px; }
    @media (max-width: 640px) { .fld { grid-template-columns: 1fr; } .fld .hint, .fld .ferr { grid-column: 1; } }
  `;
  async load() {
    const res = await this.store.ws("smoobu/settings/get", this._config.entry_id ? { entry_id: this._config.entry_id } : {}, { cache: false });
    // Ungespeicherten Entwurf behalten, solange er zum selben Konto gehört
    if (!this._draft || !this.dirty || this._draftEntry !== res.entry_id) {
      this._draft = res.erlaubt ? clone(res.werte) : null;
      this._draftEntry = res.entry_id;
    }
    return res;
  }
  // Neuer Datenstand (alle 10 min / Webhook) darf einen offenen Entwurf nicht überschreiben
  _reload() { if (this.dirty && this._data) return; return super._reload(); }
  get dirty() { return !!this._data?.werte && !!this._draft && !same(this._data.werte, this._draft); }
  changes() {
    const out = {};
    for (const [k, v] of Object.entries(this._draft || {})) if (!same(v, this._data.werte[k])) out[k] = v;
    return out;
  }
  // --- kleine Bausteine -----------------------------------------------------
  sw(key, label) {
    return `<button class="sw" role="switch" aria-checked="${!!this._draft[key]}" aria-label="${esc(t(label))}" data-sw="${esc(key)}"></button>`;
  }
  err(key) { const e = this._state.errors[key]; return e ? `<div class="ferr">${esc(t(SET_ERR[e] || e))}</div>` : ""; }
  fld(label, control, hint = "", key = "") {
    return `<div class="fld"><label>${esc(t(label))}</label><div class="inline">${control}</div>${hint ? `<div class="hint">${esc(t(hint))}</div>` : ""}${key ? this.err(key) : ""}</div>`;
  }
  numIn(key, min, max, step = 1, unit = "") {
    return `<input type="number" data-num="${esc(key)}" min="${min}" max="${max}" step="${step}" value="${esc(this._draft[key])}">${unit ? `<span class="unit">${esc(t(unit))}</span>` : ""}`;
  }
  timeIn(key) { return `<input type="time" data-txt="${esc(key)}" value="${esc(this._draft[key] || "")}">`; }
  // Mehrfachauswahl als Chips: options = bekannte Werte; gewählte, unbekannte Werte erscheinen zusätzlich
  pick(key, options, label = (v) => v, custom = false) {
    const sel = this._draft[key] || [];
    const all = [...options, ...sel.filter((v) => !options.includes(v))];
    const chips = all.map((v) => `<button class="chip" data-pick="${esc(key)}" data-v="${esc(v)}" aria-pressed="${sel.includes(v)}">${esc(label(v))}</button>`).join("");
    // v1.18.0: weitere Kanäle per Dropdown (Smoobu-Kanäle) statt Freitext
    const add = custom ? this.chanSelect(key, all, "＋ Weiteren Kanal wählen …") : "";
    return `<div class="chips">${chips || `<span class="muted">${t("keine verfügbar")}</span>`}${add}</div>`;
  }
  // v1.18.0: Kanal-Dropdown in drei Gruppen (Backend meta.kanal_auswahl): mit Buchungen (Anzahl),
  // in den Einstellungen genutzt, übrige Smoobu-Kanäle. Bereits gewählte Kanäle (exclude) fehlen.
  // Smoobu hat keinen Endpunkt „angebundene Kanäle“ – daher Buchungen + Katalog aus der API-Doku.
  chanSelect(target, exclude, placeholder = "＋ Kanal hinzufügen …") {
    const a = this._data?.meta?.kanal_auswahl || { buchungen: [], eingestellt: [], katalog: [] };
    const skip = new Set((exclude || []).map((x) => String(x).toLowerCase()));
    const opt = (name, text) => skip.has(name.toLowerCase()) ? "" : `<option value="${esc(name)}">${esc(text)}</option>`;
    const grp = (label, html) => html ? `<optgroup label="${esc(t(label))}">${html}</optgroup>` : "";
    const booked = a.buchungen.map((c) => opt(c.name, `${chn(c.name)} · ${c.buchungen} ${t(c.buchungen === 1 ? "Buchung" : "Buchungen")}`)).join("");
    const used = a.eingestellt.map((n) => opt(n, chn(n))).join("");
    const cat = a.katalog.map((n) => opt(n, chn(n))).join("");
    if (!booked && !used && !cat) return "";
    return `<select class="chadd" data-chadd="${esc(target)}" aria-label="${esc(t("Kanal hinzufügen"))}">
      <option value="">${esc(t(placeholder))}</option>${grp("Kanäle mit Buchungen", booked)}${grp("In den Einstellungen genutzt", used)}${grp("Weitere Smoobu-Kanäle", cat)}</select>`;
  }
  // --- Reiter -----------------------------------------------------------------
  tabPush(meta) {
    const d = this._draft;
    const groups = meta.push_arten.map((kind) => {
      const [name, desc] = PUSH_INFO[kind] || [kind, ""];
      const on = d[`notify_${kind}`];
      let extra = "";
      if (kind === "zahlung") extra += this.fld("Tage vor Anreise", this.numIn("notify_zahlung_days", 1, 60, 1, "Tage"), "", "notify_zahlung_days");
      if (PUSH_TIME[kind]) extra += this.fld("Uhrzeit", this.timeIn(PUSH_TIME[kind]), "", PUSH_TIME[kind]);
      // v1.18.0: je Push-Art, ob sie in der Ruhezeit wartet (an) oder immer sofort kommt (aus)
      extra += this.fld("Hält Ruhezeit ein", this.sw(`notify_${kind}_quiet`, "Hält Ruhezeit ein"),
        d.notify_quiet ? (d[`notify_${kind}_quiet`] ? "Wird in der Ruhezeit gesammelt und zum Ende zugestellt." : "Kommt auch in der Ruhezeit sofort.")
          : "Ruhezeit ist aus – wirkt erst, wenn sie eingeschaltet ist.", `notify_${kind}_quiet`);
      const to = d[`notify_${kind}_to`] || [];
      return `<div class="grp ${on ? "" : "off"}"><div class="gh"><div class="grow"><b>${esc(t(name))}</b><span class="sub">${esc(t(desc))}</span>
          ${on && !to.length ? `<div class="ferr">${t("Kein Empfänger gewählt – es kommt kein Push.")}</div>` : ""}</div>${this.sw(`notify_${kind}`, name)}</div>
        <div class="gb">${this.fld("Empfänger", this.pick(`notify_${kind}_to`, meta.handys, phoneName), "", `notify_${kind}_to`)}${extra}</div></div>`;
    }).join("");
    const waits = meta.push_arten.filter((k) => d[`notify_${k}`] && d[`notify_${k}_quiet`]);
    const quiet = `<div class="grp ${d.notify_quiet ? "" : "off"}"><div class="gh"><div class="grow"><b>${t("Ruhezeit")}</b>
        <span class="sub">${t("Pushes mit „Hält Ruhezeit ein“ werden gesammelt und zum Ende der Ruhezeit zugestellt.")}</span></div>${this.sw("notify_quiet", "Ruhezeit")}</div>
      <div class="gb">${this.fld("Von", this.timeIn("notify_quiet_from"), "", "notify_quiet_from")}${this.fld("Bis", this.timeIn("notify_quiet_to"), "", "notify_quiet_to")}
        ${this.fld("Warten in der Ruhezeit", waits.length ? waits.map((k) => `<span class="chip" aria-pressed="true">${esc(t((PUSH_INFO[k] || [k])[0]))}</span>`).join(" ") : `<span class="muted">${t("keine – alle kommen sofort")}</span>`,
          "Einstellbar je Push-Art („Hält Ruhezeit ein“). Dringende Vorschläge und Bestätigungen kommen immer sofort.")}</div></div>`;
    const none = meta.handys.length ? "" : `<div class="note">${t("Kein Handy mit HA-App gefunden (notify.mobile_app_…).")}</div>`;
    return none + groups + quiet;
  }
  tabAssist(meta) {
    const d = this._draft;
    const ai = `<select data-sel="ai_entity"><option value="">${t("– keine –")}</option>${meta.ki_entitaeten.map((e) =>
      `<option value="${esc(e.entity_id)}" ${d.ai_entity === e.entity_id ? "selected" : ""}>${esc(e.name)}</option>`).join("")}
      ${d.ai_entity && !meta.ki_entitaeten.some((e) => e.entity_id === d.ai_entity) ? `<option value="${esc(d.ai_entity)}" selected>${esc(d.ai_entity)} (${t("nicht gefunden")})</option>` : ""}</select>`;
    const states = Object.keys(this._hass.states || {}).sort();
    const status = `<div class="chips">${(d.assist_status || []).map((id) => `<button class="chip" data-rm="assist_status" data-v="${esc(id)}" aria-pressed="true"
        title="${esc(t("Entfernen"))}">${esc(this._hass.states[id]?.attributes?.friendly_name || id)}<span class="x">✕</span></button>`).join("")}
      <input type="text" class="add" data-addto="assist_status" list="sm-ents" placeholder="${esc(t("Entität suchen + Enter"))}" style="width:240px">
      <datalist id="sm-ents">${states.map((s) => `<option value="${esc(s)}">${esc(this._hass.states[s]?.attributes?.friendly_name || "")}</option>`).join("")}</datalist></div>`;
    return `<div class="grp"><div class="gh"><div class="grow"><b>${t("KI erlauben")}</b><span class="sub">${t("Aus = keinerlei KI-Aufruf, keine Daten an KI-Anbieter.")}</span></div>${this.sw("ai_enabled", "KI erlauben")}</div>
        <div class="gb">${this.fld("KI-Entität", ai, "ai_task-Entität, die Vorschläge erzeugt.", "ai_entity")}
          ${this.fld("Automatische Antwortvorschläge", this.sw("assistant", "Automatische Antwortvorschläge"), "Wirkt nur, wenn die KI erlaubt ist.")}</div></div>
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Kontext & Links")}</b></div></div>
        <div class="gb">${this.fld("Kontext-Entitäten", status, "Zustände, die die KI bei Antworten kennen darf (z. B. Heizung, Tür).", "assist_status")}
          ${this.fld("Dashboard-Pfad für „Bearbeiten“", `<input type="text" data-txt="assist_path" value="${esc(d.assist_path)}">`, "Ziel des Buttons „Bearbeiten“ im Push.", "assist_path")}</div></div>
      ${this.privacyGroup()}`;
  }
  // v1.18.0b6: Datenschutz-Stufe, Einzelschalter (nur bei „Individuell“), eigene Namen, Vorschau
  privacyGroup() {
    const d = this._draft;
    const lvl = d.ai_privacy || "standard";
    const levels = PRIVACY_LEVELS.map(([k, l]) => `<button class="chip" data-privacy="${k}" aria-pressed="${lvl === k}">${esc(t(l))}</button>`).join("");
    const desc = (PRIVACY_LEVELS.find((x) => x[0] === lvl) || PRIVACY_LEVELS[0])[2];
    const flags = lvl !== "individuell" ? "" : PRIVACY_FLAGS.map(([k, l, loss, hint]) =>
      this.fld(l, this.sw(k, l), `${t("Einbuße")} ${t(loss)}: ${hint}`, k)).join("")
      + this.fld("Nachrichten aus dem Verlauf", this.numIn("ai_history", 0, 6, 1), "0–6. Weniger = Rückbezüge („wie besprochen“) gehen verloren.", "ai_history");
    const names = `<input type="text" data-names="ai_host_names" value="${esc((d.ai_host_names || []).join(", "))}">`;
    const changed = this.dirty && Object.keys(this.changes()).some((k) => k.startsWith("ai_"));
    return `<div class="grp"><div class="gh"><div class="grow"><b>${t("Datenschutz")}</b>
        <span class="sub">${t("Was an die KI geht. Nicht garantiert anonym: Die Gästenachricht ist Freitext, nur bekannte Namen und typische Muster werden ersetzt.")}</span></div></div>
      <div class="gb">${this.fld("Datenschutz-Stufe", `<div class="chips">${levels}</div>`, desc, "ai_privacy")}
        ${flags}
        ${this.fld("Eigene Namen", names, "Kommagetrennt, werden nie ersetzt (z. B. eure Signatur). Standard: Wörter aus dem Kontonamen.", "ai_host_names")}
        ${this.fld("Was geht an die KI?", `<button class="btn flat" data-prompt="letzte">${t("Letzte KI-Anfrage")}</button>
          <button class="btn flat" data-prompt="probe">${t("Probelauf nächste Buchung")}</button>`,
          changed ? "Probelauf nutzt die gespeicherten Einstellungen – erst speichern." : "Zeigt den exakten Text. Der Probelauf ruft die KI nicht auf.")}</div></div>`;
  }
  tabProv(meta) {
    const d = this._draft;
    const fixed = meta.feste_provisionen;
    // v1.18.0: liefert Smoobu zu diesem Kanal eine gültige Provision? (letzte 24 Monate) → dann greift der %-Wert nur als Rückfall
    const src = meta.provision_herkunft || {};
    const srcBadge = (ch) => {
      const x = src[ch];
      if ((d.direct_channels || []).includes(ch)) return `<span class="muted">${t("Direktkanal")}</span>`;
      if (!x) return `<span class="muted">${t("keine Buchungen")}</span>`;
      const tip = `${x.mit_provision} ${t("von")} ${x.buchungen} ${t("Buchungen mit Provision von Smoobu")}${x.prozent_schnitt !== null ? ` · Ø ${num(x.prozent_schnitt, 1)} %` : ""}${x.ungueltig ? ` · ${x.ungueltig} ${t("unplausibel (> 40 %) – ignoriert")}` : ""}`;
      if (x.status === "smoobu") return `<span class="badge good" data-tip="${esc(tip)}" title="${esc(tip)}">✓ ${t("Smoobu liefert")}${x.prozent_schnitt !== null ? ` · Ø ${num(x.prozent_schnitt, 1)} %` : ""}</span>`;
      if (x.status === "teilweise") return `<span class="badge warn" title="${esc(tip)}">◐ ${t("teilweise")} (${x.mit_provision}/${x.buchungen})</span>`;
      return `<span class="badge" title="${esc(tip)}">${t("Wert hier wird genutzt")}</span>`;
    };
    const rows = Object.entries(d.commissions).map(([ch, pct]) => `<tr><td>${esc(chn(ch))}</td>
      <td class="n"><span class="inline" style="justify-content:flex-end"><input type="number" data-comm="${esc(ch)}" min="0" max="50" step="0.1" value="${esc(pct)}"><span class="unit">%</span></span></td>
      <td>${srcBadge(ch)}</td>
      <td>${fixed.includes(ch) ? "" : `<button class="lnk" data-cdel="${esc(ch)}">${t("Entfernen")}</button>`}</td></tr>`).join("");
    // Kanäle mit Buchungen, aber ohne eigene Zeile (laufen über „Alle übrigen Portale“)
    const others = Object.keys(src).filter((ch) => !(ch in d.commissions) && !(d.direct_channels || []).includes(ch));
    const otherNote = others.length ? `<div class="sub" style="margin-top:6px">${t("Weitere Kanäle mit Buchungen")}: ${others.map((ch) => `<button class="lnk" data-cuse="${esc(ch)}" title="${esc(t("In die Tabelle übernehmen"))}">＋ ${esc(chn(ch))}</button> ${srcBadge(ch)}`).join(" · ")}</div>` : "";
    return `<div class="grp"><div class="gh"><div class="grow"><b>${t("Provision je Kanal")}</b>
        <span class="sub">${t("Gilt nur für Buchungen, zu denen Smoobu keine Provision liefert.")}</span></div></div>
      <div class="gb"><div class="scroll"><table class="prov"><thead><tr><th>${t("Kanal")}</th><th class="n">${t("Provision")}</th><th>${t("Provision von Smoobu (24 Monate)")}</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>
        ${otherNote}
        <div class="inline">${this.chanSelect("commissions", Object.keys(d.commissions))}</div>${this.err("commissions")}
        ${this.fld("Alle übrigen Portale", this.numIn("commission_other", 0, 50, 0.1, "%"), "", "commission_other")}</div></div>
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Direktkanäle")}</b><span class="sub">${t("Zählen als Direktvermarktung (Direkt vs. Portale).")}</span></div></div>
        <div class="gb">${this.pick("direct_channels", meta.kanaele, chn, true)}${this.err("direct_channels")}</div></div>
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Zahlung über das Portal")}</b><span class="sub">${t("Buchungen dieser Kanäle zählen nicht als offene Zahlung.")}</span></div></div>
        <div class="gb">${this.pick("payment_excluded_channels", meta.kanaele, chn, true)}${this.err("payment_excluded_channels")}</div></div>`;
  }
  // v1.18.0: variable Kosten (Deckungsbeitrag) und Preisaufschläge aus dem Smoobu-Preistool
  tabCost(meta) {
    const d = this._draft;
    const share = d.cost_grid_share || [];
    const months = MONTHS_SHORT.map((m, i) => `<label class="inline" style="gap:4px"><span class="unit" style="width:28px">${esc(t(m))}</span>
      <input type="number" data-share="${i}" min="0" max="100" step="1" value="${esc(share[i] ?? "")}" style="width:64px"><span class="unit">%</span></label>`).join("");
    const mk = Object.entries(d.channel_markups || {}).map(([ch, pct]) => `<tr><td>${esc(chn(ch))}</td>
      <td class="n"><span class="inline" style="justify-content:flex-end"><input type="number" data-mk="${esc(ch)}" min="-50" max="300" step="1" value="${esc(pct)}"><span class="unit">%</span></span></td>
      <td><button class="lnk" data-mdel="${esc(ch)}">${t("Entfernen")}</button></td></tr>`).join("");
    // Vorschau Heizkosten-Verteilung: Anteil je Monat relativ zum Januar (je Nacht)
    const days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    const wJan = HEAT_PROMILLE[0] / 31;
    const dist = MONTHS_SHORT.map((m, i) => `${t(m)} ${num((HEAT_PROMILLE[i] / days[i]) / wJan * 100, 0)} %`).join(" · ");
    return `<div class="note">${t("Variable Kosten = Kosten, die nur durch einen Aufenthalt entstehen. Deckungsbeitrag = Netto − variable Kosten. Fixkosten (Grundsteuer, Versicherung, Internet) gehören nicht hierher.")}</div>
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Je Aufenthalt")}</b></div></div><div class="gb">
        ${this.fld("Reinigung", this.numIn("cost_cleaning", 0, 1000, 0.5, "€"), "", "cost_cleaning")}
        ${this.fld("Wäsche", this.numIn("cost_laundry", 0, 1000, 0.5, "€"), "", "cost_laundry")}</div></div>
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Heizung & Warmwasser")}</b>
        <span class="sub">${t("Jahreskosten aus der Nebenkostenabrechnung. Verteilung nach Gradtagszahlen, skaliert auf die Gästenächte des Abrechnungsjahres.")}</span></div></div><div class="gb">
        ${this.fld("Heizkosten im Abrechnungsjahr", this.numIn("cost_heating_year", 0, 100000, 0.01, "€"), "", "cost_heating_year")}
        ${this.fld("Warmwasser im Abrechnungsjahr", this.numIn("cost_hot_water_year", 0, 100000, 0.01, "€"), "Im Sommer deckt die Solarthermie – gleiche Verteilung wie die Heizung.", "cost_hot_water_year")}
        ${this.fld("Abrechnungsjahr", this.numIn("cost_ref_year", 2015, 2100, 1), "", "cost_ref_year")}
        <div class="sub">${t("Kosten je Nacht relativ zum Januar")}: ${esc(dist)}</div></div></div>
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Wasser & Strom je Nacht")}</b>
        <span class="sub">${t("Strompreis je Monat = Netzanteil × Netzpreis + Rest × Wert des PV-Stroms (entgangene Einspeisevergütung).")}</span></div></div><div class="gb">
        ${this.fld("Wasser/Abwasser", this.numIn("cost_water_night", 0, 100, 0.01, "€"), "", "cost_water_night")}
        ${this.fld("Strom", this.numIn("cost_power_kwh", 0, 200, 0.1, "kWh"), "", "cost_power_kwh")}
        ${this.fld("Netzstrompreis", this.numIn("cost_grid_price", 0, 200, 0.01, "ct/kWh"), "", "cost_grid_price")}
        ${this.fld("Wert PV-Strom", this.numIn("cost_pv_value", 0, 200, 0.01, "ct/kWh"), "", "cost_pv_value")}
        ${this.fld("Netzanteil je Monat", `<div class="chips">${months}</div>`, "Netzbezug ÷ Hausverbrauch, z. B. aus dem Energie-Dashboard.", "cost_grid_share")}</div></div>
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Aufschläge je Kanal")}</b>
        <span class="sub">${t("Wie im Smoobu-Preistool: Kanalpreis = Basispreis + Aufschlag. Grundlage für Preisuntergrenzen und Empfehlungen.")}</span></div></div>
      <div class="gb"><div class="scroll"><table class="prov"><thead><tr><th>${t("Kanal")}</th><th class="n">${t("Aufschlag")}</th><th></th></tr></thead><tbody>${mk}</tbody></table></div>
        <div class="inline">${this.chanSelect("channel_markups", Object.keys(d.channel_markups || {}))}</div>${this.err("channel_markups")}
        ${this.fld("Booking.com Genius-Rabatt", this.numIn("genius_discount", 0, 50, 1, "%"), "Genius-Gäste zahlen weniger als den Kanalpreis.", "genius_discount")}
        ${this.fld("Anteil Genius-Buchungen", this.numIn("genius_share", 0, 100, 1, "%"), "Unbekannt? 100 % lassen – vorsichtige Annahme (siehe Booking.com-Extranet).", "genius_share")}
        ${(() => {
          // v1.18.0: Checkup aus den eigenen Buchungen (Booking.com markiert Genius-Gäste in der Notiz)
          const g = meta.genius_check;
          if (!g || !g.buchungen) return `<div class="sub">${t("Genius-Check: keine Booking.com-Buchungen in den letzten 24 Monaten.")}</div>`;
          const same = Number(d.genius_share) === g.anteil;
          return `<div class="note">${t("Genius-Check")}: <b>${num(g.genius)} ${t("von")} ${num(g.buchungen)}</b> ${t("Booking.com-Buchungen der letzten 24 Monate waren Genius-Gäste")} (${num(g.anteil)} %).
            ${same ? `✓ ${t("passt zur Einstellung")}` : `<button class="btn flat sm" data-genius="${g.anteil}">${t("Gemessenen Anteil übernehmen")} (${num(g.anteil)} %)</button>`}
            <div class="sub">${t("Den Rabatt selbst (10/15/20 %) liefert Booking.com nicht – bitte im Extranet unter Genius nachsehen.")}</div></div>`;
        })()}</div></div>
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Last-Minute")}</b>
        <span class="sub">${t("Standard: kein Rabatt. Nur Lücken zwischen zwei Gästen oder Nächte in schwach gebuchten Monaten bekommen einen Vorschlag – nie unter der Untergrenze.")}</span></div></div><div class="gb">
        ${this.fld("Last-Minute-Fenster", this.numIn("lastminute_days", 1, 14, 1, "Tage"), "So viele Tage vor Anreise gilt eine freie Nacht als Last-Minute.", "lastminute_days")}
        ${this.fld("Höchster Rabatt", this.numIn("lastminute_max_discount", 0, 30, 1, "%"), "", "lastminute_max_discount")}</div></div>`;
  }
  // v1.18.0: Benutzerrollen – nur Admins vergeben Rollen; alle sehen die Übersicht Rolle × Recht
  tabRights(meta) {
    const d = this._draft;
    const m = meta.rollen || { rollen: [], rechte: [] };
    const roleName = (id) => m.rollen.find((r) => r.id === id)?.name || id;
    const head = `<tr><th>${t("Recht")}</th>${m.rollen.map((r) => `<th class="n">${esc(t(r.name))}</th>`).join("")}</tr>`;
    const rows = m.rechte.map((x) => `<tr><td>${esc(t(x.name))}</td>${m.rollen.map((r) => `<td class="n">${r.rechte.includes(x.id) ? "✓" : "–"}</td>`).join("")}</tr>`).join("");
    const opts = (val, withDefault) => `${withDefault ? `<option value="" ${!val ? "selected" : ""}>${t("Standard")} (${esc(t(roleName(d.default_role)))})</option>` : ""}
      ${m.rollen.map((r) => `<option value="${r.id}" ${val === r.id ? "selected" : ""}>${esc(t(r.name))}</option>`).join("")}`;
    const own = meta.zugriff ? `<div class="note">${t("Deine Rolle")}: <b>${esc(t(meta.zugriff.rolle_name))}</b>${meta.zugriff.admin ? ` – ${t("Admins dürfen immer alles und vergeben die Rollen.")}` : ""}</div>` : "";
    const users = meta.admin ? meta.benutzer.map((u) => u.admin
      ? this.fld(u.name, `<span class="badge good">${t("Admin")}</span>`, t("HA-Admin: immer alle Rechte"))
      : this.fld(u.name, `<select data-role="${esc(u.id)}">${opts(d.user_roles?.[u.id] || "", true)}</select>`, "", `user_roles`)).join("") : "";
    return `${own}
      ${meta.admin ? `<div class="grp"><div class="gh"><div class="grow"><b>${t("Rollen der Benutzer")}</b>
        <span class="sub">${t("Gilt für die Smoobu-Seiten und -Aktionen. Normale HA-Entitäten kann HA nicht je Benutzer sperren.")}</span></div></div>
        <div class="gb">${users}${this.fld("Standardrolle", `<select data-sel="default_role">${opts(d.default_role, false)}</select>`, "Für Benutzer ohne eigene Rolle (bisheriges Verhalten: Betrieb).", "default_role")}</div></div>` : ""}
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Was darf welche Rolle?")}</b></div></div>
        <div class="gb"><div class="scroll"><table class="prov">${head}${rows}</table></div></div></div>`;
  }
  tabGeneral(meta) {
    const d = this._draft;
    const codes = meta.wohnungen.map((w) => this.fld(w.name, `<input type="text" data-code="${esc(w.id)}" maxlength="4" style="width:90px"
      value="${esc(d.apartment_codes[w.id] || "")}" placeholder="${esc(w.auto)}">`, `${t("Leer = automatisch")} (${w.auto})`, `apartment_codes.${w.id}`)).join("");
    const board = `<div class="grp"><div class="gh"><div class="grow"><b>${t("Aufgaben-Board „Wartet auf dich“")}</b>
        <span class="sub">${t("Welche Kategorien in der Übersicht erscheinen. Erledigt/Später gilt für alle Benutzer.")}</span></div></div>
      <div class="gb">${this.pick("task_categories", TASK_CATS.map(([k]) => k), (k) => t(Object.fromEntries(TASK_CATS)[k] || k))}${this.err("task_categories")}</div></div>`;
    return `${board}<div class="grp"><div class="gh"><div class="grow"><b>${t("Abruf")}</b></div></div><div class="gb">
        ${this.fld("Webhook (Echtzeit)", this.sw("use_webhook", "Webhook"), "Smoobu meldet Änderungen sofort über Nabu Casa.")}
        ${this.fld("Abfrageintervall", this.numIn("scan_interval", 1, 120, 1, "min"), "Zusätzlicher Abgleich neben dem Webhook.", "scan_interval")}
        ${this.fld("Tage Rückblick", this.numIn("days_back", 0, 365, 1, "Tage"), "", "days_back")}
        ${this.fld("Tage Vorschau", this.numIn("days_ahead", 30, 730, 1, "Tage"), "", "days_ahead")}
        ${this.fld("Details für nächste Buchungen", this.numIn("enrich_count", 0, 20, 1), "Vorname, Kurtaxe usw. für die laufende + n kommende Buchungen je Wohnung.", "enrich_count")}</div></div>
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Standardzeiten")}</b></div></div><div class="gb">
        ${this.fld("Check-in", this.timeIn("default_checkin"), "Wenn die Buchung keine Ankunftszeit hat.", "default_checkin")}
        ${this.fld("Check-out", this.timeIn("default_checkout"), "Wenn die Buchung keine Abreisezeit hat.", "default_checkout")}
        ${this.fld("Wartezeit nach Check-out", this.numIn("checkout_buffer", 0, 240, 5, "min"), "Freigabe = Abreisezeit + Wartezeit (z. B. bis Reinigungsbeginn).", "checkout_buffer")}</div></div>
      <div class="grp"><div class="gh"><div class="grow"><b>${t("Auswertungen")}</b></div></div><div class="gb">
        ${this.fld("Jahre Historie", this.numIn("history_years", 1, 5, 1, "Jahre"), "Wird ignoriert, wenn „Daten abrufen seit“ gesetzt ist.", "history_years")}
        ${this.fld("Daten abrufen seit", `<input type="date" data-txt="history_since" value="${esc(d.history_since || "")}">${d.history_since ? `<button class="lnk" data-clear="history_since">${t("Leeren")}</button>` : ""}`,
          "Leer = „Jahre Historie“ gilt. Mindestens ab 01.01. des Vorjahres.", "history_since")}</div></div>
      ${codes ? `<div class="grp"><div class="gh"><div class="grow"><b>${t("Wohnungskürzel")}</b><span class="sub">${t("Höchstens 4 Buchstaben/Ziffern, eindeutig über alle Konten.")}</span></div></div><div class="gb">${codes}</div></div>` : ""}`;
  }
  body(res) {
    if (!res.erlaubt) return `<div class="head"><h2>${esc(t(this._config.title))}</h2></div><div class="empty">${t("Keine Berechtigung für die Smoobu-Einstellungen.")}</div>`;
    const { meta } = res;
    const tab = this._state.tab;
    const errTabs = new Set(Object.keys(this._state.errors).map((k) => SET_FIELD_TAB(k.split(".")[0])));
    const tabs = SET_TABS.map(([k, l]) => `<button data-tab="${k}" aria-pressed="${tab === k}">${esc(t(l))}${errTabs.has(k) ? `<span class="e"></span>` : ""}</button>`).join("");
    const konten = res.konten.length > 1 ? `<select data-entry>${res.konten.map((k) => `<option value="${esc(k.entry_id)}" ${k.entry_id === res.entry_id ? "selected" : ""}>${esc(k.title)}</option>`).join("")}</select>` : "";
    const content = tab === "assistent" ? this.tabAssist(meta) : tab === "provisionen" ? this.tabProv(meta) : tab === "kosten" ? this.tabCost(meta)
      : tab === "rechte" ? this.tabRights(meta)
      : tab === "allgemein" ? this.tabGeneral(meta) : this.tabPush(meta);
    const n = this.dirty ? Object.keys(this.changes()).length : 0;
    const status = this._state.saving ? t("Speichere … die Integration lädt danach neu.")
      : n ? `${n} ${t(n === 1 ? "ungespeicherte Änderung" : "ungespeicherte Änderungen")}` : t("Alles gespeichert.");
    return `<div class="head"><h2>${esc(t(this._config.title))}</h2>${konten}</div><nav class="stabs">${tabs}</nav>${content}
      <div class="foot"><span class="grow ${n ? "dirty" : ""}">${esc(status)}</span>
        <button class="btn flat" data-reset ${!n || this._state.saving ? "disabled" : ""}>${t("Verwerfen")}</button>
        <button class="btn" data-save ${!n || this._state.saving ? "disabled" : ""}>${t("Speichern")}</button></div>`;
  }
  // Nur Fußzeile aktualisieren (bei Texteingaben – ohne die Felder neu zu zeichnen)
  refreshFoot() {
    const n = this.dirty ? Object.keys(this.changes()).length : 0;
    const g = this.$(".foot .grow");
    if (!g) return;
    g.textContent = n ? `${n} ${t(n === 1 ? "ungespeicherte Änderung" : "ungespeicherte Änderungen")}` : t("Alles gespeichert.");
    g.classList.toggle("dirty", !!n);
    this.$$(".foot button").forEach((b) => { b.disabled = !n || this._state.saving; });
  }
  bind(root) {
    if (!this._draft) return;
    const d = this._draft;
    const redraw = () => this.render();
    root.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => this.setState({ tab: b.dataset.tab })));
    root.querySelectorAll("[data-sw]").forEach((b) => b.addEventListener("click", () => { d[b.dataset.sw] = !d[b.dataset.sw]; redraw(); }));
    root.querySelectorAll("[data-pick]").forEach((b) => b.addEventListener("click", () => {
      const k = b.dataset.pick, v = b.dataset.v, list = d[k] || [];
      d[k] = list.includes(v) ? list.filter((x) => x !== v) : [...list, v];
      redraw();
    }));
    root.querySelectorAll("[data-rm]").forEach((b) => b.addEventListener("click", () => {
      d[b.dataset.rm] = (d[b.dataset.rm] || []).filter((x) => x !== b.dataset.v); redraw();
    }));
    root.querySelectorAll("[data-addto]").forEach((inp) => inp.addEventListener("keydown", (e) => {
      if (e.key !== "Enter") return;
      const v = inp.value.trim(), k = inp.dataset.addto;
      if (v && !(d[k] || []).includes(v)) d[k] = [...(d[k] || []), v];
      redraw();
      this.$(`[data-addto="${k}"]`)?.focus();
    }));
    root.querySelectorAll("[data-num]").forEach((inp) => inp.addEventListener("input", () => {
      d[inp.dataset.num] = inp.value === "" ? inp.value : Number(inp.value); this.refreshFoot();
    }));
    root.querySelectorAll("[data-txt]").forEach((inp) => inp.addEventListener("input", () => {
      d[inp.dataset.txt] = inp.dataset.txt === "history_since" ? inp.value || null : inp.value; this.refreshFoot();
    }));
    root.querySelectorAll("[data-sel]").forEach((s) => s.addEventListener("change", () => { d[s.dataset.sel] = s.value || null; redraw(); }));
    root.querySelectorAll("[data-clear]").forEach((b) => b.addEventListener("click", () => { d[b.dataset.clear] = null; redraw(); }));
    root.querySelectorAll("[data-code]").forEach((inp) => inp.addEventListener("input", () => {
      d.apartment_codes = { ...d.apartment_codes, [inp.dataset.code]: inp.value }; this.refreshFoot();
    }));
    // Provisionen: Prozent, entfernen; hinzufügen über das Kanal-Dropdown (data-chadd)
    root.querySelectorAll("[data-comm]").forEach((inp) => inp.addEventListener("input", () => {
      d.commissions = { ...d.commissions, [inp.dataset.comm]: inp.value === "" ? "" : Number(inp.value) }; this.refreshFoot();
    }));
    root.querySelectorAll("[data-cdel]").forEach((b) => b.addEventListener("click", () => {
      const c = { ...d.commissions }; delete c[b.dataset.cdel]; d.commissions = c; redraw();
    }));
    // v1.18.0: Kanal aus dem Dropdown übernehmen. Provision startet mit „Alle übrigen Portale“
    // (bisher gerechneter Satz, Ergebnis ändert sich erst beim Anpassen), Aufschlag mit 0 %, Listen hängen an.
    const addChannel = (target, name) => {
      if (!name) return;
      if (target === "commissions") { if (!(name in d.commissions)) d.commissions = { ...d.commissions, [name]: d.commission_other }; }
      else if (target === "channel_markups") { if (!(name in (d.channel_markups || {}))) d.channel_markups = { ...d.channel_markups, [name]: 0 }; }
      else if (!(d[target] || []).includes(name)) d[target] = [...(d[target] || []), name];
      redraw();
    };
    root.querySelectorAll("[data-chadd]").forEach((sel) => sel.addEventListener("change", () => addChannel(sel.dataset.chadd, sel.value)));
    root.querySelectorAll("[data-cuse]").forEach((b) => b.addEventListener("click", () => addChannel("commissions", b.dataset.cuse)));
    root.querySelector("[data-genius]")?.addEventListener("click", (e) => { d.genius_share = Number(e.target.dataset.genius); redraw(); });
    // Benutzerrollen (nur Admins sehen die Auswahl); leer = Standardrolle
    root.querySelectorAll("[data-role]").forEach((sel) => sel.addEventListener("change", () => {
      const roles = { ...(d.user_roles || {}) };
      if (sel.value) roles[sel.dataset.role] = sel.value; else delete roles[sel.dataset.role];
      d.user_roles = roles; this.refreshFoot();
    }));
    // Kosten & Preise: Netzanteil je Monat, Aufschläge (entfernen; hinzufügen über das Kanal-Dropdown)
    root.querySelectorAll("[data-share]").forEach((inp) => inp.addEventListener("input", () => {
      const list = [...(d.cost_grid_share || [])];
      list[Number(inp.dataset.share)] = inp.value === "" ? "" : Number(inp.value);
      d.cost_grid_share = list; this.refreshFoot();
    }));
    root.querySelectorAll("[data-mk]").forEach((inp) => inp.addEventListener("input", () => {
      d.channel_markups = { ...d.channel_markups, [inp.dataset.mk]: inp.value === "" ? "" : Number(inp.value) }; this.refreshFoot();
    }));
    root.querySelectorAll("[data-mdel]").forEach((b) => b.addEventListener("click", () => {
      const c = { ...d.channel_markups }; delete c[b.dataset.mdel]; d.channel_markups = c; redraw();
    }));
    root.querySelector("[data-entry]")?.addEventListener("change", async (e) => {
      if (this.dirty && !(await confirmDialog(t("Ungespeicherte Änderungen verwerfen?")))) { e.target.value = this._data.entry_id; return; }
      this._config = { ...this._config, entry_id: e.target.value };
      this._draft = null; this._data = null; this._state.errors = {};
      super._reload();
    });
    root.querySelector("[data-reset]")?.addEventListener("click", () => {
      this._draft = clone(this._data.werte); this.setState({ errors: {} });
    });
    root.querySelector("[data-save]")?.addEventListener("click", () => this.save());
    // Datenschutz-Stufe: feste Stufe setzt die Einzelschalter auf deren Voreinstellung, damit
    // „Individuell“ danach mit der zuletzt gewählten Stufe beginnt
    root.querySelectorAll("[data-privacy]").forEach((b) => b.addEventListener("click", () => {
      const lvl = b.dataset.privacy;
      const preset = this._data?.meta?.datenschutz_stufen?.[lvl];
      if (preset) Object.assign(d, preset);
      d.ai_privacy = lvl; redraw();
    }));
    root.querySelectorAll("[data-names]").forEach((inp) => inp.addEventListener("input", () => {
      d[inp.dataset.names] = inp.value.split(/[,;]/).map((x) => x.trim()).filter(Boolean); this.refreshFoot();
    }));
    root.querySelectorAll("[data-prompt]").forEach((b) => b.addEventListener("click", async () => {
      const probe = b.dataset.prompt === "probe";
      b.disabled = true;
      try {
        const res = await this.store.ws("smoobu/assistant/preview", { entry_id: this._data.entry_id, ...(probe ? { probelauf: true } : {}) }, { cache: false });
        promptDialog(probe ? "Probelauf: so ginge es jetzt an die KI" : "Zuletzt an die KI gesendet", res);
      } catch (e) {
        toast(`${t("Fehler")}: ${e?.message || e}`);
      } finally { b.disabled = false; }
    }));
  }
  async save() {
    const changes = this.changes();
    if (!Object.keys(changes).length) return;
    this.setState({ saving: true, errors: {} });
    try {
      const r = await this.store.ws("smoobu/settings/set", { entry_id: this._data.entry_id, changes }, { cache: false });
      if (!r.ok) {
        const first = Object.keys(r.fehler)[0];
        this.setState({ saving: false, errors: r.fehler, tab: first ? SET_FIELD_TAB(first.split(".")[0]) : this._state.tab });
        toast(t("Bitte die markierten Felder prüfen."));
        return;
      }
      this._data.werte = r.werte;
      this._draft = clone(r.werte);
      this.setState({ saving: false });
      toast(t("Einstellungen gespeichert."));
      // Integration wurde neu geladen → Datenabo erneuern, alle Karten laden neu
      this.store.resubscribe();
    } catch (e) {
      this.setState({ saving: false });
      toast(`${t("Fehler")}: ${e?.message || e}`);
    }
  }
  getCardSize() { return 10; }
}

// ===========================================================================
// Registrierung
// ===========================================================================
const CARDS = [
  ["smoobu-header-card", SmoobuHeaderCard, "Smoobu Kopfleiste", "Seiten-Navigation, Wohnungsauswahl und Hell/Dunkel/System"],
  ["smoobu-overview-card", SmoobuOverviewCard, "Smoobu Übersicht", "Status, Gäste, Kennzahlen, Lücken, offene Zahlungen"],
  ["smoobu-timeline-card", SmoobuTimelineCard, "Smoobu Belegungsplan", "Belegung mit Preisen und Mindestaufenthalt; sperren und Preise setzen"],
  ["smoobu-bookings-card", SmoobuBookingsCard, "Smoobu Buchungen", "Buchungsliste mit Suche, Filtern, Summen und CSV-Export"],
  ["smoobu-analytics-card", SmoobuAnalyticsCard, "Smoobu Finanzen", "Umsatz, Kosten und Kennzahlen je Kanal, frei filterbar mit Vergleich"],
  ["smoobu-stats-card", SmoobuStatsCard, "Smoobu Statistik", "Analyse-Werkbank: Kennzahlen mit Vergleich, Buchungstempo mit Prognose, Saison-Matrix"],
  ["smoobu-inbox-card", SmoobuInboxCard, "Smoobu Posteingang", "Nachrichten der Gäste lesen und beantworten"],
  ["smoobu-assistant-card", SmoobuAssistantCard, "Smoobu Assistent", "KI-Assistent: Wissensdatenbank, Lernbeispiele, Vorschläge"],
  ["smoobu-settings-card", SmoobuSettingsCard, "Smoobu Einstellungen", "Benachrichtigungen, KI-Assistent, Provisionen und Abruf direkt im Dashboard ändern"],
];
for (const [tag, cls] of CARDS) if (!customElements.get(tag)) customElements.define(tag, cls);
if (!customElements.get("smoobu-booking-dialog")) customElements.define("smoobu-booking-dialog", SmoobuBookingDialog);
window.customCards = window.customCards || [];
for (const [type, , name, description] of CARDS) {
  if (!window.customCards.some((c) => c.type === type)) window.customCards.push({ type, name, description, preview: false });
}
console.info(`%c SMOOBU-CARDS %c ${SMOOBU_CARDS_VERSION} `, "background:#17211D;color:#fff;padding:2px 4px;border-radius:3px 0 0 3px",
  "background:#2F6B4F;color:#fff;padding:2px 4px;border-radius:0 3px 3px 0");

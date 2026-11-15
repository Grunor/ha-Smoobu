<p align="center"><img src="custom_components/smoobu/brand/icon@2x.png" width="128" alt="Smoobu for Home Assistant"></p>

# Smoobu für Home Assistant / Smoobu for Home Assistant

**[🇩🇪 Deutsch](#deutsch) · [🇬🇧 English](#english)**

---

## Deutsch

Custom-Integration für [Smoobu](https://www.smoobu.com/), den Channel Manager für Ferienwohnungen.
Sie verbindet Home Assistant direkt mit der Smoobu-API und stellt Buchungen, Gästedaten, Belegung und Statistik als Entitäten bereit. Über einen Webhook kommen Änderungen in Echtzeit an.

> Nicht offiziell. Dieses Projekt steht in keiner Verbindung zu Smoobu GmbH.

---

### Inhalt

- [Warum diese Integration?](#warum-diese-integration)
- [Funktionen](#funktionen)
- [Voraussetzungen](#voraussetzungen)
- [Smoobu-API-Schlüssel erstellen](#smoobu-api-schlüssel-erstellen)
- [Installation](#installation)
- [Einrichtung](#einrichtung)
- [Optionen](#optionen)
- [Entitäten](#entitäten)
- [Aktionen](#aktionen)
- [Dashboard-Karten](#dashboard-karten-ab-180)
- [Events](#events)
- [Beispiele](#beispiele)
- [Webhook](#webhook)
- [Datenschutz und Sicherheit](#datenschutz-und-sicherheit)
- [Fehlerbehebung](#fehlerbehebung)
- [Technische Details](#technische-details)
- [Changelog](#changelog)

---

### Warum diese Integration?

- **Der iCal-Export von Smoobu enthält keine vollständigen Gastnamen mehr.** Wer den Smoobu-Kalender per iCal (oder über einen Google-Kalender-Import) einbindet, sieht nur noch Platzhalter.
- **Die alte API-Anmeldung per `Api-Key`-Header wurde von Smoobu zum 31.10.2026 abgeschaltet.** Seitdem muss jede Anfrage einzeln per HMAC-SHA256 signiert werden. Mit der `rest:`-Integration von Home Assistant ist das nicht möglich, weil Jinja-Templates keine HMAC-Signatur berechnen können.

Diese Integration übernimmt die Signatur und stellt alle Daten nativ in Home Assistant bereit.

---

### Funktionen

- 📅 **Belegungskalender je Wohnung** mit vollem Gastnamen, Kanal, Personen, Preis und Kontaktdaten
- 👤 **Sensoren für aktuelle und nächste Buchung:** Gastname, Vorname, Personenzahl, Anreise, Abreise
- 🏠 **Binärsensoren:** belegt, Anreise heute, Abreise heute, Gästewechsel heute, Hund beim aktuellen/nächsten Gast
- 📊 **Statistik:** Buchungen, Auslastung und Umsatz 30 Tage, Umsatz Monat/Jahr/Vorjahr (anteilig nach Nächten), Preis je Buchung, offene Zahlungen
- ⚡ **Echtzeit-Webhook:** Nabu Casa Cloudhook oder externe HTTPS-URL, wird automatisch bei Smoobu registriert
- 🔔 **Event `smoobu_event`** bei neuer, geänderter oder stornierter Buchung und bei neuer Gastnachricht
- 🛠️ **Aktionen:** Buchungen abfragen, einzelne Buchung abrufen, Nachrichten lesen und senden, Zeiträume sperren, Sperren löschen, Preise und Mindestaufenthalt setzen, Ankunfts-/Abreisezeit und Notiz ändern
- 🧭 **Kanal-Auswertung:** ein Sensor je Kanal (Portale und Direktkanäle) mit Umsatz, Netto, Kosten, Nächten, Ø Aufenthalt, Ø Personen, Ø Vorlaufzeit, Stornoquote – Monat, Jahr, bis heute, Vorjahr
- 🎚️ **Filter für Dashboards ohne Templates:** Auswahl-Entitäten Kanal, Zeitraum, Vergleich + Auswertungs-Sensoren
- 🔮 **Prognose Jahresende:** gebucht + Nachbuchungen wie im Vorjahr
- 🖥️ **Eigene Dashboard-Karten:** Übersicht, Belegungsplan mit Preisen, Buchungsliste, Finanzen, Posteingang – werden automatisch geladen
- 🔐 **HMAC-SHA256-Signatur** nach aktueller Smoobu-Spezifikation
- 🌍 Deutsch und Englisch, Einrichtung komplett über die Oberfläche, Diagnose-Download mit geschwärzten Gästedaten

---

### Voraussetzungen

- Home Assistant **2025.2** oder neuer (lokal getestet mit 2026.2)
- Smoobu-Konto mit API-Zugang
- Für den Echtzeit-Webhook entweder **Home Assistant Cloud (Nabu Casa)** oder eine **externe HTTPS-URL** (Smoobu akzeptiert nur HTTPS). Ohne beides arbeitet die Integration nur per Abfrageintervall.

---

### Smoobu-API-Schlüssel erstellen

1. In Smoobu anmelden.
2. **Erweitert → API-Schlüssel** öffnen und oben rechts **Neu erstellen** klicken.
3. Optional ein **Label** vergeben (nur ein Name zum Wiedererkennen, z. B. „Home Assistant“) und bestätigen.
4. Im folgenden Fenster das **Secret** kopieren (in der deutschen Oberfläche teils als „Verschlüsselung“ beschriftet). **Es wird nur einmal angezeigt.**
5. Den **API-Schlüssel** aus der Spalte **„Schlüssel“ (Key)** in der Liste kopieren. Das Label ist **nicht** der Schlüssel.

| Feld in Home Assistant | Wert aus Smoobu |
|---|---|
| API-Schlüssel | Spalte „Schlüssel“ (Key) in der Liste |
| Secret | Secret aus dem Fenster nach dem Erstellen |

> Für Gastnamen, E-Mail und Telefon muss der Schlüssel Zugriff auf Gästedaten haben. Bietet Smoobu beim Schlüssel eine Option für Gästedaten („Guest Data (PII)“) an, diese aktivieren. Zeigt `binary_sensor.smoobu_gastdaten_fehlen` „an“, fehlt diese Berechtigung.

---

### Installation

#### Über den Marketplace (HACS) – empfohlen

1. In Home Assistant **Marketplace** (bzw. HACS) öffnen.
2. Oben rechts **⋮ → Benutzerdefinierte Repositories**.
3. Repository `https://github.com/Grunor/ha-Smoobu` eintragen, Kategorie **Integration**, hinzufügen.
4. **Smoobu** suchen und herunterladen.
5. Home Assistant **neu starten**.

Updates erscheinen danach automatisch als normales Update in Home Assistant.

#### Manuell

1. Beim neuesten [Release](https://github.com/Grunor/ha-Smoobu/releases) die Datei `smoobu.zip` herunterladen und entpacken.
2. Den Inhalt nach `/config/custom_components/smoobu` kopieren, z. B. per Samba oder Studio Code Server.
3. Home Assistant **neu starten**.

---

### Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
2. **Smoobu** auswählen.
3. **API-Schlüssel** und **Secret** eintragen.

Die Integration prüft den Schlüssel, legt für jede Smoobu-Wohnung ein Gerät an und registriert, falls möglich, den Webhook bei Smoobu.

Wird der Schlüssel später ungültig (gelöscht, Secret neu erzeugt), meldet Home Assistant eine **Neu-Anmeldung**. Dort neuen Schlüssel und neues Secret eintragen, eine Neueinrichtung ist nicht nötig.

---

### Optionen

Unter **Einstellungen → Geräte & Dienste → Smoobu → Konfigurieren**:

| Option | Standard | Bedeutung |
|---|---|---|
| Abfrageintervall | 10 min | Regelmäßige Abfrage als Rückfall zum Webhook |
| Echtzeit-Webhook verwenden | an | Webhook anlegen und bei Smoobu registrieren. Abschalten entfernt die Registrierung. |
| Standard-Check-in | 16:00 | Gilt, wenn in der Buchung keine Ankunftszeit steht |
| Standard-Check-out | 11:00 | Gilt, wenn in der Buchung keine Abreisezeit steht (Freigabezeit, ohne Puffer) |
| Kanäle mit Zahlung über das Portal | Airbnb, Booking.com | Buchungen dieser Kanäle zählen nicht als offene Zahlung |
| Puffer nach Smoobu-Abreisezeit | 0 min | Steht in der Buchung eine Abreisezeit, gilt die Wohnung erst nach dieser Zeit + Puffer als frei |
| Rückblick | 30 Tage | Wie weit zurück Buchungen geladen werden |
| Vorschau | 365 Tage | Wie weit voraus Buchungen geladen werden |
| Detaildaten für die nächsten n Buchungen | 3 | Laufende und nächste n Buchungen je Wohnung werden zusätzlich einzeln abgerufen (Vor-/Nachname, Kurtaxe, Preisdetails) |

Nach dem Speichern wird die Integration automatisch neu geladen.

---

### Entitäten

Je Smoobu-Wohnung entsteht ein Gerät **„Smoobu &lt;Wohnungsname&gt;“**, zusätzlich ein Gerät **„Smoobu“** für das Konto.

**Benennung:** `<domain>.smoobu_<wohnungsname>_<entität>`. Der Wohnungsname kommt aus Smoobu, der Entitätsteil aus der Systemsprache von Home Assistant. Bei mehreren Wohnungen bekommt jede ihren eigenen Satz Entitäten. Die Beispiele unten gelten für eine Wohnung namens „Ferienwohnung“ bei deutscher Systemsprache. Bei englischer Systemsprache heißen die Entitäten englisch (siehe [English](#english)).

#### Je Wohnung

| Entität | Beispiel-ID | Inhalt |
|---|---|---|
| Kalender | `calendar.smoobu_ferienwohnung_belegung` | Alle Buchungen. Titel = Gastname, mit 🐕 bei Hund (blockierte Zeiträume: „Blockiert“). Beginn = Anreise + Check-in-Zeit, Ende = Abreise + Check-out-Zeit. |
| Belegt | `binary_sensor.smoobu_ferienwohnung_belegt` | An von der Check-in-Zeit bis zur Freigabe (Abreisezeit + Puffer bzw. Standard-Check-out) |
| Anreise heute | `binary_sensor.smoobu_ferienwohnung_anreise_heute` | Heute reist ein Gast an |
| Abreise heute | `binary_sensor.smoobu_ferienwohnung_abreise_heute` | Heute reist ein Gast ab |
| Gästewechsel heute | `binary_sensor.smoobu_ferienwohnung_gastewechsel_heute` | Abreise und Anreise am selben Tag |
| Hund aktueller Gast | `binary_sensor.smoobu_ferienwohnung_hund_aktueller_gast` | Laufende Buchung erwähnt einen Hund/ein Haustier (Zusatzleistung oder Notiz). Attribut `hund_hinweis` = Fundstelle |
| Hund nächster Gast | `binary_sensor.smoobu_ferienwohnung_hund_naechster_gast` | Wie oben für die nächste Buchung |
| Aktueller Gast | `sensor.smoobu_ferienwohnung_aktueller_gast` | Voller Name des aktuellen Gastes |
| Aktueller Vorname | `sensor.smoobu_ferienwohnung_aktueller_vorname` | Vorname des aktuellen Gastes |
| Aktuelle Personen | `sensor.smoobu_ferienwohnung_aktuelle_personen` | Erwachsene + Kinder, 0 wenn frei |
| Nächster Gast | `sensor.smoobu_ferienwohnung_nachster_gast` | Voller Name des nächsten Gastes |
| Nächster Vorname | `sensor.smoobu_ferienwohnung_nachster_vorname` | Vorname des nächsten Gastes |
| Nächste Personen | `sensor.smoobu_ferienwohnung_nachste_personen` | Personenzahl der nächsten Buchung |
| Nächste Anreise | `sensor.smoobu_ferienwohnung_nachste_anreise` | Zeitstempel der nächsten Anreise |
| Nächste Abreise | `sensor.smoobu_ferienwohnung_nachste_abreise` | Freigabe der laufenden Buchung, sonst der nächsten |
| Buchungen 30 Tage | `sensor.smoobu_ferienwohnung_buchungen_30_tage` | Anzahl Anreisen in den nächsten 30 Tagen, Liste im Attribut `buchungen` |
| Auslastung 30 Tage | `sensor.smoobu_ferienwohnung_auslastung_30_tage` | Belegte Nächte in % (inkl. Blockierungen) |
| Umsatz 30 Tage | `sensor.smoobu_ferienwohnung_umsatz_30_tage` | Summe der Buchungspreise der Anreisen in den nächsten 30 Tagen |
| Preis aktueller Gast | `sensor.smoobu_ferienwohnung_preis_aktueller_gast` | Buchungspreis der laufenden Buchung. Attribute: `aufschluesselung` (Preiselemente), `preis_pro_nacht`, `anzahlung`, `offen`, `kurtaxe` … |
| Preis nächster Gast | `sensor.smoobu_ferienwohnung_preis_nachster_gast` | Wie oben für die nächste Buchung |
| Umsatz Monat | `sensor.smoobu_ferienwohnung_umsatz_monat` | Umsatz des laufenden Monats, Buchungspreis **anteilig nach Nächten**. Attribute: `davon_bis_heute`, `vormonat`, `vorjahresmonat` |
| Umsatz Jahr | `sensor.smoobu_ferienwohnung_umsatz_jahr` | Umsatz des laufenden Jahres (gebucht). Attribute: `davon_bis_heute`, `gebucht_ab_heute`, `monate`, `monate_vorjahr`, `vorjahr_gesamt` |
| Umsatz Vormonat / Folgemonat | `sensor.smoobu_ferienwohnung_umsatz_vormonat` / `…_umsatz_folgemonat` | Umsatz des Vor- bzw. Folgemonats. Attribute: `vorjahresmonat`, `veraenderung_vorjahr_prozent`, `auslastung`, `auslastung_vorjahr`, `gaeste_naechte`, `gesperrt_naechte` |
| Auslastung Monat | `sensor.smoobu_ferienwohnung_auslastung_monat` | Auslastung des laufenden Monats in %, **nur Gäste-Nächte**. Attribute: `vormonat`, `folgemonat`, `vorjahresmonat`, `monate`, `monate_vorjahr` |
| Gesperrte Nächte Monat | `sensor.smoobu_ferienwohnung_gesperrte_nachte_monat` | Vom Gastgeber gesperrte Nächte im laufenden Monat (separat von der Auslastung). Attribute: `monate`, `monate_vorjahr`, `monate_prozent`, `jahr_gesamt`, `vorjahr_gesamt` |
| Umsatz Vorjahr | `sensor.smoobu_ferienwohnung_umsatz_vorjahr` | Umsatz des Vorjahres |
| Offene Zahlungen | `sensor.smoobu_ferienwohnung_offene_zahlungen` | Laufende/kommende Buchungen mit offenem Betrag (Preis − bezahlte Anzahlung). Portal-Kanäle aus den Optionen (Standard Airbnb, Booking.com) zählen nicht. Attribute: `buchungen` (mit `offen`), `offener_betrag` |

#### Konto (Diagnose)

| Entität | Beispiel-ID | Inhalt |
|---|---|---|
| Letzte Aktualisierung | `sensor.smoobu_letzte_aktualisierung` | Zeitpunkt der letzten erfolgreichen Abfrage |
| Letztes Ereignis | `sensor.smoobu_letztes_ereignis` | Letzte Webhook-Aktion (z. B. `newReservation`) mit Buchungs-ID und Gast |
| Webhook | `sensor.smoobu_webhook` | `registriert`, `manuell` (URL muss in Smoobu eingetragen werden) oder `aus`. Attribut `url`. |
| Gastdaten fehlen | `binary_sensor.smoobu_gastdaten_fehlen` | An, wenn Smoobu keine Gastnamen liefert (PII-Berechtigung fehlt) |

#### Einzelne Buchungsfelder (aktueller und nächster Gast)

Jedes Feld der laufenden bzw. nächsten Buchung gibt es zusätzlich als eigene Entität, z. B. `sensor.smoobu_ferienwohnung_aktueller_gast_e_mail` oder `binary_sensor.smoobu_ferienwohnung_nachster_gast_preis_bezahlt`.

| Feld | aktiv | Feld | aktiv |
|---|---|---|---|
| Kanal, Sprache, E-Mail, Telefon | ✅ | Buchungs-ID, Referenz-ID, Gast-ID, Buchungstyp | ⬜ |
| Erwachsene, Kinder, Nächte | ✅ | Personen | ⬜ |
| Check-in-Zeit, Check-out-Zeit | ✅ | Gäste-App (Link) | ⬜ |
| Anreise (nur aktueller Gast), Abreise | ✅ | Freigabe | ⬜ |
| Anzahlung, offener Betrag | ✅ | Kaution, Kurtaxe | ⬜ |
| Notiz, Assistent-Notiz (voller Text im Attribut `text`) | ✅ | Erstellt, Geändert | ⬜ |
| Preis bezahlt, Anzahlung bezahlt (Binärsensoren) | ✅ | Kaution bezahlt | ⬜ |

⬜ = angelegt, aber deaktiviert (in HA unter Entität → Einstellungen aktivierbar). **Hinweis:** Kontaktdaten und Notizen landen als Entitäten in der Historie von Home Assistant.

#### Preise & Verfügbarkeit (Smoobu-Tagespreise, 60 Tage)

| Entität | Beispiel-ID | Inhalt |
|---|---|---|
| Preis heute / morgen | `sensor.smoobu_ferienwohnung_preis_heute` / `…_preis_morgen` | Tagespreis laut Smoobu. Attribute: `preise_60_tage`, `mindestaufenthalt_60_tage`, `verfuegbar` |
| Mindestaufenthalt heute | `sensor.smoobu_ferienwohnung_mindestaufenthalt_heute` | Nächte |
| Nächster freier Tag | `sensor.smoobu_ferienwohnung_nachster_freier_tag` | Erster buchbarer Tag ab heute |
| Freie Nächte 30 Tage | `sensor.smoobu_ferienwohnung_freie_nachte_30_tage` | Anzahl buchbarer Nächte |
| Nächste Lücke | `sensor.smoobu_ferienwohnung_nachste_lucke` | Beginn der nächsten freien Lücke zwischen zwei Belegungen. Attribute: `bis`, `naechte`, `mindestaufenthalt`, `buchbar`, `alle_luecken_60_tage` |

#### Nachrichten

| Entität | Beispiel-ID | Inhalt |
|---|---|---|
| Letzte Gästenachricht | `sensor.smoobu_letzte_gastenachricht` | Text der letzten Nachricht (per Webhook `newMessage` geladen, übersteht Neustarts). Attribute: `text`, `betreff`, `absender`, `gast`, `buchungs_id`, `empfangen` |

#### Direktvermarktung vs. Portale, Nettoumsatz

Brutto = Buchungspreis laut Smoobu. Provision = Wert, den Smoobu zur Buchung liefert (`commission-included`, bei Airbnb und Booking.com meist vorhanden), sonst der in den Optionen eingestellte %-Satz des Kanals. Die Booking.com-Zahlungsgebühr („Payment charge“) wird aus der Buchung gelesen. Netto = Brutto − Provision − Zahlungsgebühr, anteilig nach Nächten.

| Entität | Beispiel-ID | Inhalt |
|---|---|---|
| Nettoumsatz Monat / Jahr | `sensor.smoobu_ferienwohnung_nettoumsatz_monat` / `…_jahr` | Netto; Attribute `brutto`, `provision`, `zahlungsgebuehren`, `kostenquote_prozent`, `davon_bis_heute`, `vorjahr_gesamt`, `vorjahr_bis_heute`, `veraenderung_vorjahr_bis_heute_prozent`, `monate`, `monate_vorjahr`, `kanaele` |
| Provision & Gebühren Jahr | `sensor.smoobu_ferienwohnung_provision_gebuhren_jahr` | Summe Provision + Zahlungsgebühren; `je_kanal`, `vorjahr`, `vorjahr_bis_heute`, Kostenquote |
| Umsatz Direkt / Portale Jahr | `sensor.smoobu_ferienwohnung_umsatz_direkt_jahr` / `…_umsatz_portale_jahr` | Brutto der Gruppe; `netto`, `buchungen`, `naechte`, `netto_pro_nacht`, `anteil_prozent`, `bis_heute`, `vorjahr`, `vorjahr_bis_heute`, Veränderung, `monate`, `monate_vorjahr` |
| Direktanteil Jahr | `sensor.smoobu_ferienwohnung_direktanteil_jahr` | % am Bruttoumsatz; `anteil_naechte_prozent`, `vorjahr_prozent`, `veraenderung_prozentpunkte`, `ersparnis_direkt` (Direktumsatz × Kostenquote der Portale), `kanaele` / `kanaele_vorjahr` / `…_bis_heute` je Kanal (Brutto, Netto, Kosten, Buchungen, Nächte, Netto/Nacht, Anteil) |

Je Gast zusätzlich: `…_aktueller_gast_kanalgruppe` (Direkt/Portal), `…_provision`, `…_nettopreis`; die Preis-Sensoren haben die Attribute `kanal_gruppe`, `provision`, `provision_quelle`, `zahlungsgebuehr`, `netto`, `kostenquote_prozent`.

**Optionen → Schritt „Provisionen“:** % je Kanal (Standard Airbnb 15,5 · Booking.com 15 · FeWo-direkt 8 · Website 0 · Direktbuchung 0), sonstige Portale (15), weitere Kanäle als `Kanal=Prozent; …`, Direktkanäle (Standard: Direct booking, Website).

#### Kanäle, Auswertung mit Filtern, Prognose (ab 1.7.0)

**Ein Sensor je Kanal** entsteht automatisch, sobald ein Kanal in den Buchungen vorkommt (z. B. `sensor.smoobu_apartment_kanal_booking_com`). Zustand = Brutto laufendes Jahr. Attribute flach für Kacheln: `netto`, `kosten`, `kostenquote_prozent`, `naechte`, `auslastung_prozent`, `buchungen`, `stornos`, `stornoquote_prozent`, `netto_pro_nacht`, `aufenthalt_schnitt`, `personen_schnitt`, `vorlauf_schnitt`, `bis_heute_brutto`, `veraenderung_vorjahr_bis_heute_prozent`, `prognose_jahr`. Dazu alle Kennzahlen je Zeitraum (`jahr`, `bis_heute`, `vorjahr`, `vorjahr_bis_heute`, `monat`, `vormonat`, `folgemonat`, `vorjahresmonat`, `letzte_12_monate`) und Monatswerte (`monate`, `monate_netto`, `monate_vorjahr`, `monate_vorjahr_netto`).

**Filter:** Drei Auswahl-Entitäten je Wohnung – `select.…_auswertung_kanal` (Alle Kanäle, Direkt, Portale, jeder Kanal), `select.…_auswertung_zeitraum` (laufender Monat, Vormonat, Folgemonat, laufendes Jahr, Jahr bis heute, Vorjahr, letzte/nächste 12 Monate, gesamt) und `select.…_auswertung_vergleich` (Vorjahr, Vorperiode, kein). Die Sensoren `sensor.…_auswertung_*` (Brutto, Netto, Kosten, Kostenquote, Nächte, Auslastung, Buchungen, Stornoquote, Netto pro Nacht, Aufenthaltsdauer, Vorlaufzeit, Personen je Buchung, Direktanteil) zeigen sofort die Werte der Auswahl, jeweils mit `vergleichswert` und `veraenderung_prozent` bzw. `veraenderung_punkte`. Die Auswahl übersteht Neustarts.

**Prognose:** `sensor.…_prognose_jahr` = gebuchter Jahresumsatz + Umsatz, der im Vorjahr ab dem gleichen Stichtag noch nachgebucht wurde (aus dem Erstellungsdatum der Buchungen).

Bezugsgrößen: Umsatz und Nächte werden anteilig nach Nächten gezählt. Buchungen, Stornos, Ø Aufenthalt, Ø Personen und Ø Vorlaufzeit gehören zur Buchung und zählen im Zeitraum der **Anreise**. Stornos zählen nie zum Umsatz. Option **„Auswertung: Jahre Historie“** (Standard 2) legt fest, wie weit zurück geladen wird.

#### Attribute der Buchungs-Entitäten

`Aktueller Gast`, `Nächster Gast`, `Belegt`, `Anreise heute` und `Abreise heute` tragen die komplette Buchung als Attribute:

| Attribut | Bedeutung |
|---|---|
| `buchungs_id`, `referenz_id`, `typ` | Smoobu-ID, Buchungsnummer des Kanals, Buchungstyp |
| `gastname`, `vorname`, `nachname`, `gast_id` | Gastdaten |
| `email`, `telefon`, `sprache` | Kontakt und Sprache |
| `kanal`, `kanal_id` | Buchungskanal (Airbnb, Booking.com, Direkt …) |
| `wohnung`, `wohnung_id` | Wohnung |
| `anreise`, `abreise` | ISO-Zeitstempel inkl. Check-in-/Check-out-Zeit |
| `freigabe` | Ab hier gilt die Wohnung als frei (Abreisezeit + Puffer bzw. Standard-Check-out) |
| `check_in_zeit`, `check_out_zeit` | Zeiten laut Smoobu (leer = Standard aus den Optionen) |
| `naechte`, `erwachsene`, `kinder`, `personen` | Aufenthalt |
| `preis`, `preis_bezahlt` | Gesamtpreis und Zahlungsstatus |
| `anzahlung`, `anzahlung_bezahlt`, `kaution`, `kaution_bezahlt` | Anzahlung und Kaution |
| `kurtaxe`, `provision_enthalten` | nur bei Buchungen mit Detaildaten |
| `notiz`, `assistent_notiz` | Notizen aus Smoobu |
| `gaeste_app` | Link zur Smoobu-Gäste-App |
| `erstellt`, `geaendert` | Zeitstempel aus Smoobu |
| `blockiert` | blockierter Zeitraum (keine Gästebuchung) |
| `hund`, `hund_hinweis` | Hund/Haustier erwähnt (Preiselement oder Notiz) und Fundstelle |
| `smoobu_rohdaten` | **alle** Felder der API-Antwort unverändert, inkl. `priceElements` |

Zeitabhängige Entitäten werden jede Minute neu ausgewertet. „Belegt“ wechselt dadurch pünktlich zur Check-in-Zeit, auch ohne neue API-Abfrage. In die Historie schreibt Home Assistant nur echte Änderungen.

---

### Aktionen

Alle Aktionen haben das optionale Feld `config_entry_id`. Ohne Angabe wird das einzige eingerichtete Smoobu-Konto verwendet.

#### `smoobu.refresh`

Ruft die Daten sofort ab.

#### `smoobu.get_reservations`

Buchungen nach Filter. Gibt Antwortdaten zurück (`count`, `reservations`).

| Feld | Typ | Beschreibung |
|---|---|---|
| `arrival_from` / `arrival_to` | Datum | Anreise von/bis |
| `departure_from` / `departure_to` | Datum | Abreise von/bis |
| `apartment_id` | Zahl | nur diese Wohnung |
| `show_cancellation` | bool | Stornos einschließen (Standard: nein) |

#### `smoobu.get_reservation`

Eine Buchung mit allen Details. Pflichtfeld: `reservation_id`. Antwort: `reservation`.

#### `smoobu.get_messages`

Nachrichten einer Buchung. Pflichtfeld: `reservation_id`, optional `only_related_to_guest`. Antwort: `count`, `messages`.

#### `smoobu.send_message`

Nachricht an den Gast oder als Gastgeber-Notiz.

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `reservation_id` | ja | Buchungs-ID |
| `message` | ja | Text oder HTML |
| `subject` | nein | Betreff |
| `recipient` | nein | `guest` (Standard) oder `host` |
| `internal` | nein | nur bei `host`: Notiz vor dem Gast verbergen |


#### `smoobu.block_period` (ab 1.9.0)

Sperrt einen Zeitraum (über den Sperr-Kanal von Smoobu, wird an alle Portale übertragen). Felder: `start_date` (erste Nacht), `end_date` (Tag nach der letzten Nacht), `notice`, `apartment_id` (nur bei mehreren Wohnungen). Die ID des Sperr-Kanals wird aus vorhandenen Sperrzeiten gelesen.

#### `smoobu.delete_reservation` (ab 1.9.0)

Löscht eine Sperrzeit. Eine **Direktbuchung** wird nur mit `allow_booking: true` storniert. **Portalbuchungen** (Airbnb, Booking.com …) werden nie storniert – das muss im Portal passieren.

#### `smoobu.set_rates` (ab 1.9.0)

Setzt `price` (pro Nacht) und/oder `min_stay` (Nächte) für `start_date` bis `end_date` (beide inklusive).

#### `smoobu.update_reservation` (ab 1.9.0)

Ändert `arrival_time`, `departure_time` und/oder `notice` einer Buchung (`reservation_id`).

---

### Dashboard-Karten (ab 1.8.0)

Die Integration bringt eigene Karten mit. Sie werden automatisch geladen (keine Ressource eintragen) und erscheinen im Kartendialog unter „Smoobu …“. Ein Klick auf eine Buchung öffnet überall dieselbe Detailansicht: Gast und Kontakt, Preis mit Positionen, Provision, Gebühr und Netto, Notiz bearbeiten, Ankunfts-/Abreisezeit ändern, Nachrichtenverlauf und Antwort, Sperre löschen bzw. Direktbuchung stornieren.

| Karte | Inhalt | Optionen |
|---|---|---|
| `custom:smoobu-overview-card` | Status, Gäste-Kacheln, Anreise/Abreise/Gästewechsel heute, Hunde, Kennzahlen Monat/Jahr mit Vorjahr, Prognose, nächste Anreisen, **Lücken mit Prüfung gegen den Mindestaufenthalt**, offene Zahlungen | `title`, `entities` (eigene HA-Entitäten als Chips), `upcoming`, `gap_days`, `apartment_id` |
| `custom:smoobu-timeline-card` | Belegungsplan je Monat mit Kanalfarben, Sperrzeiten, Tagespreis, Mindestaufenthalt, nicht buchbaren Lücken. Tage markieren → **sperren** oder **Preis/Mindestaufenthalt setzen** | `title`, `months` (3), `show_prices`, `actions`, `apartment_id` |
| `custom:smoobu-bookings-card` | Buchungsliste: Suche, Zeitraum, Kanal- und Statusfilter (inkl. Stornos, Sperrzeiten), Sortierung, Summen, CSV-Export | `title`, `period`, `status`, `apartment_id` |
| `custom:smoobu-analytics-card` | Finanzen: Zeitraum frei (auch benutzerdefiniert), Kanäle mehrfach wählbar, Vergleich Vorjahr/Vorperiode. Kennzahlen mit Veränderung, gestapeltes Diagramm je Kanal mit Vergleichslinie, Anteile, Erkenntnisse, Kanaltabelle | `title`, `period`, `compare`, `apartment_id` |
| `custom:smoobu-inbox-card` | Posteingang: laufende, kommende und kürzliche Buchungen, Nachrichtenverlauf, antworten, ✨ KI-Vorschlag | `title`, `days_back`, `days_ahead`, `message_entity` |
| `custom:smoobu-assistant-card` | KI-Assistent: Wissensdatenbank (freigeben, bearbeiten, vertraulich), Vorschläge, Gelerntes, Lücken, Import | `title` |

```yaml
# Beispiel: eigene Seite „Smoobu“ mit Übersicht und Belegungsplan
type: custom:smoobu-overview-card
entities:
  - climate.ferienwohnung
---
type: custom:smoobu-timeline-card
months: 4
```

Datenquelle der Karten sind WebSocket-Befehle (`smoobu/info`, `smoobu/analytics`, `smoobu/bookings`, `smoobu/booking`, `smoobu/rates`, `smoobu/subscribe`). Sie aktualisieren sich bei jedem neuen Datenstand von selbst. Alle Texte aus Smoobu werden vor der Anzeige maskiert.

---

### KI-Assistent (ab 1.10.0)

Antwortvorschläge für Gästenachrichten auf Basis einer Wissensdatenbank, die aus euren eigenen Antworten lernt. **Nichts wird ohne Bestätigung an Gäste gesendet.**

- **Ablauf:** Neue Gästenachricht (Webhook) → Entwurf per `ai_task.generate_data` (Anbieter frei wählbar, z. B. Google Gemini) → Push an die gewählten Handys mit **Senden / Bearbeiten / Ignorieren**; erkennt der Assistent eine neue Ankunftszeit, gibt es zusätzlich **„Ankunft HH:MM übernehmen“**.
- **Keine Erfindungen:** Die Anweisung erlaubt nur Fakten aus Wissen, Buchung, Belegung und HA-Status. Unbekanntes wird als `[OFFEN: …]` markiert, als Wissenslücke gemeldet und blockiert das Senden per Push.
- **Wissensdatenbank** (in HA gespeichert, Karte `custom:smoobu-assistant-card`): Einträge Thema + Text, Status aktiv/Vorschlag/aus, **vertraulich** = geht nie an die KI.
- **Lernen:** Jede gesendete Antwort (Karte, Push, direkt in Smoobu) wird mit der Gästenachricht davor gespeichert; neue Vorschläge orientieren sich an den ähnlichsten Beispielen (lokale BM25-Suche). Aktion `smoobu.assistant_import` übernimmt den bisherigen Verlauf, `smoobu.assistant_build_knowledge` schlägt daraus Wissenseinträge vor.
- **Kontext:** Buchung, Belegung davor/danach (früher Check-in / später Check-out), frei wählbare HA-Entitäten (z. B. Heizung, Tür, Außentemperatur) – bei Problemen („kalt“, „kein Wasser“) Push als **dringend** mit Hinweis.
- **Zusatzaufgaben (Optionen):** Tagesbriefing per Push, tägliche Meldung nicht buchbarer Lücken (Mindestaufenthalt) mit Button zum Anpassen.
- **Entitäten/Aktionen:** `sensor.smoobu_assistent_offene_vorschlage`, `smoobu.assistant_suggest` (Anlass: antwort, willkommen, anreise, abreise, bewertung), WebSocket `smoobu/assistant/*`.
- **Datenschutz:** Gästenachrichten und Buchungsdaten gehen an den gewählten KI-Anbieter.

---

### Events

Jedes Webhook-Ereignis wird als Event **`smoobu_event`** auf den Home-Assistant-Eventbus gelegt.

| Feld | Inhalt |
|---|---|
| `action` | `newReservation`, `updateReservation`, `cancelReservation`, `deleteReservation`, `newMessage`, `onlineCheckInUpdate`, `updateRates` |
| `reservation_id` | Buchungs-ID (bei `newMessage` die ID der zugehörigen Buchung) |
| `apartment_id`, `apartment` | Wohnung |
| `guest_name` | Gastname |
| `arrival`, `departure` | Anreise- und Abreisedatum |
| `channel` | Buchungskanal |
| `data` | komplette Nutzdaten von Smoobu |
| `config_entry_id` | Smoobu-Konto in Home Assistant |

Nach jedem Ereignis (außer `updateRates`) aktualisiert die Integration sofort alle Entitäten.

---

### Beispiele

#### Push bei neuer Buchung

```yaml
# Zweck: Sofortige Push-Benachrichtigung, sobald Smoobu eine neue Buchung meldet.
# Auslöser ist das Webhook-Event der Smoobu-Integration (Echtzeit, kein Polling).
alias: fewo_buchung_neu_push
description: "Changelog:\nV1.0: Push bei neuer Smoobu-Buchung"
mode: queued  # mehrere Buchungen kurz hintereinander nacheinander abarbeiten
triggers:
  - alias: "Auslöser: Smoobu meldet neue Buchung"
    trigger: event
    event_type: smoobu_event
    event_data:
      action: newReservation
actions:
  - alias: "Aktion: Push mit Gast, Zeitraum und Kanal"
    action: notify.mobile_app_dein_handy
    data:
      title: "Neue Buchung"
      message: >-
        {{ trigger.event.data.guest_name }}:
        {{ trigger.event.data.arrival }} – {{ trigger.event.data.departure }}
        ({{ trigger.event.data.channel }})
      data:
        tag: smoobu_buchung  # neue Meldung ersetzt die vorherige am Handy
```

#### Push bei Stornierung

```yaml
# Zweck: Hinweis bei Stornierung, z. B. um geplantes Vorheizen zu prüfen.
alias: fewo_buchung_storno_push
description: "Changelog:\nV1.0: Push bei Smoobu-Stornierung"
mode: queued
triggers:
  - alias: "Auslöser: Smoobu meldet Stornierung"
    trigger: event
    event_type: smoobu_event
    event_data:
      action: cancelReservation
actions:
  - alias: "Aktion: Push mit Gast und Zeitraum"
    action: notify.mobile_app_dein_handy
    data:
      title: "Buchung storniert"
      message: >-
        {{ trigger.event.data.guest_name }}
        ({{ trigger.event.data.arrival }} – {{ trigger.event.data.departure }})
```

#### Willkommensnachricht am Anreisetag

```yaml
# Zweck: Am Anreisetag um 10:00 eine persönliche Nachricht an den Gast senden.
# Buchungs-ID und Vorname kommen aus den Attributen des Binärsensors „Anreise heute“.
alias: fewo_gast_willkommen_nachricht
description: "Changelog:\nV1.0: Willkommensnachricht am Anreisetag"
mode: single
triggers:
  - alias: "Auslöser: täglich 10:00"
    trigger: time
    at: "10:00:00"
conditions:
  - alias: "Prüfung: Reist heute ein Gast an?"
    condition: state
    entity_id: binary_sensor.smoobu_ferienwohnung_anreise_heute
    state: "on"
actions:
  - alias: "Aktion: Nachricht über Smoobu an den Gast senden"
    action: smoobu.send_message
    data:
      reservation_id: "{{ state_attr('binary_sensor.smoobu_ferienwohnung_anreise_heute', 'buchungs_id') }}"
      subject: "Willkommen"
      message: >-
        Hallo {{ state_attr('binary_sensor.smoobu_ferienwohnung_anreise_heute', 'vorname') }},
        wir freuen uns auf euch! Die Wohnung ist ab 16 Uhr bereit.
```

#### Buchungen eines Monats in einem Skript abfragen

```yaml
# Zweck: Alle Anreisen im Dezember abrufen und die Anzahl melden.
# get_reservations liefert Antwortdaten → in response_variable ablegen.
alias: skript_smoobu_buchungen_dezember
sequence:
  - alias: "Aktion: Buchungen mit Anreise im Dezember abrufen"
    action: smoobu.get_reservations
    data:
      arrival_from: "2026-12-01"
      arrival_to: "2026-12-31"
    response_variable: ergebnis
  - alias: "Aktion: Anzahl per Push melden"
    action: notify.mobile_app_dein_handy
    data:
      message: "Dezember: {{ ergebnis.count }} Buchungen"
```

#### Gästewechsel als Reinigungs-Erinnerung

```yaml
# Zweck: Am Morgen eines Wechseltags an die Reinigung zwischen Check-out und Check-in erinnern.
alias: fewo_reinigung_gaestewechsel_erinnerung
description: "Changelog:\nV1.0: Erinnerung bei Gästewechsel"
mode: single
triggers:
  - alias: "Auslöser: täglich 08:00"
    trigger: time
    at: "08:00:00"
conditions:
  - alias: "Prüfung: Ist heute Gästewechsel?"
    condition: state
    entity_id: binary_sensor.smoobu_ferienwohnung_gastewechsel_heute
    state: "on"
actions:
  - alias: "Aktion: Push an die Reinigung"
    action: notify.mobile_app_dein_handy
    data:
      title: "Gästewechsel heute"
      message: "Reinigung zwischen 11 und 16 Uhr einplanen."
```

---

### Webhook

Die Integration richtet den Webhook beim Start selbst ein:

1. Sie registriert einen Home-Assistant-Webhook mit zufälliger ID (nur `POST`).
2. Ist Home Assistant Cloud aktiv, erzeugt sie einen **Nabu Casa Cloudhook**. Sonst verwendet sie die **externe HTTPS-URL** von Home Assistant.
3. Sie trägt die URL über die Smoobu-API (`/api/users/webhooks`) ein. Eine bereits eingetragene gleiche URL wird erkannt und nicht doppelt angelegt.

**Wenn die automatische Registrierung nicht klappt,** erscheint eine Benachrichtigung in Home Assistant mit der URL. Diese in Smoobu unter **Einstellungen → API** als Webhook-URL eintragen. Die URL steht auch im Attribut `url` von `sensor.smoobu_webhook`.

Wird der Webhook in den Optionen abgeschaltet oder die Integration gelöscht, entfernt sie die Registrierung bei Smoobu und den Cloudhook wieder.

---

### Datenschutz und Sicherheit

- API-Schlüssel und Secret liegen im Config-Entry von Home Assistant, nicht in YAML-Dateien.
- Gästedaten (Name, E-Mail, Telefon, Notizen) stehen in Entitäts-Attributen und damit auch in der **Historie** von Home Assistant. Wer das nicht möchte, schließt die betroffenen Entitäten im Recorder aus.
- Der **Diagnose-Download** schwärzt Zugangsdaten, Webhook-URL und alle Gästedaten.
- Smoobu signiert Webhooks nicht. Die Integration schützt sich deshalb über die geheime, zufällige Webhook-URL und nimmt nur Ereignisse an, deren Smoobu-Benutzer-ID zum eingerichteten Konto passt. Bei abweichender ID wird mit `403` abgelehnt.
- Die Webhook-URL nicht weitergeben. Bei Verdacht: Webhook in den Optionen aus- und wieder einschalten, dann wird eine neue URL erzeugt.

---

### Fehlerbehebung

| Problem | Ursache / Lösung |
|---|---|
| Einrichtung meldet „Schlüssel oder Secret ungültig“ | Schlüssel/Secret falsch kopiert, Secret neu erzeugt, oder Schlüssel gelöscht. Neuen Schlüssel erstellen. Die Signatur hängt von der Uhrzeit ab: die Systemzeit von Home Assistant muss stimmen (max. 5 min Abweichung). |
| Gastnamen leer, `binary_sensor.smoobu_gastdaten_fehlen` ist an | Beim API-Schlüssel fehlt die Option „Guest Data (PII)“. In Smoobu aktivieren oder neuen Schlüssel mit dieser Option anlegen. |
| `sensor.smoobu_webhook` = `manuell` | Automatische Registrierung abgelehnt. URL aus dem Attribut `url` in Smoobu eintragen. |
| `sensor.smoobu_webhook` = `aus` | Webhook in den Optionen deaktiviert oder keine HTTPS-URL verfügbar (Nabu Casa nicht angemeldet, keine externe URL gesetzt). |
| Änderungen kommen verzögert | Ohne Webhook greift nur das Abfrageintervall (Standard 10 min). |
| Fehler `429` im Protokoll | Ratenlimit von Smoobu (700 Anfragen/Minute) erreicht. Abfrageintervall erhöhen oder „Detaildaten für die nächsten n Buchungen“ verringern. |

**Debug-Protokoll:** Einstellungen → Geräte & Dienste → Smoobu → **Debug-Protokollierung aktivieren**, Vorgang wiederholen, Protokoll herunterladen. Alternativ in `configuration.yaml`:

```yaml
# Ausführliches Protokoll nur für die Smoobu-Integration
logger:
  logs:
    custom_components.smoobu: debug
```

---

### Technische Details

**Signatur** nach [docs.smoobu.com](https://docs.smoobu.com/):

```
canonical = METHOD \n PFAD \n QUERY \n TIMESTAMP \n NONCE \n SHA256_HEX(Body) \n API_KEY
X-Signature = Base64( HMAC-SHA256(Secret, canonical) )
```

- `QUERY`: Parameter alphabetisch sortiert, Schlüssel und Werte RFC-3986-kodiert, ohne `?`
- `TIMESTAMP`: ISO 8601 UTC, z. B. `2026-04-01T12:00:00Z`
- `NONCE`: neue UUID v4 je Anfrage
- Header: `X-API-Key`, `X-Timestamp`, `X-Nonce`, `X-Signature`

**Verwendete Endpunkte:** `GET /api/me`, `GET /api/rates`, `GET /api/apartments`, `GET /api/apartments/{id}`, `GET /api/reservations`, `GET /api/reservations/{id}`, `GET /api/reservations/{id}/messages`, `POST /api/reservations/{id}/messages/send-message-to-guest`, `POST /api/reservations/{id}/messages/send-message-to-host`, `GET/POST/DELETE /api/users/webhooks`.

**Datenabruf:** Ein Coordinator je Konto lädt alle Buchungen im Zeitfenster [heute − Rückblick, heute + Vorschau], Stornos ausgenommen. Wohnungsdetails werden alle 24 h aktualisiert. Detaildaten der laufenden und nächsten Buchungen werden zwischengespeichert und nur neu abgerufen, wenn sich `modifiedAt` ändert. Blättert eine Kalenderkarte über das Zeitfenster hinaus, fragt der Kalender direkt bei Smoobu nach.

**Typ:** `iot_class: cloud_push`, `integration_type: service`, Abhängigkeiten `webhook` (Pflicht) und `cloud` (optional).

---

### Changelog

Alle Änderungen stehen in [CHANGELOG.md](CHANGELOG.md) und bei den [Releases](https://github.com/Grunor/ha-Smoobu/releases).

---

## English

Custom integration for [Smoobu](https://www.smoobu.com/), the channel manager for vacation rentals.
It connects Home Assistant directly to the Smoobu API and provides bookings, guest data, occupancy and statistics as entities. A webhook delivers changes in real time.

> Unofficial. This project is not affiliated with Smoobu GmbH.

---

### Contents

- [Why this integration?](#why-this-integration)
- [Features](#features)
- [Requirements](#requirements)
- [Create a Smoobu API key](#create-a-smoobu-api-key)
- [Installation](#installation-1)
- [Setup](#setup)
- [Options](#options)
- [Entities](#entities)
- [Actions](#actions)
- [Dashboard cards](#dashboard-cards-since-180)
- [Events](#events-1)
- [Examples](#examples)
- [Webhook](#webhook-1)
- [Privacy and security](#privacy-and-security)
- [Troubleshooting](#troubleshooting)
- [Technical details](#technical-details)
- [Changelog](#changelog-1)

---

### Why this integration?

- **Smoobu's iCal export no longer contains full guest names.** If you include the Smoobu calendar via iCal (or via a Google Calendar import), you only see placeholders.
- **Smoobu switched off the old `Api-Key` header authentication on 31 Oct 2026.** Every request now has to be signed individually with HMAC-SHA256. Home Assistant's `rest:` integration cannot do this, because Jinja templates cannot compute an HMAC signature.

This integration handles the signing and exposes all data natively in Home Assistant.

---

### Features

- 📅 **Occupancy calendar per apartment** with full guest name, channel, guests, price and contact details
- 👤 **Sensors for the current and next booking:** guest name, first name, number of guests, arrival, departure
- 🏠 **Binary sensors:** occupied, arrival today, departure today, changeover today, dog with current/next guest
- 📊 **Statistics:** 30-day bookings, occupancy and revenue, revenue month/year/previous year (split by nights), price per booking, unpaid bookings
- ⚡ **Real-time webhook:** Nabu Casa cloudhook or external HTTPS URL, registered with Smoobu automatically
- 🔔 **Event `smoobu_event`** for new, changed or cancelled bookings and new guest messages
- 🛠️ **Actions:** query bookings, get a single booking, read messages, send messages
- 🔐 **HMAC-SHA256 signing** according to the current Smoobu specification
- 🌍 German and English, set up entirely in the UI, diagnostics download with redacted guest data

---

### Requirements

- Home Assistant **2025.2** or newer (tested locally with 2026.2)
- Smoobu account with API access
- For the real-time webhook either **Home Assistant Cloud (Nabu Casa)** or an **external HTTPS URL** (Smoobu only accepts HTTPS). Without either, the integration works by polling only.

---

### Create a Smoobu API key

1. Log in to Smoobu.
2. Open **Advanced → API Keys** and click **Create New** in the top-right corner.
3. Optionally enter a **Label** (just a name to recognise the key, e.g. "Home Assistant") and submit.
4. In the following window copy the **Secret**. **It is shown only once.**
5. Copy the **API key** from the **Key** column in the list. The label is **not** the key.

| Field in Home Assistant | Value from Smoobu |
|---|---|
| API key | "Key" column in the list |
| Secret | Secret from the window after creating the key |

> For guest names, email and phone the key needs access to guest data. If Smoobu offers a guest data option ("Guest Data (PII)") for the key, enable it. If `binary_sensor.smoobu_guest_data_missing` is on, this permission is missing.

---

### Installation

#### Via Marketplace (HACS) – recommended

1. Open **Marketplace** (or HACS) in Home Assistant.
2. Top right **⋮ → Custom repositories**.
3. Enter `https://github.com/Grunor/ha-Smoobu`, category **Integration**, add.
4. Search for **Smoobu** and download it.
5. **Restart** Home Assistant.

Updates then show up as regular updates in Home Assistant.

#### Manual

1. Download `smoobu.zip` from the latest [release](https://github.com/Grunor/ha-Smoobu/releases) and unpack it.
2. Copy the contents to `/config/custom_components/smoobu`, e.g. via Samba or Studio Code Server.
3. **Restart** Home Assistant.

---

### Setup

1. **Settings → Devices & services → Add integration**.
2. Select **Smoobu**.
3. Enter the **API key** and **secret**.

The integration validates the key, creates one device per Smoobu apartment and, if possible, registers the webhook with Smoobu.

If the key becomes invalid later (deleted, secret regenerated), Home Assistant asks you to **re-authenticate**. Enter the new key and secret there; no new setup is needed.

---

### Options

Under **Settings → Devices & services → Smoobu → Configure**:

| Option | Default | Meaning |
|---|---|---|
| Polling interval | 10 min | Regular polling as a fallback to the webhook |
| Use real-time webhook | on | Create the webhook and register it with Smoobu. Turning it off removes the registration. |
| Default check-in | 16:00 | Used when the booking has no arrival time |
| Default check-out | 11:00 | Used when the booking has no departure time (release time, no buffer) |
| Channels paid via the portal | Airbnb, Booking.com | Bookings from these channels do not count as unpaid |
| Buffer after Smoobu departure time | 0 min | If the booking has a departure time, the apartment counts as vacant only after that time + buffer |
| Days back | 30 days | How far back bookings are loaded |
| Days ahead | 365 days | How far ahead bookings are loaded |
| Fetch details for next n bookings | 3 | The current and next n bookings per apartment are additionally fetched one by one (first/last name, city tax, price details) |

The integration reloads automatically after saving.

---

### Entities

Each Smoobu apartment becomes a device **"Smoobu &lt;apartment name&gt;"**, plus one device **"Smoobu"** for the account.

**Naming:** `<domain>.smoobu_<apartment_name>_<entity>`. The apartment name comes from Smoobu, the entity part from the Home Assistant system language. With several apartments, each gets its own set of entities. The examples below are for an apartment named "Apartment" with English system language. With German system language the entity IDs are German (see [Deutsch](#deutsch)).

#### Per apartment

| Entity | Example ID | Content |
|---|---|---|
| Calendar | `calendar.smoobu_apartment_occupancy` | All bookings. Title = guest name, with 🐕 for dogs (blocked periods: "Blockiert"). Start = arrival + check-in time, end = departure + check-out time. |
| Occupied | `binary_sensor.smoobu_apartment_occupied` | On from check-in time until release (departure time + buffer, or default check-out) |
| Arrival today | `binary_sensor.smoobu_apartment_arrival_today` | A guest arrives today |
| Departure today | `binary_sensor.smoobu_apartment_departure_today` | A guest leaves today |
| Changeover today | `binary_sensor.smoobu_apartment_changeover_today` | Departure and arrival on the same day |
| Dog current guest | `binary_sensor.smoobu_apartment_dog_current_guest` | Current booking mentions a dog/pet (add-on or note). Attribute `hund_hinweis` = where it was found |
| Dog next guest | `binary_sensor.smoobu_apartment_dog_next_guest` | Same for the next booking |
| Current guest | `sensor.smoobu_apartment_current_guest` | Full name of the current guest |
| Current first name | `sensor.smoobu_apartment_current_first_name` | First name of the current guest |
| Current guests count | `sensor.smoobu_apartment_current_guests_count` | Adults + children, 0 if vacant |
| Next guest | `sensor.smoobu_apartment_next_guest` | Full name of the next guest |
| Next first name | `sensor.smoobu_apartment_next_first_name` | First name of the next guest |
| Next guests count | `sensor.smoobu_apartment_next_guests_count` | Number of guests of the next booking |
| Next arrival | `sensor.smoobu_apartment_next_arrival` | Timestamp of the next arrival |
| Next departure | `sensor.smoobu_apartment_next_departure` | Release time of the current booking, otherwise of the next one |
| Bookings 30 days | `sensor.smoobu_apartment_bookings_30_days` | Number of arrivals in the next 30 days, list in attribute `buchungen` |
| Occupancy rate 30 days | `sensor.smoobu_apartment_occupancy_rate_30_days` | Booked nights in % (incl. blocked periods) |
| Revenue 30 days | `sensor.smoobu_apartment_revenue_30_days` | Sum of booking prices of arrivals in the next 30 days |
| Price current guest | `sensor.smoobu_apartment_price_current_guest` | Booking price of the current booking. Attributes: `aufschluesselung` (price elements), `preis_pro_nacht`, `anzahlung`, `offen`, `kurtaxe` … |
| Price next guest | `sensor.smoobu_apartment_price_next_guest` | Same for the next booking |
| Revenue month | `sensor.smoobu_apartment_revenue_month` | Revenue of the current month, booking price **split by nights**. Attributes: `davon_bis_heute`, `vormonat`, `vorjahresmonat` |
| Revenue year | `sensor.smoobu_apartment_revenue_year` | Revenue of the current year (booked). Attributes: `davon_bis_heute`, `gebucht_ab_heute`, `monate`, `monate_vorjahr`, `vorjahr_gesamt` |
| Revenue previous / next month | `sensor.smoobu_apartment_revenue_previous_month` / `…_revenue_next_month` | Revenue of the previous/next month. Attributes: `vorjahresmonat`, `veraenderung_vorjahr_prozent`, `auslastung`, `auslastung_vorjahr`, `gaeste_naechte`, `gesperrt_naechte` |
| Occupancy rate month | `sensor.smoobu_apartment_occupancy_rate_month` | Occupancy of the current month in %, **guest nights only**. Attributes: `vormonat`, `folgemonat`, `vorjahresmonat`, `monate`, `monate_vorjahr` |
| Blocked nights month | `sensor.smoobu_apartment_blocked_nights_month` | Nights blocked by the host this month (separate from occupancy). Attributes: `monate`, `monate_vorjahr`, `monate_prozent`, `jahr_gesamt`, `vorjahr_gesamt` |
| Revenue previous year | `sensor.smoobu_apartment_revenue_previous_year` | Revenue of the previous year |
| Unpaid bookings | `sensor.smoobu_apartment_unpaid_bookings` | Current/upcoming bookings with an open amount (price − paid prepayment). Portal channels from the options (default Airbnb, Booking.com) are excluded. Attributes: `buchungen` (with `offen`), `offener_betrag` |

#### Account (diagnostic)

| Entity | Example ID | Content |
|---|---|---|
| Last update | `sensor.smoobu_last_update` | Time of the last successful poll |
| Last event | `sensor.smoobu_last_event` | Last webhook action (e.g. `newReservation`) with booking ID and guest |
| Webhook | `sensor.smoobu_webhook` | `registriert` (registered), `manuell` (URL must be entered in Smoobu) or `aus` (off). Attribute `url`. |
| Guest data missing | `binary_sensor.smoobu_guest_data_missing` | On if Smoobu returns no guest names (PII permission missing) |

#### Individual booking fields (current and next guest)

Every field of the current/next booking is also available as its own entity, e.g. `sensor.smoobu_apartment_current_guest_email` or `binary_sensor.smoobu_apartment_next_guest_price_paid`.

| Field | enabled | Field | enabled |
|---|---|---|---|
| Channel, language, email, phone | ✅ | Booking ID, reference ID, guest ID, booking type | ⬜ |
| Adults, children, nights | ✅ | Guests | ⬜ |
| Check-in time, check-out time | ✅ | Guest app (link) | ⬜ |
| Arrival (current guest only), departure | ✅ | Release | ⬜ |
| Prepayment, open amount | ✅ | Deposit, city tax | ⬜ |
| Note, assistant note (full text in attribute `text`) | ✅ | Created, modified | ⬜ |
| Price paid, prepayment paid (binary sensors) | ✅ | Deposit paid | ⬜ |

⬜ = created but disabled (enable in HA under entity → settings). **Note:** contact details and notes are stored in the Home Assistant history as entities.

#### Prices & availability (Smoobu daily rates, 60 days)

| Entity | Example ID | Content |
|---|---|---|
| Price today / tomorrow | `sensor.smoobu_apartment_price_today` / `…_price_tomorrow` | Daily rate from Smoobu. Attributes: `preise_60_tage`, `mindestaufenthalt_60_tage`, `verfuegbar` |
| Minimum stay today | `sensor.smoobu_apartment_minimum_stay_today` | Nights |
| Next free day | `sensor.smoobu_apartment_next_free_day` | First bookable day from today |
| Free nights 30 days | `sensor.smoobu_apartment_free_nights_30_days` | Number of bookable nights |
| Next gap | `sensor.smoobu_apartment_next_gap` | Start of the next free gap between two stays. Attributes: `bis`, `naechte`, `mindestaufenthalt`, `buchbar`, `alle_luecken_60_tage` |

#### Messages

| Entity | Example ID | Content |
|---|---|---|
| Last guest message | `sensor.smoobu_last_guest_message` | Text of the latest message (loaded via webhook `newMessage`, survives restarts). Attributes: `text`, `betreff`, `absender`, `gast`, `buchungs_id`, `empfangen` |

#### Direct marketing vs. portals, net revenue

Gross = booking price from Smoobu. Commission = the value Smoobu sends with the booking (`commission-included`, usually present for Airbnb and Booking.com), otherwise the channel percentage from the options. Booking.com payment charges are read from the booking. Net = gross − commission − payment charge, prorated by nights.

| Entity | Example ID | Content |
|---|---|---|
| Net revenue month / year | `sensor.smoobu_apartment_net_revenue_month` / `…_year` | Net; attributes `brutto`, `provision`, `zahlungsgebuehren`, `kostenquote_prozent`, `davon_bis_heute`, `vorjahr_gesamt`, `vorjahr_bis_heute`, change, `monate`, `monate_vorjahr`, `kanaele` |
| Commission & fees year | `sensor.smoobu_apartment_commission_fees_year` | Commission + payment fees; `je_kanal`, previous year, cost ratio |
| Direct / portal revenue year | `sensor.smoobu_apartment_direct_revenue_year` / `…_portal_revenue_year` | Gross of the group; net, bookings, nights, net per night, share, year-to-date, previous year, monthly values |
| Direct share year | `sensor.smoobu_apartment_direct_share_year` | % of gross revenue; share of nights, previous year, change in points, `ersparnis_direkt` (direct revenue × portal cost ratio), per-channel tables |

Per guest additionally: channel group (direct/portal), commission and net price; price sensors carry `kanal_gruppe`, `provision`, `provision_quelle`, `zahlungsgebuehr`, `netto`.

**Options → step "Commissions":** % per channel (defaults Airbnb 15.5 · Booking.com 15 · FeWo-direkt 8 · Website 0 · Direct booking 0), other portals (15), further channels as `Channel=percent; …`, direct channels (default: Direct booking, Website).

#### Channels, filtered analysis, forecast (since 1.7.0)

**One sensor per channel** is created automatically as soon as a channel appears in the bookings (e.g. `sensor.smoobu_apartment_channel_booking_com`). State = gross current year. Flat attributes for tiles: `netto`, `kosten`, `kostenquote_prozent`, `naechte`, `auslastung_prozent`, `buchungen`, `stornos`, `stornoquote_prozent`, `netto_pro_nacht`, `aufenthalt_schnitt`, `personen_schnitt`, `vorlauf_schnitt`, `bis_heute_brutto`, `veraenderung_vorjahr_bis_heute_prozent`, `prognose_jahr`. Plus all key figures per period (`jahr`, `bis_heute`, `vorjahr`, `vorjahr_bis_heute`, `monat`, `vormonat`, `folgemonat`, `vorjahresmonat`, `letzte_12_monate`) and monthly values (`monate`, `monate_netto`, `monate_vorjahr`, `monate_vorjahr_netto`).

**Filters:** three select entities per apartment – channel (all, direct, portals, each channel), period (current/previous/next month, current year, year to date, previous year, last/next 12 months, all) and comparison (previous year, previous period, none). The `sensor.…_analysis_*` sensors (gross, net, costs, cost ratio, nights, occupancy, bookings, cancellation rate, net per night, stay, lead time, guests per booking, direct share) follow the selection immediately, each with `vergleichswert` and `veraenderung_prozent` / `veraenderung_punkte`. The selection survives restarts.

**Forecast:** `sensor.…_forecast_year` = booked revenue of the year + revenue that was still booked last year after the same date (from the booking creation date).

Revenue and nights are prorated by night. Bookings, cancellations, avg. stay, avg. guests and avg. lead time belong to the booking and count in the period of **arrival**. Cancellations never count as revenue. Option **"Analysis: years of history"** (default 2) sets how far back data is loaded.

#### Attributes of the booking entities

`Current guest`, `Next guest`, `Occupied`, `Arrival today` and `Departure today` carry the complete booking as attributes. **The attribute keys are German** (independent of the system language):

| Attribute | Meaning |
|---|---|
| `buchungs_id`, `referenz_id`, `typ` | Smoobu ID, channel booking number, booking type |
| `gastname`, `vorname`, `nachname`, `gast_id` | Guest name, first name, last name, guest ID |
| `email`, `telefon`, `sprache` | Email, phone, language |
| `kanal`, `kanal_id` | Booking channel (Airbnb, Booking.com, direct …) |
| `wohnung`, `wohnung_id` | Apartment |
| `anreise`, `abreise` | Arrival/departure as ISO timestamp incl. check-in/check-out time |
| `freigabe` | Release: apartment counts as vacant from here (departure time + buffer, or default check-out) |
| `check_in_zeit`, `check_out_zeit` | Times from Smoobu (empty = default from options) |
| `naechte`, `erwachsene`, `kinder`, `personen` | Nights, adults, children, total guests |
| `preis`, `preis_bezahlt` | Total price and payment status |
| `anzahlung`, `anzahlung_bezahlt`, `kaution`, `kaution_bezahlt` | Prepayment and deposit |
| `kurtaxe`, `provision_enthalten` | City tax, commission included (only for bookings with details) |
| `notiz`, `assistent_notiz` | Notes from Smoobu |
| `gaeste_app` | Link to the Smoobu guest app |
| `erstellt`, `geaendert` | Created/modified timestamps from Smoobu |
| `blockiert` | Blocked period (no guest booking) |
| `hund`, `hund_hinweis` | Dog/pet mentioned (price element or note) and where |
| `smoobu_rohdaten` | **all** fields of the API response unchanged, incl. `priceElements` |

Time-dependent entities are re-evaluated every minute, so "Occupied" switches exactly at check-in time even without a new API poll. Home Assistant only writes real changes to the history.

---

### Actions

All actions have the optional field `config_entry_id`. If omitted, the only configured Smoobu account is used.

#### `smoobu.refresh`

Fetches the data immediately.

#### `smoobu.get_reservations`

Bookings by filter. Returns response data (`count`, `reservations`).

| Field | Type | Description |
|---|---|---|
| `arrival_from` / `arrival_to` | date | Arrival from/to |
| `departure_from` / `departure_to` | date | Departure from/to |
| `apartment_id` | number | Only this apartment |
| `show_cancellation` | bool | Include cancellations (default: no) |

#### `smoobu.get_reservation`

One booking with all details. Required: `reservation_id`. Response: `reservation`.

#### `smoobu.get_messages`

Messages of a booking. Required: `reservation_id`, optional `only_related_to_guest`. Response: `count`, `messages`.

#### `smoobu.send_message`

Message to the guest or as a host note.

| Field | Required | Description |
|---|---|---|
| `reservation_id` | yes | Booking ID |
| `message` | yes | Text or HTML |
| `subject` | no | Subject |
| `recipient` | no | `guest` (default) or `host` |
| `internal` | no | only with `host`: hide the note from the guest |


#### `smoobu.block_period` (since 1.9.0)

Blocks a period (through Smoobu's block channel, pushed to all portals). Fields: `start_date` (first night), `end_date` (day after the last night), `notice`, `apartment_id` (only with several apartments). The block channel ID is read from existing blocks.

#### `smoobu.delete_reservation` (since 1.9.0)

Deletes a block. A **direct booking** is only cancelled with `allow_booking: true`. **Portal bookings** (Airbnb, Booking.com …) are never cancelled – do that in the portal.

#### `smoobu.set_rates` (since 1.9.0)

Sets `price` (per night) and/or `min_stay` (nights) for `start_date` to `end_date` (both inclusive).

#### `smoobu.update_reservation` (since 1.9.0)

Changes `arrival_time`, `departure_time` and/or `notice` of a booking (`reservation_id`).

---

### Dashboard cards (since 1.8.0)

The integration ships its own cards. They are loaded automatically (no resource needed) and appear in the card picker as "Smoobu …". Clicking a booking opens the same detail view everywhere: guest and contact, price with line items, commission, fee and net, edit note, change arrival/departure time, message thread and reply, delete a block or cancel a direct booking.

| Card | Content | Options |
|---|---|---|
| `custom:smoobu-overview-card` | Status, guest tiles, arrivals/departures/changeover today, dogs, key figures month/year vs. last year, forecast, upcoming arrivals, **gaps checked against the minimum stay**, open payments | `title`, `entities`, `upcoming`, `gap_days`, `apartment_id` |
| `custom:smoobu-timeline-card` | Occupancy plan per month with channel colours, blocks, daily price, minimum stay, unbookable gaps. Mark days → **block** or **set price/minimum stay** | `title`, `months` (3), `show_prices`, `actions`, `apartment_id` |
| `custom:smoobu-bookings-card` | Booking list: search, period, channel and status filters (incl. cancellations, blocks), sorting, totals, CSV export | `title`, `period`, `status`, `apartment_id` |
| `custom:smoobu-analytics-card` | Finance: free period (also custom), multiple channels, comparison previous year/period. Key figures with change, stacked chart per channel with comparison line, shares, insights, channel table | `title`, `period`, `compare`, `apartment_id` |
| `custom:smoobu-inbox-card` | Inbox: current, upcoming and recent bookings, message thread, reply, ✨ AI suggestion | `title`, `days_back`, `days_ahead`, `message_entity` |
| `custom:smoobu-assistant-card` | AI assistant: knowledge base (approve, edit, confidential), suggestions, learned examples, gaps, import | `title` |

The cards read data through WebSocket commands (`smoobu/info`, `smoobu/analytics`, `smoobu/bookings`, `smoobu/booking`, `smoobu/rates`, `smoobu/subscribe`) and refresh themselves on every data update. All texts from Smoobu are escaped before display.

---

### AI assistant (since 1.10.0)

Reply suggestions for guest messages based on a knowledge base that learns from your own replies. **Nothing is sent to guests without confirmation.**

- **Flow:** new guest message (webhook) → draft via `ai_task.generate_data` (any provider, e.g. Google Gemini) → push to the chosen phones with **Send / Edit / Ignore**; if a new arrival time is detected, also **"Apply arrival HH:MM"**.
- **No invention:** only facts from knowledge, booking, occupancy and HA state are allowed. Unknown items are marked `[OFFEN: …]`, reported as knowledge gaps and block sending via push.
- **Knowledge base** (stored in HA, card `custom:smoobu-assistant-card`): topic + text, status active/suggestion/off, **confidential** = never sent to the AI.
- **Learning:** every sent reply (card, push, directly in Smoobu) is stored with the guest message before it; new suggestions follow the most similar examples (local BM25 search). `smoobu.assistant_import` imports the history, `smoobu.assistant_build_knowledge` suggests knowledge entries from it.
- **Context:** booking, occupancy before/after (early check-in / late check-out), selectable HA entities (heating, door, outdoor temperature) – problem reports are pushed as **urgent** with a hint.
- **Extra tasks (options):** daily briefing push, daily report of unbookable gaps (minimum stay) with a button to adjust.
- **Entities/actions:** `sensor.smoobu_assistant_open_suggestions`, `smoobu.assistant_suggest`, WebSocket `smoobu/assistant/*`.
- **Privacy:** guest messages and booking data are sent to the chosen AI provider.

---

### Events

Every webhook event is fired on the Home Assistant event bus as **`smoobu_event`**.

| Field | Content |
|---|---|
| `action` | `newReservation`, `updateReservation`, `cancelReservation`, `deleteReservation`, `newMessage`, `onlineCheckInUpdate`, `updateRates` |
| `reservation_id` | Booking ID (for `newMessage` the ID of the related booking) |
| `apartment_id`, `apartment` | Apartment |
| `guest_name` | Guest name |
| `arrival`, `departure` | Arrival and departure date |
| `channel` | Booking channel |
| `data` | Complete payload from Smoobu |
| `config_entry_id` | Smoobu account in Home Assistant |

After every event (except `updateRates`) the integration refreshes all entities immediately.

---

### Examples

#### Push notification for a new booking

```yaml
# Purpose: Instant push notification as soon as Smoobu reports a new booking.
# Triggered by the webhook event of the Smoobu integration (real time, no polling).
alias: rental_booking_new_push
description: "Changelog:\nV1.0: Push for new Smoobu booking"
mode: queued  # process several bookings arriving shortly after each other one by one
triggers:
  - alias: "Trigger: Smoobu reports a new booking"
    trigger: event
    event_type: smoobu_event
    event_data:
      action: newReservation
actions:
  - alias: "Action: push with guest, period and channel"
    action: notify.mobile_app_your_phone
    data:
      title: "New booking"
      message: >-
        {{ trigger.event.data.guest_name }}:
        {{ trigger.event.data.arrival }} – {{ trigger.event.data.departure }}
        ({{ trigger.event.data.channel }})
      data:
        tag: smoobu_booking  # a new notification replaces the previous one on the phone
```

#### Push notification for a cancellation

```yaml
# Purpose: Notice on cancellation, e.g. to check planned pre-heating.
alias: rental_booking_cancel_push
description: "Changelog:\nV1.0: Push for Smoobu cancellation"
mode: queued
triggers:
  - alias: "Trigger: Smoobu reports a cancellation"
    trigger: event
    event_type: smoobu_event
    event_data:
      action: cancelReservation
actions:
  - alias: "Action: push with guest and period"
    action: notify.mobile_app_your_phone
    data:
      title: "Booking cancelled"
      message: >-
        {{ trigger.event.data.guest_name }}
        ({{ trigger.event.data.arrival }} – {{ trigger.event.data.departure }})
```

#### Welcome message on arrival day

```yaml
# Purpose: Send a personal message to the guest at 10:00 on arrival day.
# Booking ID and first name come from the attributes of the "Arrival today" binary sensor.
alias: rental_guest_welcome_message
description: "Changelog:\nV1.0: Welcome message on arrival day"
mode: single
triggers:
  - alias: "Trigger: daily at 10:00"
    trigger: time
    at: "10:00:00"
conditions:
  - alias: "Check: Is a guest arriving today?"
    condition: state
    entity_id: binary_sensor.smoobu_apartment_arrival_today
    state: "on"
actions:
  - alias: "Action: send message to the guest via Smoobu"
    action: smoobu.send_message
    data:
      reservation_id: "{{ state_attr('binary_sensor.smoobu_apartment_arrival_today', 'buchungs_id') }}"
      subject: "Welcome"
      message: >-
        Hi {{ state_attr('binary_sensor.smoobu_apartment_arrival_today', 'vorname') }},
        we are looking forward to your stay! The apartment is ready from 4 pm.
```

#### Query the bookings of a month in a script

```yaml
# Purpose: Get all arrivals in December and report the count.
# get_reservations returns response data → store it in response_variable.
alias: script_smoobu_bookings_december
sequence:
  - alias: "Action: get bookings with arrival in December"
    action: smoobu.get_reservations
    data:
      arrival_from: "2026-12-01"
      arrival_to: "2026-12-31"
    response_variable: result
  - alias: "Action: report the count via push"
    action: notify.mobile_app_your_phone
    data:
      message: "December: {{ result.count }} bookings"
```

#### Changeover as cleaning reminder

```yaml
# Purpose: On the morning of a changeover day, remind about cleaning between check-out and check-in.
alias: rental_cleaning_changeover_reminder
description: "Changelog:\nV1.0: Reminder on changeover"
mode: single
triggers:
  - alias: "Trigger: daily at 08:00"
    trigger: time
    at: "08:00:00"
conditions:
  - alias: "Check: Is today a changeover day?"
    condition: state
    entity_id: binary_sensor.smoobu_apartment_changeover_today
    state: "on"
actions:
  - alias: "Action: push to the cleaning team"
    action: notify.mobile_app_your_phone
    data:
      title: "Changeover today"
      message: "Schedule cleaning between 11 am and 4 pm."
```

---

### Webhook

The integration sets up the webhook itself on startup:

1. It registers a Home Assistant webhook with a random ID (`POST` only).
2. If Home Assistant Cloud is active, it creates a **Nabu Casa cloudhook**. Otherwise it uses the **external HTTPS URL** of Home Assistant.
3. It registers the URL via the Smoobu API (`/api/users/webhooks`). An identical URL that is already registered is detected and not added twice.

**If automatic registration fails,** a notification with the URL appears in Home Assistant. Enter this URL in Smoobu under **Settings → API** as webhook URL. The URL is also available in the `url` attribute of `sensor.smoobu_webhook`.

If the webhook is turned off in the options or the integration is deleted, the registration at Smoobu and the cloudhook are removed again.

---

### Privacy and security

- API key and secret are stored in the Home Assistant config entry, not in YAML files.
- Guest data (name, email, phone, notes) is stored in entity attributes and therefore also in the Home Assistant **history**. If you don't want that, exclude the affected entities from the recorder.
- The **diagnostics download** redacts credentials, the webhook URL and all guest data.
- Smoobu does not sign webhooks. The integration therefore relies on the secret, random webhook URL and only accepts events whose Smoobu user ID matches the configured account. Other IDs are rejected with `403`.
- Do not share the webhook URL. If in doubt: turn the webhook off and on again in the options, which creates a new URL.

---

### Troubleshooting

| Problem | Cause / solution |
|---|---|
| Setup reports "Invalid key/secret" | Key/secret copied incorrectly, secret regenerated, or key deleted. Create a new key. The signature depends on the time: the Home Assistant system clock must be correct (max. 5 min deviation). |
| Guest names empty, `binary_sensor.smoobu_guest_data_missing` is on | The API key lacks the "Guest Data (PII)" option. Enable it in Smoobu or create a new key with this option. |
| `sensor.smoobu_webhook` = `manuell` | Automatic registration was rejected. Enter the URL from the `url` attribute in Smoobu. |
| `sensor.smoobu_webhook` = `aus` | Webhook disabled in the options, or no HTTPS URL available (Nabu Casa not logged in, no external URL set). |
| Changes arrive late | Without the webhook only the polling interval applies (default 10 min). |
| Error `429` in the log | Smoobu rate limit (700 requests/minute) reached. Increase the polling interval or reduce "Fetch details for next n bookings". |

**Debug log:** Settings → Devices & services → Smoobu → **Enable debug logging**, repeat the action, download the log. Alternatively in `configuration.yaml`:

```yaml
# Verbose logging for the Smoobu integration only
logger:
  logs:
    custom_components.smoobu: debug
```

---

### Technical details

**Signature** according to [docs.smoobu.com](https://docs.smoobu.com/):

```
canonical = METHOD \n PATH \n QUERY \n TIMESTAMP \n NONCE \n SHA256_HEX(body) \n API_KEY
X-Signature = Base64( HMAC-SHA256(secret, canonical) )
```

- `QUERY`: parameters sorted alphabetically, keys and values RFC 3986 encoded, without `?`
- `TIMESTAMP`: ISO 8601 UTC, e.g. `2026-04-01T12:00:00Z`
- `NONCE`: new UUID v4 per request
- Headers: `X-API-Key`, `X-Timestamp`, `X-Nonce`, `X-Signature`

**Endpoints used:** `GET /api/me`, `GET /api/rates`, `GET /api/apartments`, `GET /api/apartments/{id}`, `GET /api/reservations`, `GET /api/reservations/{id}`, `GET /api/reservations/{id}/messages`, `POST /api/reservations/{id}/messages/send-message-to-guest`, `POST /api/reservations/{id}/messages/send-message-to-host`, `GET/POST/DELETE /api/users/webhooks`.

**Data retrieval:** One coordinator per account loads all bookings in the window [today − days back, today + days ahead], excluding cancellations. Apartment details are refreshed every 24 h. Details of the current and next bookings are cached and only fetched again when `modifiedAt` changes. If a calendar card scrolls beyond the window, the calendar queries Smoobu directly.

**Type:** `iot_class: cloud_push`, `integration_type: service`, dependencies `webhook` (required) and `cloud` (optional).

---

### Changelog

All changes are listed in [CHANGELOG.md](CHANGELOG.md) and under [Releases](https://github.com/Grunor/ha-Smoobu/releases).

---

## Lizenz / License

MIT

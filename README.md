<p align="center"><img src="custom_components/smoobu/brand/icon@2x.png" width="128" alt="Smoobu for Home Assistant"></p>

# Smoobu für Home Assistant / Smoobu for Home Assistant

> 🗺️ **Roadmap:** geplante Funktionen im [Roadmap-Board](https://github.com/users/Grunor/projects/1) und in [ROADMAP.md](ROADMAP.md) / planned features on the [roadmap board](https://github.com/users/Grunor/projects/1) and in [ROADMAP.md](ROADMAP.md)

[![Release](https://img.shields.io/github/v/release/Grunor/ha-Smoobu)](https://github.com/Grunor/ha-Smoobu/releases)
[![Validate](https://github.com/Grunor/ha-Smoobu/actions/workflows/validate.yml/badge.svg)](https://github.com/Grunor/ha-Smoobu/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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
- [Screenshots](#screenshots)
- [Voraussetzungen](#voraussetzungen)
- [Smoobu-API-Schlüssel erstellen](#smoobu-api-schlüssel-erstellen)
- [Installation](#installation)
- [Einrichtung](#einrichtung)
- [Optionen](#optionen)
- [Entitäten](#entitäten)
- [Aktionen](#aktionen)
- [Dashboard-Karten](#dashboard-karten-ab-180)
- [Dashboard-Vorlage](#dashboard-vorlage)
- [KI-Assistent und KI-Sperre](#ki-assistent-ab-1100)
- [Lexware Office (Beta)](#lexware-office-beta-ab-1200)
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

**Daten in Home Assistant**
- 📅 **Belegungskalender je Wohnung** mit vollem Gastnamen, Kanal, Personen, Preis und Kontaktdaten
- 👤 **Sensoren für aktuelle und nächste Buchung** (Gastname, Vorname, Personen, Anreise, Abreise) und **Binärsensoren** (belegt, Anreise/Abreise/Gästewechsel heute, Hund beim aktuellen/nächsten Gast)
- 📊 **Kennzahlen-Sensoren:** Buchungen, Auslastung und Umsatz (Monat/Jahr/Vorjahr, anteilig nach Nächten), offene Zahlungen, Prognose Jahresende, ein Sensor je Kanal
- ⚡ **Echtzeit-Webhook** (Nabu Casa oder eigene HTTPS-URL, automatisch bei Smoobu registriert) und Event **`smoobu_event`** bei neuer, geänderter oder stornierter Buchung und neuer Gastnachricht
- 🛠️ **Aktionen:** Buchungen abfragen, Nachrichten lesen und senden, Zeiträume sperren, Preise und Mindestaufenthalt setzen, Ankunfts-/Abreisezeit, Notiz und Zahlungsstatus ändern

**Smoobu-Dashboard** (eigene Karten, automatisch geladen, fertige [Dashboard-Vorlage](docs/dashboard-vorlage.yaml) mit 9 Seiten)
- 🏠 **Übersicht:** Status heute in einem Satz, aktueller und nächster Gast, Belegung der nächsten Wochen, Kennzahlen mit Verlauf, freie Zeiträume gegen den Mindestaufenthalt geprüft, Aufgaben-Board **„Wartet auf dich“** (Nachrichten, Rechnungen, Preise, Last-Minute, Lücken, **Einrichtung**) mit Erledigt/Später
- 🗓️ **Kalender & Preise:** Kanalfarben, Tagespreis, Mindestaufenthalt, nicht buchbare Lücken; Anreise und Abreise antippen → **sperren** oder **Preis setzen**
- 📋 **Buchungen:** Suche, Filter, Summen je Gruppe (anstehend/aktuell/vergangen), **Stammgäste** („↻ 2× · Mai 25“), CSV-Export; Details mit Zahlungsstatus, Zeiten, Notiz, Nachrichten und **Umbuchen** (Zeitraum/Unterkunft, Beta)
- 💶 **Finanzen:** Zeitraum, Vergleich (Stichtag Vorjahr, ganzes Vorjahr, Vorperiode, mehrere Jahre), Kanäle, Raster; Diagramm je Kanal, Kanaltabelle, Erkenntnisse
- 📈 **Statistik-Werkbank:** Bewertung & Empfehlung (Preise per Button übernehmen und rückgängig machen), **Deckungsbeitrag** mit Brücke, Buchungstempo mit Prognose, Saison-Matrix mit Abweichung zum Ø, Wochentage, Kanäle, Buchungsfenster und -zeitpunkt, verlorene Nächte, Stornos, Gäste, Ehrentafel, Service, **Reinigung** (wer hat wann welche Wohnung gereinigt); **eigene Module** mit Vorlagen, Vorschau und Bearbeiten; Anordnung im HA-Benutzerprofil
- 🌦️ **Saisons** frei einstellbar (Name + Startmonat) mit **automatischer Erkennung** aus den bisherigen Jahren
- 💬 **Posteingang:** offene Gastnachrichten, „Keine Antwort nötig“, KI-Vorschlag
- 🧾 **Umsatzsteuer (optional):** Beträge ohne USt in Finanzen, Statistik und Umsatz-Sensoren – mit „USt-pflichtig seit“, Sätzen mit Gültigkeit, Steuerart je Smoobu-Preisbestandteil und Kosten ohne Vorsteuer; Umschalter Brutto / ohne USt
- 🧾 **Lexware Office (BETA, optional, ab Lexware-Tarif XL):** Rechnungsentwurf per Button aus den Buchungsdetails nach deinen Lexware-Artikeln (je Nacht, Zusatzperson, Kind, Hund, Endreinigung bis/ab n Nächte, Rest aus dem Buchungspreis), Firmen netto mit Gast als Ansprechpartner, Zahlungsstand (Anzahlung/komplett) und Hinweise in „Wartet auf dich“
- 🔑 **Türcodes:** Zufallscode je Buchung (Stellen einstellbar, keine trivialen Codes) oder statischer Code je Wohnung, z. B. für einen Schlüsseltresor (ab 1.20.0 mit „gültig ab/bis“ und nächstem Code, der am Starttag nachrückt; maßgeblich ist der Anreisetag, Erinnerung vor Ablauf), Gültigkeit Check-in − 2 h bis Check-out + 1 h (einstellbar), in der Smoobu-Notiz, in den Buchungsdetails, als Entität und optional direkt im Schloss (Matter, Z-Wave JS, ZHA, Zigbee2MQTT oder eigenes Skript); in Antworten als Platzhalter `{{ turcode }}`, der erst beim Senden lokal ersetzt wird
- 🧹 **Reinigungsboard:** Reinigung je Abreise mit Check-out, nächster Anreise und Gästewechsel; **zuweisen**, selbst übernehmen und abhaken, Push an die zugewiesene Person (bei Zuweisung und am Vorabend)
- ⚙️ **Einstellungen im Dashboard** mit **Rollenkonfigurator** (Rechte je Rolle per Häkchen, eigene Rollen, Rolle **Reinigung** – sieht vom Gast nur den Vornamen); neue Optionen erscheinen unter „Wartet auf dich“ → Einrichtung, Neuerungen unter **„✨ Neu“** in der Kopfzeile
- 🎨 Hell/Dunkel/System, mehrere Wohnungen mit Gesamtansicht, Handy-Ansicht

**Benachrichtigungen und KI**
- 🔔 **Pushes** je Art an/aus mit eigenen Empfängern und Ruhezeit: neue Buchung, Storno/Änderung, **Umbuchung** (Zeitraum/Unterkunft), Gastnachricht, KI-Vorschlag, Zahlungserinnerung, Tagesbriefing, Lücken
- 🤖 **KI-Assistent (optional):** Antwortvorschläge mit Wissensdatenbank und Datenschutz-Stufen; **komplett abschaltbar** (keine Daten an KI-Anbieter)

**Technik**
- 🔐 **HMAC-SHA256-Signatur** nach aktueller Smoobu-Spezifikation
- 🌍 Deutsch und Englisch, Einrichtung komplett über die Oberfläche, Diagnose-Download mit geschwärzten Gästedaten

---

### Screenshots

Alle Bilder zeigen eine **erfundene Demo-Ferienwohnung**. Die Bilder stammen aus der echten Integration (Stand 1.19.0), aber mit Demodaten (`tools/screenshots/`). Echte Gäste- oder Umsatzdaten kommen darin nicht vor.

**Übersicht, hell und dunkel:** Status heute in einem Satz, aktueller und nächster Gast, Belegung der nächsten 6 Wochen mit Preisen, Kennzahlen mit 12-Monats-Verlauf, nächste Anreisen, freie Zeiträume und das Aufgaben-Board „Wartet auf dich“ mit Reitern und Zählern (Antworten, Zahlungen als erhalten markieren, Preise übernehmen, Lücken anpassen, Einrichtung)
![Übersicht hell](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_uebersicht_hell.png)
![Übersicht dunkel](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_uebersicht_dunkel.png)

**Was ist neu und Einrichtung:** „✨ Neu“ in der Kopfzeile listet Neuerungen mit Link zur Stelle; neue Optionen stehen unter „Wartet auf dich“ → Einrichtung mit „Einstellen →“
![Was ist neu](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/was_ist_neu.png)
![Einrichtung](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/wartet_einrichtung.png)

**Statistik-Werkbank:** Aussage-Satz, Kennzahlen mit Vergleich und Endstand, Bewertung & Empfehlung, Buchungstempo, Saison-Matrix und weitere Module (Werkbank am PC, Einfach am Handy)
![Statistik](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_statistik_hell.png)

**Reinigungsboard (ab 1.19.0):** Reinigung je Abreise mit Check-out, nächster Anreise (Uhrzeit, Personen, Hund) und Gästewechsel; zuweisen per Auswahl, selbst übernehmen, abhaken; am Handy gut bedienbar. **Ab 1.20.0 Reinigung später planen:** 📅 Reinigungstag wählbar vom Abreisetag bis zur nächsten Belegung; liegt er später, sperrt die Integration die Nächte dazwischen automatisch in Smoobu (Anreise am Reinigungstag bleibt möglich), verschieben/zurücksetzen/früher erledigt passt die Sperre an

![Reinigung später planen](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/reinigung_planen.png)

![Reinigung](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/reinigung.png)
![Reinigung am Handy](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/reinigung_handy.png)

**Statistik „Reinigung“:** wer hat wann welche Wohnung gereinigt – je Person (Anteil, Gästewechsel, Hunde, Gäste Ø, Nächte, Zeit bis zum Abhaken), je Monat, je Wohnung und als Liste
![Statistik Reinigung](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/statistik_reinigung.png)

**Türcodes (ab 1.19.0):** Stellen, Gültigkeit, Smoobu-Notiz und Schloss je Wohnung
![Türcodes](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_tuercode.png)

**Stromkosten (ab 1.19.0):** konstant wie bisher oder gemessen aus dem Stromzähler der Wohnung – Vorheizstart bis Check-out, Leerstand separat oder anteilig, Netzanteil stündlich aus dem Energie-Dashboard. **Netzanteil (ab 1.19.1b5)** wahlweise aus einem Netzbezug-Sensor der Wohnung (z. B. ein Sensor, der den Wohnungsverbrauch zeitgleich nach Autarkie auf Netz/PV aufteilt; Lücken wie importierte Monatswerte werden gemittelt), stündlich aus dem Energie-Dashboard (ganzes Haus), aus 12 festen Monatswerten oder als ein Jahreswert
![Stromkosten](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_strom.png)

**Nebenkostenabrechnung (ab 1.19.0):** PDF hochladen, die KI liest die Werte, Vorschlag mit Herleitung, Fundstelle und Prüfung – übernommen erst nach Bestätigung
![Nebenkosten](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_nebenkosten.png)

**Rollenkonfigurator (ab 1.19.0):** Rechte je Rolle per Häkchen, eigene Rollen anlegen; Hinweis bei Kombinationen, die im Dashboard kaum nutzbar sind
![Rollen](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_rollen.png)

**Deckungsbeitrag:** Netto minus variable Kosten mit Vergleich; die Brücke zeigt, was Preis je Nacht, Anzahl der Nächte (Umsatz minus eingesparte Kosten) und Kosten je Nacht am Ergebnis geändert haben
![Deckungsbeitrag](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/statistik_deckungsbeitrag.png)

**Saison-Matrix:** Monate × Jahre mit Abweichung zum Ø des Monats (▲/▼, Auslastung in Prozentpunkten); Kennzahlen Auslastung, Umsatz, ADR, RevPAR, Netto, DB
![Saison-Matrix](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/statistik_saisonmatrix.png)

**Saisons mit automatischer Erkennung:** eigene Saisons mit Namen und Startmonat; Vorschläge für 2, 3 und 4 Saisons aus den bisherigen Jahren
![Saisons](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_saisons.png)

**Kalender & Preise:** Anreise und Abreise antippen → sperren oder Preis setzen; Kanalfarben, Tagespreis, Mindestaufenthalt, nicht buchbare Lücken
![Kalender](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/kalender_auswahl.png)

**Buchungen:** Summen je Gruppe, Stammgäste mit Anzahl früherer Aufenthalte und letztem Besuch, Filter und CSV-Export
![Buchungen](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_buchungen_hell.png)

**Umbuchen (Beta):** Zeitraum oder Unterkunft einer Direktbuchung ändern – mit Belegungsprüfung und Preisvorschlag
![Umbuchen](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/umbuchen.png)

**Mehrere Wohnungen:** Auswahl „Alle“ oder eine Wohnung oben rechts; Gesamtansicht mit Status je Wohnung und einer Kalenderzeile je Wohnung
![Alle Wohnungen](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_uebersicht_alle_hell.png)
![Kalender alle Wohnungen dunkel](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_kalender_alle_dunkel.png)

<details><summary>Weitere Bilder: Finanzen, Posteingang, Buchungsdetails, Einstellungen, Assistent, KI gesperrt, Handy</summary>

![Finanzen](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_finanzen_hell.png)
![Posteingang](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/posteingang.png)
![Buchungsdetails](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/buchungsdetails.png)
![Buchungsdetails mit offener Zahlung](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/buchungsdetails_zahlung.png)
![Einstellungen Kosten](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_einstellungen_kosten_hell.png)
![Einstellungen Datenschutz](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_datenschutz.png)
![Assistent](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/assistent.png)
![Posteingang mit gesperrter KI](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/ki_gesperrt_posteingang.png)
![Statistik am Handy](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_statistik_handy_dunkel.png)

</details>

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
| Standard-Check-out | 11:00 | Gilt, wenn in der Buchung keine Abreisezeit steht (offizielle Check-out-Zeit) |
| Kanäle mit Zahlung über das Portal | Airbnb, Booking.com | Buchungen dieser Kanäle zählen nicht als offene Zahlung |
| Wartezeit nach Check-out | 30 min | Zeit bis zur tatsächlichen Freigabe (z. B. Reinigungsstart): Freigabe = Abreisezeit bzw. Standard-Check-out + Wartezeit, z. B. 11:00 + 30 min = 11:30 |
| Rückblick | 30 Tage | Wie weit zurück Buchungen geladen werden |
| Vorschau | 365 Tage | Wie weit voraus Buchungen geladen werden |
| Detaildaten für die nächsten n Buchungen | 3 | Laufende und nächste n Buchungen je Wohnung werden zusätzlich einzeln abgerufen (Vor-/Nachname, Kurtaxe, Preisdetails) |

Schritt **Provisionen**: Provision je Kanal in %, Direktkanäle. Schritt **KI-Assistent**:

| Option | Standard | Bedeutung |
|---|---|---|
| **KI-Funktionen erlauben** | aus (bei Installationen vor 1.14.0 mit gewählter KI: an) | Hauptschalter. Aus = KI **gesperrt**: kein Aufruf von `ai_task`, keine Daten an einen KI-Anbieter, KI-Buttons in den Karten ausgegraut. Gilt für Karten, Aktionen, WebSocket, Push-Buttons und Webhook |
| Automatische Antwortvorschläge | an (wirkt nur mit erlaubter KI) | Bei jeder neuen Gästenachricht einen Vorschlag erzeugen und per Push senden (nur mit erlaubter KI) |
| KI (KI-Aufgabe) | – | `ai_task`-Entität, z. B. Google Gemini; Pflicht, wenn die KI erlaubt ist |
| HA-Entitäten als Kontext | – | z. B. Heizung, Tür, Außentemperatur |
| Dashboard-Seite für „Bearbeiten“ | `/lovelace` | z. B. `/dashboard-ferienwohnung/smoobu-nachrichten` |

Schritt **Benachrichtigungen** (ab 1.17.0) – je Push-Art an/aus und eigene Empfänger (`notify.mobile_app_*`; leer = bisherige Empfänger des Assistenten):

| Push-Art | Standard | Wann |
|---|---|---|
| Neue Buchung | aus | sofort (Ruhezeit beachtet) |
| Storno / Änderung | aus | sofort, mit Vorher → Nachher (Personen, Ankunftszeit, Preis) |
| Umbuchung (ab 1.18.0) | wie „Storno / Änderung“ | sofort, wenn sich Zeitraum oder Unterkunft ändert: Vorher → Nachher mit Nächten bzw. Wohnungsnamen; ausgeschaltet kommt die Änderung unter „Storno / Änderung“ |
| Neue Gästenachricht | aus | sofort, wenn kein KI-Vorschlag kommt; verschwindet nach Antwort/Abhaken |
| KI-Antwortvorschlag | an | sofort, nicht dringende in der Ruhezeit gesammelt |
| Zahlungserinnerung | aus, 7 Tage, 09:00 | täglich zur Uhrzeit: offener Betrag X Tage vor und am Anreisetag |
| Tagesbriefing | aus, 07:30 | täglich zur Uhrzeit, funktioniert ohne KI |
| Nicht buchbare Lücken | aus, 09:05 | täglich zur Uhrzeit, funktioniert ohne KI |
| **Ruhezeit** | aus, 21:00–07:00 | Je Push-Art einstellbar („Hält Ruhezeit ein“): solche Pushes werden gesammelt und zum Ende zugestellt (je Thema der neueste Stand). Standard: Buchung, Storno/Änderung und KI-Vorschlag warten; Gästenachricht, Zahlung, Briefing und Lücken kommen sofort. Dringende Vorschläge und Bestätigungen kommen immer sofort |

Schritt **Wohnungskürzel** (ab 1.17.0): eigenes Kürzel je Wohnung (bis 4 Zeichen, Buchstaben/Ziffern, eindeutig über alle Konten); leer = automatisch. Gilt für Dashboard und Pushes.

**Nur in der Einstellungs-Karte** (`custom:smoobu-settings-card`, ab 1.18.0): **Kosten** (variable Kosten je Aufenthalt und Nacht, ab 1.19.0 **Strom, Wasser und Heizung konstant oder aus Zähler**, **Nebenkostenabrechnung per KI**), **Preise & Kanäle** (Provisionen, Direktkanäle, Zahlung über das Portal sowie – ab 1.19.1 hierher verschoben – Aufschläge je Kanal, Genius, Last-Minute), **Reinigung & Zugang** (ab 1.19.0: Reinigung = Zeit × Stundenlohn je Reinigungskraft, Pushes an Reinigungskräfte, Türcodes), **Benutzer & Rechte** (Rollen, nur Admins), **Saisons** (2–6 Saisons mit Namen und Startmonat, automatische Erkennung aus den bisherigen Jahren) und die Kategorien des Aufgaben-Boards. Neue Optionen nach einem Update erscheinen in der Übersicht unter **„Wartet auf dich“ → Einrichtung** mit Link zur Stelle.

Nach dem Speichern wird die Integration automatisch neu geladen.

---

### Entitäten

Je Smoobu-Wohnung entsteht ein Gerät **„Smoobu &lt;Wohnungsname&gt;“**, zusätzlich ein Gerät **„Smoobu“** für das Konto.

**Benennung:** `<domain>.smoobu_<wohnungsname>_<entität>`. Der Wohnungsname kommt aus Smoobu, der Entitätsteil aus der Systemsprache von Home Assistant. Bei mehreren Wohnungen bekommt jede ihren eigenen Satz Entitäten. Die Beispiele unten gelten für eine Wohnung namens „Ferienwohnung“ bei deutscher Systemsprache. Bei englischer Systemsprache heißen die Entitäten englisch (siehe [English](#english)).

#### Je Wohnung

| Entität | Beispiel-ID | Inhalt |
|---|---|---|
| Kalender | `calendar.smoobu_ferienwohnung_belegung` | Alle Buchungen. Titel = Gastname, mit 🐕 bei Hund (blockierte Zeiträume: „Blockiert“). Beginn = Anreise + Check-in-Zeit, Ende = Abreise + Check-out-Zeit. |
| Belegt | `binary_sensor.smoobu_ferienwohnung_belegt` | An von der Check-in-Zeit bis zur Freigabe (Abreisezeit bzw. Standard-Check-out + Wartezeit) |
| Anreise heute | `binary_sensor.smoobu_ferienwohnung_anreise_heute` | Heute reist ein Gast an |
| Türcode aktueller / nächster Gast (ab 1.19.0, nur mit Türcodes an) | `sensor.smoobu_ferienwohnung_turcode_aktueller_gast`, `…_turcode_nachster_gast` | Code als Zustand; Attribute `gueltig_von`, `gueltig_bis`, `status`, `buchung_id`, `code_platz`. **Den Zustand sieht jeder HA-Benutzer, der die Entität sehen kann – nicht auf Gäste-Dashboards zeigen.** |
| Anreise morgen | `binary_sensor.smoobu_ferienwohnung_anreise_morgen` | Morgen reist ein Gast an (Attribute wie „Anreise heute“, u. a. `hund`) |
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
| Letzte Gästenachricht | `sensor.smoobu_letzte_gastenachricht` | Text der letzten Nachricht **vom Gast** (per Webhook `newMessage` geladen, übersteht Neustarts; eigene Nachrichten an den Gast ändern ihn ab 1.14.0 nicht). Attribute: `text`, `betreff`, `absender`, `gast`, `buchungs_id`, `empfangen` |

#### Direktvermarktung vs. Portale, Nettoumsatz

Brutto = Buchungspreis laut Smoobu. Provision = Wert, den Smoobu zur Buchung liefert (`commission-included`, bei Airbnb und Booking.com meist vorhanden), sonst der in den Optionen eingestellte %-Satz des Kanals. Die Booking.com-Zahlungsgebühr („Payment charge“) wird aus der Buchung gelesen. Netto = Brutto − Provision − Zahlungsgebühr, anteilig nach Nächten.

| Entität | Beispiel-ID | Inhalt |
|---|---|---|
| Erlös Monat / Jahr (bis 1.19: Nettoumsatz) | `sensor.smoobu_ferienwohnung_erlos_monat` / `…_jahr` | Erlös (Umsatz − Provision/Gebühren); Attribute `brutto`, `provision`, `zahlungsgebuehren`, `kostenquote_prozent`, `davon_bis_heute`, `vorjahr_gesamt`, `vorjahr_bis_heute`, `veraenderung_vorjahr_bis_heute_prozent`, `monate`, `monate_vorjahr`, `kanaele` |
| Provision & Gebühren Jahr | `sensor.smoobu_ferienwohnung_provision_gebuhren_jahr` | Summe Provision + Zahlungsgebühren; `je_kanal`, `vorjahr`, `vorjahr_bis_heute`, Kostenquote |
| Umsatz Direkt / Portale Jahr | `sensor.smoobu_ferienwohnung_umsatz_direkt_jahr` / `…_umsatz_portale_jahr` | Brutto der Gruppe; `netto`, `buchungen`, `naechte`, `netto_pro_nacht`, `anteil_prozent`, `bis_heute`, `vorjahr`, `vorjahr_bis_heute`, Veränderung, `monate`, `monate_vorjahr` |
| Direktanteil Jahr | `sensor.smoobu_ferienwohnung_direktanteil_jahr` | % am Bruttoumsatz; `anteil_naechte_prozent`, `vorjahr_prozent`, `veraenderung_prozentpunkte`, `ersparnis_direkt` (Direktumsatz × Kostenquote der Portale), `kanaele` / `kanaele_vorjahr` / `…_bis_heute` je Kanal (Brutto, Netto, Kosten, Buchungen, Nächte, Netto/Nacht, Anteil) |

Je Gast zusätzlich: `…_aktueller_gast_kanalgruppe` (Direkt/Portal), `…_provision`, `…_erlos` (bis 1.19: `…_nettopreis`); die Preis-Sensoren haben die Attribute `kanal_gruppe`, `provision`, `provision_quelle`, `zahlungsgebuehr`, `netto`, `kostenquote_prozent`.

**Optionen → Schritt „Provisionen“:** % je Kanal (Standard Airbnb 15,5 · Booking.com 15 · FeWo-direkt 8 · Website 0 · Direktbuchung 0), sonstige Portale (15), weitere Kanäle als `Kanal=Prozent; …`, Direktkanäle (Standard: Direct booking, Website). In der Einstellungs-Karte wählst du Kanäle per Dropdown: zuerst Kanäle mit Buchungen (mit Anzahl), dann in den Einstellungen genutzte, dann alle übrigen Smoobu-Kanäle. Smoobu hat keinen API-Endpunkt für angebundene Kanäle. Ein angebundenes Portal ohne Buchung (z. B. HomeToGo) findest du deshalb in der Katalog-Gruppe.

**Optionen → Schritt „Kosten & Preise“ (ab 1.18.0):** variable Kosten für den Deckungsbeitrag (Netto − variable Kosten) und die Aufschläge aus dem Smoobu-Preistool für die Empfehlungen. Je Aufenthalt Reinigung und Wäsche; Heiz- und Warmwasserkosten des Abrechnungsjahres (aus der Nebenkostenabrechnung), verteilt nach Gradtagszahlen (Januar 170 ‰ … Juli 13 ‰ – je Nacht im Januar ≈ 12× so teuer wie im Juli) und skaliert auf die Gästenächte des Abrechnungsjahres; Wasser je Nacht; Strom in kWh je Nacht mit Netzanteil je Monat (Netzstrom zum Netzpreis, PV-Strom zur Einspeisevergütung). Aufschläge je Kanal (`Kanal=Prozent; …`), Booking.com-Genius-Rabatt und Anteil Genius-Buchungen (unbekannt → 100 %, vorsichtige Annahme). Fixkosten gehören nicht hierher. Neue Kennzahlen in der Statistik: `var_kosten`, `db`, `db_pro_nacht`, `db_revpar`.

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
| `freigabe` | Ab hier gilt die Wohnung als frei (Abreisezeit bzw. Standard-Check-out + Wartezeit) |
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

Die Integration bringt eigene Karten mit. Sie werden automatisch geladen (keine Ressource eintragen) und erscheinen im Kartendialog unter „Smoobu …“. Ein Klick auf eine Buchung öffnet überall dieselbe Detailansicht: Gast und Kontakt mit **Stammgast-Hinweis** (frühere Aufenthalte, letzter Besuch), Preis mit Positionen, Provision, Gebühr und Netto, Zahlung/Anzahlung als erhalten markieren, Notiz bearbeiten, Ankunfts-/Abreisezeit ändern, **Umbuchen** (Zeitraum/Unterkunft einer Direktbuchung, Beta), Nachrichtenverlauf und Antwort, Sperre löschen bzw. Direktbuchung stornieren.

| Karte | Inhalt | Optionen |
|---|---|---|
| `custom:smoobu-header-card` (ab 1.15.0) | Kopfleiste: Seiten-Navigation (mit Zähler offener Nachrichten), **„✨ Neu“** (ungelesene Neuerungen mit Link zur Stelle, gelesen je HA-Benutzer), **Wohnungsauswahl** „Alle / Wohnung …“ (ab 2 Wohnungen), **Hell / Dunkel / System**. Färbt auch den Seitenhintergrund passend | `pages` (Liste `name`, `path`, optional `badge: nachrichten`, `optional: true` = nur zeigen, wenn die Ansicht existiert; Pfade relativ zum Dashboard), `show_apartments`, `page_background` |
| `custom:smoobu-overview-card` | Status heute als kurzer Satz, aktueller und nächster Gast, Belegung der nächsten Wochen mit Preisen, Kennzahlen mit 12-Monats-Verlauf und Vorjahr, Prognose, nächste Anreisen, **freie Zeiträume mit Prüfung gegen den Mindestaufenthalt**, Aufgaben-Board „Wartet auf dich“ (Reiter Nachrichten, Rechnungen, Preise, Last-Minute, Lücken, Einrichtung; Erledigt/Später für alle Benutzer) | `title`, `entities` (eigene HA-Entitäten als Chips), `upcoming`, `gap_days`, `band_days` (42), `apartment_id` |
| `custom:smoobu-timeline-card` | Kalender & Preise je Monat mit Kanalfarben, Sperrzeiten, Tagespreis, Mindestaufenthalt, nicht buchbaren Lücken. **Anreise und Abreise antippen** (ein Tipp = 1 Nacht) → **sperren** oder **Preis/Mindestaufenthalt setzen** | `title`, `months` (3), `show_prices`, `actions`, `apartment_id` |
| `custom:smoobu-bookings-card` | Buchungsliste: Suche, Zeitraum, Kanal- und Statusfilter (inkl. Stornos, Sperrzeiten), Sortierung, Trennzeilen Anstehend/Aktuell/Vergangen mit Summen, **Stammgast-Abzeichen**, CSV-Export | `title`, `period`, `status`, `apartment_id` |
| `custom:smoobu-analytics-card` | Finanzen: dieselbe Filterleiste wie die Statistik (Monat/Quartal/Saison/Jahr/Frei mit ‹ › blättern, Vergleich Stichtag Vorjahr/Ganzes Vorjahr/Vorperiode/Kein, Raster Auto/Tag/Woche/Monat, Wohnung, Kanäle mehrfach), dazu Schnellwahl (Vormonat, Folgemonat, Vorjahr, Jahr bis heute, letzte/nächste 12 Monate, gesamter Zeitraum) und Mehrfachvergleich über mehrere Jahre bzw. Perioden (Tabelle und zusätzliche Linien). Bei „Stichtag Vorjahr“ zusätzlich der **Endstand** des Vergleichszeitraums in den Kacheln. Kennzahlen mit Veränderung, gestapeltes Diagramm je Kanal mit Vergleichslinie, Anteile, Erkenntnisse, Kanaltabelle | `title`, `period` (`monat`/`quartal`/`saison`/`jahr`/`custom` oder ein Schnellwahl-Schlüssel), `compare` (`stichtag` Standard, `vorjahr`, `vorperiode`, `kein`), `compare_count` (Standard 1), `raster` (`auto`), `apartment_id` |
| `custom:smoobu-stats-card` | Statistik-Werkbank: Aussage-Satz, Filterleiste (Monat/Quartal/Saison/Jahr/frei, Vergleich Stichtag Vorjahr/Vorjahr/Vorperiode, Kanäle, Wohnung, Raster), Ansicht Werkbank/Einfach je Gerät; 14 Module (Kennzahlen mit Fokus-Verlauf, **Deckungsbeitrag** (Netto − variable Kosten mit Brücke Preis/Nächte/Kosten je Nacht), **Bewertung & Empfehlung** (Buchungsstand je Monat gegen die Vorjahre am gleichen Tag, Preis senken/halten/erhöhen in Schritten, Preisuntergrenze je Kanal aus den variablen Kosten, Hinweise zu Wochenende, Einzelnächten, Feiertagen und kurzen Lücken – auch in „Einfach“; Empfehlungen und Hinweise per Button übernehmen, änderbar, mit Vorschau und Rückgängig), Buchungstempo mit Prognose-Spanne, Saison-Matrix (mit Abweichung zum Ø, auch DB), Belegung nach Wochentag, Kanal-Wirtschaftlichkeit, Buchungsfenster, verlorene Nächte, Stornos, Gäste (Anteil Buchungen und Nächte), **Ehrentafel** (Fun-Statistik: „Die Goldene Fußmatte“ und „Die Rostige Klobürste“ – je Top 3 der abgeschlossenen Aufenthalte nach Preis je Nacht, Kommunikation, Extra-Stunden durch frühen Check-in/späten Check-out, Vorlauf, Aufenthaltsdauer und Portal-Abzug; Perzentil-Rang je Kriterium, fehlende Werte neutral; Vorname + Initial; nur Anzeige, nichts wird gespeichert), Service/Antwortzeit, Datentabelle mit CSV) plus Baukasten für eigene Module (Vorlagen, Live-Vorschau, nachträglich bearbeiten, Darstellung im Modulkopf umschalten); Anordnung und eigene Module im HA-Benutzerprofil (alle Geräte, übersteht Updates). Zeitraum „Saison“ nach den eingestellten Saisons. Werte mit n < 5 als „wenig Daten“ markiert | `title`, `period`, `compare`, `matrix_exclude_years` (Standard `[2020]`), `matrix_since`, `apartment_id` |
| `custom:smoobu-inbox-card` | Posteingang: laufende, kommende und kürzliche Buchungen, Nachrichtenverlauf, antworten, ✨ KI-Vorschlag. **Antwort offen** = neueste Nachricht kommt vom Gast (Nachrichten an den Gast, auch automatische, schließen); Button **„Keine Antwort nötig“** hakt sie ohne Antwort ab, bis der Gast erneut schreibt (rückgängig machbar) | `title`, `days_back`, `days_ahead`, `message_entity` |
| `custom:smoobu-cleaning-card` (ab 1.19.0) | Reinigungsboard: Reinigungen je Abreise (Check-out, nächste Anreise mit Uhrzeit/Personen/Hund, Gästewechsel), Filter Für mich / Nicht zugewiesen / Alle offenen / Erledigt; **zuweisen** und **Reinigungstag planen** mit automatischer Sperre (Recht „Reinigung zuweisen“), **übernehmen/abgeben** und **abhaken** (Recht „Reinigung übernehmen und abhaken“); vom Gast nur der Vorname. Push an die zugewiesene Person über das in den Einstellungen gewählte Handy | `title`, `days` (30), `apartment_id` |
| `custom:smoobu-assistant-card` | KI-Assistent: Wissensdatenbank (freigeben, bearbeiten, vertraulich), Vorschläge, Gelerntes, Lücken, Import | `title` |
| `custom:smoobu-settings-card` | Einstellungen im Dashboard: Benachrichtigungen (Push-Arten, Empfänger, Uhrzeiten, Ruhezeit), KI-Assistent, Preise & Kanäle (Provisionen, Direktkanäle, Aufschläge, Genius, Last-Minute), Kosten, Reinigung & Zugang (Reinigungskosten, Pushes an Reinigungskräfte, Türcodes), Benutzer & Rechte (Rollen Verwalter/Betrieb/Mitarbeiter/Reinigung/Nur lesen/Kein Zugriff und eigene Rollen; ab 1.19.0 **Rechte je Rolle einstellbar**, **abschaltbare Module** (Reinigung, Kosten, Preise) und **Fokus-Modus** – Benutzer ausgewählter Rollen sehen in HA nur Smoobu, ohne Seitenleiste und Menüs (Oberflächen-Sperre, nicht der HA-API); nur Admins vergeben und stellen Rollen ein; Prüfung im Backend für Karten und `smoobu.*`-Aktionen), Allgemein & Abruf inkl. Wohnungskürzel und **Saisons** (mit automatischer Erkennung) – dieselben Werte wie der Options-Dialog, dazu Optionen, die es nur hier gibt. Ändern dürfen HA-Admins und die in der Option „Einstellungen im Dashboard erlauben für“ gewählten Benutzer (Prüfung im Backend); nach dem Speichern lädt die Integration neu | `title`, `tab`, `entry_id` |

**Design (ab 1.15.0):** Eigene, aufeinander abgestimmte Farben für hell und dunkel (Kanäle, Zustände, Flächen) und die Schrift *Schibsted Grotesk* (SIL OFL, wird mit der Integration ausgeliefert, kein externer Server). Der Modus wird **je Gerät** gespeichert; „System“ folgt dem Dunkelmodus von Home Assistant.

**Mehrere Wohnungen (ab 1.15.0):** Ohne `apartment_id` folgen alle Karten der Wohnungsauswahl der Kopfleiste (je Gerät gespeichert). „Alle“ zeigt Daten aller Wohnungen zusammen: Umsätze summiert, Auslastung über alle verfügbaren Nächte, Listen mit Wohnungskürzel (automatisch aus dem Namen, z. B. „Haus Seeblick“ → „HS“), Kalender mit einer Zeile je Wohnung, Finanzen mit Wohnungsvergleich. Sperren und Preise gelten immer für die markierte Wohnung. Eine Karte mit `apartment_id` bleibt fest bei dieser Wohnung. Bei nur einer Wohnung gibt es keine Auswahl.

```yaml
# Beispiel: eigene Seite „Smoobu“ mit Kopfleiste, Übersicht und Kalender
type: custom:smoobu-header-card
---
type: custom:smoobu-overview-card
entities:
  - climate.ferienwohnung
---
type: custom:smoobu-timeline-card
months: 4
```

Datenquelle der Karten sind WebSocket-Befehle (u. a. `smoobu/info`, `smoobu/analytics`, `smoobu/stats`, `smoobu/bookings`, `smoobu/booking`, `smoobu/booking/move`, `smoobu/rates`, `smoobu/rates/apply`, `smoobu/tasks/get`, `smoobu/cleaning/get`, `smoobu/cleaning/set`, `smoobu/cleaning/stats`, `smoobu/settings/get`, `smoobu/message_status`, `smoobu/subscribe`). Sie aktualisieren sich bei jedem neuen Datenstand von selbst. Alle Texte aus Smoobu werden vor der Anzeige maskiert.

---

### Dashboard-Vorlage

[`docs/dashboard-vorlage.yaml`](docs/dashboard-vorlage.yaml) ist ein komplettes Dashboard mit 8 Seiten (Übersicht, Kalender, Reinigung, Buchungen, Finanzen, Statistik, Nachrichten, Assistent, Einstellungen) und Kopfleiste – so wie auf den [Screenshots](#screenshots).

1. **Einstellungen → Dashboards → Dashboard hinzufügen → Neues Dashboard von Grund auf**, URL z. B. `dashboard-ferienwohnung`
2. Dashboard öffnen → ✎ → ⋮ → **Raw-Konfigurationseditor** → Inhalt der Vorlage einfügen → Speichern
3. Andere URL gewählt? `/dashboard-ferienwohnung/` in der Vorlage ersetzen. Bei der Übersicht eigene Entitäten unter `entities` eintragen.

---

### KI-Assistent (ab 1.10.0)

Antwortvorschläge für Gästenachrichten auf Basis einer Wissensdatenbank, die aus euren eigenen Antworten lernt. **Nichts wird ohne Bestätigung an Gäste gesendet.**

- **KI-Sperre (ab 1.14.0):** Option **„KI-Funktionen erlauben“** (Optionen → KI-Assistent). Aus = jeder KI-Aufruf wird abgelehnt – zentral in der Integration, also auch über Aktionen, WebSocket, Push-Buttons und Webhook. Die Karten grauen ✨ Vorschlag und 📚 Wissen erzeugen aus und zeigen „🔒 KI gesperrt“. **Ohne KI weiter nutzbar:** Wissensdatenbank pflegen, Lernen aus gesendeten Antworten, Verlauf importieren, Tagesbriefing, Lücken-Meldung, Nachrichten senden.

- **Ablauf:** Neue Gästenachricht (Webhook) → Entwurf per `ai_task.generate_data` (Anbieter frei wählbar, z. B. Google Gemini) → Push an die gewählten Handys mit **Senden / Bearbeiten / Ignorieren**; erkennt der Assistent eine neue Ankunftszeit, gibt es zusätzlich **„Ankunft HH:MM übernehmen“**.
- **Keine Erfindungen:** Die Anweisung erlaubt nur Fakten aus Wissen, Buchung, Belegung und HA-Status. Unbekanntes wird als `[OFFEN: …]` markiert, als Wissenslücke gemeldet und blockiert das Senden per Push.
- **Wissensdatenbank** (in HA gespeichert, Karte `custom:smoobu-assistant-card`): Einträge Thema + Text, Status aktiv/Vorschlag/aus, **vertraulich** = geht nie an die KI.
- **Lernen:** Jede gesendete Antwort (Karte, Push, direkt in Smoobu) wird mit der Gästenachricht davor gespeichert; neue Vorschläge orientieren sich an den ähnlichsten Beispielen (lokale BM25-Suche). Aktion `smoobu.assistant_import` übernimmt den bisherigen Verlauf, `smoobu.assistant_build_knowledge` schlägt daraus Wissenseinträge vor.
- **Kontext:** Buchung, Belegung davor/danach (früher Check-in / später Check-out), frei wählbare HA-Entitäten (z. B. Heizung, Tür, Außentemperatur) – bei Problemen („kalt“, „kein Wasser“) Push als **dringend** mit Hinweis.
- **Zusatzaufgaben (Optionen):** Tagesbriefing per Push, tägliche Meldung nicht buchbarer Lücken (Mindestaufenthalt) mit Button zum Anpassen.
- **Entitäten/Aktionen:** `sensor.smoobu_assistent_offene_vorschlage`, `smoobu.assistant_suggest` (Anlass: antwort, willkommen, anreise, abreise, bewertung), WebSocket `smoobu/assistant/*`.
- **Datenschutz:** Nur bei erlaubter KI gehen Gästenachrichten und Buchungsdaten an den gewählten KI-Anbieter (vertrauliche Wissenseinträge nie). Was genau, legt die **Datenschutz-Stufe** fest (ab 1.18.0b6, siehe unten).

#### Datenschutz-Stufe für die KI (ab 1.18.0b6)

Option **„Datenschutz-Stufe“** (Optionen → KI-Assistent bzw. Einstellungskarte → KI-Assistent → Datenschutz). Fehlt die Option (bestehende Installation), gilt **Standard**.

| Stufe | Was an die KI geht | Einbuße |
|---|---|---|
| **Standard** (empfohlen) | Gastnamen als Platzhalter (`[GAST_VORNAME]`, `[GAST_NAME]` …), die Integration setzt sie nach der Antwort lokal wieder ein. Adresse, PLZ/Ort, Kennzeichen, Geburtsdatum und Ausweisnummer geschwärzt. Daten relativ („Fr., in 3 Tagen“, im Entwurf als `[ANREISE]` und lokal ersetzt). Namen in Lernbeispielen (über die Buchung des Beispiels), im Verlauf und in Status-Entitäten (laufende und nahe Gäste) ebenfalls ersetzt. | praktisch keine |
| **Streng** | wie Standard, dazu nur 2 Nachrichten Verlauf, ohne Kanal und Bezahlstatus | gering |
| **Maximal** | nur die geschützte Gästenachricht und die Wissensdatenbank – keine Buchungsdaten, kein Verlauf, keine Beispiele, keine Status-Entitäten | hoch: Antworten allgemeiner, Ton nicht mehr eurer, Zeiten und Probleme bleiben `[OFFEN]` |
| **Individuell** | jeder Schalter einzeln, mit Beschreibung der Einbuße | je nach Wahl |

- **Eigene Namen** (Standard: Wörter aus dem Kontonamen) werden nie ersetzt, z. B. eure Signatur.
- **„Was geht an die KI?“** in der Einstellungskarte: „Letzte KI-Anfrage“ zeigt den exakt gesendeten Text (nur im Speicher, nach Neustart leer), „Probelauf nächste Buchung“ baut den Text für die laufende bzw. nächste Buchung, ohne die KI aufzurufen (geht auch bei gesperrter KI). WebSocket `smoobu/assistant/preview`.
- **Grenzen:** Ersetzt werden nur **bekannte** Namen aus den Smoobu-Buchungen. Andere Namen im Freitext (Begleitpersonen, Kinder) und alles, was keinem Muster folgt (z. B. „mein Sohn hat eine Nussallergie“), bleiben stehen. Die Gästenachricht selbst muss die KI lesen, um zu antworten. **Vollständig anonym ist das nicht.** Pseudonymisierte Daten gelten nach DSGVO weiter als personenbezogen; für einen Cloud-Anbieter braucht ihr einen Auftragsverarbeitungsvertrag. Nichts verlässt das Haus nur mit einer lokalen KI (z. B. Ollama als `ai_task`-Entität).

![Datenschutz-Stufe](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_datenschutz.png)
![Probelauf: was an die KI ginge](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/datenschutz_probelauf.png)

---

### Lexware Office (Beta, ab 1.20.0)

> **BETA** – noch nicht mit einem echten Lexware-Konto bestätigt. Jeden Entwurf in Lexware prüfen.

Optionales Modul für die [Lexware Office Public API](https://developers.lexware.io/docs/) (laut Lexware ab Tarif **XL**). Einschalten unter Einstellungen → Reiter **„Lexware (Beta)“** (oder Options-Dialog, letzter Schritt) mit dem API-Key aus Lexware (Erweiterungen → Public API). Ohne XL lässt sich alles im **Testmodus** mit Beispielartikeln ausprobieren – dabei wird nichts gesendet.

- **Positionen:** je Kanalgruppe (Direkt/Portal) eine Liste von Regelzeilen. Jede Zeile = ein Lexware-Artikel (Bezeichnung, Einheit, Steuersatz aus Lexware) mit Menge (pauschal, je Nacht, je Person/Zusatzperson, je Kind, je Hund mit Obergrenze …), optionaler Bedingung (z. B. nur bis 14 Nächte) und Preis aus dem Artikel oder **Rest aus dem Buchungspreis** – so stimmt die Summe immer mit Smoobu. „Vorlage übernehmen“ legt eine typische Ferienwohnungs-Rechnung an. Platzhalter `[Portal]`, `[n]`, `[Nächte]`, `[Fällig]`, `[Betrag]`, `[Anzahlung]` ersetzt die Integration.
- **Rechnung:** Button „Rechnungsentwurf erstellen“ in den Buchungsdetails → Vorschau (Mengen, Preise, Hunde, Gesamtrabatt, Firma, Kontakt) → Lexware bekommt einen **Entwurf**; finalisiert wird in Lexware. Rechnungsdatum = heute, **fällig am Anreisetag** (so zeigt Lexware die Rechnung bis zur Anreise als offen, nicht als überfällig). Privatgäste brutto, Firmen netto (einstellbar); bei Firmen wird der Gast Ansprechpartner.
- **Kontakt:** Suche über den Namen (bei Firmen Firmenname), nur exakte Treffer; mehrere Treffer → Auswahl in der Vorschau; sonst neuer Kunde.
- **Zahlungen:** Abgleich per Webhook (öffentliche HTTPS-URL, z. B. Nabu Casa) und stündlich. Soll-Anzahlung = Anzahlung aus Smoobu, sonst 50 % (einstellbar). Hinweise in „Wartet auf dich“ und Push „Rechnungen & Zahlungen“: Anzahlung nach n Tagen nicht da (Storno möglich – die Integration storniert nie selbst), Rest am Anreisetag offen, Entwurf nicht finalisiert, Rechnung fehlt.
- **Bedeutung „bezahlt“** (auch ohne Lexware): je Kanalgruppe „Zahlung erhalten“ oder „Rechnung gestellt“ von Hand – mit Lexware automatisch „Zahlung laut Lexware“ bzw. „Rechnung gestellt laut Lexware“ (nur Lexware → Smoobu).
- **Recht:** „Rechnungen erstellen (Lexware)“; den Zahlungsstand sieht, wer „Finanzen“ sehen darf.

![Lexware: Rechnung in den Buchungsdetails](docs/screenshots/lexware_rechnung.png) ![Lexware: Vorschau](docs/screenshots/lexware_vorschau.png)

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
- **Reinigungsdaten (Beschäftigte):** Das Reinigungsboard speichert je erledigter Reinigung, **wer** gereinigt hat und wer abgehakt hat, dazu Tag, Wohnung und Dauer – keine Gastnamen. Bei angestellten Reinigungskräften sind das Beschäftigtendaten: Informiert die Personen, dass und wofür (Einsatzplanung, Abrechnung, Kosten je Aufenthalt) das erfasst wird (Art. 13 DSGVO). Nach der Frist **„Person aufbewahren“** (Einstellungen → Reinigung & Zugang → Datenschutz, Standard **10 Jahre** = steuerliche Aufbewahrung) wird die Person automatisch zu **„Unbekannt“**; die Statistik bleibt. Offene, nicht erledigte Einträge verfallen nach 60 Tagen.
- **Verantwortlich** für die Verarbeitung (DSGVO) bist du als Betreiber der Home-Assistant-Installation. Die Integration speichert alles lokal in Home Assistant; an Dritte gehen Daten nur an Smoobu selbst und – wenn eingeschaltet – an den gewählten KI-Anbieter (siehe Datenschutz-Stufe).
- **Lexware (Beta):** Für Rechnungen gehen Name, Adresse, E-Mail, Telefon, Zeitraum und Preis des Gastes an Lexware Office – nur auf Knopfdruck. Rechnungsdaten gehen nie an die KI. Der API-Key liegt in den Optionen und wird nie an die Dashboard-Karten geschickt.
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
- [Screenshots](#screenshots-1)
- [Requirements](#requirements)
- [Create a Smoobu API key](#create-a-smoobu-api-key)
- [Installation](#installation-1)
- [Setup](#setup)
- [Options](#options)
- [Entities](#entities)
- [Actions](#actions)
- [Dashboard cards](#dashboard-cards-since-180)
- [Dashboard template](#dashboard-template)
- [AI assistant and AI lock](#ai-assistant-since-1100)
- [Lexware Office (beta)](#lexware-office-beta-since-1200)
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

**Data in Home Assistant**
- 📅 **Occupancy calendar per property** with full guest name, channel, guests, price and contact details
- 👤 **Sensors for the current and next booking** (guest name, first name, guests, arrival, departure) and **binary sensors** (occupied, arrival/departure/changeover today, dog with current/next guest)
- 📊 **KPI sensors:** bookings, occupancy and revenue (month/year/previous year, split by nights), unpaid bookings, year-end forecast, one sensor per channel
- ⚡ **Real-time webhook** (Nabu Casa or your own HTTPS URL, registered with Smoobu automatically) and event **`smoobu_event`** for new, changed or cancelled bookings and new guest messages
- 🛠️ **Actions:** query bookings, read and send messages, block periods, set prices and minimum stay, change arrival/departure time, note and payment status

**Smoobu dashboard** (own cards, loaded automatically, ready-made [dashboard template](docs/dashboard-vorlage.yaml) with 9 pages)
- 🏠 **Overview:** today's status in one sentence, current and next guest, occupancy of the next weeks, KPIs with trend, free periods checked against the minimum stay, task board **"Waiting for you"** (messages, invoices, prices, last-minute, gaps, **setup**) with done/later
- 🗓️ **Calendar & prices:** channel colours, daily price, minimum stay, unbookable gaps; tap arrival and departure → **block** or **set price**
- 📋 **Bookings:** search, filters, totals per group (upcoming/current/past), **returning guests** ("↻ 2× · May 25"), CSV export; details with payment status, times, note, messages and **rebooking** (dates/property, beta)
- 💶 **Finances:** period, comparison (same day last year, full previous year, previous period, several years), channels, grid; chart per channel, channel table, insights
- 📈 **Statistics workbench:** rating & recommendation (apply prices with one click and undo), **contribution margin** with bridge, booking pace with forecast, season matrix with deviation from the average, weekdays, channels, booking window and timing, lost nights, cancellations, guests, hall of fame, service, **cleaning** (who cleaned which property when); **custom modules** with templates, preview and editing; arrangement stored in the HA user profile
- 🌦️ **Seasons** freely adjustable (name + start month) with **automatic detection** from past years
- 💬 **Inbox:** open guest messages, "No reply needed", AI suggestion
- 🧾 **VAT (optional):** amounts excluding VAT in finances, statistics and revenue sensors – with "VAT liable since", rates with validity, tax type per Smoobu price element and costs without input VAT; toggle gross / excl. VAT
- 🧾 **Lexware Office (BETA, optional, Lexware plan XL and up):** draft invoice by button from the booking details based on your Lexware articles (per night, extra person, child, dog, final cleaning up to/from n nights, remainder of the booking price), companies net with the guest as contact person, payment status (deposit/full) and notices in "Waiting for you"
- 🔑 **Door codes:** random code per booking (digits configurable, no trivial codes), valid from check-in − 2 h to check-out + 1 h (configurable), in the Smoobu note, in the booking details, as an entity and optionally written to the lock (Matter, Z-Wave JS, ZHA, Zigbee2MQTT or own script); in replies as placeholder `{{ turcode }}`, replaced locally only when sending
- 🧹 **Cleaning board:** one cleaning per departure with check-out, next arrival and same-day changeover; **assign**, take over and tick off, push to the assigned person (on assignment and the evening before)
- ⚙️ **Settings in the dashboard** with a **role configurator** (permissions per role via checkboxes, custom roles, role **Cleaning** – sees only the guest's first name); new options appear under "Waiting for you" → Setup, changes under **"✨ New"** in the header
- 🎨 Light/dark/system, several properties with a combined view, mobile view

**Notifications and AI**
- 🔔 **Pushes** per type on/off with own recipients and quiet hours: new booking, cancellation/change, **rebooking** (dates/property), guest message, AI suggestion, payment reminder, daily briefing, gaps
- 🤖 **AI assistant (optional):** reply suggestions with a knowledge base and privacy levels; **can be switched off completely** (no data sent to an AI provider)

**Technical**
- 🔐 **HMAC-SHA256 signing** according to the current Smoobu specification
- 🌍 German and English, set up entirely in the UI, diagnostics download with redacted guest data

---

### Screenshots

All images show a **fictional demo apartment**. They come from the real integration (version 1.19.0), but with demo data (`tools/screenshots/`). No real guest or revenue data appears in them. The screenshots show the German interface; the cards follow the Home Assistant language.

**Overview, light and dark:** today's status in one sentence, current and next guest, occupancy of the next 6 weeks with prices, KPIs with 12-month trend, upcoming arrivals, free periods and the task board "Waiting for you" with tabs and counters (reply, mark payments as received, apply prices, adjust gaps, setup)
![Overview light](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_uebersicht_hell.png)
![Overview dark](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_uebersicht_dunkel.png)

**What's new and setup:** "✨ New" in the header lists changes with a link to the location; new options appear under "Waiting for you" → Setup with "Configure →"
![What's new](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/was_ist_neu.png)
![Setup](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/wartet_einrichtung.png)

**Statistics workbench:** summary sentence, KPIs with comparison and final value, rating & recommendation, booking pace, season matrix and more modules (workbench on the PC, simple view on the phone)
![Statistics](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_statistik_hell.png)

**Cleaning board (from 1.19.0):** one cleaning per departure with check-out, next arrival (time, guests, dog) and same-day changeover; assign via dropdown, take over, tick off; works well on the phone
![Cleaning](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/reinigung.png)
![Cleaning on the phone](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/reinigung_handy.png)

**Statistics "Cleaning":** who cleaned which property when – per person (share, changeovers, dogs, average guests, nights, time to tick off), per month, per property and as a list
![Statistics cleaning](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/statistik_reinigung.png)

**Door codes (from 1.19.0):** digits, validity, Smoobu note and lock per property
![Door codes](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_tuercode.png)

**Electricity costs (from 1.19.0):** constant as before or measured from the property's meter – pre-heating start to check-out, vacancy separately or distributed, grid share hourly from the energy dashboard. **Grid share (from 1.19.1b5)** either from a grid import sensor of the property (e.g. a sensor that splits the property's consumption into grid/PV by self-sufficiency at the same time; gaps such as imported monthly values are averaged), hourly from the energy dashboard (whole house), from 12 fixed monthly values or as one annual value
![Electricity costs](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_strom.png)

**Utility bill (from 1.19.0):** upload a PDF, the AI reads the values, suggestion with derivation, source location and checks – applied only after confirmation
![Utility bill](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_nebenkosten.png)

**Role configurator (from 1.19.0):** permissions per role via checkboxes, custom roles; hint for combinations that are hardly usable in the dashboard
![Roles](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_rollen.png)

**Contribution margin:** net minus variable costs with comparison; the bridge shows what price per night, number of nights (revenue minus saved costs) and costs per night changed
![Contribution margin](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/statistik_deckungsbeitrag.png)

**Season matrix:** months × years with deviation from the month's average (▲/▼, occupancy in percentage points); measures occupancy, revenue, ADR, RevPAR, net, CM
![Season matrix](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/statistik_saisonmatrix.png)

**Seasons with automatic detection:** own seasons with name and start month; suggestions for 2, 3 and 4 seasons from past years
![Seasons](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_saisons.png)

**Calendar & prices:** tap arrival and departure → block or set price; channel colours, daily price, minimum stay, unbookable gaps
![Calendar](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/kalender_auswahl.png)

**Bookings:** totals per group, returning guests with number of earlier stays and last visit, filters and CSV export
![Bookings](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_buchungen_hell.png)

**Rebooking (beta):** change the dates or property of a direct booking – with availability check and price suggestion
![Rebooking](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/umbuchen.png)

**Several properties:** select "All" or one property at the top right; combined view with status per property and one calendar row per property
![All properties](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_uebersicht_alle_hell.png)
![Calendar all properties dark](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_kalender_alle_dunkel.png)

<details><summary>More: finances, inbox, booking details, settings, assistant, AI locked, mobile</summary>

![Finances](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_finanzen_hell.png)
![Inbox](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/posteingang.png)
![Booking details](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/buchungsdetails.png)
![Booking details with open payment](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/buchungsdetails_zahlung.png)
![Settings costs](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_einstellungen_kosten_hell.png)
![Settings privacy](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_datenschutz.png)
![Assistant](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/assistent.png)
![Inbox with AI locked](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/ki_gesperrt_posteingang.png)
![Statistics on the phone](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/seite_statistik_handy_dunkel.png)

</details>

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
| Default check-out | 11:00 | Used when the booking has no departure time (official check-out time) |
| Channels paid via the portal | Airbnb, Booking.com | Bookings from these channels do not count as unpaid |
| Waiting time after check-out | 30 min | Time until the actual release (e.g. cleaning start): release = departure time or default check-out + waiting time, e.g. 11:00 + 30 min = 11:30 |
| Days back | 30 days | How far back bookings are loaded |
| Days ahead | 365 days | How far ahead bookings are loaded |
| Fetch details for next n bookings | 3 | The current and next n bookings per apartment are additionally fetched one by one (first/last name, city tax, price details) |

Step **Commissions**: commission per channel in %, direct channels. Step **AI assistant**:

| Option | Default | Meaning |
|---|---|---|
| **Allow AI features** | off (installations before 1.14.0 with an AI selected: on) | Master switch. Off = AI **locked**: no `ai_task` call, no data sent to an AI provider, AI buttons in the cards greyed out. Applies to cards, actions, WebSocket, push buttons and webhook |
| Automatic reply suggestions | on (only effective with AI allowed) | Create a suggestion for every new guest message and push it (only with AI allowed) |
| AI (AI task) | – | `ai_task` entity, e.g. Google Gemini; required when AI is allowed |
| HA entities as context | – | e.g. heating, door, outdoor temperature |
| Dashboard page for "Edit" | `/lovelace` | e.g. `/dashboard-ferienwohnung/smoobu-nachrichten` |

Step **Notifications** (since 1.17.0) – per push type on/off and own recipients (`notify.mobile_app_*`; empty = previous assistant recipients):

| Push type | Default | When |
|---|---|---|
| New booking | off | immediately (quiet hours respected) |
| Cancellation / change | off | immediately, before → after (guests, arrival time, price) |
| Rebooking (since 1.18.0) | like "Cancellation / change" | immediately when dates or property change: before → after with nights or property names; when switched off the change arrives under "Cancellation / change" |
| New guest message | off | immediately when no AI suggestion is sent; removed after reply/mark done |
| AI reply suggestion | on | immediately, non-urgent ones collected during quiet hours |
| Payment reminder | off, 7 days, 09:00 | daily at the time: open amount X days before and on the arrival day |
| Daily briefing | off, 07:30 | daily at the time, works without AI |
| Unbookable gaps | off, 09:05 | daily at the time, works without AI |
| **Quiet hours** | off, 21:00–07:00 | Set per push type ("Respects quiet hours"): those pushes are collected and delivered at the end (latest state per topic). Default: booking, cancellation/change and AI suggestion wait; guest message, payment, briefing and gaps arrive immediately. Urgent suggestions and confirmations always arrive immediately |

Step **Property codes** (since 1.17.0): own code per property (up to 4 characters, letters/digits, unique across accounts); empty = automatic. Used in dashboard and pushes.

The integration reloads automatically after saving.

---

### Entities

Each Smoobu apartment becomes a device **"Smoobu &lt;apartment name&gt;"**, plus one device **"Smoobu"** for the account.

**Naming:** `<domain>.smoobu_<apartment_name>_<entity>`. The apartment name comes from Smoobu, the entity part from the Home Assistant system language. With several apartments, each gets its own set of entities. The examples below are for an apartment named "Apartment" with English system language. With German system language the entity IDs are German (see [Deutsch](#deutsch)).

#### Per apartment

| Entity | Example ID | Content |
|---|---|---|
| Calendar | `calendar.smoobu_apartment_occupancy` | All bookings. Title = guest name, with 🐕 for dogs (blocked periods: "Blockiert"). Start = arrival + check-in time, end = departure + check-out time. |
| Occupied | `binary_sensor.smoobu_apartment_occupied` | On from check-in time until release (departure time or default check-out + waiting time) |
| Arrival today | `binary_sensor.smoobu_apartment_arrival_today` | A guest arrives today |
| Arrival tomorrow | `binary_sensor.smoobu_apartment_arrival_tomorrow` | A guest arrives tomorrow (same attributes as "Arrival today", incl. `hund`) |
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
| Last guest message | `sensor.smoobu_last_guest_message` | Text of the latest message **from the guest** (loaded via webhook `newMessage`, survives restarts; since 1.14.0 your own messages to the guest do not change it). Attributes: `text`, `betreff`, `absender`, `gast`, `buchungs_id`, `empfangen` |

#### Direct marketing vs. portals, net revenue

Gross = booking price from Smoobu. Commission = the value Smoobu sends with the booking (`commission-included`, usually present for Airbnb and Booking.com), otherwise the channel percentage from the options. Booking.com payment charges are read from the booking. Net = gross − commission − payment charge, prorated by nights.

| Entity | Example ID | Content |
|---|---|---|
| Revenue after commission month / year (until 1.19: net revenue) | `sensor.smoobu_apartment_revenue_after_commission_month` / `…_year` | Revenue after commission/fees; attributes `brutto`, `provision`, `zahlungsgebuehren`, `kostenquote_prozent`, `davon_bis_heute`, `vorjahr_gesamt`, `vorjahr_bis_heute`, change, `monate`, `monate_vorjahr`, `kanaele` |
| Commission & fees year | `sensor.smoobu_apartment_commission_fees_year` | Commission + payment fees; `je_kanal`, previous year, cost ratio |
| Direct / portal revenue year | `sensor.smoobu_apartment_direct_revenue_year` / `…_portal_revenue_year` | Gross of the group; net, bookings, nights, net per night, share, year-to-date, previous year, monthly values |
| Direct share year | `sensor.smoobu_apartment_direct_share_year` | % of gross revenue; share of nights, previous year, change in points, `ersparnis_direkt` (direct revenue × portal cost ratio), per-channel tables |

Per guest additionally: channel group (direct/portal), commission and net price; price sensors carry `kanal_gruppe`, `provision`, `provision_quelle`, `zahlungsgebuehr`, `netto`.

**Options → step "Commissions":** % per channel (defaults Airbnb 15.5 · Booking.com 15 · FeWo-direkt 8 · Website 0 · Direct booking 0), other portals (15), further channels as `Channel=percent; …`, direct channels (default: Direct booking, Website). In the settings card you pick channels from a dropdown: channels with bookings first (with count), then those used in the settings, then all other Smoobu channels. Smoobu has no API endpoint for connected channels, so a connected portal without bookings (e.g. HomeToGo) is in the catalogue group.

**Options → step "Costs & prices" (from 1.18.0):** variable costs for the contribution margin (net − variable costs) and the markups from the Smoobu pricing tool for recommendations. Cleaning and laundry per stay; heating and hot water costs of the billing year (from the utility bill), spread by heating degree days (January 170 ‰ … July 13 ‰ – a January night costs ≈ 12× a July night) and scaled to the guest nights of the billing year; water per night; electricity in kWh per night with a grid share per month (grid power at the grid price, PV power at the feed-in tariff). Markups per channel (`Channel=percent; …`), Booking.com Genius discount and share of Genius bookings (unknown → 100 %, cautious assumption). Fixed costs don't belong here. New statistics measures: `var_kosten`, `db`, `db_pro_nacht`, `db_revpar`.

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
| `freigabe` | Release: apartment counts as vacant from here (departure time or default check-out + waiting time) |
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

The integration ships its own cards. They are loaded automatically (no resource needed) and appear in the card picker as "Smoobu …". Clicking a booking opens the same detail view everywhere: guest and contact with a **returning-guest note** (earlier stays, last visit), price with line items, commission, fee and net, mark payment/prepayment as received, edit note, change arrival/departure time, **rebooking** (dates/property of a direct booking, beta), message thread and reply, delete a block or cancel a direct booking.

| Card | Content | Options |
|---|---|---|
| `custom:smoobu-header-card` (since 1.15.0) | Header: page navigation (with open-message counter), **"✨ New"** (unread changes with a link to the location, read state per HA user), **property selector** "All / property …" (from 2 properties), **Light / Dark / System**. Also colours the page background | `pages` (list of `name`, `path`, optional `badge: nachrichten`, `optional: true` = only shown if the view exists; paths relative to the dashboard), `show_apartments`, `page_background` |
| `custom:smoobu-overview-card` | Today's status as a short sentence, current and next guest, occupancy of the next weeks with prices, key figures with 12-month trend and previous year, forecast, upcoming arrivals, **free periods checked against the minimum stay**, task board "Waiting for you" (tabs messages, invoices, prices, last-minute, gaps, setup; done/later for all users) | `title`, `entities`, `upcoming`, `gap_days`, `band_days` (42), `apartment_id` |
| `custom:smoobu-timeline-card` | Calendar & prices per month with channel colours, blocks, daily price, minimum stay, unbookable gaps. **Tap arrival and departure** (one tap = 1 night) → **block** or **set price/minimum stay** | `title`, `months` (3), `show_prices`, `actions`, `apartment_id` |
| `custom:smoobu-bookings-card` | Booking list: search, period, channel and status filters (incl. cancellations, blocks), sorting, group rows upcoming/current/past with totals, **returning-guest badge**, CSV export | `title`, `period`, `status`, `apartment_id` |
| `custom:smoobu-analytics-card` | Finance: the same filter bar as the statistics (month/quarter/season/year/custom with ‹ › paging, comparison same day last year/full previous year/previous period/none, grid auto/day/week/month, property, multiple channels), plus quick select (previous month, next month, previous year, year to date, last/next 12 months, whole period) and multi-period comparison across several years or periods (table and extra lines). With "Same day last year" the tiles also show the **final value** of the comparison period. Key figures with change, stacked chart per channel with comparison line, shares, insights, channel table | `title`, `period` (`monat`/`quartal`/`saison`/`jahr`/`custom` or a quick-select key), `compare` (`stichtag` default, `vorjahr`, `vorperiode`, `kein`), `compare_count` (default 1), `raster` (`auto`), `apartment_id` |
| `custom:smoobu-stats-card` | Statistics workbench: summary sentence, filter bar (month/quarter/season/year/custom, comparison same day last year/previous year/previous period, channels, property, grid), Workbench/Simple view per device; 14 modules (KPIs with focus trend, **contribution margin** (net − variable costs with bridge price/nights/costs per night), **assessment & recommendation** (bookings on hand per month vs. previous years on the same day, lower/keep/raise price in steps, price floor per channel from variable costs, notes on weekends, single nights, holidays and short gaps – also in Simple; apply recommendations and notes via button, editable, with preview and undo), booking pace with forecast range, season matrix (with deviation from the average, also CM), occupancy by weekday, channel economics, booking window, lost nights, cancellations, guests (share of bookings and nights), **hall of fame** (fun statistics: "The Golden Doormat" and "The Rusty Toilet Brush" – top 3 completed stays each by price per night, communication, extra hours from early check-in/late check-out, lead time, length of stay and portal deduction; percentile rank per criterion, missing values neutral; first name + initial; display only, nothing is stored), service/response time, data table with CSV) plus a builder for custom modules (templates, live preview, edit afterwards, switch the view in the module header); arrangement and custom modules stored in the HA user profile (all devices, survives updates). Period "Season" follows the configured seasons. Values with n < 5 flagged as "low data" | `title`, `period`, `compare`, `matrix_exclude_years` (default `[2020]`), `matrix_since`, `apartment_id` |
| `custom:smoobu-inbox-card` | Inbox: current, upcoming and recent bookings, message thread, reply, ✨ AI suggestion. **Reply pending** = latest message is from the guest (messages to the guest, including automatic ones, close it); **"No reply needed"** marks it done without replying until the guest writes again (can be undone) | `title`, `days_back`, `days_ahead`, `message_entity` |
| `custom:smoobu-cleaning-card` (from 1.19.0) | Cleaning board: cleanings per departure (check-out, next arrival with time/guests/dog, same-day changeover), filters For me / Unassigned / All open / Done; **assign** (permission "Assign cleaning"), **take over/hand back** and **tick off** (permission "Take over and tick off cleaning"); only the guest's first name. Push to the assigned person via the phone chosen in the settings | `title`, `days` (30), `apartment_id` |
| `custom:smoobu-assistant-card` | AI assistant: knowledge base (approve, edit, confidential), suggestions, learned examples, gaps, import | `title` |
| `custom:smoobu-settings-card` | Settings in the dashboard: notifications (push types, recipients, times, quiet hours), AI assistant, commissions & channels, costs & prices, users & permissions (roles manager/operations/staff/cleaning/read only/no access and custom roles; from 1.19.0 **permissions per role are configurable**; only admins assign and configure roles; checked in the backend for cards and `smoobu.*` actions), general & polling incl. apartment codes – the same values as the options dialog. Editable by HA admins and the users selected in the option "Allow dashboard settings for" (checked in the backend); the integration reloads after saving | `title`, `tab`, `entry_id` |

**Design (since 1.15.0):** dedicated, matched colours for light and dark (channels, states, surfaces) and the *Schibsted Grotesk* typeface (SIL OFL, shipped with the integration, no external server). The mode is stored **per device**; "System" follows Home Assistant's dark mode.

**Several properties (since 1.15.0):** cards without `apartment_id` follow the property selector of the header (stored per device). "All" combines all properties: revenue summed, occupancy over all available nights, lists with a property code (derived from the name automatically), calendar with one row per property, finance with a property comparison. Blocks and prices always apply to the marked property. A card with `apartment_id` stays on that property. With a single property there is no selector.

The cards read data through WebSocket commands (including `smoobu/info`, `smoobu/analytics`, `smoobu/stats`, `smoobu/bookings`, `smoobu/booking`, `smoobu/booking/move`, `smoobu/rates`, `smoobu/rates/apply`, `smoobu/tasks/get`, `smoobu/cleaning/get`, `smoobu/cleaning/set`, `smoobu/cleaning/stats`, `smoobu/settings/get`, `smoobu/message_status`, `smoobu/subscribe`) and refresh themselves on every data update. All texts from Smoobu are escaped before display.

---

### Dashboard template

[`docs/dashboard-vorlage.yaml`](docs/dashboard-vorlage.yaml) is a complete dashboard with 8 pages (overview, calendar, cleaning, bookings, finances, statistics, messages, assistant, settings) and a header card – as shown in the [screenshots](#screenshots-1).

1. **Settings → Dashboards → Add dashboard → New dashboard from scratch**, URL e.g. `dashboard-ferienwohnung`
2. Open it → ✎ → ⋮ → **Raw configuration editor** → paste the template → Save
3. Different URL? Replace `/dashboard-ferienwohnung/` in the template. Add your own entities under `entities` on the overview. Page titles are German – rename as you like.

---

### AI assistant (since 1.10.0)

Reply suggestions for guest messages based on a knowledge base that learns from your own replies. **Nothing is sent to guests without confirmation.**

- **AI lock (since 1.14.0):** option **"Allow AI features"** (Options → AI assistant). Off = every AI call is rejected – centrally in the integration, so also via actions, WebSocket, push buttons and webhook. The cards grey out ✨ Suggestion and 📚 Build knowledge and show "🔒 AI locked". **Still usable without AI:** knowledge base, learning from sent replies, history import, daily briefing, gap report, sending messages.

- **Flow:** new guest message (webhook) → draft via `ai_task.generate_data` (any provider, e.g. Google Gemini) → push to the chosen phones with **Send / Edit / Ignore**; if a new arrival time is detected, also **"Apply arrival HH:MM"**.
- **No invention:** only facts from knowledge, booking, occupancy and HA state are allowed. Unknown items are marked `[OFFEN: …]`, reported as knowledge gaps and block sending via push.
- **Knowledge base** (stored in HA, card `custom:smoobu-assistant-card`): topic + text, status active/suggestion/off, **confidential** = never sent to the AI.
- **Learning:** every sent reply (card, push, directly in Smoobu) is stored with the guest message before it; new suggestions follow the most similar examples (local BM25 search). `smoobu.assistant_import` imports the history, `smoobu.assistant_build_knowledge` suggests knowledge entries from it.
- **Context:** booking, occupancy before/after (early check-in / late check-out), selectable HA entities (heating, door, outdoor temperature) – problem reports are pushed as **urgent** with a hint.
- **Extra tasks (options):** daily briefing push, daily report of unbookable gaps (minimum stay) with a button to adjust.
- **Entities/actions:** `sensor.smoobu_assistant_open_suggestions`, `smoobu.assistant_suggest`, WebSocket `smoobu/assistant/*`.
- **Privacy:** only when AI is allowed are guest messages and booking data sent to the chosen AI provider (confidential knowledge entries never). What exactly is set by the **privacy level** (since 1.18.0b6, see below).

#### Privacy level for the AI (since 1.18.0b6)

Option **"Privacy level"** (Options → AI assistant, or settings card → AI assistant → Privacy). If the option is missing (existing installation), **Standard** applies.

| Level | What goes to the AI | Loss |
|---|---|---|
| **Standard** (recommended) | Guest names as placeholders (`[GAST_VORNAME]`, `[GAST_NAME]` …), restored locally after the reply. Address, postcode/town, licence plate, date of birth and ID number redacted. Relative dates ("Fri, in 3 days", `[ANREISE]` in the draft, replaced locally). Names in learning examples (via the example's booking), the history and status entities (current and upcoming guests) are replaced too. | practically none |
| **Strict** | like Standard, plus only 2 messages of history, no channel and payment status | small |
| **Maximum** | only the protected guest message and the knowledge base – no booking data, no history, no examples, no status entities | high: more generic replies, tone no longer yours, times and problems stay `[OFFEN]` |
| **Custom** | every switch individually, with a description of the loss | depends |

- **Own names** (default: words of the account name) are never replaced, e.g. your signature.
- **"What goes to the AI?"** in the settings card: "Last AI request" shows the exact text sent (memory only, empty after a restart), "Dry run next booking" builds the text for the current/next booking without calling the AI (works with AI locked too). WebSocket `smoobu/assistant/preview`.
- **Limits:** only **known** names from the Smoobu bookings are replaced. Other names in free text (companions, children) and anything without a pattern (e.g. "my son has a nut allergy") remain. The AI has to read the guest message to reply. **This is not fully anonymous.** Pseudonymised data is still personal data under GDPR; a cloud provider needs a data processing agreement. Only a local AI (e.g. Ollama as an `ai_task` entity) keeps everything in the house.

---

### Lexware Office (beta, since 1.20.0)

> **BETA** – not yet confirmed with a real Lexware account. Review every draft in Lexware.

Optional module for the [Lexware Office Public API](https://developers.lexware.io/docs/) (according to Lexware plan **XL** and up). Enable it in the settings tab **"Lexware (beta)"** (or the last step of the options dialog) with the API key from Lexware (Add-ons → Public API). Without XL everything can be tried in **test mode** with sample articles – nothing is sent.

- **Lines:** per channel group (direct/portal) a list of rules. Each rule = one Lexware article (name, unit, tax rate from Lexware) with quantity (flat, per night, per person/extra person, per child, per dog with cap …), optional condition (e.g. only up to 14 nights) and price from the article or the **remainder of the booking price** – so the total always matches Smoobu. "Use template" creates a typical holiday-rental invoice. Placeholders `[Portal]`, `[n]`, `[Nächte]`, `[Fällig]`, `[Betrag]`, `[Anzahlung]` are replaced by the integration.
- **Invoice:** button "Create draft invoice" in the booking details → preview (quantities, prices, dogs, total discount, company, contact) → Lexware receives a **draft**; finalising happens in Lexware. Invoice date = today, **due on arrival day** (Lexware shows it as open, not overdue, until arrival). Private guests gross, companies net (configurable); for companies the guest becomes the contact person.
- **Contact:** looked up by name (company name for companies), exact matches only; several → choice in the preview; otherwise a new customer.
- **Payments:** sync via webhook (public HTTPS URL, e.g. Nabu Casa) and hourly. Due deposit = deposit from Smoobu, otherwise 50 % (configurable). Notices in "Waiting for you" and push "Invoices & payments": deposit missing after n days (cancellation possible – the integration never cancels on its own), balance open on arrival day, draft not finalised, invoice missing.
- **Meaning of "paid"** (also without Lexware): per channel group "payment received" or "invoice issued" by hand – with Lexware automatically "payment according to Lexware" or "invoice issued according to Lexware" (Lexware → Smoobu only).
- **Permission:** "Create invoices (Lexware)"; the payment status is visible to everyone who may see "Finances".

![Lexware: invoice in the booking details](docs/screenshots/lexware_rechnung.png) ![Lexware: preview](docs/screenshots/lexware_vorschau.png)

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
- **Cleaning data (staff):** for each completed cleaning the cleaning board stores **who** cleaned and who checked it off, plus date, property and duration – no guest names. For employed cleaners this is employee data: tell them that and why it is recorded (scheduling, payroll, cost per stay; Art. 13 GDPR). After the **"Keep person for"** period (Settings → Cleaning & access → Privacy, default **10 years** = tax retention), the person automatically becomes **"Unknown"**; statistics stay. Open, unfinished entries expire after 60 days.
- You, as operator of the Home Assistant installation, are the **controller** under GDPR. The integration stores everything locally in Home Assistant; data only goes to Smoobu itself and – if enabled – to the chosen AI provider (see privacy level).
- **Lexware (beta):** for invoices the guest's name, address, e-mail, phone, period and price are sent to Lexware Office – only on button press. Invoice data never goes to the AI. The API key is stored in the options and never sent to the dashboard cards.
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

## Hilfe & Mitmachen / Support & contributing

- **Fragen / Questions:** [Discussions](https://github.com/Grunor/ha-Smoobu/discussions)
- **Fehler, Wünsche / Bugs, ideas:** [Issue anlegen / open an issue](https://github.com/Grunor/ha-Smoobu/issues/new/choose) – bitte keine Schlüssel oder echten Gästedaten / no keys or real guest data
- **Sicherheitslücken / Vulnerabilities:** privat melden / report privately, see [SECURITY.md](SECURITY.md)
- **Mitentwickeln / Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md) · [Verhaltenskodex / Code of conduct](CODE_OF_CONDUCT.md)

---

## Lizenz / License

MIT

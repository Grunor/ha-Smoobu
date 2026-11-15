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
- 🏠 **Binärsensoren:** belegt, Anreise heute, Abreise heute, Gästewechsel heute
- 📊 **Statistik für 30 Tage:** Buchungen, Auslastung, Umsatz, offene Zahlungen
- ⚡ **Echtzeit-Webhook:** Nabu Casa Cloudhook oder externe HTTPS-URL, wird automatisch bei Smoobu registriert
- 🔔 **Event `smoobu_event`** bei neuer, geänderter oder stornierter Buchung und bei neuer Gastnachricht
- 🛠️ **Aktionen:** Buchungen abfragen, einzelne Buchung abrufen, Nachrichten lesen, Nachrichten senden
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
2. **Einstellungen → Erweitert → API-Schlüssel** öffnen.
3. **API-Schlüssel erstellen** und eine Bezeichnung vergeben, z. B. „Home Assistant“.
4. Die Option **„Guest Data (PII)“ aktivieren**. Ohne diese Berechtigung liefert Smoobu Namen, E-Mail und Telefon als leere Felder.
5. **Generate Secret** klicken und **Schlüssel und Secret sofort kopieren**. Das Secret wird nur einmal angezeigt.

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
| Standard-Check-out | 11:00 | Gilt, wenn in der Buchung keine Abreisezeit steht |
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
| Kalender | `calendar.smoobu_ferienwohnung_belegung` | Alle Buchungen. Titel = Gastname (blockierte Zeiträume: „Blockiert“). Beginn = Anreise + Check-in-Zeit, Ende = Abreise + Check-out-Zeit. |
| Belegt | `binary_sensor.smoobu_ferienwohnung_belegt` | An zwischen Check-in- und Check-out-Zeit einer Gästebuchung |
| Anreise heute | `binary_sensor.smoobu_ferienwohnung_anreise_heute` | Heute reist ein Gast an |
| Abreise heute | `binary_sensor.smoobu_ferienwohnung_abreise_heute` | Heute reist ein Gast ab |
| Gästewechsel heute | `binary_sensor.smoobu_ferienwohnung_gastewechsel_heute` | Abreise und Anreise am selben Tag |
| Aktueller Gast | `sensor.smoobu_ferienwohnung_aktueller_gast` | Voller Name des aktuellen Gastes |
| Aktueller Vorname | `sensor.smoobu_ferienwohnung_aktueller_vorname` | Vorname des aktuellen Gastes |
| Aktuelle Personen | `sensor.smoobu_ferienwohnung_aktuelle_personen` | Erwachsene + Kinder, 0 wenn frei |
| Nächster Gast | `sensor.smoobu_ferienwohnung_nachster_gast` | Voller Name des nächsten Gastes |
| Nächster Vorname | `sensor.smoobu_ferienwohnung_nachster_vorname` | Vorname des nächsten Gastes |
| Nächste Personen | `sensor.smoobu_ferienwohnung_nachste_personen` | Personenzahl der nächsten Buchung |
| Nächste Anreise | `sensor.smoobu_ferienwohnung_nachste_anreise` | Zeitstempel der nächsten Anreise |
| Nächste Abreise | `sensor.smoobu_ferienwohnung_nachste_abreise` | Abreise der laufenden Buchung, sonst der nächsten |
| Buchungen 30 Tage | `sensor.smoobu_ferienwohnung_buchungen_30_tage` | Anzahl Anreisen in den nächsten 30 Tagen, Liste im Attribut `buchungen` |
| Auslastung 30 Tage | `sensor.smoobu_ferienwohnung_auslastung_30_tage` | Belegte Nächte in % (inkl. Blockierungen) |
| Umsatz 30 Tage | `sensor.smoobu_ferienwohnung_umsatz_30_tage` | Summe der Buchungspreise der Anreisen in den nächsten 30 Tagen |
| Offene Zahlungen | `sensor.smoobu_ferienwohnung_offene_zahlungen` | Laufende/kommende Buchungen, die nicht als bezahlt markiert sind. Attribute: `buchungen`, `offener_betrag` |

#### Konto (Diagnose)

| Entität | Beispiel-ID | Inhalt |
|---|---|---|
| Letzte Aktualisierung | `sensor.smoobu_letzte_aktualisierung` | Zeitpunkt der letzten erfolgreichen Abfrage |
| Letztes Ereignis | `sensor.smoobu_letztes_ereignis` | Letzte Webhook-Aktion (z. B. `newReservation`) mit Buchungs-ID und Gast |
| Webhook | `sensor.smoobu_webhook` | `registriert`, `manuell` (URL muss in Smoobu eingetragen werden) oder `aus`. Attribut `url`. |
| Gastdaten fehlen | `binary_sensor.smoobu_gastdaten_fehlen` | An, wenn Smoobu keine Gastnamen liefert (PII-Berechtigung fehlt) |

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
| `check_in_zeit`, `check_out_zeit` | Zeiten laut Smoobu (leer = Standard aus den Optionen) |
| `naechte`, `erwachsene`, `kinder`, `personen` | Aufenthalt |
| `preis`, `preis_bezahlt` | Gesamtpreis und Zahlungsstatus |
| `anzahlung`, `anzahlung_bezahlt`, `kaution`, `kaution_bezahlt` | Anzahlung und Kaution |
| `kurtaxe`, `provision_enthalten` | nur bei Buchungen mit Detaildaten |
| `notiz`, `assistent_notiz` | Notizen aus Smoobu |
| `gaeste_app` | Link zur Smoobu-Gäste-App |
| `erstellt`, `geaendert` | Zeitstempel aus Smoobu |
| `blockiert` | blockierter Zeitraum (keine Gästebuchung) |
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

**Verwendete Endpunkte:** `GET /api/me`, `GET /api/apartments`, `GET /api/apartments/{id}`, `GET /api/reservations`, `GET /api/reservations/{id}`, `GET /api/reservations/{id}/messages`, `POST /api/reservations/{id}/messages/send-message-to-guest`, `POST /api/reservations/{id}/messages/send-message-to-host`, `GET/POST/DELETE /api/users/webhooks`.

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
- 🏠 **Binary sensors:** occupied, arrival today, departure today, changeover today
- 📊 **30-day statistics:** bookings, occupancy rate, revenue, unpaid bookings
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
2. Open **Settings → Advanced → API Keys**.
3. Click **Create API Key** and give it a label, e.g. "Home Assistant".
4. **Enable the "Guest Data (PII)" option.** Without it, Smoobu returns names, email and phone as empty fields.
5. Click **Generate Secret** and **copy the key and the secret right away**. The secret is shown only once.

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
| Default check-out | 11:00 | Used when the booking has no departure time |
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
| Calendar | `calendar.smoobu_apartment_occupancy` | All bookings. Title = guest name (blocked periods: "Blockiert"). Start = arrival + check-in time, end = departure + check-out time. |
| Occupied | `binary_sensor.smoobu_apartment_occupied` | On between check-in and check-out time of a guest booking |
| Arrival today | `binary_sensor.smoobu_apartment_arrival_today` | A guest arrives today |
| Departure today | `binary_sensor.smoobu_apartment_departure_today` | A guest leaves today |
| Changeover today | `binary_sensor.smoobu_apartment_changeover_today` | Departure and arrival on the same day |
| Current guest | `sensor.smoobu_apartment_current_guest` | Full name of the current guest |
| Current first name | `sensor.smoobu_apartment_current_first_name` | First name of the current guest |
| Current guests count | `sensor.smoobu_apartment_current_guests_count` | Adults + children, 0 if vacant |
| Next guest | `sensor.smoobu_apartment_next_guest` | Full name of the next guest |
| Next first name | `sensor.smoobu_apartment_next_first_name` | First name of the next guest |
| Next guests count | `sensor.smoobu_apartment_next_guests_count` | Number of guests of the next booking |
| Next arrival | `sensor.smoobu_apartment_next_arrival` | Timestamp of the next arrival |
| Next departure | `sensor.smoobu_apartment_next_departure` | Departure of the current booking, otherwise of the next one |
| Bookings 30 days | `sensor.smoobu_apartment_bookings_30_days` | Number of arrivals in the next 30 days, list in attribute `buchungen` |
| Occupancy rate 30 days | `sensor.smoobu_apartment_occupancy_rate_30_days` | Booked nights in % (incl. blocked periods) |
| Revenue 30 days | `sensor.smoobu_apartment_revenue_30_days` | Sum of booking prices of arrivals in the next 30 days |
| Unpaid bookings | `sensor.smoobu_apartment_unpaid_bookings` | Current/upcoming bookings not marked as paid. Attributes: `buchungen`, `offener_betrag` |

#### Account (diagnostic)

| Entity | Example ID | Content |
|---|---|---|
| Last update | `sensor.smoobu_last_update` | Time of the last successful poll |
| Last event | `sensor.smoobu_last_event` | Last webhook action (e.g. `newReservation`) with booking ID and guest |
| Webhook | `sensor.smoobu_webhook` | `registriert` (registered), `manuell` (URL must be entered in Smoobu) or `aus` (off). Attribute `url`. |
| Guest data missing | `binary_sensor.smoobu_guest_data_missing` | On if Smoobu returns no guest names (PII permission missing) |

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
| `check_in_zeit`, `check_out_zeit` | Times from Smoobu (empty = default from options) |
| `naechte`, `erwachsene`, `kinder`, `personen` | Nights, adults, children, total guests |
| `preis`, `preis_bezahlt` | Total price and payment status |
| `anzahlung`, `anzahlung_bezahlt`, `kaution`, `kaution_bezahlt` | Prepayment and deposit |
| `kurtaxe`, `provision_enthalten` | City tax, commission included (only for bookings with details) |
| `notiz`, `assistent_notiz` | Notes from Smoobu |
| `gaeste_app` | Link to the Smoobu guest app |
| `erstellt`, `geaendert` | Created/modified timestamps from Smoobu |
| `blockiert` | Blocked period (no guest booking) |
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

**Endpoints used:** `GET /api/me`, `GET /api/apartments`, `GET /api/apartments/{id}`, `GET /api/reservations`, `GET /api/reservations/{id}`, `GET /api/reservations/{id}/messages`, `POST /api/reservations/{id}/messages/send-message-to-guest`, `POST /api/reservations/{id}/messages/send-message-to-host`, `GET/POST/DELETE /api/users/webhooks`.

**Data retrieval:** One coordinator per account loads all bookings in the window [today − days back, today + days ahead], excluding cancellations. Apartment details are refreshed every 24 h. Details of the current and next bookings are cached and only fetched again when `modifiedAt` changes. If a calendar card scrolls beyond the window, the calendar queries Smoobu directly.

**Type:** `iot_class: cloud_push`, `integration_type: service`, dependencies `webhook` (required) and `cloud` (optional).

---

### Changelog

All changes are listed in [CHANGELOG.md](CHANGELOG.md) and under [Releases](https://github.com/Grunor/ha-Smoobu/releases).

---

## Lizenz / License

MIT

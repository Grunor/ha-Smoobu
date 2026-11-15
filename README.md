# Smoobu für Home Assistant

Custom-Integration für [Smoobu](https://www.smoobu.com/), den Channel Manager für Ferienwohnungen.
Sie verbindet Home Assistant direkt mit der Smoobu-API und stellt Buchungen, Gästedaten, Belegung und Statistik als Entitäten bereit. Über einen Webhook kommen Änderungen in Echtzeit an.

> Nicht offiziell. Dieses Projekt steht in keiner Verbindung zu Smoobu GmbH.

---

## Inhalt

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

## Warum diese Integration?

- **Der iCal-Export von Smoobu enthält keine vollständigen Gastnamen mehr.** Wer den Smoobu-Kalender per iCal (oder über einen Google-Kalender-Import) einbindet, sieht nur noch Platzhalter.
- **Die alte API-Anmeldung per `Api-Key`-Header wurde von Smoobu zum 31.10.2026 abgeschaltet.** Seitdem muss jede Anfrage einzeln per HMAC-SHA256 signiert werden. Mit der `rest:`-Integration von Home Assistant ist das nicht möglich, weil Jinja-Templates keine HMAC-Signatur berechnen können.

Diese Integration übernimmt die Signatur und stellt alle Daten nativ in Home Assistant bereit.

---

## Funktionen

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

## Voraussetzungen

- Home Assistant **2025.2** oder neuer (lokal getestet mit 2026.2)
- Smoobu-Konto mit API-Zugang
- Für den Echtzeit-Webhook entweder **Home Assistant Cloud (Nabu Casa)** oder eine **externe HTTPS-URL** (Smoobu akzeptiert nur HTTPS). Ohne beides arbeitet die Integration nur per Abfrageintervall.

---

## Smoobu-API-Schlüssel erstellen

1. In Smoobu anmelden.
2. **Einstellungen → Erweitert → API-Schlüssel** öffnen.
3. **API-Schlüssel erstellen** und eine Bezeichnung vergeben, z. B. „Home Assistant“.
4. Die Option **„Guest Data (PII)“ aktivieren**. Ohne diese Berechtigung liefert Smoobu Namen, E-Mail und Telefon als leere Felder.
5. **Generate Secret** klicken und **Schlüssel und Secret sofort kopieren**. Das Secret wird nur einmal angezeigt.

---

## Installation

### Über den Marketplace (HACS) – empfohlen

1. In Home Assistant **Marketplace** (bzw. HACS) öffnen.
2. Oben rechts **⋮ → Benutzerdefinierte Repositories**.
3. Repository `https://github.com/Grunor/ha-Smoobu` eintragen, Kategorie **Integration**, hinzufügen.
4. **Smoobu** suchen und herunterladen.
5. Home Assistant **neu starten**.

Updates erscheinen danach automatisch als normales Update in Home Assistant.

### Manuell

1. Den neuesten [Release](https://github.com/Grunor/ha-Smoobu/releases) herunterladen.
2. Den Ordner `custom_components/smoobu` nach `/config/custom_components/smoobu` kopieren, z. B. per Samba oder Studio Code Server.
3. Home Assistant **neu starten**.

---

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
2. **Smoobu** auswählen.
3. **API-Schlüssel** und **Secret** eintragen.

Die Integration prüft den Schlüssel, legt für jede Smoobu-Wohnung ein Gerät an und registriert, falls möglich, den Webhook bei Smoobu.

Wird der Schlüssel später ungültig (gelöscht, Secret neu erzeugt), meldet Home Assistant eine **Neu-Anmeldung**. Dort neuen Schlüssel und neues Secret eintragen, eine Neueinrichtung ist nicht nötig.

---

## Optionen

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

## Entitäten

Je Smoobu-Wohnung entsteht ein Gerät, zusätzlich ein Gerät **„Smoobu“** für das Konto.
Die Entitäts-IDs richten sich nach dem Wohnungsnamen in Smoobu und der Systemsprache. Die Beispiele unten gelten für eine Wohnung namens „Ferienwohnung“ bei deutscher Systemsprache.

### Je Wohnung

| Entität | Beispiel-ID | Inhalt |
|---|---|---|
| Kalender | `calendar.ferienwohnung_belegung` | Alle Buchungen. Titel = Gastname (blockierte Zeiträume: „Blockiert“). Beginn = Anreise + Check-in-Zeit, Ende = Abreise + Check-out-Zeit. |
| Belegt | `binary_sensor.ferienwohnung_belegt` | An zwischen Check-in- und Check-out-Zeit einer Gästebuchung |
| Anreise heute | `binary_sensor.ferienwohnung_anreise_heute` | Heute reist ein Gast an |
| Abreise heute | `binary_sensor.ferienwohnung_abreise_heute` | Heute reist ein Gast ab |
| Gästewechsel heute | `binary_sensor.ferienwohnung_gastewechsel_heute` | Abreise und Anreise am selben Tag |
| Aktueller Gast | `sensor.ferienwohnung_aktueller_gast` | Voller Name des aktuellen Gastes |
| Aktueller Vorname | `sensor.ferienwohnung_aktueller_vorname` | Vorname des aktuellen Gastes |
| Aktuelle Personen | `sensor.ferienwohnung_aktuelle_personen` | Erwachsene + Kinder, 0 wenn frei |
| Nächster Gast | `sensor.ferienwohnung_nachster_gast` | Voller Name des nächsten Gastes |
| Nächster Vorname | `sensor.ferienwohnung_nachster_vorname` | Vorname des nächsten Gastes |
| Nächste Personen | `sensor.ferienwohnung_nachste_personen` | Personenzahl der nächsten Buchung |
| Nächste Anreise | `sensor.ferienwohnung_nachste_anreise` | Zeitstempel der nächsten Anreise |
| Nächste Abreise | `sensor.ferienwohnung_nachste_abreise` | Abreise der laufenden Buchung, sonst der nächsten |
| Buchungen 30 Tage | `sensor.ferienwohnung_buchungen_30_tage` | Anzahl Anreisen in den nächsten 30 Tagen, Liste im Attribut `buchungen` |
| Auslastung 30 Tage | `sensor.ferienwohnung_auslastung_30_tage` | Belegte Nächte in % (inkl. Blockierungen) |
| Umsatz 30 Tage | `sensor.ferienwohnung_umsatz_30_tage` | Summe der Buchungspreise der Anreisen in den nächsten 30 Tagen |
| Offene Zahlungen | `sensor.ferienwohnung_offene_zahlungen` | Laufende/kommende Buchungen, die nicht als bezahlt markiert sind. Attribute: `buchungen`, `offener_betrag` |

### Konto (Diagnose)

| Entität | Beispiel-ID | Inhalt |
|---|---|---|
| Letzte Aktualisierung | `sensor.smoobu_letzte_aktualisierung` | Zeitpunkt der letzten erfolgreichen Abfrage |
| Letztes Ereignis | `sensor.smoobu_letztes_ereignis` | Letzte Webhook-Aktion (z. B. `newReservation`) mit Buchungs-ID und Gast |
| Webhook | `sensor.smoobu_webhook` | `registriert`, `manuell` (URL muss in Smoobu eingetragen werden) oder `aus`. Attribut `url`. |
| Gastdaten fehlen | `binary_sensor.smoobu_gastdaten_fehlen` | An, wenn Smoobu keine Gastnamen liefert (PII-Berechtigung fehlt) |

### Attribute der Buchungs-Entitäten

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

## Aktionen

Alle Aktionen haben das optionale Feld `config_entry_id`. Ohne Angabe wird das einzige eingerichtete Smoobu-Konto verwendet.

### `smoobu.refresh`

Ruft die Daten sofort ab.

### `smoobu.get_reservations`

Buchungen nach Filter. Gibt Antwortdaten zurück (`count`, `reservations`).

| Feld | Typ | Beschreibung |
|---|---|---|
| `arrival_from` / `arrival_to` | Datum | Anreise von/bis |
| `departure_from` / `departure_to` | Datum | Abreise von/bis |
| `apartment_id` | Zahl | nur diese Wohnung |
| `show_cancellation` | bool | Stornos einschließen (Standard: nein) |

### `smoobu.get_reservation`

Eine Buchung mit allen Details. Pflichtfeld: `reservation_id`. Antwort: `reservation`.

### `smoobu.get_messages`

Nachrichten einer Buchung. Pflichtfeld: `reservation_id`, optional `only_related_to_guest`. Antwort: `count`, `messages`.

### `smoobu.send_message`

Nachricht an den Gast oder als Gastgeber-Notiz.

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `reservation_id` | ja | Buchungs-ID |
| `message` | ja | Text oder HTML |
| `subject` | nein | Betreff |
| `recipient` | nein | `guest` (Standard) oder `host` |
| `internal` | nein | nur bei `host`: Notiz vor dem Gast verbergen |

---

## Events

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

## Beispiele

### Push bei neuer Buchung

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

### Push bei Stornierung

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

### Willkommensnachricht am Anreisetag

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
    entity_id: binary_sensor.ferienwohnung_anreise_heute
    state: "on"
actions:
  - alias: "Aktion: Nachricht über Smoobu an den Gast senden"
    action: smoobu.send_message
    data:
      reservation_id: "{{ state_attr('binary_sensor.ferienwohnung_anreise_heute', 'buchungs_id') }}"
      subject: "Willkommen"
      message: >-
        Hallo {{ state_attr('binary_sensor.ferienwohnung_anreise_heute', 'vorname') }},
        wir freuen uns auf euch! Die Wohnung ist ab 16 Uhr bereit.
```

### Buchungen eines Monats in einem Skript abfragen

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

### Gästewechsel als Reinigungs-Erinnerung

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
    entity_id: binary_sensor.ferienwohnung_gastewechsel_heute
    state: "on"
actions:
  - alias: "Aktion: Push an die Reinigung"
    action: notify.mobile_app_dein_handy
    data:
      title: "Gästewechsel heute"
      message: "Reinigung zwischen 11 und 16 Uhr einplanen."
```

---

## Webhook

Die Integration richtet den Webhook beim Start selbst ein:

1. Sie registriert einen Home-Assistant-Webhook mit zufälliger ID (nur `POST`).
2. Ist Home Assistant Cloud aktiv, erzeugt sie einen **Nabu Casa Cloudhook**. Sonst verwendet sie die **externe HTTPS-URL** von Home Assistant.
3. Sie trägt die URL über die Smoobu-API (`/api/users/webhooks`) ein. Eine bereits eingetragene gleiche URL wird erkannt und nicht doppelt angelegt.

**Wenn die automatische Registrierung nicht klappt,** erscheint eine Benachrichtigung in Home Assistant mit der URL. Diese in Smoobu unter **Einstellungen → API** als Webhook-URL eintragen. Die URL steht auch im Attribut `url` von `sensor.smoobu_webhook`.

Wird der Webhook in den Optionen abgeschaltet oder die Integration gelöscht, entfernt sie die Registrierung bei Smoobu und den Cloudhook wieder.

---

## Datenschutz und Sicherheit

- API-Schlüssel und Secret liegen im Config-Entry von Home Assistant, nicht in YAML-Dateien.
- Gästedaten (Name, E-Mail, Telefon, Notizen) stehen in Entitäts-Attributen und damit auch in der **Historie** von Home Assistant. Wer das nicht möchte, schließt die betroffenen Entitäten im Recorder aus.
- Der **Diagnose-Download** schwärzt Zugangsdaten, Webhook-URL und alle Gästedaten.
- Smoobu signiert Webhooks nicht. Die Integration schützt sich deshalb über die geheime, zufällige Webhook-URL und nimmt nur Ereignisse an, deren Smoobu-Benutzer-ID zum eingerichteten Konto passt. Bei abweichender ID wird mit `403` abgelehnt.
- Die Webhook-URL nicht weitergeben. Bei Verdacht: Webhook in den Optionen aus- und wieder einschalten, dann wird eine neue URL erzeugt.

---

## Fehlerbehebung

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

## Technische Details

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

## Changelog

### 1.0.0 (15.11.2026)
- Erstveröffentlichung: HMAC-Client, Einrichtung über die Oberfläche mit Neu-Anmeldung und Optionen, Kalender, 12 Sensoren und 4 Binärsensoren je Wohnung, Diagnose-Entitäten, Echtzeit-Webhook mit automatischer Registrierung, Event `smoobu_event`, 5 Aktionen, Diagnose-Download, Übersetzungen Deutsch/Englisch.

---

## Lizenz

MIT

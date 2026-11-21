# Changelog

Format je Version: deutsch, dann englisch. Versionierung nach [SemVer](https://semver.org/lang/de/): MAJOR = inkompatible Änderung (z. B. Entitäts-IDs), MINOR = neue Funktion, PATCH = Korrektur.
Format per version: German, then English. Versioning follows [SemVer](https://semver.org/): MAJOR = breaking change (e.g. entity IDs), MINOR = new feature, PATCH = fix.

Änderungen werden auf dem Branch `develop` unter „Unveröffentlicht“ gesammelt. Ein Release entsteht, sobald die Version in `custom_components/smoobu/manifest.json` erhöht und nach `main` übernommen wird. Beta-Versionen (z. B. `1.17.0b1`) werden direkt von `develop` als Pre-Release veröffentlicht.
Changes are collected on the `develop` branch under "Unreleased". A release is created as soon as the version in `custom_components/smoobu/manifest.json` is increased and merged into `main`. Beta versions (e.g. `1.17.0b1`) are published from `develop` as pre-releases.

## Unveröffentlicht / Unreleased

- Roadmap: `ROADMAP.md` mit geplanten Funktionen (je ein Issue mit Label `roadmap`) / roadmap file with planned features (one issue each, label `roadmap`)

## 1.19.0 – 2026-11-21

**Deutsch**
- Stabiler Release mit allen Änderungen der Betas 1.19.0b1–1.19.0b12 (Einzelheiten in den Abschnitten unten). Die wichtigsten Neuerungen:
  - **Reinigung:** Reinigungsboard (neue Seite `smoobu-reinigung`, Karte `custom:smoobu-cleaning-card`) mit Zuweisen, Übernehmen, Abhaken und gebuchter Reinigungszeit; Pushes an die Reinigungskraft (bei Zuweisung und am Vorabend); Reinigung auch in den Buchungsdetails; Statistik-Modul „Reinigung“ (wer hat wann welche Wohnung gereinigt); Kosten = Zeit × Stundenlohn je Person
  - **Rollen & Rechte:** Rechte je Rolle einstellbar, eigene Rollen, neue Rolle **„Reinigung“** (nur Vorname des Gastes), neue Rechte „Kalender sehen“, „Reinigung übernehmen und abhaken“, „Reinigung zuweisen“
  - **Fokus-Modus je Rolle:** Benutzer der Rolle sehen in Home Assistant nur Smoobu – ohne Seitenleiste und Menüs, andere Seiten leiten auf die Startseite um (zentral eingestellt, Standard für „Reinigung“)
  - **Neue HA-Benutzer werden gemeldet** (HA-Meldung + Push), damit Rechte nicht vergessen werden
  - **Türcodes:** Zufallscode je Buchung oder statischer Code je Wohnung (z. B. Schlüsseltresor), Gültigkeit, Smoobu-Notiz, Entitäten, Schloss-Adapter (Matter, Z-Wave JS, ZHA, Zigbee2MQTT, eigenes Skript); der Code geht nie an die KI
  - **Strom, Wasser, Heizung** konstant oder gemessen aus Zählern (je Buchung ab Vorheizstart, Leerstand separat oder anteilig); **Nebenkostenabrechnung** hochladen und von der KI auswerten lassen
  - **Module abschaltbar:** Reinigung, Kosten, Preise
  - **Einstellungen neu sortiert:** neuer Reiter „Reinigung & Zugang“, Entitäten per Dropdown mit vorgefilterten Vorschlägen
  - **Schnelleres Laden** (Kartendatei komprimiert und zwischenspeicherbar), rund 530 englische Texte ergänzt
- **Hinweise beim Umstieg von 1.18.0**
  - **Standardrechte geändert:** „Betrieb“ ohne „Preise ändern“; „Mitarbeiter“ ohne „Kalender ändern“, dafür mit „Reinigung zuweisen“. Wer diese Rollen nutzt, bitte unter Einstellungen → Benutzer & Rechte prüfen (in der Rolle angepasste Rechte bleiben unverändert)
  - Für das Reinigungsboard eine Ansicht mit Pfad `smoobu-reinigung` und der Karte `custom:smoobu-cleaning-card` anlegen (siehe `docs/dashboard-vorlage.yaml`); der Reiter erscheint dann automatisch
  - Die Option „Reinigung je Aufenthalt“ ist jetzt der **Standard-Stundenlohn** (bei 60 min bleibt der Betrag gleich)
  - Türcodes sind standardmäßig aus; Strom/Wasser/Heizung bleiben „Konstant“, bis ein Zähler gewählt wird
  - Beim ersten Start werden vorhandene HA-Benutzer still übernommen – gemeldet werden nur neue

![Reinigungsboard](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/reinigung.png)
![Buchungsdetails mit Zugang und Reinigung](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/buchungsdetails.png)
![Rollen und Rechte](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_rollen.png)
![Fokus-Modus](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_fokus.png)
![Module](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_module.png)
![Türcodes](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_tuercode.png)
![Stromkosten aus Zähler](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/einstellungen_strom.png)
![Statistik Reinigung](https://raw.githubusercontent.com/Grunor/ha-Smoobu/main/docs/screenshots/statistik_reinigung.png)

**English**
- Stable release with all changes of betas 1.19.0b1–1.19.0b12 (details in the sections below). Main changes:
  - **Cleaning:** cleaning board (new page `smoobu-reinigung`, card `custom:smoobu-cleaning-card`) to assign, take over and tick off cleanings with booked cleaning time; pushes to the cleaner (on assignment and the evening before); cleaning also in the booking details; statistics module "Cleaning" (who cleaned which property when); costs = time × hourly wage per person
  - **Roles & permissions:** permissions per role configurable, custom roles, new role **"Cleaning"** (guest first name only), new permissions "View calendar", "Take over and tick off cleaning", "Assign cleaning"
  - **Focus mode per role:** users of the role only see Smoobu in Home Assistant – no sidebar and menus, other pages redirect to the start page (configured centrally, default for "Cleaning")
  - **New HA users are reported** (HA notification + push) so permissions are not forgotten
  - **Door codes:** random code per booking or a static code per property (e.g. key safe), validity, Smoobu note, entities, lock adapters (Matter, Z-Wave JS, ZHA, Zigbee2MQTT, own script); the code never goes to the AI
  - **Electricity, water, heating** constant or measured from meters (per booking from pre-heating start, vacancy separate or distributed); **upload the utility bill** and let the AI read it
  - **Switchable modules:** cleaning, costs, prices
  - **Settings reorganised:** new tab "Cleaning & access", entities via dropdown with pre-filtered suggestions
  - **Faster loading** (card file compressed and cacheable), about 530 English texts added
- **Notes when upgrading from 1.18.0**
  - **Default permissions changed:** "Operations" without "Change prices"; "Staff" without "Change calendar" but with "Assign cleaning". If you use these roles, please check under Settings → Users & permissions (permissions customised in a role stay as they are)
  - For the cleaning board create a view with path `smoobu-reinigung` and the card `custom:smoobu-cleaning-card` (see `docs/dashboard-vorlage.yaml`); the tab then appears automatically
  - The option "cleaning per stay" is now the **standard hourly wage** (at 60 min the amount stays the same)
  - Door codes are off by default; electricity/water/heating stay "Constant" until a meter is chosen
  - On the first start existing HA users are taken over silently – only new ones are reported

## 1.19.0b12 – 2026-11-21

### Geändert / Changed
- **Neuer Einstellungs-Reiter „Reinigung & Zugang“:** Reinigungszeit und Stundenlöhne (vorher „Kosten & Preise“), Pushes an Reinigungskräfte (vorher „Benachrichtigungen“) und Türcodes (vorher „Allgemein & Abruf“) an einer Stelle. „Kosten & Preise“ zeigt die Reinigung nur noch als Summe je Aufenthalt.
- **Buchungsdetails:** eigene Abschnitte „Zugang“ (Türcode) und „Reinigung“ statt Zeilen unter „Aufenthalt“; die Reinigungszeit speichert beim Ändern wie auf dem Reinigungsboard. Hinweis auf die Standardzeiten, wenn Ankunft/Abreise leer sind.
- **Einheitliche Begriffe:** Rechte „Kalender sehen“ / „Kalender ändern“ (wie die Seite „Kalender“), Module kurz „Reinigung“, „Kosten“, „Preise“. Gespeicherte Rechte bleiben gültig.
- **Englisch:** rund 530 fehlende englische Texte der Karten ergänzt (u. a. alles aus 1.19).
- README-Bilder neu erzeugt.
- **New settings tab "Cleaning & access":** cleaning time and hourly wages (previously "Costs & prices"), pushes to cleaners (previously "Notifications") and door codes (previously "General & polling") in one place.
- **Booking details:** own sections "Access" (door code) and "Cleaning"; cleaning time saves on change like on the cleaning board. Hint on default times if arrival/departure are empty.
- **Consistent terms:** permissions "View calendar" / "Change calendar", modules "Cleaning", "Costs", "Prices". Stored permissions stay valid.
- **English:** about 530 missing English card texts added (incl. everything from 1.19).
- README images regenerated.

## 1.19.0b11 – 2026-11-21

### Geändert / Changed
- **Schnelleres Laden der Karten:** Die Kartendatei wird komprimiert ausgeliefert (gzip, ca. 170 statt 570 KB; wird beim Start einmalig erzeugt) und darf im Browser zwischengespeichert werden (Adresse enthält die Version, nach Updates lädt die neue Datei trotzdem). Spürbar vor allem am Handy und über Nabu Casa.
- **Faster card loading:** the card file is served compressed (gzip, about 170 instead of 570 KB; created once at startup) and may be cached by the browser (the URL contains the version, so updates still load the new file). Noticeable mainly on phones and via Nabu Casa.

## 1.19.0b10 – 2026-11-21

### Neu / New
- **Module abschaltbar** (Einstellungen → Allgemein & Abruf → Module, Standard alle an): **Reinigung** (Reinigungsboard, Reinigung in den Buchungsdetails, Pushes, Aufgaben, Statistik-Modul; aus = Reinigungskosten nach Standardlohn), **Kosten & Deckungsbeitrag** (variable Kosten, Deckungsbeitrag in Finanzen/Statistik, Zählermessung ohne Recorder-Abfragen, Nebenkosten-Upload) und **Preise & Empfehlungen** (Bewertung & Empfehlung, Preis-/Last-Minute-Aufgaben, Aufschläge, Genius, Last-Minute). Ausgeschaltet verschwinden Seiten, Blöcke, Pushes und Aufgaben; gespeicherte Daten bleiben. Sind Kosten und Preise aus, entfällt der Reiter „Kosten & Preise“.
- **Switchable modules** (Settings → General & polling → Modules, all on by default): **Cleaning**, **Costs & contribution margin** and **Prices & recommendations**. When off, pages, blocks, pushes and tasks disappear; stored data is kept. With costs and prices off, the "Costs & prices" tab is hidden.

## 1.19.0b9 – 2026-11-21

### Geändert / Changed
- **Reinigungsboard:** Wer „Gästedaten sehen“ darf (alle Standardrollen außer „Reinigung“), sieht den vollen Gastnamen; die Rolle „Reinigung“ weiterhin nur den Vornamen.
- **Cleaning board:** users with "View guest data" (all default roles except "Cleaning") see the full guest name; the "Cleaning" role still only sees the first name.

## 1.19.0b8 – 2026-11-21

### Neu / New
- **Neue HA-Benutzer werden gemeldet:** Wird in Home Assistant ein Benutzer angelegt (auch während die Integration nicht lief), erscheint eine HA-Meldung und ein sofortiger Push an alle Smoobu-Empfänger mit dem Hinweis, Rolle und Fokus-Modus dringend zu prüfen (Link zu den Smoobu-Einstellungen). Beim ersten Start werden vorhandene Benutzer still übernommen; Systembenutzer werden ignoriert.
- **New HA users are reported:** when a user is created in Home Assistant (also while the integration was not running), an HA notification and an immediate push to all Smoobu recipients ask to check role and focus mode urgently (link to the Smoobu settings). Existing users are taken over silently on the first start; system users are ignored.

## 1.19.0b7 – 2026-11-21

### Neu / New
- **Fokus-Modus je Rolle** (Einstellungen → Benutzer & Rechte → Fokus-Modus, nur Admins): Benutzer ausgewählter Rollen sehen in Home Assistant nur noch Smoobu – Seitenleiste und Menüs (Suche, Assist, Drei-Punkte) sind ausgeblendet, jede andere Seite (andere Dashboards, Verlauf, Energie …) leitet auf die Startseite der Rolle um. Startseite je Rolle wählbar (Automatisch = Reinigung für reine Reinigungsrollen, sonst Übersicht). Standard: an für „Reinigung“. Zentral eingestellt, ohne Eingriff am Gerät; Admins sind nie betroffen. Hinweis: Sperre der Oberfläche, nicht der HA-API – Smoobu-Daten prüft weiterhin der Server.
- **Focus mode per role** (Settings → Users & permissions → Focus mode, admins only): users of selected roles only see Smoobu in Home Assistant – sidebar and menus (search, Assist, three dots) are hidden and every other page (other dashboards, history, energy …) redirects to the role's start page. Start page selectable per role (automatic = cleaning page for cleaning-only roles, otherwise overview). Default: on for "Cleaning". Configured centrally, no access to the device needed; admins are never affected. Note: this locks the UI, not the HA API – Smoobu data is still checked by the server.

## 1.19.0b6 – 2026-11-21

### Korrigiert / Fixed
- Stundenlohn 0 €/h wurde in den Einstellungen als leer angezeigt (und beim nächsten Speichern entfernt).
- An hourly wage of 0 €/h was shown as empty in the settings (and removed on the next save).

## 1.19.0b5 – 2026-11-21

### Geändert / Changed
- **Standardrechte der Rollen:** „Betrieb“ ohne „Preise ändern“; „Mitarbeiter“ ohne „Belegung ändern“, dafür mit „Reinigung zuweisen“. Angepasste Rollen in den Einstellungen bleiben unverändert.
- **Default role rights:** "Operations" without "Change prices"; "Staff" without "Change occupancy" but with "Assign cleaning". Roles customised in the settings stay as they are.

### Korrigiert / Fixed
- Stundenlohn 0 €/h je Reinigungskraft (z. B. Inhaber) wurde ignoriert und durch den Standardlohn ersetzt.
- An hourly wage of 0 €/h per cleaner (e.g. owner) was ignored and replaced by the default wage.

## 1.19.0b4 – 2026-11-21

### Neu / New
- **Entitäten per Dropdown wählen** (Strom-/Wasser-/Heizungszähler, Preis-Entitäten, Vorheizstart, Schloss/Skript): Auswahlliste mit vorgefilterten Vorschlägen – passend zur Ferienwohnung (Name, Kürzel, Bereich, „FeWo“) bzw. zum Zweck (z. B. „Vorheiz“, „Strompreis“) oben unter „Vorschläge“, alle übrigen darunter; „Andere Entität…“ für freie Eingabe. Preis-Vorschläge nur noch mit Währung (kein CO₂ je kWh).
- **Pick entities from a dropdown** (power/water/heat meters, price entities, preheat start, lock/script): list with pre-filtered suggestions – matching the holiday apartment (name, code, area, "FeWo") or the purpose (e.g. "preheat", "electricity price") on top under "Suggestions", all others below; "Other entity…" for free input. Price suggestions only with a currency (no CO₂ per kWh).

## 1.19.0b3 – 2026-11-21

### Neu / New
- **Reinigung in den Buchungsdetails bearbeiten:** dieselben Aktionen wie auf dem Reinigungsboard – zuweisen (Recht „Reinigung zuweisen“), übernehmen/abgeben, erledigt/wieder offen und Reinigungszeit (Recht „Reinigung“). Gilt für Reinigungen im Zeitraum des Boards (7 Tage zurück bis 60 Tage voraus).
- **Edit the cleaning in the booking details:** the same actions as on the cleaning board – assign ("Assign cleaning" right), take over/hand back, done/reopen and cleaning time ("Cleaning" right). Applies to cleanings within the board's range (7 days back to 60 days ahead).

### Korrigiert / Fixed
- „Zuweisen →“ bei „Reinigung nicht zugewiesen“ leitete auf die erste Dashboard-Ansicht um, wenn die Ansicht `smoobu-reinigung` fehlte – jetzt Hinweis, wie die Seite angelegt wird.
- "Assign →" on "Cleaning not assigned" redirected to the first dashboard view when the `smoobu-reinigung` view was missing – now shows how to add the page.

## 1.19.0b2 – 2026-11-21

### Neu / New
- **Statischer Türcode je Wohnung** (Einstellungen → Allgemein & Abruf → Türcodes → „Code“): Modus „Zufall je Buchung“ (Standard) oder „Statisch“ mit festem Code (4–12 Ziffern/Buchstaben), z. B. für einen Schlüsseltresor. Jede Buchung bekommt diesen Code – in der Smoobu-Notiz, in den Buchungsdetails (Kennzeichen „statisch“, kein „Neu erzeugen“), in den Türcode-Entitäten (Attribut `art`) und über den Platzhalter `{{ turcode }}`. Wird der Code geändert oder der Modus gewechselt, bekommen alle laufenden und kommenden Buchungen den neuen Code (Notiz ersetzt, ein eingestelltes Schloss neu programmiert). Statische Codes werden wie alle Türcodes vor jeder KI-Anfrage durch den Platzhalter ersetzt.
- **Static door code per apartment** (Settings → General & polling → Door codes → "Code"): mode "random per booking" (default) or "static" with a fixed code (4–12 digits/letters), e.g. for a key safe. Every booking gets this code – in the Smoobu note, in the booking details (marked "static", no "renew"), in the door code entities (attribute `art`) and via the `{{ turcode }}` placeholder. Changing the code or the mode updates all current and upcoming bookings (note replaced, a configured lock reprogrammed). Static codes are replaced by the placeholder before every AI request like all door codes.

## 1.19.0b1 – 2026-11-21

> Beta / Pre-release

**Deutsch**
- **Rollenkonfigurator** (Einstellungen → Benutzer & Rechte, nur Admins): Rechte je Rolle per Häkchen einstellbar, „↺ Standard“ je Rolle, **eigene Rollen** anlegen, umbenennen, löschen (max. 10). „Kein Zugriff“ bleibt fest. Gespeichert werden nur Abweichungen vom Standard (neue Optionen `role_rights`, `custom_roles`). Kombinationen wie „Preise ändern“ ohne „Finanzen sehen“ sind erlaubt, die Karte zeigt dazu einen Hinweis. Gelöschte eigene Rolle → betroffene Benutzer bekommen die Standardrolle; ist sie selbst Standardrolle, wird das Speichern abgelehnt
- Neue Rechte **„Belegung sehen (nur Vorname des Gastes)“**, **„Reinigung übernehmen und abhaken“**, **„Reinigung zuweisen“**. „Gästedaten und Buchungen sehen“ schließt „Belegung sehen“ ein. Übersicht und Kalender brauchen jetzt nur noch „Belegung sehen“; ohne „Gästedaten“ liefert das Backend vom Gast nur den Vornamen (keine Kontaktdaten, Notizen, Smoobu-Rohdaten; Suche nur im Vornamen)
- Neue Standardrolle **„Reinigung“**: Belegung sehen + Reinigung übernehmen und abhaken. Verwalter und Betrieb bekommen alle neuen Rechte, Mitarbeiter „Reinigung übernehmen und abhaken“
- **Reinigungsboard** – neue Karte `custom:smoobu-cleaning-card` und Seite `smoobu-reinigung` (Reiter erscheint, sobald die Ansicht existiert): Reinigung je Abreise mit Check-out, nächster Anreise (Uhrzeit, Personen, Hund) und Gästewechsel; zuweisen, selbst übernehmen/abgeben, abhaken. Nicht zugewiesene sind für alle mit Recht „Reinigung“ sichtbar; wer zuweisen darf, sieht sie zusätzlich im Aufgaben-Board unter dem neuen Reiter **„Reinigung“** (nächste 7 Tage)
- **Push für Reinigungen** an die zugewiesene Person (bei Zuweisung/Abgabe und am Vorabend, Uhrzeit einstellbar, Standard 18:00, hält die Ruhezeit ein). Handy je Person unter Einstellungen → Benachrichtigungen → Reinigung (Optionen `cleaning_phones`, `cleaning_notify`, `cleaning_remind_time`)
- **Statistik-Modul „Reinigung“**: wer hat wann welche Wohnung gereinigt – je Person (Anteil, Gästewechsel, Hunde, Gäste Ø, Nächte, Median Zeit vom Check-out bis zum Abhaken), je Monat, je Wohnung, Liste; dazu nicht abgehakte Reinigungen. Erfasst ab dem Update (beim Abhaken wird ein Schnappschuss gespeichert, erledigte Einträge bleiben 3 Jahre)
- Neue WebSocket-Befehle `smoobu/cleaning/get`, `smoobu/cleaning/set`, `smoobu/cleaning/stats`
- **Stromkosten konstant oder gemessen** (Einstellungen → Kosten & Preise → Stromkosten): „Konstant“ bleibt Standard (wie bisher). „Aus Zähler“: Verbrauch je Buchung aus der stündlichen HA-Langzeitstatistik eines Stromzählers je Wohnung, ab Vorheizstart (optionaler Zeitstempel-Sensor, sonst Check-in − 4 h, einstellbar) bis Check-out; Strompreis optional aus einer Entität (Verlauf, davor fester Preis); Netzanteil optional **stündlich** aus dem Energie-Dashboard (Netzbezug ÷ Hausverbrauch). **Strom im Leerstand** wahlweise **separat als Fixkosten** (Standard, Hinweis im Statistik-Modul Deckungsbeitrag) oder **anteilig** nach Gästenächten auf die Buchungen. Buchungen ohne Messwert (vor Zählerstart, Zukunft) bleiben geschätzt; Feld `strom_quelle` je Buchung. Monatstabelle mit kWh, Aufenthalte, Leerstand, Netzanteil, Kosten und Vorschlag „Ø kWh je Gästenacht“ für den konstanten Wert
- **Nebenkostenabrechnung von der KI auswerten** (Kosten & Preise): PDF/JPG/PNG hochladen (max. 15 MB, nur lokal gespeichert in `smoobu_belege/`, eigene nicht durchsuchbare Medienquelle `smoobu` für den KI-Anhang). Die KI des Assistenten liest Heizung, Warmwasser, Wasser, Strom und Preis; Vorschlag je Wert mit alt/neu, Herleitung (z. B. ÷ Gästenächte aus Smoobu), Fundstelle und Prüfung (Plausibilität, Abgleich Gästenächte und gemessener Zähler). Übernommen wird nur nach Auswahl und „Speichern“. Die KI-Sperre gilt auch hier; die Datei geht vollständig an die gewählte KI (Hinweis in der Karte)
- **Wasser und Heizung ebenfalls konstant oder aus Zähler** (Kosten & Preise → Wasserkosten / Heizkosten): Wasserzähler (m³ oder L) × Preis je m³ Frisch- + Abwasser, Heizungszähler (Wärme kWh, Gas m³, Öl L) × Preis je Einheit, jeweils fest oder aus einer Entität; Option „Zähler misst auch Warmwasser“. Standard bleibt „Konstant“. Vorheizen und Leerstand gelten gemeinsam für alle Zähler (Block „Messung“); `wasser_quelle`/`heizung_quelle` je Buchung
- **Reinigung = Zeit × Stundenlohn**: Standard-Reinigungszeit (60 min) und Standard-Stundenlohn; je Reinigungskraft ein eigener Lohn (gilt für Reinigungen, die die Person laut Reinigungsboard erledigt hat oder die ihr zugewiesen sind). Die bisherige Option „Reinigung je Aufenthalt“ ist jetzt der Standard-Stundenlohn – bei 60 min bleibt der Betrag gleich. Statistik „Reinigung“ zeigt Kosten gesamt und je Person; Feld `reinigung_kosten` je Buchung
- **Reinigungszeit je Reinigung buchbar** (Reinigungsboard und Buchungsdetails, Feld „Dauer“ in Minuten; leer = Standardzeit, Standard 60 min). Kosten = gebuchte Dauer × Stundenlohn der Person; Statistik „Reinigung“ mit Ø Zeit je Person, Zeit je Reinigung (* = Standard) und Anzahl gebuchter Zeiten
- **Türcodes** (Einstellungen → Allgemein & Abruf → Türcodes, Standard aus): Zufallscode je Buchung, automatisch bei neuer Buchung (keine für Sperrzeiten), Stellen einstellbar (4–10, Standard 6) aus kryptografischem Zufall, ohne triviale Codes (1234, 1111, 1212 …) und ohne Doppelte bei überschneidender Gültigkeit. Gültig ab Check-in − 2 h bis Check-out + 1 h (einstellbar); bei geänderten Zeiten wandert die Gültigkeit mit, der Code bleibt. Eigene Zeile „Türcode: … (gültig …)“ in der Smoobu-Notiz (abschaltbar, Rest der Notiz bleibt), Anzeige in den Buchungsdetails mit „Kopieren“ und „Neu erzeugen“ (Recht „Belegung ändern“), Sehen nur mit „Gästedaten sehen“. **Schloss-Adapter je Wohnung:** kein Schloss, Matter (`matter.set_lock_credential`, ab HA 2026.4), Z-Wave JS, ZHA, Zigbee2MQTT oder eigenes Skript – Code wird 10 min vor Gültigkeitsbeginn in einen freien Code-Platz geschrieben und nach Ende bzw. bei Storno gelöscht; Fehler als HA-Meldung. Neue Entitäten „Türcode aktueller Gast“ / „Türcode nächster Gast“ je Wohnung. Antwortvorschläge nutzen den Platzhalter `{{ turcode }}`, der erst beim Senden lokal ersetzt wird – der Code geht nie an die KI
- Neue WebSocket-Befehle `smoobu/doorcode/get|renew`, `smoobu/energie/leerstand`, `smoobu/nebenkosten/list|analyse|delete`, HTTP `POST /api/smoobu/nebenkosten/<entry_id>`
- Karte `custom:smoobu-timeline-card`: Standardtitel jetzt „Kalender & Preise“ (vorher „Belegungsplan“), passend zur Seite **Kalender**
- README und Screenshots auf den Stand von 1.18.0 gebracht (Funktionsliste, neue Bilder zu Was ist neu, Einrichtung, Deckungsbeitrag, Saison-Matrix, Saisons, Kalender-Auswahl, Buchungen, Umbuchen; Optionen Saisons und Push „Umbuchung“)
- GitHub: Formulare für Fehlerberichte und Funktionswünsche (Fragen → Discussions), PR-Vorlage, `CONTRIBUTING.md`, `SECURITY.md` (private Meldung über GitHub), Verhaltenskodex; neue Prüfung `validate.yml` (hassfest, HACS, pytest) und `requirements_test.txt`

**English**
- **Role configurator** (Settings → Users & permissions, admins only): permissions per role via checkboxes, "↺ Default" per role, **custom roles** (create, rename, delete, max. 10). "No access" stays fixed. Only deviations from the defaults are stored (new options `role_rights`, `custom_roles`). Combinations such as "Change prices" without "View finances" are allowed; the card shows a hint. Deleting a custom role → affected users get the default role; if it is the default role itself, saving is refused
- New permissions **"View occupancy (guest first name only)"**, **"Take over and tick off cleaning"**, **"Assign cleaning"**. "View guest data and bookings" includes "View occupancy". Overview and calendar now only need "View occupancy"; without "guest data" the backend only delivers the guest's first name (no contact data, notes, raw Smoobu data; search only in the first name)
- New default role **"Cleaning"**: view occupancy + take over and tick off cleaning. Manager and operations get all new permissions, staff gets "Take over and tick off cleaning"
- **Cleaning board** – new card `custom:smoobu-cleaning-card` and page `smoobu-reinigung` (tab appears once the view exists): one cleaning per departure with check-out, next arrival (time, guests, dog) and same-day changeover; assign, take over/hand back, tick off. Unassigned cleanings are visible to everybody with the cleaning permission; those allowed to assign also see them on the task board under the new tab **"Cleaning"** (next 7 days)
- **Cleaning push** to the assigned person (on assignment/hand-back and the evening before, time configurable, default 18:00, respects quiet hours). Phone per person under Settings → Notifications → Cleaning (options `cleaning_phones`, `cleaning_notify`, `cleaning_remind_time`)
- **Statistics module "Cleaning"**: who cleaned which property when – per person (share, changeovers, dogs, average guests, nights, median time from check-out to tick-off), per month, per property, list; plus cleanings not ticked off. Recorded from the update on (a snapshot is stored when ticking off, done entries are kept for 3 years)
- New WebSocket commands `smoobu/cleaning/get`, `smoobu/cleaning/set`, `smoobu/cleaning/stats`
- **Electricity costs constant or measured** (Settings → Costs & prices → Electricity): "Constant" stays the default (as before). "From meter": consumption per booking from the hourly HA long-term statistics of an energy meter per property, from pre-heating start (optional timestamp sensor, otherwise check-in − 4 h, configurable) to check-out; price optionally from an entity (history, before that the fixed price); grid share optionally **hourly** from the energy dashboard (grid import ÷ house consumption). **Vacancy electricity** either **separately as fixed costs** (default, note in the statistics module contribution margin) or **distributed** to bookings by guest nights. Bookings without measurement (before the meter, future) stay estimated; field `strom_quelle` per booking. Monthly table with kWh, stays, vacancy, grid share, costs and suggestion "avg. kWh per guest night" for the constant value
- **Let the AI read your utility bill** (Costs & prices): upload PDF/JPG/PNG (max. 15 MB, stored locally only in `smoobu_belege/`, own non-browsable media source `smoobu` for the AI attachment). The assistant's AI reads heating, hot water, water, electricity and price; suggestion per value with old/new, derivation (e.g. ÷ guest nights from Smoobu), source location and checks (plausibility, guest nights and measured meter). Applied only after selection and "Save". The AI lock applies; the file is sent completely to the chosen AI (note in the card)
- **Water and heating also constant or from a meter** (Costs & prices → Water costs / Heating costs): water meter (m³ or L) × price per m³ fresh + waste water, heating meter (heat kWh, gas m³, oil L) × price per unit, each fixed or from an entity; option "meter also measures hot water". Default stays "Constant". Pre-heating and vacancy apply to all meters (block "Measurement"); `wasser_quelle`/`heizung_quelle` per booking
- **Cleaning = time × hourly wage**: standard cleaning time (60 min) and standard hourly wage; an own wage per cleaner (applies to cleanings the person did according to the cleaning board or that are assigned to them). The previous option "cleaning per stay" is now the standard hourly wage – at 60 min the amount stays the same. Statistics "Cleaning" shows costs in total and per person; field `reinigung_kosten` per booking
- **Cleaning time bookable per cleaning** (cleaning board and booking details, field "Duration" in minutes; empty = standard time, default 60 min). Costs = booked duration × the person's hourly wage; statistics "Cleaning" with average time per person, time per cleaning (* = standard) and number of booked times
- **Door codes** (Settings → General & polling → Door codes, default off): random code per booking, created automatically for new bookings (none for blocks), digits configurable (4–10, default 6) from cryptographic randomness, without trivial codes (1234, 1111, 1212 …) and without duplicates for overlapping validity. Valid from check-in − 2 h to check-out + 1 h (configurable); when times change the validity follows, the code stays. Own line "Türcode: … (gültig …)" in the Smoobu note (can be switched off, rest of the note stays), shown in the booking details with "Copy" and "Renew" (permission "Change occupancy"), visible only with "View guest data". **Lock adapter per property:** no lock, Matter (`matter.set_lock_credential`, HA 2026.4+), Z-Wave JS, ZHA, Zigbee2MQTT or own script – the code is written to a free code slot 10 min before validity starts and removed after the end or on cancellation; errors as HA notification. New entities "Door code current guest" / "Door code next guest" per property. Reply suggestions use the placeholder `{{ turcode }}`, replaced locally only when sending – the code never goes to the AI
- New WebSocket commands `smoobu/doorcode/get|renew`, `smoobu/energie/leerstand`, `smoobu/nebenkosten/list|analyse|delete`, HTTP `POST /api/smoobu/nebenkosten/<entry_id>`
- Card `custom:smoobu-timeline-card`: default title is now "Calendar & prices" (previously "Occupancy plan"), matching the **Calendar** page
- README and screenshots updated to 1.18.0 (feature list, new images for what's new, setup, contribution margin, season matrix, seasons, calendar selection, bookings, rebooking; options seasons and push "Rebooking")
- GitHub: forms for bug reports and feature requests (questions → Discussions), PR template, `CONTRIBUTING.md`, `SECURITY.md` (private reporting via GitHub), code of conduct; new check `validate.yml` (hassfest, HACS, pytest) and `requirements_test.txt`

## 1.18.0 – 2026-11-20

**Deutsch**
- Stabiler Release mit allen Änderungen der Betas 1.17.1b1–1.17.1b4 und 1.18.0b1–1.18.0b9 (Einzelheiten in den Abschnitten unten). Die wichtigsten Neuerungen:
  - **Einstellungen im Dashboard** (neue Karte `custom:smoobu-settings-card`) mit **Benutzerrollen** und Rechten je Seite/Aktion
  - **Bewertung & Empfehlung**, Preise per Button übernehmen und rückgängig machen, Last-Minute- und Lücken-Hinweise, Aufgaben-Board **„Wartet auf dich“**
  - **Kosten & Preise**: variable Kosten, Deckungsbeitrag, Preisuntergrenzen je Kanal; neues Statistik-Modul **Deckungsbeitrag** mit Brücke
  - **Statistik**: Ehrentafel, Saison-Matrix mit Abweichungen, eigene Module mit Vorlagen/Vorschau/Bearbeiten, Anordnung im HA-Benutzerprofil
  - **Saisons** frei einstellbar, mit automatischer Erkennung aus den bisherigen Jahren
  - **Finanzen** mit Filter und Vergleich wie die Statistik; Seite **Kalender** (vorher „Belegung“)
  - **Buchungen**: Summen je Gruppe, Stammgäste, **Umbuchen** (Beta) in den Details
  - **Benachrichtigungen**: Ruhezeit je Push-Art, neue Push-Art **Umbuchung**
  - **„Was ist neu“** in der Kopfzeile und neue Einstellungen im Reiter „Einrichtung“
  - Korrekturen: Preise für einzelne Nächte, Sperren bei Smoobu-Konten mit Pflichtfeldern im Buchungsformular
- **Hinweise beim Umstieg von 1.17.0**
  - Benutzerrollen: Admins haben alle Rechte. Alle anderen HA-Benutzer bekommen die Standardrolle **„Betrieb“** (alles außer Einstellungen ändern) – bitte unter Einstellungen → Benutzer & Rechte prüfen
  - Neue Einstellungen (Saisons, variable Kosten, Push „Umbuchung“, Ruhezeit je Push-Art, Rollen) erscheinen in der Übersicht unter „Wartet auf dich“ → **Einrichtung**
  - Die Seite „Belegung“ heißt jetzt „Kalender“ (Pfad `smoobu-kalender`). Bestehende Dashboards mit `smoobu-belegung` funktionieren weiter; zum Umbenennen den Pfad der Ansicht ändern
  - Für die Seite Einstellungen eine Ansicht mit Pfad `smoobu-einstellungen` und der Karte `custom:smoobu-settings-card` anlegen (siehe README / `docs/dashboard-vorlage.yaml`)

**English**
- Stable release with all changes of betas 1.17.1b1–1.17.1b4 and 1.18.0b1–1.18.0b9 (details in the sections below). Main changes:
  - **Settings in the dashboard** (new card `custom:smoobu-settings-card`) with **user roles** and rights per page/action
  - **Rating & recommendation**, apply prices with one click and undo, last-minute and gap hints, task board **"Waiting for you"**
  - **Costs & prices**: variable costs, contribution margin, price floors per channel; new statistics module **contribution margin** with bridge
  - **Statistics**: hall of fame, season matrix with deviations, custom modules with templates/preview/edit, arrangement in the HA user profile
  - **Seasons** freely adjustable, with automatic detection from past years
  - **Finances** with filters and comparison like the statistics; page **Calendar** (formerly "Occupancy")
  - **Bookings**: totals per group, returning guests, **rebooking** (beta) in the details
  - **Notifications**: quiet hours per push type, new push type **Rebooking**
  - **"What's new"** in the header and new settings in the "Setup" tab
  - Fixes: prices for single nights, blocking for Smoobu accounts with required fields in the booking form
- **Notes when upgrading from 1.17.0**
  - User roles: admins have all rights. All other HA users get the default role **"Operations"** (everything except changing settings) – please check under Settings → Users & rights
  - New settings (seasons, variable costs, "Rebooking" push, quiet hours per push type, roles) appear in the overview under "Waiting for you" → **Setup**
  - The page "Occupancy" is now called "Calendar" (path `smoobu-kalender`). Existing dashboards with `smoobu-belegung` keep working; to rename, change the path of the view
  - For the settings page create a view with path `smoobu-einstellungen` and the card `custom:smoobu-settings-card` (see README / `docs/dashboard-vorlage.yaml`)

## 1.18.0b9 – 2026-11-20

> Beta / Pre-release

**Deutsch**
- **Einstellungen: Kanäle per Dropdown statt Freitext.** Provisionen, Aufschläge je Kanal, Direktkanäle und „Zahlung über das Portal“ wählen Kanäle aus einer Liste in drei Gruppen: **Kanäle mit Buchungen** (alle geladenen Buchungen ab „Daten abrufen seit“, inkl. Stornos und künftiger, mit Anzahl), **in den Einstellungen genutzt** und **weitere Smoobu-Kanäle** (Kanaltabelle der Smoobu-API-Doku, z. B. HomeToGo, Hundeurlaub.de, HRS). Bereits eingetragene Kanäle und Sperr-Kanäle fehlen in der Liste. Ein neuer Provisions-Kanal startet mit dem Satz von „Alle übrigen Portale“, ein neuer Aufschlag mit 0 %. Kanalnamen in den Tabellen lassen sich nicht mehr per Freitext umbenennen. „Weitere Kanäle mit Buchungen“ unter der Provisionstabelle übernimmt einen Kanal per Klick
- Hintergrund: Smoobu hat **keinen API-Endpunkt für angebundene Kanäle**. Ein angebundenes Portal ohne bisherige Buchung erscheint deshalb in der Katalog-Gruppe. Sobald eine Buchung kommt, steht es unter „Kanäle mit Buchungen“
- Options-Dialog: Direktkanäle und „Zahlung über das Portal“ bieten dieselbe Kanalliste (eigene Namen weiter möglich)
- **Ruhezeit je Push-Art einstellbar.** Jede Push-Art (Buchung, Storno/Änderung, Gästenachricht, KI-Vorschlag, Zahlung, Briefing, Lücken) hat den Schalter **„Hält Ruhezeit ein“**: an = wird in der Ruhezeit gesammelt und zum Ende zugestellt, aus = kommt immer sofort. In der Einstellungs-Karte zeigt der Block Ruhezeit, welche Arten warten. Standard wie bisher (Buchung, Storno, Vorschlag warten; Zahlung, Briefing, Lücken sofort). Der Schalter „Gästenachrichten trotzdem sofort“ entfällt, sein Wert wird übernommen. Dringende Vorschläge und Bestätigungen/Fehler kommen weiter immer sofort. Neue Optionen `notify_<art>_quiet`, `notify_quiet_messages` wird für Downgrades mitgeführt
- **„Was ist neu“ und neue Einstellungen.** Neues Register `neuigkeiten.py` (je Neuerung Titel, Kurztext DE/EN, Zielseite, Stelle, nötiges Recht):
  - Kopfzeile aller Smoobu-Seiten: **„✨ Neu“** mit Anzahl ungelesener Neuerungen; die Liste zeigt Titel, Kurzbeschreibung und „Ansehen →“ bzw. „Einstellen →“. Der Link öffnet die Seite, springt zur Stelle und hebt sie kurz hervor (bei Einstellungen mit dem passenden Reiter). „Alle als gelesen markieren“, gelesene einblendbar
  - **„NEU“-Markierung an der Stelle selbst** (z. B. Modul Deckungsbeitrag, Saison-Matrix, „＋ Modul“, Block Saisons, Push „Umbuchung“, Ruhezeit, Buchungen, Umbuchen, Kalender-Hinweis); verschwindet, sobald gelesen (Klick auf die Markierung genügt)
  - Gelesen je HA-Benutzer im Benutzerprofil (`frontend/user_data`, Schlüssel `smoobu_neu_gesehen`) – auf allen Geräten gleich
  - **„Wartet auf dich“ → neuer Reiter „Einrichtung“**: neue Optionen, die für die eigene Ferienwohnung einzustellen sind (Saisons, Push „Umbuchung“, Ruhezeit je Push-Art, variable Kosten, Benutzerrollen), mit „Einstellen →“ und Erledigt/Später wie die übrigen Aufgaben. Nur mit Recht „Einstellungen“. Die neue Kategorie erscheint auch bei bereits gespeicherter Kategorienauswahl, bis diese erneut gespeichert wird
  - `smoobu/info` liefert `neuigkeiten` (nach Rechten gefiltert)
- **Buchungsdetails: Umbuchen (Zeitraum / Unterkunft).** Bei Direktbuchungen „📅 Umbuchen“: neue Anreise, Abreise und ggf. Unterkunft (Wohnungen desselben Kontos), „Prüfen“ zeigt Nächte vorher → nachher, Überschneidungen mit Buchungen/Sperren, Hinweis auf Mindestaufenthalt und einen **Preisvorschlag** (alter Preis ± Tagespreise der alten/neuen Nächte, damit Reinigung/Rabatte erhalten bleiben; ohne alte Tagespreise anteilig), im Feld änderbar. Laufende Aufenthalte lassen sich verlängern/verkürzen. Smoobu dokumentiert das Ändern von Zeitraum/Unterkunft per API nicht: die Integration sendet die Änderung, liest die Buchung danach bei Smoobu nach und meldet klar, falls Smoobu sie nicht übernommen hat; der Preis wird erst danach in einem zweiten Schritt gespeichert. Portalbuchungen zeigen nur den Hinweis, dass sie im Portal geändert werden müssen. Rechte: Umbuchen „Belegung“, Preis „Finanzen“. Neuer Websocket `smoobu/booking/move` (mit `dry_run`), Backend `umbuchung.py`
- Umbuchen ist in der Oberfläche als **BETA** gekennzeichnet, bis es mit echten Smoobu-Buchungen bestätigt ist
- Screenshot-Werkzeug: `SMOOBU_KLICK_DIALOG` (Klicks im Buchungsdialog)
- **Neue Push-Art „Umbuchung“ (Zeitraum / Unterkunft).** Ändert sich Anreise, Abreise oder die Unterkunft einer Buchung, kommt „📅 Umgebucht: Gast“ bzw. „🏠 Unterkunft gewechselt: Gast“ mit Vorher → Nachher (Zeitraum mit Nächten, Wohnungsname); weitere gleichzeitige Änderungen (Personen, Ankunft, Preis) stehen darunter. Eigene Einstellungen (an/aus, Empfänger, Ruhezeit) in der Einstellungs-Karte und im Options-Dialog; ohne eigene Einstellung gilt „Storno & Änderung“. Ist die Umbuchung ausgeschaltet, kommt die Änderung wie bisher unter „Storno & Änderung“. Unterkunftswechsel wurden bisher gar nicht gemeldet
- **Fehlerbehebung: Preise für eine einzelne Nacht.** Smoobu lehnte `"T:T"` mit 422 „Date range … is invalid“ ab; ein einzelner Tag geht jetzt als `"JJJJ-MM-TT"` (laut Smoobu-Doku). Betrifft Kalender „Preis setzen“, Last-Minute/Empfehlung „Übernehmen“, Lücken-Vorschläge und „Rückgängig“ (dort bei unterschiedlichen alten Preisen je Tag)
- **Fehlerbehebung: Sperren im Kalender.** Verlangt das Smoobu-Konto im Buchungsformular Pflichtfelder (Vorname, Nachname, E-Mail, Telefon, Adresse …), lehnte Smoobu die Sperre mit 400 ab. Die Integration sendet die Sperre zuerst ohne Gastdaten und ergänzt bei diesem Fehler genau die verlangten Felder mit neutralen Platzhaltern („Sperre Home Assistant“, `sperre@example.com` – reservierte, nie zustellbare Domain) und sendet einmal erneut
- **Kalender: Auswahl wie eine Buchung.** Erster Tipp = Anreise, zweiter Tipp = Abreise (19. + 20. = 1 Nacht); ein einzelner Tipp = 1 Nacht ab diesem Tag. Der Abreisetag ist markiert, die Leiste zeigt „Anreise … → Abreise … (n Nächte)“. Bisher zählte jeder angetippte Tag als Nacht. Dadurch auch korrigiert: „Anpassen“ einer nicht buchbaren Lücke markierte eine Nacht zu viel
- **Saisons einstellbar und automatisch erkannt.** Einstellungen → Allgemein & Abruf → **Saisons**: 2–6 Saisons mit eigenem Namen und Startmonat, jede läuft bis zum Start der nächsten (auch über den Jahreswechsel); Monatsleiste zur Kontrolle, „Standard (Jahreszeiten)“ stellt Winter/Frühling/Sommer/Herbst wieder her. **Automatische Erkennung** aus den abgeschlossenen Jahren: RevPAR je Monat im Verhältnis zum Jahres-Ø (Median über die Jahre), daraus die beste Aufteilung in 2, 3 und 4 zusammenhängende Saisons (je ≥ 2 Monate) mit Index, Auslastung und erklärter Schwankung, Empfehlung markiert; „Übernehmen“ füllt die Saisons, gespeichert wird mit „Speichern“. Ab 2 abgeschlossenen Jahren
- Die Saisons gelten überall in Statistik und Finanzen: Zeitraum „Saison“ (Blättern, Vorperiode, Vorjahr mit unterschiedlich langen Saisons), Gruppierung „Saison“ im Baukasten und in den Modulen. Bei Zeitraum „Saison“ zeigt die Filterleiste die Definition aller Saisons, die gewählte hervorgehoben
- Neue Option `saisons` (Liste aus `name`, `start`), Backend `seasons.py` (`validate`, `from_options`, `month_map`, `order`, `detect`); `smoobu/info` liefert `saisons`, Einstellungs-Meta `saison_erkennung` und `saison_standard`; `stats.query(..., seasons=)`
- **Statistik: Anordnung und eigene Module bleiben erhalten.** Sie werden jetzt im HA-Benutzerprofil gespeichert (`frontend/user_data`, Schlüssel `smoobu_statistik_layout`) statt nur im Browser-Speicher des Geräts. Sie überstehen damit Updates, App-Neuinstallationen und geleerte Caches und gelten auf allen Geräten desselben HA-Benutzers. Eine bisher nur lokal gespeicherte Anordnung wird beim ersten Laden einmalig übernommen. Werkbank/Einfach bleibt je Gerät
- **Statistik: neues Modul „Deckungsbeitrag“** (direkt nach den Kennzahlen, auch in gespeicherten Anordnungen). Gleicher Zeitraum, Vergleich und Kanalfilter wie die Kennzahlen. Kacheln DB, DB je belegter Nacht, DB-RevPAR, variable Kosten, Netto, belegte Nächte mit Vergleich (bei „Stichtag Vorjahr“ zusätzlich Endstand des DB). **Brücke „Was hat den DB verändert?“**: DB Vergleich → Preis je Nacht → weniger/mehr Nächte (Umsatz minus eingesparte bzw. zusätzliche variable Kosten) → Kosten je Nacht → DB jetzt; Summe exakt = Veränderung. Dazu ein Satz mit dem Ergebnis und DB je Monat mit Vergleichslinie. Fixkosten sind nicht enthalten
- Saison-Matrix: zusätzliche Kennzahl **DB**
- **Statistik → eigene Module: nachträglich einstellbar, Vorschau, Vorlagen.** Jedes eigene Modul hat im Kopf einen Darstellungs-Umschalter (Balken, Linie, Heatmap, Tabelle, Kennzahl – sofort gespeichert) und **✎ Bearbeiten** (auch unter „Anordnen“): öffnet den Baukasten mit allen Einstellungen; „Änderungen speichern“ überschreibt das Modul an seiner Stelle, „Als neues Modul“ legt eine Kopie an. Der Baukasten zeigt eine **Vorschau** mit aktuellem Zeitraum und Filter, die bei jeder Änderung neu lädt. **Vorlagen** zum Einfügen (z. B. Umsatz je Monat nach Kanal, Auslastung nach Wochentag, Preis je Nacht nach Saison und Kanal, Netto je Nacht nach Aufenthaltsdauer, Vorlauf/Stornoquote je Kanal, Stammgäste, Hunde je Saison, Gästesprachen, Deckungsbeitrag je Monat); Vorlagen mit Kennzahlen, die die Installation nicht liefert, werden ausgeblendet
- Eigene Module: Kanalnamen in Legende, Achse, Tabellen- und Heatmap-Kopf wie im Rest der Karte (z. B. „Direktbuchung“ statt „Direct booking“)
- Screenshot-Werkzeug: `SMOOBU_KLICK_VOLL=1` (ganze Seite nach Klick), `SMOOBU_KLICK_WARTEN` (ms)
- **Statistik: Kennzahl-Kacheln ohne Datum.** „Vgl. X“ ohne „(Stand TT.MM.JJ)“; der Stichtag steht weiter in der Vergleichsauswahl und im Tooltip
- **Stammgäste in Buchungsliste und Details.** Die Buchungsliste zeigt hinter dem Namen ein Abzeichen „↻ 2× · Mai 25“ (frühere Aufenthalte und Monat des letzten), Tooltip mit genauem Zeitraum. In den Buchungsdetails steht im Block Gast die Zeile **Stammgast**: „2× bei uns · zuletzt 01.05.25 – 04.05.25“, ein Klick auf den Zeitraum öffnet die frühere Buchung, bei Neukunden „Nein – erster Aufenthalt“. Wiedererkennung wie in der Statistik (Smoobu-Gast-ID, E-Mail oder voller Name), über alle Wohnungen des Kontos, nur echte Aufenthalte (ohne Stornos/Sperren) mit Anreise vor dieser Buchung. CSV-Export mit `besuche_vorher`, `zuletzt_anreise`, `zuletzt_abreise`
- `smoobu/bookings` und `smoobu/booking` liefern je Buchung `besuche_vorher` und ggf. `zuletzt_id`, `zuletzt_anreise`, `zuletzt_abreise`, `zuletzt_wohnung_id` (nur mit Recht „Gäste“). Backend `analytics.guest_history`
- **Buchungen: Summen in den Trennzeilen.** Die Trennzeilen Anstehend / Aktuell / Vergangen zeigen spaltengenau dieselben Summen wie die Fußzeile: Nächte, Personen, Brutto, Kosten, Netto, Netto/Nacht (Summe Netto ÷ Summe Nächte) und Offen (bei 0 leer). Wie bisher ohne Sperren und Stornos. Fußzeile und Trennzeilen nutzen denselben Code. „1 Buchungen“ heißt jetzt „1 Buchung“
- **Statistik → Saison-Matrix: Abweichungs-Indikatoren.** Jede Zelle zeigt klein unter dem Wert, wie sie zum Durchschnitt liegt: Monatszellen gegen das Ø desselben Monats, die Ø-Spalte gegen das Ø aller Monate (Saisonstärke), die Jahreszeile gegen Ø Jahr. ▲/▼ mit Abweichung, Auslastung in Prozentpunkten, sonst in %; unter ±3 PP bzw. ±5 % „≈“. Noch offene Monate und das laufende Jahr grau (Buchungsstand, keine Bewertung), offene Monate ohne Buchung ohne Indikator. Tooltip mit genauer Abweichung und Bezugswert, Legende erklärt die Indikatoren
- `smoobu/settings/get` → `meta.kanal_auswahl` (`buchungen` mit `name`, `buchungen`, `letzte`; `eingestellt`; `katalog`; `alle`). `meta.kanaele` enthält jetzt nur noch genutzte Kanäle (Buchungen + Einstellungen) statt einer festen Grundliste

**English**
- **Settings: channels from a dropdown instead of free text.** Commissions, markups per channel, direct channels and "payment via the portal" pick channels from a list in three groups: **channels with bookings** (all loaded bookings since "Fetch data since", incl. cancellations and future ones, with count), **used in the settings** and **other Smoobu channels** (channel table of the Smoobu API docs, e.g. HomeToGo, Hundeurlaub.de, HRS). Channels already entered and block channels are left out. A new commission channel starts with the rate of "All other portals", a new markup with 0 %. Channel names in the tables can no longer be renamed as free text. "Other channels with bookings" below the commission table adds a channel with one click
- Background: Smoobu has **no API endpoint for connected channels**. A connected portal without any booking yet therefore appears in the catalogue group. As soon as a booking arrives, it is listed under "Channels with bookings"
- Options dialog: direct channels and "payment via the portal" offer the same channel list (custom names still possible)
- **Quiet hours per push type.** Every push type (booking, cancellation/change, guest message, AI suggestion, payment, briefing, gaps) has the switch **"Respects quiet hours"**: on = collected during quiet hours and delivered when they end, off = always immediately. In the settings card the quiet hours block lists which types wait. Defaults as before (booking, cancellation, suggestion wait; payment, briefing, gaps immediately). The switch "Guest messages immediately anyway" is gone, its value is carried over. Urgent suggestions and confirmations/errors still always arrive immediately. New options `notify_<type>_quiet`, `notify_quiet_messages` is kept for downgrades
- **"What's new" and new settings.** New registry `neuigkeiten.py` (per change title, short text DE/EN, target page, location, required right):
  - Header of all Smoobu pages: **"✨ New"** with the number of unread changes; the list shows title, short description and "View →" or "Configure →". The link opens the page, jumps to the location and highlights it briefly (for settings with the matching tab). "Mark all as read", read ones can be shown
  - **"NEW" badge at the location itself** (e.g. contribution margin module, season matrix, "＋ Module", seasons block, "Rebooking" push, quiet hours, bookings, rebook, calendar hint); disappears once read (clicking the badge is enough)
  - Read state per HA user in the user profile (`frontend/user_data`, key `smoobu_neu_gesehen`) – the same on all devices
  - **"Waiting for you" → new tab "Setup"**: new options to configure for your own holiday rental (seasons, "Rebooking" push, quiet hours per push type, variable costs, user roles), with "Configure →" and done/later like the other tasks. Only with the "settings" right. The new category also appears with an already saved category selection until it is saved again
  - `smoobu/info` returns `neuigkeiten` (filtered by rights)
- **Booking details: rebook (dates / property).** For direct bookings "📅 Rebook": new arrival, departure and optionally property (properties of the same account), "Check" shows nights before → after, overlaps with bookings/blocks, a minimum stay hint and a **price suggestion** (old price ± daily prices of old/new nights, so cleaning/discounts are kept; without old daily prices pro rata), editable. Current stays can be extended/shortened. Smoobu does not document changing dates/property via API: the integration sends the change, reads the booking back from Smoobu and reports clearly if Smoobu did not apply it; the price is only saved afterwards in a second step. Portal bookings only show a hint that they must be changed in the portal. Rights: rebooking "occupancy", price "finances". New websocket `smoobu/booking/move` (with `dry_run`), backend `umbuchung.py`
- Rebooking is marked **BETA** in the UI until it is confirmed with real Smoobu bookings
- Screenshot tool: `SMOOBU_KLICK_DIALOG` (clicks inside the booking dialog)
- **New push type "Rebooking" (dates / property).** If arrival, departure or the property of a booking changes, "📅 Rebooked: guest" or "🏠 Property changed: guest" arrives with before → after (dates with nights, property name); other simultaneous changes (guests, arrival time, price) are listed below. Own settings (on/off, recipients, quiet hours) in the settings card and the options dialog; without own setting "Cancellation / change" applies. If rebooking is switched off, the change arrives as before under "Cancellation / change". Property changes were not reported at all before
- **Fix: prices for a single night.** Smoobu rejected `"D:D"` with 422 "Date range … is invalid"; a single day is now sent as `"YYYY-MM-DD"` (as documented by Smoobu). Affects calendar "Set price", last-minute/recommendation "Apply", gap suggestions and "Undo" (there with different old prices per day)
- **Fix: blocking in the calendar.** If the Smoobu account requires fields in the booking form (first name, last name, e-mail, phone, address …), Smoobu rejected the block with 400. The integration first sends the block without guest data and, on this error, adds exactly the requested fields with neutral placeholders ("Sperre Home Assistant", `sperre@example.com` – reserved, never deliverable domain) and retries once
- **Calendar: selection like a booking.** First tap = arrival, second tap = departure (19th + 20th = 1 night); a single tap = 1 night from that day. The departure day is marked, the bar shows "Arrival … → Departure … (n nights)". Previously every tapped day counted as a night. This also fixes: "Adjust" for an unbookable gap selected one night too many
- **Seasons adjustable and detected automatically.** Settings → General & fetching → **Seasons**: 2–6 seasons with their own name and start month, each runs until the next one starts (also across the turn of the year); month bar for checking, "Default (seasons of the year)" restores winter/spring/summer/autumn. **Automatic detection** from the completed years: RevPAR per month relative to the yearly average (median over the years), from that the best split into 2, 3 and 4 contiguous seasons (≥ 2 months each) with index, occupancy and explained variation, recommendation marked; "Apply" fills in the seasons, saved with "Save". From 2 completed years
- The seasons apply everywhere in statistics and finances: period "Season" (paging, previous period, previous year with seasons of different length), grouping "Season" in the builder and in the modules. With period "Season" the filter bar shows the definition of all seasons, the selected one highlighted
- New option `saisons` (list of `name`, `start`), backend `seasons.py` (`validate`, `from_options`, `month_map`, `order`, `detect`); `smoobu/info` returns `saisons`, settings meta `saison_erkennung` and `saison_standard`; `stats.query(..., seasons=)`
- **Statistics: arrangement and custom modules are kept.** They are now stored in the HA user profile (`frontend/user_data`, key `smoobu_statistik_layout`) instead of only in the browser storage of the device. They therefore survive updates, app reinstalls and cleared caches and apply to all devices of the same HA user. An arrangement so far stored only locally is taken over once on the first load. Workbench/simple stays per device
- **Statistics: new module "Contribution margin"** (right after the KPIs, also in saved layouts). Same period, comparison and channel filter as the KPIs. Tiles CM, CM per occupied night, CM-RevPAR, variable costs, net, occupied nights with comparison (with "same day last year" also the final CM). **Bridge "What changed the CM?"**: CM comparison → price per night → fewer/more nights (revenue minus saved or additional variable costs) → costs per night → CM now; the sum equals the change exactly. Plus a sentence with the result and CM per month with comparison line. Fixed costs are not included
- Season matrix: additional measure **CM**
- **Statistics → custom modules: adjustable afterwards, preview, templates.** Every custom module has a view switch in its header (bars, line, heatmap, table, KPI – saved immediately) and **✎ Edit** (also under "Arrange"): opens the builder with all settings; "Save changes" overwrites the module in place, "As new module" creates a copy. The builder shows a **preview** with the current period and filter that reloads on every change. **Templates** to insert (e.g. revenue per month by channel, occupancy by weekday, price per night by season and channel, net per night by length of stay, lead time/cancellation rate by channel, returning guests, dogs by season, guest languages, contribution margin per month); templates with measures the installation does not provide are hidden
- Custom modules: channel names in legend, axis, table and heatmap headers as in the rest of the card (e.g. "Direktbuchung" instead of "Direct booking" in German)
- Screenshot tool: `SMOOBU_KLICK_VOLL=1` (full page after click), `SMOOBU_KLICK_WARTEN` (ms)
- **Statistics: KPI tiles without date.** "Comp. X" without "(as of DD.MM.YY)"; the reference day is still shown in the comparison selector and the tooltip
- **Returning guests in the booking list and details.** The booking list shows a badge "↻ 2× · May 25" after the name (earlier stays and month of the last one), tooltip with the exact dates. The booking details show the row **Returning guest** in the guest block: "2× with us · last 01.05.25 – 04.05.25", clicking the dates opens the earlier booking, new guests show "No – first stay". Recognition as in the statistics (Smoobu guest ID, e-mail or full name), across all properties of the account, only real stays (no cancellations/blocks) arriving before this booking. CSV export with `besuche_vorher`, `zuletzt_anreise`, `zuletzt_abreise`
- `smoobu/bookings` and `smoobu/booking` return `besuche_vorher` per booking and, if any, `zuletzt_id`, `zuletzt_anreise`, `zuletzt_abreise`, `zuletzt_wohnung_id` (only with the "guests" right). Backend `analytics.guest_history`
- **Bookings: totals in the group rows.** The group rows Upcoming / Current / Past show the same column-aligned totals as the footer: nights, guests, gross, costs, net, net/night (total net ÷ total nights) and open (empty when 0). As before without blocks and cancellations. Footer and group rows share the same code. "1 Bookings" now reads "1 Booking"
- **Statistics → season matrix: deviation indicators.** Every cell shows a small indicator below the value: month cells vs. the Ø of the same month, the Ø column vs. the Ø of all months (seasonal strength), the year row vs. Ø year. ▲/▼ with deviation, occupancy in percentage points, otherwise in %; below ±3 pp or ±5 % "≈". Months still open and the current year in grey (booking status, no rating), open months without bookings without indicator. Tooltip with exact deviation and reference value, legend explains the indicators
- `smoobu/settings/get` → `meta.kanal_auswahl` (`buchungen` with `name`, `buchungen`, `letzte`; `eingestellt`; `katalog`; `alle`). `meta.kanaele` now only contains channels in use (bookings + settings) instead of a fixed base list

## 1.18.0b8 – 2026-11-17

> Beta / Pre-release

**Deutsch**
- **Finanzen: Filter und Vergleich wie in der Statistik.** Gleiche Filterleiste (gemeinsamer Code): Zeitraum Monat/Quartal/Saison/Jahr/Frei mit ‹ › blättern, Vergleich **Stichtag Vorjahr** (neuer Standard) / Ganzes Vorjahr / Vorperiode, Raster, Wohnungsauswahl (ohne Kopfzeilen-Auswahl), Kanal-Chips; die Leiste läuft beim Scrollen mit (am Handy nicht). Was es nur in den Finanzen gibt, bleibt: „Kein Vergleich“, Mehrfachvergleich (1–10 Jahre/Perioden) und die bisherigen Zeiträume als **Schnellwahl** (Vormonat, Folgemonat, Vorjahr, Jahr bis heute, letzte/nächste 12 Monate, gesamter Zeitraum)
- Finanzen: Bei „Stichtag Vorjahr“ zeigen Brutto, Netto, Auslastung, Netto/Nacht und Buchungen zusätzlich den **Endstand** des Vergleichszeitraums (wie Statistik, nur wenn der Zeitraum am Stichtag noch lief); Kopfzeile nennt das Stichtag-Datum
- Finanzen: **Raster** Auto/Tag/Woche/Monat für das Diagramm (Wochen = ISO-Kalenderwochen, Randwochen auf den Zeitraum gekürzt). `smoobu/analytics` hat dafür den neuen Parameter `raster` (`auto` = bisheriges Verhalten: bis 62 Tage je Tag, sonst je Monat; „Tag“ über 400 Tage → Wochen)
- Kartenoptionen Finanzen: `period` versteht weiter alle bisherigen Werte (`jahr_bis_heute` … werden zur Schnellwahl, `custom` = Frei), `compare: vorjahr_stand` = `stichtag`; neu `raster`
- Seite **„Belegung“ heißt jetzt „Kalender“** – Reiter, Dashboard-Vorlage und Pfad (`smoobu-kalender` statt `smoobu-belegung`). Bestehende Dashboards funktionieren ohne Änderung weiter: Hat ein Dashboard nur die alte Ansicht `smoobu-belegung`, zeigt der Reiter dorthin. Übersicht: Option `kalender_path` (Standard `smoobu-kalender`) ersetzt `belegung_path`, die alte Option gilt weiter

**English**
- **Finance: filters and comparison as in the statistics.** Same filter bar (shared code): period month/quarter/season/year/custom with ‹ › paging, comparison **same day last year** (new default) / full previous year / previous period, grid, property selection (unless the header shows one), channel chips; the bar stays visible while scrolling (not on phones). Finance-only features remain: "no comparison", multi-period comparison (1–10 years/periods) and the previous periods as **quick select** (previous month, next month, previous year, year to date, last/next 12 months, whole period)
- Finance: with "Same day last year", gross, net, occupancy, net/night and bookings also show the **final value** of the comparison period (as in the statistics, only if the period was still running on the reference day); the header names the reference date
- Finance: chart **grid** auto/day/week/month (weeks = ISO calendar weeks, edge weeks trimmed to the period). `smoobu/analytics` has a new parameter `raster` (`auto` = previous behaviour: daily up to 62 days, otherwise monthly; "day" over 400 days → weeks)
- Finance card options: `period` still accepts all previous values (`jahr_bis_heute` … become quick select, `custom` = custom), `compare: vorjahr_stand` = `stichtag`; new `raster`
- Page **"Occupancy" is now "Calendar"** – tab, dashboard template and path (`smoobu-kalender` instead of `smoobu-belegung`). Existing dashboards keep working unchanged: if a dashboard only has the old view `smoobu-belegung`, the tab points there. Overview: option `kalender_path` (default `smoobu-kalender`) replaces `belegung_path`, the old option still works

## 1.18.0b7 – 2026-11-17

> Beta / Pre-release

**Deutsch**
- **Ehrentafel** (Statistik, neues Modul nach „Gäste“, nur Werkbank): Fun-Statistik mit zwei Ranglisten der abgeschlossenen Aufenthalte (Abreise im Zeitraum) – 🏆 **Die Goldene Fußmatte** (hoher Preis je Nacht netto, wenig Anliegen, pünktlich, früh gebucht, Stammgast-Bonus +25) und 🪠 **Die Rostige Klobürste** (Extra-Stunden durch früheren Check-in/späteren Check-out gegenüber den Standardzeiten, Billigpreis, viele Gastnachrichten je Nacht, kurzer Aufenthalt, hoher Portal-Abzug). Je Kriterium Perzentil-Rang 0–100, gleich gewichtet; fehlende Werte zählen neutral. Je Platz Medaille, Vorname + Initial, zwei Sprüche, Tooltip mit allen Kriterien, Klick öffnet die Buchung; Hinweis unter 5 Gästen. Niemand steht auf beiden Listen. Neuer Websocket-Modus `smoobu/stats` → `mode: ranking` (Recht „Finanzen“). Nur Anzeige, nichts wird gespeichert oder verschickt
- Statistik, Modul Gäste: je Merkmal (Personen, Hund, Stammgäste, Sprache) neben dem Anteil der **Buchungen** auch der Anteil der **Nächte** (Doppelbalken, Tooltip mit Anzahl). Buchungen nach Anreise im Zeitraum, Nächte = belegte Nächte im Zeitraum
- Statistik, Kennzahlenleiste: Bei „Stichtag Vorjahr“ zeigt jede Kachel zusätzlich den **Endstand** des Vergleichszeitraums (mit Abstand in % bzw. PP) und das Stichtag-Datum. Pfeil und Farbe bewerten weiter gegen den Stand am Stichtag. Nur wenn der Vergleichszeitraum am Stichtag noch lief (sonst sind beide gleich)
- Statistik: Zeitraum „Saison“ zeigte bei Frühling, Sommer und Herbst „undefined“ statt des Namens (Monatsschlüssel 1-basiert statt 0-basiert)

**English**
- **Hall of fame** (statistics, new module after "Guests", workbench only): fun statistics with two rankings of completed stays (departure in the period) – 🏆 **The Golden Doormat** (high net price per night, few requests, punctual, booked early, regular bonus +25) and 🪠 **The Rusty Toilet Brush** (extra hours from earlier check-in/later check-out compared with the default times, bargain price, many guest messages per night, short stay, high portal deduction). Percentile rank 0–100 per criterion, equally weighted; missing values count as neutral. Per place medal, first name + initial, two quips, tooltip with all criteria, click opens the booking; notice below 5 guests. Nobody appears on both lists. New websocket mode `smoobu/stats` → `mode: ranking` (permission "finances"). Display only, nothing is stored or sent
- Statistics, Guests module: for each attribute (people, dog, repeat guests, language) the share of **nights** is shown next to the share of **bookings** (double bar, tooltip with counts). Bookings by arrival in the period, nights = occupied nights within the period
- Statistics, KPI bar: with "Same day last year" every tile also shows the **final value** of the comparison period (with difference in % or PP) and the reference date. Arrow and colour still rate against the status on the reference day. Only when the comparison period was still running on the reference day (otherwise both are equal)
- Statistics: period "Season" showed "undefined" instead of the name for spring, summer and autumn (month keys 1-based instead of 0-based)

## 1.18.0b6 – 2026-11-17

> Beta / Pre-release

**Deutsch**
- **Datenschutz-Stufe für die KI** (Optionen → KI-Assistent und Einstellungskarte → KI-Assistent → Datenschutz): Standard (Voreinstellung, auch für bestehende Installationen), Streng, Maximal, Individuell. Standard ersetzt bekannte Gastnamen durch Platzhalter (`[GAST_VORNAME]`, `[GAST_NAME]`, `[GAST_NACHNAME]`) und setzt sie nach der Antwort lokal wieder ein, schwärzt zusätzlich Adresse, PLZ/Ort, Kennzeichen, Geburtsdatum und Ausweisnummer und gibt Daten relativ an (`[ANREISE]`/`[ABREISE]` im Entwurf, lokal ersetzt). Gilt für Gästenachricht, Verlauf, Lernbeispiele (Name des Gastes der jeweiligen Buchung), Status-Entitäten (laufende und nahe Gäste) und „Wissen erzeugen“ (Vorlagen mit Buchungsbezug ab dem nächsten Import). Streng: nur 2 Nachrichten Verlauf, ohne Kanal/Bezahlstatus. Maximal: nur Gästenachricht + Wissensdatenbank. Individuell: neun Einzelschalter mit Beschreibung der Einbuße. Neue Optionen `ai_privacy`, `ai_pseudonym`, `ai_redact_extended`, `ai_dates_relative`, `ai_send_dates`, `ai_send_guests`, `ai_send_payment`, `ai_history`, `ai_examples`, `ai_status`, `ai_host_names`
- **Eigene Namen** (`ai_host_names`, Standard: Wörter aus dem Kontonamen) werden nie ersetzt – sonst würde z. B. eure Signatur bei einem gleichnamigen Gast zum Platzhalter
- **„Was geht an die KI?“** in der Einstellungskarte: letzte KI-Anfrage (exakter Text, nur im Speicher) und Probelauf mit der laufenden/nächsten Buchung ohne KI-Aufruf (auch bei gesperrter KI). Neuer Websocket-Befehl `smoobu/assistant/preview` (Recht „Antworten“); Assistent-Zustand mit `datenschutz` und `letzte_ki_anfrage`
- Grenzen: nur bekannte Namen und typische Muster; die Gästenachricht bleibt Freitext. Details in der README unter „Datenschutz-Stufe für die KI“

**English**
- **Privacy level for the AI** (options → AI assistant and settings card → AI assistant → privacy): Standard (default, also for existing installations), Strict, Maximum, Custom. Standard replaces known guest names with placeholders (`[GAST_VORNAME]`, `[GAST_NAME]`, `[GAST_NACHNAME]`) and restores them locally after the reply, additionally redacts address, postcode/town, licence plate, date of birth and ID number, and uses relative dates (`[ANREISE]`/`[ABREISE]` in the draft, replaced locally). Applies to guest message, history, learning examples (name of the guest of that booking), status entities (current and upcoming guests) and "build knowledge" (templates with booking reference from the next import). Strict: only 2 messages of history, no channel/payment status. Maximum: guest message + knowledge base only. Custom: nine individual switches with a description of the loss. New options `ai_privacy`, `ai_pseudonym`, `ai_redact_extended`, `ai_dates_relative`, `ai_send_dates`, `ai_send_guests`, `ai_send_payment`, `ai_history`, `ai_examples`, `ai_status`, `ai_host_names`
- **Own names** (`ai_host_names`, default: words of the account name) are never replaced – otherwise e.g. your signature would become a placeholder for a guest with the same name
- **"What goes to the AI?"** in the settings card: last AI request (exact text, memory only) and a dry run with the current/next booking without calling the AI (works with AI locked too). New websocket command `smoobu/assistant/preview` (permission "reply"); assistant state with `datenschutz` and `letzte_ki_anfrage`
- Limits: only known names and typical patterns; the guest message stays free text. Details in the README under "Privacy level for the AI"

## 1.18.0b5 – 2026-11-17

> Beta / Pre-release

**Deutsch**
- **Übersicht → „Wartet auf dich“ als Aufgaben-Board:** Reiter mit Zählern (Alle · Nachrichten · Rechnungen · Preise · Last-Minute · Lücken). Neu dabei: Preisempfehlungen der Monate (senken/erhöhen), Feiertagsnächte und Wochenend-Aufschlag, Last-Minute-Nächte mit Vorschlag und kurze Lücken – jeweils mit „Übernehmen …“ bzw. „Anpassen …“ (gleicher Dialog wie in der Statistik). Jede Aufgabe hat „✓ Erledigt“ (ausblenden) und „Später“ (morgen wieder), gespeichert im Backend und damit für alle Benutzer gleich; ändert sich der Inhalt (neue Gastnachricht, anderer Preisvorschlag), erscheint sie wieder. „Alle“ zeigt je Kategorie höchstens 2 mit Link „weitere“. Welche Kategorien erscheinen, steht in den Einstellungen unter Allgemein & Abruf (Option `task_categories`). Neue Websocket-Befehle `smoobu/tasks/get` und `smoobu/tasks/set` (Recht je Kategorie: Nachrichten = Antworten, Rechnungen = Belegung, Preise/Last-Minute/Lücken = Preise)
- **Übersicht ohne Recht „Finanzen“:** Umsatz-Kacheln und Fußzeile entfallen, Rest bleibt nutzbar (vorher Fehler)

**English**
- **Overview → "Waiting for you" as a task board:** tabs with counts (all · messages · invoices · prices · last minute · gaps). New: monthly price recommendations (lower/raise), holiday nights and weekend markup, last-minute nights with a suggestion and short gaps – each with "Apply …" or "Adjust …" (same dialog as in statistics). Every task has "✓ Done" (hide) and "Later" (back tomorrow), stored in the backend and therefore the same for all users; if the content changes (new guest message, different price suggestion) it reappears. "All" shows at most 2 per category with a "more" link. Which categories appear is set under settings → general & polling (option `task_categories`). New websocket commands `smoobu/tasks/get` and `smoobu/tasks/set` (permission per category: messages = reply, invoices = occupancy, prices/last minute/gaps = prices)
- **Overview without the "finances" permission:** revenue tiles and footer are omitted, the rest stays usable (previously an error)

## 1.18.0b4 – 2026-11-17

> Beta / Pre-release

**Deutsch**
- **Genius-Check (Einstellungen → Kosten & Preise):** zählt die Booking.com-Buchungen der letzten 24 Monate mit Genius-Gast (Booking.com schreibt „booker_is_genius“ in die Notiz) und zeigt den Anteil neben der Option „Anteil Genius-Buchungen“, mit Button „Gemessenen Anteil übernehmen“. Den Rabatt selbst liefert Booking.com nicht. Buchungsdatensätze haben dafür das neue Feld `genius`

**English**
- **Genius check (settings → costs & prices):** counts the Booking.com bookings of the last 24 months with a Genius guest (Booking.com writes "booker_is_genius" into the note) and shows the share next to the option "share of Genius bookings", with a "use measured share" button. Booking.com does not provide the discount itself. Booking records get the new field `genius` for this

## 1.18.0b3 – 2026-11-17

> Beta / Pre-release

**Deutsch**
- **Empfehlungen übernehmen (Statistik → Bewertung & Empfehlung):** Button „Übernehmen …“ an jeder Monatsempfehlung, „Preis anpassen …“ immer, dazu Buttons an den Hinweisen (Fr/Sa-Aufschlag, Feiertagsnächte, Mindestaufenthalt, je kurze Lücke). Dialog mit änderbarem Preis bzw. Prozent, Zeitraum (Standard: ab heute bis Monatsende), Mindestaufenthalt sowie den Häkchen „Feiertagsnächte auslassen“ (beim Senken vorbelegt) und „Tage mit eigenem Preis nicht überschreiben“ (vorbelegt; eigener Preis = abweichend vom häufigsten Preis im Zeitraum). Live-Vorschau der Kanalpreise mit Aufschlägen und Netto, Warnung unter der Untergrenze, „Vorschau“ zeigt je Tag alt → neu und was ausgelassen wird, vor dem Schreiben eine Bestätigung. Danach liest die Integration die Preise in Smoobu nach und meldet Abweichungen. Ereignis `smoobu_event` mit `typ: preise_geaendert` bzw. `preise_zurueckgesetzt`
- **Rückgängig:** die letzten Preisänderungen stehen im Modul; „Rückgängig“ setzt die vorher gespeicherten Tageswerte wieder (nur künftige Tage, übersteht Neustarts, je Konto die letzten 30 Änderungen)
- **Benutzerrollen:** Verwalter (alles inkl. Einstellungen), Betrieb (alles außer Einstellungen – Standard, entspricht dem bisherigen Verhalten), Mitarbeiter (Belegung, Gäste, Nachrichten und Antworten, keine Finanzen/Preise), Nur lesen (Belegung, Gäste, Nachrichten), Kein Zugriff. Rollen vergeben nur HA-Admins (Einstellungskarte → „Benutzer & Rechte“, mit Übersicht Rolle × Recht); Admins haben immer alle Rechte. Geprüft im Backend bei allen Websocket-Befehlen der Karten und bei den Aktionen `smoobu.*` (Automationen ohne Benutzer dürfen weiterhin alles). Ohne Recht fehlen Seiten und Buttons, Preise/Umsätze werden aus Buchungsdaten entfernt, Tagespreise ohne Preis ausgeliefert. Bisherige Option „Einstellungen im Dashboard erlauben für“ gilt als Rolle Verwalter. Grenze: normale HA-Entitäten (z. B. Umsatz-Sensoren) kann HA nicht je Benutzer sperren
- **Last-Minute (Hinweis im Modul „Bewertung & Empfehlung“):** freie Nächte im Last-Minute-Fenster mit Auswertung der eigenen Buchungen (Anteil, Netto je Nacht Last-Minute gegen früher gebucht, Ø Aufenthalt) und einem bereinigten Vergleich innerhalb desselben Kanals und Monats (sonst verfälschen Kanal-Aufschläge und Saison das Bild). Standard: kein Rabatt. Ein Rabatt bis zum eingestellten Höchstwert (Standard 10 %, nie unter der Untergrenze) wird nur für Nächte vorgeschlagen, die eine Lücke zwischen zwei Gästen sind oder in einem schwach gebuchten Monat liegen – je Nacht per Button übernehmbar. Zeigt der bereinigte Vergleich eine Prämie ≥ 5 % (mind. 10 Nächte), gibt es stattdessen einen Button „+5 % auf die freien Nächte“. Neue Optionen „Last-Minute-Fenster“ (1–14 Tage, Standard 3) und „Höchster Last-Minute-Rabatt“ (Standard 10 %) unter Kosten & Preise
- **Neue Websocket-Befehle:** `smoobu/rates/apply` (mit `dry_run` für die Vorschau), `smoobu/rates/undo`, `smoobu/rates/changes`
- **Einstellungen → Provisionen & Kanäle:** neue Spalte „Provision von Smoobu (24 Monate)“ je Kanal – ✓ Smoobu liefert (mit Ø %, der %-Wert ist dann nur Rückfall), ◐ teilweise (x/y Buchungen) oder „Wert hier wird genutzt“; Direktkanäle gekennzeichnet; Kanäle mit Buchungen ohne eigene Zeile darunter. Gültig = 1–40 % des Preises (darüber als unplausibel ignoriert)
- **Fix:** Bestätigungsdialoge waren ungestylt (der Schriftname mit Anführungszeichen beendete das style-Attribut)

**English**
- **Apply recommendations (statistics → assessment & recommendation):** "Apply …" button on every monthly recommendation, "Adjust price …" always, plus buttons on the notes (Fri/Sat markup, holiday nights, minimum stay, per short gap). Dialog with editable price or percentage, range (default: today until month end), minimum stay and the checkboxes "skip holiday nights" (preset when lowering) and "don't overwrite days with their own price" (preset; own price = different from the most common price in the range). Live preview of channel prices with markups and net, warning below the floor, "Preview" lists old → new per day and what is skipped, confirmation before writing. Afterwards the integration reads the prices back from Smoobu and reports deviations. Event `smoobu_event` with `typ: preise_geaendert` or `preise_zurueckgesetzt`
- **Undo:** recent price changes are listed in the module; "Undo" restores the previously stored daily values (future days only, survives restarts, last 30 changes per account)
- **User roles:** manager (everything incl. settings), operations (everything except settings – default, matches previous behaviour), staff (occupancy, guests, messages and replies, no finances/prices), read only (occupancy, guests, messages), no access. Only HA admins assign roles (settings card → "Users & permissions", with a role × permission overview); admins always have all permissions. Checked in the backend for all card websocket commands and the `smoobu.*` actions (automations without a user may still do everything). Without permission pages and buttons are hidden, prices/revenue are removed from booking data, daily rates come without price. The existing option "Allow dashboard settings for" counts as manager. Limitation: regular HA entities (e.g. revenue sensors) cannot be restricted per user by HA
- **Last minute (note in the assessment & recommendation module):** free nights in the last-minute window with an analysis of the property's own bookings (share, net per night last minute vs. booked earlier, average stay) and an adjusted comparison within the same channel and month (otherwise channel markups and season distort the picture). Default: no discount. A discount up to the configured maximum (default 10 %, never below the floor) is only suggested for nights that are a gap between two guests or fall in a weakly booked month – applicable per night via button. If the adjusted comparison shows a premium ≥ 5 % (at least 10 nights), a "+5 % on the free nights" button is offered instead. New options "last-minute window" (1–14 days, default 3) and "maximum last-minute discount" (default 10 %) under costs & prices
- **New websocket commands:** `smoobu/rates/apply` (with `dry_run` for the preview), `smoobu/rates/undo`, `smoobu/rates/changes`
- **Settings → commissions & channels:** new column "commission from Smoobu (24 months)" per channel – ✓ Smoobu provides (with average %, the % value is then only a fallback), ◐ partly (x/y bookings) or "value here is used"; direct channels marked; channels with bookings but no own row listed below. Valid = 1–40 % of the price (above is ignored as implausible)
- **Fix:** confirmation dialogs were unstyled (the quoted font name ended the style attribute)

## 1.18.0b2 – 2026-11-17

> Beta / Pre-release

**Deutsch**
- **Gesperrte Nächte sind nicht verfügbar:** Auslastung, RevPAR, Netto-RevPAR (Statistik) und die Auslastung der Finanzen/Auswertungs-Sensoren rechnen jetzt mit verfügbaren Nächten = Tage × Wohnungen − gesperrte Nächte. Bisher zählte die Statistik gesperrte Nächte als verfügbar, die Finanzen nicht – jetzt einheitlich. Gesperrte Nächte werden gesondert ausgewiesen (Kennzahl „Auslastung“: „… verfügbar · … gesperrt“, je Zelle `verfuegbar`/`gesperrt`). Die bisherigen Monats-Sensoren (`…_auslastung_monat` usw.) bleiben unverändert
- **Kosten & Preise (neuer Options-Schritt und Reiter in der Einstellungskarte):** variable Kosten je Aufenthalt (Reinigung, Wäsche) und je Nacht (Heizung, Warmwasser, Wasser, Strom). Heizung und Warmwasser als Jahreskosten aus der Nebenkostenabrechnung, verteilt nach Gradtagszahlen (Januar ≈ 12× Juli, Oktober dazwischen) und skaliert auf die Gästenächte des Abrechnungsjahres. Strom mit Netzanteil je Monat: Netzstrom zum Netzpreis, PV-Strom zur Einspeisevergütung. Dazu Aufschläge je Kanal aus dem Smoobu-Preistool sowie Booking.com-Genius (Rabatt und Anteil; ohne Angabe 100 % = vorsichtig). Die Smoobu-API liefert diese Aufschläge nicht – deshalb als Option
- **Deckungsbeitrag:** je Buchung Netto − variable Kosten; neue Statistik-Kennzahlen `var_kosten`, `db`, `db_pro_nacht`, `db_revpar` (auch im Baukasten)
- **Statistik → Bewertung & Empfehlung (neues Modul, direkt nach den Kennzahlen, auch in „Einfach“):** je Monat (laufender + 2) Buchungsstand gegen den Stand der Vorjahre am gleichen Tag (P25–P75, Median), Bewertung schwach/normal/stark (mind. 10 PP Abstand zum Median), Netto- und DB-RevPAR, Prognose. Empfehlung Preis senken (−10 %, deutlich unter allen Vorjahren −15 %) / halten / erhöhen (+10 %) – nur für Monate, die innerhalb von 31 Tagen beginnen, und nie unter der Preisuntergrenze. Preisuntergrenze je Kanal und 1/2/3 Nächte = Basispreis, ab dem der Deckungsbeitrag positiv ist (Aufschlag, Genius und gemessene Kostenquote des Kanals eingerechnet). Hinweise: einheitlicher Preis, Wochenend-Aufschlag (Belegung Fr/Sa gegen So–Do, mit € je Jahr), Einzelnächte (Deckungsbeitrag 1 vs. 2 Nächte), Feiertagsnächte zum Normalpreis (Bayern + Heiligabend/Silvester, mit Belegung der Vorjahre), kurze Lücken mit Untergrenze. Bewusst kein „optimaler Preis“: die Preiselastizität ist ohne Preis-Historie nicht schätzbar

**English**
- **Blocked nights are not available:** occupancy, RevPAR, net RevPAR (statistics) and the occupancy of the finance/analysis sensors now use available nights = days × properties − blocked nights. Previously statistics counted blocked nights as available and finances did not – now consistent. Blocked nights are shown separately (KPI "occupancy": "… available · … blocked", per cell `verfuegbar`/`gesperrt`). The existing monthly sensors (`…_auslastung_monat` etc.) are unchanged
- **Costs & prices (new options step and settings card tab):** variable costs per stay (cleaning, laundry) and per night (heating, hot water, water, electricity). Heating and hot water as annual costs from the utility bill, spread by heating degree days (January ≈ 12× July, October in between) and scaled to the guest nights of the billing year. Electricity with a grid share per month: grid power at the grid price, PV power at the feed-in tariff. Plus markups per channel from the Smoobu pricing tool and Booking.com Genius (discount and share; default 100 % = cautious). The Smoobu API does not provide these markups – hence an option
- **Contribution margin:** per booking net − variable costs; new statistics measures `var_kosten`, `db`, `db_pro_nacht`, `db_revpar` (also in the builder)
- **Statistics → assessment & recommendation (new module, right after the KPIs, also in Simple):** per month (current + 2) bookings on hand vs. previous years on the same day (P25–P75, median), rating weak/normal/strong (at least 10 pp from the median), net and margin RevPAR, forecast. Recommendation lower price (−10 %, clearly below all previous years −15 %) / keep / raise (+10 %) – only for months starting within 31 days and never below the price floor. Price floor per channel and 1/2/3 nights = base price from which the margin is positive (markup, Genius and measured channel cost ratio included). Notes: uniform price, weekend markup (occupancy Fri/Sat vs. Sun–Thu, with € per year), single nights (margin 1 vs. 2 nights), holiday nights at the normal price (Bavaria + Christmas Eve/New Year's Eve, with previous years' occupancy), short gaps with floor. Deliberately no "optimal price": price elasticity can't be estimated without price history

## 1.18.0b1 – 2026-11-17

> Beta / Pre-release

**Deutsch**
- **Einstellungen im Dashboard:** neue Karte `custom:smoobu-settings-card` mit vier Reitern – Benachrichtigungen (je Push-Art an/aus, Empfänger als Handy-Chips, Uhrzeiten, Ruhezeit; Warnung „kein Empfänger“), KI-Assistent (KI erlauben, KI-Entität, Antwortvorschläge, Kontext-Entitäten, Dashboard-Pfad), Provisionen & Kanäle (Provision je Kanal inkl. eigener Kanäle, übrige Portale, Direktkanäle, Kanäle mit Portalzahlung) und Allgemein & Abruf (Webhook, Intervall, Zeiträume, Standardzeiten, Wartezeit, Historie, Wohnungskürzel). Entwurf bleibt bis „Speichern“ lokal, „Verwerfen“ setzt zurück, Fehler erscheinen am Feld und am Reiter. Nach dem Speichern lädt die Integration neu, alle Karten holen danach frische Daten (neues Datenabo)
- **Berechtigung:** neue Option „Einstellungen im Dashboard erlauben für“ (HA-Benutzer). Admins dürfen immer, die gewählten Benutzer zusätzlich; geprüft im Backend (`smoobu/settings/get|set`), andere sehen „Keine Berechtigung“. Die Liste selbst ändern nur Admins
- **Kopfzeile:** optionaler Reiter „Einstellungen“ mit Zahnrad (erscheint, sobald das Dashboard eine Ansicht `smoobu-einstellungen` hat; am Handy nur das Zahnrad)
- **Optionen → Benachrichtigungen:** Abschnitte jetzt optional ohne eigenen Standardwert (Fix aus 1.17.1b4 vervollständigt) – fehlende Abschnitte übernehmen beim Speichern die bisherigen Werte statt abgelehnt zu werden

**English**
- **Settings in the dashboard:** new card `custom:smoobu-settings-card` with four tabs – notifications (on/off per push type, recipients as phone chips, times, quiet hours; "no recipient" warning), AI assistant (allow AI, AI entity, reply suggestions, context entities, dashboard path), commissions & channels (commission per channel incl. custom channels, other portals, direct channels, channels paid via portal) and general & polling (webhook, interval, ranges, default times, waiting time, history, apartment codes). The draft stays local until "Save", "Discard" resets, errors are shown at the field and the tab. After saving the integration reloads and all cards fetch fresh data (new subscription)
- **Permission:** new option "Allow dashboard settings for" (HA users). Admins always may, the selected users additionally; checked in the backend (`smoobu/settings/get|set`), others see "No permission". Only admins can change the list itself
- **Header:** optional "Settings" tab with a gear icon (shown once the dashboard has a view `smoobu-einstellungen`; gear only on phones)
- **Options → notifications:** sections are now optional without their own default (completes the 1.17.1b4 fix) – missing sections keep the previous values on save instead of being rejected

## 1.17.1b4 – 2026-11-17

> Beta / Pre-release

**Deutsch**
- **Fix Optionen → Benachrichtigungen:** OK-Button war gesperrt, weil die Abschnitte einen leeren Standardwert hatten und damit die Vorbelegung der Pflichtfelder (z. B. „aktiv“) im Formular überschrieben

**English**
- **Fix options → notifications:** the OK button was disabled because the sections had an empty default that overrode the pre-filled required fields (e.g. "active") in the form

## 1.17.1b3 – 2026-11-16

> Beta / Pre-release

**Deutsch**
- **Kommunikationsaufwand je Kanal (Statistik → Service):** welche Portal-Gäste generell die meiste Kommunikation brauchen – je Kanal Anliegen je Buchung (Gastnachrichten bis zur nächsten Antwort, mehrere am Stück zählen einmal), Gastnachrichten je Buchung, Anteil Buchungen mit Nachricht und Index (Ø aller Kanäle = 100), mit Hinweis auf den aufwendigsten Kanal. Eigene und automatische Nachrichten zählen nicht (Smoobu kennzeichnet Vorlagen nicht). Die Zähler entstehen beim gedrosselten Nachrichtenabruf; bereits ausgewertete Buchungen werden dafür einmalig im Hintergrund nachgeladen. Buchungen ganz ohne Nachrichtenverlauf (Smoobu liefert für ältere Buchungen oft keinen) zählen nicht als „0 Anliegen“
- **Saison-Matrix:** Spalte Ø jetzt ganz links, danach die Jahre absteigend (aktuelles bzw. kommendes Jahr vorne) – am Handy ist das Wichtigste ohne Wischen sichtbar; gilt auch für die Jahreszeile; Legende erklärt ADR, RevPAR und Ø immer (nicht nur bei gewählter Kennzahl)

**English**
- **Communication effort per channel (statistics → service):** which portals' guests generally need the most communication – per channel requests per booking (guest messages until the next reply, several in a row count once), guest messages per booking, share of bookings with a message and an index (average of all channels = 100), naming the most demanding channel. Own and automatic messages are not counted (Smoobu does not mark templates). Counts are collected by the throttled message fetch; already evaluated bookings are reloaded once in the background. Bookings without any message history (Smoobu often has none for older bookings) do not count as "0 requests"
- **Season matrix:** Ø column now first, followed by the years in descending order (current or next year first) – on phones the most relevant columns are visible without scrolling; also applies to the year row; legend always explains ADR, RevPAR and Ø (not only for the selected measure)

## 1.17.1b2 – 2026-11-16

> Beta / Pre-release

**Deutsch**
- **Abkürzungen erklärt:** kurze Legendenzeile mit ADR (Ø Preis je belegter Nacht), RevPAR (Umsatz je verfügbarer Nacht = ADR × Auslastung), Netto-RevPAR, PP (Prozentpunkte), n, Vgl., Ø, N, Δ, Pace, P10–P90 und KW – unter der Kennzahlenleiste und dem Verlauf der Statistik, in Saison-Matrix, Wochentag-Belegung, Buchungstempo und unter der Kanaltabelle der Finanzen
- **Lücken an einer Stelle bearbeiten:** in der Übersicht bei „nicht buchbar“ neuer Button „Anpassen“ → öffnet den Belegungsplan mit markierten Tagen und vorausgefülltem Mindestaufenthalt (Option `belegung_path`, Standard `smoobu-belegung`, leer = ohne Button); Reiter und Kachel „Lücken“ im Assistenten entfallen (Auswertung bleibt in Statistik → Verlorene Nächte)
- **Keine doppelte Wohnungsauswahl:** die Statistik blendet ihre eigene Auswahl aus, sobald die Kopfzeile eine zeigt (gleiche Einstellung)
- **Statistik:** Modul „Datentabelle“ standardmäßig ausgeblendet (doppelt die Seite Buchungen inkl. CSV), über ↺ wieder einblendbar; neue Option `simple_users` (Benutzername oder -ID) – diese Nutzer starten ohne eigene Wahl in „Einfach“
- **Kopfzeile:** optionaler Rücksprung vor den Reitern (`home: {name, path}`), z. B. „← Host“

**English**
- **Abbreviations explained:** short legend line for ADR, RevPAR, net RevPAR, PP, n, Vgl., Ø, N, Δ, pace, P10–P90 and KW – below the statistics KPI bar and trend, in season matrix, weekday occupancy, booking pace and below the finance channel table
- **Fix gaps in one place:** in the overview "not bookable" gaps get an "Adjust" button → opens the occupancy plan with the days selected and minimum stay prefilled (option `belegung_path`, default `smoobu-belegung`, empty = no button); the assistant's "Gaps" tab and tile are gone (analysis stays in statistics → lost nights)
- **No duplicate apartment picker:** statistics hides its own picker when the header shows one (same setting)
- **Statistics:** "Data table" module hidden by default (duplicates the bookings page incl. CSV), can be restored via ↺; new option `simple_users` (user name or ID) – these users start in "Simple" without a stored choice
- **Header:** optional back link before the tabs (`home: {name, path}`), e.g. "← Host"


## 1.17.1b1 – 2026-11-16

> Beta / Pre-release

**Deutsch**
- **Korrektur Übersicht – aktueller Gast am Anreisetag:** Status, Gästekarten und die Zeilen der Mehr-Wohnungen-Ansicht rechnen jetzt mit Uhrzeit (wie die Sensoren). Ab der Check-in-Zeit ist der anreisende Gast „Aktueller Gast“, ab der Check-out-Zeit ist der abreisende Gast weg. Vorher blieb der Gast am Anreisetag bis Mitternacht „Nächster Gast, heute“ und „Aktueller Gast“ zeigte „keine“. Gilt auch für Gästewechsel und Abreise; Uhrzeit in der Zeitzone von Home Assistant. Die Übersicht prüft jede Minute und zeichnet bei Statuswechsel neu (offenes Tablet)
- **Anzeigenamen statt Schlüsseln:** Kanäle „Direct booking“ → „Direktbuchung“, „Blocked channel“ → „Sperre“; Preiselemente „Base price“ → „Grundpreis“, „Cleaning fee“ → „Endreinigung“ u. a. (0-€-Rabattzeilen ausgeblendet); Assistent: Anlass-Auswahl, Absicht im KI-Vorschlag („Späte Anreise“ statt `spaete_anreise`), Quelle und Status der Wissenseinträge und Vorschläge, KI-Name statt Entitäts-ID. Nur Anzeige – Filter, Farben und Sensoren nutzen weiter die Smoobu-Namen
- **Buchungsdetails:** Ankunfts-/Abreisezeit und Notiz werden wie alle Schreibaktionen erst nach Bestätigung in Smoobu gespeichert; „In Smoobu öffnen“ heißt jetzt „Smoobu öffnen“ (führt zur Smoobu-Anmeldung, Tooltip mit Buchungs-ID)
- **„Wartet auf dich“:** Portal-Buchungen ohne Markierung heißen „Nicht als erhalten markiert“ statt „Zahlung offen“ – es ist kein Geld offen, nur die Markierung fehlt
- Englische Oberfläche: relative Zeitangaben („vor 2 Std.“) übersetzt
- Dashboard-Vorlage: Statistik-Seite ergänzt, Geräte-Chips der Übersicht nur noch als auskommentiertes Beispiel; Screenshots neu erzeugt

**English**
- **Fix overview – current guest on arrival day:** status, guest cards and the rows of the multi-property view now use the time of day (like the sensors). From the check-in time the arriving guest is the "Current guest", from the check-out time the departing guest is gone. Previously the guest stayed "Next guest, today" until midnight and "Current guest" showed "none". Also applies to changeover and departure days; time in Home Assistant's time zone. The overview checks every minute and re-renders when the status changes (open tablet)
- **Display names instead of keys:** German UI shows "Direktbuchung"/"Sperre" for Smoobu's "Direct booking"/"Blocked channel" and German price element names; assistant: occasion picker, intent of the AI suggestion, source and status of knowledge entries and suggestions, AI name instead of the entity ID. Display only – filters, colours and sensors keep Smoobu's names
- **Booking details:** arrival/departure time and note are saved in Smoobu only after confirmation, like every other write action; "Open in Smoobu" is now "Open Smoobu" (opens the Smoobu login, tooltip with booking ID)
- **"Waiting for you":** unmarked portal bookings are labelled "Not marked as received" instead of "Payment open" – no money is outstanding, only the mark is missing
- English UI: relative times translated
- Dashboard template: statistics page added, overview device chips only as a commented example; screenshots regenerated

## 1.17.0 – 2026-11-16

**Deutsch**
- Stabiler Release mit allen Änderungen der Betas 1.17.0b1–1.17.0b6 (Einzelheiten in den Abschnitten unten): u. a. Statistik-Werkbank (neue Karte `custom:smoobu-stats-card` mit 12 Modulen, Baukasten und Prognose nach Buchungstempo), Zahlungseingang im Dashboard markieren (auch Portal-Buchungen), Benachrichtigungen mit Ruhezeit, Wohnungskürzel, Option „Daten abrufen seit“, Datumsanzeige mit Jahr
- **Buchungszeitpunkt:** Ansicht „Gebucht im → für“ ist jetzt Standard, „Monate vorher“ per Umschalter

**English**
- Stable release with all changes of betas 1.17.0b1–1.17.0b6 (details in the sections below): including the statistics workbench (new card `custom:smoobu-stats-card` with 12 modules, builder and pace-based forecast), marking payments as received in the dashboard (portal bookings too), notifications with quiet hours, apartment codes, option "load data since", dates with year
- **Booking timing:** view "Booked in → for" is now the default, "Months before" via the switch

## 1.17.0b6 – 2026-11-16

> Beta / Pre-release

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

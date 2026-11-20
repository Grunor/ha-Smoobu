# Sicherheitsrichtlinie / Security policy

## Unterstützte Versionen / Supported versions

Sicherheitskorrekturen gibt es für die jeweils neueste stabile Version und die aktuelle Beta.
Security fixes are provided for the latest stable release and the current beta.

| Version | Unterstützt / Supported |
|---|---|
| neueste stabile / latest stable (z. B. 1.18.x) | ✅ |
| aktuelle Beta / current beta | ✅ |
| ältere / older | ❌ |

## Lücke melden / Reporting a vulnerability

Bitte **kein öffentliches Issue** anlegen. Melde die Lücke privat über GitHub:
**Security → Report a vulnerability** ([direkt](https://github.com/Grunor/ha-Smoobu/security/advisories/new)).

Please **do not open a public issue**. Report it privately via GitHub:
**Security → Report a vulnerability** ([direct link](https://github.com/Grunor/ha-Smoobu/security/advisories/new)).

Hilfreich sind / Helpful details:
- betroffene Version und Bereich (z. B. Webhook, WebSocket-Befehle, Rechteprüfung, KI-Assistent) / affected version and area
- Schritte zum Nachstellen / steps to reproduce
- mögliche Auswirkung / possible impact

Du bekommst eine Rückmeldung in der Regel innerhalb von 7 Tagen. Nach der Korrektur wird die Lücke im Changelog und als Security Advisory veröffentlicht; auf Wunsch mit Nennung.
You will usually get a reply within 7 days. After the fix, the issue is published in the changelog and as a security advisory, with credit if you wish.

## Was besonders schützenswert ist / What is especially sensitive

Die Integration verarbeitet Gästedaten (Namen, Kontakt, Nachrichten) und einen Smoobu-API-Schlüssel mit Schreibrechten (Buchungen, Preise, Nachrichten). Relevant sind daher vor allem:
The integration handles guest data (names, contact details, messages) and a Smoobu API key with write access (bookings, prices, messages). Most relevant are therefore:

- Umgehung der Benutzerrollen bei Karten, WebSocket-Befehlen oder `smoobu.*`-Aktionen / bypassing user roles for cards, WebSocket commands or `smoobu.*` actions
- Annahme gefälschter Webhook-Aufrufe / accepting forged webhook calls
- Gästedaten oder Schlüssel in Logs, Diagnose oder an KI-Anbieter trotz gesperrter KI / guest data or keys leaking to logs, diagnostics or AI providers while AI is locked
- Einschleusen von Code über Texte aus Smoobu (z. B. Gastnachrichten) in die Karten / script injection through Smoobu texts (e.g. guest messages) into the cards

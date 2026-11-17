"""Datenschutz für KI-Anfragen (ab v1.18.0b6, Wunsch Betreiber 17.11.2026).

Was dieses Modul leistet
------------------------
Alles, was an die KI geht, läuft durch diesen Filter (siehe assistant.build_prompt,
_history, _examples_text, build_knowledge). Gesteuert über die Option „Datenschutz-Stufe“:

- standard   (Voreinstellung, auch für bestehende Installationen)
             Gastnamen → Platzhalter, nach der Antwort lokal zurückgesetzt; erweiterte
             Schwärzung (Adresse, Kennzeichen, Geburtsdatum, Ausweisnummer); Daten relativ.
             Praktisch ohne Einbuße.
- streng     wie standard, zusätzlich Verlauf nur 2 Nachrichten, ohne Bezahlstatus/Kanal
- maximal    nur Gästenachricht (pseudonymisiert) + Wissensdatenbank; keine Buchungsdaten,
             kein Verlauf, keine Beispiele, keine Status-Entitäten
- individuell  jeder Schalter einzeln (Optionen ai_*)

Grenzen (bewusst dokumentiert, siehe README „Datenschutz“)
----------------------------------------------------------
- Ersetzt werden nur BEKANNTE Namen (aus den Smoobu-Buchungen). Andere Namen im Freitext
  (Begleitpersonen, Kinder) und alles, was keinem Muster folgt, bleiben stehen.
- Die erweiterte Schwärzung arbeitet mit Mustern → Best-Effort, kein Garant.
- Pseudonymisierte Daten gelten nach DSGVO weiter als personenbezogen.

Warum Platzhalter statt Weglassen: Die KI schreibt „Hallo [GAST_VORNAME]“, die Integration
setzt den Namen vor dem Speichern des Vorschlags wieder ein → Anrede bleibt persönlich.
Eigene Namen der Gastgeber (Option „Eigene Namen“, Standard aus dem Kontonamen) werden nie
ersetzt (Entscheidung Betreiber) – sonst würde z. B. die Signatur „Anna“ bei einem Gast namens
Anna zum Platzhalter und in der Antwort durch den Namen des aktuellen Gastes ersetzt.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

# ---------------------------------------------------------------------------
# Optionen
# ---------------------------------------------------------------------------
CONF_AI_PRIVACY = "ai_privacy"
DEFAULT_AI_PRIVACY = "standard"
PRIVACY_LEVELS = ["standard", "streng", "maximal", "individuell"]
CONF_AI_HOST_NAMES = "ai_host_names"  # Namen der Gastgeber, werden nie ersetzt

# Einzelschalter (wirken nur bei Stufe „individuell“; sonst gilt die Voreinstellung der Stufe)
CONF_AI_PSEUDONYM = "ai_pseudonym"          # Gastnamen durch Platzhalter ersetzen
CONF_AI_REDACT_EXT = "ai_redact_extended"   # Adresse, Kennzeichen, Geburtsdatum, Ausweis schwärzen
CONF_AI_DATES_RELATIVE = "ai_dates_relative"  # „Fr., in 3 Tagen“ statt Kalenderdatum
CONF_AI_SEND_DATES = "ai_send_dates"        # Anreise/Abreise, Uhrzeiten, Belegung davor/danach
CONF_AI_SEND_GUESTS = "ai_send_guests"      # Erwachsene, Kinder, Hund
CONF_AI_SEND_PAYMENT = "ai_send_payment"    # Kanal, Buchungsstatus, bezahlt
CONF_AI_HISTORY = "ai_history"              # Anzahl Nachrichten aus dem Verlauf (0–6)
CONF_AI_EXAMPLES = "ai_examples"            # frühere Antworten als Stilvorlage
CONF_AI_STATUS = "ai_status"                # Status-Entitäten (Heizung, Tür …)

FLAGS = [
    CONF_AI_PSEUDONYM, CONF_AI_REDACT_EXT, CONF_AI_DATES_RELATIVE, CONF_AI_SEND_DATES,
    CONF_AI_SEND_GUESTS, CONF_AI_SEND_PAYMENT, CONF_AI_HISTORY, CONF_AI_EXAMPLES, CONF_AI_STATUS,
]
MAX_HISTORY = 6  # wie bisher fest im Code

_STANDARD = {
    CONF_AI_PSEUDONYM: True, CONF_AI_REDACT_EXT: True, CONF_AI_DATES_RELATIVE: True,
    CONF_AI_SEND_DATES: True, CONF_AI_SEND_GUESTS: True, CONF_AI_SEND_PAYMENT: True,
    CONF_AI_HISTORY: MAX_HISTORY, CONF_AI_EXAMPLES: True, CONF_AI_STATUS: True,
}
PRESETS: dict[str, dict[str, Any]] = {
    "standard": _STANDARD,
    "streng": {**_STANDARD, CONF_AI_HISTORY: 2, CONF_AI_SEND_PAYMENT: False},
    "maximal": {
        **_STANDARD, CONF_AI_SEND_DATES: False, CONF_AI_SEND_GUESTS: False, CONF_AI_SEND_PAYMENT: False,
        CONF_AI_HISTORY: 0, CONF_AI_EXAMPLES: False, CONF_AI_STATUS: False,
    },
}


def level(options: dict[str, Any]) -> str:
    """Gewählte Stufe; fehlt sie (Installation vor dieser Version) → „standard“ (Entscheidung Betreiber)."""
    value = str(options.get(CONF_AI_PRIVACY) or DEFAULT_AI_PRIVACY)
    return value if value in PRIVACY_LEVELS else DEFAULT_AI_PRIVACY


def resolve(options: dict[str, Any]) -> dict[str, Any]:
    """Wirksame Schalter: Stufe → Voreinstellung; „individuell“ → gespeicherte Einzelwerte."""
    lvl = level(options)
    if lvl != "individuell":
        return dict(PRESETS[lvl])
    out = {}
    for key, default in _STANDARD.items():
        raw = options.get(key, default)
        out[key] = max(0, min(MAX_HISTORY, int(raw))) if key == CONF_AI_HISTORY else bool(raw)
    return out


def host_names(options: dict[str, Any], title: str | None) -> list[str]:
    """Eigene Namen: Option, sonst Wörter des Kontonamens (z. B. „Anna & Ben Beispiel“)."""
    names = options.get(CONF_AI_HOST_NAMES)
    if names is None:
        names = re.findall(r"[^\W\d_]{2,}", title or "")
    return [str(n).strip() for n in names if str(n).strip()]


# ---------------------------------------------------------------------------
# Erweiterte Schwärzung (Best-Effort, zusätzlich zu assistant.redact)
# ---------------------------------------------------------------------------
_STREET = r"(?:straße|strasse|str\.|weg|gasse|platz|allee|ring|damm|ufer|steig|chaussee)"
_REDACT_EXT = [
    # Straße + Hausnummer (deutsch: „Hauptstraße 12a“, „Am Hang Weg 3“), englisch „12 Baker Street“
    # Ausgenommen sind häufige Wörter ohne Adressbezug („Parkplatz 2“, „Rundweg 3 km“), sonst
    # würden auch eure eigenen Antworten in den Beispielen unnötig geschwärzt.
    (re.compile(rf"\b(?!(?:park|stell|spiel|sport|camping|wander|rad|fuß|fuss|geh|rund|spazier|feld)\w*{_STREET})"
                rf"[A-ZÄÖÜ][\wäöüß.-]*{_STREET}[ \t]*\d{{1,4}}[ \t]?[a-zA-Z]?\b", re.IGNORECASE), "[ADRESSE]"),
    (re.compile(r"\b\d{1,5}[ \t]+[A-Z][a-z]+(?:[ \t][A-Z][a-z]+)?[ \t]+(?:Street|St\.|Road|Rd\.|Avenue|Ave\.|Lane|Drive)\b"), "[ADRESSE]"),
    # PLZ + Ort (5 Ziffern + großgeschriebenes Wort)
    (re.compile(r"\b\d{5}[ \t]+[A-ZÄÖÜ][a-zäöüß]{2,}(?:[ \t-][A-ZÄÖÜ][a-zäöüß]+)?\b"), "[PLZ ORT]"),
    # Geburtsdatum mit Stichwort, danach jedes Datum mit Jahr 19xx (typisch Geburtsdaten)
    (re.compile(r"(?i)\b(geb(?:oren|urtsdatum|\.)|date of birth|dob|born|geburtstag|birthday)([^\d\n]{0,20})"
                r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"), r"\1\2[GEBURTSDATUM]"),
    (re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]19\d{2}\b"), "[DATUM]"),
    # Ausweis-/Passnummer mit Stichwort
    (re.compile(r"(?i)\b(ausweis\w*|personalausweis\w*|reisepass\w*|pass(?:nummer|nr\.?)?|passport(?: no\.?| number)?|id card)"
                r"([^\w\n]{0,15}(?:nr\.?|nummer|no\.?|number)?[^\w\n]{0,5})[A-Z0-9]{6,12}\b"), r"\1\2[AUSWEIS]"),
    # Kfz-Kennzeichen (deutsch: „AN-RG 123“, „M AB 1234E“) – nur mit Großbuchstaben, daher selten falsch
    (re.compile(r"\b[A-ZÄÖÜ]{1,3}[- ][A-Z]{1,2}[- ]?\d{1,4}[EH]?\b"), "[KENNZEICHEN]"),
]


def redact_extended(text: str) -> str:
    for pattern, repl in _REDACT_EXT:
        text = pattern.sub(repl, text or "")
    return text


# ---------------------------------------------------------------------------
# Pseudonymisierung bekannter Gastnamen
# ---------------------------------------------------------------------------
PH_NAME, PH_FIRST, PH_LAST = "[GAST_NAME]", "[GAST_VORNAME]", "[GAST_NACHNAME]"
PH_ARRIVAL, PH_DEPARTURE = "[ANREISE]", "[ABREISE]"
# Namensteile, die nie ersetzt werden (Anreden, Partikel, Kürzel)
_SKIP = {"von", "van", "der", "den", "de", "du", "la", "le", "di", "da", "zu", "und", "and", "mr", "mrs", "ms",
         "herr", "frau", "familie", "family", "dr", "prof"}


def _parts(name: str | None) -> list[str]:
    return [p for p in re.split(r"[\s,]+", name or "") if len(p) >= 2 and p.casefold().strip(".") not in _SKIP]


def name_parts(rec: dict[str, Any]) -> tuple[str, str, str]:
    """(voller Name, Vorname, Nachname) einer Buchung; Nachname notfalls = Name ohne Vorname."""
    full = (rec.get("gast") or "").strip()
    first = (rec.get("vorname") or "").strip()
    last = (rec.get("nachname") or "").strip()
    if not last and full and first and full.casefold().startswith(first.casefold()):
        last = full[len(first):].strip()
    return full, first, last


class Pseudonymizer:
    """Ersetzt die Namen bestimmter Buchungen durch Platzhalter (eigene Namen bleiben stehen)."""

    def __init__(self, keep: list[str] | None = None) -> None:
        self.keep = {k.casefold() for k in (keep or [])}

    def _rules(self, rec: dict[str, Any]) -> list[tuple[re.Pattern, str]]:
        full, first, last = name_parts(rec)
        rules: list[tuple[str, str]] = []
        # Längste Form zuerst: voller Name, dann Nachname/Vorname komplett, dann einzelne Teile
        if full and " " in full:
            rules.append((full, PH_NAME))
        if last:
            rules.append((last, PH_LAST))
        if first:
            rules.append((first, PH_FIRST))
        rules += [(p, PH_LAST) for p in _parts(last)] + [(p, PH_FIRST) for p in _parts(first)]
        if not first and not last:  # nur voller Name bekannt → erster Teil Vorname, Rest Nachname
            parts = _parts(full)
            rules += [(p, PH_FIRST if i == 0 else PH_LAST) for i, p in enumerate(parts)]
        out, seen = [], set()
        for text, ph in rules:
            key = text.casefold()
            if len(text) < 2 or key in seen or key in self.keep or key.strip(".") in _SKIP:
                continue
            seen.add(key)
            # Leerraum im Namen flexibel, Wortgrenzen unicode-fähig (Umlaute, Akzente)
            body = r"\s+".join(re.escape(w) for w in text.split())
            out.append((re.compile(rf"(?<!\w){body}(?!\w)", re.IGNORECASE), ph))
        return out

    def apply(self, text: str, *recs: dict[str, Any] | None) -> str:
        for rec in recs:
            if rec:
                for pattern, ph in self._rules(rec):
                    text = pattern.sub(ph, text or "")
        return text or ""


def restore(text: str, rec: dict[str, Any] | None, generic: bool = False) -> str:
    """Platzhalter in der KI-Antwort lokal durch die echten Werte ersetzen.

    generic=True: neutral ersetzen („Gast“) – für Texte, die in die Wissensdatenbank wandern.
    """
    if not text:
        return text
    rec = rec or {}
    full, first, last = name_parts(rec)
    if generic:
        values = {PH_NAME: "Gast", PH_FIRST: "Gast", PH_LAST: "Gast", PH_ARRIVAL: "Anreisetag", PH_DEPARTURE: "Abreisetag"}
    else:
        values = {
            PH_NAME: full or first or "Gast",
            PH_FIRST: first or full or "Gast",
            PH_LAST: last or full or "Gast",
            PH_ARRIVAL: _de_date(rec.get("anreise")) or "Anreisetag",
            PH_DEPARTURE: _de_date(rec.get("abreise")) or "Abreisetag",
        }
    for ph, value in values.items():
        text = text.replace(ph, value)
    return text


# ---------------------------------------------------------------------------
# Daten relativ
# ---------------------------------------------------------------------------
_DOW = ["Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa.", "So."]


def _as_date(value: Any) -> date | None:
    try:
        return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _de_date(value: Any) -> str | None:
    d = _as_date(value)
    return d.strftime("%d.%m.%Y") if d else None


def relative(value: Any, today: date) -> str:
    """„Fr., in 3 Tagen“ / „heute“ / „Mo., vor 2 Tagen“ – ohne Kalenderdatum."""
    d = _as_date(value)
    if d is None:
        return "unbekannt"
    diff = (d - today).days
    when = {0: "heute", 1: "morgen", -1: "gestern"}.get(
        diff, f"in {diff} Tagen" if diff > 0 else f"vor {-diff} Tagen"
    )
    return f"{_DOW[d.weekday()]}, {when}"

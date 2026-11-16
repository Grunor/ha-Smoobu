"""KI-Assistent für Gästenachrichten (ab v1.10.0).

Aufgaben
--------
1. Antwortvorschläge: Bei jeder neuen Gästenachricht (Webhook „newMessage“)
   erstellt der Assistent einen Entwurf und schickt ihn per Push mit den
   Buttons Senden / Bearbeiten / Ignorieren an die Gastgeber. Nichts geht ohne
   Bestätigung an Gäste.
2. Wissensdatenbank: Einträge (Thema + Text), in HA gespeichert (.storage),
   über die Dashboard-Karte gepflegt. Einträge mit „vertraulich“ gehen nicht
   an die KI (z. B. Tresor-Code).
3. Selbstlernend: Jede gesendete Gastgeber-Antwort wird mit der Gästenachricht
   davor als Beispiel gespeichert (auch Antworten direkt in Smoobu und
   geänderte Vorschläge). Bei neuen Nachrichten werden die ähnlichsten
   Beispiele (BM25-Textsuche, lokal) als Stilvorlage mitgegeben.
4. Zusatzaufgaben (immer mit Bestätigung per Push-Button):
   - späte Anreise erkannt → Ankunftszeit in Smoobu übernehmen
   - früher Check-in / später Check-out → Belegung davor/danach als Fakt im Prompt
   - dringende Probleme → sofortiger Push mit HA-Status
   - Lücken, die wegen Mindestaufenthalt nicht buchbar sind → Vorschlag + Button
   - Tagesbriefing am Morgen
   - Vorschläge für Willkommen/Anreise/Abreise/Bewertung auf Abruf

KI-Sperre (ab v1.14.0): Option „KI-Funktionen erlauben“. Aus = jeder KI-Aufruf
wird in `_ai()` abgelehnt (einzige Stelle, an der ai_task aufgerufen wird) –
egal ob über Karte, WebSocket, Aktion, Push-Button oder Webhook. Ohne KI weiter
verfügbar: Wissensdatenbank pflegen, Lernen aus gesendeten Antworten, Verlauf
importieren, Tagesbriefing, Lücken-Meldung, Nachrichten senden.

KI: HA-Aktion `ai_task.generate_data` mit strukturierter Antwort – der Anbieter
(Gemini, OpenAI …) wird in den Optionen gewählt; kein eigener API-Schlüssel.
Die Anweisung verbietet Erfindungen: Unbekanntes wird als [OFFEN: …]
markiert und als Wissenslücke gemeldet (validiert am 15.11.2026 mit Gemini).
"""

from __future__ import annotations

import asyncio
import html
import logging
import math
import re
import uuid
from collections import Counter
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .api import SmoobuError
from .const import (
    CONF_AI_ENTITY,
    CONF_ASSISTANT,
    CONF_ASSIST_BRIEFING_TIME,
    CONF_ASSIST_PATH,
    CONF_ASSIST_STATUS,
    CONF_NOTIFY_GAPS_TIME,
    DEFAULT_NOTIFY_GAPS_TIME,
    DOMAIN,
    ai_allowed,
)
from .models import free_gaps, strip_html
from .notifications import opt_enabled, opt_recipients

if TYPE_CHECKING:
    from .coordinator import SmoobuCoordinator

_LOGGER = logging.getLogger(__name__)

STORE_VERSION = 1
AI_TIMEOUT = 120  # Sekunden; Gemini braucht teils > 20 s
ACTION_PREFIX = "SMOOBU_"
MAX_EXAMPLES = 400
AI_LOCKED = "KI ist in den Integrationsoptionen deaktiviert (Smoobu → Konfigurieren → KI-Assistent)"
INTENTS = [
    "frage", "spaete_anreise", "frueher_checkin", "spaeter_checkout", "problem_dringend",
    "dank", "buchungsanfrage", "stornierung", "sonstiges",
]
OCCASIONS = {
    "antwort": "Antwort auf die letzte Gästenachricht",
    "willkommen": "Willkommensnachricht direkt nach der Buchung",
    "anreise": "Nachricht am Anreisetag (Zugang, Parken, Ankunft)",
    "abreise": "Nachricht am Abreisetag (Check-out, Dank)",
    "bewertung": "Bitte um eine Bewertung nach der Abreise",
}

_STOP = set(
    "der die das und oder ein eine einen einem einer ist sind war wir ihr ich du sie es zu im in am an auf "
    "mit für fur von bei auch noch nicht kein keine ja nein hallo hi liebe lieber grüße gruesse viele danke "
    "the a an and or is are was we you i to in on at for of with it this that hello hi thanks regards "
    "uns euch dich dir mir mich mein dein unser euer haben hat habe wird werden kann können koennen".split()
)


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-zäöüß0-9]+", (text or "").casefold())
    return [w for w in words if len(w) > 2 and w not in _STOP]


_QUOTE_RE = re.compile(
    r"(\n|^)\s*-{3,}\s*(Ursprüngliche Nachricht|Original Message|Original-Nachricht)"
    r"|Von meinem(/meiner)? [^\n]{0,40}gesendet|Sent from my|Gesendet von Outlook|Gesendet mit der"
    r"|(\n|^)\s*(Von|From):\s|(\n|^)\s*>"
    r"|(\n|^)[^\n]{0,80}(schrieb am|schrieb |wrote:|ha scritto:)"
    r"|(\n|^)\s*Reply to:\s|(\n|^)\s*Gesendet:\s",
    re.IGNORECASE,
)


def strip_quote(text: str) -> str:
    """Zitierten E-Mail-Verlauf, Signaturen und Mail-Köpfe abschneiden.

    Signaturen hängen oft ohne Zeilenumbruch am Text („…ThomasVon meinem/meiner Galaxy gesendet“).
    """
    text = text or ""
    m = _QUOTE_RE.search(text)
    return (text[: m.start()] if m and m.start() > 2 else text).strip()


# Schwärzen, bevor etwas gespeichert oder an die KI geschickt wird
_REDACT = [
    (re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,3})?\b"), "[IBAN]"),
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[E-MAIL]"),
    (re.compile(r"https?://\S*(?:[?&]t=|check-in/|request_id|hotel_id|token)\S*", re.IGNORECASE), "[LINK]"),
    (re.compile(r"(?<![\w.])(?:\+\d{2}[\d \t/-]{7,}\d|0\d{2,4}[ \t/-]?\d[\d \t/-]{4,}\d)"), "[TELEFON]"),
    (re.compile(r"(?i)\b((?:zahlen)?code|pin|key ?code)([^\d\n]{0,40}?)\d{3,6}\b"), r"\1\2[CODE]"),
]


def redact(text: str) -> str:
    """IBAN, E-Mail, Telefon, Zugangs-Codes und persönliche Links unkenntlich machen."""
    for pattern, repl in _REDACT:
        text = pattern.sub(repl, text or "")
    return text


def clean(text: str) -> str:
    """HTML/Entities entfernen, Zitate/Signaturen abschneiden, sensible Daten schwärzen."""
    text = html.unescape(strip_html(text or "")).replace("\xa0", " ")
    return redact(strip_quote(text)).strip()


def _norm_prefix(text: str) -> str:
    return re.sub(r"[^a-zäöüß]+", "", clean(text).casefold())[:60]


# Anrede-Zeile („Hallo Henrika,“) – wird für die Vorlagenerkennung übersprungen
_GREETING_RE = re.compile(
    r"^\s*(hallo|hi|hey|hello|dear|liebe[rs]?|guten (morgen|tag|abend)|good (morning|evening|afternoon)"
    r"|moin|servus|bonjour|buongiorno|ciao|hola|beste|merhaba)\b[^\n]{0,40}\n",
    re.IGNORECASE,
)

# Automatische Antworten der Portale (Booking-Anfragen u. ä.) – keine echten Antworten
PLATFORM_AUTO = {"request approved", "request declined", "confirm for free", "anfrage angenommen",
                 "anfrage abgelehnt"}


def body_key(text: str) -> str:
    """Schlüssel des Nachrichtenkerns ohne Anrede – gleiche Vorlage trotz anderem Gastnamen."""
    t = clean(text)
    t = _GREETING_RE.sub("", t, count=1)
    # Anrede ohne Zeilenumbruch („Hallo Saskia,falls du …“)
    t = re.sub(r"^\s*(hallo|hi|hello|dear|bonjour)\s+[^,\n]{1,30},", "", t, flags=re.IGNORECASE)
    return re.sub(r"[^a-zäöüß]+", "", t.casefold())[:80]


def norm_subject(subj: str) -> str:
    """Betreff ohne Nummern/Daten („Rechnung RE2026-045 …“ → „Rechnung RE# …“)."""
    return re.sub(r"[\d][\d.\-/:]*", "#", (subj or "").strip())


def rank(query: str, docs: list[str], k: int = 4) -> list[int]:
    """BM25-Ranking: Indizes der k ähnlichsten Texte (lokal, ohne KI)."""
    q = _tokens(query)
    if not q or not docs:
        return []
    toks = [_tokens(d) for d in docs]
    n = len(toks)
    avg = sum(len(t) for t in toks) / n or 1
    df = Counter(w for t in toks for w in set(t))
    scores = []
    for i, t in enumerate(toks):
        tf = Counter(t)
        s = 0.0
        for w in q:
            if w not in tf:
                continue
            idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
            s += idf * tf[w] * 2.2 / (tf[w] + 1.2 * (0.25 + 0.75 * len(t) / avg))
        scores.append((s, i))
    return [i for s, i in sorted(scores, reverse=True)[:k] if s > 0]


class SmoobuAssistant:
    """Assistent je Smoobu-Konto (hängt am Coordinator)."""

    def __init__(self, hass: HomeAssistant, coordinator: SmoobuCoordinator) -> None:
        self.hass = hass
        self.c = coordinator
        entry = coordinator.config_entry
        self.store: Store = Store(hass, STORE_VERSION, f"{DOMAIN}_assistant_{entry.entry_id}")
        self.data: dict[str, Any] = {"wissen": [], "beispiele": [], "vorschlaege": {}, "import": None}
        self.last_error: str | None = None
        self.busy: set[int] = set()
        self.throttle = 0.2  # Pause zwischen Abfragen beim Import (s)
        self._unsubs: list = []
        self._listeners: list = []

    # --- Optionen ------------------------------------------------------
    @property
    def opts(self) -> dict[str, Any]:
        return dict(self.c.config_entry.options)

    @property
    def ai_allowed(self) -> bool:
        """KI-Hauptschalter (ab v1.14.0): False = KI explizit gesperrt."""
        return ai_allowed(self.opts)

    @property
    def enabled(self) -> bool:
        """Automatische Vorschläge bei neuen Gästenachrichten – nur mit erlaubter KI."""
        # v1.17.0: nie gespeichert → an (sobald die KI erlaubt ist); bewusst ausgeschaltet bleibt aus
        return self.ai_allowed and bool(self.opts.get(CONF_ASSISTANT, True))

    def _require_ai(self) -> None:
        """Vor jeder KI-Funktion: gesperrt → verständlicher Fehler statt stillem Nichtstun."""
        if not self.opts.get(CONF_AI_ENTITY):
            raise SmoobuError("Keine KI ausgewählt (Optionen → KI-Assistent)")
        if not self.ai_allowed:
            raise SmoobuError(AI_LOCKED)

    # --- Lebenszyklus ----------------------------------------------------
    async def async_setup(self) -> None:
        stored = await self.store.async_load()
        if stored:
            self.data.update(stored)
        self._unsubs.append(
            self.hass.bus.async_listen("mobile_app_notification_action", self._on_push_action)
        )
        # v1.17.0: an/aus und Uhrzeiten aus dem Optionsschritt „Benachrichtigungen“
        # (ohne neue Optionen gelten Tagesbriefing/Lücken wie bisher)
        if opt_enabled(self.opts, "briefing"):
            hh, mm = (self.opts.get(CONF_ASSIST_BRIEFING_TIME) or "07:30")[:5].split(":")
            self._unsubs.append(
                async_track_time_change(self.hass, self._briefing, hour=int(hh), minute=int(mm), second=0)
            )
        if opt_enabled(self.opts, "luecken"):
            hh, mm = (self.opts.get(CONF_NOTIFY_GAPS_TIME) or DEFAULT_NOTIFY_GAPS_TIME)[:5].split(":")
            self._unsubs.append(
                async_track_time_change(self.hass, self._gap_check, hour=int(hh), minute=int(mm), second=0)
            )

    async def async_unload(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()
        await self.store.async_save(self.data)

    def add_listener(self, cb) -> callable:
        self._listeners.append(cb)
        return lambda: self._listeners.remove(cb)

    @callback
    def _changed(self) -> None:
        self.store.async_delay_save(lambda: self.data, 5)
        for cb in list(self._listeners):
            cb()

    # --- Wissensdatenbank -------------------------------------------------
    def save_knowledge(self, item: dict[str, Any]) -> dict[str, Any]:
        items = self.data["wissen"]
        now = dt_util.now().isoformat()
        if item.get("id"):
            for i, old in enumerate(items):
                if old["id"] == item["id"]:
                    items[i] = {**old, **item, "geaendert": now}
                    self._changed()
                    return items[i]
        new = {
            "id": uuid.uuid4().hex[:10],
            "thema": item.get("thema", "").strip(),
            "text": item.get("text", "").strip(),
            "status": item.get("status", "aktiv"),  # aktiv | vorschlag | aus
            "vertraulich": bool(item.get("vertraulich")),
            "quelle": item.get("quelle", "manuell"),
            "geaendert": now,
        }
        items.append(new)
        self._changed()
        return new

    def delete_knowledge(self, item_id: str) -> None:
        self.data["wissen"] = [w for w in self.data["wissen"] if w["id"] != item_id]
        self._changed()

    async def delete_suggestion(self, rid: int) -> None:
        """v1.17.0: Vorschlag ganz entfernen (z. B. Testvorschlag) inkl. Push."""
        if self.data["vorschlaege"].pop(str(rid), None) is not None:
            self._changed()
        await self._clear_push(rid)

    def delete_example(self, ex_id: str) -> None:
        self.data["beispiele"] = [b for b in self.data["beispiele"] if b["id"] != ex_id]
        self._changed()

    def learn(self, rid: int, guest: str | None, answer: str, source: str, key: str | None = None) -> None:
        """Gästenachricht + Gastgeber-Antwort als Beispiel speichern (doppelte Schlüssel ignoriert)."""
        answer = clean(answer)
        guest = clean(guest or "")
        # Airbnb-Reaktionen und „keine Antwort nötig“ sind keine Lernbeispiele
        if len(answer) < 3 or answer.startswith("You reacted") or guest.startswith("Marked as no reply"):
            return
        key = key or f"{rid}:{hash(answer)}"
        if any(b.get("key") == key for b in self.data["beispiele"]):
            return
        rec = next((r for r in self.c.records_all() if r["id"] == rid), {})
        self.data["beispiele"].append(
            {
                "id": uuid.uuid4().hex[:10],
                "key": key,
                "buchung_id": rid,
                "gast": guest[:1500],
                "antwort": answer[:2500],
                "sprache": rec.get("sprache"),
                "kanal": rec.get("kanal"),
                "quelle": source,  # verlauf | smoobu | gesendet | vorschlag | bearbeitet
                "zeit": dt_util.now().isoformat(),
            }
        )
        self.data["beispiele"] = self.data["beispiele"][-MAX_EXAMPLES:]
        self._changed()

    # --- Kontext -------------------------------------------------------
    def _status_lines(self) -> list[str]:
        lines = []
        for eid in self.opts.get(CONF_ASSIST_STATUS) or []:
            st = self.hass.states.get(eid)
            if st is None:
                continue
            name = st.attributes.get("friendly_name") or eid
            extra = ""
            if eid.startswith("climate."):
                extra = (
                    f" (Ist {st.attributes.get('current_temperature')} °C, "
                    f"Soll {st.attributes.get('temperature')} °C)"
                )
            unit = st.attributes.get("unit_of_measurement") or ""
            lines.append(f"- {name}: {st.state}{(' ' + unit) if unit else ''}{extra}")
        return lines

    def _neighbours(self, rec: dict[str, Any]) -> list[str]:
        """Fakten für früheren Check-in / späteren Check-out."""
        out = []
        guests = [r for r in self.c.records_all() if not r["storniert"] and r["id"] != rec["id"]]
        prev = [r for r in guests if r["abreise"] == rec["anreise"]]
        nxt = [r for r in guests if r["anreise"] == rec["abreise"]]
        out.append(
            f"- Am Anreisetag ({rec['anreise']}) reist vorher "
            + ("ein anderer Gast/Sperre ab → früher Check-in nur nach Reinigung, eher nicht zusagen."
               if prev else "niemand ab → früher Check-in grundsätzlich möglich (Gastgeber entscheidet).")
        )
        out.append(
            f"- Am Abreisetag ({rec['abreise']}) reist danach "
            + ("ein neuer Gast an → späterer Check-out nicht möglich."
               if nxt else "niemand an → späterer Check-out grundsätzlich möglich (Gastgeber entscheidet).")
        )
        return out

    def _knowledge_text(self, query: str) -> str:
        items = [w for w in self.data["wissen"] if w["status"] == "aktiv"]
        lines = []
        for w in items:
            if w.get("vertraulich"):
                lines.append(f"- {w['thema']}: [VERTRAULICH – Gastgeber ergänzt selbst]")
            else:
                lines.append(f"- {w['thema']}: {w['text']}")
        # Bei sehr großer Datenbank nur die passendsten 40 Einträge
        if len(lines) > 40:
            idx = rank(query, [f"{w['thema']} {w['text']}" for w in items], 40)
            lines = [lines[i] for i in idx]
        return "\n".join(lines) or "- (noch keine Einträge)"

    def _examples_text(self, query: str, k: int = 4) -> str:
        ex = [b for b in self.data["beispiele"] if b.get("gast")]
        idx = rank(query, [b["gast"] for b in ex], k)
        if not idx:
            # Ohne Treffer: die neuesten selbst geschriebenen Antworten als Stilprobe
            idx = list(range(max(len(ex) - 2, 0), len(ex)))
        parts = []
        for i in idx:
            b = ex[i]
            parts.append(f"Gast: {b['gast'][:500]}\nGastgeber: {b['antwort'][:700]}")
        return "\n---\n".join(parts) or "(noch keine Beispiele)"

    def _booking_text(self, rec: dict[str, Any]) -> str:
        return (
            f"Gast {rec.get('gast')} (Vorname {rec.get('vorname')}), Kanal {rec.get('kanal')}, "
            f"Sprache {rec.get('sprache') or 'unbekannt'}, Anreise {rec['anreise']} "
            f"(Check-in-Zeit laut Smoobu {rec.get('check_in') or 'nicht angegeben'}), Abreise {rec['abreise']} "
            f"(Check-out-Zeit {rec.get('check_out') or 'nicht angegeben'}), {rec['naechte']} Nächte, "
            f"{rec['erwachsene']} Erwachsene, {rec['kinder']} Kinder, Hund: {'ja' if rec.get('hund') else 'nein'}, "
            f"Status {rec['status']}, bezahlt: {'ja' if rec.get('bezahlt') else 'nein'}"
        )

    def build_prompt(self, rec: dict[str, Any], guest_text: str, occasion: str, history: str) -> str:
        today = dt_util.now()
        return f"""ROLLE: Du schreibst Nachrichtenentwürfe für die Gastgeber einer Ferienwohnung. Die Gastgeber prüfen jeden Entwurf vor dem Senden.
AUFGABE: {OCCASIONS.get(occasion, OCCASIONS['antwort'])}.
REGELN (strikt):
1. Verwende NUR Fakten aus WISSEN, BUCHUNG, BELEGUNG und STATUS. Erfinde nichts: keine Orte, Ausstattung, Preise, Zusagen, Codes, Uhrzeiten.
2. Ist etwas nicht beantwortbar, schreibe an dieser Stelle [OFFEN: kurze Frage an die Gastgeber] und trage die Frage in 'wissensluecke' ein.
3. Früherer Check-in / späterer Check-out: nur zusagen, wenn BELEGUNG es erlaubt UND das WISSEN es grundsätzlich erlaubt; sonst [OFFEN: …].
4. Einträge mit [VERTRAULICH …] nie ausschreiben; schreibe dort [OFFEN: vertrauliche Angabe ergänzen].
5. Schreibe in der Sprache der Gästenachricht (sonst Buchungssprache), Anrede wie in den BEISPIELEN, herzlich und kurz, Gruß wie in den BEISPIELEN.
6. Orientiere dich im Ton an den BEISPIELEN, kopiere aber keine Fakten daraus, die nicht zu dieser Buchung passen (z. B. Namen, Daten).
7. Bei Problemen in der Wohnung (Heizung, Wasser, Strom, Schlüssel, Sicherheit) setze dringend = true und gib den Gastgebern im 'hinweis' konkret an, was laut STATUS los sein könnte.
HEUTE: {today.strftime('%A, %d.%m.%Y %H:%M')}
WISSEN:
{self._knowledge_text(guest_text or occasion)}
BUCHUNG: {self._booking_text(rec)}
BELEGUNG:
{chr(10).join(self._neighbours(rec))}
STATUS (Home Assistant):
{chr(10).join(self._status_lines()) or '- (keine Angaben)'}
BEISPIELE früherer Antworten der Gastgeber:
{self._examples_text(guest_text or occasion)}
BISHERIGER VERLAUF (älteste zuerst, gekürzt):
{history or '(keiner)'}
GÄSTENACHRICHT: {redact(guest_text) if guest_text else '(keine – Nachricht aus Anlass oben schreiben)'}
"""

    STRUCTURE = {
        "antwort": {"description": "Nachrichtenentwurf an den Gast", "required": True,
                    "selector": {"text": {"multiline": True}}},
        "absicht": {"description": "eine von: " + ", ".join(INTENTS), "required": True, "selector": {"text": None}},
        "sprache": {"description": "Sprachcode der Antwort, z. B. de, en", "required": False, "selector": {"text": None}},
        "ankunftszeit": {"description": "vom Gast genannte neue Ankunftszeit HH:MM, sonst leer",
                         "required": False, "selector": {"text": None}},
        "abreisezeit": {"description": "vom Gast genannte Abreisezeit HH:MM, sonst leer",
                        "required": False, "selector": {"text": None}},
        "dringend": {"description": "true nur bei Problemen in der Wohnung", "required": True,
                     "selector": {"boolean": None}},
        "hinweis": {"description": "kurzer interner Hinweis an die Gastgeber (Deutsch), sonst leer",
                    "required": False, "selector": {"text": None}},
        "wissensluecke": {"description": "Fragen, die WISSEN nicht beantwortet, sonst leer",
                          "required": False, "selector": {"text": None}},
        "zusammenfassung": {"description": "Gästenachricht in einem kurzen deutschen Satz",
                            "required": False, "selector": {"text": None}},
    }

    async def _ai(self, instructions: str, structure: dict[str, Any], task: str) -> dict[str, Any]:
        # Zentrale Sperre: einzige Stelle mit ai_task-Aufruf → hier greift die Option immer
        self._require_ai()
        entity = self.opts.get(CONF_AI_ENTITY)
        try:
            async with asyncio.timeout(AI_TIMEOUT):
                resp = await self.hass.services.async_call(
                    "ai_task",
                    "generate_data",
                    {"entity_id": entity, "task_name": task, "instructions": instructions, "structure": structure},
                    blocking=True,
                    return_response=True,
                )
        except TimeoutError as err:
            raise SmoobuError(f"KI hat nicht innerhalb von {AI_TIMEOUT} s geantwortet") from err
        except Exception as err:  # noqa: BLE001 – Anbieterfehler (Guthaben, Modell) sichtbar machen
            raise SmoobuError(f"KI-Fehler ({entity}): {err}") from err
        data = (resp or {}).get("data")
        if not isinstance(data, dict):
            raise SmoobuError(f"KI lieferte keine strukturierte Antwort: {resp}")
        return data

    # --- Vorschlag ------------------------------------------------------------
    async def _messages(self, rid: int) -> list[dict[str, Any]]:
        msgs = await self.c.client.get_messages(rid, False)
        return sorted(msgs, key=lambda m: int(m.get("id") or 0))

    @staticmethod
    def _text(m: dict[str, Any]) -> str:
        return strip_html(m.get("message") or m.get("messageHtml") or m.get("htmlMessage") or "")

    def _history(self, msgs: list[dict[str, Any]], limit: int = 6) -> str:
        lines = []
        for m in msgs[-limit:]:
            who = "Gast" if int(m.get("type") or 0) == 1 else "Gastgeber"
            lines.append(f"{who}: {clean(self._text(m))[:600]}")
        return "\n".join(lines)

    async def suggest(
        self,
        rid: int,
        occasion: str = "antwort",
        guest_text: str | None = None,
        notify: bool = False,
        msgs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Vorschlag erzeugen, speichern und optional per Push melden."""
        self._require_ai()  # früh abbrechen: kein Nachrichtenabruf, wenn KI gesperrt
        rec = next((r for r in self.c.records_all() if r["id"] == rid), None)
        if rec is None:
            raise SmoobuError(f"Buchung {rid} nicht gefunden")
        if rid in self.busy:
            raise SmoobuError("Für diese Buchung läuft gerade schon ein Vorschlag")
        self.busy.add(rid)
        try:
            if msgs is None:  # beim Webhook bereits geladen → nicht doppelt abfragen
                msgs = []
                try:
                    msgs = await self._messages(rid)
                except SmoobuError as err:
                    _LOGGER.debug("Verlauf %s nicht ladbar: %s", rid, err)
            last_guest = next((m for m in reversed(msgs) if int(m.get("type") or 0) == 1), None)
            if guest_text is None and occasion == "antwort" and last_guest:
                guest_text = strip_quote(self._text(last_guest))
            prompt = self.build_prompt(rec, guest_text or "", occasion, self._history(msgs))
            result = await self._ai(prompt, self.STRUCTURE, f"smoobu_{occasion}")
            self.last_error = None
        except SmoobuError as err:
            self.last_error = str(err)
            self._changed()
            raise
        finally:
            self.busy.discard(rid)
        sid = uuid.uuid4().hex[:8]
        sug = {
            "id": sid,
            "buchung_id": rid,
            "gast": rec.get("gast"),
            "anlass": occasion,
            "gastnachricht": guest_text,
            "nachricht_id": last_guest.get("id") if last_guest and occasion == "antwort" else None,
            "antwort": (result.get("antwort") or "").strip(),
            "absicht": (result.get("absicht") or "sonstiges").strip(),
            "sprache": result.get("sprache"),
            "ankunftszeit": _hhmm(result.get("ankunftszeit")),
            "abreisezeit": _hhmm(result.get("abreisezeit")),
            "dringend": bool(result.get("dringend")),
            "hinweis": (result.get("hinweis") or "").strip(),
            "wissensluecke": (result.get("wissensluecke") or "").strip(),
            "zusammenfassung": (result.get("zusammenfassung") or "").strip(),
            "offen": "[OFFEN" in (result.get("antwort") or ""),
            "status": "offen",
            "erstellt": dt_util.now().isoformat(),
        }
        self.data["vorschlaege"][str(rid)] = sug
        # Wissenslücke als Vorschlag für die Datenbank merken
        if sug["wissensluecke"] and not any(
            w["thema"] == sug["wissensluecke"][:80] for w in self.data["wissen"]
        ):
            self.save_knowledge(
                {"thema": sug["wissensluecke"][:80], "text": "", "status": "vorschlag", "quelle": "wissensluecke"}
            )
        self._changed()
        if notify:
            await self._push_suggestion(sug, rec)
        return sug

    # --- Vorlagen (automatische Smoobu-Nachrichten) ---------------------------
    def is_template(self, m: dict[str, Any]) -> bool:
        """Automatische Nachricht (Willkommen, Check-in-Info …) – keine Antwort auf den Gast."""
        subj = norm_subject(m.get("subject") or "")
        if subj and subj in set(self.data.get("vorlagen_betreff") or []):
            return True
        text = clean(self._text(m))
        if text.casefold().strip(" .!") in PLATFORM_AUTO:
            return True
        key = body_key(text)
        return len(key) >= 40 and key in set(self.data.get("vorlagen_anfang") or [])

    # --- Webhook: neue Nachricht -------------------------------------------
    async def on_new_message(self, rid: int) -> None:
        """Neue Nachricht: Gast → Vorschlag; Gastgeber → lernen + offenen Vorschlag erledigen."""
        try:
            msgs = await self._messages(rid)
        except SmoobuError as err:
            _LOGGER.debug("Nachrichten %s nicht ladbar: %s", rid, err)
            return
        if not msgs:
            return
        latest = msgs[-1]
        if int(latest.get("type") or 0) == 2:
            if self.is_template(latest):
                return  # automatische Nachricht: weder lernen noch Vorschlag erledigen
            prev_guest = next((m for m in reversed(msgs[:-1]) if int(m.get("type") or 0) == 1), None)
            self.learn(rid, self._text(prev_guest) if prev_guest else None, self._text(latest), "smoobu",
                       key=f"msg:{latest.get('id')}")
            sug = self.data["vorschlaege"].get(str(rid))
            if sug and sug["status"] == "offen":
                sug["status"] = "erledigt"
                self._changed()
            # v1.17.0: auch einen reinen Nachrichten-Push (ohne Vorschlag) entfernen – beantwortet
            await self._clear_push(rid)
            return
        # v1.17.0: Mit automatischem Vorschlag (KI erlaubt, Vorschlag-Push an) kommt der Vorschlag,
        # der die Gästenachricht enthält. Sonst – oder wenn der Vorschlag scheitert – der Nachrichten-Push.
        if self.enabled and opt_enabled(self.opts, "vorschlag"):
            try:
                await self.suggest(rid, "antwort", notify=True, msgs=msgs)
                return
            except SmoobuError as err:
                _LOGGER.warning("Smoobu-Assistent: Vorschlag für %s fehlgeschlagen: %s", rid, err)
        await self._push_message(rid, latest)

    # --- Senden / Push-Aktionen -------------------------------------------------
    async def send(self, rid: int, text: str, source: str = "gesendet") -> None:
        await self.c.client.send_message(rid, text)
        sug = self.data["vorschlaege"].get(str(rid))
        guest = sug.get("gastnachricht") if sug else None
        if sug and sug["status"] == "offen":
            same = _norm(text) == _norm(sug["antwort"])
            source = "vorschlag" if same else "bearbeitet"
            sug["status"] = "gesendet"
        self.learn(rid, guest, text, source)
        await self._clear_push(rid)
        self._changed()

    async def dismiss(self, rid: int) -> None:
        """„Keine Antwort erforderlich“: offenen Vorschlag verwerfen und Push entfernen (v1.14.0)."""
        sug = self.data["vorschlaege"].get(str(rid))
        if sug and sug["status"] == "offen":
            sug["status"] = "ignoriert"
            self._changed()
        await self._clear_push(rid)

    async def _on_push_action(self, event: Event) -> None:
        action = str(event.data.get("action") or "")
        if not action.startswith(ACTION_PREFIX):
            return
        parts = action.split("_")  # SMOOBU_<ART>_<rid>_<sid>
        if len(parts) < 4:
            return
        kind, rid, sid = parts[1], int(parts[2]), parts[3]
        if kind == "LUECKE":
            try:
                await self.apply_gap(sid)
                await self._notify("✅ Lücke angepasst", "Mindestaufenthalt/Preis in Smoobu gesetzt.", {"tag": "smoobu_luecke_ok"}, kind="luecken", always=True)
            except SmoobuError as err:
                await self._notify("⚠️ Smoobu-Assistent", f"Lücke nicht angepasst: {err}", {"tag": "smoobu_luecke_ok"}, kind="luecken", always=True)
            return
        sug = self.data["vorschlaege"].get(str(rid))
        if not sug or sug["id"] != sid:
            return
        try:
            if kind == "SENDEN":
                text = event.data.get("reply_text") or sug["antwort"]
                await self.send(rid, text)
                await self._notify("✅ Gesendet", f"Antwort an {sug['gast']} gesendet.", {"tag": f"smoobu_vorschlag_{rid}"}, always=True)
            elif kind == "IGNORIEREN":
                sug["status"] = "ignoriert"
                self._changed()
            elif kind == "ZEIT" and sug.get("ankunftszeit"):
                await self.c.client.update_reservation(rid, {"arrivalTime": sug["ankunftszeit"]})
                self.c.force_revenue_refresh = True
                await self.c.async_request_refresh()
                await self._notify("🕘 Ankunftszeit übernommen",
                                   f"{sug['gast']}: Ankunft {sug['ankunftszeit']} in Smoobu gespeichert.",
                                   {"tag": f"smoobu_zeit_{rid}"}, always=True)
        except SmoobuError as err:
            await self._notify("⚠️ Smoobu-Assistent", f"Aktion fehlgeschlagen: {err}", {"tag": f"smoobu_fehler_{rid}"}, always=True)

    async def _push_suggestion(self, sug: dict[str, Any], rec: dict[str, Any]) -> None:
        rid, sid = sug["buchung_id"], sug["id"]
        actions = []
        if not sug["offen"]:
            actions.append({"action": f"{ACTION_PREFIX}SENDEN_{rid}_{sid}", "title": "Senden"})
        actions.append({"action": "URI", "title": "Bearbeiten", "uri": self.opts.get(CONF_ASSIST_PATH) or "/lovelace"})
        if sug.get("ankunftszeit") and sug["ankunftszeit"] != (rec.get("check_in") or "")[:5]:
            actions.append({"action": f"{ACTION_PREFIX}ZEIT_{rid}_{sid}", "title": f"Ankunft {sug['ankunftszeit']} übernehmen"})
        else:
            actions.append({"action": f"{ACTION_PREFIX}IGNORIEREN_{rid}_{sid}", "title": "Ignorieren"})
        head = "🚨 DRINGEND – " if sug["dringend"] else "✉️ "
        body = f"„{(sug['gastnachricht'] or '')[:180]}“\n\n➜ {sug['antwort'][:600]}"
        if sug["hinweis"]:
            body += f"\n\nℹ️ {sug['hinweis'][:200]}"
        if sug["offen"]:
            body += "\n\n✏️ Enthält [OFFEN] – bitte im Dashboard ergänzen."
        data: dict[str, Any] = {"tag": f"smoobu_vorschlag_{rid}", "actions": actions,
                                "url": self.opts.get(CONF_ASSIST_PATH) or "/lovelace",
                                "clickAction": self.opts.get(CONF_ASSIST_PATH) or "/lovelace"}
        if sug["dringend"]:
            data["push"] = {"interruption-level": "time-sensitive"}
            data["ttl"] = 0
            data["priority"] = "high"
        await self._notify(f"{head}{rec.get('gast')} ({rec.get('kanal')})", body, data, kind="vorschlag", urgent=sug["dringend"])

    async def _push_message(self, rid: int, msg: dict[str, Any]) -> None:
        """v1.17.0: Neue Gästenachricht ohne KI-Vorschlag (Push-Art „nachricht“)."""
        rec = next((r for r in self.c.records_all() if r["id"] == rid), {}) or {}
        text = strip_quote(self._text(msg))[:400]
        prefix = ""
        if self.c.data and len(self.c.data.apartments) > 1:
            prefix = f"[{self.c.apartment_code(rec.get('wohnung_id'))}] "
        path = self.opts.get(CONF_ASSIST_PATH) or "/lovelace"
        await self._notify(f"💬 {prefix}{rec.get('gast') or 'Gast'}" + (f" ({rec['kanal']})" if rec.get("kanal") else ""),
                           f"„{text}“", {"tag": f"smoobu_vorschlag_{rid}", "url": path, "clickAction": path},
                           kind="nachricht")

    async def _clear_push(self, rid: int) -> None:
        # Vorschlag und Nachricht teilen sich die Kennung → beide Empfängerkreise aufräumen
        for kind in ("vorschlag", "nachricht"):
            await self._notify(None, "clear_notification", {"tag": f"smoobu_vorschlag_{rid}"}, kind=kind, always=True)

    async def _notify(self, title: str | None, message: str, data: dict[str, Any], *,
                      kind: str = "vorschlag", urgent: bool = False, always: bool = False) -> None:
        """Zustellung über die Benachrichtigungen (v1.17.0): Empfänger, an/aus und Ruhezeit je Art.

        always=True: Bestätigungen/Fehler auf eigene Aktionen – unabhängig von an/aus, sofort.
        """
        notifier = getattr(self.c, "notifier", None)
        if notifier is None:
            return
        await notifier.send(kind, title, message, data, urgent=urgent or always, check_enabled=not always)

    # --- Zusatzaufgaben ---------------------------------------------------------
    def briefing_text(self) -> str | None:
        today = dt_util.now().date().isoformat()
        recs = [r for r in self.c.records_all() if not r["storniert"] and not r["blockiert"]]
        arr = [r for r in recs if r["anreise"] == today]
        dep = [r for r in recs if r["abreise"] == today]
        open_s = [s for s in self.data["vorschlaege"].values() if s["status"] == "offen"]
        lines = []
        for r in dep:
            lines.append(f"🛫 Abreise: {r['gast']}" + (f" (Check-out {r['check_out']})" if r.get("check_out") else ""))
        for r in arr:
            lines.append(
                f"🛬 Anreise: {r['gast']}, {r['personen']} P., {r['naechte']} N."
                + (f", Ankunft {r['check_in']}" if r.get("check_in") else "")
                + (" 🐕" if r.get("hund") else "")
                + (f", offen {r['offen']:.2f} €" if r.get("offen") else "")
            )
        if arr and dep:
            lines.append("🔄 Gästewechsel – Reinigung zwischen Check-out und Check-in")
        if open_s:
            lines.append(f"✉️ {len(open_s)} unbeantwortete Nachricht(en): " + ", ".join(s["gast"] or "?" for s in open_s))
        return "\n".join(lines) or None

    async def _briefing(self, _now: datetime) -> None:
        text = self.briefing_text()
        if text:
            await self._notify("☀️ Haus heute", text, {"tag": "smoobu_briefing", "url": self.opts.get(CONF_ASSIST_PATH) or "/lovelace"},
                               kind="briefing")

    def gap_suggestions(self) -> list[dict[str, Any]]:
        """Lücken (≤ 30 Tage), die wegen Mindestaufenthalt nicht buchbar sind."""
        out = []
        today = dt_util.now().date()
        for apt in self.c.data.apartments if self.c.data else {}:
            rates = self.c.data.rates.get(apt, {})
            for g in free_gaps(self.c.bookings_for(apt), today, 30):
                min_stay = (rates.get(g["von"]) or {}).get("min_length_of_stay")
                price = (rates.get(g["von"]) or {}).get("price")
                if min_stay and min_stay > g["naechte"]:
                    days = (date.fromisoformat(g["von"]) - today).days
                    out.append({**g, "wohnung": apt, "mindestaufenthalt": min_stay, "preis": price,
                                "preis_vorschlag": round(price * 0.85) if price and days <= 7 else None})
        return out

    async def _gap_check(self, _now: datetime) -> None:
        for g in self.gap_suggestions():
            key = f"gap:{g['von']}:{g['bis']}"
            if key in self.data.setdefault("gemeldet", []):
                continue
            self.data["gemeldet"] = (self.data["gemeldet"] + [key])[-100:]
            msg = (f"{g['von']} – {g['bis']} ({g['naechte']} N.) ist frei, aber Mindestaufenthalt {g['mindestaufenthalt']} N. "
                   f"→ nicht buchbar.")
            if g["preis_vorschlag"]:
                msg += f" Last-Minute: Preis {g['preis']} → {g['preis_vorschlag']} €?"
            gid = uuid.uuid4().hex[:8]
            self.data.setdefault("luecken", {})[gid] = g
            await self._notify("📅 Nicht buchbare Lücke", msg, {
                "tag": f"smoobu_luecke_{g['von']}",
                "actions": [{"action": f"{ACTION_PREFIX}LUECKE_{g['wohnung']}_{gid}", "title": f"Mindestaufenthalt {g['naechte']} setzen"}],
            }, kind="luecken")
            self._changed()

    async def apply_gap(self, gid: str) -> None:
        g = self.data.get("luecken", {}).get(gid)
        if not g:
            raise SmoobuError("Lücke nicht mehr bekannt")
        last = (date.fromisoformat(g["bis"]) - timedelta(days=1)).isoformat()
        await self.c.client.set_rates(g["wohnung"], g["von"], last, g.get("preis_vorschlag"), g["naechte"])
        self.c.force_revenue_refresh = True
        await self.c.async_request_refresh()

    # --- Verlauf importieren / Wissen erzeugen ------------------------------------
    async def import_history(self, years: int = 2) -> dict[str, Any]:
        """Alle Nachrichten der Gästebuchungen laden und als Lernbeispiele speichern.

        Zwei Durchläufe: erst alle Nachrichten laden und Vorlagen erkennen
        (gleicher Betreff in ≥ 3 Buchungen = automatische Smoobu-Nachricht),
        dann Paare „Gästenachricht → eure nächste eigene Antwort“ bilden.
        Frühere Import-Beispiele werden ersetzt; Texte werden bereinigt und geschwärzt.
        """
        since = (dt_util.now().date() - timedelta(days=365 * years)).isoformat()
        recs = [r for r in self.c.records_all()
                if not r["blockiert"] and not r["storniert"] and r["anreise"] >= since]
        state = {"start": dt_util.now().isoformat(), "buchungen": len(recs), "fertig": 0, "beispiele": 0,
                 "laeuft": True, "fehler": 0, "vorlagen": {}}
        self.data["import"] = state
        self._changed()
        loaded: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
        for r in recs:
            try:
                loaded.append((r, await self._messages(r["id"])))
            except SmoobuError:
                state["fehler"] += 1
            state["fertig"] += 1
            if state["fertig"] % 10 == 0:
                self._changed()
            await asyncio.sleep(self.throttle)  # Smoobu schonen
        # Vorlagen erkennen: gleicher Betreff (ohne Nummern) oder gleicher Text ohne Anrede
        # ≥ 3-mal in ≥ 2 Buchungen = automatische Nachricht
        subj_books: dict[str, list[int]] = {}
        body_books: dict[str, list[int]] = {}
        for r, msgs in loaded:
            for m in msgs:
                if int(m.get("type") or 0) != 2:
                    continue
                subj = norm_subject(m.get("subject") or "")
                if subj:
                    subj_books.setdefault(subj, []).append(r["id"])
                key = body_key(self._text(m))
                if len(key) >= 40:
                    body_books.setdefault(key, []).append(r["id"])
        def _is_tmpl(books: list[int]) -> bool:
            # ≥ 3 Nachrichten in ≥ 2 verschiedenen Buchungen
            return len(books) >= 3 and len(set(books)) >= 2

        self.data["vorlagen_betreff"] = sorted(k for k, v in subj_books.items() if _is_tmpl(v))
        self.data["vorlagen_anfang"] = sorted(k for k, v in body_books.items() if _is_tmpl(v))
        # Vorlagentexte (neueste Fassung je Betreff) – Quelle für die Wissensdatenbank
        templates: dict[str, str] = {}
        for _r, msgs in loaded:
            for m in msgs:
                subj = norm_subject(m.get("subject") or "")
                if int(m.get("type") or 0) == 2 and subj in self.data["vorlagen_betreff"]:
                    templates[subj] = clean(self._text(m))
        # Paare bilden (frühere Import-Beispiele ersetzen)
        self.data["beispiele"] = [b for b in self.data["beispiele"] if b.get("quelle") != "verlauf"]
        for r, msgs in loaded:
            last_guest = None
            for m in msgs:
                typ = int(m.get("type") or 0)
                if typ == 1:
                    last_guest = self._text(m)
                elif typ == 2 and last_guest and not self.is_template(m):
                    before = len(self.data["beispiele"])
                    self.learn(r["id"], last_guest, self._text(m), "verlauf", key=f"msg:{m.get('id')}")
                    state["beispiele"] += len(self.data["beispiele"]) - before
                    last_guest = None
        state["vorlagen"] = {k: v[:3000] for k, v in templates.items()}
        state["laeuft"] = False
        state["ende"] = dt_util.now().isoformat()
        self._changed()
        return state

    async def build_knowledge(self) -> int:
        """Aus eigenen Vorlagen + Antworten Wissensvorschläge erzeugen (Status „vorschlag“)."""
        self._require_ai()
        imp = self.data.get("import") or {}
        sources = [f"VORLAGE „{k}“:\n{clean(v)[:1800]}" for k, v in (imp.get("vorlagen") or {}).items()]
        sources += [f"ANTWORT:\n{b['antwort'][:600]}" for b in self.data["beispiele"][-80:]]
        if not sources:
            raise SmoobuError("Keine Texte vorhanden – zuerst den Verlauf importieren")
        text = "\n\n".join(sources)[:30000]
        prompt = (
            "Extrahiere aus den folgenden Nachrichten der Gastgeber einer Ferienwohnung alle wiederverwendbaren "
            "FAKTEN für eine Wissensdatenbank (z. B. Check-in/-out-Zeiten, Parken, Schlüssel/Zugang, WLAN, "
            "Hunde, Ausstattung, Regeln, Bewertung, Zahlung, Umgebung). Je Fakt eine Zeile im Format "
            "'Thema | Fakt'. Nur was ausdrücklich in den Texten steht, nichts ergänzen. Persönliche Daten von "
            "Gästen weglassen. Konkrete Zugangscodes NICHT übernehmen, stattdessen 'Code wird separat "
            "mitgeteilt'.\n\nTEXTE:\n" + text
        )
        result = await self._ai(prompt, {"fakten": {"description": "eine Zeile je Fakt: Thema | Fakt",
                                                    "required": True, "selector": {"text": {"multiline": True}}}},
                                "smoobu_wissen")
        count = 0
        existing = {w["thema"].casefold() for w in self.data["wissen"]}
        for line in str(result.get("fakten") or "").splitlines():
            thema, sep, fakt = line.strip(" -•").partition("|")
            if not sep or not fakt.strip() or thema.strip().casefold() in existing:
                continue
            self.save_knowledge({"thema": thema.strip()[:80], "text": fakt.strip(), "status": "vorschlag",
                                 "quelle": "verlauf"})
            existing.add(thema.strip().casefold())
            count += 1
        return count

    # --- Zustand für Karte/Sensor ----------------------------------------------
    def state(self) -> dict[str, Any]:
        sugs = sorted(self.data["vorschlaege"].values(), key=lambda s: s["erstellt"], reverse=True)
        return {
            "aktiv": self.enabled,
            # Für die Karten: False → KI-Buttons ausgrauen (Sperre greift serverseitig ohnehin)
            "ki_erlaubt": self.ai_allowed,
            "ki_sperre": None if self.ai_allowed else (AI_LOCKED if self.opts.get(CONF_AI_ENTITY) else "Keine KI ausgewählt"),
            "ki": self.opts.get(CONF_AI_ENTITY),
            # v1.17.0: Empfänger der Vorschlag-Pushes (aus „Benachrichtigungen“, sonst bisherige)
            "empfaenger": opt_recipients(self.opts, "vorschlag"),
            "status_entitaeten": self.opts.get(CONF_ASSIST_STATUS) or [],
            "fehler": self.last_error,
            "wissen": self.data["wissen"],
            "beispiele": list(reversed(self.data["beispiele"]))[:200],
            "beispiele_anzahl": len(self.data["beispiele"]),
            "vorschlaege": sugs[:50],
            "offen": [s for s in sugs if s["status"] == "offen"],
            "import": {k: v for k, v in (self.data.get("import") or {}).items() if k != "vorlagen"},
            "vorlagen": list(((self.data.get("import") or {}).get("vorlagen") or {}).keys()),
            "luecken": self.gap_suggestions(),
        }


def _hhmm(value: Any) -> str | None:
    m = re.search(r"(\d{1,2})[:.](\d{2})", str(value or ""))
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    return f"{h:02d}:{mi:02d}" if h < 24 and mi < 60 else None


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).casefold()

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
 *   custom:smoobu-inbox-card      Nachrichten der laufenden/kommenden Buchungen, antworten
 * Ein Klick auf eine Buchung öffnet überall dieselbe Detailansicht
 * (Gast, Preis, Kosten, Notiz, Zeiten ändern, Nachrichten, Sperre löschen).
 *
 * Datenquelle: WebSocket-Befehle smoobu/* (websocket_api.py), Aktionen über
 * die Smoobu-Aktionen (smoobu.block_period, set_rates, …).
 * Sicherheit: Alle Texte aus Smoobu (Namen, Nachrichten, Notizen) werden vor
 * der Ausgabe maskiert (esc), damit kein fremdes HTML ausgeführt wird.
 */

const SMOOBU_CARDS_VERSION = "1.15.3";

// ---------------------------------------------------------------------------
// Texte (Deutsch; Englisch für HA-Oberflächen in anderer Sprache)
// ---------------------------------------------------------------------------
const EN = {
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
  "Details": "Details", "In Smoobu öffnen": "Open in Smoobu", "Grund (optional)": "Reason (optional)",
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
  "Darstellung": "Appearance", "Hell": "Light", "Dunkel": "Dark", "System": "System", "Belegung": "Occupancy", "Assistent": "Assistant",
  "Zurück": "Back", "Weiter": "Next", "Zahl unten = Preis/Nacht": "Number below = price/night",
  "Keine Buchung in den nächsten 6 Monaten.": "No booking in the next 6 months.", "Danach keine Buchung in den nächsten 6 Monaten.": "No booking afterwards in the next 6 months.",
  "gebucht + Nachbuchungen wie im Vorjahr": "booked + pickup like last year", "Nachrichten": "Messages",
};
let LANG = "de";
const t = (s) => (LANG === "de" ? s : EN[s] || s);

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
const fdow = (s) => fdate(s, { weekday: "short", day: "2-digit", month: "2-digit" });
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

// Gewählte Wohnung je Gerät: „alle“ oder apartment_id (nur relevant ab 2 Wohnungen)
const AptSel = {
  listeners: new Set(),
  get value() { const v = lsGet(APT_KEY, ALL); return v === ALL ? ALL : Number(v) || ALL; },
  set value(v) { lsSet(APT_KEY, String(v)); this.listeners.forEach((l) => l()); },
};

// Virtuelle „Wohnung“ für die Gesamtansicht: Kanäle aller Wohnungen, Währung der ersten
function allApartment(info) {
  const ws = info.wohnungen;
  const seen = new Map();
  for (const w of ws) for (const k of w.kanaele) if (!seen.has(k.name)) seen.set(k.name, k);
  return { apartment_id: ALL, name: t("Alle Wohnungen"), kuerzel: "", currency: ws[0]?.currency || "EUR",
    kanaele: [...seen.values()], direktkanaele: ws[0]?.direktkanaele, check_in: ws[0]?.check_in, check_out: ws[0]?.check_out,
    erster_tag: ws.map((w) => w.erster_tag).filter(Boolean).sort()[0] || null, alle: true };
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
    if (!this._sub) {
      this._sub = this.hass.connection.subscribeMessage(() => {
        // Neuer Datenstand → alle Zwischenergebnisse verwerfen und Karten neu laden
        this._cache.clear();
        this.info = null;
        this.listeners.forEach((l) => l());
      }, { type: "smoobu/subscribe" });
    }
    return () => this.listeners.delete(cb);
  }
  invalidate() {
    this._cache.clear();
    this.info = null;
    this.listeners.forEach((l) => l());
  }
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
      ? `<div class="err">${t("Fehler")}: ${esc(this._error)}</div>`
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
    chips.push(`<button class="chip" data-ch="${esc(ch.name)}" aria-pressed="${sel.has(ch.name)}"><span class="dot" style="background:${chColor(ch.name)}"></span>${esc(ch.name)}</button>`);
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
// „Sa, 21.11.“ – deutsche Wochentage ohne Punkt (toLocaleDateString liefert „Sa.,“)
const WD_DE = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
const fdowLong = (s) => {
  if (!s) return "–";
  const d = D(String(s).slice(0, 10));
  return LANG === "de" ? `${WD_DE[d.getDay()]}, ${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}.`
    : fdate(s, { weekday: "short", day: "2-digit", month: "2-digit" });
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

// Status einer Wohnung heute → kurze, präzise Sätze für den Kopf
function stayStatus(apt, bookings, today) {
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
  if (arr && dep) return { key: "chg", pill: t("Gästewechsel"), title: t("Gästewechsel heute"), current: dep, next: arr,
    text: `${esc(dep.gast)} reist bis ${co(dep)} ab, ${esc(arr.gast)}${arr.hund ? " 🐕" : ""} kommt um ${ci(arr)}. Reinigung dazwischen.` };
  if (dep) return { key: "dep", pill: t("Abreise"), title: t("Abreise heute"), current: dep, next,
    text: `${esc(dep.gast)} reist bis ${co(dep)} ab. ${after(today, next)}` };
  if (arr) return { key: "arr", pill: t("Anreise"), title: t("Anreise heute"), current: null, next: arr,
    text: `${esc(arr.gast)}${arr.hund ? " 🐕" : ""} kommt um ${ci(arr)}, ${plural(arr.naechte, "Nacht", "Nächte")} bis ${fdowLong(arr.abreise)}.` };
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
  static defaults = { title: "", entities: [], upcoming: 5, gap_days: 60, band_days: 42 };
  static css = `
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
    const [month, ytd, last12, prevYear, list, ...rates] = await Promise.all([
      this.store.ws("smoobu/analytics", { ...tg, period: "monat", compare: "vorjahr_stand" }),
      this.store.ws("smoobu/analytics", { ...tg, period: "jahr_bis_heute", compare: "vorjahr" }),
      this.store.ws("smoobu/analytics", { ...tg, start: iso(addMonths(m0, -11)), end: iso(addMonths(m0, 1)), compare: "vorjahr" }),
      this.store.ws("smoobu/analytics", { ...tg, period: "vorjahr", compare: "kein" }).catch(() => null),
      this.store.ws("smoobu/bookings", { ...tg, start: iso(addDays(D(today), -1)), end: iso(addDays(D(today), 180)) }),
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
    return { apt, apts, info, today, month, ytd, last12, prevYear, bookings, status, ratesBy };
  }

  // ---- Kopf ----------------------------------------------------------------
  heroSingle(d) {
    const { apt, today, bookings, month, status } = d;
    const cur = apt.currency;
    const s = stayStatus(apt, bookings, today);
    const open = bookings.filter((b) => status[b.id]?.offen);
    const dm = month.veraenderung_prozent?.brutto;
    const lead2 = `${monthName(today)}: ${money(month.brutto, cur)} gebucht${dm !== null && dm !== undefined ? `, ${dm >= 0 ? "+" : "−"}${num(Math.abs(dm), 0)} % ggü. dem Buchungsstand des Vorjahres` : ""}. Auslastung ${pct(month.auslastung_prozent, 0)}.`;
    const guestCard = (b, label) => {
      if (!b) return `<div class="guest none"><div class="gl">${t(label)}</div><div class="gm">${t("keine")}</div></div>`;
      const portal = b.gruppe === "Portal";
      const note = b.hund ? `<div class="note">🐕 ${esc(b.hund_hinweis || t("Hund dabei"))}</div>`
        : b.offen > 0 && !portal ? `<div class="note bad">${t("Offen")} ${money(b.offen, cur, 2)}</div>`
        : portal ? `<div class="note">${t("Bezahlt über")} ${esc(b.kanal)}</div>` : "";
      const isNext = label === "Nächster Gast";
      const when = isNext ? `, ${daysWord(nightsBetween(today, b.anreise))}` : "";
      return `<div class="guest" data-id="${b.id}" style="--c:${colorOf(apt, b.kanal)}">
        <div class="gl">${t(label)}${when}</div><div class="gn">${esc(b.gast || "–")}${b.hund ? " 🐕" : ""}</div>
        <div class="gm">${fdowLong(b.anreise)} bis ${fdowLong(b.abreise)}<br>${plural(b.naechte, t("Nacht"), t("Nächte"))}, ${plural(b.personen, t("Person"), t("Personen"))}<br>
          ${isNext ? `${t("Ankunft")} ${uhr(b.check_in || apt.check_in) || "–"}` : `${t("Abreise bis")} ${uhr(b.check_out || apt.check_out || "11:00")}`}</div>${note}
        <div class="gf"><span class="dot" style="background:${colorOf(apt, b.kanal)}"></span>${esc(b.kanal)}<b>${money(b.brutto, cur)}</b></div></div>`;
    };
    const curLabel = s.current && s.current.abreise === today ? "Reist heute ab" : "Aktueller Gast";
    return `<section class="hero">
      <div><div class="h-state"><span class="pill ${s.key}">${s.pill}</span><span>${fdate(today, { weekday: "long", day: "numeric", month: "long" })}</span></div>
        <h1>${s.title}</h1><p class="lead">${s.text}</p><p class="lead2">${lead2}</p>
        <div class="events">${this.events(d, open)}</div></div>
      <div class="guests">${guestCard(s.current, curLabel)}${guestCard(s.next, "Nächster Gast")}</div></section>`;
  }
  heroMulti(d) {
    const { apts, today, bookings, status } = d;
    const per = apts.map((w) => ({ w, s: stayStatus(w, bookings.filter((b) => b.wohnung_id === w.apartment_id), today) }));
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
      const s = p.s, c = s.current, n = s.next;
      if (s.key === "chg") return `${esc(c.gast)} reist ab, ${esc(n.gast)} kommt um ${uhr(n.check_in || p.w.check_in || "16:00")}`;
      if (s.key === "dep") return `${esc(c.gast)} reist heute ab${n ? `, nächste Anreise ${fdowLong(n.anreise)}` : ""}`;
      if (s.key === "arr") return `${esc(n.gast)} kommt um ${uhr(n.check_in || p.w.check_in || "16:00")}`;
      if (s.key === "occ") return `${esc(c.gast)} bis ${fdowLong(c.abreise)}`;
      return n ? `Frei bis ${fdowLong(n.anreise)}, dann ${esc(n.gast)}` : t("Keine Buchung in den nächsten 6 Monaten.");
    };
    return `<section class="hero">
      <div><div class="h-state"><span>${fdate(today, { weekday: "long", day: "numeric", month: "long" })}</span></div>
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
        title="${esc(`${b.gast} · ${b.kanal} · ${fdate(b.anreise)} – ${fdate(b.abreise)}`)}"><span class="bn">${esc(b.gast)}${b.hund ? " 🐕" : ""}</span>${sub}</div>`;
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
      .map((c) => `<span><i class="dot" style="background:${chColor(c.name)}"></i>${esc(c.name)}</span>`).join("")
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
    const { apt, apts, today, bookings, status, ratesBy } = d;
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
        <span class="badge ${g.buchbar ? "good" : "bad"}">${t(g.buchbar ? "buchbar" : "nicht buchbar")}</span></div>`;
    }).join("");
    const open = guests.filter((b) => status[b.id]?.offen);
    // Offene Zahlungen: laufende und Anreisen der nächsten 30 Tage zuerst (max. 3), Rest als Summe
    const unpaidAll = guests.filter((b) => b.offen > 0 && b.gruppe !== "Portal" && b.status !== "vergangen");
    const soon = iso(addDays(D(today), 30));
    const unpaid = unpaidAll.filter((b) => b.anreise <= soon).slice(0, 3);
    const later = unpaidAll.filter((b) => !unpaid.includes(b));
    const ago = (s) => {
      if (!s) return "";
      const ms = Date.now() - new Date(String(s).replace(" ", "T")).getTime();
      if (isNaN(ms)) return "";
      if (ms < 0) return fdowLong(s);
      const h = Math.round(ms / 3600000);
      return h < 1 ? t("gerade eben") : h < 24 ? `vor ${h} Std.` : `vor ${Math.round(h / 24)} ${Math.round(h / 24) === 1 ? "Tag" : "Tagen"}`;
    };
    const todo = [
      ...open.map((b) => `<div class="todo msg"><div class="tt">${esc(b.gast)} ${t("wartet auf Antwort")}${this.code(b)}</div>
        ${status[b.id].letzte_text ? `<p>„${esc(status[b.id].letzte_text)}“</p>` : "<p></p>"}
        <div class="ta"><button class="btn" data-id="${b.id}">${t("Antworten")}</button><span class="ago">${ago(status[b.id].letzte_zeit)}</span></div></div>`),
      ...unpaid.map((b) => `<div class="todo"><div class="tt">${t("Zahlung offen")}${this.code(b)}</div><p>${esc(b.gast)}, ${t("Anreise")} ${fdowLong(b.anreise)}</p>
        <div class="ta"><span class="amt">${money(b.offen, cur, 2)}</span><button class="btn flat" data-id="${b.id}">${t("Buchung öffnen")}</button></div></div>`),
      later.length ? `<div class="sub" style="padding:4px 2px">${t("Später fällig")}: ${plural(later.length, t("Buchung"), t("Buchungen"))}, ${money(later.reduce((a, b) => a + b.offen, 0), cur, 2)}</div>` : "",
    ].join("");
    return `<section class="three">
      <div class="panel"><div class="ph"><h2>${t("Nächste Anreisen")}</h2></div>${arrivals || `<div class="done">${t("Keine Anreisen geplant.")}</div>`}</div>
      <div class="panel"><div class="ph"><h2>${t("Freie Zeiträume")}</h2><span class="sub">${t("nächste")} ${this._config.gap_days} ${t("Tage")}</span></div>${gapRows || `<div class="done">${t("Keine Lücken.")}</div>`}</div>
      <div class="panel"><div class="ph"><h2>${t("Wartet auf dich")}</h2></div>${todo || `<div class="done">✓ ${t("Alles erledigt.")}</div>`}</div></section>`;
  }

  body(d) {
    const { month, ytd, today } = d;
    return `${this.multi ? this.heroMulti(d) : this.heroSingle(d)}${this.band(d)}${this.kpis(d)}${this.lists(d)}
      <p class="foot">${t("Vergleich")}: ${monthName(today)} ${t("ggü. Buchungsstand am")} ${fdate(month.stichtag_vergleich)},
        ${t("Jahr ggü.")} ${fdate(ytd.vergleich?.von)}–${fdate(iso(addDays(D(ytd.vergleich?.bis || today), -1)))}. ${t("PP = Prozentpunkte")}.
        ${t("Prognose")} = ${t("gebucht + Nachbuchungen wie im Vorjahr")}. ${t("Verläufe: kräftige Linie = letzte 12 Monate bzw. dieses Jahr, blasse Linie = Vorjahr.")}</p>`;
  }
  bind(root) {
    root.querySelectorAll("[data-id]").forEach((el) => el.addEventListener("click", (e) => { e.stopPropagation(); this.openBooking(Number(el.dataset.id)); }));
    root.querySelectorAll("[data-apt]").forEach((el) => el.addEventListener("click", () => { AptSel.value = Number(el.dataset.apt); }));
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
            title="${esc(b.blockiert ? t("Sperrzeit") : `${b.gast}, ${b.personen} P., ${b.kanal}, ${money(b.brutto, cur)}`)}"
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
            <label>${t("Mindestaufenthalt")} <input data-k="min" type="number" min="1" max="90" style="width:70px"></label>
            <button class="btn" data-act="do-rate">${t("Speichern")}</button>`
          : `<button class="btn" data-act="block">🔒 ${t("Sperren")}</button><button class="btn" data-act="rate">€ ${t("Preis setzen")}</button>`}
        <button class="btn flat" data-act="clear">${t("Abbrechen")}</button></div>`
      : `<div class="legend">${t("Tage markieren: erst ersten, dann letzten Tag antippen")}</div>`;
    const chans = apts.flatMap((w) => w.kanaele).filter((c, i, a) => a.findIndex((x) => x.name === c.name) === i);
    return `
      <div class="head"><h2>${esc(this._config.title || t("Belegungsplan"))}</h2>
        <button class="btn flat" data-act="prev" aria-label="${t("Zurück")}">◀</button><button class="btn flat" data-act="now">${t("Heute")}</button>
        <button class="btn flat" data-act="next" aria-label="${t("Weiter")}">▶</button></div>
      <div class="scroll"><div class="months ${this.multi ? "multi" : ""}">${rows.join("")}</div></div>
      <div class="legend">${chans.map((c) => `<span><span class="dot" style="background:${chColor(c.name)}"></span>${esc(c.name)}</span>`).join("")}
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
    if (a === "clear") return this.setState({ selStart: null, selEnd: null, panel: null });
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
      this.setState({ selStart: null, selEnd: null, selApt: null, panel: null }, true);
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
    wrap.innerHTML = `<div style="background:${p.surf};color:${p.ink};padding:22px;border-radius:16px;max-width:380px;font:15px/1.45 ${FONT};border:1px solid ${p.line};box-shadow:0 12px 40px rgba(0,0,0,.3)">
      <div style="margin-bottom:18px">${esc(text)}</div><div style="display:flex;gap:8px;justify-content:flex-end">
      <button data-v="0" style="font:600 14px ${FONT};padding:8px 16px;border-radius:999px;border:1px solid ${p.line};background:none;color:${p.acc};cursor:pointer">${t("Nein")}</button>
      <button data-v="1" style="font:600 14px ${FONT};padding:8px 16px;border-radius:999px;border:none;background:${p.acc};color:${p.accInk};cursor:pointer">${t("Ja")}</button></div></div>`;
    wrap.addEventListener("click", (e) => {
      const v = e.target?.dataset?.v;
      if (v !== undefined || e.target === wrap) { wrap.remove(); resolve(v === "1"); }
    });
    document.body.appendChild(wrap);
  });
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
class SmoobuBookingsCard extends SmoobuCard {
  static defaults = { title: "", period: "jahr", status: [] };
  static initialState = (c) => ({ period: c.period || "jahr", from: null, to: null, channels: [], status: c.status || [],
    search: "", sort: "anreise", dir: 1 });
  static css = `.toolbar input[type=search] { min-width: 180px; flex: 1 1 180px; }
    td .dot { margin-right: 6px; } td.st ha-icon { color: var(--sm-muted); } tr.cx td { text-decoration: line-through; opacity: .6; }
    tr.bl td { color: var(--sm-muted); font-style: italic; }`;
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
    rows.sort((a, b) => {
      const x = a[k] ?? "", y = b[k] ?? "";
      return (typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y))) * s.dir;
    });
    return rows;
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
    const body = rows.map((b) => `<tr class="click ${b.storniert ? "cx" : ""} ${b.blockiert ? "bl" : ""}" data-id="${b.id}">
      <td class="st"><ha-icon icon="${STATUS_ICON[b.status]}" title="${t(b.status)}"></ha-icon></td>
      ${this.multi ? `<td>${codeTag(b.wohnung)}</td>` : ""}<td>${fdow(b.anreise)}</td><td>${fdow(b.abreise)}</td><td class="n">${b.naechte}</td>
      <td>${b.blockiert ? `🔒 ${esc(b.notiz || t("Gesperrt"))}` : esc(b.gast)}${b.hund ? " 🐕" : ""}</td>
      <td class="n">${b.blockiert ? "" : b.personen}</td>
      <td><span class="dot" style="background:${colorOf(apt, b.kanal, b.blockiert)}"></span>${esc(b.kanal)}</td>
      <td class="n">${b.blockiert ? "" : money(b.brutto, cur, 2)}</td><td class="n">${b.blockiert ? "" : money(b.kosten, cur, 2)}</td>
      <td class="n">${b.blockiert ? "" : money(b.netto, cur, 2)}</td><td class="n">${b.netto_pro_nacht ? money(b.netto_pro_nacht, cur) : ""}</td>
      <td class="n">${b.offen > 0 ? `<span class="badge bad">${money(b.offen, cur, 2)}</span>` : ""}</td>
      <td class="n">${b.vorlauf_tage ?? ""}</td></tr>`).join("");
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
      this.setState({ sort: k, dir: s.sort === k ? -s.dir : 1 });
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
function barChart({ labels, stacks, line, fmt, unit, daily }) {
  const W = 800, H = 260, L = 56, R = 8, T = 10, B = 28;
  const n = labels.length || 1;
  const sums = labels.map((_, i) => stacks.reduce((a, s) => a + (s.values[i] || 0), 0));
  const max = niceMax(Math.max(...sums, ...(line?.values || [0])) * 1.05);
  const y = (v) => T + (H - T - B) * (1 - v / max);
  const bw = (W - L - R) / n;
  let svg = "";
  for (let g = 0; g <= 4; g++) {
    const v = (max / 4) * g;
    svg += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" stroke-opacity=".12"/>
      <text x="${L - 6}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="currentColor" fill-opacity=".6">${fmt(v)}</text>`;
  }
  const step = daily ? Math.ceil(n / 15) : 1;
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
    const lbl = daily ? fdate(lab, { day: "2-digit", month: "2-digit" }) : D(`${lab}-01`).toLocaleDateString(locale(), { month: "short" });
    if (i % step === 0) svg += `<text x="${x + bw / 2}" y="${H - 8}" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity=".7">${lbl}</text>`;
    const tip = `${daily ? fdate(lab) : D(`${lab}-01`).toLocaleDateString(locale(), { month: "long", year: "numeric" })}: ${fmt(sums[i])}` +
      (parts.length > 1 ? ` (${parts.join(", ")})` : "") + (line ? ` · ${line.label}: ${fmt(line.values[i] || 0)}` : "");
    svg += `<rect class="hit" data-tip="${esc(tip)}" x="${x}" y="${T}" width="${bw}" height="${H - T - B}" fill="transparent"><title>${esc(tip)}</title></rect>`;
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
class SmoobuAnalyticsCard extends SmoobuCard {
  static defaults = { title: "", period: "jahr", compare: "vorjahr" };
  static initialState = (c) => ({ period: c.period, compare: c.compare, channels: [], from: null, to: null, metric: "brutto" });
  static css = `
    .split { display: grid; grid-template-columns: minmax(0, 1fr) 200px; gap: 16px; align-items: center; }
    @media (max-width: 700px) { .split { grid-template-columns: 1fr; } }
    .share { display: flex; flex-direction: column; align-items: center; gap: 6px; font-size: .8rem; }
    .bar-in { height: 5px; border-radius: 3px; background: var(--sm-accent); margin-top: 3px; }
    .grid { margin-bottom: 4px; }
    .tip { min-height: 1.2em; font-size: .82rem; color: var(--sm-muted); margin-top: 4px; }
    .ins li { margin: 4px 0; } .ins { padding-left: 18px; margin: 4px 0; }
  `;
  async load() {
    const apt = await this.apartment();
    const s = this._state;
    const params = { ...this.target, compare: s.compare };
    if (s.period === "custom") {
      if (!s.from || !s.to) { const info = await this.store.getInfo(); const [a, b] = periodRange("jahr", info.heute); params.start = iso(a); params.end = iso(b); }
      else { params.start = s.from; params.end = iso(addDays(D(s.to), 1)); }
    } else params.period = s.period;
    if (s.channels.length) params.channels = s.channels;
    const r = await this.store.ws("smoobu/analytics", params);
    // Gesamtansicht: dieselbe Auswertung je Wohnung für den Wohnungsvergleich
    let per = [];
    if (this.multi) {
      const info = await this.store.getInfo();
      per = await Promise.all(info.wohnungen.filter((w) => !params.entry_id || w.entry_id === params.entry_id)
        .map((w) => this.store.ws("smoobu/analytics", { ...params, apartment_id: w.apartment_id }).then((x) => ({ w, x })).catch(() => null)));
      per = per.filter(Boolean);
    }
    return { apt, r, per };
  }
  insights(apt, r) {
    const cur = apt.currency;
    const out = [];
    const chans = Object.entries(r.kanaele);
    const portals = chans.filter(([, v]) => v.gruppe === "Portal" && v.brutto > 0);
    if (portals.length) {
      const [n, v] = portals.reduce((a, b) => (b[1].kostenquote_prozent > a[1].kostenquote_prozent ? b : a));
      out.push(`Teuerstes Portal: <b>${esc(n)}</b> mit ${pct(v.kostenquote_prozent)} Kosten (${money(v.kosten, cur)}).`);
      const pb = portals.reduce((a, [, v]) => a + v.brutto, 0), pk = portals.reduce((a, [, v]) => a + v.kosten, 0);
      const direct = chans.filter(([, v]) => v.gruppe === "Direkt").reduce((a, [, v]) => a + v.brutto, 0);
      if (direct && pb) out.push(`Direktbuchungen sparten rund <b>${money((direct * pk) / pb, cur)}</b> Portalkosten (Ø ${pct((pk / pb) * 100)}).`);
    }
    const best = chans.filter(([, v]) => v.netto_pro_nacht).sort((a, b) => b[1].netto_pro_nacht - a[1].netto_pro_nacht);
    if (best.length > 1) out.push(`Bester Erlös je Nacht: <b>${esc(best[0][0])}</b> ${money(best[0][1].netto_pro_nacht, cur)} netto, schwächster: ${esc(best.at(-1)[0])} ${money(best.at(-1)[1].netto_pro_nacht, cur)}.`);
    const storno = chans.filter(([, v]) => v.stornos > 0 && v.buchungen + v.stornos >= 3).sort((a, b) => b[1].stornoquote_prozent - a[1].stornoquote_prozent);
    if (storno.length) out.push(`Höchste Stornoquote: <b>${esc(storno[0][0])}</b> ${pct(storno[0][1].stornoquote_prozent)} (${storno[0][1].stornos} von ${storno[0][1].stornos + storno[0][1].buchungen}, ${money(storno[0][1].storno_volumen, cur)}).`);
    const lead = chans.filter(([, v]) => v.vorlauf_schnitt !== null && v.buchungen >= 2).sort((a, b) => a[1].vorlauf_schnitt - b[1].vorlauf_schnitt);
    if (lead.length > 1) out.push(`Kurzfristigste Gäste: <b>${esc(lead[0][0])}</b> (Ø ${num(lead[0][1].vorlauf_schnitt)} Tage Vorlauf), langfristigste: ${esc(lead.at(-1)[0])} (Ø ${num(lead.at(-1)[1].vorlauf_schnitt)} Tage).`);
    if (r.vergleich && r.veraenderung_prozent?.brutto !== null && r.veraenderung_prozent?.brutto !== undefined) {
      const ch = r.veraenderung_prozent.brutto;
      out.push(`Umsatz ${ch >= 0 ? "über" : "unter"} dem Vergleichszeitraum: ${delta(ch)} (${money(r.brutto - r.vergleich.brutto, cur)}).`);
    }
    if (r.prognose) out.push(`Prognose ${new Date().getFullYear()}: <b>${money(r.prognose.prognose, cur)}</b> brutto (gebucht ${money(r.prognose.gebucht, cur)} + ${t("Nachbuchung wie Vorjahr")} ${money(r.prognose.nachbuchung_vorjahr, cur)}).`);
    return out;
  }
  body({ apt, r, per = [] }) {
    const cur = apt.currency;
    const s = this._state;
    const c = r.vergleich;
    const dp = r.veraenderung_prozent || {}, dpp = r.veraenderung_punkte || {};
    const cmpTxt = (k, f) => (c ? `${t("Vergleich")} ${f(c[k])}` : "");
    const m = s.metric;
    const reihe = r.reihe;
    const colors = Object.fromEntries(Object.keys(r.farben || {}).map((n) => [n, chColor(n)]));
    const stacks = m === "brutto"
      ? Object.entries(reihe.kanaele).map(([name, values]) => ({ name, values, color: colors[name] || colorOf(apt, name) }))
      : [{ name: t(m === "netto" ? "Netto" : "Nächte"), values: reihe[m], color: PAL[DARK ? "dark" : "light"].acc }];
    const fmt = m === "naechte" ? (v) => num(v) : (v) => money(v, cur);
    const line = c?.reihe ? { values: c.reihe[m], label: t(COMPARE_LABEL[s.compare]) } : null;
    const chans = Object.entries(r.kanaele);
    const cmpCh = c?.kanaele || {};
    const table = chans.map(([n, v]) => `<tr><td><span class="dot" style="background:${colors[n] || colorOf(apt, n)}"></span> ${esc(n)}</td>
      <td class="n">${money(v.brutto, cur)}</td><td class="n" style="min-width:90px">${pct(v.anteil_prozent, 0)}
        <div class="bar-in" style="width:${v.anteil_prozent}%;background:${colors[n] || colorOf(apt, n)}"></div></td>
      <td class="n">${cmpCh[n] ? delta(((v.brutto - cmpCh[n].brutto) / (cmpCh[n].brutto || 1)) * 100) : c ? `<span class="badge">neu</span>` : ""}</td>
      <td class="n">${money(v.netto, cur)}</td><td class="n">${pct(v.kostenquote_prozent)}</td><td class="n">${v.naechte}</td>
      <td class="n">${money(v.netto_pro_nacht, cur)}</td><td class="n">${v.buchungen}</td><td class="n">${v.stornos ? pct(v.stornoquote_prozent, 0) : "–"}</td>
      <td class="n">${num(v.aufenthalt_schnitt, 1)}</td><td class="n">${num(v.vorlauf_schnitt)}</td><td class="n">${num(v.personen_schnitt, 1)}</td></tr>`).join("");
    const ins = this.insights(apt, r);
    return `
      <div class="head"><h2>${esc(this._config.title || t("Finanzen"))}${this.multi ? ` <span class="sub">${t("Alle Wohnungen")}</span>` : ""}</h2>
        <span class="sub">${fdate(r.von)} – ${fdate(iso(addDays(D(r.bis), -1)))}${c ? `, ${t("Vergleich")} ${fdate(c.von)} – ${fdate(iso(addDays(D(c.bis), -1)))}` : ""}</span></div>
      <div class="toolbar">${periodSelect(s.period)}
        ${s.period === "custom" ? `<input type="date" data-k="from" value="${s.from || ""}"> – <input type="date" data-k="to" value="${s.to || ""}">` : ""}
        <select data-k="compare">${Object.entries(COMPARE_LABEL).map(([k, v]) => `<option value="${k}" ${k === s.compare ? "selected" : ""}>${t("Vergleich")}: ${t(v)}</option>`).join("")}</select>
      </div>
      <div class="toolbar">${channelChips(apt, s.channels, colors)}</div>
      <div class="grid">
        ${tile(t("Brutto"), money(r.brutto, cur), `${cmpTxt("brutto", (v) => money(v, cur))} ${delta(dp.brutto)}`)}
        ${tile(t("Netto"), money(r.netto, cur), `${cmpTxt("netto", (v) => money(v, cur))} ${delta(dp.netto)}`)}
        ${tile(t("Kosten"), money(r.kosten, cur), `${pct(r.kostenquote_prozent)} ${delta(dpp.kostenquote_prozent, "pp", true)}`)}
        ${tile(t("Auslastung"), pct(r.auslastung_prozent, 0), `${r.naechte} ${t("Nächte")} · ${r.gesperrt_naechte} ${t("Gesperrt")} ${delta(dpp.auslastung_prozent, "pp")}`)}
        ${tile(t("Netto/Nacht"), money(r.netto_pro_nacht, cur), `${t("Brutto/Nacht")} ${money(r.brutto_pro_nacht, cur)} ${delta(dp.netto_pro_nacht)}`)}
        ${tile(t("Buchungen"), num(r.buchungen), `${r.stornos} ${t("Stornos")} (${pct(r.stornoquote_prozent, 0)}) ${delta(dp.buchungen)}`)}
        ${tile(t("Ø Aufenthalt"), `${num(r.aufenthalt_schnitt, 1)} N`, `${cmpTxt("aufenthalt_schnitt", (v) => num(v, 1))} ${delta(dp.aufenthalt_schnitt)}`)}
        ${tile(t("Ø Vorlauf"), `${num(r.vorlauf_schnitt)} ${t("Tage")}`, `Median ${num(r.vorlauf_median)} · ${cmpTxt("vorlauf_schnitt", (v) => num(v))}`)}
        ${tile(t("Ø Personen"), num(r.personen_schnitt, 1), `${r.hunde} × 🐕 · ${money(r.preis_pro_buchung, cur)} je Buchung`)}
        ${tile(t("Direktanteil"), pct(r.direktanteil_prozent, 0), delta(dpp.direktanteil_prozent, "pp"))}
        ${r.prognose ? tile(t("Prognose Jahr"), money(r.prognose.prognose, cur), `${t("Netto")} ${money(r.prognose.prognose_netto, cur)}`) : ""}
      </div>
      <h3>${t("Diagramm")}</h3>
      <div class="row"><div class="seg">${["brutto", "netto", "naechte"].map((k) => `<button data-metric="${k}" aria-pressed="${m === k}">${t(k === "brutto" ? "Brutto" : k === "netto" ? "Netto" : "Nächte")}</button>`).join("")}</div>
        ${line ? `<span class="sub">┄ ${esc(line.label)}</span>` : ""}</div>
      <div class="split"><div>${barChart({ labels: reihe.labels, stacks, line, fmt, daily: reihe.einheit === "tag" })}<div class="tip" data-k="tip"></div></div>
        <div class="share">${donut(chans.map(([n, v]) => ({ name: n, value: v.brutto, color: colors[n] || colorOf(apt, n) })), pct(r.direktanteil_prozent, 0))}
          <span class="sub">${t("Direktanteil")}</span></div></div>
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
        <th class="n">${t("Netto")}</th><th class="n">${t("Kosten")}</th><th class="n">${t("Nächte")}</th><th class="n">${t("Netto/Nacht")}</th>
        <th class="n">${t("Buchungen")}</th><th class="n">${t("Stornoquote")}</th><th class="n">${t("Ø Aufenthalt")}</th><th class="n">${t("Ø Vorlauf")}</th><th class="n">${t("Ø Personen")}</th></tr></thead>
        <tbody>${table || `<tr><td colspan="13" class="empty">${t("Keine Daten")}</td></tr>`}</tbody>
        <tfoot><tr><td>${t("Summe")}</td><td class="n">${money(r.brutto, cur)}</td><td class="n">100 %</td><td class="n">${delta(dp.brutto)}</td>
          <td class="n">${money(r.netto, cur)}</td><td class="n">${pct(r.kostenquote_prozent)}</td><td class="n">${r.naechte}</td>
          <td class="n">${money(r.netto_pro_nacht, cur)}</td><td class="n">${r.buchungen}</td><td class="n">${pct(r.stornoquote_prozent, 0)}</td>
          <td class="n">${num(r.aufenthalt_schnitt, 1)}</td><td class="n">${num(r.vorlauf_schnitt)}</td><td class="n">${num(r.personen_schnitt, 1)}</td></tr></tfoot></table></div>`;
  }
  bind(root) {
    const s = this._state;
    root.querySelector('[data-k="period"]')?.addEventListener("change", (e) => this.setState({ period: e.target.value }, true));
    root.querySelector('[data-k="compare"]')?.addEventListener("change", (e) => this.setState({ compare: e.target.value }, true));
    root.querySelector('[data-k="from"]')?.addEventListener("change", (e) => this.setState({ from: e.target.value }, true));
    root.querySelector('[data-k="to"]')?.addEventListener("change", (e) => this.setState({ to: e.target.value }, true));
    root.querySelectorAll("[data-ch]").forEach((el) => el.addEventListener("click", () => this.setState({ channels: toggleChannel(s.channels, el.dataset.ch) }, true)));
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
  constructor() { super(); this.attachShadow({ mode: "open" }); this.data = null; this.err = null; }
  connectedCallback() {
    this._esc = (e) => e.key === "Escape" && this.remove();
    window.addEventListener("keydown", this._esc);
    this.render();
    this.load();
  }
  disconnectedCallback() { window.removeEventListener("keydown", this._esc); }
  async load() {
    try {
      const [info, d] = await Promise.all([this.store.getInfo(),
        this.store.ws("smoobu/booking", { ...this.target, reservation_id: this.rid }, { cache: false })]);
      this.apt = info.wohnungen.find((w) => w.apartment_id === (d.buchung?.wohnung_id ?? this.target.apartment_id)) || info.wohnungen[0];
      this.data = d;
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
    this.shadowRoot.innerHTML = `<style>${vars}${BASE_CSS}${DIALOG_CSS}</style><div class="back"><div class="dlg">
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
    const positions = (b.positionen || []).map((p) => `<div class="row"><span class="grow">${esc(p.name)}</span><span>${money(p.betrag, cur, 2)}</span></div>`).join("");
    const msgs = newestFirst(d.nachrichten).map((m) => `<div class="msg ${Number(m.typ) === 2 ? "out" : ""}"><div class="h">${dirLabel(m)}${m.zeit ? " · " + esc(fdate(m.zeit, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })) : ""}${m.betreff ? " · " + esc(m.betreff) : ""}</div>${msgHtml(m.text)}</div>`).join("");
    const canCancel = !b.blockiert && b.gruppe === "Direkt" && !b.storniert && b.status !== "vergangen";
    return `
      <div class="row" style="margin-bottom:12px"><span class="badge"><span class="dot" style="background:${color}"></span> ${esc(b.kanal)}</span>
        <span class="badge"><ha-icon icon="${STATUS_ICON[b.status] || "mdi:help"}"></ha-icon> ${t(b.status || "")}</span>
        ${b.referenz ? `<span class="badge">#${esc(b.referenz)}</span>` : ""}<span class="badge">ID ${esc(b.id)}</span>
        ${b.offen > 0 ? `<span class="badge bad">${t("Offen")} ${money(b.offen, cur, 2)}</span>` : b.blockiert ? "" : `<span class="badge good">✓ ${t("bezahlt")}</span>`}</div>
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
          b.anzahlung && ["Anzahlung", `${money(b.anzahlung, cur, 2)} ${b.anzahlung_bezahlt ? "✓" : "✗"}`],
          b.kurtaxe && ["Kurtaxe", money(b.kurtaxe, cur, 2)],
        ])}</div>` : ""}
        <div><h3>${t("Notiz")}</h3><textarea data-k="notice">${esc(b.notiz || "")}</textarea>
          <div class="row"><button class="btn flat" data-act="notice">${t("Speichern")}</button></div>
          ${b.assistent_notiz ? `<div class="sub" style="margin-top:8px;white-space:pre-wrap">${esc(b.assistent_notiz)}</div>` : ""}</div>
      </div>
      ${!b.blockiert ? `<h3>${t("Nachrichten")} (${(d.nachrichten || []).length})</h3><div class="msgs">${msgs || `<div class="muted">${t("keine")}</div>`}</div>
        <textarea data-k="msg" placeholder="${t("Antworten")} ${t("an den Gast")} …" style="margin-top:8px"></textarea>
        <div class="row"><span class="grow"></span><button class="btn" data-act="send">✉ ${t("Senden")}</button></div>` : ""}
      <div class="acts">
        ${b.blockiert ? `<button class="btn danger" data-act="unblock">🔓 ${t("Sperre löschen")}</button>` : ""}
        ${canCancel ? `<button class="btn danger" data-act="cancel">${t("Stornieren")}</button>` : ""}
        <span class="grow"></span>
        <a class="btn flat" href="https://login.smoobu.com/" target="_blank" rel="noopener" style="text-decoration:none">${t("In Smoobu öffnen")} ↗</a>
      </div>`;
  }
  bind() {
    const r = this.shadowRoot;
    r.querySelector(".back")?.addEventListener("click", (e) => { if (e.target.classList.contains("back")) this.remove(); });
    r.querySelectorAll("[data-act]").forEach((el) => el.addEventListener("click", () => this.act(el.dataset.act)));
  }
  async act(a) {
    if (a === "close") return this.remove();
    const v = (k) => this.shadowRoot.querySelector(`[data-k="${k}"]`)?.value;
    const id = this.rid;
    try {
      if (a === "times") {
        const data = { reservation_id: id };
        if (v("ci")) data.arrival_time = v("ci");
        if (v("co")) data.departure_time = v("co");
        await this.store.service("update_reservation", data);
      } else if (a === "notice") {
        await this.store.service("update_reservation", { reservation_id: id, notice: v("notice") || "" });
      } else if (a === "send") {
        const text = (v("msg") || "").trim();
        if (!text) return;
        if (!(await confirmDialog(`${t("Senden")} ${t("an den Gast")}?`))) return;
        await this.store.ws("smoobu/assistant/send", { ...this.target, reservation_id: id, text }, { cache: false });
        this.store.invalidate();
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
    .pending { display: inline-block; margin-top: 2px; padding: 1px 8px; border-radius: 999px; font-size: .75rem; font-weight: 600;
      background: var(--sm-bad); color: #fff; }
    /* v1.14.0: „Keine Antwort nötig“ – klein in der Liste, normal im Verlauf */
    .btn.mini { padding: 2px 8px; font-size: .75rem; min-height: 0; margin: 2px 0 0 6px; }
    .done { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: .75rem; font-weight: 600;
      background: color-mix(in srgb, var(--sm-good) 18%, transparent); color: var(--sm-good); }
    .noreply { display: flex; gap: 8px; align-items: center; margin: 4px 0 8px; }
    .btn[disabled].locked { opacity: .45; cursor: not-allowed; }
    .opencount { padding: 2px 10px; border-radius: 999px; font-size: .85rem; font-weight: 600; background: var(--sm-bad); color: #fff; }
    .sugbox { margin-top: 8px; padding: 8px 12px; border-radius: 10px; font-size: .85rem;
      background: color-mix(in srgb, var(--sm-accent) 10%, transparent); border-left: 4px solid var(--sm-accent); }
    .sugbox.urgent { border-left-color: var(--sm-bad); background: color-mix(in srgb, var(--sm-bad) 12%, transparent); }
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
      if (this._data?.status) this._data.status[id] = this.threadStatus(d, this._data.status[id]);
      if (this._state.sel === id) this.setState({ thread: d, loadingThread: false, sug, draft: sug?.antwort || "",
        ai: !!a, aiAllowed: !!a?.ki_erlaubt, aiReason: a?.ki_sperre || "" });
    } catch (e) { this.setState({ thread: { fehler: e.message || String(e), nachrichten: [] }, loadingThread: false }); }
  }
  threadStatus(d, prev = {}) {
    const last = newestFirst((d.nachrichten || []).filter((m) => !m.intern))[0];
    const guest = !!last && Number(last.typ) === 1;
    const doneId = prev.erledigt_id;
    const dismissed = guest && doneId != null && Number(last.id) <= Number(doneId);
    return { ...prev, offen: guest && !dismissed, ohne_antwort: dismissed, letzte_zeit: last?.zeit };
  }
  async noReply(id, done = true) {
    try {
      const r = await this.store.ws("smoobu/message_done", { ...this.target, reservation_id: id, done }, { cache: false });
      if (this._data?.status) this._data.status[id] = r.status;
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
      `<div class="sub">${t("Nachrichten")} · ${esc(last.attributes.gast || "")} · ${fdate(last.attributes.empfangen, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</div>` +
      `${msgHtml(String(last.attributes.text).slice(0, 2000))}</div>` : "";
    const openCount = guests.filter((b) => status[b.id]?.offen).length;
    const items = guests.map((b) => { const op = !!status[b.id]?.offen;
      return `<div class="item ${s.sel === b.id ? "on" : ""} ${op ? "open" : ""}" data-rid="${b.id}">
      <span class="dot" style="background:${colorOf(apt, b.kanal)}"></span><div class="grow"><b>${esc(b.gast)}</b>${b.hund ? " 🐕" : ""}${this.code(b)}
      <div class="sub">${fdate(b.anreise)} – ${fdate(b.abreise)} · ${t(b.status)}</div>
      ${op ? `<span class="pending">💬 ${t("Antwort offen")}</span><button class="btn flat mini" data-noreply="${b.id}" title="${t("Keine Antwort nötig")}">✓ ${t("Keine Antwort nötig")}</button>` : ""}</div></div>`; }).join("");
    const th = s.thread;
    const msgs = th ? newestFirst(th.nachrichten).map((m) => `<div class="msg ${Number(m.typ) === 2 ? "out" : ""}"><div class="h">${dirLabel(m)} ${m.zeit ? esc(fdate(m.zeit, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })) : ""} ${m.betreff ? "· " + esc(m.betreff) : ""}</div>${msgHtml(m.text)}</div>`).join("") : "";
    const right = !s.sel ? `<div class="empty">← ${t("Gast")}</div>`
      : s.loadingThread ? `<div class="empty">${t("Laden …")}</div>`
      : `${th?.fehler ? `<div class="err">${esc(th.fehler)}</div>` : ""}
        <div class="row"><b class="grow">${esc(th?.buchung?.gast || "")}</b><button class="btn flat" data-act="detail">${t("Details")}</button></div>
        ${status[s.sel]?.offen ? `<div class="noreply"><span class="pending">💬 ${t("Antwort offen")}</span>
          <button class="btn flat" data-noreply="${s.sel}">✓ ${t("Keine Antwort nötig")}</button></div>`
          : status[s.sel]?.ohne_antwort ? `<div class="noreply"><span class="done">✓ ${t("Ohne Antwort erledigt")}</span>
          <button class="btn flat" data-undo="${s.sel}">↶ ${t("Rückgängig")}</button></div>` : ""}
        <div class="msgs">${msgs || `<div class="muted">${t("keine")}</div>`}</div>
        ${s.sug ? `<div class="sugbox ${s.sug.dringend ? "urgent" : ""}"><b>✨ ${s.sug.dringend ? "DRINGEND · " : ""}${esc(s.sug.absicht)}</b>
          ${s.sug.zusammenfassung ? ` · ${esc(s.sug.zusammenfassung)}` : ""}
          ${s.sug.hinweis ? `<div>ℹ️ ${esc(s.sug.hinweis)}</div>` : ""}
          ${s.sug.wissensluecke ? `<div>❓ Wissenslücke: ${esc(s.sug.wissensluecke)}</div>` : ""}
          ${s.sug.offen ? `<div>✏️ Bitte die Stellen [OFFEN: …] ergänzen.</div>` : ""}</div>` : ""}
        <textarea data-k="msg" placeholder="${t("Antworten")} …" style="margin-top:8px;min-height:140px">${esc(s.draft || "")}</textarea>
        <div class="row">${s.ai ? (() => {
          // KI gesperrt (Option „KI-Funktionen erlauben“ aus): Bedienelemente ausgegraut + Tooltip;
          // die eigentliche Sperre liegt im Backend, das hier ist nur die Anzeige.
          const lock = !s.aiAllowed;
          const tip = esc(s.aiReason || t("KI in den Integrationsoptionen deaktiviert"));
          return `<select data-k="anlass" ${lock ? `disabled title="${tip}"` : ""}>${["antwort", "willkommen", "anreise", "abreise", "bewertung"].map((a) => `<option value="${a}">${a}</option>`).join("")}</select>
          <button class="btn flat ${lock ? "locked" : ""}" data-act="ai" ${s.thinking || lock ? "disabled" : ""} ${lock ? `title="${tip}"` : ""}>${lock ? `🔒 ${t("KI gesperrt")}` : s.thinking ? `⏳ ${t("KI denkt …")}` : `✨ ${t("Vorschlag")}`}</button>`; })() : ""}
          <span class="grow"></span><button class="btn" data-act="send">✉ ${t("Senden")}</button></div>`;
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
  static initialState = () => ({ tab: "wissen", edit: null, filter: "" });
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
          <select data-f="status">${["aktiv", "vorschlag", "aus"].map((x) => `<option ${x === w.status ? "selected" : ""}>${x}</option>`).join("")}</select>
          <span class="grow"></span><button class="btn flat" data-a="cancel">${t("Abbrechen")}</button><button class="btn" data-a="save">${t("Speichern")}</button></div></div>`
      : `<div class="kn ${w.status}" data-id="${w.id}"><div class="row"><span class="t grow">${esc(w.thema)}${w.vertraulich ? " 🔒" : ""}</span>
          ${w.status === "vorschlag" ? `<span class="badge warn">Vorschlag · ${esc(w.quelle)}</span><button class="btn" data-a="ok">✓ Freigeben</button>` : `<span class="badge">${w.status}</span>`}
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
        <span class="badge">${esc(st.ki || "keine KI")}</span></div>
      ${st.ki_erlaubt === false ? `<div class="lockinfo">🔒 ${esc(st.ki_sperre || t("KI in den Integrationsoptionen deaktiviert"))}.
        Wissensdatenbank, Lernen, Import, Tagesbriefing und Lücken funktionieren weiter – es gehen keine Daten an einen KI-Anbieter.</div>` : ""}
      ${st.fehler && st.ki_erlaubt !== false ? `<div class="err">Letzter Fehler: ${esc(st.fehler)}</div>` : ""}
      <div class="grid" style="margin-top:8px">
        ${tile("Offene Vorschläge", num(st.offen.length))}
        ${tile("Wissen", num(st.wissen.filter((w) => w.status === "aktiv").length), `${st.wissen.filter((w) => w.status === "vorschlag").length} zur Freigabe`)}
        ${tile("Lernbeispiele", num(st.beispiele_anzahl))}
        ${tile("Nicht buchbare Lücken", num(st.luecken.length))}
      </div>
      <div class="tabs">${[["wissen", "📚 Wissen"], ["vorschlaege", "✨ Vorschläge"], ["beispiele", "🎓 Gelernt"], ["luecken", "📅 Lücken"], ["import", "⬇ Import"]]
        .map(([k, l]) => `<button class="chip" data-tab="${k}" aria-pressed="${tab === k}">${l}</button>`).join("")}</div>`;
    let body = "";
    if (tab === "wissen") body = this.knowledge(st);
    if (tab === "vorschlaege") body = st.vorschlaege.map((v) => `<div class="ex click" data-bid="${v.buchung_id}">
        <div class="row"><b class="grow">${esc(v.gast || v.buchung_id)}</b>${v.dringend ? '<span class="badge bad">dringend</span>' : ""}
        <span class="badge">${esc(INTENT_LABEL[v.absicht] || v.absicht)}</span><span class="badge ${v.status === "offen" ? "warn" : ""}">${esc(v.status)}</span>
        <span class="sub">${fdate(v.erstellt, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</span></div>
        ${v.gastnachricht ? `<div class="g">„${esc(v.gastnachricht.slice(0, 300))}“</div>` : ""}<div class="a">➜ ${esc(v.antwort)}</div></div>`).join("")
      || `<div class="empty">${t("Keine Daten")}</div>`;
    if (tab === "beispiele") body = st.beispiele.slice(0, 60).map((b) => `<div class="ex"><div class="row"><span class="badge">${esc(b.quelle)}</span>
        <span class="sub grow">${esc(b.kanal || "")} · ${esc(b.sprache || "")}</span><button class="btn flat" data-del-ex="${b.id}">🗑</button></div>
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
    root.querySelectorAll("[data-bid]").forEach((el) => el.addEventListener("click", () => this.openBooking(Number(el.dataset.bid))));
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
// Kopfleiste (v1.15.0): Seiten-Navigation, Wohnungsauswahl, Hell/Dunkel/System
// ===========================================================================
// Eine Karte oben auf jeder Smoobu-Seite. Die Seitenpfade sind relativ zum
// aktuellen Dashboard (z. B. „smoobu-belegung“ → /dashboard-x/smoobu-belegung).
// Zusätzlich färbt sie den Seitenhintergrund passend zum gewählten Modus,
// damit zwischen den Karten keine helle HA-Fläche im Dunkelmodus bleibt.
const DEFAULT_PAGES = [
  { name: "Übersicht", path: "smoobu" }, { name: "Belegung", path: "smoobu-belegung" },
  { name: "Buchungen", path: "smoobu-buchungen" }, { name: "Finanzen", path: "smoobu-finanzen" },
  { name: "Nachrichten", path: "smoobu-nachrichten", badge: "nachrichten" }, { name: "Assistent", path: "smoobu-assistent" },
];
const ICON_SVG = {
  hell: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>`,
  dunkel: `<svg viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>`,
  system: `<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg>`,
};
class SmoobuHeaderCard extends SmoobuCard {
  static defaults = { pages: DEFAULT_PAGES, show_apartments: true, page_background: true };
  static css = `
    ha-card { background: none; border: 0; padding: 14px 0 2px; overflow: visible; } /* Abstand zur HA-Kopfzeile */
    .bar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
    .tabs { display: flex; gap: 4px; flex-wrap: wrap; }
    .tabs a { padding: 8px 15px; border-radius: 999px; color: var(--sm-muted); font-weight: 500; text-decoration: none; cursor: pointer;
      display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
    .tabs a:hover { color: var(--sm-ink); background: color-mix(in srgb, var(--sm-ink) 6%, transparent); }
    .tabs a.on { background: var(--sm-accent); color: var(--sm-acc-ink); font-weight: 600; }
    .tabs i { font-style: normal; font-size: .7rem; font-weight: 700; background: var(--sm-bad); color: #fff; border-radius: 9px; padding: 0 6px; line-height: 1.5; }
    .right { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .seg button { display: inline-flex; gap: 6px; align-items: center; }
    .seg.theme button[aria-pressed="true"] { background: var(--sm-accent); color: var(--sm-acc-ink); }
    .seg svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
    .seg .n { opacity: .7; margin-left: 2px; }
    @media (max-width: 700px) { .seg .lbl { display: none; } }
  `;
  async load() {
    const info = await this.store.getInfo();
    let open = 0;
    if ((this._config.pages || []).some((p) => p.badge === "nachrichten")) {
      try {
        const list = await this.store.ws("smoobu/bookings", { ...this.target, start: iso(addDays(D(info.heute), -14)), end: iso(addDays(D(info.heute), 60)) });
        const ids = list.buchungen.filter((b) => !b.blockiert && !b.storniert && b.status !== "vergangen").slice(0, 60).map((b) => b.id);
        if (ids.length) {
          const st = (await this.store.ws("smoobu/message_status", { ...this.target, reservation_ids: ids })).status || {};
          open = Object.values(st).filter((x) => x.offen).length;
        }
      } catch (e) { open = 0; }
    }
    return { info, open };
  }
  href(path) {
    if (path.startsWith("/")) return path;
    const parts = location.pathname.split("/").filter(Boolean);
    return `/${parts[0] || "lovelace"}/${path}`;
  }
  body({ info, open }) {
    const here = location.pathname.split("/").filter(Boolean).pop();
    const tabs = (this._config.pages || []).map((p) => `<a class="${p.path === here ? "on" : ""}" data-href="${esc(this.href(p.path))}">${esc(t(p.name))}${p.badge === "nachrichten" && open ? `<i>${open}</i>` : ""}</a>`).join("");
    const ws = info.wohnungen;
    const sel = this.target.apartment_id;
    const apts = this._config.show_apartments && ws.length > 1 && !this._config.apartment_id
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
  disconnectedCallback() { this._restoreBg(); super.disconnectedCallback(); }
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
// Registrierung
// ===========================================================================
const CARDS = [
  ["smoobu-header-card", SmoobuHeaderCard, "Smoobu Kopfleiste", "Seiten-Navigation, Wohnungsauswahl und Hell/Dunkel/System"],
  ["smoobu-overview-card", SmoobuOverviewCard, "Smoobu Übersicht", "Status, Gäste, Kennzahlen, Lücken, offene Zahlungen"],
  ["smoobu-timeline-card", SmoobuTimelineCard, "Smoobu Belegungsplan", "Belegung mit Preisen und Mindestaufenthalt; sperren und Preise setzen"],
  ["smoobu-bookings-card", SmoobuBookingsCard, "Smoobu Buchungen", "Buchungsliste mit Suche, Filtern, Summen und CSV-Export"],
  ["smoobu-analytics-card", SmoobuAnalyticsCard, "Smoobu Finanzen", "Umsatz, Kosten und Kennzahlen je Kanal, frei filterbar mit Vergleich"],
  ["smoobu-inbox-card", SmoobuInboxCard, "Smoobu Posteingang", "Nachrichten der Gäste lesen und beantworten"],
  ["smoobu-assistant-card", SmoobuAssistantCard, "Smoobu Assistent", "KI-Assistent: Wissensdatenbank, Lernbeispiele, Vorschläge"],
];
for (const [tag, cls] of CARDS) if (!customElements.get(tag)) customElements.define(tag, cls);
if (!customElements.get("smoobu-booking-dialog")) customElements.define("smoobu-booking-dialog", SmoobuBookingDialog);
window.customCards = window.customCards || [];
for (const [type, , name, description] of CARDS) {
  if (!window.customCards.some((c) => c.type === type)) window.customCards.push({ type, name, description, preview: false });
}
console.info(`%c SMOOBU-CARDS %c ${SMOOBU_CARDS_VERSION} `, "background:#17211D;color:#fff;padding:2px 4px;border-radius:3px 0 0 3px",
  "background:#2F6B4F;color:#fff;padding:2px 4px;border-radius:0 3px 3px 0");

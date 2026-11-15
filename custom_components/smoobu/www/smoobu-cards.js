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

const SMOOBU_CARDS_VERSION = "1.13.0";

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
  :host { display: block; --sm-gap: 12px; --sm-radius: var(--ha-card-border-radius, 12px);
    --sm-muted: var(--secondary-text-color); --sm-line: var(--divider-color, rgba(127,127,127,.2));
    --sm-good: var(--success-color, #2e9e5b); --sm-bad: var(--error-color, #db4437);
    --sm-warn: var(--warning-color, #f2a900); --sm-accent: var(--primary-color); }
  ha-card { padding: 16px; overflow: hidden; }
  h2 { margin: 0 0 4px; font-size: 1.25rem; font-weight: 500; display: flex; align-items: center; gap: 8px; }
  h3 { margin: 16px 0 8px; font-size: .95rem; font-weight: 600; color: var(--sm-muted); text-transform: uppercase; letter-spacing: .04em; }
  .sub { color: var(--sm-muted); font-size: .85rem; }
  .row { display: flex; gap: var(--sm-gap); flex-wrap: wrap; align-items: center; }
  .grow { flex: 1 1 auto; }
  .grid { display: grid; gap: var(--sm-gap); grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
  .tile { background: var(--secondary-background-color, rgba(127,127,127,.08)); border-radius: 10px; padding: 10px 12px; min-width: 0; }
  .tile .l { font-size: .78rem; color: var(--sm-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .tile .v { font-size: 1.35rem; font-weight: 600; margin-top: 2px; white-space: nowrap; }
  .tile .s { font-size: .78rem; color: var(--sm-muted); margin-top: 2px; }
  .delta { font-size: .75rem; font-weight: 600; padding: 1px 5px; border-radius: 6px; white-space: nowrap; }
  .delta.up { color: var(--sm-good); background: color-mix(in srgb, var(--sm-good) 14%, transparent); }
  .delta.down { color: var(--sm-bad); background: color-mix(in srgb, var(--sm-bad) 14%, transparent); }
  .delta.flat { color: var(--sm-muted); }
  .chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 16px; font-size: .82rem;
    border: 1px solid var(--sm-line); background: none; color: var(--primary-text-color); cursor: pointer; font: inherit; font-size: .82rem; }
  .chip[aria-pressed="true"] { background: color-mix(in srgb, var(--sm-accent) 18%, transparent); border-color: var(--sm-accent); }
  .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex: none; }
  .badge { display: inline-flex; align-items: center; gap: 4px; font-size: .75rem; padding: 2px 8px; border-radius: 10px;
    background: var(--secondary-background-color, rgba(127,127,127,.12)); }
  .badge.good { background: color-mix(in srgb, var(--sm-good) 18%, transparent); color: var(--sm-good); }
  .badge.bad { background: color-mix(in srgb, var(--sm-bad) 18%, transparent); color: var(--sm-bad); }
  .badge.warn { background: color-mix(in srgb, var(--sm-warn) 22%, transparent); }
  select, input, textarea { font: inherit; color: var(--primary-text-color); background: var(--card-background-color);
    border: 1px solid var(--sm-line); border-radius: 8px; padding: 6px 8px; }
  textarea { width: 100%; box-sizing: border-box; min-height: 70px; resize: vertical; }
  button.btn { font: inherit; border: none; border-radius: 8px; padding: 7px 14px; cursor: pointer;
    background: var(--sm-accent); color: var(--text-primary-color, #fff); }
  button.btn.flat { background: none; color: var(--sm-accent); border: 1px solid var(--sm-line); }
  button.btn.danger { background: var(--sm-bad); }
  button.btn:disabled { opacity: .5; cursor: default; }
  table { width: 100%; border-collapse: collapse; font-size: .85rem; }
  th, td { padding: 6px 8px; text-align: left; border-bottom: 1px solid var(--sm-line); white-space: nowrap; }
  th { font-weight: 600; color: var(--sm-muted); font-size: .75rem; text-transform: uppercase; cursor: pointer; user-select: none; }
  td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
  tr.click { cursor: pointer; } tr.click:hover td { background: var(--secondary-background-color, rgba(127,127,127,.06)); }
  tfoot td { font-weight: 600; border-bottom: none; }
  .scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .empty { color: var(--sm-muted); padding: 16px 0; text-align: center; }
  .err { color: var(--sm-bad); padding: 8px 0; }
  .list > div { padding: 8px 0; border-bottom: 1px solid var(--sm-line); display: flex; gap: 10px; align-items: center; }
  .list > div:last-child { border-bottom: none; }
  .list .click { cursor: pointer; }
  .muted { color: var(--sm-muted); }
  ha-icon { --mdc-icon-size: 18px; }
  .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 8px 0 12px; }
  .toast { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); background: var(--primary-text-color);
    color: var(--card-background-color); padding: 8px 16px; border-radius: 8px; z-index: 10001; font-size: .9rem; }
`;

function toast(msg) {
  const el = document.createElement("div");
  el.style.cssText = "position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#323232;color:#fff;" +
    "padding:10px 18px;border-radius:8px;z-index:10001;font:14px Roboto,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.3)";
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
      this._unsub = this.store.subscribe(() => this._reload());
      this._reload();
    } else if (this.onHass) {
      this.onHass();
    }
  }
  get hass() { return this._hass; }
  disconnectedCallback() { this._unsub?.(); this._unsub = null; this._hass && (this._rebind = true); }
  connectedCallback() {
    if (this._rebind && this._hass) { this._rebind = false; this._unsub = this.store.subscribe(() => this._reload()); this._reload(); }
  }
  get target() {
    const t = {};
    if (this._config?.entry_id) t.entry_id = this._config.entry_id;
    if (this._config?.apartment_id) t.apartment_id = Number(this._config.apartment_id);
    return t;
  }
  async apartment() {
    const info = await this.store.getInfo();
    const id = this._config?.apartment_id ? Number(this._config.apartment_id) : null;
    return info.wohnungen.find((w) => id === null || w.apartment_id === id) || info.wohnungen[0];
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
    this.shadowRoot.innerHTML = `<style>${BASE_CSS}${this.constructor.css || ""}</style><ha-card>${body}</ha-card>`;
    if (scroll) { const s = this.shadowRoot.querySelector(".scroll"); if (s) s.scrollLeft = scroll; }
    this.bind?.(this.shadowRoot);
  }
  $(sel) { return this.shadowRoot.querySelector(sel); }
  $$(sel) { return [...this.shadowRoot.querySelectorAll(sel)]; }
  openBooking(id) { SmoobuBookingDialog.open(this._hass, id, this.target); }
  getCardSize() { return 6; }
  getGridOptions() { return { columns: 12, min_columns: 6 }; }
}

// Kleine Bausteine
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
    chips.push(`<button class="chip" data-ch="${esc(ch.name)}" aria-pressed="${sel.has(ch.name)}"><span class="dot" style="background:${colors[ch.name] || ch.farbe}"></span>${esc(ch.name)}</button>`);
  }
  return chips.join("");
}
function toggleChannel(list, ch) {
  if (!ch) return [];
  const s = new Set(list || []);
  s.has(ch) ? s.delete(ch) : s.add(ch);
  return [...s];
}
function colorOf(apt, name, blocked = false) {
  if (blocked) return "#9E9E9E";
  return apt?.kanaele.find((c) => c.name === name)?.farbe || "#00A6A6";
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

// ===========================================================================
// Übersicht
// ===========================================================================
class SmoobuOverviewCard extends SmoobuCard {
  static defaults = { title: "", entities: [], upcoming: 5, gap_days: 60 };
  static css = `
    .hero { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--sm-gap); margin: 12px 0; }
    .guest { border-radius: 12px; padding: 12px 14px; border-left: 5px solid var(--c, var(--sm-accent));
      background: var(--secondary-background-color, rgba(127,127,127,.08)); cursor: pointer; }
    .guest .n { font-size: 1.2rem; font-weight: 600; } .guest .m { color: var(--sm-muted); font-size: .85rem; margin-top: 4px; }
    .status { font-size: .9rem; padding: 4px 12px; border-radius: 14px; font-weight: 600; }
    .status.on { background: color-mix(in srgb, var(--sm-warn) 25%, transparent); }
    .status.off { background: color-mix(in srgb, var(--sm-good) 20%, transparent); color: var(--sm-good); }
    .today { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
    .cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 4px 24px; }
    /* v1.10.2: Abstand nach oben – in Panel-Ansichten klebt die Karte sonst an der Kopfzeile */
    :host { padding-top: 8px; }
    .cmpnote { font-size: .72rem; color: var(--sm-muted); margin-top: 6px; }
    .ent { display: inline-flex; gap: 6px; align-items: center; font-size: .82rem; padding: 4px 10px; border-radius: 14px;
      background: var(--secondary-background-color, rgba(127,127,127,.1)); cursor: pointer; }
  `;
  async load() {
    const apt = await this.apartment();
    const info = await this.store.getInfo();
    const today = info.heute;
    const tg = this.target;
    const [month, ytd, list, rates] = await Promise.all([
      this.store.ws("smoobu/analytics", { ...tg, period: "monat", compare: "vorjahr_stand" }),
      this.store.ws("smoobu/analytics", { ...tg, period: "jahr_bis_heute", compare: "vorjahr" }),
      this.store.ws("smoobu/bookings", { ...tg, start: iso(addDays(D(today), -1)), end: iso(addDays(D(today), 180)) }),
      this.store.ws("smoobu/rates", { ...tg, start: today, end: iso(addDays(D(today), this._config.gap_days + 21)) }).catch(() => ({ preise: {} })),
    ]);
    return { apt, today, month, ytd, bookings: list.buchungen, rates: rates.preise };
  }
  body({ apt, today, month, ytd, bookings, rates }) {
    const cur = apt.currency;
    const guests = bookings.filter((b) => !b.blockiert && !b.storniert);
    const staying = guests.find((b) => b.anreise <= today && b.abreise > today);
    // Nach der Freigabe am Abreisetag: abgereisten Gast noch zeigen, aber so benennen
    const current = staying || guests.find((b) => b.abreise === today);
    const arrivals = guests.filter((b) => b.anreise === today);
    const departures = guests.filter((b) => b.abreise === today);
    const next = guests.filter((b) => b.anreise > today).slice(0, this._config.upcoming);
    const occupied = guests.some((b) => b.anreise <= today && b.abreise > today);
    const nextGuest = guests.find((b) => b.anreise > today);
    const freeFrom = current ? current.abreise : null;
    const gaps = findGaps(bookings, rates, today, this._config.gap_days);
    const unpaid = guests.filter((b) => b.offen > 0 && b.status !== "vergangen");
    const days = (b) => nightsBetween(today, b.anreise);
    const guestCard = (b, label) => b ? `<div class="guest" data-id="${b.id}" style="--c:${colorOf(apt, b.kanal)}">
        <div class="sub">${t(label)}</div><div class="n">${esc(b.gast || "–")}${b.hund ? " 🐕" : ""}</div>
        <div class="m">${fdow(b.anreise)} → ${fdow(b.abreise)} · ${b.naechte} ${t("Nächte")} · ${b.personen} ${t("Personen")}</div>
        <div class="m"><span class="dot" style="background:${colorOf(apt, b.kanal)}"></span> ${esc(b.kanal)} · ${money(b.brutto, cur)}
          ${b.check_in ? ` · ${t("Ankunft")} ${esc(b.check_in)}` : ""}${label === "Nächster Gast" ? ` · ${days(b) === 1 ? t("morgen") : `in ${days(b)} ${t("Tage")}`}` : ""}</div>
      </div>` : "";
    const ents = (this._config.entities || []).map((e) => {
      const id = typeof e === "string" ? e : e.entity;
      const st = this._hass.states[id];
      if (!st) return "";
      const name = (typeof e === "object" && e.name) || st.attributes.friendly_name || id;
      const val = this._hass.formatEntityState ? this._hass.formatEntityState(st) : st.state;
      return `<span class="ent" data-entity="${esc(id)}"><ha-icon icon="${esc(st.attributes.icon || "mdi:information-outline")}"></ha-icon><b>${esc(name)}</b> ${esc(val)}</span>`;
    }).join("");
    const m = month, y = ytd;
    return `
      <div class="row"><h2 class="grow">${esc(this._config.title || apt.name)}</h2>
        <span class="status ${occupied ? "on" : "off"}">${occupied ? `${t("Belegt")} · ${t("frei ab")} ${fdate(freeFrom)}` : t("Frei")}</span></div>
      <div class="today">
        ${/* v1.10.2: nur noch Ereignisse von heute (Anreise, Abreise, Reinigung); Hund als 🐕 am Namen */ ""}
        ${arrivals.length ? `<span class="badge warn">🛬 ${t("Anreise heute")}: ${arrivals.map((b) => esc(b.gast) + (b.hund ? " 🐕" : "") + (b.check_in ? ` ${esc(b.check_in)}` : "")).join(", ")}</span>` : ""}
        ${departures.length ? `<span class="badge warn">🛫 ${t("Abreise heute")}: ${departures.map((b) => esc(b.gast)).join(", ")}</span>` : ""}
        ${departures.length ? `<span class="badge ${arrivals.length ? "bad" : ""}">🧹 ${t("Reinigung heute")}${arrivals.length && arrivals[0].check_in ? ` ${t("bis")} ${esc(arrivals[0].check_in)}` : ""}</span>` : ""}
        ${arrivals.length && departures.length ? `<span class="badge bad">🔄 ${t("Gästewechsel heute")}</span>` : ""}
        ${ents}
      </div>
      <div class="hero">${guestCard(current, staying ? "Aktueller Gast" : "Heute abgereist")}${guestCard(nextGuest, "Nächster Gast")}</div>
      <div class="grid">
        ${tile(`${t("Monat")} ${t("Brutto")}`, money(m.brutto, cur), `${t("Netto")} ${money(m.netto, cur)} ${delta(m.veraenderung_prozent?.brutto)}`)}
        ${tile(t("Auslastung"), pct(m.auslastung_prozent, 0), `${m.naechte} ${t("Nächte")} ${delta(m.veraenderung_punkte?.auslastung_prozent, "pp")}`)}
        ${tile(t("Jahr bis heute"), money(y.brutto, cur), `${t("Netto")} ${money(y.netto, cur)} ${delta(y.veraenderung_prozent?.brutto)}`)}
        ${tile(t("Prognose Jahr"), money(y.prognose?.prognose, cur), `${t("gebucht")} ${money(y.prognose?.gebucht, cur)}`)}
        ${tile(t("Netto/Nacht"), money(y.netto_pro_nacht, cur), `${t("Vorjahr")} ${money(y.vergleich?.netto_pro_nacht, cur)}`)}
        ${tile(t("Direktanteil"), pct(y.direktanteil_prozent, 0), delta(y.veraenderung_punkte?.direktanteil_prozent, "pp"))}
      </div>
      <div class="cmpnote">${t("Vergleich")}: ${t("Monat ggü. Buchungsstand am")} ${fdate(m.stichtag_vergleich)} ·
        ${t("Jahr ggü.")} ${fdate(y.vergleich?.von)} – ${fdate(iso(addDays(D(y.vergleich?.bis || today), -1)))} · ${t("PP = Prozentpunkte")}</div>
      <div class="cols">
        <div><h3>${t("Nächste Anreisen")}</h3><div class="list">
          ${next.map((b) => `<div class="click" data-id="${b.id}"><span class="dot" style="background:${colorOf(apt, b.kanal)}"></span>
            <div class="grow"><b>${esc(b.gast)}</b>${b.hund ? " 🐕" : ""}<div class="sub">${fdow(b.anreise)} – ${fdow(b.abreise)} · ${b.naechte} N · ${b.personen} P · ${esc(b.kanal)}</div></div>
            <div class="n">${money(b.brutto, cur)}</div></div>`).join("") || `<div class="muted">${t("keine")}</div>`}
        </div></div>
        <div><h3>${t("Lücken")} (${this._config.gap_days} ${t("Tage")})</h3><div class="list">
          ${gaps.map((g) => `<div><ha-icon icon="mdi:calendar-blank-outline"></ha-icon><div class="grow"><b>${fdow(g.von)} – ${fdow(g.bis)}</b>
            <div class="sub">${g.naechte} ${t("Nächte")}${g.preis ? ` · ${money(g.preis, cur)}/${t("Nacht")}` : ""}${g.min ? ` · min. ${g.min}` : ""}</div></div>
            ${g.buchbar ? `<span class="badge good">✓</span>` : `<span class="badge bad">${t("nicht buchbar")}</span>`}</div>`).join("") || `<div class="muted">${t("keine")}</div>`}
          </div>
          <h3>${t("Offene Zahlungen")}</h3><div class="list">
          ${unpaid.map((b) => `<div class="click" data-id="${b.id}"><ha-icon icon="mdi:cash-clock"></ha-icon><div class="grow"><b>${esc(b.gast)}</b>
            <div class="sub">${fdate(b.anreise)} · ${esc(b.kanal)}</div></div><span class="badge bad">${money(b.offen, cur, 2)}</span></div>`).join("") || `<div class="muted">${t("keine")}</div>`}
        </div></div>
      </div>`;
  }
  bind(root) {
    root.querySelectorAll("[data-id]").forEach((el) => el.addEventListener("click", () => this.openBooking(Number(el.dataset.id))));
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
  static initialState = () => ({ offset: 0, selStart: null, selEnd: null, panel: null });
  static css = `
    .months { min-width: 900px; }
    .month { display: grid; grid-template-columns: 64px 1fr; align-items: stretch; border-bottom: 1px solid var(--sm-line); }
    .ml { font-weight: 600; font-size: .85rem; padding-top: 6px; text-transform: capitalize; }
    .days { position: relative; display: grid; grid-template-columns: repeat(31, 1fr); }
    .c { height: 64px; border-left: 1px solid var(--sm-line); font-size: .68rem; padding: 2px 2px 0; box-sizing: border-box;
      cursor: pointer; position: relative; color: var(--sm-muted); user-select: none; }
    .c.we { background: color-mix(in srgb, var(--sm-muted) 7%, transparent); }
    .c.today { box-shadow: inset 0 0 0 2px var(--sm-accent); }
    .c.past { opacity: .55; }
    .c.sel { background: color-mix(in srgb, var(--sm-accent) 22%, transparent); }
    .c.badgap { background: repeating-linear-gradient(45deg, color-mix(in srgb, var(--sm-bad) 16%, transparent) 0 4px, transparent 4px 8px); }
    .c.none { cursor: default; background: none; border-left-color: transparent; }
    .c .d { font-weight: 600; color: var(--primary-text-color); }
    .c .p { position: absolute; bottom: 2px; left: 2px; right: 2px; text-align: center; font-variant-numeric: tabular-nums; }
    .c .ms { position: absolute; bottom: 14px; left: 2px; right: 2px; text-align: center; font-size: .6rem; }
    .bar { position: absolute; top: 22px; height: 20px; border-radius: 10px; color: #fff; font-size: .72rem; line-height: 20px;
      padding: 0 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; box-sizing: border-box;
      box-shadow: 0 1px 2px rgba(0,0,0,.25); }
    .bar.cl { border-top-left-radius: 0; border-bottom-left-radius: 0; }
    .bar.cr { border-top-right-radius: 0; border-bottom-right-radius: 0; }
    .bar.blocked { background: repeating-linear-gradient(45deg, #9e9e9e 0 6px, #8a8a8a 6px 12px) !important; }
    .legend { display: flex; flex-wrap: wrap; gap: 10px; font-size: .78rem; color: var(--sm-muted); margin-top: 10px; }
    .panel { margin-top: 12px; padding: 12px; border-radius: 10px; border: 1px solid var(--sm-accent);
      display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
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
    const [list, rates] = await Promise.all([
      this.store.ws("smoobu/bookings", { ...tg, start: iso(start), end: iso(end) }),
      this._config.show_prices && rs < end
        ? this.store.ws("smoobu/rates", { ...tg, start: iso(rs), end: iso(addDays(end, 21)) }).catch(() => ({ preise: {} }))
        : Promise.resolve({ preise: {} }),
    ]);
    return { apt, today, start, end, bookings: list.buchungen.filter((b) => !b.storniert), rates: rates.preise };
  }
  body({ apt, today, start, end, bookings, rates }) {
    const cur = apt.currency;
    const { selStart, selEnd } = this._state;
    const lo = selStart && selEnd ? (selStart < selEnd ? selStart : selEnd) : selStart;
    const hi = selStart && selEnd ? (selStart < selEnd ? selEnd : selStart) : selStart;
    // Nächte in Lücken, die wegen Mindestaufenthalt nicht buchbar sind
    const bad = new Set();
    for (const g of findGaps(bookings, rates, iso(D(today) > start ? D(today) : start), Math.max(nightsBetween(iso(start), iso(end)), 1))) {
      if (!g.buchbar) for (let d = D(g.von); d < D(g.bis); d = addDays(d, 1)) bad.add(iso(d));
    }
    const rows = [];
    for (let m = new Date(start); m < end; m = addMonths(m, 1)) {
      const dim = new Date(m.getFullYear(), m.getMonth() + 1, 0).getDate();
      const mStart = iso(m), mEnd = iso(addMonths(m, 1));
      let cells = "";
      for (let i = 1; i <= 31; i++) {
        if (i > dim) { cells += `<div class="c none"></div>`; continue; }
        const day = new Date(m.getFullYear(), m.getMonth(), i);
        const ds = iso(day);
        const r = rates[ds];
        const cls = ["c", day.getDay() % 6 === 0 ? "we" : "", ds === today ? "today" : "", ds < today ? "past" : "",
          lo && ds >= lo && ds <= (hi || lo) ? "sel" : "", bad.has(ds) ? "badgap" : ""].join(" ");
        const wd = day.toLocaleDateString(locale(), { weekday: "narrow" });
        cells += `<div class="${cls}" data-day="${ds}"><span class="d">${i}</span> ${wd}
          ${r && r.min_length_of_stay > 1 ? `<div class="ms">☾${r.min_length_of_stay}</div>` : ""}
          ${r && r.price ? `<div class="p">${num(r.price)}</div>` : ""}</div>`;
      }
      let bars = "";
      for (const b of bookings) {
        if (b.abreise <= mStart || b.anreise >= mEnd) continue;
        const a = D(b.anreise), d = D(b.abreise);
        const cutL = b.anreise < mStart, cutR = b.abreise > mEnd;
        const left = cutL ? 0 : (a.getDate() - 1 + 0.55) / 31;
        const right = cutR ? dim / 31 : Math.min((b.abreise === mEnd ? dim + 0.45 : d.getDate() - 1 + 0.45) / 31, 1);
        const label = b.blockiert ? `🔒 ${t("Gesperrt")}${b.notiz ? " · " + esc(b.notiz) : ""}` : `${esc(b.gast || "")}${b.hund ? " 🐕" : ""} · ${b.personen}P`;
        bars += `<div class="bar ${b.blockiert ? "blocked" : ""} ${cutL ? "cl" : ""} ${cutR ? "cr" : ""}" data-id="${b.id}"
          title="${esc(b.blockiert ? t("Sperrzeit") : `${b.gast} · ${b.kanal} · ${money(b.brutto, cur)}`)}"
          style="left:calc(${(left * 100).toFixed(3)}%);width:calc(${((right - left) * 100).toFixed(3)}%);background:${colorOf(apt, b.kanal)}">${label}</div>`;
      }
      rows.push(`<div class="month"><div class="ml">${m.toLocaleDateString(locale(), MONTH_FMT)}</div><div class="days">${cells}${bars}</div></div>`);
    }
    const nights = lo ? nightsBetween(lo, hi || lo) + 1 : 0;
    const p = this._state.panel;
    const panel = !this._config.actions ? "" : lo ? `<div class="panel">
        <b>${t("Auswahl")}: ${fdow(lo)} – ${fdow(hi || lo)} (${nights} ${t("Nächte")})</b>
        ${p === "block" ? `<input data-k="notice" placeholder="${t("Grund (optional)")}" style="width:180px">
            <button class="btn" data-act="do-block">${t("Sperren")}</button>`
          : p === "rate" ? `<label>${t("Preis/Nacht")} <input data-k="price" type="number" min="1" step="1"></label>
            <label>${t("Mindestaufenthalt")} <input data-k="min" type="number" min="1" max="90" style="width:70px"></label>
            <button class="btn" data-act="do-rate">${t("Speichern")}</button>`
          : `<button class="btn" data-act="block">🔒 ${t("Sperren")}</button><button class="btn" data-act="rate">€ ${t("Preis setzen")}</button>`}
        <button class="btn flat" data-act="clear">${t("Abbrechen")}</button></div>`
      : `<div class="legend">${t("Tage markieren: erst ersten, dann letzten Tag antippen")}</div>`;
    return `
      <div class="row"><h2 class="grow">${esc(this._config.title || t("Belegungsplan"))}</h2>
        <button class="btn flat" data-act="prev">◀</button><button class="btn flat" data-act="now">${t("Heute")}</button>
        <button class="btn flat" data-act="next">▶</button></div>
      <div class="scroll"><div class="months">${rows.join("")}</div></div>
      <div class="legend">${apt.kanaele.map((c) => `<span><span class="dot" style="background:${c.farbe}"></span> ${esc(c.name)}</span>`).join("")}
        <span><span class="dot" style="background:#9e9e9e"></span> ${t("Gesperrt")}</span>
        <span><span class="dot" style="background:var(--sm-bad)"></span> ${t("nicht buchbar")} (${t("Mindestaufenthalt zu hoch")})</span>
        ${this._config.show_prices ? `<span>${t("Preis/Nacht")} · ☾ ${t("Mindestaufenthalt")}</span>` : ""}</div>
      ${panel}`;
  }
  bind(root) {
    root.querySelectorAll(".bar").forEach((el) => el.addEventListener("click", (e) => { e.stopPropagation(); this.openBooking(Number(el.dataset.id)); }));
    if (this._config.actions) root.querySelectorAll(".c[data-day]").forEach((el) => el.addEventListener("click", () => {
      const d = el.dataset.day;
      const { selStart, selEnd } = this._state;
      if (!selStart || selEnd) this.setState({ selStart: d, selEnd: null, panel: null });
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
    const apt = await this.apartment();
    try {
      if (a === "do-block") {
        const notice = this.$('[data-k="notice"]')?.value || undefined;
        if (!(await confirmDialog(`${t("Sperren")}: ${fdate(lo)} – ${fdate(hi)}?`))) return;
        await this.store.service("block_period", { apartment_id: apt.apartment_id, start_date: lo, end_date: iso(addDays(D(hi), 1)), ...(notice ? { notice } : {}) });
      } else if (a === "do-rate") {
        const price = this.$('[data-k="price"]')?.value, min = this.$('[data-k="min"]')?.value;
        if (!price && !min) return;
        if (!(await confirmDialog(`${t("Preis setzen")}: ${fdate(lo)} – ${fdate(hi)}${price ? ` · ${price} €` : ""}${min ? ` · ☾${min}` : ""}?`))) return;
        await this.store.service("set_rates", { apartment_id: apt.apartment_id, start_date: lo, end_date: hi,
          ...(price ? { price: Number(price) } : {}), ...(min ? { min_stay: Number(min) } : {}) });
      }
      toast(t("Gespeichert"));
      this.setState({ selStart: null, selEnd: null, panel: null }, true);
    } catch (e) {
      toast(`${t("Fehler")}: ${e.message || e}`);
    }
  }
}

// Bestätigungsdialog (eigener, damit er über allen HA-Dialogen liegt)
function confirmDialog(text) {
  return new Promise((resolve) => {
    const wrap = document.createElement("div");
    wrap.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10002;display:flex;align-items:center;justify-content:center";
    wrap.innerHTML = `<div style="background:var(--card-background-color,#fff);color:var(--primary-text-color,#000);padding:20px;border-radius:12px;max-width:360px;font:15px Roboto,sans-serif">
      <div style="margin-bottom:16px">${esc(text)}</div><div style="display:flex;gap:8px;justify-content:flex-end">
      <button data-v="0" style="padding:8px 14px;border-radius:8px;border:1px solid #999;background:none;color:inherit;cursor:pointer">${t("Nein")}</button>
      <button data-v="1" style="padding:8px 14px;border-radius:8px;border:none;background:var(--primary-color,#03a9f4);color:#fff;cursor:pointer">${t("Ja")}</button></div></div>`;
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
    rows = rows.map((b) => ({ ...b, kosten: Math.round((b.provision + b.zahlungsgebuehr) * 100) / 100 }));
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
    const head = BOOKING_COLS.map(([k, l, n]) => `<th class="${n || ""}" data-sort="${k}">${t(l)}${s.sort === k ? (s.dir > 0 ? " ▲" : " ▼") : ""}</th>`).join("");
    const body = rows.map((b) => `<tr class="click ${b.storniert ? "cx" : ""} ${b.blockiert ? "bl" : ""}" data-id="${b.id}">
      <td class="st"><ha-icon icon="${STATUS_ICON[b.status]}" title="${t(b.status)}"></ha-icon></td>
      <td>${fdow(b.anreise)}</td><td>${fdow(b.abreise)}</td><td class="n">${b.naechte}</td>
      <td>${b.blockiert ? `🔒 ${esc(b.notiz || t("Gesperrt"))}` : esc(b.gast)}${b.hund ? " 🐕" : ""}</td>
      <td class="n">${b.blockiert ? "" : b.personen}</td>
      <td><span class="dot" style="background:${colorOf(apt, b.kanal, b.blockiert)}"></span>${esc(b.kanal)}</td>
      <td class="n">${b.blockiert ? "" : money(b.brutto, cur, 2)}</td><td class="n">${b.blockiert ? "" : money(b.kosten, cur, 2)}</td>
      <td class="n">${b.blockiert ? "" : money(b.netto, cur, 2)}</td><td class="n">${b.netto_pro_nacht ? money(b.netto_pro_nacht, cur) : ""}</td>
      <td class="n">${b.offen > 0 ? `<span class="badge bad">${money(b.offen, cur, 2)}</span>` : ""}</td>
      <td class="n">${b.vorlauf_tage ?? ""}</td></tr>`).join("");
    return `
      <div class="row"><h2 class="grow">${esc(this._config.title || t("Buchungen"))}</h2>
        <button class="btn flat" data-act="csv">⬇ ${t("Export CSV")}</button></div>
      <div class="toolbar">
        <input type="search" data-k="search" placeholder="${t("Suche")} (Name, E-Mail, Telefon, Notiz …)" value="${esc(s.search)}">
        ${periodSelect(s.period)}
        ${s.period === "custom" ? `<input type="date" data-k="from" value="${s.from || ""}"> – <input type="date" data-k="to" value="${s.to || ""}">` : ""}
      </div>
      <div class="toolbar">${channelChips(apt, s.channels)}</div>
      <div class="toolbar">${statusChips}</div>
      <div class="scroll"><table><thead><tr>${head}</tr></thead><tbody>${body || `<tr><td colspan="13" class="empty">${t("Keine Daten")}</td></tr>`}</tbody>
      <tfoot><tr><td colspan="3">${t("Summe")} · ${valid.length} ${t("Buchungen")}</td><td class="n">${num(sum("naechte"))}</td><td></td>
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
      const cols = ["id", "status", "anreise", "abreise", "naechte", "gast", "email", "telefon", "personen", "erwachsene", "kinder",
        "kanal", "gruppe", "brutto", "provision", "zahlungsgebuehr", "netto", "netto_pro_nacht", "offen", "bezahlt", "vorlauf_tage",
        "erstellt", "hund", "notiz"];
      downloadCsv(`smoobu-buchungen-${iso(new Date())}.csv`, [cols, ...(this._rows || []).map((b) => cols.map((c) => b[c]))]);
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
      svg += `<rect x="${x + bw * 0.14}" y="${y1}" width="${bw * 0.72}" height="${Math.max(y0 - y1, 0)}" fill="${s.color}" rx="2"/>`;
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
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block;color:var(--primary-text-color)" role="img">${svg}</svg>`;
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
    .bar-in { height: 6px; border-radius: 3px; background: var(--sm-accent); }
    .tip { min-height: 1.2em; font-size: .82rem; color: var(--sm-muted); margin-top: 4px; }
    .ins li { margin: 4px 0; } .ins { padding-left: 18px; margin: 4px 0; }
    .seg { display: inline-flex; border: 1px solid var(--sm-line); border-radius: 8px; overflow: hidden; }
    .seg button { border: none; background: none; padding: 5px 10px; font: inherit; font-size: .82rem; cursor: pointer; color: var(--primary-text-color); }
    .seg button[aria-pressed="true"] { background: color-mix(in srgb, var(--sm-accent) 20%, transparent); }
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
    return { apt, r };
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
  body({ apt, r }) {
    const cur = apt.currency;
    const s = this._state;
    const c = r.vergleich;
    const dp = r.veraenderung_prozent || {}, dpp = r.veraenderung_punkte || {};
    const cmpTxt = (k, f) => (c ? `${t("Vergleich")} ${f(c[k])}` : "");
    const m = s.metric;
    const reihe = r.reihe;
    const colors = r.farben || {};
    const stacks = m === "brutto"
      ? Object.entries(reihe.kanaele).map(([name, values]) => ({ name, values, color: colors[name] || colorOf(apt, name) }))
      : [{ name: t(m === "netto" ? "Netto" : "Nächte"), values: reihe[m], color: "var(--sm-accent)" }];
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
      <div class="row"><h2 class="grow">${esc(this._config.title || t("Finanzen"))}</h2>
        <span class="sub">${fdate(r.von)} – ${fdate(iso(addDays(D(r.bis), -1)))}${c ? ` · ${t("Vergleich")} ${fdate(c.von)} – ${fdate(iso(addDays(D(c.bis), -1)))}` : ""}</span></div>
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
  .back { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 10000; display: flex; justify-content: center; align-items: flex-start;
    overflow-y: auto; padding: 24px 8px; box-sizing: border-box; }
  .dlg { background: var(--card-background-color, #fff); color: var(--primary-text-color); border-radius: 16px; width: min(760px, 100%);
    padding: 20px; box-sizing: border-box; box-shadow: 0 8px 32px rgba(0,0,0,.35); font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
  .top { display: flex; gap: 10px; align-items: flex-start; } .top h2 { flex: 1; }
  .x { background: none; border: none; font-size: 1.6rem; cursor: pointer; color: var(--sm-muted); line-height: 1; }
  .kv { display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; font-size: .9rem; }
  .kv dt { color: var(--sm-muted); } .kv dd { margin: 0; }
  .sec { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 8px 24px; }
  .msgs { display: flex; flex-direction: column; gap: 8px; max-height: 360px; overflow-y: auto; padding: 4px; }
  .msg { max-width: 85%; padding: 8px 12px; border-radius: 12px; font-size: .88rem; white-space: pre-wrap; word-break: break-word;
    background: var(--secondary-background-color, rgba(127,127,127,.12)); align-self: flex-start; }
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
    this.shadowRoot.innerHTML = `<style>${BASE_CSS}${DIALOG_CSS}</style><div class="back"><div class="dlg">
      <div class="top"><h2>${d?.buchung ? (d.buchung.blockiert ? `🔒 ${t("Sperrzeit")}` : esc(d.buchung.gast)) + (d.buchung.hund ? " 🐕" : "") : t("Details")}</h2>
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
    const msgs = newestFirst(d.nachrichten).map((m) => `<div class="msg ${m.typ === 2 ? "out" : ""}"><div class="h">${m.typ === 2 ? "→ " + t("Gast") : "← " + t("Gast")}${m.zeit ? " · " + esc(fdate(m.zeit, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })) : ""}${m.betreff ? " · " + esc(m.betreff) : ""}</div>${msgHtml(m.text)}</div>`).join("");
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
  static initialState = () => ({ sel: null, thread: null, loadingThread: false, draft: "", sug: null, thinking: false, ai: false });
  static css = `
    .wrap { display: grid; grid-template-columns: 280px minmax(0, 1fr); gap: 16px; }
    @media (max-width: 700px) { .wrap { grid-template-columns: 1fr; } }
    .item { padding: 8px 10px; border-radius: 10px; cursor: pointer; display: flex; gap: 8px; align-items: center; }
    .item:hover, .item.on { background: color-mix(in srgb, var(--sm-accent) 12%, transparent); }
    /* v1.13.0: Gast wartet auf Antwort → roter Rand links, rote Tönung, Badge */
    .item.open { border-left: 4px solid var(--sm-bad); padding-left: 6px;
      background: color-mix(in srgb, var(--sm-bad) 10%, transparent); }
    .item.open.on, .item.open:hover { background: color-mix(in srgb, var(--sm-bad) 18%, transparent); }
    .item.open b { color: var(--sm-bad); }
    .pending { display: inline-block; margin-top: 2px; padding: 1px 8px; border-radius: 999px; font-size: .75rem; font-weight: 600;
      background: var(--sm-bad); color: #fff; }
    .opencount { padding: 2px 10px; border-radius: 999px; font-size: .85rem; font-weight: 600; background: var(--sm-bad); color: #fff; }
    .sugbox { margin-top: 8px; padding: 8px 12px; border-radius: 10px; font-size: .85rem;
      background: color-mix(in srgb, var(--sm-accent) 10%, transparent); border-left: 4px solid var(--sm-accent); }
    .sugbox.urgent { border-left-color: var(--sm-bad); background: color-mix(in srgb, var(--sm-bad) 12%, transparent); }
    .last { padding: 10px 12px; border-radius: 10px; border-left: 4px solid var(--sm-accent); margin-bottom: 12px;
      background: var(--secondary-background-color, rgba(127,127,127,.08)); cursor: pointer; white-space: pre-wrap; }
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
      // Status aus dem frischen Verlauf übernehmen (neueste sichtbare Nachricht vom Gast = offen)
      const last = newestFirst((d.nachrichten || []).filter((m) => !m.intern))[0];
      if (this._data?.status) this._data.status[id] = { ...(this._data.status[id] || {}), offen: !!last && last.typ === 1, letzte_zeit: last?.zeit };
      if (this._state.sel === id) this.setState({ thread: d, loadingThread: false, sug, draft: sug?.antwort || "", ai: !!a?.aktiv });
    } catch (e) { this.setState({ thread: { fehler: e.message || String(e), nachrichten: [] }, loadingThread: false }); }
  }
  async aiSuggest() {
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
    const lastHtml = last && last.attributes.text ? `<div class="last" data-rid="${esc(last.attributes.buchungs_id || "")}">` +
      `<div class="sub">${t("Nachrichten")} · ${esc(last.attributes.gast || "")} · ${fdate(last.attributes.empfangen, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</div>` +
      `${msgHtml(String(last.attributes.text).slice(0, 2000))}</div>` : "";
    const openCount = guests.filter((b) => status[b.id]?.offen).length;
    const items = guests.map((b) => { const op = !!status[b.id]?.offen;
      return `<div class="item ${s.sel === b.id ? "on" : ""} ${op ? "open" : ""}" data-rid="${b.id}">
      <span class="dot" style="background:${colorOf(apt, b.kanal)}"></span><div class="grow"><b>${esc(b.gast)}</b>${b.hund ? " 🐕" : ""}
      <div class="sub">${fdate(b.anreise)} – ${fdate(b.abreise)} · ${t(b.status)}</div>
      ${op ? `<span class="pending">💬 ${t("Antwort offen")}</span>` : ""}</div></div>`; }).join("");
    const th = s.thread;
    const msgs = th ? newestFirst(th.nachrichten).map((m) => `<div class="msg ${m.typ === 2 ? "out" : ""}"><div class="h">${m.typ === 2 ? "→" : "←"} ${m.zeit ? esc(fdate(m.zeit, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })) : ""} ${m.betreff ? "· " + esc(m.betreff) : ""}</div>${msgHtml(m.text)}</div>`).join("") : "";
    const right = !s.sel ? `<div class="empty">← ${t("Gast")}</div>`
      : s.loadingThread ? `<div class="empty">${t("Laden …")}</div>`
      : `${th?.fehler ? `<div class="err">${esc(th.fehler)}</div>` : ""}
        <div class="row"><b class="grow">${esc(th?.buchung?.gast || "")}</b><button class="btn flat" data-act="detail">${t("Details")}</button></div>
        <div class="msgs">${msgs || `<div class="muted">${t("keine")}</div>`}</div>
        ${s.sug ? `<div class="sugbox ${s.sug.dringend ? "urgent" : ""}"><b>✨ ${s.sug.dringend ? "DRINGEND · " : ""}${esc(s.sug.absicht)}</b>
          ${s.sug.zusammenfassung ? ` · ${esc(s.sug.zusammenfassung)}` : ""}
          ${s.sug.hinweis ? `<div>ℹ️ ${esc(s.sug.hinweis)}</div>` : ""}
          ${s.sug.wissensluecke ? `<div>❓ Wissenslücke: ${esc(s.sug.wissensluecke)}</div>` : ""}
          ${s.sug.offen ? `<div>✏️ Bitte die Stellen [OFFEN: …] ergänzen.</div>` : ""}</div>` : ""}
        <textarea data-k="msg" placeholder="${t("Antworten")} …" style="margin-top:8px;min-height:140px">${esc(s.draft || "")}</textarea>
        <div class="row">${s.ai ? `<select data-k="anlass">${["antwort", "willkommen", "anreise", "abreise", "bewertung"].map((a) => `<option value="${a}">${a}</option>`).join("")}</select>
          <button class="btn flat" data-act="ai" ${s.thinking ? "disabled" : ""}>${s.thinking ? "⏳ KI denkt …" : "✨ Vorschlag"}</button>` : ""}
          <span class="grow"></span><button class="btn" data-act="send">✉ ${t("Senden")}</button></div>`;
    return `<div class="row"><h2 class="grow">${esc(this._config.title || t("Posteingang"))}</h2>${openCount ? `<span class="opencount">💬 ${openCount} ${t("warten auf Antwort")}</span>` : ""}</div>${lastHtml}
      <div class="wrap"><div>${items || `<div class="empty">${t("Keine Daten")}</div>`}</div><div>${right}</div></div>`;
  }
  bind(root) {
    root.querySelectorAll("[data-rid]").forEach((el) => el.addEventListener("click", () => el.dataset.rid && this.select(Number(el.dataset.rid))));
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
    .kn { border: 1px solid var(--sm-line); border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; }
    .kn.vorschlag { border-color: var(--sm-warn); background: color-mix(in srgb, var(--sm-warn) 8%, transparent); }
    .kn.aus { opacity: .55; }
    .kn .t { font-weight: 600; } .kn .x { white-space: pre-wrap; font-size: .88rem; margin-top: 4px; }
    .kn input[data-f="thema"] { width: 100%; box-sizing: border-box; margin-bottom: 6px; }
    .ex { border-bottom: 1px solid var(--sm-line); padding: 8px 0; font-size: .85rem; }
    .ex .g { color: var(--sm-muted); white-space: pre-wrap; } .ex .a { white-space: pre-wrap; margin-top: 4px; }
    .prog { height: 6px; border-radius: 3px; background: var(--sm-line); overflow: hidden; margin-top: 6px; }
    .prog > div { height: 100%; background: var(--sm-accent); }
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
    const head = `<div class="row"><h2 class="grow">🤖 ${esc(this._config.title || "Assistent")}</h2>
        <span class="badge ${st.aktiv ? "good" : "bad"}">${st.aktiv ? "aktiv" : "aus"}</span>
        <span class="badge">${esc(st.ki || "keine KI")}</span></div>
      ${st.fehler ? `<div class="err">Letzter Fehler: ${esc(st.fehler)}</div>` : ""}
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
        <button class="btn" data-a="wissen" ${this._state.busy ? "disabled" : ""}>${this._state.busy ? "⏳ KI arbeitet …" : "📚 Wissen erzeugen"}</button></div>
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
// Registrierung
// ===========================================================================
const CARDS = [
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
console.info(`%c SMOOBU-CARDS %c ${SMOOBU_CARDS_VERSION} `, "background:#1E5BB8;color:#fff;padding:2px 4px;border-radius:3px 0 0 3px",
  "background:#2E9E5B;color:#fff;padding:2px 4px;border-radius:0 3px 3px 0");

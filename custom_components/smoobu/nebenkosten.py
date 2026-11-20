"""Nebenkostenabrechnung hochladen und von der KI auswerten lassen (ab v1.19.0, Wunsch Betreiber 20.11.2026).

Ablauf:
1. Upload in der Einstellungs-Karte (Reiter Kosten & Preise): PDF, JPG oder PNG, max. 15 MB, über
   die HTTP-Ansicht `/api/smoobu/nebenkosten/<entry_id>` (Recht „einstellungen“). Die Datei bleibt
   lokal im HA-Konfigurationsordner (`smoobu_belege/<entry_id>/`), nicht im Medien-Ordner – dort
   sähen sie alle HA-Benutzer (auch der Gäste-Tablet-Benutzer).
2. Auswertung über die KI des Assistenten (`ai_task.generate_data` mit Anhang). Die KI liest nur;
   sie schreibt nie in die Einstellungen. Dafür braucht es die eigene Medienquelle `smoobu`
   (media_source.py), weil HA Anhänge nur über Medienquellen mit lokalem Pfad annimmt.
3. Vorschlag mit Prüfung: je Option alter und neuer Wert, Herleitung, Fundstelle im Dokument und
   Status ok/prüfen (Plausibilität, Abgleich mit den Gästenächten aus Smoobu und – falls gemessen –
   mit dem Stromzähler). Übernommen wird erst in der Karte nach Bestätigung (Entwurf → Speichern).

Datenschutz (Entscheidung Betreiber 20.11.2026): Die Abrechnung geht vollständig an die gewählte KI
(Name, Adresse, Zählernummern) – die Datenschutz-Stufe pseudonymisiert nur Gästenamen und greift
bei Dateien nicht. Die Karte weist darauf hin. Die KI-Sperre (Option „KI erlauben“) gilt auch hier.
"""

from __future__ import annotations

import logging
import re
import secrets
from datetime import date
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COST_GRID_PRICE, CONF_COST_HEATING_YEAR, CONF_COST_HOT_WATER_YEAR, CONF_COST_POWER_KWH,
    CONF_COST_REF_YEAR, CONF_COST_WATER_NIGHT, DEFAULT_COST_GRID_PRICE, DEFAULT_COST_HEATING_YEAR,
    DEFAULT_COST_HOT_WATER_YEAR, DEFAULT_COST_POWER_KWH, DEFAULT_COST_REF_YEAR, DEFAULT_COST_WATER_NIGHT, DOMAIN,
)
from .deckungsbeitrag import ref_nights_by_month

_LOGGER = logging.getLogger(__name__)
MAX_BYTES = 15 * 1024 * 1024
MIME = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
MAX_UPLOADS = 20

INSTRUCTIONS = """Du liest die angehängte Nebenkostenabrechnung einer Ferienwohnung.
Gib nur Werte an, die im Dokument stehen oder sich direkt daraus ergeben – nichts schätzen.
Gemeint sind ausschließlich Kosten bzw. Verbräuche, die der FERIENWOHNUNG zugeordnet sind (nicht dem ganzen Haus,
außer das Dokument betrifft nur die Ferienwohnung). Beträge in Euro brutto, Dezimalpunkt.
- heizkosten_eur: Heizkosten der Ferienwohnung im Abrechnungszeitraum (ohne Warmwasser, falls getrennt ausgewiesen)
- warmwasser_eur: Kosten für die Warmwasserbereitung der Ferienwohnung
- wasser_eur: Frischwasser + Abwasser der Ferienwohnung zusammen
- strom_kwh / strom_eur: Stromverbrauch bzw. -kosten der Ferienwohnung; strompreis_ct: Arbeitspreis in ct/kWh
- oel_liter: Heizölverbrauch, falls angegeben; gaestenaechte: Belegungs- bzw. Gästenächte, falls angegeben
- fundstellen: je gefundenem Feld eine Zeile „feld: Seite X – kurzes Zitat“
- hinweise: Auffälligkeiten (Rechenfehler, unplausible Umrechnungsfaktoren, Schätzwerte, fehlende Angaben) auf Deutsch, sonst leer
Fehlt ein Wert, lass das Feld leer."""


def _num(desc: str) -> dict[str, Any]:
    return {"description": desc, "required": False, "selector": {"number": {"mode": "box", "step": 0.01}}}


STRUCTURE: dict[str, Any] = {
    "abrechnungsjahr": _num("Abrechnungsjahr (z. B. 2025)"),
    "zeitraum": {"description": "Abrechnungszeitraum wie im Dokument", "required": False, "selector": {"text": None}},
    "heizkosten_eur": _num("Heizkosten der Ferienwohnung in Euro"),
    "warmwasser_eur": _num("Warmwasserkosten der Ferienwohnung in Euro"),
    "wasser_eur": _num("Frisch- und Abwasser der Ferienwohnung in Euro"),
    "strom_kwh": _num("Stromverbrauch der Ferienwohnung in kWh"),
    "strom_eur": _num("Stromkosten der Ferienwohnung in Euro"),
    "strompreis_ct": _num("Strom-Arbeitspreis in ct/kWh"),
    "oel_liter": _num("Heizölverbrauch in Litern"),
    "gaestenaechte": _num("Gästenächte laut Dokument"),
    "fundstellen": {"description": "je Feld eine Zeile „feld: Seite X – Zitat“", "required": False, "selector": {"text": {"multiline": True}}},
    "hinweise": {"description": "Auffälligkeiten auf Deutsch, sonst leer", "required": False, "selector": {"text": {"multiline": True}}},
}

LABELS = {
    CONF_COST_HEATING_YEAR: ("Heizkosten im Abrechnungsjahr", "€"),
    CONF_COST_HOT_WATER_YEAR: ("Warmwasser im Abrechnungsjahr", "€"),
    CONF_COST_REF_YEAR: ("Abrechnungsjahr", ""),
    CONF_COST_WATER_NIGHT: ("Wasser/Abwasser je Nacht", "€"),
    CONF_COST_POWER_KWH: ("Strom je Nacht", "kWh"),
    CONF_COST_GRID_PRICE: ("Netzstrompreis", "ct/kWh"),
}
DEFAULTS = {
    CONF_COST_HEATING_YEAR: DEFAULT_COST_HEATING_YEAR, CONF_COST_HOT_WATER_YEAR: DEFAULT_COST_HOT_WATER_YEAR,
    CONF_COST_REF_YEAR: DEFAULT_COST_REF_YEAR, CONF_COST_WATER_NIGHT: DEFAULT_COST_WATER_NIGHT,
    CONF_COST_POWER_KWH: DEFAULT_COST_POWER_KWH, CONF_COST_GRID_PRICE: DEFAULT_COST_GRID_PRICE,
}


def _f(value: Any) -> float | None:
    try:
        v = float(str(value).replace(",", ".")) if value not in (None, "") else None
    except ValueError:
        return None
    return v if v is not None and v >= 0 else None


def _sources(text: str | None) -> dict[str, str]:
    out = {}
    for line in str(text or "").splitlines():
        key, sep, rest = line.partition(":")
        if sep and key.strip():
            out[key.strip().lower()] = rest.strip()
    return out


def proposal(extracted: dict[str, Any], options: dict[str, Any], records: list[dict[str, Any]],
             measured_kwh: dict[int, float] | None = None) -> dict[str, Any]:
    """Aus den KI-Werten Vorschläge für die Optionen bauen und prüfen (reine Logik, testbar)."""
    src = _sources(extracted.get("fundstellen"))
    year = _f(extracted.get("abrechnungsjahr"))
    year = int(year) if year and 2000 <= year <= 2100 else None
    nights_doc = _f(extracted.get("gaestenaechte"))
    nights_smoobu = sum(ref_nights_by_month(records, year).values()) if year else 0
    nights = nights_smoobu or (int(nights_doc) if nights_doc else 0)
    items: list[dict[str, Any]] = []
    checks: list[str] = []

    def add(key: str, new: float | None, how: str, field: str, warn: str | None = None, digits: int = 2) -> None:
        if new is None:
            return
        old = options.get(key, DEFAULTS[key])
        label, unit = LABELS[key]
        items.append({"key": key, "label": label, "einheit": unit, "alt": old, "neu": round(new, digits),
                      "herleitung": how, "fundstelle": src.get(field, ""), "status": "pruefen" if warn else "ok",
                      "hinweis": warn or "", "gleich": abs(float(old) - round(new, digits)) < 10 ** -digits})

    if year:
        add(CONF_COST_REF_YEAR, year, "aus dem Dokument", "abrechnungsjahr", digits=0)
    heat = _f(extracted.get("heizkosten_eur"))
    add(CONF_COST_HEATING_YEAR, heat, "Heizkosten laut Abrechnung", "heizkosten_eur",
        "ungewöhnlich hoch – Anteil Ferienwohnung prüfen" if heat and heat > 5000 else None)
    ww = _f(extracted.get("warmwasser_eur"))
    add(CONF_COST_HOT_WATER_YEAR, ww, "Warmwasser laut Abrechnung", "warmwasser_eur",
        "Warmwasser höher als Heizung – Umrechnungsfaktor prüfen" if ww and heat and ww > heat else None)
    if nights_doc and nights_smoobu and abs(nights_doc - nights_smoobu) / nights_smoobu > 0.1:
        checks.append(f"Gästenächte laut Dokument {int(nights_doc)}, laut Smoobu {nights_smoobu} – Werte je Nacht mit Smoobu gerechnet")
    water = _f(extracted.get("wasser_eur"))
    if water is not None and nights:
        per = water / nights
        add(CONF_COST_WATER_NIGHT, per, f"{water:.2f} € ÷ {nights} Gästenächte ({'Smoobu' if nights_smoobu else 'Dokument'})",
            "wasser_eur", "mehr als 10 € je Nacht – prüfen" if per > 10 else None)
    kwh = _f(extracted.get("strom_kwh"))
    if kwh is not None and nights:
        per = kwh / nights
        warn = "unter 0,5 oder über 50 kWh je Nacht – prüfen" if not 0.5 <= per <= 50 else None
        meas = (measured_kwh or {}).get(year) if year else None
        if meas and abs(meas - kwh) / max(kwh, 1) > 0.15:
            warn = (warn + "; " if warn else "") + f"Zähler in HA misst {meas:.0f} kWh für {year}"
        elif meas:
            checks.append(f"Strom: Abrechnung {kwh:.0f} kWh, Zähler in HA {meas:.0f} kWh – passt")
        add(CONF_COST_POWER_KWH, per, f"{kwh:.0f} kWh ÷ {nights} Gästenächte", "strom_kwh", warn, digits=1)
    price = _f(extracted.get("strompreis_ct"))
    how, field = "Arbeitspreis laut Abrechnung", "strompreis_ct"
    if price is None and kwh and _f(extracted.get("strom_eur")):
        price, how, field = _f(extracted["strom_eur"]) / kwh * 100, "Stromkosten ÷ kWh (inkl. Grundpreisanteil)", "strom_eur"
    add(CONF_COST_GRID_PRICE, price, how, field, "außerhalb 15–80 ct/kWh – prüfen" if price and not 15 <= price <= 80 else None)
    if not nights and (water is not None or kwh is not None):
        checks.append("Keine Gästenächte für das Abrechnungsjahr – Werte je Nacht nicht berechenbar")
    return {"jahr": year, "zeitraum": extracted.get("zeitraum") or "", "naechte": nights,
            "naechte_quelle": "smoobu" if nights_smoobu else ("dokument" if nights_doc else None),
            "werte": items, "pruefungen": checks, "hinweise_ki": (extracted.get("hinweise") or "").strip(),
            "oel_liter": _f(extracted.get("oel_liter"))}


class UtilityBills:
    """Hochgeladene Abrechnungen eines Kontos (Dateien + Auswertungen)."""

    def __init__(self, hass: HomeAssistant, coordinator: Any) -> None:
        self.hass = hass
        self.c = coordinator
        self.entry_id = coordinator.config_entry.entry_id
        self.dir = Path(hass.config.path("smoobu_belege", self.entry_id))
        self.store: Store = Store(hass, 1, f"{DOMAIN}_nebenkosten_{self.entry_id}")
        self.items: list[dict[str, Any]] | None = None

    async def list(self) -> list[dict[str, Any]]:
        if self.items is None:
            self.items = list(await self.store.async_load() or [])
        return self.items

    def path(self, file: str) -> Path | None:
        """Datei im Belegordner (Schutz gegen Pfade außerhalb, z. B. „../“)."""
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,120}", file or ""):
            return None
        p = (self.dir / file).resolve()
        return p if p.parent == self.dir.resolve() and p.is_file() else None

    async def add(self, name: str, data: bytes, user: str | None) -> dict[str, Any]:
        ext = Path(name or "").suffix.lower()
        if ext not in MIME:
            raise ValueError("invalid_type")
        if not data or len(data) > MAX_BYTES:
            raise ValueError("invalid_size")
        if ext == ".pdf" and not data.startswith(b"%PDF"):
            raise ValueError("invalid_type")
        file = f"{dt_util.now().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}{ext}"

        def write() -> None:
            self.dir.mkdir(parents=True, exist_ok=True)
            (self.dir / file).write_bytes(data)

        await self.hass.async_add_executor_job(write)
        items = await self.list()
        item = {"id": file.rsplit(".", 1)[0], "datei": file, "name": Path(name).name[:120], "groesse": len(data),
                "zeit": dt_util.now().isoformat(timespec="seconds"), "benutzer": user, "auswertung": None, "fehler": None}
        items.insert(0, item)
        for old in items[MAX_UPLOADS:]:
            await self._unlink(old["datei"])
        del items[MAX_UPLOADS:]
        await self.store.async_save(items)
        return item

    async def _unlink(self, file: str) -> None:
        if p := self.path(file):
            await self.hass.async_add_executor_job(p.unlink)

    async def delete(self, item_id: str) -> None:
        items = await self.list()
        for it in [i for i in items if i["id"] == item_id]:
            await self._unlink(it["datei"])
            items.remove(it)
        await self.store.async_save(items)

    async def analyse(self, item_id: str) -> dict[str, Any]:
        """KI-Auswertung (über die zentrale KI-Sperre des Assistenten) + Vorschlag; Ergebnis gespeichert."""
        items = await self.list()
        item = next((i for i in items if i["id"] == item_id), None)
        if item is None or not self.path(item["datei"]):
            raise ValueError("not_found")
        assistant = getattr(self.c, "assistant", None)
        if assistant is None:
            raise ValueError("no_ai")
        ext = Path(item["datei"]).suffix.lower()
        try:
            extracted = await assistant._ai(  # noqa: SLF001 – einzige KI-Stelle (Sperre, Zeitlimit, Fehlertext)
                INSTRUCTIONS, STRUCTURE, "Smoobu Nebenkostenabrechnung",
                attachments=[{"media_content_id": f"media-source://{DOMAIN}/{self.entry_id}/{item['datei']}",
                              "media_content_type": MIME[ext]}])
        except Exception as err:  # noqa: BLE001
            item["fehler"] = str(err)
            await self.store.async_save(items)
            raise
        records = self.c.records_all()
        result = proposal(extracted, dict(self.c.config_entry.options), records, self._measured_kwh())
        item.update({"auswertung": {"ki": extracted, "vorschlag": result, "zeit": dt_util.now().isoformat(timespec="seconds")},
                     "fehler": None, "jahr": result["jahr"]})
        await self.store.async_save(items)
        return item

    def _measured_kwh(self) -> dict[int, float]:
        """Gemessener FeWo-Strom je Kalenderjahr (nur vollständige Jahre aus energie.allocate)."""
        out: dict[int, float] = {}
        data = self.c.data
        for res in ((data.energy if data else {}) or {}).values():
            by_year: dict[int, list] = {}
            for k, m in res.get("monate", {}).items():
                by_year.setdefault(int(k[:4]), []).append(m)
            for y, ms in by_year.items():
                if len(ms) == 12 and all(m["vollstaendig"] for m in ms) and y < date.today().year:
                    out[y] = out.get(y, 0.0) + sum(m["kwh"] for m in ms)
        return out

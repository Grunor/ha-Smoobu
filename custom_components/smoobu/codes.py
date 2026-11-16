"""Wohnungskürzel (v1.15.0 automatisch, ab v1.17.0 in den Optionen anpassbar)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntryState

from .const import CONF_APARTMENT_CODES, DOMAIN, MAX_CODE_LEN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# Allgemeine Wörter, die im Kürzel nichts unterscheiden („Ferienwohnung Seeblick“ → „SE“)
_GENERIC = {"ferienwohnung", "fewo", "wohnung", "apartment", "appartement", "ferienhaus", "studio", "zimmer"}


def short_codes(names: list[str], taken: set[str] | None = None) -> list[str]:
    """Automatische, eindeutige Kürzel je Wohnung (v1.15.0), z. B. „Haus Sonnenhang“ → „HS“.

    Mehrere Wörter → Anfangsbuchstaben der ersten beiden (Zahlen ganz),
    ein Wort → die ersten zwei Buchstaben. Allgemeine Wörter (Ferienwohnung …)
    zählen nur, wenn sonst nichts übrig bleibt. Doppelte Kürzel bekommen 2, 3 …
    `taken` (v1.17.0): bereits vergebene (eigene) Kürzel, die nicht doppelt vorkommen dürfen.
    """
    out: list[str] = []
    taken = set(taken or ())
    for name in names:
        words = re.findall(r"[0-9]+|[^\W\d_]+", name or "")
        useful = [w for w in words if w.casefold() not in _GENERIC] or words
        if useful and all(w.isdigit() for w in useful) and useful != words:
            useful = [words[0], *useful]  # „Wohnung 2“ → „W2“ statt nur „2“
        if not useful:
            code = "?"
        elif len(useful) == 1:
            code = useful[0][:2] if not useful[0].isdigit() else useful[0]
        else:
            code = "".join(w if w.isdigit() else w[0] for w in useful[:2])
        code = code.upper()
        base, n = code, 2
        while code in out or code in taken:
            code = f"{base}{n}"
            n += 1
        out.append(code)
    return out



def clean_code(value: Any) -> str:
    """Eigenes Kürzel normalisieren: Großbuchstaben/Ziffern, höchstens MAX_CODE_LEN Zeichen."""
    return re.sub(r"[^0-9A-ZÄÖÜ]", "", str(value or "").upper())[:MAX_CODE_LEN]


def apartment_list(hass: HomeAssistant) -> list[tuple[Any, int, str]]:
    """(Config-Entry, Wohnungs-ID, Name) aller geladenen Konten – gleiche Reihenfolge wie smoobu/info."""
    out = []
    for e in hass.config_entries.async_entries(DOMAIN):
        if e.state is not ConfigEntryState.LOADED or not getattr(e, "runtime_data", None):
            continue
        data = e.runtime_data.data
        for apt_id, apt in (data.apartments if data else {}).items():
            out.append((e, int(apt_id), apt.get("name") or str(apt_id)))
    return out


def all_codes(hass: HomeAssistant, overrides: dict[str, dict[str, str]] | None = None) -> dict[tuple[str, int], str]:
    """Kürzel je (entry_id, Wohnung): eigene aus den Optionen haben Vorrang, der Rest automatisch.

    `overrides` ersetzt die gespeicherten eigenen Kürzel eines Kontos (für die Vorschau im Optionsdialog).
    """
    apts = apartment_list(hass)
    own: dict[tuple[str, int], str] = {}
    for e, apt_id, _name in apts:
        codes = (overrides or {}).get(e.entry_id, e.options.get(CONF_APARTMENT_CODES) or {})
        code = clean_code(codes.get(str(apt_id)))
        if code:
            own[(e.entry_id, apt_id)] = code
    rest = [(e, a, n) for e, a, n in apts if (e.entry_id, a) not in own]
    auto = short_codes([n for _e, _a, n in rest], taken=set(own.values()))
    return {**own, **{(e.entry_id, a): code for (e, a, _n), code in zip(rest, auto, strict=True)}}

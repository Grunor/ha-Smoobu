"""Benutzerrollen und Rechte (ab v1.18.0, Wunsch Betreiber 17.11.2026; Rollenkonfigurator ab v1.19.0).

Ein HA-Admin legt je HA-Benutzer eine Rolle fest (Option `user_roles`). Jede Rolle ist ein Bündel
von Rechten. Ab v1.19.0 (Wunsch Betreiber 20.11.2026) sind die Bündel einstellbar:

- Standardrollen (ROLES) bringen ihre Standardrechte mit. Ein Admin kann sie je Rolle ändern
  (Option `role_rights`, gespeichert werden nur Abweichungen vom Standard – so bekommen nicht
  angepasste Rollen neue Rechte späterer Versionen automatisch). „Kein Zugriff“ bleibt fest leer.
- Eigene Rollen (Option `custom_roles`: {id: {name, rechte}}) legt ein Admin an, benennt sie und
  löscht sie wieder. IDs beginnen mit „eigen_“, damit sie nie mit Standardrollen kollidieren.
- Abhängigkeiten (DEPENDS, z. B. „Preise ändern“ ohne „Finanzen sehen“) sind bewusst nur
  Hinweise in der Karte (Entscheidung Betreiber 20.11.2026: Warnhinweis statt Automatik).
- „Gästedaten sehen“ schließt „Belegung sehen“ immer ein (wer Namen und Kontakt sieht, sieht
  auch die Belegung) – sonst entstünden Rollen, die Buchungen, aber keinen Kalender sehen.

Regeln:
- HA-Admins haben immer alle Rechte und als einzige das Recht, Rollen zu vergeben/einzustellen.
- Aufrufe ohne Benutzer (Automationen, Skripte, interne Aufrufe) sind erlaubt – sonst würden
  bestehende Automationen mit smoobu.* plötzlich scheitern.
- Benutzer ohne Eintrag (oder mit gelöschter Rolle) bekommen die Standardrolle (Option
  `default_role`, Standard „betrieb“). Wer in der älteren Option „Einstellungen im Dashboard
  erlauben für“ steht, gilt als „verwalter“.
- Geprüft wird im Backend (Websocket-Befehle der Karten und smoobu.*-Aktionen). Die Karten
  blenden zusätzlich aus, was nicht erlaubt ist.

Grenze: Normale HA-Entitäten (z. B. Umsatz-Sensoren) kann HA nicht je Benutzer sperren –
die Rollen gelten für die Smoobu-Karten und -Aktionen.
"""

from __future__ import annotations

from typing import Any

from .const import (
    CONF_CUSTOM_ROLES,
    CONF_DEFAULT_ROLE,
    CONF_FOCUS_ROLES,
    CONF_ROLE_RIGHTS,
    DEFAULT_FOCUS_ROLES,
    CONF_SETTINGS_USERS,
    CONF_USER_ROLES,
    DEFAULT_ROLE,
)

# Rechte (Schlüssel → Bezeichnung). Reihenfolge = Reihenfolge in der Rollen-Matrix.
RIGHTS: dict[str, str] = {
    # v1.19.0 (Wunsch Betreiber 20.11.2026, Rolle „Reinigung“): Übersicht und Kalender mit Zeitraum,
    # Check-in/-out, Personen und Hund – vom Gast nur der Vorname, ohne Kontakt, Notizen und Preise
    "belegung_sehen": "Belegung sehen (nur Vorname des Gastes)",
    "gaeste": "Gästedaten und Buchungen sehen",
    "finanzen": "Finanzen, Statistik und Preise sehen",
    "nachrichten": "Nachrichten lesen",
    "antworten": "Antworten und KI-Vorschläge",
    "belegung": "Belegung ändern (sperren, Zeiten, Storno)",
    # v1.19.0: Reinigungsboard – offene Reinigungen sehen, sich eintragen, eigene abhaken
    "reinigung": "Reinigung übernehmen und abhaken",
    # v1.19.0: Reinigungen anderen Benutzern zuweisen (Reinigungsboard)
    "reinigung_zuweisen": "Reinigung zuweisen",
    "preise": "Preise ändern und Empfehlungen übernehmen",
    "einstellungen": "Einstellungen ändern",
}

_ALL = frozenset(RIGHTS)
# Standardrolle → (Bezeichnung, Standardrechte)
ROLES: dict[str, tuple[str, frozenset[str]]] = {
    "verwalter": ("Verwalter", _ALL),
    # Standard ab v1.19.0b5 = Konfiguration des Betreibers (21.11.2026): Betrieb ohne „Preise ändern“,
    # Mitarbeiter ohne „Belegung ändern“, dafür mit „Reinigung zuweisen“
    "betrieb": ("Betrieb", _ALL - {"einstellungen", "preise"}),
    "mitarbeiter": ("Mitarbeiter", frozenset({"belegung_sehen", "gaeste", "nachrichten", "antworten", "reinigung", "reinigung_zuweisen"})),
    # v1.19.0: sehr einfache Rolle für Reinigungskräfte (Belegung, Check-in/-out, Reinigung abhaken)
    "reinigung": ("Reinigung", frozenset({"belegung_sehen", "reinigung"})),
    "lesen": ("Nur lesen", frozenset({"belegung_sehen", "gaeste", "nachrichten"})),
    "kein": ("Kein Zugriff", frozenset()),
}
# Rollen, deren Rechte sich nicht einstellen lassen („Kein Zugriff“ mit Rechten wäre widersinnig)
LOCKED_ROLES = frozenset({"kein"})
CUSTOM_PREFIX = "eigen_"
MAX_CUSTOM_ROLES = 10
MAX_ROLE_NAME = 30

# Recht → Rechte, ohne die es im Dashboard kaum nutzbar ist (nur Hinweise, keine Pflicht)
DEPENDS: dict[str, tuple[str, ...]] = {
    "preise": ("finanzen", "belegung_sehen"),  # Preise setzen geht über den Kalender und braucht die Preise
    "belegung": ("belegung_sehen",),           # sperren/Zeiten ändern im Kalender
    "reinigung": ("belegung_sehen",),          # ohne: Reinigungen ohne Vornamen der Gäste
    "reinigung_zuweisen": ("belegung_sehen",),
    "antworten": ("nachrichten",),             # antworten ohne die Nachricht zu lesen
}
ADMIN = "admin"
SYSTEM = "system"


def _clean(rights: Any) -> frozenset[str]:
    """Nur bekannte Rechte; „gaeste“ schließt „belegung_sehen“ ein (siehe Modul-Doku)."""
    out = frozenset(r for r in (rights or []) if r in RIGHTS)
    return out | {"belegung_sehen"} if "gaeste" in out else out


def roles(options: Any) -> dict[str, dict[str, Any]]:
    """Alle Rollen eines Eintrags mit wirksamen Rechten: Standardrollen (ggf. angepasst) + eigene."""
    o = options or {}
    overrides = o.get(CONF_ROLE_RIGHTS) or {}
    out: dict[str, dict[str, Any]] = {}
    for rid, (name, default) in ROLES.items():
        custom = overrides.get(rid) if rid not in LOCKED_ROLES else None
        rights = _clean(custom) if isinstance(custom, (list, tuple, set, frozenset)) else default
        out[rid] = {"name": name, "rechte": rights, "art": "standard", "standard": default}
    for rid, cfg in (o.get(CONF_CUSTOM_ROLES) or {}).items():
        if str(rid).startswith(CUSTOM_PREFIX) and isinstance(cfg, dict):
            out[str(rid)] = {"name": str(cfg.get("name") or rid), "rechte": _clean(cfg.get("rechte")), "art": "eigen"}
    return out


def role_of(user: Any, options: Any) -> str:
    """Rolle eines HA-Benutzers für einen Smoobu-Eintrag (admin/system/eine Rolle aus roles())."""
    if user is None:
        return SYSTEM
    if getattr(user, "is_admin", False):
        return ADMIN
    o = options or {}
    known = roles(o)
    role = (o.get(CONF_USER_ROLES) or {}).get(user.id)
    if role in known:
        return role
    if user.id in (o.get(CONF_SETTINGS_USERS) or []):
        return "verwalter"
    default = o.get(CONF_DEFAULT_ROLE, DEFAULT_ROLE)
    return default if default in known else DEFAULT_ROLE


def rights_of(user: Any, options: Any) -> frozenset[str]:
    role = role_of(user, options)
    if role in (ADMIN, SYSTEM):
        return _ALL
    return roles(options)[role]["rechte"]


def allowed(user: Any, options: Any, right: str) -> bool:
    return right in rights_of(user, options)


def describe(user: Any, options: Any) -> dict[str, Any]:
    """Für die Karten: eigene Rolle und Rechte (zum Ausblenden von Seiten und Buttons)."""
    role = role_of(user, options)
    return {
        "rolle": role,
        "rolle_name": "Admin" if role == ADMIN else "System" if role == SYSTEM else roles(options)[role]["name"],
        "rechte": sorted(rights_of(user, options)),
        "admin": role == ADMIN,
    }


# ---------------------------------------------------------------------------
# Fokus-Modus (v1.19.0b7, Wunsch Betreiber 21.11.2026)
# Benutzer einer Fokus-Rolle sehen in HA nur noch Smoobu: die Karten blenden Seitenleiste und Menü aus und
# leiten jede andere Seite auf die Startseite der Rolle um. Das ist eine Sperre der Oberfläche, keine
# Rechteprüfung (HA kennt keine Rechte je Benutzer und Entität); Smoobu-Daten prüft weiterhin der Server.
# Admins sind nie betroffen. Startseite "" = automatisch: Seite Reinigung für reine Reinigungsrollen,
# sonst die Übersicht – jeweils im Dashboard des Assistent-Pfads (assist_path), sonst /lovelace.
# ---------------------------------------------------------------------------
FOCUS_PAGES = ("smoobu", "smoobu-kalender", "smoobu-reinigung", "smoobu-buchungen", "smoobu-nachrichten",
               "smoobu-assistent", "smoobu-finanzen", "smoobu-statistik", "smoobu-einstellungen")
_CLEANING_ONLY = frozenset({"belegung_sehen", "reinigung", "reinigung_zuweisen"})


def module_on(options: Any, name: str) -> bool:
    """Modul an? Option `module_<name>` (Standard an). Module: reinigung, kosten, preise (const.MODULES)."""
    return bool((options or {}).get(f"module_{name}", True))


def focus_roles(options: Any) -> dict[str, str]:
    """{Rolle: Startseite} der Fokus-Rollen (gespeichert oder Standard); unbekannte Rollen fallen weg."""
    o = options or {}
    cfg = o.get(CONF_FOCUS_ROLES, DEFAULT_FOCUS_ROLES)
    known = roles(o)
    return {str(r): str(p or "") for r, p in (cfg or {}).items() if r in known and r not in LOCKED_ROLES}


def focus_dashboard(options: Any) -> str:
    """Dashboard der Smoobu-Seiten, z. B. „/dashboard-ferienwohnung“ (aus dem Assistent-Pfad)."""
    path = str((options or {}).get("assist_path") or "")
    parts = [p for p in path.split("/") if p]
    return f"/{parts[0]}" if parts else "/lovelace"


def focus_of(user: Any, options: Any) -> dict[str, Any] | None:
    """Fokus-Modus eines Benutzers: {start, erlaubt: [Pfad-Präfixe]} oder None (kein Fokus, Admin, System)."""
    role = role_of(user, options)
    if role in (ADMIN, SYSTEM):
        return None
    cfg = focus_roles(options)
    if role not in cfg:
        return None
    dash = focus_dashboard(options)
    start = cfg[role]
    if not start:
        have = rights_of(user, options)
        start = (f"{dash}/smoobu-reinigung" if module_on(options, "reinigung") and have <= _CLEANING_ONLY
                 and have & {"reinigung", "reinigung_zuweisen"} else f"{dash}/smoobu")
    sdash = "/" + start.strip("/").split("/")[0]
    # erlaubt: alle Smoobu-Seiten im Dashboard der Startseite (Präfix „…/smoobu“ deckt smoobu-* ab) + Startseite
    return {"start": start, "erlaubt": sorted({f"{sdash}/smoobu", start}), "rolle": role}


def hints(rights: Any) -> list[dict[str, Any]]:
    """Fehlende Abhängigkeiten einer Rechte-Auswahl (für Warnhinweise; gleiche Regel wie die Karte)."""
    have = _clean(rights)
    return [{"recht": r, "fehlt": [d for d in deps if d not in have]}
            for r, deps in DEPENDS.items() if r in have and any(d not in have for d in deps)]


def matrix(options: Any = None) -> dict[str, Any]:
    """Rollen × Rechte für die Einstellungskarte (wirksame Rechte, Standard, Art, Abhängigkeiten)."""
    return {
        "rechte": [{"id": k, "name": v} for k, v in RIGHTS.items()],
        "rollen": [{"id": rid, "name": r["name"], "rechte": sorted(r["rechte"]), "art": r["art"],
                    "standard": sorted(r["standard"]) if "standard" in r else None,
                    "fest": rid in LOCKED_ROLES}
                   for rid, r in roles(options).items()],
        "abhaengig": {k: list(v) for k, v in DEPENDS.items()},
        "eigen_praefix": CUSTOM_PREFIX,
        "max_eigene": MAX_CUSTOM_ROLES,
        "max_name": MAX_ROLE_NAME,
    }


# Felder einer Buchung, die nur mit „finanzen“ ausgeliefert werden
FINANCE_KEYS = {
    "brutto", "netto", "provision", "provision_quelle", "zahlungsgebuehr", "kostenquote_prozent",
    "brutto_pro_nacht", "netto_pro_nacht", "offen", "anzahlung", "anzahlung_bezahlt", "bezahlt",
    "kurtaxe", "positionen", "var_kosten", "db", "var_naechte", "strom_kosten", "wasser_kosten", "heizung_kosten", "reinigung_kosten", "price", "price-details", "prepayment",
    "prepayment-paid", "price-paid", "commission-included", "deposit", "deposit-paid", "city-tax", "priceElements",
}
# Felder, die nur mit „gaeste“ ausgeliefert werden (Personenbezug)
GUEST_KEYS = {"gast", "vorname", "email", "telefon", "gast_id", "guest-name", "firstname", "lastname", "phone", "guestId",
              "notiz", "assistent_notiz", "notice", "assistant-notice", "guest-app-url",
              # v1.18.0: Aufenthalts-Historie des Gastes (Personenbezug)
              "besuche_vorher", "zuletzt_id", "zuletzt_anreise", "zuletzt_abreise", "zuletzt_wohnung_id"}


# v1.19.0: mit „belegung_sehen“ ohne „gaeste“ bleibt vom Gast nur der Vorname (Entscheidung Betreiber
# 20.11.2026: Reinigung darf den Vornamen sehen, z. B. für einen Begrüßungszettel)
FIRST_NAME_KEYS = {"vorname", "firstname"}


def strip(item: dict[str, Any], rights: frozenset[str]) -> dict[str, Any]:
    """Buchung ohne die Felder, die der Benutzer nicht sehen darf."""
    drop = set()
    if "finanzen" not in rights:
        drop |= FINANCE_KEYS
    if "gaeste" not in rights:
        drop |= GUEST_KEYS
        if "belegung_sehen" in rights:
            drop -= FIRST_NAME_KEYS
    if not drop:
        return item
    out = {k: v for k, v in item.items() if k not in drop}
    # Anzeigename „gast“ wird von allen Karten genutzt → bei Vorname-Sicht durch den Vornamen ersetzen
    if "gaeste" not in rights and "belegung_sehen" in rights and "gast" in item:
        out["gast"] = item.get("vorname") or ("Sperre" if item.get("blockiert") else "Gast")
    return out

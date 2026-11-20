"""Benutzerrollen und Rechte (ab v1.18.0, Wunsch Betreiber 17.11.2026).

Ein HA-Admin legt je HA-Benutzer eine Rolle fest (Option `user_roles`). Jede Rolle ist ein
festes Bündel von Rechten – bewusst keine frei klickbare Matrix: fünf klar benannte Rollen
sind im Alltag verständlicher und lassen keine widersprüchlichen Kombinationen zu (z. B.
„Preise ändern“ ohne „Finanzen sehen“).

Regeln:
- HA-Admins haben immer alle Rechte und als einzige das Recht, Rollen zu vergeben.
- Aufrufe ohne Benutzer (Automationen, Skripte, interne Aufrufe) sind erlaubt – sonst würden
  bestehende Automationen mit smoobu.* plötzlich scheitern.
- Benutzer ohne Eintrag bekommen die Standardrolle (Option `default_role`, Standard
  „betrieb“ = Verhalten bis v1.18.0b2: alles außer Einstellungen). Wer in der älteren
  Option „Einstellungen im Dashboard erlauben für“ steht, gilt als „verwalter“.
- Geprüft wird im Backend (Websocket-Befehle der Karten und smoobu.*-Aktionen). Die Karten
  blenden zusätzlich aus, was nicht erlaubt ist.

Grenze: Normale HA-Entitäten (z. B. Umsatz-Sensoren) kann HA nicht je Benutzer sperren –
die Rollen gelten für die Smoobu-Karten und -Aktionen.
"""

from __future__ import annotations

from typing import Any

from .const import CONF_DEFAULT_ROLE, CONF_SETTINGS_USERS, CONF_USER_ROLES, DEFAULT_ROLE

# Rechte (Schlüssel → Bezeichnung)
RIGHTS: dict[str, str] = {
    "finanzen": "Finanzen, Statistik und Preise sehen",
    "gaeste": "Gästedaten und Buchungen sehen",
    "nachrichten": "Nachrichten lesen",
    "antworten": "Antworten und KI-Vorschläge",
    "belegung": "Belegung ändern (sperren, Zeiten, Storno)",
    "preise": "Preise ändern und Empfehlungen übernehmen",
    "einstellungen": "Einstellungen ändern",
}

# Rolle → (Bezeichnung, Rechte)
ROLES: dict[str, tuple[str, frozenset[str]]] = {
    "verwalter": ("Verwalter", frozenset(RIGHTS)),
    "betrieb": ("Betrieb", frozenset(RIGHTS) - {"einstellungen"}),
    "mitarbeiter": ("Mitarbeiter", frozenset({"gaeste", "nachrichten", "antworten", "belegung"})),
    "lesen": ("Nur lesen", frozenset({"gaeste", "nachrichten"})),
    "kein": ("Kein Zugriff", frozenset()),
}
ADMIN = "admin"
SYSTEM = "system"


def role_of(user: Any, options: Any) -> str:
    """Rolle eines HA-Benutzers für einen Smoobu-Eintrag (admin/system/eine der ROLES)."""
    if user is None:
        return SYSTEM
    if getattr(user, "is_admin", False):
        return ADMIN
    o = options or {}
    roles = o.get(CONF_USER_ROLES) or {}
    role = roles.get(user.id)
    if role in ROLES:
        return role
    if user.id in (o.get(CONF_SETTINGS_USERS) or []):
        return "verwalter"
    default = o.get(CONF_DEFAULT_ROLE, DEFAULT_ROLE)
    return default if default in ROLES else DEFAULT_ROLE


def rights_of(user: Any, options: Any) -> frozenset[str]:
    role = role_of(user, options)
    if role in (ADMIN, SYSTEM):
        return frozenset(RIGHTS)
    return ROLES[role][1]


def allowed(user: Any, options: Any, right: str) -> bool:
    return right in rights_of(user, options)


def describe(user: Any, options: Any) -> dict[str, Any]:
    """Für die Karten: eigene Rolle und Rechte (zum Ausblenden von Seiten und Buttons)."""
    role = role_of(user, options)
    return {
        "rolle": role,
        "rolle_name": "Admin" if role == ADMIN else "System" if role == SYSTEM else ROLES[role][0],
        "rechte": sorted(rights_of(user, options)),
        "admin": role == ADMIN,
    }


def matrix() -> dict[str, Any]:
    """Rollen × Rechte für die Anzeige in der Einstellungskarte."""
    return {
        "rechte": [{"id": k, "name": v} for k, v in RIGHTS.items()],
        "rollen": [{"id": k, "name": n, "rechte": sorted(r)} for k, (n, r) in ROLES.items()],
    }


# Felder einer Buchung, die nur mit „finanzen“ ausgeliefert werden
FINANCE_KEYS = {
    "brutto", "netto", "provision", "provision_quelle", "zahlungsgebuehr", "kostenquote_prozent",
    "brutto_pro_nacht", "netto_pro_nacht", "offen", "anzahlung", "anzahlung_bezahlt", "bezahlt",
    "kurtaxe", "positionen", "var_kosten", "db", "var_naechte", "price", "price-details", "prepayment",
    "prepayment-paid", "price-paid", "commission-included", "deposit", "deposit-paid", "city-tax", "priceElements",
}
# Felder, die nur mit „gaeste“ ausgeliefert werden (Personenbezug)
GUEST_KEYS = {"gast", "vorname", "email", "telefon", "gast_id", "guest-name", "firstname", "lastname", "phone", "guestId",
              "notiz", "assistent_notiz", "notice", "assistant-notice", "guest-app-url",
              # v1.18.0: Aufenthalts-Historie des Gastes (Personenbezug)
              "besuche_vorher", "zuletzt_id", "zuletzt_anreise", "zuletzt_abreise", "zuletzt_wohnung_id"}


def strip(item: dict[str, Any], rights: frozenset[str]) -> dict[str, Any]:
    """Buchung ohne die Felder, die der Benutzer nicht sehen darf."""
    drop = set()
    if "finanzen" not in rights:
        drop |= FINANCE_KEYS
    if "gaeste" not in rights:
        drop |= GUEST_KEYS
    return {k: v for k, v in item.items() if k not in drop} if drop else item

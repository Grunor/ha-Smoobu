"""Zugangs-Anleitung für Reinigungskräfte (v1.20.0b4, Wunsch Betreiber 28.11.2026).

Zweck: Eine neue Reinigungskraft soll ohne Hilfe in die HA-App und auf das Reinigungsboard kommen. In den
Einstellungen (Reiter „Reinigung & Zugang“) erzeugt die Karte je Benutzer einen fertigen Text zum Kopieren
oder Teilen (WhatsApp, Signal, SMS). Entscheidungen Betreiber 28.11.2026:
- erst einmal nur Text (kein PDF) – die Nachricht kommt auf dem Handy an, auf dem auch die App läuft;
  Links lassen sich dort antippen, QR-Codes wären nur auf Papier sinnvoll
- Sprache je Reinigungskraft wählbar (de, en, pl, nl, fr – wie die Gastsprachen)
- Companion App (nicht Browser): Pushes bei Zuweisung und am Vorabend kommen nur über die App
- Schritt „Passwort ändern“ gehört dazu. HA kann einen Wechsel beim ersten Login NICHT erzwingen, deshalb
  bittet der Text darum und der Fokus-Modus lässt die Seite /profile/security zu (rechte.focus_of)
- Ansprechpartner aus den Einstellungen (Name + Telefon); leer = Name des Benutzers, der den Text erzeugt

Bewusst NICHT im Text: das Passwort. Der Text sagt, dass es separat kommt (anderer Kanal als die Nachricht,
damit Adresse, Benutzername und Passwort nie zusammen in einem Chatverlauf stehen). Es wird nichts
gespeichert; der Text entsteht bei jedem Aufruf neu.

Adresse: externe URL von HA, Nabu Casa bevorzugt (helpers.network.get_url mit prefer_cloud). Ohne externe
Adresse gibt es einen Fehler statt einer Anleitung, die außerhalb des Heimnetzes nicht funktioniert.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

CONF_GUIDE_LANGS = "zugang_sprachen"           # {HA-Benutzer-ID: Sprachcode}
CONF_GUIDE_CONTACT_NAME = "zugang_kontakt_name"
CONF_GUIDE_CONTACT_PHONE = "zugang_kontakt_telefon"
LANGS = ("de", "en", "pl", "nl", "fr")
DEFAULT_LANG = "de"
PROFILE_SECURITY = "/profile/security"

# Offizielle Store-Seiten der Home-Assistant-Companion-App
APP_IOS = "https://apps.apple.com/app/home-assistant/id1099568401"
APP_ANDROID = "https://play.google.com/store/apps/details?id=io.homeassistant.companion.android"

# Textbausteine je Sprache. Formatierung im WhatsApp-Stil (*fett*); in anderen Messengern bleiben nur Sternchen.
# Platzhalter: {name} {url} {user} {wohnungen} {kontakt} {ios} {android} {pw_url}
TEXTS: dict[str, dict[str, str]] = {
    "de": {
        "hallo": "Hallo *{name}*, so kommst du in unsere Reinigungsplanung 🧹",
        "s1": "*1. App installieren*", "ios": "iPhone", "android": "Android",
        "s2": "*2. Server verbinden*",
        "s2t": "App öffnen → „Adresse manuell eingeben“ wählen und diese Adresse einfügen (lange drücken → kopieren):",
        "s3": "*3. Anmelden*", "user": "Benutzername", "pw": "Passwort: bekommst du separat von mir.",
        "perm": "Benachrichtigungen bitte *erlauben*, Standort *ablehnen*.",
        "s4": "*4. Passwort ändern (bitte gleich machen)*",
        "s4t": "Nach dem Anmelden diesen Link öffnen oder auf der Reinigungsseite auf 🔑 tippen:",
        "s5": "*5. So geht's*",
        "s5t": "Du siehst die Reinigungen für {wohnungen}. Übernimm eine Reinigung und hake sie nach dem Putzen ab.",
        "push": "Du bekommst eine Nachricht, wenn dir eine Reinigung zugewiesen wird, und am Vorabend.",
        "fragen": "Fragen? {kontakt}", "und": "und",
    },
    "en": {
        "hallo": "Hi *{name}*, here's how to get into our cleaning schedule 🧹",
        "s1": "*1. Install the app*", "ios": "iPhone", "android": "Android",
        "s2": "*2. Connect the server*",
        "s2t": "Open the app → choose \"Enter address manually\" and paste this address (long press → copy):",
        "s3": "*3. Log in*", "user": "Username", "pw": "Password: I'll send it to you separately.",
        "perm": "Please *allow* notifications and *deny* location.",
        "s4": "*4. Change your password (please do it right away)*",
        "s4t": "After logging in, open this link or tap 🔑 on the cleaning page:",
        "s5": "*5. How it works*",
        "s5t": "You'll see the cleanings for {wohnungen}. Take over a cleaning and tick it off when you're done.",
        "push": "You'll get a message when a cleaning is assigned to you, and the evening before.",
        "fragen": "Questions? {kontakt}", "und": "and",
    },
    "pl": {
        "hallo": "Cześć *{name}*, tak dostaniesz się do naszego planu sprzątania 🧹",
        "s1": "*1. Zainstaluj aplikację*", "ios": "iPhone", "android": "Android",
        "s2": "*2. Połącz z serwerem*",
        "s2t": "Otwórz aplikację → wybierz „Wprowadź adres ręcznie” i wklej ten adres (przytrzymaj → kopiuj):",
        "s3": "*3. Zaloguj się*", "user": "Nazwa użytkownika", "pw": "Hasło: wyślę Ci osobno.",
        "perm": "Powiadomienia proszę *zezwolić*, lokalizację *odrzucić*.",
        "s4": "*4. Zmień hasło (najlepiej od razu)*",
        "s4t": "Po zalogowaniu otwórz ten link albo dotknij 🔑 na stronie sprzątania:",
        "s5": "*5. Jak to działa*",
        "s5t": "Widzisz sprzątania dla {wohnungen}. Przejmij sprzątanie i odhacz je po zakończeniu.",
        "push": "Dostaniesz wiadomość, gdy zostanie Ci przydzielone sprzątanie, oraz wieczorem dzień wcześniej.",
        "fragen": "Pytania? {kontakt}", "und": "i",
    },
    "nl": {
        "hallo": "Hoi *{name}*, zo kom je in onze schoonmaakplanning 🧹",
        "s1": "*1. App installeren*", "ios": "iPhone", "android": "Android",
        "s2": "*2. Server verbinden*",
        "s2t": "Open de app → kies „Adres handmatig invoeren” en plak dit adres (lang indrukken → kopiëren):",
        "s3": "*3. Inloggen*", "user": "Gebruikersnaam", "pw": "Wachtwoord: krijg je apart van mij.",
        "perm": "Meldingen graag *toestaan*, locatie *weigeren*.",
        "s4": "*4. Wachtwoord wijzigen (graag meteen)*",
        "s4t": "Open na het inloggen deze link of tik op de schoonmaakpagina op 🔑:",
        "s5": "*5. Zo werkt het*",
        "s5t": "Je ziet de schoonmaakbeurten voor {wohnungen}. Neem een schoonmaakbeurt over en vink die na het schoonmaken af.",
        "push": "Je krijgt een bericht als je een schoonmaakbeurt toegewezen krijgt, en de avond ervoor.",
        "fragen": "Vragen? {kontakt}", "und": "en",
    },
    "fr": {
        "hallo": "Bonjour *{name}*, voici comment accéder à notre planning de ménage 🧹",
        "s1": "*1. Installer l'application*", "ios": "iPhone", "android": "Android",
        "s2": "*2. Connecter le serveur*",
        "s2t": "Ouvre l'application → choisis « Saisir l'adresse manuellement » et colle cette adresse (appui long → copier) :",
        "s3": "*3. Se connecter*", "user": "Nom d'utilisateur", "pw": "Mot de passe : je te l'envoie séparément.",
        "perm": "Notifications : *autoriser*, localisation : *refuser*.",
        "s4": "*4. Changer le mot de passe (de préférence tout de suite)*",
        "s4t": "Après la connexion, ouvre ce lien ou touche 🔑 sur la page ménage :",
        "s5": "*5. Comment ça marche*",
        "s5t": "Tu vois les ménages pour {wohnungen}. Prends un ménage et coche-le une fois terminé.",
        "push": "Tu reçois un message quand un ménage t'est attribué, et la veille au soir.",
        "fragen": "Des questions ? {kontakt}", "und": "et",
    },
}

class GuideError(Exception):
    """Anleitung nicht möglich (Code: no_external_url, user_not_found, is_admin)."""


def lang_of(options: Any, user_id: str) -> str:
    """Gespeicherte Sprache eines Benutzers (unbekannt/leer → Deutsch)."""
    lang = ((options or {}).get(CONF_GUIDE_LANGS) or {}).get(user_id)
    return lang if lang in LANGS else DEFAULT_LANG


def login_name(user: Any) -> str | None:
    """Anmeldename eines HA-Benutzers (Anbieter „homeassistant“); None bei z. B. reinen Token-Benutzern."""
    for cred in getattr(user, "credentials", None) or []:
        if getattr(cred, "auth_provider_type", None) == "homeassistant":
            name = (getattr(cred, "data", None) or {}).get("username")
            if name:
                return str(name)
    return None


def server_url(hass: HomeAssistant) -> str:
    """Externe Adresse (Nabu Casa bevorzugt) ohne Schrägstrich am Ende; sonst GuideError."""
    from homeassistant.helpers.network import NoURLAvailableError, get_url

    try:
        url = get_url(hass, allow_internal=False, allow_ip=False, prefer_cloud=True)
    except NoURLAvailableError as err:
        raise GuideError("no_external_url") from err
    return url.rstrip("/")


def _join(items: list[str], und: str) -> str:
    """„A“, „A und B“, „A, B und C“ (Wohnungsnamen im Fließtext)."""
    items = [i for i in items if i]
    if len(items) <= 1:
        return items[0] if items else ""
    return f"{', '.join(items[:-1])} {und} {items[-1]}"


def build_text(lang: str, *, name: str, user: str | None, url: str, wohnungen: list[str],
               kontakt_name: str = "", kontakt_telefon: str = "", push: bool = True) -> str:
    """Fertige Nachricht. Reine Funktion (ohne hass) – testbar und in allen Sprachen gleich aufgebaut."""
    tx = TEXTS.get(lang) or TEXTS[DEFAULT_LANG]
    kontakt = ", ".join(p for p in (kontakt_name.strip(), kontakt_telefon.strip()) if p)
    apts = _join(wohnungen, tx["und"]) or "—"
    lines = [
        tx["hallo"].format(name=name), "",
        tx["s1"], f"{tx['ios']}: {APP_IOS}", f"{tx['android']}: {APP_ANDROID}", "",
        tx["s2"], tx["s2t"], url, "",
        tx["s3"], *([f"{tx['user']}: *{user}*"] if user else []), tx["pw"], tx["perm"], "",
        tx["s4"], tx["s4t"], f"{url}{PROFILE_SECURITY}", "",
        tx["s5"], tx["s5t"].format(wohnungen=apts) + (f" {tx['push']}" if push else ""),
    ]
    if kontakt:
        lines += ["", tx["fragen"].format(kontakt=kontakt)]
    return "\n".join(lines)


async def async_guide(hass: HomeAssistant, entry: Any, user_id: str, author: Any, lang: str | None = None,
                      kontakt_name: str | None = None, kontakt_telefon: str | None = None) -> dict[str, Any]:
    """Anleitung für einen Benutzer. Werte aus der Karte (Entwurf) haben Vorrang vor den gespeicherten
    Optionen, damit der Text auch vor dem Speichern stimmt."""
    from .reinigung import CONF_CLEANING_NOTIFY

    target = await hass.auth.async_get_user(user_id)
    if target is None or target.system_generated or not target.is_active:
        raise GuideError("user_not_found")
    if target.is_admin:
        # Admins sind nie im Fokus-Modus; ihr Anmeldename soll nicht über die Karte an Verwalter gehen
        raise GuideError("is_admin")
    o = entry.options
    lang = lang if lang in LANGS else lang_of(o, user_id)
    name_c = (kontakt_name if kontakt_name is not None else o.get(CONF_GUIDE_CONTACT_NAME, "")) or ""
    phone_c = (kontakt_telefon if kontakt_telefon is not None else o.get(CONF_GUIDE_CONTACT_PHONE, "")) or ""
    if not name_c.strip():
        name_c = getattr(author, "name", "") or ""  # Standard: wer den Text erzeugt (Entscheidung 28.11.2026)
    url = server_url(hass)
    coordinator = getattr(entry, "runtime_data", None)
    data = getattr(coordinator, "data", None) if coordinator else None
    apts = [str(a.get("name") or i) for i, a in (data.apartments if data else {}).items()]
    user = login_name(target)
    push = bool(o.get(CONF_CLEANING_NOTIFY, True)) and bool(o.get("module_reinigung", True))
    text = build_text(lang, name=target.name or user or "", user=user, url=url, wohnungen=apts,
                      kontakt_name=name_c, kontakt_telefon=phone_c, push=push)
    return {"text": text, "sprache": lang, "url": url, "benutzername": user, "name": target.name}

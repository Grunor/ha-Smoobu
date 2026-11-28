"""Zugangs-Anleitung (zugang.py, v1.20.0b4): Text je Sprache, Websocket mit Rechteprüfung, Einstellungen."""
from custom_components.smoobu import settings, zugang
from custom_components.smoobu.const import DOMAIN

from .test_smoobu import setup  # noqa: F401  (Fixture)

URL = "https://abc123.ui.nabu.casa"


def test_text_alle_sprachen():
    """Jede Sprache enthält Adresse, Profil-Link, Store-Links, Benutzername – und nie ein Passwort-Feld mit Wert."""
    for lang in zugang.LANGS:
        text = zugang.build_text(lang, name="Maria", user="maria", url=URL, wohnungen=["Haus Hutzelbuck"],
                                 kontakt_name="René", kontakt_telefon="0170 123")
        assert f"\n{URL}\n" in text and f"{URL}/profile/security" in text
        assert zugang.APP_IOS in text and zugang.APP_ANDROID in text
        assert "*maria*" in text and "Haus Hutzelbuck" in text and "René, 0170 123" in text
        assert set(zugang.TEXTS[lang]) == set(zugang.TEXTS["de"])  # gleiche Bausteine in allen Sprachen
    # ohne Push, ohne Kontakt, ohne Benutzername, mehrere Wohnungen
    t = zugang.build_text("de", name="M", user=None, url=URL, wohnungen=["A", "B", "C"], push=False)
    assert "A, B und C" in t and "Vorabend" not in t and "Fragen?" not in t and "Benutzername" not in t
    assert "\n\n\n" not in t
    assert zugang.build_text("xx", name="M", user="m", url=URL, wohnungen=[]).startswith("Hallo")  # Fallback de


async def test_ws_anleitung(hass, setup, hass_ws_client, hass_admin_user, hass_read_only_user, hass_read_only_access_token):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    hass.config.external_url = URL
    login = zugang.login_name(hass_read_only_user)  # Testbenutzer bringt Anmeldedaten „homeassistant“ mit
    assert login
    hass.config_entries.async_update_entry(entry, options={**entry.options,
        "user_roles": {hass_read_only_user.id: "reinigung"}, zugang.CONF_GUIDE_LANGS: {hass_read_only_user.id: "pl"},
        zugang.CONF_GUIDE_CONTACT_PHONE: "0170 1"})
    await hass.async_block_till_done()

    ws = await hass_ws_client(hass)  # Admin
    await ws.send_json({"id": 1, "type": "smoobu/guide", "user_id": hass_read_only_user.id})
    res = (await ws.receive_json())["result"]
    assert res["sprache"] == "pl" and res["url"] == URL and res["benutzername"] == login
    assert res["text"].startswith("Cześć") and f"{hass_admin_user.name}, 0170 1" in res["text"]  # Kontakt leer → Admin
    # Werte aus dem Entwurf haben Vorrang
    await ws.send_json({"id": 2, "type": "smoobu/guide", "user_id": hass_read_only_user.id, "sprache": "en",
                        "kontakt_name": "René", "kontakt_telefon": ""})
    res = (await ws.receive_json())["result"]
    assert res["text"].startswith("Hi") and "Questions? René" in res["text"]
    # Admins bekommen keine Anleitung
    await ws.send_json({"id": 3, "type": "smoobu/guide", "user_id": hass_admin_user.id})
    assert (await ws.receive_json())["error"]["code"] == "is_admin"
    # ohne externe Adresse: Fehler statt Anleitung
    hass.config.external_url = None
    await ws.send_json({"id": 4, "type": "smoobu/guide", "user_id": hass_read_only_user.id})
    assert (await ws.receive_json())["error"]["code"] == "no_external_url"

    # Reinigungskraft selbst (ohne Recht „einstellungen“) darf keine Anleitung erzeugen
    ws2 = await hass_ws_client(hass, hass_read_only_access_token)
    await ws2.send_json({"id": 1, "type": "smoobu/guide", "user_id": hass_read_only_user.id})
    assert (await ws2.receive_json())["error"]["code"] == "unauthorized"


async def test_einstellungen(hass, setup, hass_admin_user):  # noqa: F811
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    opts, err = settings.validate(hass, entry, {zugang.CONF_GUIDE_LANGS: {"u": "nl", "v": ""},
                                                zugang.CONF_GUIDE_CONTACT_NAME: " René ",
                                                zugang.CONF_GUIDE_CONTACT_PHONE: "+49 170 / 123-4"}, hass_admin_user)
    assert not err and opts[zugang.CONF_GUIDE_LANGS] == {"u": "nl"} and opts[zugang.CONF_GUIDE_CONTACT_NAME] == "René"
    _o, err = settings.validate(hass, entry, {zugang.CONF_GUIDE_LANGS: {"u": "xx"},
                                              zugang.CONF_GUIDE_CONTACT_PHONE: "abc"}, hass_admin_user)
    assert err == {zugang.CONF_GUIDE_LANGS: "invalid_lang", zugang.CONF_GUIDE_CONTACT_PHONE: "invalid_phone"}

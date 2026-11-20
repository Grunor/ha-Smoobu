"""Kanal-Auswahl (v1.18.0): Buchungen + Optionen + Smoobu-Katalog, ohne Doppelte."""

from custom_components.smoobu.channel_catalog import (
    SMOOBU_CHANNEL_CATALOG,
    channel_choices,
    configured_channels,
)


def _rec(kanal, anreise="2026-05-01", blockiert=False):
    return {"kanal": kanal, "anreise": anreise, "blockiert": blockiert}


def test_groups_order_and_dedup():
    records = [
        _rec("Booking.com", "2026-03-01"), _rec("Booking.com", "2026-08-01"), _rec("Airbnb"),
        _rec("Hundeurlaub.de"), _rec("Blockiert", blockiert=True), _rec("Blocked channel"),
    ]
    res = channel_choices(records, configured_channels({}, {"Airbnb": 15, "HomeToGo": 15}, ["booking.com", "Website"]))
    # 1) Buchungen nach Anzahl, mit letzter Anreise; Sperr-Kanäle fehlen
    assert [c["name"] for c in res["buchungen"]] == ["Booking.com", "Airbnb", "Hundeurlaub.de"]
    assert res["buchungen"][0] == {"name": "Booking.com", "buchungen": 2, "letzte": "2026-08-01"}
    # 2) eingestellt ohne Kanäle mit Buchungen (Abgleich ohne Groß-/Kleinschreibung)
    assert res["eingestellt"] == ["HomeToGo", "Website"]
    # 3) Katalog: weder Doppelte noch Sperr-Kanäle, gängige Namen zuerst
    low = [n.casefold() for n in res["alle"]]
    assert len(low) == len(set(low))
    assert not any(n.startswith("blocked") for n in low)
    assert res["katalog"][:3] == ["FeWo-direkt", "Expedia", "Vrbo"]
    assert "Agoda" in res["katalog"] and "HomeToGo" not in res["katalog"]


def test_catalog_covers_known_portals():
    names = set(SMOOBU_CHANNEL_CATALOG.values())
    assert {"HomeToGo", "Airbnb", "Booking.com", "Hundeurlaub.de", "HRS Destination / ImWeb"} <= names
    assert SMOOBU_CHANNEL_CATALOG[144] == "HomeToGo"


def test_configured_channels_from_option_keys():
    opts = {"direct_channels": ["Website"], "channel_markups": {"HomeToGo": 10}}
    assert configured_channels(opts, "direct_channels", "channel_markups", "missing") == ["Website", "HomeToGo"]

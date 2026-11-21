"""v1.18.0: Register „Was ist neu“ / neue Einstellungen – Pflichtfelder, eindeutige IDs, gültige Ziele und Rechte."""
from custom_components.smoobu.const import TASK_CATEGORIES
from custom_components.smoobu.neuigkeiten import NEWS, for_user
from custom_components.smoobu.rechte import RIGHTS

PAGES = {"smoobu", "smoobu-kalender", "smoobu-buchungen", "smoobu-finanzen", "smoobu-statistik", "smoobu-nachrichten",
         "smoobu-assistent", "smoobu-einstellungen", "smoobu-reinigung"}
TABS = {"benachrichtigungen", "assistent", "provisionen", "kosten", "reinigung", "rechte", "allgemein"}


def test_register_valid():
    ids = [n["id"] for n in NEWS]
    assert len(ids) == len(set(ids)), "IDs müssen eindeutig sein"
    for n in NEWS:
        assert n["art"] in ("einstellung", "funktion") and n["recht"] in RIGHTS and n["seite"] in PAGES
        assert all(n.get(k) for k in ("titel", "titel_en", "text", "text_en", "version", "sel"))
        if n["art"] == "einstellung":
            assert n["seite"] == "smoobu-einstellungen" and n.get("tab") in TABS
    assert "einrichtung" in TASK_CATEGORIES


def test_for_user_filters_by_right():
    only_guests = for_user({"gaeste"})
    assert only_guests and all(n["recht"] == "gaeste" for n in only_guests)
    assert len(for_user(set(RIGHTS))) == len(NEWS)

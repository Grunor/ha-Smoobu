# Mitmachen / Contributing

Danke für dein Interesse! Fehlerberichte, Ideen und Pull Requests sind willkommen.
Thanks for your interest! Bug reports, ideas and pull requests are welcome.

## Deutsch

### Fragen, Fehler, Wünsche
- **Fragen** zur Einrichtung oder Nutzung: [Discussions](https://github.com/Grunor/ha-Smoobu/discussions)
- **Fehler** und **Funktionswünsche**: [neues Issue](https://github.com/Grunor/ha-Smoobu/issues/new/choose) mit dem passenden Formular
- **Sicherheitslücken** privat melden, siehe [SECURITY.md](SECURITY.md)
- Keine API-Schlüssel, Secrets oder echten Gästedaten posten – Issues sind öffentlich

### Branches und Versionen
- `develop` sammelt alle Änderungen. **Pull Requests bitte gegen `develop`.**
- `main` enthält nur freigegebene Versionen (Fast-Forward von `develop`).
- Versionen nach SemVer in `custom_components/smoobu/manifest.json`. Beta = `x.y.zbN` auf `develop` → Pre-Release; stabile Version auf `main` → Release. Tag, Release-Text (aus dem Changelog) und `smoobu.zip` erzeugt der Workflow `release.yml`.

### Entwickeln
```bash
pip install -r requirements_test.txt
python -m pytest
```
- Die Integration in einer Test-Instanz von Home Assistant ausprobieren: Ordner `custom_components/smoobu` in `config/custom_components/` kopieren und Home Assistant neu starten.
- Die Dashboard-Karten liegen in `custom_components/smoobu/www/smoobu-cards.js` (ein File, ohne Build-Schritt). Texte stehen auf Deutsch im Code; englische Übersetzungen im EN-Wörterbuch derselben Datei (`t("…")`).
- Texte der Einrichtung und Optionen: `strings.json` und `translations/de.json` + `en.json` immer gemeinsam ändern.

### Screenshots
Die Bilder in `docs/screenshots` entstehen aus der echten Integration mit **erfundenen Demodaten**:
```bash
pip install playwright && playwright install chromium
python -m pytest tools/screenshots/render_screenshots.py -p no:cacheprovider   # einzelne Karten
python -m pytest tools/screenshots/render_pages.py -p no:cacheprovider         # ganze Seiten
```
Nie Screenshots mit echten Gästen oder Umsätzen einreichen.

### Changelog
Jede Änderung bekommt einen Eintrag in `CHANGELOG.md` unter **„## Unveröffentlicht / Unreleased“**: erst **Deutsch**, dann **English**, kurz und aus Nutzersicht.

## English

### Questions, bugs, ideas
- **Questions** about setup or usage: [Discussions](https://github.com/Grunor/ha-Smoobu/discussions)
- **Bugs** and **feature requests**: [new issue](https://github.com/Grunor/ha-Smoobu/issues/new/choose) using the matching form
- Report **vulnerabilities** privately, see [SECURITY.md](SECURITY.md)
- Do not post API keys, secrets or real guest data – issues are public

### Branches and versions
- `develop` collects all changes. **Please open pull requests against `develop`.**
- `main` only contains released versions (fast-forward from `develop`).
- SemVer versions in `custom_components/smoobu/manifest.json`. Beta = `x.y.zbN` on `develop` → pre-release; stable version on `main` → release. The `release.yml` workflow creates tag, release notes (from the changelog) and `smoobu.zip`.

### Development
```bash
pip install -r requirements_test.txt
python -m pytest
```
- To try the integration in a test instance, copy `custom_components/smoobu` to `config/custom_components/` and restart Home Assistant.
- The dashboard cards live in `custom_components/smoobu/www/smoobu-cards.js` (single file, no build step). UI texts are German in the code; English translations are in the EN dictionary of the same file (`t("…")`).
- Setup and option texts: always change `strings.json` and `translations/de.json` + `en.json` together.

### Screenshots
The images in `docs/screenshots` are rendered from the real integration with **fictional demo data** (commands above). Never submit screenshots with real guests or revenue.

### Changelog
Every change gets an entry in `CHANGELOG.md` under **"## Unveröffentlicht / Unreleased"**: **German** first, then **English**, short and from the user's point of view.

## Verhaltenskodex / Code of conduct
Siehe / see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

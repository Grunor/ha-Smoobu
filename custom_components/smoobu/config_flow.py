"""Einrichtung über die UI: API-Schlüssel + Secret, Optionen, Neu-Authentifizierung."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.data_entry_flow import section
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    TimeSelector,
)

from .api import SmoobuAuthError, SmoobuClient, SmoobuError
from .codes import all_codes, clean_code
from .notifications import opt_enabled, opt_recipients
from .const import (
    COMMISSION_FIELDS,
    CONF_AI_ENABLED,
    CONF_AI_ENTITY,
    CONF_APARTMENT_CODES,
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_ASSISTANT,
    CONF_ASSIST_BRIEFING,
    CONF_ASSIST_BRIEFING_TIME,
    CONF_ASSIST_GAPS,
    CONF_ASSIST_PATH,
    CONF_ASSIST_STATUS,
    CONF_CHECKOUT_BUFFER,
    CONF_COMMISSIONS,
    CONF_COMMISSION_CUSTOM,
    CONF_COMMISSION_OTHER,
    CONF_DAYS_AHEAD,
    CONF_DAYS_BACK,
    CONF_DEFAULT_CHECKIN,
    CONF_DEFAULT_CHECKOUT,
    CONF_DIRECT_CHANNELS,
    CONF_ENRICH_COUNT,
    CONF_HISTORY_YEARS,
    CONF_NOTIFY_GAPS_TIME,
    CONF_NOTIFY_PAYMENT_DAYS,
    CONF_NOTIFY_PAYMENT_TIME,
    CONF_NOTIFY_QUIET,
    CONF_NOTIFY_QUIET_FROM,
    CONF_NOTIFY_QUIET_MESSAGES,
    CONF_NOTIFY_QUIET_TO,
    CONF_PAYMENT_EXCLUDED_CHANNELS,
    CONF_SCAN_INTERVAL,
    CONF_USER_ID,
    CONF_USE_WEBHOOK,
    DEFAULT_CHECKIN,
    DEFAULT_CHECKOUT,
    DEFAULT_CHECKOUT_BUFFER,
    DEFAULT_COMMISSIONS,
    DEFAULT_COMMISSION_OTHER,
    DEFAULT_DAYS_AHEAD,
    DEFAULT_DAYS_BACK,
    DEFAULT_DIRECT_CHANNELS,
    DEFAULT_ENRICH_COUNT,
    DEFAULT_HISTORY_YEARS,
    DEFAULT_NOTIFY_GAPS_TIME,
    DEFAULT_NOTIFY_PAYMENT_DAYS,
    DEFAULT_NOTIFY_PAYMENT_TIME,
    DEFAULT_NOTIFY_QUIET_FROM,
    DEFAULT_NOTIFY_QUIET_TO,
    DEFAULT_PAYMENT_EXCLUDED_CHANNELS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USE_WEBHOOK,
    DOMAIN,
    MAX_CODE_LEN,
    NOTIFY_TYPES,
)

_LOGGER = logging.getLogger(__name__)

PASSWORD = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): TextSelector(),
        vol.Required(CONF_API_SECRET): PASSWORD,
    }
)


async def _validate(hass, api_key: str, api_secret: str) -> dict[str, Any]:
    """Schlüssel prüfen: /api/me + /api/apartments müssen signiert funktionieren."""
    client = SmoobuClient(async_get_clientsession(hass), api_key, api_secret)
    # Wohnungsliste ist der eigentliche Test (Auth-Fehler → SmoobuAuthError).
    await client.get_apartments()
    try:
        # Profil nur für Titel + Benutzer-ID (Absicherung des Webhooks).
        return await client.get_me()
    except SmoobuAuthError:
        raise
    except SmoobuError as err:
        _LOGGER.debug("/api/me nicht abrufbar: %s", err)
        return {}


class SmoobuConfigFlow(ConfigFlow, domain=DOMAIN):
    """Erst-Einrichtung und Reauth."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                me = await _validate(self.hass, user_input[CONF_API_KEY], user_input[CONF_API_SECRET])
            except SmoobuAuthError:
                errors["base"] = "invalid_auth"
            except SmoobuError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 – unerwartete Fehler dem Nutzer melden
                _LOGGER.exception("Unerwarteter Fehler bei der Smoobu-Prüfung")
                errors["base"] = "unknown"
            else:
                user_id = str(me.get("id") or user_input[CONF_API_KEY])
                # Ein Eintrag je Smoobu-Konto.
                await self.async_set_unique_id(user_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=" ".join(
                        p for p in (me.get("firstName"), me.get("lastName")) if p
                    )
                    or me.get("email")
                    or "Smoobu",
                    data={
                        CONF_API_KEY: user_input[CONF_API_KEY].strip(),
                        CONF_API_SECRET: user_input[CONF_API_SECRET].strip(),
                        CONF_USER_ID: me.get("id"),
                    },
                )
        return self.async_show_form(step_id="user", data_schema=CREDENTIALS_SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                await _validate(self.hass, user_input[CONF_API_KEY], user_input[CONF_API_SECRET])
            except SmoobuAuthError:
                errors["base"] = "invalid_auth"
            except SmoobuError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_API_KEY: user_input[CONF_API_KEY].strip(),
                        CONF_API_SECRET: user_input[CONF_API_SECRET].strip(),
                    },
                )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=CREDENTIALS_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return SmoobuOptionsFlow()


def _time_default(value: str) -> str:
    """'16:00' → '16:00:00' (Format des TimeSelectors)."""
    return value if value.count(":") == 2 else f"{value}:00"


class SmoobuOptionsFlow(OptionsFlow):
    """Abfrageintervall, Zeitfenster, Standardzeiten, Webhook an/aus."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            # TimeSelector liefert HH:MM:SS → auf HH:MM kürzen.
            for key in (CONF_DEFAULT_CHECKIN, CONF_DEFAULT_CHECKOUT):
                user_input[key] = str(user_input[key])[:5]
            for key in (
                CONF_SCAN_INTERVAL,
                CONF_DAYS_BACK,
                CONF_DAYS_AHEAD,
                CONF_ENRICH_COUNT,
                CONF_CHECKOUT_BUFFER,
                CONF_HISTORY_YEARS,
            ):
                user_input[key] = int(user_input[key])
            # Weiter zum Schritt „Provisionen“; beide Schritte werden zusammen gespeichert.
            self._general = user_input
            return await self.async_step_provisionen()

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL, default=opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=120, step=1, unit_of_measurement="min", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_USE_WEBHOOK, default=opts.get(CONF_USE_WEBHOOK, DEFAULT_USE_WEBHOOK)
                ): BooleanSelector(),
                vol.Required(
                    CONF_DEFAULT_CHECKIN,
                    default=_time_default(opts.get(CONF_DEFAULT_CHECKIN, DEFAULT_CHECKIN)),
                ): TimeSelector(),
                vol.Required(
                    CONF_DEFAULT_CHECKOUT,
                    default=_time_default(opts.get(CONF_DEFAULT_CHECKOUT, DEFAULT_CHECKOUT)),
                ): TimeSelector(),
                vol.Required(
                    CONF_CHECKOUT_BUFFER,
                    default=opts.get(CONF_CHECKOUT_BUFFER, DEFAULT_CHECKOUT_BUFFER),
                ): NumberSelector(
                    NumberSelectorConfig(min=0, max=240, step=5, unit_of_measurement="min", mode=NumberSelectorMode.BOX)
                ),
                # Kanäle, deren Zahlung das Portal abwickelt (nicht als offen zählen).
                # Eigene Kanalnamen können frei eingetragen werden.
                vol.Required(
                    CONF_PAYMENT_EXCLUDED_CHANNELS,
                    default=opts.get(
                        CONF_PAYMENT_EXCLUDED_CHANNELS, DEFAULT_PAYMENT_EXCLUDED_CHANNELS
                    ),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=["Airbnb", "Booking.com", "Expedia", "Vrbo", "HomeToGo", "Direct booking", "Website"],
                        multiple=True,
                        custom_value=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_DAYS_BACK, default=opts.get(CONF_DAYS_BACK, DEFAULT_DAYS_BACK)
                ): NumberSelector(
                    NumberSelectorConfig(min=0, max=365, step=1, unit_of_measurement="d", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_DAYS_AHEAD, default=opts.get(CONF_DAYS_AHEAD, DEFAULT_DAYS_AHEAD)
                ): NumberSelector(
                    NumberSelectorConfig(min=30, max=730, step=1, unit_of_measurement="d", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_ENRICH_COUNT, default=opts.get(CONF_ENRICH_COUNT, DEFAULT_ENRICH_COUNT)
                ): NumberSelector(
                    NumberSelectorConfig(min=0, max=20, step=1, mode=NumberSelectorMode.BOX)
                ),
                # Auswertungen/Vergleiche: Jahre vor dem laufenden Jahr (mehr = längere Abfrage)
                vol.Required(
                    CONF_HISTORY_YEARS, default=opts.get(CONF_HISTORY_YEARS, DEFAULT_HISTORY_YEARS)
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=5, step=1, unit_of_measurement="J", mode=NumberSelectorMode.BOX)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_provisionen(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Provision je Kanal und Direktkanäle (für Nettoumsatz / Direkt vs. Portale).

        Die %-Werte gelten nur für Buchungen, zu denen Smoobu keine Provision liefert.
        """
        opts = self.config_entry.options
        commissions: dict[str, float] = dict(opts.get(CONF_COMMISSIONS, DEFAULT_COMMISSIONS))
        errors: dict[str, str] = {}
        if user_input is not None:
            new: dict[str, float] = {
                channel: float(user_input[field]) for field, channel in COMMISSION_FIELDS.items()
            }
            # Freitext „Expedia=18; HomeToGo=15“ für weitere Kanäle
            custom = str(user_input.get(CONF_COMMISSION_CUSTOM) or "")
            for part in filter(None, (p.strip() for p in custom.replace("\n", ";").split(";"))):
                name, sep, value = part.partition("=")
                try:
                    if not sep or not name.strip():
                        raise ValueError
                    new[name.strip()] = float(value.strip().replace(",", "."))
                except ValueError:
                    errors[CONF_COMMISSION_CUSTOM] = "invalid_custom"
                    break
            if not errors:
                self._prov = {
                    CONF_COMMISSIONS: new,
                    CONF_COMMISSION_OTHER: float(user_input[CONF_COMMISSION_OTHER]),
                    CONF_DIRECT_CHANNELS: list(user_input[CONF_DIRECT_CHANNELS]),
                }
                # Weiter zum Schritt „Assistent“; alle Schritte werden zusammen gespeichert.
                return await self.async_step_assistent()

        def pct(field: str) -> vol.Required:
            channel = COMMISSION_FIELDS[field]
            return vol.Required(field, default=commissions.get(channel, DEFAULT_COMMISSIONS[channel]))

        known = set(COMMISSION_FIELDS.values())
        custom_default = "; ".join(
            f"{k}={v:g}" for k, v in commissions.items() if k not in known
        )
        percent = NumberSelector(
            NumberSelectorConfig(min=0, max=50, step=0.1, unit_of_measurement="%", mode=NumberSelectorMode.BOX)
        )
        schema = vol.Schema(
            {
                **{pct(field): percent for field in COMMISSION_FIELDS},
                vol.Required(
                    CONF_COMMISSION_OTHER,
                    default=opts.get(CONF_COMMISSION_OTHER, DEFAULT_COMMISSION_OTHER),
                ): percent,
                vol.Optional(CONF_COMMISSION_CUSTOM, default=custom_default): TextSelector(),
                vol.Required(
                    CONF_DIRECT_CHANNELS,
                    default=opts.get(CONF_DIRECT_CHANNELS, DEFAULT_DIRECT_CHANNELS),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=["Direct booking", "Website", "Airbnb", "Booking.com", "FeWo-direkt"],
                        multiple=True,
                        custom_value=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="provisionen", data_schema=schema, errors=errors)

    async def async_step_assistent(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """KI-Assistent: KI-Hauptschalter, KI-Entität, Push-Empfänger, Kontext-Entitäten, Zusatzaufgaben."""
        opts = self.config_entry.options
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_ASSIST_BRIEFING_TIME] = str(user_input.get(CONF_ASSIST_BRIEFING_TIME) or "07:30")[:5]
            # KI erlauben ohne gewählte KI-Entität ergibt keinen Sinn → Hinweis am Feld
            if user_input.get(CONF_AI_ENABLED) and not user_input.get(CONF_AI_ENTITY):
                errors[CONF_AI_ENTITY] = "ai_entity_required"
            else:
                # Weiter zu „Benachrichtigungen“ und „Wohnungen“; gespeichert wird am Ende alles zusammen.
                self._assist = user_input
                return await self.async_step_benachrichtigungen()
        schema = vol.Schema(
            {
                # Hauptschalter zuerst. Standard: bisheriges Verhalten (KI-Entität gewählt = erlaubt);
                # neue Installationen haben keine KI-Entität → aus.
                vol.Required(
                    CONF_AI_ENABLED, default=opts.get(CONF_AI_ENABLED, bool(opts.get(CONF_AI_ENTITY)))
                ): BooleanSelector(),
                # v1.17.0: Standard an – wirkt ohnehin nur, wenn die KI erlaubt ist („Standard an, wenn KI an“)
                vol.Required(CONF_ASSISTANT, default=opts.get(CONF_ASSISTANT, True)): BooleanSelector(),
                vol.Optional(CONF_AI_ENTITY, description={"suggested_value": opts.get(CONF_AI_ENTITY)}): EntitySelector(
                    EntitySelectorConfig(domain="ai_task")
                ),
                # v1.17.0: Empfänger, Tagesbriefing und Lücken stehen jetzt im Schritt „Benachrichtigungen“
                vol.Optional(CONF_ASSIST_STATUS, default=opts.get(CONF_ASSIST_STATUS, [])): EntitySelector(
                    EntitySelectorConfig(multiple=True)
                ),
                vol.Optional(CONF_ASSIST_PATH, default=opts.get(CONF_ASSIST_PATH, "/lovelace")): TextSelector(),
            }
        )
        return self.async_show_form(step_id="assistent", data_schema=schema, errors=errors)

    def _notify_services(self) -> list[str]:
        """Push-Empfänger: mobile_app-Dienste (nur diese können Buttons wie Senden/Ignorieren)."""
        return sorted(
            f"notify.{svc}" for svc in self.hass.services.async_services().get("notify", {})
            if svc.startswith("mobile_app_")
        )

    async def async_step_benachrichtigungen(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """v1.17.0: Welche Pushes an wen und wann (je Push-Art ein Abschnitt, dazu Ruhezeit)."""
        opts = self.config_entry.options
        if user_input is not None:
            flat: dict[str, Any] = {}
            for kind in NOTIFY_TYPES:
                sec = user_input.get(kind) or {}
                flat[f"notify_{kind}"] = bool(sec.get("aktiv"))
                flat[f"notify_{kind}_to"] = list(sec.get("empfaenger") or [])
            br, gp, pay, quiet = (user_input.get(k) or {} for k in ("briefing", "luecken", "zahlung", "ruhezeit"))
            flat[CONF_ASSIST_BRIEFING_TIME] = str(br.get("uhrzeit") or "07:30")[:5]
            flat[CONF_NOTIFY_GAPS_TIME] = str(gp.get("uhrzeit") or DEFAULT_NOTIFY_GAPS_TIME)[:5]
            flat[CONF_NOTIFY_PAYMENT_TIME] = str(pay.get("uhrzeit") or DEFAULT_NOTIFY_PAYMENT_TIME)[:5]
            flat[CONF_NOTIFY_PAYMENT_DAYS] = int(pay.get("tage") or DEFAULT_NOTIFY_PAYMENT_DAYS)
            flat[CONF_NOTIFY_QUIET] = bool(quiet.get("aktiv"))
            flat[CONF_NOTIFY_QUIET_FROM] = str(quiet.get("von") or DEFAULT_NOTIFY_QUIET_FROM)[:5]
            flat[CONF_NOTIFY_QUIET_TO] = str(quiet.get("bis") or DEFAULT_NOTIFY_QUIET_TO)[:5]
            flat[CONF_NOTIFY_QUIET_MESSAGES] = bool(quiet.get("nachrichten_sofort", True))
            # Alte Schalter mitführen, damit ältere Versionen nach einem Downgrade dasselbe tun
            flat[CONF_ASSIST_BRIEFING] = flat["notify_briefing"]
            flat[CONF_ASSIST_GAPS] = flat["notify_luecken"]
            self._notify = flat
            return await self.async_step_wohnungen()

        services = self._notify_services()
        recipients = SelectSelector(
            SelectSelectorConfig(options=services, multiple=True, custom_value=True, mode=SelectSelectorMode.DROPDOWN)
        )
        hhmm = TimeSelector()

        def kind_section(kind: str, extra: dict | None = None, collapsed: bool = True) -> section:
            fields = {
                vol.Required("aktiv", default=opt_enabled(opts, kind)): BooleanSelector(),
                vol.Optional("empfaenger", default=opt_recipients(opts, kind)): recipients,
                **(extra or {}),
            }
            return section(vol.Schema(fields), {"collapsed": collapsed})

        schema = vol.Schema(
            {
                vol.Required("buchung", default={}): kind_section("buchung", collapsed=False),
                vol.Required("storno", default={}): kind_section("storno"),
                vol.Required("nachricht", default={}): kind_section("nachricht"),
                vol.Required("vorschlag", default={}): kind_section("vorschlag"),
                vol.Required("zahlung", default={}): kind_section("zahlung", {
                    vol.Required("tage", default=int(opts.get(CONF_NOTIFY_PAYMENT_DAYS, DEFAULT_NOTIFY_PAYMENT_DAYS))): NumberSelector(
                        NumberSelectorConfig(min=1, max=60, step=1, unit_of_measurement="d", mode=NumberSelectorMode.BOX)
                    ),
                    vol.Required("uhrzeit", default=_time_default(opts.get(CONF_NOTIFY_PAYMENT_TIME, DEFAULT_NOTIFY_PAYMENT_TIME))): hhmm,
                }),
                vol.Required("briefing", default={}): kind_section("briefing", {
                    vol.Required("uhrzeit", default=_time_default(opts.get(CONF_ASSIST_BRIEFING_TIME, "07:30"))): hhmm,
                }),
                vol.Required("luecken", default={}): kind_section("luecken", {
                    vol.Required("uhrzeit", default=_time_default(opts.get(CONF_NOTIFY_GAPS_TIME, DEFAULT_NOTIFY_GAPS_TIME))): hhmm,
                }),
                vol.Required("ruhezeit", default={}): section(vol.Schema({
                    vol.Required("aktiv", default=bool(opts.get(CONF_NOTIFY_QUIET, False))): BooleanSelector(),
                    vol.Required("von", default=_time_default(opts.get(CONF_NOTIFY_QUIET_FROM, DEFAULT_NOTIFY_QUIET_FROM))): hhmm,
                    vol.Required("bis", default=_time_default(opts.get(CONF_NOTIFY_QUIET_TO, DEFAULT_NOTIFY_QUIET_TO))): hhmm,
                    vol.Required("nachrichten_sofort", default=bool(opts.get(CONF_NOTIFY_QUIET_MESSAGES, True))): BooleanSelector(),
                }), {"collapsed": False}),
            }
        )
        return self.async_show_form(step_id="benachrichtigungen", data_schema=schema)

    async def async_step_wohnungen(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """v1.17.0: Kürzel je Wohnung anpassen (leer = automatisch); eindeutig über alle Smoobu-Konten."""
        entry = self.config_entry
        coordinator = getattr(entry, "runtime_data", None)
        apts = list((coordinator.data.apartments if coordinator and coordinator.data else {}).items())
        # Feldname = Wohnungsname (wird ohne Übersetzung direkt angezeigt); bei gleichen Namen mit ID
        names = [a.get("name") or str(i) for i, a in apts]
        labels = [n if names.count(n) == 1 else f"{n} ({i})" for (i, _a), n in zip(apts, names, strict=True)]
        stored = dict(entry.options.get(CONF_APARTMENT_CODES) or {})
        errors: dict[str, str] = {}
        if user_input is not None or not apts:
            own: dict[str, str] = {}
            for (apt_id, _a), label in zip(apts, labels, strict=True):
                raw = (user_input or {}).get(label, "")
                code = clean_code(raw)
                if str(raw or "").strip() and not code:
                    errors[label] = "invalid_code"
                elif code:
                    own[str(apt_id)] = code
            # Eindeutig: untereinander und gegenüber den Kürzeln der anderen Konten
            others = {v for (eid, _a), v in all_codes(self.hass, {entry.entry_id: own}).items() if eid != entry.entry_id}
            seen: set[str] = set()
            for (apt_id, _a), label in zip(apts, labels, strict=True):
                code = own.get(str(apt_id))
                if code and (code in seen or code in others):
                    errors[label] = "duplicate_code"
                if code:
                    seen.add(code)
            if not errors:
                merged = {**entry.options, **self._general, **self._prov, **self._assist, **self._notify,
                          CONF_APARTMENT_CODES: own}
                # Ohne Auswahl entfernt der Selektor den Schlüssel nicht → explizit leeren,
                # damit eine abgewählte KI-Entität nicht aus den alten Optionen weiterlebt.
                if not self._assist.get(CONF_AI_ENTITY):
                    merged.pop(CONF_AI_ENTITY, None)
                return self.async_create_entry(data=merged)
        auto = all_codes(self.hass, {entry.entry_id: {}})
        schema = vol.Schema(
            {
                vol.Optional(label, description={"suggested_value": stored.get(str(apt_id), "")}): TextSelector()
                for (apt_id, _a), label in zip(apts, labels, strict=True)
            }
        )
        hint = ", ".join(f"{label}: {auto.get((entry.entry_id, int(apt_id)), '?')}"
                         for (apt_id, _a), label in zip(apts, labels, strict=True))
        return self.async_show_form(step_id="wohnungen", data_schema=schema, errors=errors,
                                    description_placeholders={"auto": hint, "max": str(MAX_CODE_LEN)})


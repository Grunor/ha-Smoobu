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
    SelectOptionDict,
    BooleanSelector,
    DateSelector,
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
from .channel_catalog import channel_choices, configured_channels
from .codes import all_codes, clean_code
from .deckungsbeitrag import parse_grid_share, parse_markups
from .energie import CONF_COST_GRID_SHARE_MODE, CONF_COST_GRID_SHARE_YEAR, DEFAULT_COST_GRID_SHARE_YEAR, GRID_SHARE_MODES, grid_share_mode
from .notifications import opt_enabled, opt_quiet, opt_recipients
from . import privacy
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
    CONF_CHANNEL_MARKUPS,
    CONF_COMMISSIONS,
    CONF_COMMISSION_CUSTOM,
    CONF_COST_CLEANING,
    CONF_COST_CLEANING_MINUTES,
    DEFAULT_COST_CLEANING_MINUTES,
    CONF_COST_GRID_PRICE,
    CONF_COST_GRID_SHARE,
    CONF_COST_HEATING_YEAR,
    CONF_COST_HOT_WATER_YEAR,
    CONF_COST_LAUNDRY,
    CONF_COST_POWER_KWH,
    CONF_COST_PV_VALUE,
    CONF_COST_REF_YEAR,
    CONF_COST_WATER_NIGHT,
    CONF_GENIUS_DISCOUNT,
    CONF_GENIUS_SHARE,
    CONF_LASTMINUTE_DAYS,
    CONF_LASTMINUTE_MAX_DISCOUNT,
    CONF_COMMISSION_OTHER,
    CONF_DAYS_AHEAD,
    CONF_DAYS_BACK,
    CONF_DEFAULT_CHECKIN,
    CONF_DEFAULT_CHECKOUT,
    CONF_DIRECT_CHANNELS,
    CONF_ENRICH_COUNT,
    CONF_HISTORY_SINCE,
    CONF_SETTINGS_USERS,
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
    DEFAULT_CHANNEL_MARKUPS,
    DEFAULT_COMMISSIONS,
    DEFAULT_COMMISSION_OTHER,
    DEFAULT_COST_CLEANING,
    DEFAULT_COST_GRID_PRICE,
    DEFAULT_COST_GRID_SHARE,
    DEFAULT_COST_HEATING_YEAR,
    DEFAULT_COST_HOT_WATER_YEAR,
    DEFAULT_COST_LAUNDRY,
    DEFAULT_COST_POWER_KWH,
    DEFAULT_COST_PV_VALUE,
    DEFAULT_COST_REF_YEAR,
    DEFAULT_COST_WATER_NIGHT,
    DEFAULT_GENIUS_DISCOUNT,
    DEFAULT_GENIUS_SHARE,
    DEFAULT_LASTMINUTE_DAYS,
    DEFAULT_LASTMINUTE_MAX_DISCOUNT,
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

    def _channel_options(self) -> list[str]:
        """v1.18.0: Kanal-Auswahl wie in der Einstellungs-Karte (Buchungen, Optionen, Smoobu-Katalog)."""
        entry = self.config_entry
        coordinator = getattr(entry, "runtime_data", None)
        records = coordinator.records_all() if coordinator else []
        o = entry.options
        return channel_choices(records, configured_channels(
            o, CONF_COMMISSIONS, CONF_DIRECT_CHANNELS, CONF_PAYMENT_EXCLUDED_CHANNELS, CONF_CHANNEL_MARKUPS,
        ))["alle"]

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
        # v1.18.0: HA-Benutzer für „Einstellungen im Dashboard erlauben für“ (Admins dürfen immer)
        users = [
            SelectOptionDict(value=u.id, label=f"{u.name or u.id}{' (Admin)' if u.is_admin else ''}")
            for u in await self.hass.auth.async_get_users()
            if u.is_active and not u.system_generated
        ]
        known = {u["value"] for u in users}
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
                # Auswahl: Kanäle aus Buchungen + Optionen + Smoobu-Katalog; eigene Namen weiter möglich.
                vol.Required(
                    CONF_PAYMENT_EXCLUDED_CHANNELS,
                    default=opts.get(
                        CONF_PAYMENT_EXCLUDED_CHANNELS, DEFAULT_PAYMENT_EXCLUDED_CHANNELS
                    ),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=self._channel_options(),
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
                # Auswertungen/Vergleiche: Jahre vor dem laufenden Jahr
                # (je Jahr ca. ein zusätzlicher API-Abruf à 100 Einträge, stündlich – unkritisch)
                vol.Required(
                    CONF_HISTORY_YEARS, default=opts.get(CONF_HISTORY_YEARS, DEFAULT_HISTORY_YEARS)
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=5, step=1, unit_of_measurement="J", mode=NumberSelectorMode.BOX)
                ),
                # Alternativ fester Startpunkt – hat Vorrang vor den Jahren. Optional mit
                # suggested_value statt default, damit das Feld wieder geleert werden kann.
                vol.Optional(
                    CONF_HISTORY_SINCE,
                    description={"suggested_value": opts.get(CONF_HISTORY_SINCE)},
                ): DateSelector(),
                # v1.18.0: Wer außer den Admins die Einstellungskarte im Dashboard nutzen darf.
                # Gelöschte Benutzer fallen still heraus (nur bekannte IDs als Vorbelegung).
                vol.Optional(
                    CONF_SETTINGS_USERS,
                    default=[u for u in opts.get(CONF_SETTINGS_USERS, []) if u in known],
                ): SelectSelector(SelectSelectorConfig(options=users, multiple=True, mode=SelectSelectorMode.DROPDOWN)),
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
                # Weiter zum Schritt „Kosten & Preise“ (v1.18.0); alle Schritte werden zusammen gespeichert.
                return await self.async_step_kosten()

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
                        options=self._channel_options(),
                        multiple=True,
                        custom_value=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="provisionen", data_schema=schema, errors=errors)

    async def async_step_kosten(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """v1.18.0: variable Kosten (Deckungsbeitrag) und Smoobu-Preisaufschläge je Kanal.

        Netzanteil je Monat und Aufschläge sind Freitext (12 Zahlen bzw. „Kanal=Prozent“), weil
        ein Formular mit 12 Einzelfeldern im Options-Dialog unübersichtlich wäre. Die Karte
        „Einstellungen“ im Dashboard zeigt dieselben Werte als Einzelfelder.
        """
        opts = self.config_entry.options
        errors: dict[str, str] = {}
        if user_input is not None:
            data: dict[str, Any] = {}
            for key in (CONF_COST_CLEANING, CONF_COST_CLEANING_MINUTES, CONF_COST_LAUNDRY, CONF_COST_HEATING_YEAR, CONF_COST_HOT_WATER_YEAR,
                        CONF_COST_WATER_NIGHT, CONF_COST_POWER_KWH, CONF_COST_GRID_PRICE, CONF_COST_PV_VALUE,
                        CONF_GENIUS_DISCOUNT, CONF_GENIUS_SHARE, CONF_LASTMINUTE_MAX_DISCOUNT):
                data[key] = float(user_input[key])
            data[CONF_COST_REF_YEAR] = int(user_input[CONF_COST_REF_YEAR])
            # v1.19.1b5: Netzanteil-Quelle + Jahreswert (Sensor je Wohnung: Einstellungen im Dashboard)
            data[CONF_COST_GRID_SHARE_MODE] = user_input.get(CONF_COST_GRID_SHARE_MODE, grid_share_mode(opts))
            data[CONF_COST_GRID_SHARE_YEAR] = float(user_input.get(CONF_COST_GRID_SHARE_YEAR, DEFAULT_COST_GRID_SHARE_YEAR))
            data[CONF_LASTMINUTE_DAYS] = int(user_input[CONF_LASTMINUTE_DAYS])
            try:
                data[CONF_COST_GRID_SHARE] = parse_grid_share(user_input.get(CONF_COST_GRID_SHARE))
            except ValueError:
                errors[CONF_COST_GRID_SHARE] = "invalid_grid_share"
            try:
                data[CONF_CHANNEL_MARKUPS] = parse_markups(user_input.get(CONF_CHANNEL_MARKUPS))
            except ValueError:
                errors[CONF_CHANNEL_MARKUPS] = "invalid_custom"
            if not errors:
                self._cost = data
                return await self.async_step_assistent()

        def num(key: str, default: Any, lo: float, hi: float, step: float, unit: str) -> tuple:
            return (vol.Required(key, default=opts.get(key, default)),
                    NumberSelector(NumberSelectorConfig(min=lo, max=hi, step=step, unit_of_measurement=unit,
                                                        mode=NumberSelectorMode.BOX)))

        fields = [
            num(CONF_COST_CLEANING, DEFAULT_COST_CLEANING, 0, 1000, 0.5, "€/h"),
            num(CONF_COST_CLEANING_MINUTES, DEFAULT_COST_CLEANING_MINUTES, 0, 600, 5, "min"),
            num(CONF_COST_LAUNDRY, DEFAULT_COST_LAUNDRY, 0, 1000, 0.5, "€"),
            num(CONF_COST_HEATING_YEAR, DEFAULT_COST_HEATING_YEAR, 0, 100000, 0.01, "€"),
            num(CONF_COST_HOT_WATER_YEAR, DEFAULT_COST_HOT_WATER_YEAR, 0, 100000, 0.01, "€"),
            num(CONF_COST_REF_YEAR, DEFAULT_COST_REF_YEAR, 2015, 2100, 1, ""),
            num(CONF_COST_WATER_NIGHT, DEFAULT_COST_WATER_NIGHT, 0, 100, 0.01, "€"),
            num(CONF_COST_POWER_KWH, DEFAULT_COST_POWER_KWH, 0, 200, 0.1, "kWh"),
            num(CONF_COST_GRID_PRICE, DEFAULT_COST_GRID_PRICE, 0, 200, 0.01, "ct/kWh"),
            num(CONF_COST_PV_VALUE, DEFAULT_COST_PV_VALUE, 0, 200, 0.01, "ct/kWh"),
            num(CONF_GENIUS_DISCOUNT, DEFAULT_GENIUS_DISCOUNT, 0, 50, 1, "%"),
            num(CONF_GENIUS_SHARE, DEFAULT_GENIUS_SHARE, 0, 100, 1, "%"),
            num(CONF_LASTMINUTE_DAYS, DEFAULT_LASTMINUTE_DAYS, 1, 14, 1, "d"),
            num(CONF_LASTMINUTE_MAX_DISCOUNT, DEFAULT_LASTMINUTE_MAX_DISCOUNT, 0, 30, 1, "%"),
        ]
        share = opts.get(CONF_COST_GRID_SHARE, DEFAULT_COST_GRID_SHARE)
        markups = opts.get(CONF_CHANNEL_MARKUPS, DEFAULT_CHANNEL_MARKUPS)
        schema = vol.Schema({
            **dict(fields),
            vol.Required(CONF_COST_GRID_SHARE_MODE, default=grid_share_mode(opts)): SelectSelector(SelectSelectorConfig(
                options=list(GRID_SHARE_MODES), translation_key="grid_share_mode", mode=SelectSelectorMode.DROPDOWN)),
            vol.Required(CONF_COST_GRID_SHARE, default=", ".join(f"{float(x):g}" for x in share)): TextSelector(),
            vol.Required(CONF_COST_GRID_SHARE_YEAR, default=opts.get(CONF_COST_GRID_SHARE_YEAR, DEFAULT_COST_GRID_SHARE_YEAR)):
                NumberSelector(NumberSelectorConfig(min=0, max=100, step=1, unit_of_measurement="%", mode=NumberSelectorMode.BOX)),
            vol.Optional(CONF_CHANNEL_MARKUPS, default="; ".join(f"{k}={float(v):g}" for k, v in markups.items())):
                TextSelector(),
        })
        return self.async_show_form(step_id="kosten", data_schema=schema, errors=errors)

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
                # v1.18.0b6: Abschnitt „Datenschutz – Einzelschalter“ flach speichern. Fehlt er
                # (nie aufgeklappt), gelten die bisherigen Werte (Abschnitt ohne Default, siehe
                # _notify_schema zum Frontend-Fehler mit Abschnitts-Defaults).
                single = self._privacy_section_schema()(user_input.pop("datenschutz_einzeln", None) or {})
                user_input.update(single)
                user_input[privacy.CONF_AI_HOST_NAMES] = [
                    n.strip() for n in str(single.get(privacy.CONF_AI_HOST_NAMES) or "").replace(";", ",").split(",")
                    if n.strip()
                ]
                user_input[privacy.CONF_AI_HISTORY] = int(user_input[privacy.CONF_AI_HISTORY])
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
                # v1.18.0b6: Datenschutz-Stufe (fehlt = „standard“) und Einzelschalter für „individuell“
                vol.Required(privacy.CONF_AI_PRIVACY, default=privacy.level(opts)): SelectSelector(
                    SelectSelectorConfig(options=privacy.PRIVACY_LEVELS, translation_key="ai_privacy",
                                         mode=SelectSelectorMode.LIST)
                ),
                vol.Optional("datenschutz_einzeln"): section(self._privacy_section_schema(), {"collapsed": True}),
            }
        )
        return self.async_show_form(step_id="assistent", data_schema=schema, errors=errors)

    def _privacy_section_schema(self) -> vol.Schema:
        """Einzelschalter Datenschutz (wirksam nur bei Stufe „individuell“). Defaults = bisherige Werte,
        bei fester Stufe deren Voreinstellung – so startet „individuell“ mit der zuletzt aktiven Stufe."""
        opts = self.config_entry.options
        cur = privacy.resolve(opts)
        if privacy.level(opts) == "individuell":
            cur = {**cur, **{k: opts[k] for k in privacy.FLAGS if k in opts}}
        fields: dict = {}
        for key in privacy.FLAGS:
            if key == privacy.CONF_AI_HISTORY:
                fields[vol.Required(key, default=int(cur[key]))] = NumberSelector(
                    NumberSelectorConfig(min=0, max=privacy.MAX_HISTORY, step=1, mode=NumberSelectorMode.SLIDER)
                )
            else:
                fields[vol.Required(key, default=bool(cur[key]))] = BooleanSelector()
        fields[vol.Optional(
            privacy.CONF_AI_HOST_NAMES,
            default=", ".join(privacy.host_names(opts, self.config_entry.title)),
        )] = TextSelector()
        return vol.Schema(fields)

    def _notify_services(self) -> list[str]:
        """Push-Empfänger: mobile_app-Dienste (nur diese können Buttons wie Senden/Ignorieren)."""
        return sorted(
            f"notify.{svc}" for svc in self.hass.services.async_services().get("notify", {})
            if svc.startswith("mobile_app_")
        )

    def _notify_schema(self) -> vol.Schema:
        """Formular „Benachrichtigungen“: je Push-Art ein Abschnitt, dazu Ruhezeit.

        v1.18.0: Abschnitte sind Optional OHNE default. Ein Abschnitts-Default (früher `default={}`)
        überschreibt im Frontend die Defaults der Felder darin → Pflichtfeld „aktiv“ leer →
        OK-Button gesperrt (Fehler in 1.17.0). Fehlende Abschnitte füllt der Submit-Schritt mit
        den Feld-Defaults auf (siehe async_step_benachrichtigungen).
        """
        opts = self.config_entry.options
        recipients = SelectSelector(
            SelectSelectorConfig(options=self._notify_services(), multiple=True, custom_value=True,
                                 mode=SelectSelectorMode.DROPDOWN)
        )
        hhmm = TimeSelector()

        def kind_section(kind: str, extra: dict | None = None, collapsed: bool = True) -> section:
            fields = {
                vol.Required("aktiv", default=opt_enabled(opts, kind)): BooleanSelector(),
                vol.Optional("empfaenger", default=opt_recipients(opts, kind)): recipients,
                # v1.18.0: an = wird in der Ruhezeit gesammelt, aus = kommt immer sofort
                vol.Required("ruhezeit", default=opt_quiet(opts, kind)): BooleanSelector(),
                **(extra or {}),
            }
            return section(vol.Schema(fields), {"collapsed": collapsed})

        return vol.Schema(
            {
                vol.Optional("buchung"): kind_section("buchung", collapsed=False),
                vol.Optional("storno"): kind_section("storno"),
                vol.Optional("umbuchung"): kind_section("umbuchung"),
                vol.Optional("nachricht"): kind_section("nachricht"),
                vol.Optional("vorschlag"): kind_section("vorschlag"),
                vol.Optional("zahlung"): kind_section("zahlung", {
                    vol.Required("tage", default=int(opts.get(CONF_NOTIFY_PAYMENT_DAYS, DEFAULT_NOTIFY_PAYMENT_DAYS))): NumberSelector(
                        NumberSelectorConfig(min=1, max=60, step=1, unit_of_measurement="d", mode=NumberSelectorMode.BOX)
                    ),
                    vol.Required("uhrzeit", default=_time_default(opts.get(CONF_NOTIFY_PAYMENT_TIME, DEFAULT_NOTIFY_PAYMENT_TIME))): hhmm,
                }),
                vol.Optional("briefing"): kind_section("briefing", {
                    vol.Required("uhrzeit", default=_time_default(opts.get(CONF_ASSIST_BRIEFING_TIME, "07:30"))): hhmm,
                }),
                vol.Optional("luecken"): kind_section("luecken", {
                    vol.Required("uhrzeit", default=_time_default(opts.get(CONF_NOTIFY_GAPS_TIME, DEFAULT_NOTIFY_GAPS_TIME))): hhmm,
                }),
                # v1.20.0 (BETA): Lexware – Zahlungseingang, Anzahlung fehlt, Rest am Anreisetag offen
                vol.Optional("lexware"): kind_section("lexware"),
                # v1.20.0: statischer Türcode läuft ab / Buchung ohne Code
                vol.Optional("tuercode"): kind_section("tuercode"),
                vol.Optional("ruhezeit"): section(vol.Schema({
                    vol.Required("aktiv", default=bool(opts.get(CONF_NOTIFY_QUIET, False))): BooleanSelector(),
                    vol.Required("von", default=_time_default(opts.get(CONF_NOTIFY_QUIET_FROM, DEFAULT_NOTIFY_QUIET_FROM))): hhmm,
                    vol.Required("bis", default=_time_default(opts.get(CONF_NOTIFY_QUIET_TO, DEFAULT_NOTIFY_QUIET_TO))): hhmm,
                }), {"collapsed": False}),
            }
        )

    async def async_step_benachrichtigungen(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """v1.17.0: Welche Pushes an wen und wann (je Push-Art ein Abschnitt, dazu Ruhezeit)."""
        schema = self._notify_schema()
        if user_input is not None:
            # Fehlende Abschnitte mit {} ergänzen → die Abschnitts-Schemas setzen die Feld-Defaults
            # (bisherige Werte), statt dass eine Push-Art stillschweigend „aus“ wird
            user_input = schema({**{k: {} for k in (*NOTIFY_TYPES, "ruhezeit")}, **user_input})
            flat: dict[str, Any] = {}
            for kind in NOTIFY_TYPES:
                sec = user_input.get(kind) or {}
                flat[f"notify_{kind}"] = bool(sec.get("aktiv"))
                flat[f"notify_{kind}_to"] = list(sec.get("empfaenger") or [])
                flat[f"notify_{kind}_quiet"] = bool(sec.get("ruhezeit"))
            br, gp, pay, quiet = (user_input.get(k) or {} for k in ("briefing", "luecken", "zahlung", "ruhezeit"))
            flat[CONF_ASSIST_BRIEFING_TIME] = str(br.get("uhrzeit") or "07:30")[:5]
            flat[CONF_NOTIFY_GAPS_TIME] = str(gp.get("uhrzeit") or DEFAULT_NOTIFY_GAPS_TIME)[:5]
            flat[CONF_NOTIFY_PAYMENT_TIME] = str(pay.get("uhrzeit") or DEFAULT_NOTIFY_PAYMENT_TIME)[:5]
            flat[CONF_NOTIFY_PAYMENT_DAYS] = int(pay.get("tage") or DEFAULT_NOTIFY_PAYMENT_DAYS)
            flat[CONF_NOTIFY_QUIET] = bool(quiet.get("aktiv"))
            flat[CONF_NOTIFY_QUIET_FROM] = str(quiet.get("von") or DEFAULT_NOTIFY_QUIET_FROM)[:5]
            flat[CONF_NOTIFY_QUIET_TO] = str(quiet.get("bis") or DEFAULT_NOTIFY_QUIET_TO)[:5]
            # Altwert für Downgrades: Gästenachrichten sofort = hält die Ruhezeit nicht ein
            flat[CONF_NOTIFY_QUIET_MESSAGES] = not flat["notify_nachricht_quiet"]
            # Alte Schalter mitführen, damit ältere Versionen nach einem Downgrade dasselbe tun
            flat[CONF_ASSIST_BRIEFING] = flat["notify_briefing"]
            flat[CONF_ASSIST_GAPS] = flat["notify_luecken"]
            self._notify = flat
            return await self.async_step_wohnungen()
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
                merged = {**entry.options, **self._general, **self._prov, **getattr(self, "_cost", {}),
                          **self._assist, **self._notify,
                          CONF_APARTMENT_CODES: own}
                # Ohne Auswahl entfernt der Selektor den Schlüssel nicht → explizit leeren,
                # damit eine abgewählte KI-Entität nicht aus den alten Optionen weiterlebt.
                if not self._assist.get(CONF_AI_ENTITY):
                    merged.pop(CONF_AI_ENTITY, None)
                # Gleiches für ein geleertes „Daten abrufen seit“ → wieder „Jahre Historie“
                if not self._general.get(CONF_HISTORY_SINCE):
                    merged.pop(CONF_HISTORY_SINCE, None)
                # v1.20.0: noch ein Schritt „Lexware Office (Beta)“
                self._merged = merged
                return await self.async_step_lexware()
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

    async def async_step_lexware(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """v1.20.0 (BETA): Lexware Office – Grundeinstellungen. Die Regelzeilen (Artikel je Position)
        stellt man in der Einstellungskarte ein (Liste mit Artikel-Auswahl passt nicht in dieses Formular)."""
        from .lexware import (  # noqa: PLC0415
            CONF_LEX_DEPOSIT_DAYS, CONF_LEX_DEPOSIT_PCT, CONF_LEX_ENABLED, CONF_LEX_INVOICE_DATE, CONF_LEX_KEY,
            CONF_LEX_MOCK, CONF_LEX_SEARCH, CONF_LEX_TAX_COMPANY, CONF_LEX_TAX_PRIVATE, CONF_PAID_MEANING, opt,
        )
        from .lexware_zahlung import DEFAULT_PAID_MEANING, PAID_MEANINGS  # noqa: PLC0415

        o = self.config_entry.options
        merged = dict(getattr(self, "_merged", None) or o)
        if user_input is not None:
            key = str(user_input.get(CONF_LEX_KEY) or "").strip()
            merged.update({
                CONF_LEX_ENABLED: bool(user_input.get(CONF_LEX_ENABLED)),
                CONF_LEX_MOCK: bool(user_input.get(CONF_LEX_MOCK)),
                CONF_LEX_TAX_COMPANY: user_input.get(CONF_LEX_TAX_COMPANY, "net"),
                CONF_LEX_TAX_PRIVATE: user_input.get(CONF_LEX_TAX_PRIVATE, "gross"),
                CONF_LEX_INVOICE_DATE: user_input.get(CONF_LEX_INVOICE_DATE, "erstellung"),
                CONF_LEX_DEPOSIT_PCT: float(user_input.get(CONF_LEX_DEPOSIT_PCT, 50)),
                CONF_LEX_DEPOSIT_DAYS: int(user_input.get(CONF_LEX_DEPOSIT_DAYS, 7)),
                CONF_LEX_SEARCH: user_input.get(CONF_LEX_SEARCH, "name"),
                CONF_PAID_MEANING: {"direkt": user_input.get("paid_direkt"), "portal": user_input.get("paid_portal")},
            })
            if key:  # leer = bisherigen Schlüssel behalten
                merged[CONF_LEX_KEY] = key
            elif user_input.get("lexware_api_key_loeschen"):
                merged.pop(CONF_LEX_KEY, None)
            return self.async_create_entry(data=merged)
        meaning = o.get(CONF_PAID_MEANING) or {}

        def sel(options: tuple[str, ...] | list[str], key: str) -> SelectSelector:
            return SelectSelector(SelectSelectorConfig(options=list(options), translation_key=key, mode=SelectSelectorMode.DROPDOWN))

        schema = vol.Schema({
            vol.Required(CONF_LEX_ENABLED, default=bool(opt(o, CONF_LEX_ENABLED))): BooleanSelector(),
            vol.Optional(CONF_LEX_KEY, description={"suggested_value": ""}): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required("lexware_api_key_loeschen", default=False): BooleanSelector(),
            vol.Required(CONF_LEX_MOCK, default=bool(opt(o, CONF_LEX_MOCK))): BooleanSelector(),
            vol.Required(CONF_LEX_TAX_PRIVATE, default=opt(o, CONF_LEX_TAX_PRIVATE)): sel(("gross", "net"), "lex_tax"),
            vol.Required(CONF_LEX_TAX_COMPANY, default=opt(o, CONF_LEX_TAX_COMPANY)): sel(("net", "gross"), "lex_tax"),
            vol.Required(CONF_LEX_INVOICE_DATE, default=opt(o, CONF_LEX_INVOICE_DATE)): sel(("erstellung", "anreise"), "lex_invoice_date"),
            vol.Required(CONF_LEX_DEPOSIT_PCT, default=float(opt(o, CONF_LEX_DEPOSIT_PCT))): NumberSelector(
                NumberSelectorConfig(min=0, max=100, step=1, unit_of_measurement="%", mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_LEX_DEPOSIT_DAYS, default=int(opt(o, CONF_LEX_DEPOSIT_DAYS))): NumberSelector(
                NumberSelectorConfig(min=1, max=60, step=1, unit_of_measurement="d", mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_LEX_SEARCH, default=opt(o, CONF_LEX_SEARCH)): sel(("name", "email", "beide"), "lex_search"),
            vol.Required("paid_direkt", default=meaning.get("direkt") or DEFAULT_PAID_MEANING["direkt"]): sel(PAID_MEANINGS, "paid_meaning"),
            vol.Required("paid_portal", default=meaning.get("portal") or DEFAULT_PAID_MEANING["portal"]): sel(PAID_MEANINGS, "paid_meaning"),
        })
        return self.async_show_form(step_id="lexware", data_schema=schema,
                                    description_placeholders={"key": "gesetzt" if o.get(CONF_LEX_KEY) else "nicht gesetzt"})

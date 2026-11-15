"""Einrichtung über die UI: API-Schlüssel + Secret, Optionen, Neu-Authentifizierung."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
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
from .const import (
    CONF_AI_ENABLED,
    CONF_AI_ENTITY,
    CONF_ASSISTANT,
    CONF_ASSIST_BRIEFING,
    CONF_ASSIST_BRIEFING_TIME,
    CONF_ASSIST_GAPS,
    CONF_ASSIST_PATH,
    CONF_ASSIST_RECIPIENTS,
    CONF_ASSIST_STATUS,
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_CHECKOUT_BUFFER,
    CONF_COMMISSION_CUSTOM,
    CONF_COMMISSION_OTHER,
    CONF_COMMISSIONS,
    CONF_DIRECT_CHANNELS,
    COMMISSION_FIELDS,
    DEFAULT_COMMISSION_OTHER,
    DEFAULT_COMMISSIONS,
    DEFAULT_DIRECT_CHANNELS,
    CONF_DAYS_AHEAD,
    CONF_DAYS_BACK,
    CONF_DEFAULT_CHECKIN,
    CONF_DEFAULT_CHECKOUT,
    CONF_ENRICH_COUNT,
    CONF_HISTORY_YEARS,
    CONF_PAYMENT_EXCLUDED_CHANNELS,
    CONF_SCAN_INTERVAL,
    CONF_USE_WEBHOOK,
    CONF_USER_ID,
    DEFAULT_CHECKIN,
    DEFAULT_CHECKOUT,
    DEFAULT_CHECKOUT_BUFFER,
    DEFAULT_DAYS_AHEAD,
    DEFAULT_DAYS_BACK,
    DEFAULT_ENRICH_COUNT,
    DEFAULT_HISTORY_YEARS,
    DEFAULT_PAYMENT_EXCLUDED_CHANNELS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USE_WEBHOOK,
    DOMAIN,
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
                # Ohne Auswahl entfernt der Selektor den Schlüssel nicht → explizit leeren,
                # damit eine abgewählte KI-Entität nicht aus den alten Optionen weiterlebt.
                merged = {**opts, **self._general, **self._prov, **user_input}
                if not user_input.get(CONF_AI_ENTITY):
                    merged.pop(CONF_AI_ENTITY, None)
                return self.async_create_entry(data=merged)
        # Push-Empfänger: nur mobile_app-Dienste können Buttons (Senden/Ignorieren)
        notify = sorted(
            f"notify.{svc}" for svc in self.hass.services.async_services().get("notify", {})
            if svc.startswith("mobile_app_")
        )
        schema = vol.Schema(
            {
                # Hauptschalter zuerst. Standard: bisheriges Verhalten (KI-Entität gewählt = erlaubt);
                # neue Installationen haben keine KI-Entität → aus.
                vol.Required(
                    CONF_AI_ENABLED, default=opts.get(CONF_AI_ENABLED, bool(opts.get(CONF_AI_ENTITY)))
                ): BooleanSelector(),
                vol.Required(CONF_ASSISTANT, default=opts.get(CONF_ASSISTANT, False)): BooleanSelector(),
                vol.Optional(CONF_AI_ENTITY, description={"suggested_value": opts.get(CONF_AI_ENTITY)}): EntitySelector(
                    EntitySelectorConfig(domain="ai_task")
                ),
                vol.Optional(CONF_ASSIST_RECIPIENTS, default=opts.get(CONF_ASSIST_RECIPIENTS, [])): SelectSelector(
                    SelectSelectorConfig(options=notify, multiple=True, custom_value=True, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Optional(CONF_ASSIST_STATUS, default=opts.get(CONF_ASSIST_STATUS, [])): EntitySelector(
                    EntitySelectorConfig(multiple=True)
                ),
                vol.Optional(CONF_ASSIST_PATH, default=opts.get(CONF_ASSIST_PATH, "/lovelace")): TextSelector(),
                vol.Required(CONF_ASSIST_BRIEFING, default=opts.get(CONF_ASSIST_BRIEFING, False)): BooleanSelector(),
                vol.Required(
                    CONF_ASSIST_BRIEFING_TIME, default=_time_default(opts.get(CONF_ASSIST_BRIEFING_TIME, "07:30"))
                ): TimeSelector(),
                vol.Required(CONF_ASSIST_GAPS, default=opts.get(CONF_ASSIST_GAPS, False)): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="assistent", data_schema=schema, errors=errors)


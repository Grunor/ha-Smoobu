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
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_CHECKOUT_BUFFER,
    CONF_DAYS_AHEAD,
    CONF_DAYS_BACK,
    CONF_DEFAULT_CHECKIN,
    CONF_DEFAULT_CHECKOUT,
    CONF_ENRICH_COUNT,
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
            ):
                user_input[key] = int(user_input[key])
            return self.async_create_entry(data=user_input)

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
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

"""Config flow for SF Express HK integration."""
from __future__ import annotations

import logging
import json
import time
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
    CONF_PHONE_NUMBER,
    CONF_MEMBER_ID,
    API_QUERY_USER_ENDPOINT,
    API_REGION_CODE,
    API_LANGUAGE_CODE,
    API_USER_AGENT,
    API_CONTENT_TYPE,
    API_ACCEPT_ENCODING,
    API_CARRIER,
)
from .utils import generate_syttoken

_LOGGER = logging.getLogger(__name__)

class SFExpressConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SF Express HK."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.data = {}
        self.entry: config_entries.ConfigEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SFExpressOptionsFlow:
        """Get the options flow for this handler."""
        return SFExpressOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_PHONE_NUMBER): str,
                        vol.Required(CONF_MEMBER_ID): str,
                        vol.Required("screensize"): str,
                        vol.Required("mediacode"): str,
                        vol.Required("systemversion"): str,
                        vol.Required("clientversion"): str,
                        vol.Required("model"): str,
                        vol.Required("deviceid"): str,
                        vol.Required("jsbundle"): str,
                    }
                ),
            )

        errors = {}

        try:
            # Verify SF Express credentials
            await self._verify_sf_express(user_input)
            
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth as err:
            errors["base"] = str(err)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            time_interval = str(int(time.time() * 1000))

            self.data = {
                "screensize": user_input["screensize"],
                "mediacode": user_input["mediacode"],
                "systemversion": user_input["systemversion"],
                "clientversion": user_input["clientversion"],
                "model": user_input["model"],
                "deviceid": user_input["deviceid"],
                "jsbundle": user_input["jsbundle"],
                "languagecode": API_LANGUAGE_CODE,
                "mobile": user_input[CONF_PHONE_NUMBER],
                "member_id": user_input[CONF_MEMBER_ID],
            }

            return self.async_create_entry(
                title=user_input[CONF_PHONE_NUMBER],
                data=self.data,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PHONE_NUMBER): str,
                    vol.Required(CONF_MEMBER_ID): str,
                    vol.Required("screensize"): str,
                    vol.Required("mediacode"): str,
                    vol.Required("systemversion"): str,
                    vol.Required("clientversion"): str,
                    vol.Required("model"): str,
                    vol.Required("deviceid"): str,
                    vol.Required("jsbundle"): str,
                }
            ),
            errors=errors,
        )

    async def _verify_sf_express(self, user_input: dict) -> None:
        """Verify SF Express credentials are valid."""
        body_json = json.dumps({
            "memberId": user_input[CONF_MEMBER_ID],
        })

        # Generate syttoken for member verification
        syttoken = generate_syttoken(
            body_json=body_json,
            device_id=user_input["deviceid"],
            client_version=user_input["clientversion"],
            time_interval=str(int(time.time() * 1000)),
            region_code=API_REGION_CODE,
            language_code=API_LANGUAGE_CODE,
            js_bundle=user_input["jsbundle"],
        )
        
        # Prepare headers for member verification
        headers = {
            "screensize": user_input["screensize"],
            "mediacode": user_input["mediacode"],
            "systemversion": user_input["systemversion"],
            "clientversion": user_input["clientversion"],
            "model": user_input["model"],
            "carrier": API_CARRIER,
            "deviceid": user_input["deviceid"],
            "jsbundle": user_input["jsbundle"],
            "regioncode": API_REGION_CODE,
            "memberid": user_input[CONF_MEMBER_ID],
            "mobile": user_input[CONF_PHONE_NUMBER],
            "languagecode": API_LANGUAGE_CODE,
            "timeinterval": str(int(time.time() * 1000)),
            "syttoken": syttoken,
            "content-type": API_CONTENT_TYPE,
            "accept-encoding": API_ACCEPT_ENCODING,
            "user-agent": API_USER_AGENT,
        }

        # Log request details for member verification
        _LOGGER.debug("Request URL: %s", API_QUERY_USER_ENDPOINT)
        _LOGGER.debug("Request Headers: %s", headers)
        _LOGGER.debug("Request Body: %s", body_json)
        _LOGGER.debug("Generated syttoken: %s", syttoken)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_QUERY_USER_ENDPOINT}",
                headers=headers,
                data=body_json,
            ) as response:
                response_text = await response.text()
                
                # Log response details
                _LOGGER.debug("Response Status: %d", response.status)
                _LOGGER.debug("Response Headers: %s", dict(response.headers))
                _LOGGER.debug("Response Body: %s", response_text)

                if response.status != 200:
                    _LOGGER.error(
                        "Error verifying member: %s", response.status
                    )
                    raise CannotConnect

                data = json.loads(response_text)

                if data["success"] == "false":
                    _LOGGER.error(
                        "API Error: %s (Error code: %s)", 
                        data.get("errorMessage", "Unknown error"),
                        data.get("errorCode", "unknown")
                    )
                    raise InvalidAuth(data.get("errorMessage", "Unknown error"))


class SFExpressOptionsFlow(config_entries.OptionsFlow):
    """Handle SF Express options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            try:
                # Verify SF Express credentials
                await self._verify_sf_express(user_input)
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth as err:
                errors["base"] = str(err)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                # Update the config entry with all fields
                data = {
                    "screensize": user_input["screensize"],
                    "mediacode": user_input["mediacode"],
                    "systemversion": user_input["systemversion"],
                    "clientversion": user_input["clientversion"],
                    "model": user_input["model"],
                    "deviceid": user_input["deviceid"],
                    "jsbundle": user_input["jsbundle"],
                    "languagecode": API_LANGUAGE_CODE,
                    CONF_PHONE_NUMBER: user_input[CONF_PHONE_NUMBER],
                    CONF_MEMBER_ID: user_input[CONF_MEMBER_ID],
                }

                # Update the entry
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data=data,
                )

                return self.async_create_entry(title="", data={})

        # Pre-fill with current values
        defaults = {
            CONF_PHONE_NUMBER: self._config_entry.data.get(CONF_PHONE_NUMBER),
            CONF_MEMBER_ID: self._config_entry.data.get(CONF_MEMBER_ID),
            "screensize": self._config_entry.data.get("screensize"),
            "mediacode": self._config_entry.data.get("mediacode"),
            "systemversion": self._config_entry.data.get("systemversion"),
            "clientversion": self._config_entry.data.get("clientversion"),
            "model": self._config_entry.data.get("model"),
            "deviceid": self._config_entry.data.get("deviceid"),
            "jsbundle": self._config_entry.data.get("jsbundle"),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PHONE_NUMBER, default=defaults[CONF_PHONE_NUMBER]): str,
                    vol.Required(CONF_MEMBER_ID, default=defaults[CONF_MEMBER_ID]): str,
                    vol.Required("screensize", default=defaults["screensize"]): str,
                    vol.Required("mediacode", default=defaults["mediacode"]): str,
                    vol.Required("systemversion", default=defaults["systemversion"]): str,
                    vol.Required("clientversion", default=defaults["clientversion"]): str,
                    vol.Required("model", default=defaults["model"]): str,
                    vol.Required("deviceid", default=defaults["deviceid"]): str,
                    vol.Required("jsbundle", default=defaults["jsbundle"]): str,
                }
            ),
            errors=errors,
        )

    async def _verify_sf_express(self, user_input: dict) -> None:
        """Verify SF Express credentials are valid."""
        body_json = json.dumps({
            "memberId": user_input[CONF_MEMBER_ID],
        })

        # Generate syttoken for member verification
        syttoken = generate_syttoken(
            body_json=body_json,
            device_id=user_input["deviceid"],
            client_version=user_input["clientversion"],
            time_interval=str(int(time.time() * 1000)),
            region_code=API_REGION_CODE,
            language_code=API_LANGUAGE_CODE,
            js_bundle=user_input["jsbundle"],
        )
        
        # Prepare headers for member verification
        headers = {
            "screensize": user_input["screensize"],
            "mediacode": user_input["mediacode"],
            "systemversion": user_input["systemversion"],
            "clientversion": user_input["clientversion"],
            "model": user_input["model"],
            "carrier": API_CARRIER,
            "deviceid": user_input["deviceid"],
            "jsbundle": user_input["jsbundle"],
            "regioncode": API_REGION_CODE,
            "memberid": user_input[CONF_MEMBER_ID],
            "mobile": user_input[CONF_PHONE_NUMBER],
            "languagecode": API_LANGUAGE_CODE,
            "timeinterval": str(int(time.time() * 1000)),
            "syttoken": syttoken,
            "content-type": API_CONTENT_TYPE,
            "accept-encoding": API_ACCEPT_ENCODING,
            "user-agent": API_USER_AGENT,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_QUERY_USER_ENDPOINT}",
                headers=headers,
                data=body_json,
            ) as response:
                response_text = await response.text()
                
                if response.status != 200:
                    _LOGGER.error(
                        "Error verifying member: %s", response.status
                    )
                    raise CannotConnect

                data = json.loads(response_text)

                if data["success"] == "false":
                    _LOGGER.error(
                        "API Error: %s (Error code: %s)", 
                        data.get("errorMessage", "Unknown error"),
                        data.get("errorCode", "unknown")
                    )
                    raise InvalidAuth(data.get("errorMessage", "Unknown error"))


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

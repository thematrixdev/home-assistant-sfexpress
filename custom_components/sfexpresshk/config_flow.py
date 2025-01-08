"""Config flow for SF Express HK integration."""
from __future__ import annotations

import json
import logging
import time
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_PHONE_NUMBER,
    CONF_MEMBER_ID,
    API_REGION_CODE,
    API_LANGUAGE_CODE,
    API_USER_AGENT,
    API_CONTENT_TYPE,
    API_ACCEPT_ENCODING,
    API_CARRIER,
    API_LOGIN_ENDPOINT,
    API_QUERY_USER_ENDPOINT,
)
from .utils import generate_syttoken

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
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
)

class SFExpressConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SF Express HK."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            time_interval = str(int(time.time() * 1000))

            self.data = {
                "screensize": user_input["screensize"],
                "mediacode": user_input["mediacode"],
                "systemversion": user_input["systemversion"],
                "clientversion": user_input["clientversion"],
                "model": user_input["model"],
                "carrier": API_CARRIER,
                "deviceid": user_input["deviceid"],
                "jsbundle": user_input["jsbundle"],
                "regioncode": API_REGION_CODE,
                "languagecode": API_LANGUAGE_CODE,
                "mobile": user_input[CONF_PHONE_NUMBER],
                "member_id": user_input[CONF_MEMBER_ID],
            }

            try:
                body_json = json.dumps({
                    "memberId": user_input[CONF_MEMBER_ID],
                })

                # Generate syttoken for member verification
                syttoken = generate_syttoken(
                    body_json=body_json,
                    device_id=user_input["deviceid"],
                    client_version=user_input["clientversion"],
                    time_interval=time_interval,
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
                    "timeinterval": time_interval,
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
                            errors["base"] = "cannot_connect"
                            return self.async_show_form(
                                step_id="user",
                                data_schema=STEP_USER_DATA_SCHEMA,
                                errors=errors,
                            )

                        data = await response.json()

                        if data["success"] == "false":
                            _LOGGER.error(
                                "API Error: %s (Error code: %s)", 
                                data.get("errorMessage", "Unknown error"),
                                data.get("errorCode", "unknown")
                            )
                            errors["base"] = "api_error"
                            return self.async_show_form(
                                step_id="user",
                                data_schema=STEP_USER_DATA_SCHEMA,
                                errors=errors,
                                description_placeholders={
                                    "error_detail": data.get("errorMessage", "Unknown error")
                                },
                            )

                        return self.async_create_entry(
                            title=f"SF Express HK ({user_input[CONF_PHONE_NUMBER]})",
                            data=self.data,
                        )

            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

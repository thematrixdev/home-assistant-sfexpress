"""SF Express HK sensor platform."""
from __future__ import annotations

import logging
from datetime import timedelta
import json
import aiohttp

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
import time

from .const import (
    DOMAIN,
    API_REGION_CODE,
    API_LANGUAGE_CODE,
    API_USER_AGENT,
    API_CONTENT_TYPE,
    API_ACCEPT_ENCODING,
    API_CARRIER,
    API_LIST_WAYBILL_ENDPOINT,
    API_QUERY_ROUTE_ENDPOINT,
)
from .utils import generate_syttoken

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SF Express HK sensor."""

    coordinator = SFExpressCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([SFExpressWaybillSensor(coordinator)], True)


class SFExpressCoordinator(DataUpdateCoordinator):
    """SF Express data update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry

    async def _fetch_routes(self, waybill_numbers: list[str], config: dict) -> dict:
        """Fetch route information for waybills."""
        if not waybill_numbers:
            return {}

        time_interval = str(int(time.time() * 1000))
        
        # Prepare request body
        body = {
            "isHtml": "",
            "wayBillNos": waybill_numbers,
            "clientCode": config["mobile"],
            "userId": config["member_id"]
        }
        body_json = json.dumps(body)

        # Generate new syttoken for route query
        syttoken = generate_syttoken(
            body_json=body_json,
            device_id=config["deviceid"],
            client_version=config["clientversion"],
            time_interval=time_interval,
            region_code=API_REGION_CODE,
            language_code=API_LANGUAGE_CODE,
            js_bundle=config["jsbundle"],
        )

        # Prepare headers
        headers = {
            "screensize": config["screensize"],
            "mediacode": config["mediacode"],
            "systemversion": config["systemversion"],
            "clientversion": config["clientversion"],
            "model": config["model"],
            "carrier": API_CARRIER,
            "deviceid": config["deviceid"],
            "jsbundle": config["jsbundle"],
            "regioncode": API_REGION_CODE,
            "memberid": config["member_id"],
            "mobile": config["mobile"],
            "languagecode": API_LANGUAGE_CODE,
            "timeinterval": time_interval,
            "syttoken": syttoken,
            "content-type": API_CONTENT_TYPE,
            "accept-encoding": API_ACCEPT_ENCODING,
            "user-agent": API_USER_AGENT,
        }

        # Log request details
        _LOGGER.debug("Route Request URL: %s", API_QUERY_ROUTE_ENDPOINT)
        _LOGGER.debug("Route Request Headers: %s", headers)
        _LOGGER.debug("Route Request Body: %s", body_json)
        _LOGGER.debug("Route Generated syttoken: %s", syttoken)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_QUERY_ROUTE_ENDPOINT,
                    headers=headers,
                    json=body,
                ) as response:
                    response_text = await response.text()
                    
                    # Log response details
                    _LOGGER.debug("Route Response Status: %d", response.status)
                    _LOGGER.debug("Route Response Headers: %s", dict(response.headers))
                    _LOGGER.debug("Route Response Body: %s", response_text)

                    if response.status != 200:
                        raise aiohttp.ClientError(
                            f"Error fetching routes: {response.status}"
                        )
                    
                    data = json.loads(response_text)
                    
                    if not data.get("success", False):
                        raise aiohttp.ClientError(
                            f"API Error: {data.get('errorMessage', 'Unknown error')}"
                        )
                    
                    # Create a mapping of waybill number to routes
                    routes = {}
                    for waybill in data.get("obj", []):
                        routes[waybill["waybillNo"]] = waybill.get("barNewList", [])
                    
                    return routes
        except Exception as err:
            _LOGGER.error("Error fetching route data: %s", err)
            return {}

    async def _async_update_data(self):
        """Fetch data from SF Express."""
        time_interval = str(int(time.time() * 1000))
        config = self.entry.data

        # Prepare request body
        body = {
            "dataType": 1,
            "mobile": config["mobile"],
            "memberId": config["member_id"],
            "orderStatusList": [],
            "orderType": "1",
            "pageNo": 1,
            "pageRows": 10
        }
        body_json = json.dumps(body)

        # Generate syttoken
        syttoken = generate_syttoken(
            body_json=body_json,
            device_id=config["deviceid"],
            client_version=config["clientversion"],
            time_interval=time_interval,
            region_code=API_REGION_CODE,
            language_code=API_LANGUAGE_CODE,
            js_bundle=config["jsbundle"],
        )

        # Prepare headers
        headers = {
            "screensize": config["screensize"],
            "mediacode": config["mediacode"],
            "systemversion": config["systemversion"],
            "clientversion": config["clientversion"],
            "model": config["model"],
            "carrier": API_CARRIER,
            "deviceid": config["deviceid"],
            "jsbundle": config["jsbundle"],
            "regioncode": API_REGION_CODE,
            "memberid": config["member_id"],
            "mobile": config["mobile"],
            "languagecode": API_LANGUAGE_CODE,
            "timeinterval": time_interval,
            "syttoken": syttoken,
            "content-type": API_CONTENT_TYPE,
            "accept-encoding": API_ACCEPT_ENCODING,
            "user-agent": API_USER_AGENT,
        }

        try:
            # Log request details
            _LOGGER.debug("Request URL: %s", API_LIST_WAYBILL_ENDPOINT)
            _LOGGER.debug("Request Headers: %s", headers)
            _LOGGER.debug("Request Body: %s", body_json)
            _LOGGER.debug("Generated syttoken: %s", syttoken)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_LIST_WAYBILL_ENDPOINT,
                    headers=headers,
                    data=body_json,
                ) as response:
                    response_text = await response.text()
                    
                    # Log response details
                    _LOGGER.debug("Response Status: %d", response.status)
                    _LOGGER.debug("Response Headers: %s", dict(response.headers))
                    _LOGGER.debug("Response Body: %s", response_text)

                    if response.status != 200:
                        raise aiohttp.ClientError(
                            f"Error fetching data: {response.status}"
                        )
                    
                    data = json.loads(response_text)
                    
                    if not data.get("success", False):
                        raise aiohttp.ClientError(
                            f"API Error: {data.get('errorMessage', 'Unknown error')}"
                        )
                    
                    # Get waybills in transit
                    waybills_in_transit = [
                        waybill["waybillno"]
                        for waybill in data["obj"].get("dataList", [])
                        if waybill.get("waybillStatus") != "4"
                    ]

                    # Fetch routes for waybills in transit
                    routes = await self._fetch_routes(waybills_in_transit, config)
                    
                    # Add routes to the waybill data
                    for waybill in data["obj"].get("dataList", []):
                        if waybill["waybillno"] in routes:
                            waybill["routes"] = routes[waybill["waybillno"]]
                    
                    return data["obj"]
        except Exception as err:
            _LOGGER.error("Error updating SF Express data: %s", err)
            raise


class SFExpressWaybillSensor(CoordinatorEntity, SensorEntity):
    """SF Express Waybill sensor."""

    def __init__(self, coordinator: SFExpressCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "SF Express Receiving"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_receiving"

    @property
    def native_value(self):
        """Return the number of active waybills (not delivered)."""
        if self.coordinator.data is None:
            return None
        return sum(1 for waybill in self.coordinator.data.get("dataList", [])
                  if waybill.get("waybillStatus") != "4")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
        
        waybills = []
        for waybill in self.coordinator.data.get("dataList", []):
            # Only include undelivered waybills (waybillStatus != "4")
            if waybill.get("waybillStatus") == "4":
                continue

            waybill_data = {
                "waybillno": waybill.get("waybillno"),
                "updateDateTime": waybill.get("updateDateTime"),
                "expectedDeliveryTime": waybill.get("expectedDeliveryTime"),
                "waybillStatusMessage": waybill.get("waybillStatusMessage"),
                "originateContacts": waybill.get("originateContacts"),
            }
            
            # Add routes if available, sorted by scanDate and scanTime in descending order
            if "routes" in waybill:
                routes = waybill["routes"]
                # Sort routes by scanDate and scanTime in descending order
                sorted_routes = sorted(
                    routes,
                    key=lambda x: (x["scanDate"], x["scanTime"]),
                    reverse=True
                )
                waybill_data["routes"] = sorted_routes
            
            waybills.append(waybill_data)
        
        return {
            "waybills": waybills,
            "my_receive_total": self.coordinator.data.get("myReceiveTotal", 0),
            "my_send_total": self.coordinator.data.get("mySendTotal", 0),
        }

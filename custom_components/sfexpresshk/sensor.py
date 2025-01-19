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
    API_SFBUY_COUNT_ENDPOINT,
    API_PICKUP_CODE_ENDPOINT,
    SFBUY_HEADERS,
    CONF_SFBUY_TICKET,
)
from .utils import generate_syttoken

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SF Express HK sensor."""

    coordinator = SFExpressCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entities = [SFExpressWaybillSensor(coordinator)]
    
    # Only add SFBuy sensors if ticket is configured
    if CONF_SFBUY_TICKET in entry.data:
        entities.extend([
            SFBuyAwaitingRegisterSensor(coordinator),
            SFBuyAwaitingRecordSensor(coordinator),
            SFBuyAwaitingPaymentSensor(coordinator),
            SFBuyAwaitingDeliverySensor(coordinator),
        ])

    async_add_entities(entities, True)


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
        self.sfbuy_data = None
        self._pickup_code_cache = {}  # Cache for pickup codes: {waybill_no: pickup_code}

    async def _fetch_pickup_code(self, waybill_no: str, config: dict) -> str | None:
        """Fetch pickup code for a waybill."""
        # Check cache first
        if waybill_no in self._pickup_code_cache:
            _LOGGER.debug("Using cached pickup code for waybill %s", waybill_no)
            return self._pickup_code_cache[waybill_no]

        time_interval = str(int(time.time() * 1000))
        
        # Prepare request body
        body = {"waybillNo": waybill_no}
        body_json = json.dumps(body)

        # Generate new syttoken for pickup code query
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
            _LOGGER.debug("Pickup Code Request URL: %s", API_PICKUP_CODE_ENDPOINT)
            _LOGGER.debug("Pickup Code Request Headers: %s", headers)
            _LOGGER.debug("Pickup Code Request Body: %s", body_json)
            _LOGGER.debug("Pickup Code Generated syttoken: %s", syttoken)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_PICKUP_CODE_ENDPOINT,
                    headers=headers,
                    json=body,
                ) as response:
                    response_text = await response.text()
                    
                    # Log response details
                    _LOGGER.debug("Pickup Code Response Status: %d", response.status)
                    _LOGGER.debug("Pickup Code Response Headers: %s", dict(response.headers))
                    _LOGGER.debug("Pickup Code Response Body: %s", response_text)

                    if response.status != 200:
                        raise aiohttp.ClientError(
                            f"Error fetching pickup code: {response.status}"
                        )
                    
                    data = json.loads(response_text)
                    
                    if not data.get("success", False):
                        raise aiohttp.ClientError(
                            f"API Error: {data.get('errorMessage', 'Unknown error')}"
                        )
                    
                    rec_code_info = data.get("obj", {}).get("recCodeInfo", {})
                    pickup_code = rec_code_info.get("pickupCode")
                    
                    # Cache the pickup code if it's valid
                    if pickup_code:
                        _LOGGER.debug("Caching pickup code for waybill %s", waybill_no)
                        self._pickup_code_cache[waybill_no] = pickup_code
                    
                    return pickup_code
        except Exception as err:
            _LOGGER.error("Error fetching pickup code: %s", err)
            return None

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

        try:
            # Log request details
            _LOGGER.debug("Route Request URL: %s", API_QUERY_ROUTE_ENDPOINT)
            _LOGGER.debug("Route Request Headers: %s", headers)
            _LOGGER.debug("Route Request Body: %s", body_json)
            _LOGGER.debug("Route Generated syttoken: %s", syttoken)

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
                        waybill_no = waybill["waybillNo"]
                        route_list = waybill.get("barNewList", [])
                        
                        # Sort routes by scanDate and scanTime in descending order
                        sorted_routes = sorted(
                            route_list,
                            key=lambda x: (x["scanDate"], x["scanTime"]),
                            reverse=True
                        )
                        routes[waybill_no] = {
                            "routes": sorted_routes,
                            "pickupCode": None
                        }
                        
                        # Check if the latest route has opCode 125 (待取件)
                        if sorted_routes:
                            latest_route = sorted_routes[0]  # Now this is truly the latest route
                            if latest_route.get("opCode") == "125":
                                pickup_code = await self._fetch_pickup_code(waybill_no, config)
                                if pickup_code:
                                    routes[waybill_no]["pickupCode"] = pickup_code
                                    _LOGGER.debug(
                                        "Added pickup code for waybill %s with latest opCode %s",
                                        waybill_no,
                                        latest_route.get("opCode")
                                    )
                    
                    return routes
        except Exception as err:
            _LOGGER.error("Error fetching route data: %s", err)
            return {}

    async def _fetch_sfbuy_data(self) -> dict:
        """Fetch SFBuy package count data."""
        # Only fetch if ticket is configured
        if CONF_SFBUY_TICKET not in self.entry.data:
            return None

        headers = SFBUY_HEADERS.copy()
        headers["Cookie"] = f"token={self.entry.data[CONF_SFBUY_TICKET]}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_SFBUY_COUNT_ENDPOINT}?operator=",
                    headers=headers,
                ) as response:
                    response_text = await response.text()
                    _LOGGER.debug("SFBuy Response: %s", response_text)
                    
                    if response.status != 200:
                        raise aiohttp.ClientError(
                            f"Error fetching SFBuy data: {response.status}"
                        )
                    
                    data = json.loads(response_text)
                    if data.get("msg") != "成功":
                        raise aiohttp.ClientError(
                            f"API Error: {data.get('msg', 'Unknown error')}"
                        )
                    
                    return data.get("data", {})
        except Exception as err:
            _LOGGER.error("Error fetching SFBuy data: %s", err)
            return None

    async def _async_update_data(self):
        """Fetch data from SF Express."""
        # Clear pickup code cache for waybills that are delivered
        if self.data:
            delivered_waybills = [
                waybill["waybillno"]
                for waybill in self.data.get("dataList", [])
                if waybill.get("waybillStatus") == "4"
            ]
            for waybill_no in delivered_waybills:
                if waybill_no in self._pickup_code_cache:
                    _LOGGER.debug("Removing pickup code cache for delivered waybill %s", waybill_no)
                    del self._pickup_code_cache[waybill_no]

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
                        waybill_no = waybill["waybillno"]
                        if waybill_no in routes:
                            route_data = routes[waybill_no]
                            waybill["routes"] = route_data["routes"]
                            
                            # Only include pickupCode if latest route has opCode 125 and we have a valid code
                            latest_route = route_data["routes"][0] if route_data["routes"] else None
                            if (latest_route and 
                                latest_route.get("opCode") == "125" and 
                                route_data["pickupCode"]):
                                waybill["pickupCode"] = route_data["pickupCode"]
                                _LOGGER.debug(
                                    "Including pickup code for waybill %s in attributes",
                                    waybill_no
                                )
                    
                    # Only fetch SFBuy data if ticket is configured
                    if CONF_SFBUY_TICKET in self.entry.data:
                        self.sfbuy_data = await self._fetch_sfbuy_data()

                    return data["obj"]
        except Exception as err:
            _LOGGER.error("Error updating SF Express data: %s", err)
            raise


class SFExpressWaybillSensor(CoordinatorEntity, SensorEntity):
    """SF Express Waybill sensor."""

    def __init__(self, coordinator: SFExpressCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "SFExpress Receiving"
        self._attr_unique_id = "sfexpress_receiving"

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
            
            # Add pickup code if available
            if "pickupCode" in waybill:
                waybill_data["pickupCode"] = waybill["pickupCode"]
            
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
        }


class SFBuyAwaitingRegisterSensor(CoordinatorEntity[SFExpressCoordinator], SensorEntity):
    """Representation of a SF Express SFBuy Awaiting Register sensor."""

    _attr_native_unit_of_measurement = "packages"
    _attr_has_entity_name = True

    def __init__(self, coordinator: SFExpressCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = "sfbuy_forecast"
        self._attr_name = "SFBuy Awaiting Register"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.coordinator.sfbuy_data:
            return None

        return self.coordinator.sfbuy_data.get("awaitForecastCount", 0)


class SFBuyAwaitingRecordSensor(CoordinatorEntity[SFExpressCoordinator], SensorEntity):
    """Representation of a SF Express SFBuy Awaiting Record sensor."""

    _attr_native_unit_of_measurement = "packages"
    _attr_has_entity_name = True

    def __init__(self, coordinator: SFExpressCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = "sfbuy_storage"
        self._attr_name = "SFBuy Awaiting Record"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.coordinator.sfbuy_data:
            return None

        return self.coordinator.sfbuy_data.get("awaitInStorageCount", 0)


class SFBuyAwaitingPaymentSensor(CoordinatorEntity[SFExpressCoordinator], SensorEntity):
    """Representation of a SF Express SFBuy Awaiting Payment sensor."""

    _attr_native_unit_of_measurement = "packages"
    _attr_has_entity_name = True

    def __init__(self, coordinator: SFExpressCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = "sfbuy_pay"
        self._attr_name = "SFBuy Awaiting Payment"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.coordinator.sfbuy_data:
            return None

        return self.coordinator.sfbuy_data.get("awaitPayCount", 0)


class SFBuyAwaitingDeliverySensor(CoordinatorEntity[SFExpressCoordinator], SensorEntity):
    """Representation of a SF Express SFBuy Awaiting Delivery sensor."""

    _attr_native_unit_of_measurement = "packages"
    _attr_has_entity_name = True

    def __init__(self, coordinator: SFExpressCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = "sfbuy_sign"
        self._attr_name = "SFBuy Awaiting Delivery"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.coordinator.sfbuy_data:
            return None

        return self.coordinator.sfbuy_data.get("awaitSignCount", 0)

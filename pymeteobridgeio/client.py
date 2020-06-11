"""Wrapper to retrieve Sensor data from a Meteobridge Data Logger
   Specifically developed to wotk with Home Assistant
   Developed by: @briis
   Github: https://github.com/briis/pymeteobridgeio
   License: MIT
"""

import csv
import asyncio
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError
from typing import Optional

import logging
from datetime import datetime

from pymeteobridgeio.const import (
    DEFAULT_TIMEOUT,
    DEVICE_CLASS_NONE,
    DEVICE_CLASS_COLD,
    DEVICE_CLASS_DISTANCE,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_RAIN,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_WIND,
    DEVICE_TYPE_BINARY_SENSOR,
    DEVICE_TYPE_NONE,
    DEVICE_TYPE_SENSOR,
    UNIT_SYSTEM_METRIC,
    UNIT_SYSTEM_IMPERIAL,
)
from pymeteobridgeio.errors import (
    InvalidCredentials,
    RequestError,
    ResultError,
)
from pymeteobridgeio.functions import Conversion, Units, HardwareTypes

_LOGGER = logging.getLogger(__name__)


class Meteobridge:
    """Main class to retrieve the data from the Logger."""

    def __init__(
        self,
        Host: str,
        User: str,
        Pass: str,
        unit_system: str = UNIT_SYSTEM_METRIC,
        session: Optional[ClientSession] = None,
    ):
        self._host = Host
        self._user = User
        self._pass = Pass
        self._unit_system = unit_system
        self._session: ClientSession = session

    async def get_sensor_data(self) -> dict:
        """Updates the sensor data."""
        return await self._sensor_data()

    async def get_server_data(self) -> None:
        """Returns Meteobridge Server Data."""
        return await self._meteobridge_server()

    async def _meteobridge_server(self) -> None:
        """Returns Meteobridge Server Specific Information."""
        data_template = "[mbsystem-mac:None];[mbsystem-swversion:0.0].[mbsystem-buildnum:0];[mbsystem-platform:None];[mbsystem-station:None];[mbsystem-wlanip:None];[mbsystem-lanip:None]"
        endpoint = f"http://{self._user}:{self._pass}@{self._host}/cgi-bin/template.cgi?template={data_template}"
        data = await self.async_request("get", endpoint)
        cr = csv.reader(data.splitlines(), delimiter=";")
        rows = list(cr)

        hw_name = HardwareTypes()

        for values in rows:
            item = {
                "mac_address": values[0],
                "swversion": values[1],
                "platform_hw": hw_name.platform(values[2]),
                "station_hw": values[3],
                "wlan_ip": values[4],
                "lan_ip": values[5],
                "ip_address": values[5] if values[4] == "None" else values[4],
            }
        return item

    async def _sensor_data(self) -> None:
        """Gets the sensor data from the Meteobridge Logger"""

        dataTemplate = "[DD]/[MM]/[YYYY];[hh]:[mm]:[ss];[th0temp-act:0];[thb0seapress-act:0];[th0hum-act:0];[wind0avgwind-act:0];[wind0dir-avg5.0:0];[rain0total-daysum:0];[rain0rate-act:0];[th0dew-act:0];[wind0chill-act:0];[wind0wind-max1:0];[th0lowbat-act.0:0];[thb0temp-act:0];[thb0hum-act.0:0];[th0temp-dmax:0];[th0temp-dmin:0];[wind0wind-act:0];[th0heatindex-act.1:0];[uv0index-act:0];[sol0rad-act:0];[th0temp-mmin.1:0];[th0temp-mmax.1:0];[th0temp-ymin.1:0];[th0temp-ymax.1:0];[wind0wind-mmax.1:0];[wind0wind-ymax.1:0];[rain0total-mmax.1:0];[rain0total-ymax.1:0];[rain0rate-mmax.1:0];[rain0rate-ymax.1:0];[lgt0total-act.0:0];[lgt0energy-act.0:0];[lgt0dist-act.0:0];[air0pm-act.0:0];[forecast-text:]"
        endpoint = f"http://{self._user}:{self._pass}@{self._host}/cgi-bin/template.cgi?template={dataTemplate}"

        data = await self.async_request("get", endpoint)
        cr = csv.reader(data.splitlines(), delimiter=";")
        rows = list(cr)
        cnv = Conversion()
        sensor_unit = Units()
        sensor_item = {}

        for values in rows:
            self._outtemp = cnv.temperature(float(values[2]), self._unit_system)
            self._heatindex = cnv.temperature(float(values[18]), self._unit_system)
            self._windchill = cnv.temperature(float(values[10]), self._unit_system)
            self._rainrate = cnv.rate(float(values[8]), self._unit_system)
            sensor_item = {
                "timestamp": {
                    "value": datetime.strptime(f"{values[0]} {values[1]}", "%d/%m/%Y %H:%M:%S"),
                    "name": "Timestamp",
                    "type": DEVICE_TYPE_NONE,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": None,
                    "unit": None
                    },
                "temperature": {
                    "value": self._outtemp,
                    "name": "Temperature",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system)
                    },
                "pressure": {
                    "value": cnv.pressure(float(values[3]), self._unit_system),
                    "name": "Pressure",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_PRESSURE,
                    "icon": "gauge",
                    "unit": sensor_unit.pressure(self._unit_system),
                    },
                "humidity": {
                    "value": values[4],
                    "name": "Humidity",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_HUMIDITY,
                    "icon": "water-percent",
                    "unit": "%",
                    },
                "windspeedavg": {
                    "value": cnv.speed(float(values[5]), self._unit_system),
                    "name": "Wind Speed Avg",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_WIND,
                    "icon": "weather-windy",
                    "unit": sensor_unit.wind(self._unit_system),
                    },
                "windbearing": {
                    "value": int(float(values[6])),
                    "name": "Wind Bearing",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "compass-outline",
                    "unit": "°",
                    },
                "winddirection": {
                    "value": cnv.wind_direction(float(values[6])),
                    "name": "Wind Direction",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "compass-outline",
                    "unit": None,
                    },
                "raintoday": {
                    "value": cnv.volume(float(values[7]), self._unit_system),
                    "name": "Rain today",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-rainy",
                    "unit": sensor_unit.rain(self._unit_system),
                    },
                "rainrate": {
                    "value": self._rainrate,
                    "name": "Rain rate",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-pouring",
                    "unit": sensor_unit.rain(self._unit_system, True),
                    },
                "dewpoint": {
                    "value": cnv.temperature(float(values[9]), self._unit_system),
                    "name": "Dew point",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "windchill": {
                    "value": self._windchill,
                    "name": "Wind chill",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "windgust": {
                    "value": cnv.speed(float(values[11]), self._unit_system),
                    "name": "Wind gust",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_WIND,
                    "icon": "weather-windy",
                    "unit": sensor_unit.wind(self._unit_system),
                    },
                "in_temperature": {
                    "value": cnv.temperature(float(values[13]), self._unit_system),
                    "name": "Indoor temp",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "in_humidity": {
                    "value": values[14],
                    "name": "Indoor humidity",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_HUMIDITY,
                    "icon": "water-percent",
                    "unit": "%",
                    },
                "temphigh": {
                    "value": cnv.temperature(float(values[15]), self._unit_system),
                    "name": "Temp high today",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "templow": {
                    "value": cnv.temperature(float(values[16]), self._unit_system),
                    "name": "Temp low today",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "windspeed": {
                    "value": cnv.speed(float(values[17]), self._unit_system),
                    "name": "Wind speed",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_WIND,
                    "icon": "weather-windy",
                    "unit": sensor_unit.wind(self._unit_system),
                    },
                "heatindex": {
                    "value": self._heatindex,
                    "name": "Heat index",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "uvindex": {
                    "value": float(values[19]),
                    "name": "UV index",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "weather-sunny-alert",
                    "unit": "UV",
                    },
                "solarrad": {
                    "value": float(values[20]),
                    "name": "Solar radiation",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "weather-sunny",
                    "unit": "W/m2",
                    },
                "feels_like": {
                    "value": cnv.feels_like(self._outtemp, self._heatindex, self._windchill, self._unit_system),
                    "name": "Feels like",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "temp_month_min": {
                    "value": cnv.temperature(float(values[21]), self._unit_system),
                    "name": "Temp month min",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "temp_month_max": {
                    "value": cnv.temperature(float(values[22]), self._unit_system),
                    "name": "Temp month max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "temp_year_min": {
                    "value": cnv.temperature(float(values[23]), self._unit_system),
                    "name": "Temp year min",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "temp_year_max": {
                    "value": cnv.temperature(float(values[24]), self._unit_system),
                    "name": "Temp year max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": sensor_unit.temperature(self._unit_system),
                    },
                "wind_month_max": {
                    "value": cnv.speed(float(values[25]), self._unit_system),
                    "name": "Wind speed month max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_WIND,
                    "icon": "weather-windy",
                    "unit": sensor_unit.wind(self._unit_system),
                    },
                "wind_year_max": {
                    "value": cnv.speed(float(values[26]), self._unit_system),
                    "name": "Wind speed year max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_WIND,
                    "icon": "weather-windy",
                    "unit": sensor_unit.wind(self._unit_system),
                    },
                "rain_month_max": {
                    "value": cnv.volume(float(values[27]), self._unit_system),
                    "name": "Rain month total",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-rainy",
                    "unit": sensor_unit.rain(self._unit_system),
                    },
                "rain_year_max": {
                    "value": cnv.volume(float(values[28]), self._unit_system),
                    "name": "Rain year total",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-rainy",
                    "unit": sensor_unit.rain(self._unit_system),
                    },
                "rainrate_month_max": {
                    "value": cnv.volume(float(values[29]), self._unit_system),
                    "name": "Rain rate month max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-pouring",
                    "unit": sensor_unit.rain(self._unit_system, True),
                    },
                "rainrate_year_max": {
                    "value": cnv.volume(float(values[30]), self._unit_system),
                    "name": "Rain rate year max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-pouring",
                    "unit": sensor_unit.rain(self._unit_system, True),
                    },
                "lightning_count": {
                    "value": float(values[31]),
                    "name": "Lightning Count",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "weather-lightning",
                    "unit": None,
                    },
                "lightning_energy": {
                    "value": float(values[32]),
                    "name": "Lightning Energy",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "transmission-tower",
                    "unit": None,
                    },
                "lightning_distance": {
                    "value": cnv.distance(float(values[33]), self._unit_system),
                    "name": "Lightning Distance",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_DISTANCE,
                    "icon": "map-marker-circle",
                    "unit": sensor_unit.distance(self._unit_system),
                    },
                "air_pollution": {
                    "value": values[34],
                    "name": "Air pollution",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "air-filter",
                    "unit": "µg/m3",
                    },
                "forecast": {
                    "value": values[35],
                    "name": "Station forecast",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "text-short",
                    "unit": None,
                    },
                "is_freezing": {
                    "value": True if float(self._outtemp) < 0 else False,
                    "name": "Is freezing",
                    "type": DEVICE_TYPE_BINARY_SENSOR,
                    "device_class": DEVICE_CLASS_COLD,
                    "icon": "thermometer-minus,thermometer-plus",
                    "unit": None,
                    },
                "is_raining": {
                    "value": True if float(self._rainrate) > 0 else False,
                    "name": "Is raining",
                    "type": DEVICE_TYPE_BINARY_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "water,water-off",
                    "unit": None,
                    },
                "is_lowbat": {
                    "value": True if float(values[12]) > 0 else False,
                    "name": "Battery low",
                    "type": DEVICE_TYPE_BINARY_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "battery-10,battery",
                    "unit": None,
                    },
            }

        return sensor_item

    async def async_request(self, method: str, endpoint: str) -> dict:
        """Make a request against the SmartWeather API."""

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        try:
            async with session.request(
                method, endpoint
            ) as resp:
                resp.raise_for_status()
                data = await resp.read()
                decoded_content = data.decode("utf-8")
                return decoded_content
        except asyncio.TimeoutError:
            raise RequestError("Request to endpoint timed out: {endpoint}")
        except ClientError as err:
            if err.message == "Unauthorized":
                raise InvalidCredentials("Your Username/Password combination is not correct")
            elif err.message == "Not Found":
                raise ResultError("The Meteobridge cannot not be found on this IP Address")
            else:
                raise RequestError(
                    f"Error requesting data from {endpoint}: {err}"
                ) from None
        finally:
            if not use_running_session:
                await session.close()


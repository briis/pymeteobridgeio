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
    UNIT_TYPE_DIST_KM,
    UNIT_TYPE_PRESSURE_MB,
    UNIT_TYPE_RAIN_MM,
    UNIT_TYPE_TEMP_CELCIUS,
    UNIT_TYPE_WIND_MS,
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
        unit_temperature: str = UNIT_TYPE_TEMP_CELCIUS,
        unit_wind: str = UNIT_TYPE_WIND_MS,
        unit_rain: str = UNIT_TYPE_RAIN_MM,
        unit_pressure: str = UNIT_TYPE_PRESSURE_MB,
        unit_distance: str = UNIT_TYPE_DIST_KM,
        language: str = "en",
        extra_sensors: int = 0,
        session: Optional[ClientSession] = None,
    ):
        self._host = Host
        self._user = User
        self._pass = Pass
        self._unit_temperature = unit_temperature
        self._unit_wind = unit_wind
        self._unit_rain = unit_rain
        self._unit_pressure = unit_pressure
        self._unit_distance = unit_distance
        self._language = language
        self._extra_sensors = extra_sensors
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
                "platform_hw": await hw_name.platform(values[2]),
                "station_hw": values[3],
                "wlan_ip": values[4],
                "lan_ip": values[5],
                "ip_address": values[5] if values[4] == "None" else values[4],
            }
            return item

    async def _sensor_data(self) -> None:
        """Gets the sensor data from the Meteobridge Logger"""

        dataTemplate = "[DD]/[MM]/[YYYY];[hh]:[mm]:[ss];[th0temp-act:0];[thb0seapress-act:0];[th0hum-act:0];[wind0avgwind-act:0];[wind0dir-avg5.0:0];[rain0total-daysum:0];[rain0rate-act:0];[th0dew-act:0];[wind0chill-act:0];[wind0wind-max1:0];[th0lowbat-act.0:0];[thb0temp-act:0];[thb0hum-act.0:0];[th0temp-dmax:0];[th0temp-dmin:0];[wind0wind-act:0];[th0heatindex-act.1:0];[uv0index-act:0];[sol0rad-act:0];[th0temp-mmin.1:0];[th0temp-mmax.1:0];[th0temp-ymin.1:0];[th0temp-ymax.1:0];[wind0wind-mmax.1:0];[wind0wind-ymax.1:0];[rain0total-mmax.1:0];[rain0total-ymax.1:0];[rain0rate-mmax.1:0];[rain0rate-ymax.1:0];[lgt0total-act.0:0];[lgt0energy-act.0:0];[lgt0dist-act.0:0];[air0pm-act.0:0];[wind0wind-act=bft.0:0];[th1temp-act:0];[th1hum-act:0];[th1heatindex-act.1:0];[th2temp-act:0];[th2hum-act:0];[th2heatindex-act.1:0];[th0temp-delta10:0];[thb0seapress-delta10:0];[forecast-text:]"
        endpoint = f"http://{self._user}:{self._pass}@{self._host}/cgi-bin/template.cgi?template={dataTemplate}"

        data = await self.async_request("get", endpoint)
        cr = csv.reader(data.splitlines(), delimiter=";")
        rows = list(cr)
        cnv = Conversion()
        sensor_unit = Units()
        sensor_item = {}

        for values in rows:
            self._outtemp = await cnv.temperature(float(values[2]), self._unit_temperature)
            self._heatindex = await cnv.temperature(float(values[18]), self._unit_temperature)
            self._windchill = await cnv.temperature(float(values[10]), self._unit_temperature)
            self._rainrate = await cnv.rate(float(values[8]), self._unit_rain)
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
                    "unit": self._unit_temperature,
                    },
                "pressure": {
                    "value": await cnv.pressure(float(values[3]), self._unit_pressure),
                    "name": "Pressure",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_PRESSURE,
                    "icon": "gauge",
                    "unit": self._unit_pressure,
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
                    "value": await cnv.speed(float(values[5]), self._unit_wind),
                    "name": "Wind Speed Avg",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_WIND,
                    "icon": "weather-windy",
                    "unit": self._unit_wind,
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
                    "value": await cnv.wind_direction(float(values[6]), self._language),
                    "name": "Wind Direction",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "compass-outline",
                    "unit": None,
                    },
                "raintoday": {
                    "value": await cnv.volume(float(values[7]), self._unit_rain),
                    "name": "Rain today",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-rainy",
                    "unit": self._unit_rain,
                    },
                "rainrate": {
                    "value": self._rainrate,
                    "name": "Rain rate",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-pouring",
                    "unit": f"{self._unit_rain}/h",
                    },
                "dewpoint": {
                    "value": await cnv.temperature(float(values[9]), self._unit_temperature),
                    "name": "Dew point",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
                    },
                "windchill": {
                    "value": self._windchill,
                    "name": "Wind chill",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
                    },
                "windgust": {
                    "value": await cnv.speed(float(values[11]), self._unit_wind),
                    "name": "Wind gust",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_WIND,
                    "icon": "weather-windy",
                    "unit": self._unit_wind,
                    },
                "in_temperature": {
                    "value": await cnv.temperature(float(values[13]), self._unit_temperature),
                    "name": "Indoor temp",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
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
                    "value": await cnv.temperature(float(values[15]), self._unit_temperature),
                    "name": "Temp high today",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
                    },
                "templow": {
                    "value": await cnv.temperature(float(values[16]), self._unit_temperature),
                    "name": "Temp low today",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
                    },
                "windspeed": {
                    "value": await cnv.speed(float(values[17]), self._unit_wind),
                    "name": "Wind speed",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_WIND,
                    "icon": "weather-windy",
                    "unit": self._unit_wind,
                    },
                "heatindex": {
                    "value": self._heatindex,
                    "name": "Heat index",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
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
                    "value": await cnv.feels_like(self._outtemp, self._heatindex, self._windchill, self._unit_temperature),
                    "name": "Feels like",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
                    },
                "temp_month_min": {
                    "value": await cnv.temperature(float(values[21]), self._unit_temperature),
                    "name": "Temp month min",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
                    },
                "temp_month_max": {
                    "value": await cnv.temperature(float(values[22]), self._unit_temperature),
                    "name": "Temp month max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
                    },
                "temp_year_min": {
                    "value": await cnv.temperature(float(values[23]), self._unit_temperature),
                    "name": "Temp year min",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
                    },
                "temp_year_max": {
                    "value": await cnv.temperature(float(values[24]), self._unit_temperature),
                    "name": "Temp year max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_TEMPERATURE,
                    "icon": "thermometer",
                    "unit": self._unit_temperature,
                    },
                "wind_month_max": {
                    "value": await cnv.speed(float(values[25]), self._unit_wind),
                    "name": "Wind speed month max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_WIND,
                    "icon": "weather-windy",
                    "unit": self._unit_wind,
                    },
                "wind_year_max": {
                    "value": await cnv.speed(float(values[26]), self._unit_wind),
                    "name": "Wind speed year max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_WIND,
                    "icon": "weather-windy",
                    "unit": self._unit_wind,
                    },
                "rain_month_max": {
                    "value": await cnv.volume(float(values[27]), self._unit_rain),
                    "name": "Rain month total",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-rainy",
                    "unit": self._unit_rain,
                    },
                "rain_year_max": {
                    "value": await cnv.volume(float(values[28]), self._unit_rain),
                    "name": "Rain year total",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-rainy",
                    "unit": self._unit_rain,
                    },
                "rainrate_month_max": {
                    "value": await cnv.volume(float(values[29]), self._unit_rain),
                    "name": "Rain rate month max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-pouring",
                    "unit": f"{self._unit_rain}/h",
                    },
                "rainrate_year_max": {
                    "value": await cnv.volume(float(values[30]), self._unit_rain),
                    "name": "Rain rate year max",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_RAIN,
                    "icon": "weather-pouring",
                    "unit": f"{self._unit_rain}/h",
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
                    "value": await cnv.distance(float(values[33]), self._unit_distance),
                    "name": "Lightning Distance",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_DISTANCE,
                    "icon": "map-marker-circle",
                    "unit": self._unit_distance,
                    },
                "air_pollution": {
                    "value": values[34],
                    "name": "Air pollution",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "air-filter",
                    "unit": "µg/m3",
                    },
                "bft_value": {
                    "value": values[35],
                    "name": "Beaufort Value",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "weather-tornado",
                    "unit": "BFT",
                    },
                "bft_text": {
                    "value": await cnv.beaufort_text(values[35], self._language),
                    "name": "Beaufort Text",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "weather-tornado",
                    "unit": None,
                    },
                "trend_temperature": {
                    "value": await cnv.trend_text(values[42],self._language),
                    "name": "Temperature Trend",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "trending-up",
                    "unit": None,
                    },
                "trend_pressure": {
                    "value": await cnv.trend_text(values[43],self._language),
                    "name": "Pressure Trend",
                    "type": DEVICE_TYPE_SENSOR,
                    "device_class": DEVICE_CLASS_NONE,
                    "icon": "trending-down",
                    "unit": None,
                    },
                "forecast": {
                    "value": values[44],
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

            # Check if there are Extra Sensors defined in the station
            if self._extra_sensors > 0:
                sensor_item.update(
                    {
                        "temperature_2": {
                            "value": await cnv.temperature(float(values[36]), self._unit_temperature),
                            "name": "Temperature 2",
                            "type": DEVICE_TYPE_SENSOR,
                            "device_class": DEVICE_CLASS_TEMPERATURE,
                            "icon": "thermometer",
                            "unit": self._unit_temperature,
                            },
                        "humidity_2": {
                            "value": values[37],
                            "name": "Humidity 2",
                            "type": DEVICE_TYPE_SENSOR,
                            "device_class": DEVICE_CLASS_HUMIDITY,
                            "icon": "water-percent",
                            "unit": "%",
                            },
                        "heatindex_2": {
                            "value": await cnv.temperature(float(values[38]), self._unit_temperature),
                            "name": "Heat index 2",
                            "type": DEVICE_TYPE_SENSOR,
                            "device_class": DEVICE_CLASS_TEMPERATURE,
                            "icon": "thermometer",
                            "unit": self._unit_temperature,
                            },
                    }
                )
            if self._extra_sensors > 1:
                sensor_item.update(
                    {
                        "temperature_3": {
                            "value": await cnv.temperature(float(values[39]), self._unit_temperature),
                            "name": "Temperature 3",
                            "type": DEVICE_TYPE_SENSOR,
                            "device_class": DEVICE_CLASS_TEMPERATURE,
                            "icon": "thermometer",
                            "unit": self._unit_temperature,
                            },
                        "humidity_3": {
                            "value": values[40],
                            "name": "Humidity 3",
                            "type": DEVICE_TYPE_SENSOR,
                            "device_class": DEVICE_CLASS_HUMIDITY,
                            "icon": "water-percent",
                            "unit": "%",
                            },
                        "heatindex_3": {
                            "value": await cnv.temperature(float(values[41]), self._unit_temperature),
                            "name": "Heat index 3",
                            "type": DEVICE_TYPE_SENSOR,
                            "device_class": DEVICE_CLASS_TEMPERATURE,
                            "icon": "thermometer",
                            "unit": self._unit_temperature,
                            },
                    }
                )



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
            if "Cannot connect" in str(err):
                raise ResultError(f"Meteobridge cannot be contacted on the IP Address: {self._host}")
            elif "Authorization Required" in str(err):
                raise InvalidCredentials("The supplied Username and Password are wrong")
            else:
                raise RequestError(f"Error occured {err}")
        finally:
            if not use_running_session:
                await session.close()


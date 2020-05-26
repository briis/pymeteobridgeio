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
    UNIT_SYSTEM_METRIC,
    UNIT_SYSTEM_IMPERIAL,
)
from pymeteobridgeio.errors import (
    InvalidCredentials,
    RequestError,
    ResultError,
)
from pymeteobridgeio.functions import Conversion

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
        data_template = "[mbsystem-mac:None];[mbsystem-swversion:0.0]-[mbsystem-buildnum:0];[mbsystem-platform:None];[mbsystem-station:None]"
        endpoint = f"http://{self._user}:{self._pass}@{self._host}/cgi-bin/template.cgi?template={data_template}"
        data = await self.async_request("get", endpoint)
        cr = csv.reader(data.splitlines(), delimiter=";")
        rows = list(cr)

        for values in rows:
            item = {
                "mac_address": values[0],
                "swversion": values[1],
                "platform_hw": values[2],
                "station_hw": values[3],
            }
        return item

    async def _sensor_data(self) -> None:
        """Gets the sensor data from the Meteobridge Logger"""

        dataTemplate = "[DD]/[MM]/[YYYY];[hh]:[mm]:[ss];[th0temp-act:0];[thb0seapress-act:0];[th0hum-act:0];[wind0avgwind-act:0];[wind0dir-avg5.0:0];[rain0total-daysum:0];[rain0rate-act:0];[th0dew-act:0];[wind0chill-act:0];[wind0wind-max1:0];[th0lowbat-act.0:0];[thb0temp-act:0];[thb0hum-act.0:0];[th0temp-dmax:0];[th0temp-dmin:0];[wind0wind-act:0];[th0heatindex-act.1:0];[uv0index-act:0];[sol0rad-act:0];[th0temp-mmin.1:0];[th0temp-mmax.1:0];[th0temp-ymin.1:0];[th0temp-ymax.1:0];[wind0wind-mmax.1:0];[wind0wind-ymax.1:0];[rain0total-mmax.1:0];[rain0total-ymax.1:0];[rain0rate-mmax.1:0];[rain0rate-ymax.1:0];[forecast-text:]"
        endpoint = f"http://{self._user}:{self._pass}@{self._host}/cgi-bin/template.cgi?template={dataTemplate}"

        data = await self.async_request("get", endpoint)
        cr = csv.reader(data.splitlines(), delimiter=";")
        rows = list(cr)
        cnv = Conversion()

        for values in rows:
            self._outtemp = cnv.temperature(float(values[2]), self._unit_system)
            self._heatindex = cnv.temperature(float(values[18]), self._unit_system)
            self._windchill = cnv.temperature(float(values[10]), self._unit_system)
            self._rainrate = cnv.rate(float(values[8]), self._unit_system)
            sensor_item = {
                "timestamp": datetime.strptime(f"{values[0]} {values[1]}", "%d/%m/%Y %H:%M:%S"),
                "temperature": self._outtemp,
                "pressure": cnv.pressure(float(values[3]), self._unit_system),
                "humidity": values[4],
                "windspeedavg": cnv.speed(float(values[5]), self._unit_system),
                "windbearing": int(float(values[6])),
                "winddirection": cnv.wind_direction(float(values[6])),
                "raintoday": cnv.volume(float(values[7]), self._unit_system),
                "rainrate": self._rainrate,
                "dewpoint": cnv.temperature(float(values[9]), self._unit_system),
                "windchill": self._windchill,
                "windgust": cnv.speed(float(values[11]), self._unit_system),
                "lowbattery": values[12],
                "in_temperature": cnv.temperature(float(values[13]), self._unit_system),
                "in_humidity": values[14],
                "temphigh": cnv.temperature(float(values[15]), self._unit_system),
                "templow": cnv.temperature(float(values[16]), self._unit_system),
                "windspeed": cnv.speed(float(values[17]), self._unit_system),
                "heatindex": self._heatindex,
                "uvindex": float(values[19]),
                "solarrad": float(values[20]),
                "feels_like": cnv.feels_like(self._outtemp, self._heatindex, self._windchill, self._unit_system),
                "tempmmin": cnv.temperature(float(values[21]), self._unit_system),
                "tempmmax": cnv.temperature(float(values[22]), self._unit_system),
                "tempymin": cnv.temperature(float(values[23]), self._unit_system),
                "tempymax": cnv.temperature(float(values[24]), self._unit_system),
                "windmmax": cnv.speed(float(values[25]), self._unit_system),
                "windymax": cnv.speed(float(values[26]), self._unit_system),
                "rainmmax": cnv.volume(float(values[27]), self._unit_system),
                "rainymax": cnv.volume(float(values[28]), self._unit_system),
                "rainratemmax": cnv.volume(float(values[29]), self._unit_system),
                "rainrateymax": cnv.volume(float(values[30]), self._unit_system),
                "forecast": values[31],
                "isfreezing": True if float(self._outtemp) < 0 else False,
                "israining": True if float(self._rainrate) > 0 else False,
                "islowbat": True if float(values[12]) > 0 else False
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


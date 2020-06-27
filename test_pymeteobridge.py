""" The test for the API """
"""Run an example script to quickly test."""
import asyncio
from aiohttp import ClientSession
import time
import json
import logging

from pymeteobridgeio import (
    Meteobridge,
    RequestError,
    DEVICE_TYPE_BINARY_SENSOR,
    DEVICE_TYPE_SENSOR,
    UNIT_SYSTEM_IMPERIAL,
    UNIT_SYSTEM_METRIC
)

_LOGGER = logging.getLogger(__name__)

USERNAME = "meteobridge"
UNIT_SYSTEM = UNIT_SYSTEM_METRIC
LANGUAGE = "da"
ADDITONAL_SENSORS = 0

async def realtime_data():
    """Return the raw data from a Meteobridge Station."""

    start = time.time()

    logging.basicConfig(level=logging.DEBUG)

    path_index = __file__.rfind("/")
    top_path = __file__[0:path_index]
    filepath = f"{top_path}/settings.json"
    with open(filepath) as json_file:
        data = json.load(json_file)
        host = data["connection"]["host"]
        password = data["connection"]["password"]

    session = ClientSession()

    # Connect to Meteobridge
    mb = Meteobridge(host, USERNAME, password, UNIT_SYSTEM, LANGUAGE, session)
    
    try:
        _LOGGER.info("GETTING SERVER DATA:")
        data = await mb.get_server_data()
        _LOGGER.info(f"mac_address: {data['mac_address']} swversion: {data['swversion']} platform_hw: {data['platform_hw']} station_hw: {data['station_hw']} wlan_ip: {data['wlan_ip']} lan_ip: {data['lan_ip']} ip_address: {data['ip_address']}")

        _LOGGER.info("GETTING SENSOR DATA:")
        data = await mb.get_sensor_data()
        for sensor in data:
            if data[sensor]["type"] == DEVICE_TYPE_SENSOR or data[sensor]["type"] == DEVICE_TYPE_BINARY_SENSOR:
                _LOGGER.info(f"SENSOR: {sensor} VALUE: {data[sensor]['value']} UNIT: {data[sensor]['unit']} ")

    except RequestError as err:
        _LOGGER.info(err)

    end = time.time()

    _LOGGER.info("Execution time: %s seconds", end - start)

    # Close the Session
    await session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(realtime_data())
loop.close()
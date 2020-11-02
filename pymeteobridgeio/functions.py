"""Helper Functions for Meteobridge."""
import json
import asyncio

from pymeteobridgeio.const import (
    UNIT_SYSTEM_IMPERIAL,
    UNIT_TYPE_DIST_KM,
    UNIT_TYPE_DIST_MI,
    UNIT_TYPE_PRESSURE_HPA,
    UNIT_TYPE_PRESSURE_INHG,
    UNIT_TYPE_RAIN_MM,
    UNIT_TYPE_RAIN_IN,
    UNIT_TYPE_TEMP_CELCIUS,
    UNIT_TYPE_TEMP_FAHRENHEIT,
    UNIT_TYPE_WIND_KMH,
    UNIT_TYPE_WIND_MS,
    UNIT_TYPE_WIND_MPH,
    SUPPORTED_LANGUAGES,
)

class Conversion:

    """
    Conversion Class to convert between different units.
    Meteobridge always delivers values in the following formats:
    Temperature: C
    Wind Speed: m/s
    Wind Direction: Degrees
    Pressure: mb
    Distance: km
    """

    async def temperature(self, value, unit):
        if unit == UNIT_TYPE_TEMP_FAHRENHEIT:
            # Return value F
            return round((value * 9 / 5) + 32, 1)
        else:
            # Return value C
            return round(value, 1)

    async def volume(self, value, unit):
        if unit != UNIT_TYPE_RAIN_MM:
            # Return value in
            return round(value * 0.0393700787, 2)
        else:
            # Return value mm
            return round(value, 1)

    async def rate(self, value, unit):
        if unit != UNIT_TYPE_RAIN_MM:
            # Return value in
            return round(value * 0.0393700787, 2)
        else:
            # Return value mm
            return round(value, 2)

    async def pressure(self, value, unit):
        if unit == UNIT_TYPE_PRESSURE_INHG:
            # Return value inHg
            return round(value * 0.0295299801647, 3)
        else:
            # Return value mb
            return round(value, 1)

    async def speed(self, value, unit):
        if unit == UNIT_TYPE_WIND_MPH:
            # Return value in mi/h
            return round(value * 2.2369362921, 1)
        elif unit == UNIT_TYPE_WIND_KMH:
            # Return value in km/h
            return round(value * 3.6, 1)
        else:
            # Return value in m/s
            return round(value, 1)

    async def distance(self, value, unit):
        if unit == UNIT_TYPE_DIST_MI:
            # Return value in mi
            return round(value * 0.621371192, 1)
        else:
            # Return value in km
            return round(value, 0)

    async def feels_like(self, temp, heatindex, windchill, unit):
        """ Return Feels Like Temp."""
        if unit == UNIT_TYPE_TEMP_FAHRENHEIT:
            high_temp = 80
            low_temp = 50
        else:
            high_temp = 26.666666667
            low_temp = 10

        if float(temp) > high_temp:
            return float(heatindex)
        elif float(temp) < low_temp:
            return float(windchill)
        else:
            return temp

    async def wind_direction(self, bearing, language):
        direction_array = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW","N"]
        direction = direction_array[int((bearing + 11.25) / 22.5)]
        return await get_localized_text(language, direction, "wind_dir")

    async def beaufort_text(self, bft_value, language):
        """Return a localized Beaufort description."""
        return await get_localized_text(language, str(bft_value), "beaufort")

    async def trend_text(self, value, language):
        """Returns a localized Trend String."""
        try:
            value = float(value)
            if value > 0:
                text = "rising"
            elif value < 0:
                text = "falling"
            else:
                text = "steady"
            return await get_localized_text(language, text, "trend")
        except:
            return "error"
            
class Units:
    """Returns the correct Display Unit for the current 
       Unit System and type of Sensor."""

    async def temperature(self, unit_system):
        """Return units for Temperature sensor."""
        if unit_system == UNIT_SYSTEM_IMPERIAL:
            return UNIT_TYPE_TEMP_FAHRENHEIT
        else:
            return UNIT_TYPE_TEMP_CELCIUS

    async def rain(self, unit_system, rainrate = False):
        """Return units for Rain sensor."""
        if unit_system == UNIT_SYSTEM_IMPERIAL:
            return UNIT_TYPE_RAIN_IN if not rainrate else f"{UNIT_TYPE_RAIN_IN}/h"
        else:
            return UNIT_TYPE_RAIN_MM if not rainrate else f"{UNIT_TYPE_RAIN_MM}/h"

    async def wind(self, unit_system):
        """Return units for Wind sensor."""
        if unit_system == UNIT_SYSTEM_IMPERIAL:
            return UNIT_TYPE_WIND_MPH
        else:
            return UNIT_TYPE_WIND_MS

    async def pressure(self, unit_system):
        """Return units for Wind sensor."""
        if unit_system == UNIT_SYSTEM_IMPERIAL:
            return UNIT_TYPE_PRESSURE_INHG
        else:
            return UNIT_TYPE_PRESSURE_HPA

    async def distance(self, unit_system):
        """Return units for Distance sensor."""
        if unit_system == UNIT_SYSTEM_IMPERIAL:
            return UNIT_TYPE_DIST_MI
        else:
            return UNIT_TYPE_DIST_KM

class HardwareTypes:
    """Converts HW Names to readable names."""

    async def platform(self, value):
        """Converts the Platform Naming."""
        if value == "CARAMBOLA2":
            return "Meteobridge Pro"
        elif value == "VOCORE2":
            return "Meteobridge Nano"
        else:
            return value

async def get_localized_text(language, value, index):
    """Read the localized string from the Language file."""
    if language not in SUPPORTED_LANGUAGES:
        filename = f"/translations/en.json"
    else:
        filename = f"/translations/{language}.json"

    # Build filepath
    cwd = __file__
    path_index = cwd.rfind("/")
    top_path = cwd[0:path_index]
    filepath = f"{top_path}{filename}"

    # Return Value from language string
    with open(filepath) as json_file:
        data = json.load(json_file)
        return data[index][str(value)]

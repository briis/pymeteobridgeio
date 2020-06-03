"""Helper Functions for Meteobridge."""

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
)

class Conversion:

    """
    Conversion Class to convert between different units.
    WeatherFlow always delivers values in the following formats:
    Temperature: C
    Wind Speed: m/s
    Wind Direction: Degrees
    Pressure: mb
    Distance: km
    """

    def temperature(self, value, unit):
        if unit == UNIT_SYSTEM_IMPERIAL:
            # Return value F
            return round((value * 9 / 5) + 32, 1)
        else:
            # Return value C
            return round(value, 1)

    def volume(self, value, unit):
        if unit == UNIT_SYSTEM_IMPERIAL:
            # Return value in
            return round(value * 0.0393700787, 2)
        else:
            # Return value mm
            return round(value, 1)

    def rate(self, value, unit):
        if unit == UNIT_SYSTEM_IMPERIAL:
            # Return value in
            return round(value * 0.0393700787, 2)
        else:
            # Return value mm
            return round(value, 2)

    def pressure(self, value, unit):
        if unit == UNIT_SYSTEM_IMPERIAL:
            # Return value inHg
            return round(value * 0.0295299801647, 3)
        else:
            # Return value mb
            return round(value, 1)

    def speed(self, value, unit):
        if unit == UNIT_SYSTEM_IMPERIAL:
            # Return value in mi/h
            return round(value * 2.2369362921, 1)
        elif unit == "uk":
            # Return value in km/h
            return round(value * 3.6, 1)
        else:
            # Return value in m/s
            return round(value, 1)

    def distance(self, value, unit):
        if unit == UNIT_SYSTEM_IMPERIAL:
            # Return value in mi
            return round(value * 0.621371192, 1)
        else:
            # Return value in km
            return round(value, 0)

    def feels_like(self, temp, heatindex, windchill, unit):
        """ Return Feels Like Temp."""
        if unit == UNIT_SYSTEM_IMPERIAL:
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

    def wind_direction(self, bearing):
        direction_array = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
            "N",
        ]
        direction = direction_array[int((bearing + 11.25) / 22.5)]
        return direction

class Units:
    """Returns the correct Display Unit for the current 
       Unit System and type of Sensor."""

    def temperature(self, unit_system):
        """Return units for Temperature sensor."""
        if unit_system == UNIT_SYSTEM_IMPERIAL:
            return UNIT_TYPE_TEMP_FAHRENHEIT
        else:
            return UNIT_TYPE_TEMP_CELCIUS

    def rain(self, unit_system, rainrate = False):
        """Return units for Rain sensor."""
        if unit_system == UNIT_SYSTEM_IMPERIAL:
            return UNIT_TYPE_RAIN_IN if not rainrate else f"{UNIT_TYPE_RAIN_IN}/h"
        else:
            return UNIT_TYPE_RAIN_MM if not rainrate else f"{UNIT_TYPE_RAIN_MM}/h"

    def wind(self, unit_system):
        """Return units for Wind sensor."""
        if unit_system == UNIT_SYSTEM_IMPERIAL:
            return UNIT_TYPE_WIND_MPH
        else:
            return UNIT_TYPE_WIND_MS

    def pressure(self, unit_system):
        """Return units for Wind sensor."""
        if unit_system == UNIT_SYSTEM_IMPERIAL:
            return UNIT_TYPE_PRESSURE_INHG
        else:
            return UNIT_TYPE_PRESSURE_HPA

    def distance(self, unit_system):
        """Return units for Distance sensor."""
        if unit_system == UNIT_SYSTEM_IMPERIAL:
            return UNIT_TYPE_DIST_MI
        else:
            return UNIT_TYPE_DIST_KM

class HardwareTypes:
    """Converts HW Names to readable names."""

    def platform(self, value):
        """Converts the Platform Naming."""
        if value == "CARAMBOLA2":
            return "Meteobridge Pro"
        elif value == "VOCORE2":
            return "Meteobridge Nano"
        else:
            return value

"""Helper Functions for Meteobridge."""

from pymeteobridgeio.const import (
    UNIT_SYSTEM_IMPERIAL,
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

""" A Python Wrapper to communicate with a Meteobridge Data Logger."""
from pymeteobridgeio.client import Meteobridge
from pymeteobridgeio.errors import (
    InvalidCredentials,
    RequestError,
    ResultError,
)
from pymeteobridgeio.const import (
    DEVICE_CLASS_NONE,
    DEVICE_CLASS_DISTANCE,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_RAIN,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_WIND,
    DEVICE_TYPE_BINARY_SENSOR,
    DEVICE_TYPE_SENSOR,
    DEVICE_TYPE_NONE,
    UNIT_SYSTEM_IMPERIAL,
    UNIT_SYSTEM_METRIC,
)
"""Constants for the iNELS integration."""

import logging

DOMAIN = "inels"

BROKER_CONFIG = "inels_mqtt_broker_config"
BROKER = "inels_mqtt_broker"
DEVICES = "devices"
OLD_ENTITIES = "old_entities"

CONF_DISCOVERY_PREFIX = "discovery_prefix"

TITLE = "iNELS"
DESCRIPTION = ""
INELS_VERSION = 1
LOGGER = logging.getLogger(__package__)

DEFAULT_MIN_TEMP = 10.0  # °C
DEFAULT_MAX_TEMP = 50.0  # °C

ICON_TEMPERATURE = "mdi:thermometer"
ICON_BATTERY = "mdi:battery"
ICON_NUMBER = "mdi:ray-vertex"
ICON_SWITCH = "mdi:power-socket-eu"
ICON_LIGHT = "mdi:lightbulb"
ICON_SHUTTER_CLOSED = "mdi:window-shutter"
ICON_SHUTTER_OPEN = "mdi:window-shutter-open"
ICON_BUTTON = "mdi:button-pointer"
ICON_LIGHT_IN = "mdi:brightness-4"
ICON_HUMIDITY = "mdi:water-percent"
ICON_DEW_POINT = "mdi:tailwind"
ICON_PLUS = "mdi:plus"
ICON_MINUS = "mdi:minus"
ICON_ALERT = "mdi:alert"
ICON_PROXIMITY = "mdi:contactless-payment"
ICON_BINARY_INPUT = "mdi:ab-testing"
ICON_FLASH = "mdi:flash"
ICON_FAN = "mdi:fan"
ICON_HEAT_WAVE = "mdi:heat-wave"
ICON_VALVE = "mdi:valve"
ICON_EYE = "mdi:eye"
ICON_MOTION = "mdi:motion-sensor"
ICON_HOME_FLOOD = "mdi:home-flood"
ICON_CARD_PRESENT = "mdi:smart-card-reader-outline"
ICON_CARD_ID = "mdi:smart-card-outline"
ICON_SNOWFLAKE = "mdi:snowflake"
ICON_CYCLE = "mdi:sync"
ICON_FAN_1 = "mdi:fan-speed-1"
ICON_FAN_2 = "mdi:fan-speed-2"
ICON_FAN_3 = "mdi:fan-speed-3"
ICON_ECO = "mdi:leaf"
ICON_UP = "mdi:chevron-up"
ICON_DOWN = "mdi:chevron-down"

ICON_WATER_HEATER_DICT = {
    "on": "mdi:valve-open",
    "off": "mdi:valve-closed",
}

ICON_RELAY_DICT = {
    "on": "mdi:flash",
    "off": "mdi:flash-outline",
}

ICON_THERMOSTAT = "mdi:home-thermometer-outline"

MANUAL_SETUP = "manual"

BUTTON_PRESS_STATE = "press"
BUTTON_NO_ACTION_STATE = "no_action"

FAN_SPEED_OPTIONS: "list[str]" = ["Off", "Speed 1", "Speed 2", "Speed 3"]
FAN_SPEED_DICT = {"Off": 0, "Speed 1": 1, "Speed 2": 2, "Speed 3": 3}

SELECT_OPTIONS_DICT = {
    "fan_speed": FAN_SPEED_OPTIONS,
}

SELECT_OPTIONS_ICON = {"fan_speed": ICON_FAN}

SELECT_DICT = {"fan_speed": FAN_SPEED_DICT}

# DESCRIPTION KEYWORDS
BINARY_INPUT = "binary_input"
INDEXED = "indexed"
NAME = "name"
ICON = "icon"
DEVICE_CLASS = "device_class"
ENTITY_CATEGORY = "entity_category"
OPTIONS = "options"
OPTIONS_DICT = "options_dict"
UNIT = "unit"
OVERFLOW = "overflow"
RAW_SENSOR_VALUE = "raw_sensor_value"
SUPPORTED_COLOR_MODES = "supported_color_modes"
SUPPORTED_FEATURES = "supported_features"

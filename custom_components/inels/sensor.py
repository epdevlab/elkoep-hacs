"""iNELS sensor entity."""

from __future__ import annotations

from dataclasses import dataclass

from inelsmqtt.const import BUS_SENSOR_ERRORS, TEMP_IN, TEMP_OUT  # Data types
from inelsmqtt.devices import Device

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    LIGHT_LUX,
    PERCENTAGE,
    Platform,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import (
    DEVICES,
    DOMAIN,
    ICON_CARD_ID,
    ICON_DEW_POINT,
    ICON_FLASH,
    ICON_HUMIDITY,
    ICON_LIGHT_IN,
    ICON_TEMPERATURE,
    LOGGER,
    OLD_ENTITIES,
)
from .entity import InelsBaseEntity


# SENSOR PLATFORM
@dataclass
class InelsSensorType:
    """Select type property description."""

    name: str
    icon: str
    unit: str
    indexed: bool = False
    raw_sensor_value: bool = False
    device_class: SensorDeviceClass | None = None


INELS_SENSOR_TYPES: dict[str, InelsSensorType] = {
    "temp": InelsSensorType(
        name="Temperature sensor",
        icon=ICON_TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    TEMP_IN: InelsSensorType(
        name="Internal temperature sensor",
        icon=ICON_TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    TEMP_OUT: InelsSensorType(
        name="External temperature sensor",
        icon=ICON_TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "light_in": InelsSensorType(
        name="Light intensity",
        icon=ICON_LIGHT_IN,
        unit=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
    ),
    "ain": InelsSensorType(
        name="Analog temperature sensor",
        icon=ICON_TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "humidity": InelsSensorType(
        name="Humidity",
        icon=ICON_HUMIDITY,
        unit=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    "dewpoint": InelsSensorType(
        name="Dew point",
        icon=ICON_DEW_POINT,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "temps": InelsSensorType(
        name="Temperature sensor",
        icon=ICON_TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
        indexed=True,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    "ains": InelsSensorType(
        name="Analog input",
        icon=ICON_FLASH,
        unit=UnitOfElectricPotential.VOLT,
        indexed=True,
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    "card_id": InelsSensorType(
        name="Last card ID",
        icon=ICON_CARD_ID,
        unit=None,
        raw_sensor_value=False,
    ),
}


def _process_value(val: str) -> tuple[str, bool]:
    middle_fs = True
    for k in val[1:-1]:
        if k.capitalize() != "F":
            middle_fs = False

    if (
        middle_fs
        and val[0] == "7"
        and ((val[-1] <= "F" and val[-1] >= "A") or val[-1] == "9")
    ):
        last = val[-1]
        last = int(last, 16)
        error = BUS_SENSOR_ERRORS.get(last)
        if error is not None:
            LOGGER.warning(error)
            return (float(int(val, 16)) / 100, True)

    return (float(int(val, 16)) / 100, False)


@dataclass
class InelsSensorDescriptionMixin:
    """Mixin keys."""


@dataclass
class InelsSensorDescription(SensorEntityDescription, InelsSensorDescriptionMixin):
    """Class for describing iNELS entities."""

    raw_sensor_value: bool = False


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Load iNELS switch.."""
    device_list: list[Device] = hass.data[DOMAIN][config_entry.entry_id][DEVICES]
    old_entities: list[str] = hass.data[DOMAIN][config_entry.entry_id][
        OLD_ENTITIES
    ].get(Platform.SENSOR)

    items = INELS_SENSOR_TYPES.items()
    entities: list[InelsBaseEntity] = []
    for device in device_list:
        for key, type_dict in items:
            if hasattr(device.state, key):
                if type_dict.indexed:
                    entities.extend(
                        [
                            InelsSensor(
                                device=device,
                                key=key,
                                index=k,
                                description=InelsSensorDescription(
                                    key=f"{key}{k}",
                                    name=f"{type_dict.name} {k+1}",
                                    icon=type_dict.icon,
                                    native_unit_of_measurement=type_dict.unit,
                                    raw_sensor_value=type_dict.raw_sensor_value,
                                ),
                            )
                            for k in range(len(device.state.__dict__[key]))
                        ]
                    )
                else:
                    entities.append(
                        InelsSensor(
                            device=device,
                            key=key,
                            index=-1,
                            description=InelsSensorDescription(
                                key=key,
                                name=type_dict.name,
                                icon=type_dict.icon,
                                native_unit_of_measurement=type_dict.unit,
                                raw_sensor_value=type_dict.raw_sensor_value,
                            ),
                        )
                    )
    async_add_entities(entities, True)

    if old_entities:
        for entity in entities:
            if entity.entity_id in old_entities:
                old_entities.pop(old_entities.index(entity.entity_id))

    hass.data[DOMAIN][config_entry.entry_id][Platform.SENSOR] = old_entities


class InelsSensor(InelsBaseEntity, SensorEntity):
    """Platform class for Home assistant, bus version."""

    entity_description: InelsSensorDescription
    sensor_error: bool = False

    def __init__(
        self,
        device: Device,
        key: str,
        index: int,
        description: InelsSensorDescription,
    ) -> None:
        """Initialize bus sensor."""
        super().__init__(device=device, key=key, index=index)

        self.entity_description = description

        self._attr_unique_id = slugify(f"{self._attr_unique_id}_{description.key}")
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_name = f"{self._attr_name} {description.name}"

        if self.index != -1:  # with index
            val = self._device.state.__dict__[self.key][self.index]
        else:
            val = self._device.state.__dict__[self.key]

        if not self.entity_description.raw_sensor_value and isinstance(val, str):
            val, self.sensor_error = _process_value(val)

        self._attr_device_class = self.entity_description.device_class
        self._attr_icon = self.entity_description.icon
        self._attr_native_value = val

    def _callback(self) -> None:
        """Refresh data."""
        super()._callback()

        if self.index != -1:  # with index
            val = self._device.state.__dict__[self.key][self.index]
        else:
            val = self._device.state.__dict__[self.key]

        if (not self.entity_description.raw_sensor_value) and isinstance(val, str):
            val, self.sensor_error = _process_value(val)

        self._attr_native_value = val

    @property
    def available(self) -> bool:
        """Return True if entity is available and sensor has no error."""
        return (not self.sensor_error) and super().available

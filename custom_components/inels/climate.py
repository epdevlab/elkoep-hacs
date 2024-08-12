"""iNELS climate entity."""

from __future__ import annotations

from dataclasses import dataclass

from inelsmqtt.const import Climate_action, Climate_modes
from inelsmqtt.devices import Device

from homeassistant.components.climate import (
    STATE_OFF,
    STATE_ON,
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import DEFAULT_MAX_TEMP, DEFAULT_MIN_TEMP, DEVICES, DOMAIN, OLD_ENTITIES
from .entity import InelsBaseEntity

OPERATION_LIST = [
    STATE_OFF,
    STATE_ON,
]

CLIMATE_MODE_TO_HVAC_MODE = {
    Climate_modes.Off: HVACMode.OFF,
    Climate_modes.Heat: HVACMode.HEAT,
    Climate_modes.Cool: HVACMode.COOL,
    Climate_modes.Heat_cool: HVACMode.HEAT_COOL,
    Climate_modes.Auto: HVACMode.AUTO,
}

HVAC_MODE_TO_CLIMATE_MODE = {
    HVACMode.OFF: Climate_modes.Off,
    HVACMode.HEAT: Climate_modes.Heat,
    HVACMode.COOL: Climate_modes.Cool,
    HVACMode.HEAT_COOL: Climate_modes.Heat_cool,
    HVACMode.AUTO: Climate_modes.Auto,
}

CLIMATE_ACTION_TO_HVAC_ACTION = {
    Climate_action.Off: HVACAction.OFF,
    Climate_action.Idle: HVACAction.IDLE,
    Climate_action.Heating: HVACAction.HEATING,
    Climate_action.Cooling: HVACAction.COOLING,
}


# CLIMATE PLATFORM
@dataclass
class InelsClimateType:
    """Climate type property description."""

    name: str
    features: list[ClimateEntityFeature]
    hvac_modes: list[HVACMode]
    presets: list[str] | None = None


INELS_CLIMATE_TYPES: dict[str, InelsClimateType] = {
    "thermovalve": InelsClimateType(
        name="Thermovalve",
        features=[ClimateEntityFeature.TARGET_TEMPERATURE],
        hvac_modes=[HVACMode.OFF, HVACMode.HEAT],
    ),
    "climate_controller": InelsClimateType(
        name="Virtual Thermostat",
        features=[
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE,
            ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
            ClimateEntityFeature.TARGET_TEMPERATURE,
        ],
        hvac_modes=[
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
        ],
        presets=[
            "Schedule",
            "Preset 1",
            "Preset 2",
            "Preset 3",
            "Preset 4",
            "Manual",
        ],
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Load iNELS climate entities from config entry."""
    device_list: list[Device] = hass.data[DOMAIN][config_entry.entry_id][DEVICES]
    old_entities: list[str] = hass.data[DOMAIN][config_entry.entry_id][
        OLD_ENTITIES
    ].get(Platform.CLIMATE)

    items = INELS_CLIMATE_TYPES.items()
    entities: list[InelsBaseEntity] = []
    for device in device_list:
        for key, type_dict in items:
            if hasattr(device.state, key):
                entities.append(
                    InelsClimate(
                        device=device,
                        key=key,
                        index=-1,
                        description=InelsClimateDescription(
                            key=key,
                            name=type_dict.name,
                            hvac_modes=type_dict.hvac_modes,
                            features=type_dict.features,
                            presets=type_dict.presets,
                        ),
                    )
                )

    async_add_entities(entities)

    if old_entities:
        for entity in entities:
            if entity.entity_id in old_entities:
                old_entities.pop(old_entities.index(entity.entity_id))

    hass.data[DOMAIN][config_entry.entry_id][Platform.CLIMATE] = old_entities


@dataclass
class InelsClimateDescription(ClimateEntityDescription):
    """Inels Climate entity description class."""

    name: str = "Climate"
    hvac_modes: list[HVACMode] | None = None
    features: list[ClimateEntityFeature] | None = None
    presets: list[str] | None = None


class InelsClimate(InelsBaseEntity, ClimateEntity):
    """Inels Climate entity for HA."""

    _attr_temperature_unit: str = UnitOfTemperature.CELSIUS

    entity_description: InelsClimateDescription

    def __init__(
        self, device: Device, key: str, index: int, description: InelsClimateDescription
    ) -> None:
        """Initialize a climate entity."""
        super().__init__(device=device, key=key, index=index)

        self.entity_description = description

        self._attr_max_temp = DEFAULT_MAX_TEMP
        self._attr_min_temp = DEFAULT_MIN_TEMP

        self._attr_unique_id = slugify(f"{self._attr_unique_id}_{description.key}")
        self.entity_id = f"{Platform.CLIMATE}.{self._attr_unique_id}"
        self._attr_name = f"{self._attr_name} {description.name}"
        # self._attr_supported_features = description.features

    @property
    def current_temperature(self) -> float | None:
        """Get current temperature."""
        return self._device.state.__dict__[self.key].current

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        if len(self.entity_description.features) == 0:
            return self.entity_description.features
        else:
            return self.entity_description.features[
                self._device.state.__dict__[self.key].control_mode
            ]

    @property
    def target_temperature(self) -> float | None:
        """Get target temperature."""
        if self.hvac_mode == HVACMode.COOL:
            return self._device.state.__dict__[self.key].required_cool
        else:
            return self._device.state.__dict__[self.key].required

    @property
    def target_temperature_high(self) -> float | None:
        """Return the target heat temperature."""
        # if self.
        # virt controller on two temp mode
        return self._device.state.__dict__[self.key].required

    @property
    def target_temperature_low(self) -> float | None:
        """Return the target cool temperature."""
        return self._device.state.__dict__[self.key].required_cool

    @property
    def hvac_modes(self) -> list[HVACMode] | list[str]:
        """Return a list of available HVAC modes."""
        val = self._device.state.__dict__[self.key]
        if hasattr(val, "control_mode"):  # virtual controller
            if val.control_mode == 0:  # user controller
                return [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
            else:  # auto two-temp or single-temp
                return [HVACMode.OFF, HVACMode.AUTO]
        return self.entity_description.hvac_modes

    @property
    def hvac_mode(self) -> HVACMode | str | None:
        """Return the current HVAC mode."""
        val = self._device.state.__dict__[self.key]

        return CLIMATE_MODE_TO_HVAC_MODE.get(val.climate_mode)

    @property
    def hvac_action(self) -> HVACAction | str | None:
        """Return the current HVAC action."""
        val = self._device.state.__dict__[self.key]

        return CLIMATE_ACTION_TO_HVAC_ACTION.get(val.current_action)

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        val = self._device.state.__dict__[self.key]

        if hasattr(val, "current_preset") and val.control_mode == 0:  # user controlled
            return self.preset_modes[val.current_preset]
        return None

    @property
    def preset_modes(self) -> list[str] | None:
        """Return a list of available preset modes."""
        val = self._device.state.__dict__[self.key]

        if hasattr(val, "current_preset") and val.control_mode == 0:  # user controlled
            return self.entity_description.presets
        return None

    async def async_set_temperature(self, **kwargs) -> None:
        """Set the required temperature."""
        ha_val = self._device.state
        if hasattr(ha_val.__dict__[self.key], "control_mode"):
            if ha_val.__dict__[self.key].control_mode != 0:
                return

            if ATTR_TEMPERATURE in kwargs:
                if self.hvac_mode == HVACMode.COOL:
                    ha_val.__dict__[self.key].required_cool = kwargs.get(
                        ATTR_TEMPERATURE
                    )
                else:
                    ha_val.__dict__[self.key].required = kwargs.get(ATTR_TEMPERATURE)

            if hasattr(ha_val.__dict__[self.key], "current_preset"):
                ha_val.__dict__[self.key].current_preset = 5  # manual mode
        else:
            if ATTR_TEMPERATURE in kwargs:
                if self.hvac_mode == HVACMode.COOL:
                    ha_val.__dict__[self.key].required_cool = kwargs.get(
                        ATTR_TEMPERATURE
                    )
                else:
                    ha_val.__dict__[self.key].required = kwargs.get(ATTR_TEMPERATURE)

        await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode of the climate device."""
        ha_val = self._device.state

        if hasattr(ha_val.__dict__[self.key], "control_mode"):
            ha_val.__dict__[self.key].climate_mode = HVAC_MODE_TO_CLIMATE_MODE[
                hvac_mode
            ]

            last_val = self._device.last_values.ha_value
            if (
                hvac_mode != HVACMode.OFF
                and hasattr(ha_val.__dict__[self.key], "current_preset")
                and ha_val.__dict__[self.key].current_preset == 0
            ):
                ha_val.__dict__[self.key].required = last_val.__dict__[
                    self.key
                ].required
                ha_val.__dict__[self.key].required_cool = last_val.__dict__[
                    self.key
                ].required_cool
        else:
            ha_val = self._device.state
            if hvac_mode == HVACMode.OFF:
                ha_val.__dict__[self.key].required = 0
            elif hvac_mode == HVACMode.HEAT:
                ha_val.__dict__[self.key].required = (
                    ha_val.__dict__[self.key].current + 2
                )

        return await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the climate device."""
        ha_val = self._device.state
        new_preset = self.entity_description.presets.index(preset_mode)
        ha_val.__dict__[self.key].current_preset = new_preset

        return await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

"""iNELS light."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from inelsmqtt.devices import Device

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import DEVICES, DOMAIN, ICON_FLASH, ICON_LIGHT, LOGGER, OLD_ENTITIES
from .entity import InelsBaseEntity


# LIGHT PLATFORM
@dataclass
class InelsLightAlert:
    """Inels light alert property description."""

    key: str
    message: str


thermal_alert = InelsLightAlert(
    key="toa", message="Thermal overload on light %s of device %d"
)

current_alert = InelsLightAlert(
    key="coa", message="Current overload on light %s of device %d"
)

dali_comm = InelsLightAlert(
    key="alert_dali_communication",
    message="Dali communication error on light %s of device %d",
)

dali_power = InelsLightAlert(
    key="alert_dali_communication", message="Dali power error on light %s of device %d"
)

aout_current = InelsLightAlert(
    key="aout_coa", message="Current overload of AOUT %s of device %d"
)


@dataclass
class InelsLightType:
    """Light type property description."""

    name: str
    color_modes: list[ColorMode]
    icon: str = ICON_LIGHT
    alerts: list[InelsLightAlert] | None = None


INELS_LIGHT_TYPES: dict[str, InelsLightType] = {
    "simple_light": InelsLightType(name="Light", color_modes=[ColorMode.BRIGHTNESS]),
    "light_coa_toa": InelsLightType(
        name="Light",
        color_modes=[ColorMode.BRIGHTNESS],
        alerts=[current_alert, thermal_alert],
    ),
    "dali": InelsLightType(
        name="DALI", color_modes=[ColorMode.BRIGHTNESS], alerts=[dali_comm, dali_power]
    ),
    "aout": InelsLightType(
        name="Analog output",
        icon=ICON_FLASH,
        color_modes=[ColorMode.BRIGHTNESS],
        alerts=[aout_current],
    ),
    "rgb": InelsLightType(
        name="RGB light", color_modes=[ColorMode.BRIGHTNESS, ColorMode.RGB]
    ),
    "rgbw": InelsLightType(
        name="RGBW light", color_modes=[ColorMode.BRIGHTNESS, ColorMode.RGBW]
    ),
    "warm_light": InelsLightType(
        name="Tunable white light",
        color_modes=[ColorMode.BRIGHTNESS, ColorMode.COLOR_TEMP],
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Load iNELS lights from config entry."""
    device_list: list[Device] = hass.data[DOMAIN][config_entry.entry_id][DEVICES]
    old_entities: list[str] = hass.data[DOMAIN][config_entry.entry_id][
        OLD_ENTITIES
    ].get(Platform.LIGHT)

    items = INELS_LIGHT_TYPES.items()
    entities: list[InelsBaseEntity] = []
    for device in device_list:
        for key, type_dict in items:
            if hasattr(device.state, key):
                if len(device.state.__dict__[key]) == 1:
                    entities.append(
                        InelsLight(
                            device=device,
                            key=key,
                            index=0,
                            description=InelsLightDescription(
                                key=key,
                                name=type_dict.name,
                                icon=type_dict.icon,
                                color_modes=type_dict.color_modes,
                            ),
                        )
                    )
                else:
                    entities.extend(
                        [
                            InelsLight(
                                device=device,
                                key=key,
                                index=k,
                                description=InelsLightDescription(
                                    key=f"{key}{k}",
                                    name=f"{type_dict.name} {k+1}",
                                    icon=type_dict.icon,
                                    color_modes=type_dict.color_modes,
                                ),
                            )
                            for k in range(len(device.state.__dict__[key]))
                        ]
                    )

    async_add_entities(entities, True)

    if old_entities:
        for entity in entities:
            if entity.entity_id in old_entities:
                old_entities.pop(old_entities.index(entity.entity_id))

    hass.data[DOMAIN][config_entry.entry_id][Platform.LIGHT] = old_entities


@dataclass
class InelsLightDescription(LightEntityDescription):
    """iNELS light description."""

    color_modes: list[ColorMode] = field(default_factory=list)
    alerts: list[InelsLightAlert] | None = None


class InelsLight(InelsBaseEntity, LightEntity):
    """Light class for HA."""

    _entity_description: InelsLightDescription

    def __init__(
        self,
        device: Device,
        key: str,
        index: int,
        description: InelsLightDescription,
    ) -> None:
        """Initialize a light."""
        super().__init__(
            device=device,
            key=key,
            index=index,
        )
        self._entity_description = description

        self._attr_unique_id = slugify(f"{self._attr_unique_id}_{description.key}")
        self.entity_id = f"{Platform.LIGHT}.{self._attr_unique_id}"
        self._attr_name = f"{self._attr_name} {description.name}"

        self._attr_supported_color_modes: set[ColorMode] = set()
        self._attr_supported_color_modes |= set(description.color_modes)
        self._attr_min_color_temp_kelvin = (
            2700  # standard color temp, does not represent actual bulb
        )
        self._attr_max_color_temp_kelvin = (
            6500  # standard color temp, does not represent actual bulb
        )

    @property
    def available(self) -> bool:
        """If it is available."""
        if self._entity_description.alerts:
            last_state = self._device.last_values.ha_value.__dict__[self.key][
                self.index
            ]
            for alert in self._entity_description.alerts:
                if hasattr(self._device.state, alert.key):
                    if self._device.state.__dict__[alert.key]:
                        if not last_state.__dict__[alert.key]:
                            LOGGER.warning(alert.message, self.name, self._device_id)
                        return False
        return super().available

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._device.state.__dict__[self.key][self.index].brightness > 0

    @property
    def icon(self) -> str | None:
        """Light icon."""
        return self._entity_description.icon

    @property
    def brightness(self) -> int | None:
        """Light brightness."""
        return cast(
            int,
            self._device.state.__dict__[self.key][self.index].brightness * 2.55,
        )

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color value."""
        state = self._device.state.__dict__[self.key][self.index]
        if hasattr(state, "r"):
            return (state.r, state.g, state.b)
        return None

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the RGBW color value."""
        state = self._device.state.__dict__[self.key][self.index]
        if hasattr(state, "w"):
            return tuple(int(i * 2.55) for i in (state.r, state.g, state.b, state.w))
        return None

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the color temperature in Kelvin."""
        state = self._device.state.__dict__[self.key][self.index]
        if hasattr(state, "relative_ct"):
            return int(
                (state.relative_ct / 100)
                * (self.max_color_temp_kelvin - self.min_color_temp_kelvin)
                + self.min_color_temp_kelvin
            )
        return None

    @property
    def color_mode(self) -> ColorMode | str | None:
        """Return the color mode of the light."""
        state = self._device.state.__dict__[self.key][self.index]
        if hasattr(state, "w"):
            return ColorMode.RGBW
        if hasattr(state, "r"):
            return ColorMode.RGB
        if hasattr(state, "relative_ct"):
            return ColorMode.COLOR_TEMP
        return super().color_mode

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Light to turn off."""
        if not self._device:
            return

        transition = None
        if ATTR_TRANSITION in kwargs:
            transition = int(kwargs[ATTR_TRANSITION]) / 0.065
        else:
            # mount device ha value
            ha_val = self._device.get_value().ha_value
            ha_val.__dict__[self.key][self.index].brightness = 0
            await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Light to turn on."""
        if not self._device:
            return

        ha_val = self._device.get_value().ha_value

        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]

            ha_val.__dict__[self.key][self.index].r = rgb[0]
            ha_val.__dict__[self.key][self.index].g = rgb[1]
            ha_val.__dict__[self.key][self.index].b = rgb[2]
        elif ATTR_RGBW_COLOR in kwargs:
            rgbw = kwargs[ATTR_RGBW_COLOR]

            ha_val.__dict__[self.key][self.index].r = int(rgbw[0] / 2.55)
            ha_val.__dict__[self.key][self.index].g = int(rgbw[1] / 2.55)
            ha_val.__dict__[self.key][self.index].b = int(rgbw[2] / 2.55)
            ha_val.__dict__[self.key][self.index].w = int(rgbw[3] / 2.55)
        elif ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] / 2.55)
            brightness = min(brightness, 100)

            ha_val.__dict__[self.key][self.index].brightness = brightness
        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            color_temp = int(kwargs[ATTR_COLOR_TEMP_KELVIN])

            ha_val.__dict__[self.key][self.index].relative_ct = int(  # 0-100%
                100
                * (color_temp - self.min_color_temp_kelvin)
                / (self.max_color_temp_kelvin - self.min_color_temp_kelvin)
            )
        else:
            last_val = self._device.last_values.ha_value

            # uses previously observed brightness value if it isn't 0
            ha_val.__dict__[self.key][self.index].brightness = (
                100
                if last_val.__dict__[self.key][self.index].brightness == 0
                else last_val.__dict__[self.key][self.index].brightness
            )

        await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

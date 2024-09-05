"""iNELS selector entity."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from inelsmqtt.devices import Device

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import (
    DEVICES,
    DOMAIN,
    FAN_SPEED_DICT,
    ICON_FAN,
    OLD_ENTITIES,
    SELECT_OPTIONS_DICT,
    SELECT_OPTIONS_ICON,
)
from .entity import InelsBaseEntity


# SELECT PLATFORM
@dataclass
class InelsSelectType:
    """Select type property description."""

    name: str
    icon: str
    options: list[str]
    options_dict: dict[str, int]


INELS_SELECT_TYPES: dict[str, InelsSelectType] = {
    "fan_speed": InelsSelectType(
        name="Fan speed",
        icon=ICON_FAN,
        options=["Off", "Speed 1", "Speed 2", "Speed 3"],
        options_dict={"Off": 0, "Speed 1": 1, "Speed 2": 2, "Speed 3": 3},
    ),
}


@dataclass
class InelsSelectEntityDescriptionMixin:
    """Mixin keys."""


@dataclass
class InelsSelectEntityDescription(
    SelectEntityDescription, InelsSelectEntityDescriptionMixin
):
    """Class for describing the iNELS select entities."""

    value: Callable[[Device, str], Any | None] | None = None


def __set_fan_speed(device: Device, option: str) -> Any | None:
    """Process option value and set fan speed."""
    ha_val = device.state

    if option in FAN_SPEED_DICT:
        ha_val.fan_speed = FAN_SPEED_DICT[option]

    return ha_val


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Load iNELS select entity."""
    device_list: list[Device] = hass.data[DOMAIN][config_entry.entry_id][DEVICES]
    old_entities: list[str] = hass.data[DOMAIN][config_entry.entry_id][
        OLD_ENTITIES
    ].get(Platform.SELECT, [])

    entities: list[InelsSelect] = []

    for device in device_list:
        val = device.get_value()
        if hasattr(val.ha_value, "fan_speed"):
            entities.append(
                InelsSelect(
                    device,
                    key="fan_speed",
                    index=-1,
                    description=InelsSelectEntityDescription(
                        key="fan_speed",
                        name="Fan speed",
                        value=__set_fan_speed,
                    ),
                )
            )
    async_add_entities(entities, True)

    if old_entities:
        for entity in entities:
            if entity.entity_id in old_entities:
                old_entities.pop(old_entities.index(entity.entity_id))

    hass.data[DOMAIN][config_entry.entry_id][OLD_ENTITIES][Platform.SELECT] = (
        old_entities
    )


class InelsSelect(InelsBaseEntity, SelectEntity):
    """The platform class for select for home assistant."""

    entity_description: InelsSelectEntityDescription

    def __init__(
        self,
        device: Device,
        key: str,
        index: int,
        description: InelsSelectEntityDescription,
    ) -> None:
        """Initialize a select entity."""
        super().__init__(device=device, key=key, index=index)
        self.entity_description = description

        self._attr_unique_id = slugify(f"{self._attr_unique_id}_{description.key}")
        self.entity_id = f"{Platform.SELECT}.{self._attr_unique_id}"
        self._attr_name = f"{self._attr_name} {self.entity_description.name}"

    @property
    def unique_id(self) -> str | None:
        """Return the unique_id of the entity."""
        return super().unique_id

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        return super().name

    @property
    def icon(self) -> str | None:
        """Return the icon of the entity."""
        if self.key in SELECT_OPTIONS_ICON:
            return SELECT_OPTIONS_ICON[self.key]
        return super().icon

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        state = self._device.state
        option = state.__dict__[self.key]
        return SELECT_OPTIONS_DICT[self.key][option]

    @property
    def options(self) -> list[str]:
        """Return option list."""
        if str(self.key) in SELECT_OPTIONS_DICT:
            return SELECT_OPTIONS_DICT[self.key]

        return []

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self.entity_description.value:
            new_ha_val = self.entity_description.value(self._device, option)

            self.hass.async_add_executor_job(self._device.set_ha_value, new_ha_val)

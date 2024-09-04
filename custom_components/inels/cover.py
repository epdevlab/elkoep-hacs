"""iNELS cover entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from inelsmqtt.const import Shutter_state
from inelsmqtt.devices import Device

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityDescription,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import DEVICES, DOMAIN, ICON_SHUTTER_CLOSED, ICON_SHUTTER_OPEN, OLD_ENTITIES
from .entity import InelsBaseEntity


@dataclass
class InelsShutterType:
    """Shutter type property description."""

    name: str
    supported_features: CoverEntityFeature


# SHUTTERS PLATFORM
INELS_SHUTTERS_TYPES: dict[str, InelsShutterType] = {
    "simple_shutters": InelsShutterType(  # no is_closed status
        "Shutter",
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP,
    ),
    "shutters": InelsShutterType(
        "Shutter",
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP,
    ),
    "shutters_with_pos": InelsShutterType(
        "Shutter",
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Load iNELS cover from config entry."""
    device_list: list[Device] = hass.data[DOMAIN][config_entry.entry_id][DEVICES]
    old_entities: list[str] = hass.data[DOMAIN][config_entry.entry_id][
        OLD_ENTITIES
    ].get(Platform.COVER, [])

    items = INELS_SHUTTERS_TYPES.items()
    entities: list[InelsBaseEntity] = []
    for device in device_list:
        for key, type_dict in items:
            if hasattr(device.state, key):
                if len(device.state.__dict__[key]) == 1:
                    entities.append(
                        InelsCover(
                            device=device,
                            key=key,
                            index=0,
                            description=InelsCoverEntityDescription(
                                key=key,
                                name=str(type_dict.name),
                                supported_features=type_dict.supported_features,
                            ),
                        )
                    )
                else:
                    entities.extend(
                        [
                            InelsCover(
                                device=device,
                                key=key,
                                index=k,
                                description=InelsCoverEntityDescription(
                                    key=f"{key}{k}",
                                    name=f"{type_dict.name} {k+1}",
                                    supported_features=type_dict.supported_features,
                                ),
                            )
                            for k in range(len(device.state.__dict__[key]))
                        ]
                    )

    async_add_entities(entities, False)

    if old_entities:
        for entity in entities:
            if entity.entity_id in old_entities:
                old_entities.pop(old_entities.index(entity.entity_id))

    hass.data[DOMAIN][config_entry.entry_id][OLD_ENTITIES][Platform.COVER] = old_entities


@dataclass
class InelsCoverEntityDescription(CoverEntityDescription):
    """Class for description inels entities."""

    supported_features: CoverEntityFeature | None = None


class InelsCover(InelsBaseEntity, CoverEntity):
    """Cover class for Home Assistant."""

    entity_description: InelsCoverEntityDescription

    def __init__(
        self,
        device: Device,
        key: str,
        index: int,
        description: InelsCoverEntityDescription,
    ) -> None:
        """Initialize a cover entity."""
        super().__init__(device=device, key=key, index=index)
        self.entity_description = description

        self._attr_device_class = CoverDeviceClass.SHUTTER

        self._attr_unique_id = slugify(f"{self._attr_unique_id}_{description.key}")
        self.entity_id = f"{Platform.COVER}.{self._attr_unique_id}"
        self._attr_name = f"{self._attr_name} {description.name}"

        self._attr_supported_features = description.supported_features

    @property
    def icon(self) -> str | None:
        """Cover icon."""
        return ICON_SHUTTER_CLOSED if self.is_closed is True else ICON_SHUTTER_OPEN

    @property
    def is_opening(self) -> bool | None:
        """Return whether the cover is opening."""
        if self.key not in ["shutters", "shutters_with_pos"]:
            return (
                self._device.state.__dict__[self.key][self.index].state
                == Shutter_state.Open
            )

    @property
    def is_closing(self) -> bool | None:
        """Return whether the cover is closing."""
        if self.key not in ["shutters", "shutters_with_pos"]:
            return (
                self._device.state.__dict__[self.key][self.index].state
                == Shutter_state.Closed
            )

    @property
    def is_closed(self) -> bool | None:
        """Cover is closed."""
        return self._device.state.__dict__[self.key][self.index].is_closed

    @property
    def current_cover_position(self) -> int | None:
        """Return current cover position."""
        if hasattr(self._device.state.__dict__[self.key][self.index], "position"):
            return self._device.state.__dict__[self.key][self.index].position
        return super().current_cover_position

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set cover position."""
        if hasattr(self._device.state.__dict__[self.key][self.index], "position"):
            ha_val = self._device.state
            ha_val.__dict__[self.key][self.index].position = kwargs[ATTR_POSITION]
            ha_val.__dict__[self.key][self.index].set_pos = True
            await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open cover."""
        ha_val = self._device.state
        ha_val.__dict__[self.key][self.index].state = Shutter_state.Open
        await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        ha_val = self._device.state
        ha_val.__dict__[self.key][self.index].state = Shutter_state.Closed
        await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop cover."""
        ha_val = self._device.state
        ha_val.__dict__[self.key][self.index].state = (
            Shutter_state.Stop_up if self.is_closed else Shutter_state.Stop_down
        )
        await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

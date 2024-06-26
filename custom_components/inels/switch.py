"""iNELS switch entity."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from inelsmqtt.devices import Device

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .entity import InelsBaseEntity
from .const import (
    DEVICES,
    DOMAIN,
    ICON_SWITCH,
    LOGGER,
    OLD_ENTITIES,
)


# SWITCH PLATFORM
@dataclass
class InelsSwitchAlert:
    """Inels switch alert property description."""

    key: str
    message: str


relay_overflow = InelsSwitchAlert(key="overflow", message="Relay overflow in %s of %d")


@dataclass
class InelsSwitchType:
    """Inels switch property description"""

    name: str = "Relay"
    icon: str = ICON_SWITCH
    overflow: str | None = None
    alerts: list[InelsSwitchAlert] | None = None


INELS_SWITCH_TYPES: dict[str, InelsSwitchType] = {
    "bit": InelsSwitchType(),
    "simple_relay": InelsSwitchType(),
    "relay": InelsSwitchType(alerts=[relay_overflow]),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Load iNELS switch.."""
    device_list: list[Device] = hass.data[DOMAIN][config_entry.entry_id][DEVICES]
    old_entities: list[str] = hass.data[DOMAIN][config_entry.entry_id][
        OLD_ENTITIES
    ].get(Platform.SWITCH)

    items = INELS_SWITCH_TYPES.items()
    entities: list[InelsBaseEntity] = []
    for device in device_list:
        for key, type_dict in items:
            if hasattr(device.state, key):
                if len(device.state.__dict__[key]) == 1:
                    entities.append(
                        InelsBusSwitch(
                            device=device,
                            key=key,
                            index=0,
                            description=InelsSwitchEntityDescription(
                                key=key,
                                name=type_dict.name,
                                icon=type_dict.icon,
                                overload_key=type_dict.overflow,
                            ),
                        )
                    )
                else:
                    for k in range(len(device.state.__dict__[key])):
                        description=InelsSwitchEntityDescription(
                            key=f"{key}{k}",
                            name=f"{type_dict.name} {k+1}",
                            icon=type_dict.icon,
                            overload_key=type_dict.overflow,
                        )

                        if device.inels_type == 'BITS':
                            description.name = f"Bit {device.state.__dict__[key][k].addr}"

                        entities.append(
                            InelsBusSwitch(
                                device=device,
                                key=key,
                                index=k,
                                description=description,
                            )
                        )
    async_add_entities(entities, False)

    if old_entities:
        for entity in entities:
            if entity.entity_id in old_entities:
                old_entities.pop(old_entities.index(entity.entity_id))

    hass.data[DOMAIN][config_entry.entry_id][Platform.SWITCH] = old_entities


@dataclass
class InelsSwitchEntityDescription(SwitchEntityDescription):
    """Class for description inels entities."""

    overload_key: str | None = None
    alerts: list[InelsSwitchAlert] | None = None


class InelsBusSwitch(InelsBaseEntity, SwitchEntity):
    """The platform class required by Home Assistant, bus version."""

    entity_description: InelsSwitchEntityDescription

    def __init__(
        self,
        device: Device,
        key: str,
        index: int,
        description: InelsSwitchEntityDescription,
    ) -> None:
        """Initialize a bus switch."""
        super().__init__(device=device, key=key, index=index)

        self.entity_description = description

        self._attr_unique_id = slugify(f"{self._attr_unique_id}_{description.key}")
        self.entity_id = f"{Platform.SWITCH}.{self._attr_unique_id}"
        self._attr_name = f"{self._attr_name} {description.name}"

    @property
    def available(self) -> bool:
        """Return entity availability."""
        if self.entity_description.alerts:
            last_state = self._device.last_values.ha_value.__dict__[self.key][
                self.index
            ]
            for alert in self.entity_description.alerts:
                if hasattr(self._device.state, alert.key):
                    if self._device.state.__dict__[alert.key]:
                        if not last_state.__dict__[alert.key]:
                            LOGGER.warning(alert.message, self.name, self._device_id)
                        return False
        return super().available

    @property
    def is_on(self) -> bool | None:
        """Return if switch is on."""
        state = self._device.state
        return state.__dict__[self.key][self.index].is_on

    @property
    def icon(self) -> str | None:
        """Switch icon."""
        return self.entity_description.icon

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the switch to turn off."""
        if not self._device.is_available:
            return None

        ha_val = self._device.state
        ha_val.__dict__[self.key][self.index].is_on = False

        await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the switch to turn on."""
        if not self._device.is_available:
            return None

        ha_val = self._device.state
        ha_val.__dict__[self.key][self.index].is_on = True

        await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

"""iNELS number entity."""

from __future__ import annotations

from dataclasses import dataclass

from inelsmqtt.devices import Device

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import DEVICES, DOMAIN, ICON_NUMBER, OLD_ENTITIES
from .entity import InelsBaseEntity


# NUMBER PLATFORM
@dataclass
class InelsNumberType:
    """Inels number property description."""

    name: str = "Integer"
    icon: str = ICON_NUMBER


INELS_NUMBER_TYPES: dict[str, InelsNumberType] = {"number": InelsNumberType()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Load iNELS number.."""
    device_list: list[Device] = hass.data[DOMAIN][config_entry.entry_id][DEVICES]
    old_entities: list[str] = hass.data[DOMAIN][config_entry.entry_id][
        OLD_ENTITIES
    ].get(Platform.NUMBER, [])

    items = INELS_NUMBER_TYPES.items()
    entities: list[InelsBaseEntity] = []
    for device in device_list:
        for key, type_dict in items:
            if hasattr(device.state, key):
                entities.extend(
                    [
                        InelsBusNumber(
                            device=device,
                            key=key,
                            index=k,
                            description=NumberEntityDescription(
                                key=f"{key}{k}",
                                name=f"{type_dict.name} {device.state.__dict__[key][k].addr}",
                                icon=type_dict.icon,
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

    hass.data[DOMAIN][config_entry.entry_id][OLD_ENTITIES][Platform.NUMBER] = old_entities


class InelsBusNumber(InelsBaseEntity, NumberEntity):
    """The platform class required by Home Assistant, bus version."""

    entity_description: NumberEntityDescription

    def __init__(
        self,
        device: Device,
        key: str,
        index: int,
        description: NumberEntityDescription,
    ) -> None:
        """Initialize a bus number."""
        super().__init__(device=device, key=key, index=index)

        self.entity_description = description

        self._attr_native_max_value = 2147483647
        self._attr_native_min_value = -2147483648
        self._attr_unique_id = slugify(f"{self._attr_unique_id}_{description.key}")
        self.entity_id = f"{Platform.NUMBER}.{self._attr_unique_id}"
        self._attr_name = f"{self._attr_name} {description.name}"

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return super().available

    @property
    def native_value(self) -> int | None:
        """Return number."""
        state = self._device.state
        return state.__dict__[self.key][self.index].value

    @property
    def icon(self) -> str | None:
        """Number icon."""
        return self.entity_description.icon

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        if not self._device.is_available:
            return

        ha_val = self._device.state
        ha_val.__dict__[self.key][self.index].value = value

        await self.hass.async_add_executor_job(self._device.set_ha_value, ha_val)

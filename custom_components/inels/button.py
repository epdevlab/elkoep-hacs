"""Support for iNELS buttons."""

from __future__ import annotations

from dataclasses import dataclass

from inelsmqtt.const import (
    GBP3_60,
    GCH3_31,
    GCR3_11,
    GDB3_10,
    GRT3_50,
    GSB3_20SX,
    GSB3_40SX,
    GSB3_60SX,
    GSB3_90SX,
    GSP3_100,
    IDRT3_1,
    JA3_014M,
    JA3_018M,
    WSB3_20,
    WSB3_20H,
    WSB3_40,
    WSB3_40H,
)
from inelsmqtt.devices import Device

from homeassistant.components.button import (
    SERVICE_PRESS,
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import (
    DEVICES,
    DOMAIN,
    ICON_BUTTON,
    ICON_CYCLE,
    ICON_DOWN,
    ICON_ECO,
    ICON_FAN_1,
    ICON_FAN_2,
    ICON_FAN_3,
    ICON_MINUS,
    ICON_PLUS,
    ICON_UP,
    OLD_ENTITIES,
)
from .entity import InelsBaseEntity


# BUTTON PLATFORM
@dataclass
class InelsButtonType:
    """Button type property description."""

    name: str
    icon: str = ICON_BUTTON
    entity_category: EntityCategory = EntityCategory.CONFIG


INELS_BUTTON_TYPES: dict[str, InelsButtonType] = {
    "btn": InelsButtonType(name="Button"),
    "din": InelsButtonType(name="Digital input"),
    "sw": InelsButtonType(name="Switch"),
    "plus": InelsButtonType(name="Plus", icon=ICON_PLUS),
    "minus": InelsButtonType(name="Minus", icon=ICON_MINUS),
    "interface": InelsButtonType(name="Interface"),  # special backup case
}


plus = InelsButtonType(name="Plus", icon=ICON_PLUS)
minus = InelsButtonType(name="Minus", icon=ICON_MINUS)

ROWS_3 = ["Top", "Middle", "Bottom"]
COLUMNS_3 = ["Left", "Center", "Right"]
ROWS_2 = ["Top", "Bottom"]
COLUMNS_2 = ["Left", "Right"]
UP_DOWN = ["Up", "Down"]

INELS_BUTTON_INTERFACE: dict[str, list[InelsButtonType]] = {
    GRT3_50: [
        InelsButtonType(name="Cycle", icon=ICON_CYCLE),
        InelsButtonType(name="Fan 1", icon=ICON_FAN_1),
        InelsButtonType(name="Fan 2", icon=ICON_FAN_2),
        InelsButtonType(name="Eco", icon=ICON_ECO),
        InelsButtonType(name="Fan 3", icon=ICON_FAN_3),
        plus,
        minus,
    ],
    GSB3_90SX: [
        InelsButtonType(name=f"{ROWS_3[i%3]} {COLUMNS_3[int(i/3)]}") for i in range(9)
    ],
    WSB3_20: [InelsButtonType(name=ROWS_2[int(i)]) for i in range(2)],
    WSB3_20H: [InelsButtonType(name=ROWS_2[int(i)]) for i in range(2)],
    WSB3_40: [
        InelsButtonType(name=f"{ROWS_2[i%2]} {COLUMNS_2[int(i/2)]}") for i in range(4)
    ],
    WSB3_40H: [
        InelsButtonType(name=f"{ROWS_2[i%2]} {COLUMNS_2[int(i/2)]}") for i in range(2)
    ],
    GCR3_11: [InelsButtonType(name=COLUMNS_3[i]) for i in range(3)],
    GCH3_31: [InelsButtonType(name=COLUMNS_3[i]) for i in range(3)],
    GSP3_100: [
        InelsButtonType(name=f"{ROWS_2[i%2]} {int(i/2) + 1}") for i in range(10)
    ],
    GDB3_10: [InelsButtonType(name=COLUMNS_3[i]) for i in range(3)],
    GSB3_40SX: [
        InelsButtonType(name=f"{ROWS_2[i%2]} {COLUMNS_2[int(i/2)]}") for i in range(4)
    ],
    GSB3_60SX: [
        InelsButtonType(name=f"{ROWS_2[i%2]} {COLUMNS_3[int(i/2)]}") for i in range(6)
    ],
    GSB3_20SX: [InelsButtonType(name=ROWS_2[i]) for i in range(2)],
    GBP3_60: [
        InelsButtonType(name=f"{ROWS_2[i%2]} {COLUMNS_3[int(i/2)]}") for i in range(6)
    ],
    IDRT3_1: [
        InelsButtonType(name="Down", icon=ICON_DOWN),
        InelsButtonType(name="Up", icon=ICON_UP),
    ],
    JA3_018M: [
        InelsButtonType(
            name=f"Switch {UP_DOWN[i%2]} {int(i/2) + 1}",
            icon=ICON_UP if i % 2 == 0 else ICON_DOWN,
        )
        for i in range(18)
    ],
    JA3_014M: [
        InelsButtonType(
            name=f"Switch {UP_DOWN[i % 2]} {int(i / 2) + 1}",
            icon=ICON_UP if i % 2 == 0 else ICON_DOWN,
        )
        for i in range(14)
    ],
}


@dataclass
class InelsButtonDescription(ButtonEntityDescription):
    """A class that describes button entity."""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Load iNELS buttons from config entry."""
    device_list: list[Device] = hass.data[DOMAIN][config_entry.entry_id][DEVICES]
    old_entities: list[str] = hass.data[DOMAIN][config_entry.entry_id][
        OLD_ENTITIES
    ].get(Platform.BUTTON, [])

    items = INELS_BUTTON_TYPES.items()
    entities: list[InelsBaseEntity] = []
    for device in device_list:
        val = device.state
        for key, type_dict in items:
            if hasattr(device.state, key):
                for k in range(len(val.__dict__[key])):
                    if key == "interface":  # special case
                        btn_type = INELS_BUTTON_INTERFACE.get(device.inels_type)
                        name = f"Interface {k}"
                        icon = ICON_BUTTON
                        category = EntityCategory.CONFIG
                        if btn_type and (k < len(btn_type)):
                            name = btn_type[k].name
                            icon = btn_type[k].icon
                            category = btn_type[k].entity_category

                        entities.append(
                            InelsButton(
                                device=device,
                                key="interface",
                                index=k,
                                description=InelsButtonDescription(
                                    key=f"interface{k}",
                                    name=name,
                                    icon=icon,
                                    entity_category=category,
                                ),
                            )
                        )
                    else:
                        entities.append(
                            InelsButton(
                                device=device,
                                key=key,
                                index=k,
                                description=InelsButtonDescription(
                                    key=f"{key}{k+1}",
                                    name=f"{type_dict.name} {k+1}",
                                    icon=type_dict.icon,
                                    entity_category=type_dict.entity_category,
                                ),
                            )
                        )

    async_add_entities(entities)

    if old_entities:
        for entity in entities:
            if entity.entity_id in old_entities:
                old_entities.pop(old_entities.index(entity.entity_id))

    hass.data[DOMAIN][config_entry.entry_id][OLD_ENTITIES][Platform.BUTTON] = old_entities


class InelsButton(InelsBaseEntity, ButtonEntity):
    """Button switch that can be toggled by MQTT. Specific version for Bus devices."""

    entity_description: InelsButtonDescription
    _attr_device_class: ButtonDeviceClass | None = None

    def __init__(
        self, device: Device, key: str, index: int, description: InelsButtonDescription
    ) -> None:
        """Initialize button."""
        super().__init__(device=device, key=key, index=index)
        self.entity_description = description

        self._attr_unique_id = slugify(f"{self._attr_unique_id}_{description.key}")
        self.entity_id = f"{Platform.BUTTON}.{self._attr_unique_id}"
        if description.name:
            self._attr_name = f"{self._attr_name} {description.name}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # since the buttons only work within HA, they can always be available
        return True

    def _callback(self) -> None:
        super()._callback()

        curr_val = self._device.state
        last_val = self._device.last_values.ha_value

        if (
            curr_val.__dict__[self.key][self.index]
            and not last_val.__dict__[self.key][self.index]
        ):
            self.hass.services.call(
                Platform.BUTTON,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: self.entity_id},
                True,
                self._context,
            )

    def press(self) -> None:
        """Press the button."""

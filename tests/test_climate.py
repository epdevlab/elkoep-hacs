"""iNELS climate platform testing."""

from unittest.mock import patch

import pytest

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
    HVACMode,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    STATE_UNAVAILABLE,
    Platform,
)
from homeassistant.core import HomeAssistant

from .common import MAC_ADDRESS, UNIQUE_ID, get_entity_id, old_entity_and_device_removal

DT_09 = "09"
DT_166 = "166"


@pytest.fixture(params=["thermovalve", "climate_controller"])
def entity_config(request: pytest.FixtureRequest):
    """Fixture to provide parameterized entity configuration for climate tests."""
    configs = {
        "thermovalve": {
            "entity_type": "climate",
            "device_type": "thermovalve",
            "dev_type": DT_09,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_09}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_09}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_09}/{UNIQUE_ID}",
            "climate_value": b"64\n3C\n08\n40\n00\n",
            "expected_state": HVACMode.HEAT,
        },
        "climate_controller": {
            "entity_type": "climate",
            "device_type": "climate_controller",
            "dev_type": DT_166,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_166}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_166}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_166}/{UNIQUE_ID}",
            "climate_value": b"3F\n0A\n00\n00\nFB\nFF\nFF\n7F\nFB\nFF\nFF\n7F\n00\n00\n00\n00\n00\n00\n00\n00\nFB\nFF\nFF\n7F\n00\n00\n00\n00\n00\n00\n00\n",
            "expected_state": HVACMode.OFF,
        },
    }
    return configs[request.param]


@pytest.mark.parametrize(
    "entity_config", ["thermovalve", "climate_controller"], indirect=True
)
@pytest.mark.parametrize(
    ("gw_available", "device_available", "expected_state"),
    [
        (False, True, STATE_UNAVAILABLE),
        (True, True, "lookup"),
    ],
)
async def test_climate_availability(
    hass: HomeAssistant,
    setup_entity,
    entity_config,
    gw_available,
    device_available,
    expected_state,
) -> None:
    """Test climate availability and state under different gateway and device availability conditions."""

    climate = await setup_entity(
        entity_config,
        status_value=entity_config["climate_value"],
        gw_available=gw_available,
        device_available=device_available,
    )

    assert climate is not None
    if expected_state == "lookup":
        assert climate.state == entity_config["expected_state"]
    else:
        assert climate.state == expected_state


@pytest.mark.parametrize(
    "entity_config", ["thermovalve", "climate_controller"], indirect=True
)
async def test_climate_set_temperature(
    hass: HomeAssistant, setup_entity, entity_config
) -> None:
    """Test setting temperature of a climate device."""
    climate = await setup_entity(
        entity_config, status_value=entity_config["climate_value"]
    )

    assert climate is not None
    assert climate.state in [HVACMode.OFF, HVACMode.HEAT]
    assert climate.attributes["temperature"] in [0, 32.0]  # required

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: get_entity_id(entity_config), ATTR_TEMPERATURE: 22},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]
        assert getattr(ha_value, entity_config["device_type"]).required == 22


@pytest.mark.parametrize(
    "entity_config",
    [
        "thermovalve",
        "climate_controller",
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    ("hvac_mode", "expected_value"),
    [
        (HVACMode.OFF, 0),
        (HVACMode.HEAT, 1),
        (HVACMode.COOL, 2),
    ],
)
async def test_climate_set_hvac_mode(
    hass: HomeAssistant, setup_entity, entity_config, hvac_mode, expected_value
) -> None:
    """Test setting HVAC mode of a climate device."""
    climate = await setup_entity(
        entity_config, status_value=entity_config["climate_value"]
    )

    assert climate is not None
    assert climate.state in [HVACMode.OFF, HVACMode.HEAT]

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: get_entity_id(entity_config), ATTR_HVAC_MODE: hvac_mode},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]
        if entity_config["device_type"] == "climate_controller":
            assert (
                getattr(ha_value, entity_config["device_type"]).climate_mode
                == expected_value
            )
        elif entity_config["device_type"] == "thermovalve":
            assert getattr(ha_value, entity_config["device_type"]).required in [0, 32.0]


@pytest.mark.parametrize(
    "entity_config",
    [
        "climate_controller",
    ],
    indirect=True,
)
async def test_climate_set_hvac_mode_and_preset(
    hass: HomeAssistant, setup_entity, entity_config
) -> None:
    """Test setting HVAC mode of a climate device."""
    climate = await setup_entity(
        entity_config,
        status_value=entity_config["climate_value"],
        last_value=entity_config["climate_value"],
    )

    assert climate is not None
    assert climate.state == HVACMode.OFF

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: get_entity_id(entity_config),
                ATTR_HVAC_MODE: HVACMode.COOL,
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]
        assert getattr(ha_value, entity_config["device_type"]).climate_mode == 2

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {
                ATTR_ENTITY_ID: get_entity_id(entity_config),
                ATTR_PRESET_MODE: "Schedule",
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]
        assert getattr(ha_value, entity_config["device_type"]).current_preset == 0

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: get_entity_id(entity_config),
                ATTR_HVAC_MODE: HVACMode.HEAT,
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]
        climate_state = getattr(ha_value, entity_config["device_type"])
        assert climate_state.climate_mode == 1
        assert climate_state.required == 0
        assert climate_state.required_cool == 0


@pytest.mark.parametrize(
    "entity_config",
    [
        "climate_controller",
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    ("preset_mode", "expected_value"),
    [
        ("Schedule", 0),
        ("Preset 1", 1),
        ("Preset 2", 2),
        ("Preset 3", 3),
        ("Preset 4", 4),
        ("Manual", 5),
    ],
)
async def test_climate_set_preset_mode(
    hass: HomeAssistant, setup_entity, entity_config, preset_mode, expected_value
) -> None:
    """Test setting preset mode of a climate device."""
    climate = await setup_entity(
        entity_config, status_value=entity_config["climate_value"]
    )

    assert climate is not None
    assert climate.state == HVACMode.OFF

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {
                ATTR_ENTITY_ID: get_entity_id(entity_config),
                ATTR_PRESET_MODE: preset_mode,
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]
        assert (
            getattr(ha_value, entity_config["device_type"]).current_preset
            == expected_value
        )


@pytest.mark.parametrize(
    ("entity_config", "value_key", "index"),
    [
        ("thermovalve", "climate_value", ""),
    ],
    indirect=["entity_config"],
)
async def test_climate_old_entity_and_device_removal(
    hass: HomeAssistant, mock_mqtt, entity_config, value_key, index
) -> None:
    """Test removal of old climate entity and device."""
    await old_entity_and_device_removal(
        hass, mock_mqtt, Platform.CLIMATE, entity_config, value_key, index
    )

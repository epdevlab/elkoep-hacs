"""iNELS select platform testing."""

from unittest.mock import patch

import pytest

from homeassistant.components.select import (
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_OPTION, STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from .common import MAC_ADDRESS, UNIQUE_ID, get_entity_id, old_entity_and_device_removal

DT_111 = "111"


@pytest.fixture(
    params=[
        "fan_speed",
    ]
)
def entity_config(request: pytest.FixtureRequest):
    """Fixture to provide parameterized entity configuration for select tests."""
    configs = {
        "fan_speed": {
            "entity_type": "select",
            "device_type": "fan_speed",
            "dev_type": DT_111,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_111}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_111}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_111}/{UNIQUE_ID}",
            "select_value": b"FF\nFF\nFF\nFF\n64\n64\n64\n64\n07\n07\n07\n07\n07\n07\n07\n07\n00\n00\nFF\nFF\n00\n00\nFF\nFF\n00\n00\nFF\nFF\n",
        },
    }
    return configs[request.param]


@pytest.mark.parametrize(
    "entity_config",
    [
        "fan_speed",
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    ("gw_available", "device_available", "expected_state"),
    [
        (True, False, STATE_UNAVAILABLE),
        (False, True, STATE_UNAVAILABLE),
        (True, True, "Speed 3"),
    ],
)
async def test_select_availability(
    hass: HomeAssistant,
    setup_entity,
    entity_config,
    gw_available,
    device_available,
    expected_state,
) -> None:
    """Test select availability and state under different gateway and device availability conditions."""

    select = await setup_entity(
        entity_config,
        status_value=entity_config["select_value"],
        gw_available=gw_available,
        device_available=device_available,
    )

    assert select is not None
    assert select.state == expected_state


@pytest.mark.parametrize(
    "entity_config",
    [
        "fan_speed",
    ],
    indirect=True,
)
async def test_select_option(hass: HomeAssistant, setup_entity, entity_config) -> None:
    """Test selecting an option."""
    select = await setup_entity(
        entity_config,
        status_value=entity_config["select_value"],
    )

    assert select is not None
    assert select.state == "Speed 3"

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: get_entity_id(entity_config), ATTR_OPTION: "Off"},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]
        assert getattr(ha_value, entity_config["device_type"]) == 0


@pytest.mark.parametrize(
    "entity_config",
    [
        "fan_speed",
    ],
    indirect=True,
)
async def test_select_option_bad_option(
    hass: HomeAssistant, setup_entity, entity_config
) -> None:
    """Test selecting an invalid option."""
    select = await setup_entity(
        entity_config,
        status_value=entity_config["select_value"],
    )

    assert select is not None
    assert select.state == "Speed 3"

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {
                ATTR_ENTITY_ID: get_entity_id(entity_config),
                ATTR_OPTION: "Invalid Option",
            },
            blocking=True,
        )
    await hass.async_block_till_done()

    assert select.state == "Speed 3"


@pytest.mark.parametrize(
    ("entity_config", "value_key", "index"),
    [
        ("fan_speed", "select_value", ""),
    ],
    indirect=["entity_config"],
)
async def test_select_old_entity_and_device_removal(
    hass: HomeAssistant, mock_mqtt, entity_config, value_key, index
) -> None:
    """Test removal of old select entity and device."""
    await old_entity_and_device_removal(
        hass, mock_mqtt, Platform.SELECT, entity_config, value_key, index
    )

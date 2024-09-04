"""iNELS number platform testing."""

from unittest.mock import patch

import pytest

from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from .common import MAC_ADDRESS, UNIQUE_ID, get_entity_id, old_entity_and_device_removal

DT_INTEGERS = "integers"


@pytest.fixture(params=["number"])
def entity_config(request: pytest.FixtureRequest):
    """Fixture to provide parameterized entity configuration for number tests."""
    configs = {
        "number": {
            "entity_type": "number",
            "device_type": "number",
            "dev_type": DT_INTEGERS,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_INTEGERS}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_INTEGERS}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_INTEGERS}/{UNIQUE_ID}",
            "number_value": b'{"state":{"000":1000}}',
        },
    }
    return configs[request.param]


@pytest.mark.parametrize(
    "entity_config",
    [
        "number",
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    ("gw_available", "device_available", "expected_state"),
    [
        (True, False, STATE_UNAVAILABLE),
        (False, True, STATE_UNAVAILABLE),
        (True, True, "1000"),
    ],
)
async def test_number_availability(
    hass: HomeAssistant,
    setup_entity,
    entity_config,
    gw_available,
    device_available,
    expected_state,
) -> None:
    """Test number availability and state under different gateway and device availability conditions."""

    number = await setup_entity(
        entity_config,
        status_value=entity_config["number_value"],
        gw_available=gw_available,
        device_available=device_available,
        index="0",
    )

    assert number is not None
    assert number.state == expected_state


@pytest.mark.parametrize("entity_config", ["number"], indirect=True)
async def test_number_set_value(
    hass: HomeAssistant, setup_entity, entity_config
) -> None:
    """Test setting value of a number."""
    number = await setup_entity(
        entity_config, status_value=entity_config["number_value"], index="0"
    )

    assert number is not None
    assert number.state == "1000"

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: get_entity_id(entity_config, "0"), ATTR_VALUE: 65535},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]
        assert getattr(ha_value, entity_config["device_type"])[0].value == 65535


@pytest.mark.parametrize("entity_config", ["number"], indirect=True)
async def test_number_set_out_of_range(
    hass: HomeAssistant, setup_entity, entity_config
) -> None:
    """Test min and max values of a number."""
    number = await setup_entity(
        entity_config, status_value=entity_config["number_value"], index="0"
    )

    assert number is not None

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                NUMBER_DOMAIN,
                SERVICE_SET_VALUE,
                {
                    ATTR_ENTITY_ID: get_entity_id(entity_config, "0"),
                    ATTR_VALUE: 2147483648,
                },
                blocking=True,
            )

        await hass.async_block_till_done()
        assert not mock_set_state.called

        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                NUMBER_DOMAIN,
                SERVICE_SET_VALUE,
                {
                    ATTR_ENTITY_ID: get_entity_id(entity_config, "0"),
                    ATTR_VALUE: -2147483649,
                },
                blocking=True,
            )

        await hass.async_block_till_done()
        assert not mock_set_state.called


@pytest.mark.parametrize(
    ("entity_config", "value_key", "index"),
    [
        ("number", "number_value", "0"),
    ],
    indirect=["entity_config"],
)
async def test_number_old_entity_and_device_removal(
    hass: HomeAssistant, mock_mqtt, entity_config, value_key, index
) -> None:
    """Test removal of old number and device."""
    await old_entity_and_device_removal(
        hass, mock_mqtt, Platform.NUMBER, entity_config, value_key, index
    )

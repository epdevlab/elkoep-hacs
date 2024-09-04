"""iNELS button platform testing."""

import pytest

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant

from .common import MAC_ADDRESS, UNIQUE_ID, old_entity_and_device_removal

DT_160 = "160"
DT_102 = "102"


@pytest.fixture(
    params=[
        "interface",
        "din",
    ]
)
def entity_config(request: pytest.FixtureRequest):
    """Fixture to provide parameterized entity configuration for button tests."""
    configs = {
        "interface": {
            "entity_type": "button",
            "device_type": "interface",
            "dev_type": DT_160,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_160}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_160}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_160}/{UNIQUE_ID}",
            "button_value": b"00\n0F\n0A\n28\n00\n00\n00\n00\n0A\n28\n",
            "button_last_value": b"00\n00\n0A\n28\n00\n00\n00\n00\n0A\n28\n",
        },
        "din": {
            "entity_type": "button",
            "device_type": "din",
            "dev_type": DT_102,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_102}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_102}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_102}/{UNIQUE_ID}",
            "button_value": b"00\n0F\n0A\n1D\n00\n00\n00\n00\n00\n00\n04\n37\n7F\nFF\n16\n60\n06\n7B\n",
            "button_last_value": b"00\n00\n0A\n1D\n00\n00\n00\n00\n00\n00\n04\n37\n7F\nFF\n16\n60\n06\n7B\n",
        },
    }
    return configs[request.param]


@pytest.mark.parametrize(
    ("entity_config", "index"),
    [
        ("interface", "0"),
        ("din", "1"),
    ],
    indirect=["entity_config"],
)
@pytest.mark.parametrize(
    ("gw_available", "device_available", "expected_state"),
    [
        (True, False, STATE_UNKNOWN),
        (False, True, STATE_UNKNOWN),
        (True, True, STATE_UNKNOWN),
    ],
)
async def test_button_availability(
    hass: HomeAssistant,
    setup_entity,
    entity_config,
    index,
    gw_available,
    device_available,
    expected_state,
) -> None:
    """Test button availability under different gateway and device availability conditions."""

    button = await setup_entity(
        entity_config,
        status_value=entity_config["button_value"],
        gw_available=gw_available,
        device_available=device_available,
        last_value=entity_config["button_last_value"],
        index=index,
    )

    assert button is not None
    assert button.state == expected_state

    entity = hass.data["entity_components"]["button"].get_entity(button.entity_id)

    await hass.async_add_executor_job(entity._callback)
    await hass.async_block_till_done()

    # Refresh the state
    state = hass.states.get(button.entity_id)

    assert state.state != STATE_UNKNOWN
    assert state.state != STATE_UNAVAILABLE


@pytest.mark.parametrize(
    ("entity_config", "value_key", "index"),
    [
        ("interface", "button_value", "0"),
    ],
    indirect=["entity_config"],
)
async def test_button_old_entity_and_device_removal(
    hass: HomeAssistant, mock_mqtt, entity_config, value_key, index
) -> None:
    """Test removal of old button entity and device."""
    await old_entity_and_device_removal(
        hass, mock_mqtt, Platform.BUTTON, entity_config, value_key, index
    )

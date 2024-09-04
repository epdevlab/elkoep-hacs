"""iNELS cover platform testing."""

from unittest.mock import patch

from inelsmqtt.const import Shutter_state
import pytest

from homeassistant.components.cover import (
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
    STATE_UNAVAILABLE,
    Platform,
)
from homeassistant.core import HomeAssistant

from .common import MAC_ADDRESS, UNIQUE_ID, get_entity_id, old_entity_and_device_removal

DT_03 = "03"
DT_21 = "21"
DT_109 = "109"


@pytest.fixture(params=["shutters_with_pos", "shutters", "simple_shutters"])
def entity_config(request: pytest.FixtureRequest):
    """Fixture to provide parameterized entity configuration for cover tests."""
    configs = {
        "shutters_with_pos": {
            "entity_type": "cover",
            "device_type": "shutters_with_pos",
            "dev_type": DT_21,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_21}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_21}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_21}/{UNIQUE_ID}",
            "cover_open_value": b"03\n00\n00\n",
            "cover_closed_value": b"03\n02\n64\n",
            "cover_open_half_value": b"03\n00\n32\n",
        },
        "shutters": {
            "entity_type": "cover",
            "device_type": "shutters",
            "dev_type": DT_03,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_03}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_03}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_03}/{UNIQUE_ID}",
            "cover_open_value": b"03\n00\n",
            "cover_closed_value": b"03\n01\n",
        },
        "simple_shutters": {
            "entity_type": "cover",
            "device_type": "simple_shutters",
            "dev_type": DT_109,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_109}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_109}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_109}/{UNIQUE_ID}",
            "cover_open_value": b"07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\n07\nFF\nFF\nFF\nFF\nFF\nFF\nFF\n",
            "cover_closed_value": b"06\n06\n06\n06\n06\n06\n06\n06\n06\n06\n06\n06\n06\n06\n06\n06\n06\n07\n06\n06\n06\n06\n00\n00\n00\n00\n00\n00\n00\n",
        },
    }
    return configs[request.param]


@pytest.mark.parametrize(
    "entity_config", ["shutters_with_pos", "shutters", "simple_shutters"], indirect=True
)
@pytest.mark.parametrize(
    ("gw_available", "device_available", "expected_state"),
    [
        (True, False, [STATE_UNAVAILABLE]),
        (False, True, [STATE_UNAVAILABLE]),
        (True, True, [STATE_OPEN, STATE_OPENING]),
    ],
)
async def test_cover_availability(
    hass: HomeAssistant,
    setup_entity,
    entity_config,
    gw_available,
    device_available,
    expected_state,
) -> None:
    """Test cover availability and state under different gateway and device availability conditions."""

    cover = await setup_entity(
        entity_config,
        status_value=entity_config["cover_open_value"],
        gw_available=gw_available,
        device_available=device_available,
    )

    assert cover is not None
    assert cover.state in expected_state


@pytest.mark.parametrize(
    "entity_config", ["shutters_with_pos", "simple_shutters", "shutters"], indirect=True
)
async def test_cover_open(
    hass: HomeAssistant, setup_entity, entity_config, mock_mqtt
) -> None:
    """Test cover open state."""
    cover = await setup_entity(
        entity_config, status_value=entity_config["cover_closed_value"]
    )

    assert cover is not None
    if entity_config["device_type"] == "simple_shutters":
        # simple_shutters does not have end states such as closed and open
        assert cover.state == STATE_CLOSING
    else:
        assert cover.state == STATE_CLOSED

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: get_entity_id(entity_config)},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]

        if entity_config["device_type"] == "shutters_with_pos":
            assert ha_value.shutters_with_pos[0].set_pos is False
            assert ha_value.shutters_with_pos[0].state == Shutter_state.Open
        elif entity_config["device_type"] == "shutters":
            assert ha_value.shutters[0].state == Shutter_state.Open
        elif entity_config["device_type"] == "simple_shutters":
            assert ha_value.simple_shutters[0].state == Shutter_state.Open


@pytest.mark.parametrize(
    "entity_config", ["shutters_with_pos", "simple_shutters", "shutters"], indirect=True
)
async def test_cover_close(
    hass: HomeAssistant, setup_entity, entity_config, mock_mqtt
) -> None:
    """Test cover close state."""
    cover = await setup_entity(
        entity_config, status_value=entity_config["cover_open_value"]
    )

    assert cover is not None
    if entity_config["device_type"] == "simple_shutters":
        # simple_shutters does not have end states such as closed and open
        assert cover.state == STATE_OPENING
    else:
        assert cover.state == STATE_OPEN

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: get_entity_id(entity_config)},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]

        if entity_config["device_type"] == "shutters_with_pos":
            assert ha_value.shutters_with_pos[0].set_pos is False
            assert ha_value.shutters_with_pos[0].state == Shutter_state.Closed
        elif entity_config["device_type"] == "shutters":
            assert ha_value.shutters[0].state == Shutter_state.Closed
        elif entity_config["device_type"] == "simple_shutters":
            assert ha_value.simple_shutters[0].state == Shutter_state.Closed


@pytest.mark.parametrize(
    "entity_config", ["shutters_with_pos", "simple_shutters", "shutters"], indirect=True
)
async def test_cover_stop_up(
    hass: HomeAssistant, setup_entity, entity_config, mock_mqtt
) -> None:
    """Test cover stop functionality."""
    cover = await setup_entity(
        entity_config, status_value=entity_config["cover_closed_value"]
    )

    assert cover is not None
    if entity_config["device_type"] == "simple_shutters":
        # simple_shutters does not have end states such as closed and open
        assert cover.state == STATE_CLOSING
    else:
        assert cover.state == STATE_CLOSED

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER,
            {ATTR_ENTITY_ID: get_entity_id(entity_config)},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]

        if entity_config["device_type"] == "shutters_with_pos":
            assert ha_value.shutters_with_pos[0].state == Shutter_state.Stop_up
        elif entity_config["device_type"] == "shutters":
            assert ha_value.shutters[0].state == Shutter_state.Stop_up
        elif entity_config["device_type"] == "simple_shutters":
            # !Note for testers: simple_shutters do not have an 'is_closed' state, so they always use Stop_down
            assert ha_value.simple_shutters[0].state == Shutter_state.Stop_down


@pytest.mark.parametrize(
    "entity_config", ["shutters_with_pos", "simple_shutters", "shutters"], indirect=True
)
async def test_cover_stop_down(
    hass: HomeAssistant, setup_entity, entity_config, mock_mqtt
) -> None:
    """Test cover stop functionality."""
    cover = await setup_entity(
        entity_config, status_value=entity_config["cover_open_value"]
    )

    assert cover is not None
    if entity_config["device_type"] == "simple_shutters":
        # simple_shutters does not have end states such as closed and open
        assert cover.state == STATE_OPENING
    else:
        assert cover.state == STATE_OPEN

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER,
            {ATTR_ENTITY_ID: get_entity_id(entity_config)},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]

        if entity_config["device_type"] == "shutters_with_pos":
            assert ha_value.shutters_with_pos[0].state == Shutter_state.Stop_down
        elif entity_config["device_type"] == "shutters":
            assert ha_value.shutters[0].state == Shutter_state.Stop_down
        elif entity_config["device_type"] == "simple_shutters":
            assert ha_value.simple_shutters[0].state == Shutter_state.Stop_down


@pytest.mark.parametrize("entity_config", ["shutters_with_pos"], indirect=True)
async def test_set_position(hass: HomeAssistant, setup_entity, entity_config) -> None:
    """Test set position method."""
    cover = await setup_entity(
        entity_config, status_value=entity_config["cover_open_half_value"]
    )

    assert cover is not None
    assert cover.state == STATE_OPEN
    assert round(cover.attributes["current_position"], 0) == 50.0

    with patch("inelsmqtt.devices.Device.set_ha_value") as mock_set_state:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {
                ATTR_ENTITY_ID: get_entity_id(entity_config),
                ATTR_POSITION: 75.0,
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once()

        ha_value = mock_set_state.call_args.args[0]
        assert ha_value.shutters_with_pos[0].set_pos is True
        assert ha_value.shutters_with_pos[0].position == 75


@pytest.mark.parametrize(
    ("entity_config", "value_key", "index"),
    [
        ("shutters", "cover_open_value", ""),
    ],
    indirect=["entity_config"],
)
async def test_cover_old_entity_and_device_removal(
    hass: HomeAssistant, mock_mqtt, entity_config, value_key, index
) -> None:
    """Test removal of old cover entity and device."""
    await old_entity_and_device_removal(
        hass, mock_mqtt, Platform.COVER, entity_config, value_key, index
    )

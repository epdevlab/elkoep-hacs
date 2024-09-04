"""iNELS sensor platform testing."""

import pytest

from homeassistant.const import STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant

from .common import MAC_ADDRESS, UNIQUE_ID, old_entity_and_device_removal

DT_12 = "12"
DT_30 = "30"
DT_102 = "102"
DT_156 = "156"


@pytest.fixture(
    params=[
        "temp_in",
    ]
)
def entity_config(request: pytest.FixtureRequest):
    """Fixture to provide parameterized entity configuration for sensor tests."""
    configs = {
        "temp_in": {
            "entity_type": "sensor",
            "device_type": "temp_in",
            "dev_type": DT_12,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_12}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_12}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_12}/{UNIQUE_ID}",
            "sensor_value": b"30\n00\n81\n00\n00\n",
            "expected_state": "24.0",
        },
        "humidity": {
            "entity_type": "sensor",
            "device_type": "humidity",
            "dev_type": DT_30,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_30}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_30}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_30}/{UNIQUE_ID}",
            "sensor_value": b"01\nD8\n09\n24\n00",
            "expected_state": "36",
        },
        "light_in": {
            "entity_type": "sensor",
            "device_type": "light_in",
            "dev_type": DT_102,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_102}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_102}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_102}/{UNIQUE_ID}",
            "sensor_value": b"00\n00\n0A\n1D\n00\n00\n00\n00\n00\n00\n04\n37\n7F\nFF\n16\n60\n06\n7B\n",
            "expected_state": "10.79",
        },
        "dewpoint": {
            "entity_type": "sensor",
            "device_type": "dewpoint",
            "dev_type": DT_102,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_102}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_102}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_102}/{UNIQUE_ID}",
            "sensor_value": b"00\n00\n0A\n1D\n00\n00\n00\n00\n00\n00\n04\n37\n7F\nFF\n16\n60\n06\n7B\n",
            "expected_state": "16.59",
        },
        "ains": {
            "entity_type": "sensor",
            "device_type": "ains",
            "dev_type": DT_156,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_156}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_156}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_156}/{UNIQUE_ID}",
            "sensor_value": b"00\n00\n32\n64\n00\n00\n32\n64\n00\n00\n32\n64\n00\n00\n32\n64\n00\n00\n32\n64\n00\n00\n32\n64\n00\n",
            "expected_state": "129.0",
        },
    }
    return configs[request.param]


@pytest.mark.parametrize(
    "entity_config", ["temp_in", "humidity", "light_in", "dewpoint"], indirect=True
)
@pytest.mark.parametrize(
    ("gw_available", "device_available", "expected_state"),
    [
        (True, False, STATE_UNAVAILABLE),
        (False, True, STATE_UNAVAILABLE),
        (True, True, "lookup"),
    ],
)
async def test_sensor_availability(
    hass: HomeAssistant,
    setup_entity,
    entity_config,
    gw_available,
    device_available,
    expected_state,
) -> None:
    """Test sensor availability and state under different gateway and device availability conditions."""

    sensor = await setup_entity(
        entity_config,
        status_value=entity_config["sensor_value"],
        gw_available=gw_available,
        device_available=device_available,
    )

    assert sensor is not None
    if expected_state == "lookup":
        assert sensor.state == entity_config["expected_state"]
        entity = hass.data["entity_components"]["sensor"].get_entity(sensor.entity_id)
        entity._callback()
        assert sensor.state == entity_config["expected_state"]
    else:
        assert sensor.state == expected_state


@pytest.mark.parametrize(
    "entity_config",
    [
        "ains",
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    ("gw_available", "device_available", "expected_state"),
    [
        (True, False, STATE_UNAVAILABLE),
        (False, True, STATE_UNAVAILABLE),
        (True, True, "lookup"),
    ],
)
async def test_indexed_sensor(
    hass: HomeAssistant,
    setup_entity,
    entity_config,
    gw_available,
    device_available,
    expected_state,
) -> None:
    """Test indexed sensor setup."""

    sensor = await setup_entity(
        entity_config,
        status_value=entity_config["sensor_value"],
        gw_available=gw_available,
        device_available=device_available,
        index="0",
    )

    assert sensor is not None
    if expected_state == "lookup":
        assert sensor.state == entity_config["expected_state"]
        entity = hass.data["entity_components"]["sensor"].get_entity(sensor.entity_id)
        entity._callback()
        assert sensor.state == entity_config["expected_state"]
    else:
        assert sensor.state == expected_state


@pytest.mark.parametrize(
    ("entity_config", "value_key", "index"),
    [
        ("humidity", "sensor_value", ""),
    ],
    indirect=["entity_config"],
)
async def test_sensor_old_entity_and_device_removal(
    hass: HomeAssistant, mock_mqtt, entity_config, value_key, index
) -> None:
    """Test removal of old sensor entity and device."""
    await old_entity_and_device_removal(
        hass, mock_mqtt, Platform.SENSOR, entity_config, value_key, index
    )

"""iNELS binary_sensor platform testing."""

import logging

import pytest

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant

from .common import MAC_ADDRESS, UNIQUE_ID, old_entity_and_device_removal

DT_15 = "15"
DT_115 = "115"


@pytest.fixture(
    params=[
        "low_battery",
        "flooded",
        "input",
    ]
)
def entity_config(request: pytest.FixtureRequest):
    """Fixture to provide parameterized entity configuration for binary_sensor tests."""
    configs = {
        "low_battery": {
            "entity_type": "binary_sensor",
            "device_type": "low_battery",
            "dev_type": DT_15,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_15}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_15}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_15}/{UNIQUE_ID}",
            "sensor_on_value": b"81\nFF\n00\n00\n00\n",
            "sensor_off_value": b"00\nFF\n00\n00\n00\n",
        },
        "flooded": {
            "entity_type": "binary_sensor",
            "device_type": "flooded",
            "dev_type": DT_15,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_15}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_15}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_15}/{UNIQUE_ID}",
            "sensor_on_value": b"81\nFF\n00\n00\n00\n",
            "sensor_off_value": b"00\nFF\n00\n00\n00\n",
        },
        "input": {
            "entity_type": "binary_sensor",
            "device_type": "input",
            "dev_type": DT_115,
            "unique_id": UNIQUE_ID,
            "gw_connected_topic": f"inels/connected/{MAC_ADDRESS}/gw",
            "connected_topic": f"inels/connected/{MAC_ADDRESS}/{DT_115}/{UNIQUE_ID}",
            "status_topic": f"inels/status/{MAC_ADDRESS}/{DT_115}/{UNIQUE_ID}",
            "base_topic": f"{MAC_ADDRESS}/{DT_115}/{UNIQUE_ID}",
            "sensor_on_value": b"05\n0A\n28\n",
            "sensor_off_value": b"00\n0A\n28\n",
            "alerts": {
                "alert": b"0A\n0A\n28\n",
                "tamper": b"0F\n0A\n28\n",
            },
        },
    }
    return configs[request.param]


@pytest.mark.parametrize(
    "entity_config",
    [
        "low_battery",
        "flooded",
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    ("gw_available", "device_available", "expected_state"),
    [
        (True, False, STATE_UNAVAILABLE),
        (False, True, STATE_UNAVAILABLE),
        (True, True, STATE_ON),
    ],
)
async def test_binary_sensor_availability(
    hass: HomeAssistant,
    setup_entity,
    entity_config,
    gw_available,
    device_available,
    expected_state,
) -> None:
    """Test binary sensor availability and state under different gateway and device availability conditions."""

    sensor = await setup_entity(
        entity_config,
        status_value=entity_config["sensor_on_value"],
        gw_available=gw_available,
        device_available=device_available,
    )

    assert sensor is not None
    assert sensor.state == expected_state


@pytest.mark.parametrize(
    ("entity_config", "expected_device_class"),
    [
        ("low_battery", BinarySensorDeviceClass.BATTERY),
        ("flooded", BinarySensorDeviceClass.MOISTURE),
    ],
    indirect=["entity_config"],
)
async def test_binary_sensor_device_class(
    hass: HomeAssistant, setup_entity, entity_config, expected_device_class
) -> None:
    """Test binary sensor device class."""

    sensor = await setup_entity(
        entity_config,
        status_value=entity_config["sensor_on_value"],
    )

    assert sensor is not None

    entity = hass.data["entity_components"]["binary_sensor"].get_entity(
        sensor.entity_id
    )
    assert entity.device_class == expected_device_class


@pytest.mark.parametrize(
    ("entity_config", "status_value", "expected_state"),
    [
        ("low_battery", "sensor_on_value", STATE_ON),
        ("low_battery", "sensor_off_value", STATE_OFF),
        ("flooded", "sensor_on_value", STATE_ON),
        ("flooded", "sensor_off_value", STATE_OFF),
    ],
    indirect=["entity_config"],
)
async def test_binary_sensor_states(
    hass: HomeAssistant, setup_entity, entity_config, status_value, expected_state
) -> None:
    """Test binary sensor in both on and off states."""

    sensor = await setup_entity(
        entity_config,
        status_value=entity_config[status_value],
    )

    assert sensor is not None
    assert sensor.state == expected_state


@pytest.mark.parametrize(
    "entity_config",
    [
        "input",
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    ("status_value", "expected_state", "index"),
    [
        ("sensor_on_value", STATE_ON, "0"),
        ("sensor_off_value", STATE_OFF, "1"),
    ],
)
async def test_indexed_binary_sensor_states(
    hass: HomeAssistant,
    setup_entity,
    entity_config,
    index,
    status_value,
    expected_state,
) -> None:
    """Test indexed binary sensor setup for both ON and OFF states."""

    sensor = await setup_entity(
        entity_config, status_value=entity_config[status_value], index=index
    )

    assert sensor is not None
    assert sensor.state == expected_state


@pytest.mark.parametrize(
    "entity_config",
    [
        "input",
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    ("alert_key", "expected_state", "index"),
    [
        ("alert", STATE_UNAVAILABLE, "0"),
        ("tamper", STATE_UNAVAILABLE, "1"),
    ],
)
async def test_indexed_binary_sensor_alerts(
    hass: HomeAssistant,
    setup_entity,
    entity_config,
    index,
    alert_key,
    expected_state,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test indexed binary sensor setup for both ON and OFF states."""

    caplog.set_level(logging.WARNING)

    sensor = await setup_entity(
        entity_config,
        status_value=entity_config["alerts"][alert_key],
        last_value=entity_config["sensor_on_value"],
        index=index,
    )

    assert sensor is not None
    assert sensor.state == expected_state
    assert any(alert_key.upper() in record.message for record in caplog.records)


@pytest.mark.parametrize(
    ("entity_config", "value_key", "index"),
    [
        ("low_battery", "sensor_on_value", ""),
    ],
    indirect=["entity_config"],
)
async def test_binary_sensor_old_entity_and_device_removal(
    hass: HomeAssistant, mock_mqtt, entity_config, value_key, index
) -> None:
    """Test removal of old binary_sensor entity and device."""
    await old_entity_and_device_removal(
        hass, mock_mqtt, Platform.BINARY_SENSOR, entity_config, value_key, index
    )

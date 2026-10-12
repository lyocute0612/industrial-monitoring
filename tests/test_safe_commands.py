
import pytest

from pc2_gateway.safe_commands import build_safe_command_result


def test_write_command_is_rejected():
    command = {
        "type": "command",
        "command_id": "test-001",
        "command": "write_register",
        "sensor_id": 1,
        "register": 0,
        "value": 0,
    }

    result = build_safe_command_result(command)

    assert result["type"] == "command_result"
    assert result["command_id"] == "test-001"
    assert result["command"] == "write_register"
    assert result["sensor_id"] == 1
    assert result["register"] == 0
    assert result["value"] == 0
    assert result["success"] is False
    assert "disabled" in result["message"]


@pytest.mark.parametrize(
    "message",
    [
        {},
        {"type": "heartbeat"},
        {"type": "sensor_data"},
        None,
        "invalid message",
        [],
    ],
)
def test_non_command_messages_are_ignored(message):
    assert build_safe_command_result(message) is None


@pytest.mark.parametrize("sensor_id", [1, 2, 3])
def test_all_sensors_have_hardware_writes_blocked(sensor_id):
    result = build_safe_command_result({
        "type": "command",
        "command_id": f"test-{sensor_id}",
        "command": "write_register",
        "sensor_id": sensor_id,
        "register": 0,
        "value": 0,
    })

    assert result["success"] is False
    assert result["sensor_id"] == sensor_id

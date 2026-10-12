
import json

import pytest

from pc1_server import tcp_server


class FakeSocket:
    def __init__(self):
        self.sent = []

    def sendall(self, data):
        self.sent.append(data)


def test_send_write_register_creates_valid_command(monkeypatch):
    fake_socket = FakeSocket()
    monkeypatch.setattr(tcp_server, "_client_socket", fake_socket)

    command_id = tcp_server.send_write_register(
        sensor_id=1,
        register=0,
        value=0,
    )

    assert isinstance(command_id, str)
    assert command_id

    assert len(fake_socket.sent) == 1

    message = json.loads(fake_socket.sent[0].decode("utf-8"))

    assert message == {
        "type": "command",
        "command_id": command_id,
        "command": "write_register",
        "sensor_id": 1,
        "register": 0,
        "value": 0,
    }


def test_send_command_when_pc2_disconnected(monkeypatch):
    monkeypatch.setattr(tcp_server, "_client_socket", None)

    with pytest.raises(RuntimeError, match="PC2 is not connected"):
        tcp_server.send_write_register(
            sensor_id=1,
            register=0,
            value=0,
        )


def test_store_and_get_command_result(monkeypatch):
    monkeypatch.setattr(tcp_server, "_command_results", {})
    monkeypatch.setattr(tcp_server, "_last_command_result", None)

    result = {
        "type": "command_result",
        "command_id": "test-command-001",
        "command": "write_register",
        "sensor_id": 1,
        "register": 0,
        "value": 0,
        "success": False,
        "message": "Hardware write commands are disabled during real-sensor testing",
    }

    tcp_server._store_command_result(result)

    stored = tcp_server.get_command_result("test-command-001")

    assert stored == result
    assert stored["success"] is False
    assert tcp_server.get_last_command_result() == result

    # Verify the returned copy cannot modify internal state.
    stored["success"] = True
    assert tcp_server.get_command_result("test-command-001")["success"] is False


@pytest.mark.parametrize(
    "sensor_id, register, value",
    [
        (0, 0, 0),
        (4, 0, 0),
        (1, -1, 0),
        (1, 65536, 0),
        (1, 0, -1),
        (1, 0, 65536),
    ],
)
def test_invalid_command_parameters(sensor_id, register, value):
    with pytest.raises(ValueError):
        tcp_server.send_write_register(
            sensor_id=sensor_id,
            register=register,
            value=value,
        )

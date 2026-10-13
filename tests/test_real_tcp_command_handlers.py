
import socket
import threading
import time

from pc1_server import tcp_server
from pc2_gateway.tcp_client import TcpClient
from pc2_gateway.safe_commands import build_safe_command_result


class FakeStore:
    def update(self, message):
        raise AssertionError("Command result must not enter sensor store")


class FakeDatabase:
    def insert_reading(self, reading):
        raise AssertionError("Command result must not enter SQLite")


def test_real_tcp_handlers_roundtrip(monkeypatch):
    monkeypatch.setattr(tcp_server, "_client_socket", None)
    monkeypatch.setattr(tcp_server, "_command_results", {})
    monkeypatch.setattr(tcp_server, "_last_command_result", None)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(3.0)

    host, port = listener.getsockname()
    pc2 = TcpClient(host=host, port=port)

    server_thread = None

    try:
        pc2.connect()

        accepted_socket, address = listener.accept()

        server_thread = threading.Thread(
            target=tcp_server.handle_client,
            args=(accepted_socket, address, FakeStore(), FakeDatabase()),
            daemon=True,
        )
        server_thread.start()

        def on_command(message):
            result = build_safe_command_result(message)
            if result is not None:
                pc2.send(result)

        pc2.start_receiver(on_command)

        deadline = time.monotonic() + 3.0
        while not tcp_server.is_pc2_connected():
            if time.monotonic() >= deadline:
                raise AssertionError("PC1 did not register PC2")
            time.sleep(0.01)

        command_id = tcp_server.send_write_register(
            sensor_id=1,
            register=0,
            value=0,
        )

        result = None
        deadline = time.monotonic() + 3.0

        while time.monotonic() < deadline:
            result = tcp_server.get_command_result(command_id)
            if result is not None:
                break
            time.sleep(0.01)

        assert result is not None, "PC1 did not receive command result"
        assert result["command_id"] == command_id
        assert result["type"] == "command_result"
        assert result["command"] == "write_register"
        assert result["sensor_id"] == 1
        assert result["success"] is False
        assert "disabled" in result["message"]

    finally:
        pc2.close()
        listener.close()
        if server_thread is not None:
            server_thread.join(timeout=4.0)

    assert server_thread is not None
    assert not server_thread.is_alive()


import json
import socket
import threading

from pc1_server import tcp_server
from pc2_gateway.safe_commands import build_safe_command_result


def test_tcp_command_roundtrip(monkeypatch):
    # Two connected real TCP sockets, isolated from PC1/PC2 hardware.
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(3.0)

    port = listener.getsockname()[1]
    received = {}
    errors = []

    def fake_pc2():
        try:
            with socket.create_connection(
                ("127.0.0.1", port), timeout=3.0
            ) as sock:
                sock.settimeout(3.0)
                buffer = b""

                while b"\n" not in buffer:
                    chunk = sock.recv(4096)
                    if not chunk:
                        raise ConnectionError("PC1 disconnected")
                    buffer += chunk

                command = json.loads(buffer.split(b"\n", 1)[0])
                received["command"] = command

                result = build_safe_command_result(command)
                sock.sendall(
                    (json.dumps(result) + "\n").encode("utf-8")
                )

        except Exception as error:
            errors.append(error)

    worker = threading.Thread(target=fake_pc2, daemon=True)
    worker.start()

    try:
        connection, _ = listener.accept()
        with connection:
            monkeypatch.setattr(
                tcp_server, "_client_socket", connection
            )
            monkeypatch.setattr(
                tcp_server, "_command_results", {}
            )
            monkeypatch.setattr(
                tcp_server, "_last_command_result", None
            )

            command_id = tcp_server.send_write_register(
                sensor_id=1,
                register=0,
                value=0,
            )

            connection.settimeout(3.0)
            buffer = b""

            while b"\n" not in buffer:
                chunk = connection.recv(4096)
                if not chunk:
                    raise ConnectionError("PC2 disconnected")
                buffer += chunk

            result = json.loads(buffer.split(b"\n", 1)[0])
            tcp_server._store_command_result(result)

            stored = tcp_server.get_command_result(command_id)

            assert stored is not None
            assert stored["command_id"] == command_id
            assert stored["type"] == "command_result"
            assert stored["success"] is False
            assert "disabled" in stored["message"]

            assert received["command"]["command"] == "write_register"
            assert received["command"]["sensor_id"] == 1

    finally:
        listener.close()
        worker.join(timeout=4.0)

    assert not worker.is_alive()
    assert not errors

import json
import socket
import threading
import time
import uuid
from copy import deepcopy

from pc1_server.data_store import (
    SensorDataStore,
)

from pc1_server.database import (
    SensorDatabase,
)


HOST = "192.168.50.10"
PORT = 65432


_client_socket = None
_client_lock = threading.Lock()
_send_lock = threading.Lock()

_command_results = {}
_last_command_result = None
_command_result_lock = threading.Lock()


def _set_connected_client(
    client_socket,
):
    global _client_socket

    with _client_lock:
        _client_socket = client_socket


def _clear_connected_client(
    client_socket,
):
    global _client_socket

    with _client_lock:
        if _client_socket is client_socket:
            _client_socket = None


def is_pc2_connected() -> bool:
    with _client_lock:
        return _client_socket is not None


def send_message_to_pc2(
    message: dict,
):
    with _client_lock:
        client_socket = _client_socket

    if client_socket is None:
        raise RuntimeError(
            "PC2 is not connected"
        )

    payload = (
        json.dumps(
            message,
            ensure_ascii=False,
        )
        + "\n"
    ).encode(
        "utf-8"
    )

    try:
        with _send_lock:
            client_socket.sendall(
                payload
            )

    except OSError as error:
        raise ConnectionError(
            "Failed to send message to PC2"
        ) from error


def send_write_register(
    sensor_id: int,
    register: int,
    value: int,
) -> str:
    if sensor_id not in (
        1,
        2,
        3,
    ):
        raise ValueError(
            f"Invalid sensor_id: {sensor_id}"
        )

    if not isinstance(
        register,
        int,
    ):
        raise ValueError(
            "register must be an integer"
        )

    if not isinstance(
        value,
        int,
    ):
        raise ValueError(
            "value must be an integer"
        )

    if not 0 <= register <= 0xFFFF:
        raise ValueError(
            "register must be between "
            "0 and 65535"
        )

    if not 0 <= value <= 0xFFFF:
        raise ValueError(
            "value must be between "
            "0 and 65535"
        )

    command_id = uuid.uuid4().hex

    command = {
        "type": "command",
        "command_id": command_id,
        "command": "write_register",
        "sensor_id": sensor_id,
        "register": register,
        "value": value,
    }

    send_message_to_pc2(
        command
    )

    return command_id


def _store_command_result(
    message: dict,
):
    global _last_command_result

    command_id = message.get(
        "command_id"
    )

    stored = deepcopy(
        message
    )

    with _command_result_lock:
        _last_command_result = stored

        if command_id:
            _command_results[
                command_id
            ] = stored


def get_command_result(
    command_id: str,
):
    with _command_result_lock:
        result = _command_results.get(
            command_id
        )

        if result is None:
            return None

        return deepcopy(
            result
        )


def get_last_command_result():
    with _command_result_lock:
        if _last_command_result is None:
            return None

        return deepcopy(
            _last_command_result
        )


def handle_client(
    client_socket: socket.socket,
    client_address,
    data_store: SensorDataStore,
    database: SensorDatabase,
):
    print(
        f"PC2 connected: "
        f"{client_address}"
    )

    _set_connected_client(
        client_socket
    )

    buffer = ""
    last_rx = time.monotonic()
    client_socket.settimeout(2.0)

    try:
        while True:
            try:
                data = client_socket.recv(4096)
            except socket.timeout:
                if time.monotonic() - last_rx > 15.0:
                    print("PC2 idle timeout; releasing TCP connection.")
                    break
                continue
            last_rx = time.monotonic()

            if not data:
                break

            buffer += data.decode(
                "utf-8"
            )

            while "\n" in buffer:
                line, buffer = buffer.split(
                    "\n",
                    1,
                )

                if not line.strip():
                    continue

                try:
                    message = json.loads(
                        line
                    )
                    if not isinstance(message, dict):
                        continue
                    if message.get("type") == "heartbeat":
                        with _send_lock:
                            client_socket.sendall(b'{"type":"heartbeat_ack"}\n')
                        continue

                    if (
                        message.get("type")
                        == "command_result"
                    ):
                        _store_command_result(
                            message
                        )

                        status = (
                            "SUCCESS"
                            if message.get(
                                "success"
                            )
                            else "FAILED"
                        )

                        print(
                            "Command result "
                            f"[{status}]: "
                            f"{message.get('message')}"
                        )

                        continue

                    stored_data = (
                        data_store.update(
                            message
                        )
                    )

                    database.insert_reading(
                        stored_data
                    )

                    print(
                        f"Received Sensor "
                        f"{stored_data['sensor_id']}"
                    )

                except (
                    json.JSONDecodeError,
                    ValueError,
                    TypeError,
                ) as error:
                    print(
                        f"Invalid message: "
                        f"{error}"
                    )

    except OSError as error:
        print(f"PC2 connection closed: {error}")
        print(
            "PC2 disconnected unexpectedly."
        )

    finally:
        _clear_connected_client(
            client_socket
        )

        client_socket.close()

        print(
            "PC2 disconnected."
        )


def run_server(
    data_store=None,
    database=None,
    host=HOST,
    port=PORT,
):
    if data_store is None:
        data_store = SensorDataStore()

    if database is None:
        database = SensorDatabase()

        database.initialize()

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1,
    )

    server_socket.bind(
        (
            host,
            port,
        )
    )

    server_socket.listen(
        1
    )

    print(
        "PC1 Industrial Server"
    )

    print(
        "---------------------"
    )

    print(
        f"Listening on "
        f"{host}:{port}"
    )

    print(
        "Waiting for PC2..."
    )

    try:
        while True:
            client_socket, client_address = (
                server_socket.accept()
            )

            handle_client(
                client_socket,
                client_address,
                data_store,
                database,
            )

    except KeyboardInterrupt:
        print()
        print(
            "PC1 server stopped."
        )

    finally:
        server_socket.close()


if __name__ == "__main__":
    run_server()

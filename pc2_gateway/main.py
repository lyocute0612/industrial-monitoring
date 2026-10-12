import threading
import time

from modbus.frame import (
    build_write_single_register_request,
    frame_to_hex,
)

from pc2_gateway.polling import (
    poll_once,
)

from transport.serial_transport import (
    SerialTransport,
)

from pc2_gateway.tcp_client import (
    TcpClient,
)

from pc2_gateway.gateway_state import (
    GatewayState,
)

from pc2_gateway.config import load_gateway_config

BAUD_CODE_TO_RATE = {
    1: 4800,
    2: 9600,
    3: 19200,
    4: 38400,
}


def print_sensor(
    data: dict,
):
    sensor_id = data["sensor_id"]

    print()
    print(
        f"Sensor {sensor_id}"
    )
    print(
        "-" * 30
    )

    print(
        f"Slave ID: "
        f"{data['slave_id']}"
    )

    print(
        f"TX: "
        f"{data['tx_frame']}"
    )

    print(
        f"RX: "
        f"{data['rx_frame']}"
    )

    if data["sensor_type"] == "shtc3":
        print(
            f"Humidity:    "
            f"{data['humidity']:.1f} %RH"
        )

        print(
            f"Temperature: "
            f"{data['temperature']:.1f} °C"
        )

    elif (
        data["sensor_type"]
        == "soil_7in1"
    ):
        print(
            f"Moisture:     "
            f"{data['moisture']:.1f} %"
        )

        print(
            f"Temperature:  "
            f"{data['temperature']:.1f} °C"
        )

        print(
            f"Conductivity: "
            f"{data['conductivity']} µS/cm"
        )

        print(
            f"pH:           "
            f"{data['ph']:.1f}"
        )

        print(
            f"Nitrogen:     "
            f"{data['nitrogen']} mg/kg"
        )

        print(
            f"Phosphate:    "
            f"{data['phosphate']} mg/kg"
        )

        print(
            f"Potassium:    "
            f"{data['potassium']} mg/kg"
        )

        print(
            f"Salinity:     "
            f"{data['salinity']}"
        )

        print(
            f"TDS:          "
            f"{data['tds']}"
        )


def _validate_new_slave_id(
    state: GatewayState,
    sensor_id: int,
    new_slave_id: int,
):
    for other_sensor_id, config in (
        state.get_all().items()
    ):
        if (
            other_sensor_id != sensor_id
            and config["slave_id"]
            == new_slave_id
        ):
            raise ValueError(
                f"Slave ID {new_slave_id} "
                f"is already used by "
                f"Sensor {other_sensor_id}"
            )


def handle_command(
    message: dict,
    *,
    transport,
    state: GatewayState,
    tcp_client: TcpClient,
    transport_lock: threading.Lock,
):
    command_id = message.get(
        "command_id"
    )

    command = message.get(
        "command"
    )

    sensor_id = message.get(
        "sensor_id"
    )

    register = message.get(
        "register"
    )

    value = message.get(
        "value"
    )

    result = {
        "type": "command_result",
        "command_id": command_id,
        "command": command,
        "sensor_id": sensor_id,
        "register": register,
        "value": value,
        "success": False,
    }

    try:
        if message.get("type") != "command":
            raise ValueError(
                "Expected message type 'command'"
            )

        if command != "write_register":
            raise ValueError(
                f"Unsupported command: {command}"
            )

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

        if register not in (
            0x07D0,
            0x07D1,
        ):
            raise ValueError(
                f"Unsupported writable register: "
                f"0x{register:04X}"
            )

        if register == 0x07D0:
            if not 1 <= value <= 247:
                raise ValueError(
                    "Slave ID must be "
                    "between 1 and 247"
                )

            _validate_new_slave_id(
                state,
                sensor_id,
                value,
            )

        if (
            register == 0x07D1
            and value not in BAUD_CODE_TO_RATE
        ):
            raise ValueError(
                "Baudrate code must be "
                "1, 2, 3, or 4"
            )

        config = state.get_sensor(
            sensor_id
        )

        current_slave_id = (
            config["slave_id"]
        )

        request = (
            build_write_single_register_request(
                slave_id=current_slave_id,
                register=register,
                value=value,
            )
        )

        with transport_lock:
            response = transport.exchange(
                request
            )

        if response != request:
            raise ValueError(
                "FC06 response does not "
                "match request echo"
            )

        if register == 0x07D0:
            state.set_pending_slave_id(
                sensor_id=sensor_id,
                slave_id=value,
            )

            state.apply_pending(
                sensor_id=sensor_id
            )

        elif register == 0x07D1:
            state.set_pending_baudrate(
                sensor_id=sensor_id,
                baudrate=(
                    BAUD_CODE_TO_RATE[
                        value
                    ]
                ),
            )

            state.apply_pending(
                sensor_id=sensor_id
            )

        updated_config = (
            state.get_sensor(
                sensor_id
            )
        )

        result.update(
            {
                "success": True,
                "tx_frame": frame_to_hex(
                    request
                ),
                "rx_frame": frame_to_hex(
                    response
                ),
                "slave_id": (
                    updated_config[
                        "slave_id"
                    ]
                ),
                "baudrate": (
                    updated_config[
                        "baudrate"
                    ]
                ),
                "message": (
                    "Write register successful"
                ),
            }
        )

        print()
        print(
            "FC06 command completed:"
        )
        print(
            f"Sensor {sensor_id}, "
            f"register=0x{register:04X}, "
            f"value={value}"
        )
        print(
            f"TX: {result['tx_frame']}"
        )
        print(
            f"RX: {result['rx_frame']}"
        )

    except Exception as error:
        result["message"] = str(
            error
        )

        print()
        print(
            "FC06 command failed: "
            f"{error}"
        )

    try:
        tcp_client.send(
            result
        )

    except Exception as error:
        print(
            "Could not send command "
            f"result to PC1: {error}"
        )


def main():
    config = load_gateway_config()

    shct3_port = config["shct3_port"]
    soil_port = config["soil_port"]
    baudrate = config["baudrate"]
    reconnect_interval = config["reconnect_interval"]

    print("PC2 Industrial Gateway")
    print("----------------------")
    print(f"Mode: REAL RS485 - {shct3_port} + {soil_port} (auto-reconnect)")
    print("Press Ctrl+C to stop.")

    state = GatewayState()
    transport_lock = threading.Lock()
    transport = None
    soil_transport = None
    retry_after = {
    	shct3_port: 0.0,
    	soil_port: 0.0,
    }
    

    tcp_client = TcpClient(
    	host=config["tcp_host"],
    	port=config["tcp_port"],
    )

    def safe_command_handler(message):
        # FC06 remains disabled until actual hardware registers are verified.
        if not isinstance(message, dict) or message.get("type") != "command":
            return
        result = {
            "type": "command_result",
            "command_id": message.get("command_id"),
            "command": message.get("command"),
            "sensor_id": message.get("sensor_id"),
            "register": message.get("register"),
            "value": message.get("value"),
            "success": False,
            "message": "Hardware write commands are disabled during real-sensor testing",
        }
        print("Hardware write command blocked:", message.get("command"))
        try:
            tcp_client.send(result)
        except Exception as error:
            print(f"Could not send command result to PC1: {error}")

    def try_open(port):
        if time.monotonic() < retry_after[port]:
            return None
        try:
            connection = SerialTransport(port=port, baudrate=baudrate, timeout=2.0)
            print(f"{port} connected.")
            return connection
        except Exception as error:
            print(f"WARNING: Could not open {port}: {type(error).__name__}: {error}")
            retry_after[port] = time.monotonic() + reconnect_interval
            return None

    def disconnect(port, connection):
        print(f"WARNING: Lost {port}; will try reopening it.")
        try:
            connection.close()
        except Exception as error:
            print(f"WARNING: Error closing {port}: {error}")
        retry_after[port] = time.monotonic() + reconnect_interval

    try:
        # PC1 may start receiving even when one USB device is absent.
        # Keep reading sensors even if PC1 is offline at startup.
        print("Connecting to PC1 (automatic retry enabled)...")

        while True:
            tcp_client.maintain(safe_command_handler)
            with transport_lock:
                if transport is None:
                    transport = try_open(shct3_port)
                if soil_transport is None:
                    soil_transport = try_open(soil_port)

                sensor_errors = []
                # Without SHCT3 transport, skip sensors 1 and 2; Soil can still work.
                if transport is not None:
                    results = poll_once(
                        transport,
                        state,
                        soil_transport=soil_transport,
                        on_error=lambda sensor_id, error: sensor_errors.append(
                            (sensor_id, error)
                        ),
                    )
                elif soil_transport is not None:
                    # Read Soil independently while SHCT3 transport is unavailable.
                    from pc2_gateway.polling import read_soil_sensor
                    results = []
                    try:
                        cfg = state.get_sensor(3)
                        results.append(read_soil_sensor(soil_transport, cfg["slave_id"]))
                    except Exception as error:
                        sensor_errors.append((3, error))
                else:
                    results = []

                # Broken USB handles cannot recover with exchange() retries.
                # Recreate the connection, not just the Modbus request.
                serial_error_ids = {
                    sensor_id
                    for sensor_id, error in sensor_errors
                    if isinstance(error, (OSError,)) or
                    type(error).__name__ in ("SerialException", "SerialTimeoutException")
                }
                if transport is not None and serial_error_ids.intersection((1, 2)):
                    disconnect(shct3_port, transport)
                    transport = None
                if soil_transport is not None and 3 in serial_error_ids:
                    disconnect(soil_port, soil_transport)
                    soil_transport = None

            print("\n" + "=" * 50)
            print("New polling cycle")
            for sensor_id, error in sensor_errors:
                print(
                    f"WARNING: Sensor {sensor_id} unavailable: "
                    f"{type(error).__name__}: {error}"
                )
            if transport is None:
                print(f"WARNING: {shct3_port} offline (Sensor 1 and Sensor 2).")
            if soil_transport is None:
                print(f"WARNING: {soil_port} offline (Sensor 3).")
            if not results:
                print("WARNING: No sensor readings in this cycle; will retry.")

            for sensor_data in results:
                sensor_id = sensor_data["sensor_id"]
                gateway_config = state.get_sensor(sensor_id)
                sensor_data["baudrate"] = gateway_config["baudrate"]
                print_sensor(sensor_data)
                if tcp_client.socket is not None:
                    try:
                        tcp_client.send(sensor_data)
                    except ConnectionError as error:
                        print(f"WARNING: TCP unavailable; current reading skipped: {error}")
                else:
                    print("WARNING: PC1 offline; current reading not sent.")
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\nGateway stopped.")
    finally:
        tcp_client.close()
        if transport is not None:
            transport.close()
            print(f"{shct3_port} closed.")
        if soil_transport is not None:
            soil_transport.close()
            print(f"{soil_port} closed.")


if __name__ == "__main__":
    main()

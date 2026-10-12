from modbus.crc16 import append_crc


class SensorSimulator:
    """
    Temporary simulator for the three Modbus sensors.

    Sensor 1 -> default Slave ID 3
    Sensor 2 -> default Slave ID 2
    Sensor 3 -> default Slave ID 1

    Supported Modbus functions:
        0x03 - Read Holding Registers
        0x06 - Write Single Register
    """

    SLAVE_ID_REGISTER = 0x07D0
    BAUDRATE_REGISTER = 0x07D1

    def __init__(self):
        self.sensor_config = {
            1: {
                "slave_id": 3,
                "baudrate": 9600,
            },
            2: {
                "slave_id": 2,
                "baudrate": 9600,
            },
            3: {
                "slave_id": 1,
                "baudrate": 9600,
            },
        }

        self.baud_map = {
            1: 4800,
            2: 9600,
            3: 19200,
            4: 38400,
        }

    def _find_sensor_id_by_slave_id(
        self,
        slave_id: int,
    ):
        for sensor_id, config in self.sensor_config.items():
            if config["slave_id"] == slave_id:
                return sensor_id

        return None

    @staticmethod
    def _build_read_response(
        slave_id: int,
        registers: list[int],
    ) -> bytes:
        frame = bytearray(
            [
                slave_id,
                0x03,
                len(registers) * 2,
            ]
        )

        for register in registers:
            frame.extend(
                register.to_bytes(
                    2,
                    byteorder="big",
                )
            )

        return append_crc(
            bytes(frame)
        )

    def _handle_read_holding_registers(
        self,
        request: bytes,
    ) -> bytes:
        slave_id = request[0]

        start_register = int.from_bytes(
            request[2:4],
            byteorder="big",
        )

        quantity = int.from_bytes(
            request[4:6],
            byteorder="big",
        )

        if start_register != 0:
            raise ValueError(
                "Simulator only supports start register 0"
            )

        sensor_id = self._find_sensor_id_by_slave_id(
            slave_id
        )

        if sensor_id is None:
            raise ValueError(
                f"No simulated sensor with slave ID {slave_id}"
            )

        # Sensor 1 - SHTC3
        if sensor_id == 1 and quantity == 2:
            return self._build_read_response(
                slave_id=slave_id,
                registers=[
                    0x032F,  # Humidity = 81.5 %RH
                    0x00D8,  # Temperature = 21.6 C
                ],
            )

        # Sensor 2 - SHTC3
        if sensor_id == 2 and quantity == 2:
            return self._build_read_response(
                slave_id=slave_id,
                registers=[
                    0x02F3,  # Humidity = 75.5 %RH
                    0x00E5,  # Temperature = 22.9 C
                ],
            )

        # Sensor 3 - Soil 7-in-1
        if sensor_id == 3 and quantity == 9:
            return self._build_read_response(
                slave_id=slave_id,
                registers=[
                    0x0000,  # Moisture
                    0x00F3,  # Temperature = 24.3 C
                    0x0000,  # Conductivity
                    0x0046,  # pH = 7.0
                    0x0000,  # Nitrogen
                    0x0000,  # Phosphate
                    0x0000,  # Potassium
                    0x0000,  # Salinity
                    0x0000,  # TDS
                ],
            )

        raise ValueError(
            f"Unsupported FC03 request: "
            f"sensor_id={sensor_id}, "
            f"slave_id={slave_id}, "
            f"quantity={quantity}"
        )

    def _handle_write_single_register(
        self,
        request: bytes,
    ) -> bytes:
        slave_id = request[0]

        register = int.from_bytes(
            request[2:4],
            byteorder="big",
        )

        value = int.from_bytes(
            request[4:6],
            byteorder="big",
        )

        sensor_id = self._find_sensor_id_by_slave_id(
            slave_id
        )

        if sensor_id is None:
            raise ValueError(
                f"No simulated sensor with slave ID {slave_id}"
            )

        config = self.sensor_config[
            sensor_id
        ]

        if register == self.SLAVE_ID_REGISTER:
            if not 1 <= value <= 247:
                raise ValueError(
                    "Invalid slave ID"
                )

            config["slave_id"] = value

        elif register == self.BAUDRATE_REGISTER:
            if value not in self.baud_map:
                raise ValueError(
                    "Unsupported baudrate code"
                )

            config["baudrate"] = (
                self.baud_map[value]
            )

        else:
            raise ValueError(
                f"Unsupported writable register: "
                f"0x{register:04X}"
            )

        # A successful Modbus FC06 response echoes the request.
        return request

    def exchange(
        self,
        request: bytes,
    ) -> bytes:
        if len(request) != 8:
            raise ValueError(
                "Expected 8-byte Modbus RTU request"
            )

        function_code = request[1]

        if function_code == 0x03:
            return (
                self._handle_read_holding_registers(
                    request
                )
            )

        if function_code == 0x06:
            return (
                self._handle_write_single_register(
                    request
                )
            )

        raise ValueError(
            f"Unsupported function code: "
            f"0x{function_code:02X}"
        )

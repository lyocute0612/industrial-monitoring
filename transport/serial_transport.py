
import serial


class SerialTransport:
    def __init__(
        self,
        port="COM6",
        baudrate=9600,
        timeout=2.0,
    ):
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
            write_timeout=timeout,
        )

    def exchange(self, request: bytes) -> bytes:
        if len(request) < 2:
            raise ValueError("Invalid Modbus request")

        function_code = request[1]

        self.serial.reset_input_buffer()
        self.serial.write(request)
        self.serial.flush()

        # FC03: response has variable length.
        if function_code == 0x03:
            header = self.serial.read(3)

            if len(header) != 3:
                raise TimeoutError(
                    "No complete Modbus response header"
                )

            if header[1] & 0x80:
                remaining_length = 2
            else:
                remaining_length = header[2] + 2

            payload = self.serial.read(
                remaining_length
            )

            if len(payload) != remaining_length:
                raise TimeoutError(
                    "Incomplete Modbus response"
                )

            return header + payload

        # FC06: response echoes the 8-byte request.
        if function_code == 0x06:
            response = self.serial.read(8)

            if len(response) != 8:
                raise TimeoutError(
                    "Incomplete FC06 response"
                )

            return response

        raise ValueError(
            f"Unsupported function code: {function_code}"
        )

    def close(self):
        if self.serial.is_open:
            self.serial.close()

from dataclasses import dataclass

from modbus.crc16 import validate_crc


class ModbusError(Exception):
    pass


class CRCError(ModbusError):
    pass


class InvalidFrameError(ModbusError):
    pass


class ModbusExceptionResponse(ModbusError):
    def __init__(
        self,
        slave_id: int,
        function_code: int,
        exception_code: int,
    ):
        self.slave_id = slave_id
        self.function_code = function_code
        self.exception_code = exception_code

        super().__init__(
            f"Modbus exception: "
            f"slave={slave_id}, "
            f"function=0x{function_code:02X}, "
            f"exception=0x{exception_code:02X}"
        )


@dataclass
class ReadHoldingRegistersResponse:
    slave_id: int
    function_code: int
    registers: list[int]
    raw_frame: bytes


def parse_read_holding_registers_response(
    frame: bytes,
) -> ReadHoldingRegistersResponse:

    if len(frame) < 5:
        raise InvalidFrameError(
            "Frame is too short"
        )

    if not validate_crc(frame):
        raise CRCError(
            "Invalid Modbus CRC"
        )

    slave_id = frame[0]
    function_code = frame[1]

    # Modbus exception response
    if function_code & 0x80:
        if len(frame) != 5:
            raise InvalidFrameError(
                "Invalid exception response length"
            )

        exception_code = frame[2]

        raise ModbusExceptionResponse(
            slave_id=slave_id,
            function_code=function_code,
            exception_code=exception_code,
        )

    if function_code != 0x03:
        raise InvalidFrameError(
            f"Expected function code 0x03, "
            f"received 0x{function_code:02X}"
        )

    byte_count = frame[2]

    expected_length = 3 + byte_count + 2

    if len(frame) != expected_length:
        raise InvalidFrameError(
            f"Invalid frame length: "
            f"expected {expected_length}, "
            f"received {len(frame)}"
        )

    if byte_count % 2 != 0:
        raise InvalidFrameError(
            "Register data byte count must be even"
        )

    data = frame[3:3 + byte_count]

    registers = []

    for i in range(0, len(data), 2):
        high = data[i]
        low = data[i + 1]

        value = (high << 8) | low

        registers.append(value)

    return ReadHoldingRegistersResponse(
        slave_id=slave_id,
        function_code=function_code,
        registers=registers,
        raw_frame=frame,
    )
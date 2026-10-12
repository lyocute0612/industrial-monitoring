from modbus.crc16 import append_crc


READ_HOLDING_REGISTERS = 0x03
WRITE_SINGLE_REGISTER = 0x06


def build_read_holding_registers_request(
    slave_id: int,
    start_register: int,
    quantity: int,
) -> bytes:
    """
    Build a Modbus RTU Function Code 03 request.

    Frame before CRC:
        Slave ID        1 byte
        Function Code   1 byte
        Start Address   2 bytes
        Quantity        2 bytes

    CRC is appended in low-byte, high-byte order.
    """

    if not 1 <= slave_id <= 247:
        raise ValueError("slave_id must be between 1 and 247")

    if not 0 <= start_register <= 0xFFFF:
        raise ValueError(
            "start_register must be between 0 and 65535"
        )

    if not 1 <= quantity <= 125:
        raise ValueError(
            "quantity must be between 1 and 125"
        )

    frame = bytes(
        [
            slave_id,
            READ_HOLDING_REGISTERS,
            (start_register >> 8) & 0xFF,
            start_register & 0xFF,
            (quantity >> 8) & 0xFF,
            quantity & 0xFF,
        ]
    )

    return append_crc(frame)

def build_write_single_register_request(
    slave_id: int,
    register: int,
    value: int,
) -> bytes:
    """
    Build a Modbus RTU Function Code 06 request.

    Frame before CRC:
        Slave ID        1 byte
        Function Code   1 byte
        Register        2 bytes
        Value           2 bytes

    CRC is appended in low-byte, high-byte order.
    """

    if not 1 <= slave_id <= 247:
        raise ValueError(
            "slave_id must be between 1 and 247"
        )

    if not 0 <= register <= 0xFFFF:
        raise ValueError(
            "register must be between 0 and 65535"
        )

    if not 0 <= value <= 0xFFFF:
        raise ValueError(
            "value must be between 0 and 65535"
        )

    frame = bytes(
        [
            slave_id,
            WRITE_SINGLE_REGISTER,
            (register >> 8) & 0xFF,
            register & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        ]
    )

    return append_crc(frame)

def frame_to_hex(frame: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in frame)
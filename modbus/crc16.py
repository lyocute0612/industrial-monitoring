def calculate_crc(data: bytes) -> int:
    """
    Calculate Modbus RTU CRC16.

    Returns a 16-bit integer.
    Modbus sends CRC low byte first, then high byte.
    """

    crc = 0xFFFF

    for byte in data:
        crc ^= byte

        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1

    return crc


def crc_bytes(data: bytes) -> bytes:
    """
    Return CRC in Modbus wire order:
    LOW byte first, HIGH byte second.
    """

    crc = calculate_crc(data)

    low = crc & 0xFF
    high = (crc >> 8) & 0xFF

    return bytes([low, high])


def append_crc(data: bytes) -> bytes:
    return data + crc_bytes(data)


def validate_crc(frame: bytes) -> bool:
    if len(frame) < 3:
        return False

    data = frame[:-2]
    received_crc = frame[-2:]

    calculated_crc = crc_bytes(data)

    return received_crc == calculated_crc
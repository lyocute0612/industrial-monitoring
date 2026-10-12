from modbus.crc16 import (
    calculate_crc,
    crc_bytes,
    append_crc,
    validate_crc,
)


def test_sensor_1_request_crc():
    data = bytes.fromhex(
        "03 03 00 00 00 02"
    )

    crc = crc_bytes(data)

    assert crc == bytes.fromhex("C5 E9")


def test_append_crc():
    data = bytes.fromhex(
        "03 03 00 00 00 02"
    )

    frame = append_crc(data)

    assert frame == bytes.fromhex(
        "03 03 00 00 00 02 C5 E9"
    )


def test_validate_valid_frame():
    frame = bytes.fromhex(
        "03 03 00 00 00 02 C5 E9"
    )

    assert validate_crc(frame) is True


def test_validate_invalid_frame():
    frame = bytes.fromhex(
        "03 03 00 00 00 02 C5 EA"
    )

    assert validate_crc(frame) is False
import pytest

from modbus.parser import (
    CRCError,
    parse_read_holding_registers_response,
)


def test_parse_sensor_1_response():
    frame = bytes.fromhex(
        "03 03 04 03 2F 00 D8 E8 24"
    )

    response = (
        parse_read_holding_registers_response(
            frame
        )
    )

    assert response.slave_id == 3
    assert response.function_code == 3
    assert response.registers == [
        815,
        216,
    ]


def test_parse_sensor_2_response():
    frame = bytes.fromhex(
        "02 03 04 03 19 00 E3 59 39"
    )

    response = (
        parse_read_holding_registers_response(
            frame
        )
    )

    assert response.slave_id == 2

    assert response.registers == [
        793,
        227,
    ]


def test_invalid_crc():
    frame = bytes.fromhex(
        "03 03 04 03 2F 00 D8 E8 25"
    )

    with pytest.raises(CRCError):
        parse_read_holding_registers_response(
            frame
        )


def test_parse_soil_sensor_response():
    frame = bytes.fromhex(
        "01 03 12 "
        "00 00 "
        "00 F3 "
        "00 00 "
        "00 46 "
        "00 00 "
        "00 00 "
        "00 00 "
        "00 00 "
        "00 00 "
        "0A 8E"
    )

    response = parse_read_holding_registers_response(frame)

    assert response.slave_id == 1
    assert response.function_code == 0x03

    assert response.registers == [
        0,
        243,
        0,
        70,
        0,
        0,
        0,
        0,
        0,
    ]
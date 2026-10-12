import pytest

from modbus.frame import (
    build_read_holding_registers_request,
    build_write_single_register_request,
)


def test_sensor_1_read_request():
    frame = build_read_holding_registers_request(
        slave_id=3,
        start_register=0,
        quantity=2,
    )

    assert frame == bytes.fromhex(
        "03 03 00 00 00 02 C5 E9"
    )


def test_sensor_2_read_request():
    frame = build_read_holding_registers_request(
        slave_id=2,
        start_register=0,
        quantity=2,
    )

    assert frame == bytes.fromhex(
        "02 03 00 00 00 02 C4 38"
    )


def test_soil_sensor_read_request():
    frame = build_read_holding_registers_request(
        slave_id=1,
        start_register=0,
        quantity=9,
    )

    assert frame == bytes.fromhex(
        "01 03 00 00 00 09 85 CC"
    )


def test_invalid_slave_id():
    with pytest.raises(ValueError):
        build_read_holding_registers_request(
            slave_id=0,
            start_register=0,
            quantity=2,
        )


def test_invalid_quantity():
    with pytest.raises(ValueError):
        build_read_holding_registers_request(
            slave_id=3,
            start_register=0,
            quantity=0,
        )

def test_write_slave_id_request():
    frame = (
        build_write_single_register_request(
            slave_id=3,
            register=0x07D0,
            value=4,
        )
    )

    assert frame == bytes.fromhex(
        "03 06 07 D0 00 04 89 66"
    )


def test_write_baudrate_request():
    frame = (
        build_write_single_register_request(
            slave_id=3,
            register=0x07D1,
            value=2,
        )
    )

    assert frame == bytes.fromhex(
        "03 06 07 D1 00 02 58 A4"
    )
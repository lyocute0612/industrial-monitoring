from sensors.shtc3 import (
    decode_shtc3_registers,
)


def test_sensor_1_values():
    reading = decode_shtc3_registers(
        [815, 216]
    )

    assert reading.humidity == 81.5
    assert reading.temperature == 21.6


def test_sensor_2_values():
    reading = decode_shtc3_registers(
        [793, 227]
    )

    assert reading.humidity == 79.3
    assert reading.temperature == 22.7
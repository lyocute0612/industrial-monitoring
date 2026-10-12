from modbus.frame import (
    build_read_holding_registers_request,
)

from modbus.parser import (
    parse_read_holding_registers_response,
)

from sensors.shtc3 import (
    decode_shtc3_registers,
)

from sensors.soil_7in1 import (
    decode_soil_7in1_registers,
)

from simulator.sensor_simulator import (
    SensorSimulator,
)

from modbus.frame import (
    build_read_holding_registers_request,
    build_write_single_register_request,
)

def test_simulator_write_single_register_echo():
    simulator = SensorSimulator()

    request = (
        build_write_single_register_request(
            slave_id=3,
            register=0x07D0,
            value=4,
        )
    )

    response = simulator.exchange(
        request
    )

    assert response == request

def test_simulator_changes_slave_id():
    simulator = SensorSimulator()

    request = (
        build_write_single_register_request(
            slave_id=3,
            register=0x07D0,
            value=4,
        )
    )

    simulator.exchange(
        request
    )

    assert (
        simulator.sensor_config[1]["slave_id"]
        == 4
    )

def test_simulator_changes_baudrate():
    simulator = SensorSimulator()

    request = (
        build_write_single_register_request(
            slave_id=3,
            register=0x07D1,
            value=3,
        )
    )

    response = simulator.exchange(
        request
    )

    assert response == request

    assert (
        simulator.sensor_config[1]["baudrate"]
        == 19200
    )

def test_simulator_sensor_1():
    simulator = SensorSimulator()

    request = (
        build_read_holding_registers_request(
            slave_id=3,
            start_register=0,
            quantity=2,
        )
    )

    response_frame = simulator.exchange(
        request
    )

    response = (
        parse_read_holding_registers_response(
            response_frame
        )
    )

    reading = decode_shtc3_registers(
        response.registers
    )

    assert reading.humidity == 81.5
    assert reading.temperature == 21.6


def test_simulator_sensor_2():
    simulator = SensorSimulator()

    request = (
        build_read_holding_registers_request(
            slave_id=2,
            start_register=0,
            quantity=2,
        )
    )

    response_frame = simulator.exchange(
        request
    )

    response = (
        parse_read_holding_registers_response(
            response_frame
        )
    )

    reading = decode_shtc3_registers(
        response.registers
    )

    assert reading.humidity == 75.5
    assert reading.temperature == 22.9


def test_simulator_soil_sensor():
    simulator = SensorSimulator()

    request = (
        build_read_holding_registers_request(
            slave_id=1,
            start_register=0,
            quantity=9,
        )
    )

    response_frame = simulator.exchange(
        request
    )

    response = (
        parse_read_holding_registers_response(
            response_frame
        )
    )

    reading = decode_soil_7in1_registers(
        response.registers
    )

    assert reading.moisture == 0.0
    assert reading.temperature == 24.3
    assert reading.conductivity == 0
    assert reading.ph == 7.0
    assert reading.nitrogen == 0
    assert reading.phosphate == 0
    assert reading.potassium == 0
    assert reading.salinity == 0
    assert reading.tds == 0
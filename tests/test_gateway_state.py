from pc2_gateway.gateway_state import (
    GatewayState,
)


def test_initial_sensor_config():
    state = GatewayState()

    sensor_1 = state.get_sensor(1)

    assert sensor_1["slave_id"] == 3
    assert sensor_1["baudrate"] == 9600

    assert (
        sensor_1["pending_slave_id"]
        == 3
    )

    assert (
        sensor_1["pending_baudrate"]
        == 9600
    )


def test_pending_slave_id():
    state = GatewayState()

    state.set_pending_slave_id(
        sensor_id=1,
        slave_id=4,
    )

    sensor = state.get_sensor(1)

    assert sensor["slave_id"] == 3

    assert (
        sensor["pending_slave_id"]
        == 4
    )


def test_apply_pending_slave_id():
    state = GatewayState()

    state.set_pending_slave_id(
        sensor_id=1,
        slave_id=4,
    )

    state.apply_pending(
        sensor_id=1
    )

    sensor = state.get_sensor(1)

    assert sensor["slave_id"] == 4

    assert (
        sensor["pending_slave_id"]
        == 4
    )


def test_pending_baudrate():
    state = GatewayState()

    state.set_pending_baudrate(
        sensor_id=1,
        baudrate=19200,
    )

    sensor = state.get_sensor(1)

    assert sensor["baudrate"] == 9600

    assert (
        sensor["pending_baudrate"]
        == 19200
    )
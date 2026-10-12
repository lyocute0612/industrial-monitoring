from pc2_gateway.polling import (
    poll_once,
)

from simulator.sensor_simulator import (
    SensorSimulator,
)

from pc2_gateway.gateway_state import (
    GatewayState,
)

from pc2_gateway.gateway_state import GatewayState

def test_poll_once_returns_three_sensors():
    simulator = SensorSimulator()
    state = GatewayState()

    results = poll_once(
        simulator,
        state,
	soil_transport=simulator,
    )

    assert len(results) == 3

def test_poll_sensor_1_values():
    simulator = SensorSimulator()

    state = GatewayState()

    results = poll_once(
        simulator,
        state,
    )

    sensor_1 = results[0]

    assert sensor_1["humidity"] == 81.5
    assert sensor_1["temperature"] == 21.6


def test_poll_sensor_2_values():
    simulator = SensorSimulator()
    state = GatewayState()

    results = poll_once(
        simulator,
        state,
    )

    sensor_2 = results[1]

    assert sensor_2["sensor_id"] == 2
    assert sensor_2["slave_id"] == 2
    assert sensor_2["humidity"] == 75.5
    assert sensor_2["temperature"] == 22.9


def test_poll_soil_values():
    simulator = SensorSimulator()
    state = GatewayState()

    results = poll_once(
        simulator,
        state,
	soil_transport=simulator,
    )

    soil = results[2]

    assert soil["sensor_id"] == 3
    assert soil["slave_id"] == 1
    assert soil["moisture"] == 0.0
    assert soil["temperature"] == 24.3
    assert soil["conductivity"] == 0
    assert soil["ph"] == 7.0
    assert soil["nitrogen"] == 0
    assert soil["phosphate"] == 0
    assert soil["potassium"] == 0
    assert soil["salinity"] == 0
    assert soil["tds"] == 0
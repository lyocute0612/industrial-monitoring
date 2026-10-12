import time

from modbus.frame import (
    build_read_holding_registers_request,
    frame_to_hex,
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

from pc2_gateway.gateway_state import GatewayState

def read_shtc3_sensor(
    transport,
    sensor_id: int,
    slave_id: int,
):
    request = (
        build_read_holding_registers_request(
            slave_id=slave_id,
            start_register=0,
            quantity=2,
        )
    )

    response_frame = transport.exchange(
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

    return {
        "sensor_id": sensor_id,
        "slave_id": slave_id,
        "sensor_type": "shtc3",
        "humidity": reading.humidity,
        "temperature": reading.temperature,
        "tx_frame": frame_to_hex(request),
        "rx_frame": frame_to_hex(
            response_frame
        ),
    }


def read_soil_sensor(
    transport,
    slave_id: int,
):
    request = (
        build_read_holding_registers_request(
            slave_id=slave_id,
            start_register=0,
            quantity=9,
        )
    )

    response_frame = transport.exchange(
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

    return {
        "sensor_id": 3,
        "slave_id": slave_id,
        "sensor_type": "soil_7in1",
        "moisture": reading.moisture,
        "temperature": reading.temperature,
        "conductivity": (
            reading.conductivity
        ),
        "ph": reading.ph,
        "nitrogen": reading.nitrogen,
        "phosphate": reading.phosphate,
        "potassium": reading.potassium,
        "salinity": reading.salinity,
        "tds": reading.tds,
        "tx_frame": frame_to_hex(request),
        "rx_frame": frame_to_hex(
            response_frame
        ),
    }



def poll_once(
    transport,
    state: GatewayState,
    soil_transport=None,
    on_error=None,
):
    """Read independent sensors; failed reads do not stop other sensors.

    on_error(sensor_id, exception) is called after all attempts fail.
    Only successful readings are returned (no fabricated sensor values).
    """
    results = []
    configs = {sensor_id: state.get_sensor(sensor_id) for sensor_id in (1, 2, 3)}

    def read_with_retry(sensor_id, read_func, attempts=2):
        for attempt in range(1, attempts + 1):
            try:
                return read_func()
            except Exception as error:
                # Do not intercept Ctrl+C or other BaseException signals.
                if attempt < attempts:
                    print(
                        f"Sensor {sensor_id} read failed "
                        f"(attempt {attempt}/{attempts}): {error}. Retrying..."
                    )
                    time.sleep(0.2)
                else:
                    if on_error is not None:
                        on_error(sensor_id, error)
                    else:
                        print(
                            f"Sensor {sensor_id} unavailable after "
                            f"{attempts} attempts: {type(error).__name__}: {error}"
                        )
        return None

    sensor_1 = read_with_retry(
        1,
        lambda: read_shtc3_sensor(
            transport=transport,
            sensor_id=1,
            slave_id=configs[1]["slave_id"],
        ),
    )
    if sensor_1 is not None:
        results.append(sensor_1)

    # Keep the 200 ms delay that stabilized sequential COM6 requests.
    time.sleep(0.2)

    sensor_2 = read_with_retry(
        2,
        lambda: read_shtc3_sensor(
            transport=transport,
            sensor_id=2,
            slave_id=configs[2]["slave_id"],
        ),
    )
    if sensor_2 is not None:
        results.append(sensor_2)

    # No COM7 on legacy test setups: skip Soil 7-in-1 entirely.
    if soil_transport is not None:
        time.sleep(0.2)
        sensor_3 = read_with_retry(
            3,
            lambda: read_soil_sensor(
                transport=soil_transport,
                slave_id=configs[3]["slave_id"],
            ),
        )
        if sensor_3 is not None:
            results.append(sensor_3)

    return results

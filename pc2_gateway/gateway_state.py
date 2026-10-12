from copy import deepcopy
from threading import Lock


class GatewayState:
    def __init__(self):
        self._lock = Lock()

        self._sensors = {
            1: {
                "slave_id": 3,
                "baudrate": 9600,
                "pending_slave_id": 3,
                "pending_baudrate": 9600,
            },
            2: {
                "slave_id": 2,
                "baudrate": 9600,
                "pending_slave_id": 2,
                "pending_baudrate": 9600,
            },
            3: {
                "slave_id": 1,
                "baudrate": 9600,
                "pending_slave_id": 1,
                "pending_baudrate": 9600,
            },
        }

    def get_sensor(
        self,
        sensor_id: int,
    ) -> dict:
        with self._lock:
            if sensor_id not in self._sensors:
                raise ValueError(
                    f"Invalid sensor_id: {sensor_id}"
                )

            return deepcopy(
                self._sensors[sensor_id]
            )

    def set_pending_slave_id(
        self,
        sensor_id: int,
        slave_id: int,
    ):
        if not 1 <= slave_id <= 247:
            raise ValueError(
                "slave_id must be between 1 and 247"
            )

        with self._lock:
            self._sensors[
                sensor_id
            ][
                "pending_slave_id"
            ] = slave_id

    def set_pending_baudrate(
        self,
        sensor_id: int,
        baudrate: int,
    ):
        if baudrate not in (
            4800,
            9600,
            19200,
            38400,
        ):
            raise ValueError(
                f"Unsupported baudrate: {baudrate}"
            )

        with self._lock:
            self._sensors[
                sensor_id
            ][
                "pending_baudrate"
            ] = baudrate

    def apply_pending(
        self,
        sensor_id: int,
    ) -> dict:
        with self._lock:
            sensor = self._sensors[
                sensor_id
            ]

            sensor["slave_id"] = (
                sensor["pending_slave_id"]
            )

            sensor["baudrate"] = (
                sensor["pending_baudrate"]
            )

            return deepcopy(sensor)

    def get_all(self) -> dict:
        with self._lock:
            return deepcopy(
                self._sensors
            )
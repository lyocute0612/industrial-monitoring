from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock


class SensorDataStore:
    VALID_SENSOR_IDS = {1, 2, 3}

    def __init__(self):
        self._latest = {}
        self._lock = Lock()

    def update(
        self,
        data: dict,
    ) -> dict:
        if not isinstance(data, dict):
            raise TypeError(
                "Sensor data must be a dictionary"
            )

        if "sensor_id" not in data:
            raise ValueError(
                "Missing sensor_id"
            )

        sensor_id = data["sensor_id"]

        if sensor_id not in self.VALID_SENSOR_IDS:
            raise ValueError(
                f"Unsupported sensor_id: {sensor_id}"
            )

        record = deepcopy(data)

        record["received_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        with self._lock:
            self._latest[sensor_id] = record

        return deepcopy(record)

    def get_latest(
        self,
        sensor_id: int,
    ):
        if sensor_id not in self.VALID_SENSOR_IDS:
            raise ValueError(
                f"Unsupported sensor_id: {sensor_id}"
            )

        with self._lock:
            record = self._latest.get(
                sensor_id
            )

            if record is None:
                return None

            return deepcopy(record)

    def get_all(self) -> dict:
        with self._lock:
            return deepcopy(
                self._latest
            )
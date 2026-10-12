from pc1_server.data_store import (
    SensorDataStore,
)


def test_store_starts_empty():
    store = SensorDataStore()

    assert store.get_all() == {}


def test_store_sensor_1():
    store = SensorDataStore()

    store.update(
        {
            "sensor_id": 1,
            "humidity": 81.5,
            "temperature": 21.6,
        }
    )

    sensor = store.get_latest(1)

    assert sensor["sensor_id"] == 1
    assert sensor["humidity"] == 81.5
    assert sensor["temperature"] == 21.6

    assert "received_at" in sensor


def test_store_three_sensors():
    store = SensorDataStore()

    store.update(
        {
            "sensor_id": 1,
            "humidity": 81.5,
        }
    )

    store.update(
        {
            "sensor_id": 2,
            "humidity": 75.5,
        }
    )

    store.update(
        {
            "sensor_id": 3,
            "ph": 7.0,
        }
    )

    data = store.get_all()

    assert len(data) == 3

    assert data[1]["humidity"] == 81.5
    assert data[2]["humidity"] == 75.5
    assert data[3]["ph"] == 7.0


def test_new_data_replaces_old_data():
    store = SensorDataStore()

    store.update(
        {
            "sensor_id": 1,
            "temperature": 20.0,
        }
    )

    store.update(
        {
            "sensor_id": 1,
            "temperature": 25.0,
        }
    )

    sensor = store.get_latest(1)

    assert sensor["temperature"] == 25.0

    assert len(
        store.get_all()
    ) == 1


def test_invalid_sensor_id():
    store = SensorDataStore()

    try:
        store.update(
            {
                "sensor_id": 99,
            }
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError"
        )
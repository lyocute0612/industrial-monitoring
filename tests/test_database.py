from pc1_server.database import (
    SensorDatabase,
)


def test_database_starts_empty(
    tmp_path,
):
    db_path = (
        tmp_path
        / "test.db"
    )

    database = SensorDatabase(
        db_path
    )

    database.initialize()

    assert (
        database.count_readings()
        == 0
    )


def test_insert_sensor_1(
    tmp_path,
):
    db_path = (
        tmp_path
        / "test.db"
    )

    database = SensorDatabase(
        db_path
    )

    database.initialize()

    database.insert_reading(
        {
            "sensor_id": 1,
            "slave_id": 3,
            "sensor_type": "shtc3",
            "humidity": 81.5,
            "temperature": 21.6,
            "received_at": (
                "2026-10-07T10:00:00+00:00"
            ),
        }
    )

    assert (
        database.count_readings()
        == 1
    )

    latest = database.get_latest(
        1
    )

    assert latest["sensor_id"] == 1
    assert latest["slave_id"] == 3

    assert (
        latest["humidity"]
        == 81.5
    )

    assert (
        latest["temperature"]
        == 21.6
    )


def test_insert_soil_sensor(
    tmp_path,
):
    database = SensorDatabase(
        tmp_path / "test.db"
    )

    database.initialize()

    database.insert_reading(
        {
            "sensor_id": 3,
            "slave_id": 1,
            "sensor_type": (
                "soil_7in1"
            ),
            "moisture": 50.2,
            "temperature": 24.3,
            "conductivity": 400,
            "ph": 7.0,
            "nitrogen": 10,
            "phosphate": 20,
            "potassium": 30,
            "salinity": 40,
            "tds": 200,
        }
    )

    latest = database.get_latest(
        3
    )

    assert latest["sensor_id"] == 3
    assert latest["moisture"] == 50.2
    assert latest["temperature"] == 24.3
    assert latest["ph"] == 7.0

    assert latest["nitrogen"] == 10
    assert latest["phosphate"] == 20
    assert latest["potassium"] == 30


def test_database_keeps_history(
    tmp_path,
):
    database = SensorDatabase(
        tmp_path / "test.db"
    )

    database.initialize()

    database.insert_reading(
        {
            "sensor_id": 1,
            "temperature": 20.0,
        }
    )

    database.insert_reading(
        {
            "sensor_id": 1,
            "temperature": 21.0,
        }
    )

    database.insert_reading(
        {
            "sensor_id": 1,
            "temperature": 22.0,
        }
    )

    assert (
        database.count_readings()
        == 3
    )

    history = database.get_history(
        sensor_id=1,
        limit=10,
    )

    assert len(history) == 3

    assert (
        history[0]["temperature"]
        == 22.0
    )

    assert (
        history[1]["temperature"]
        == 21.0
    )

    assert (
        history[2]["temperature"]
        == 20.0
    )
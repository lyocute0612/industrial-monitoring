from datetime import (
    datetime,
    timedelta,
    timezone,
)

from pc1_server.data_store import (
    SensorDataStore,
)
from pc1_server.database import (
    SensorDatabase,
)
from pc1_server.web_server import (
    create_app,
)


def test_history_api_returns_oldest_first(
    tmp_path,
):
    database = SensorDatabase(
        tmp_path / "history.db"
    )
    database.initialize()

    base = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    database.insert_reading(
        {
            "sensor_id": 1,
            "slave_id": 3,
            "sensor_type": "shtc3",
            "received_at": base.isoformat(),
            "humidity": 80.0,
            "temperature": 20.0,
        }
    )

    database.insert_reading(
        {
            "sensor_id": 1,
            "slave_id": 3,
            "sensor_type": "shtc3",
            "received_at": (
                base + timedelta(seconds=1)
            ).isoformat(),
            "humidity": 81.0,
            "temperature": 21.0,
        }
    )

    app = create_app(
        SensorDataStore(),
        database,
    )

    client = app.test_client()

    response = client.get(
        "/history/1?limit=10"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["count"] == 2
    assert payload["readings"][0]["humidity"] == 80.0
    assert payload["readings"][1]["humidity"] == 81.0


def test_history_api_rejects_invalid_sensor(
    tmp_path,
):
    database = SensorDatabase(
        tmp_path / "history.db"
    )
    database.initialize()

    app = create_app(
        SensorDataStore(),
        database,
    )

    client = app.test_client()

    response = client.get(
        "/history/9"
    )

    assert response.status_code == 400

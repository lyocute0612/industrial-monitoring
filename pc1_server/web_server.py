from flask import (
    Flask,
    jsonify,
    render_template,
    request,
)

from pc1_server.data_store import (
    SensorDataStore,
)

from pc1_server.database import (
    SensorDatabase,
)

from pc1_server.tcp_server import (
    is_pc2_connected,
)


HISTORY_FIELDS = {
    1: (
        "humidity",
        "temperature",
    ),
    2: (
        "humidity",
        "temperature",
    ),
    3: (
        "moisture",
        "temperature",
        "conductivity",
        "ph",
        "nitrogen",
        "phosphate",
        "potassium",
        "salinity",
        "tds",
    ),
}


def _history_payload(
    sensor_id: int,
    rows: list,
) -> list:
    fields = HISTORY_FIELDS[
        sensor_id
    ]

    result = []

    # Database returns newest first. The browser chart needs
    # chronological order from oldest to newest.
    for row in reversed(rows):
        item = {
            "id": row.get("id"),
            "sensor_id": row.get(
                "sensor_id"
            ),
            "slave_id": row.get(
                "slave_id"
            ),
            "received_at": row.get(
                "received_at"
            ),
        }

        for field in fields:
            item[field] = row.get(
                field
            )

        result.append(item)

    return result


def create_app(
    data_store: SensorDataStore,
    database: SensorDatabase,
) -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    @app.get("/")
    def index():
        return render_template(
            "index.html"
        )

    @app.get("/latest")
    def latest():
        sensors = (
            data_store.get_all()
        )

        payload = {
            "pc2_connected": (
                is_pc2_connected()
            ),
            "sensors": {
                str(sensor_id): data
                for sensor_id, data
                in sensors.items()
            },
        }

        return jsonify(
            payload
        )

    @app.get(
        "/history/<int:sensor_id>"
    )
    def history(sensor_id: int):
        if sensor_id not in HISTORY_FIELDS:
            return jsonify(
                {
                    "error": (
                        "sensor_id must be "
                        "1, 2, or 3"
                    )
                }
            ), 400

        limit = request.args.get(
            "limit",
            default=60,
            type=int,
        )

        if limit is None:
            limit = 60

        limit = max(
            1,
            min(limit, 500),
        )

        rows = database.get_history(
            sensor_id=sensor_id,
            limit=limit,
        )

        return jsonify(
            {
                "sensor_id": sensor_id,
                "limit": limit,
                "count": len(rows),
                "fields": list(
                    HISTORY_FIELDS[
                        sensor_id
                    ]
                ),
                "readings": (
                    _history_payload(
                        sensor_id,
                        rows,
                    )
                ),
            }
        )

    return app


def run_web_server(
    data_store: SensorDataStore,
    database: SensorDatabase,
    host: str = "127.0.0.1",
    port: int = 5000,
):
    app = create_app(
        data_store,
        database,
    )

    print(
        "PC1 Web Dashboard"
    )

    print(
        "-----------------"
    )

    print(
        f"Dashboard: "
        f"http://{host}:{port}"
    )

    app.run(
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


if __name__ == "__main__":
    store = SensorDataStore()
    database = SensorDatabase()
    database.initialize()

    run_web_server(
        store,
        database,
    )

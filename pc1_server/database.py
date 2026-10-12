import json
import sqlite3

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path


class SensorDatabase:
    def __init__(
        self,
        db_path="data/industrial_monitoring.db",
    ):
        self.db_path = Path(
            db_path
        )

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def initialize(self):
        with sqlite3.connect(
            self.db_path
        ) as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    sensor_id INTEGER NOT NULL,
                    slave_id INTEGER,
                    sensor_type TEXT,

                    received_at TEXT NOT NULL,

                    humidity REAL,
                    temperature REAL,

                    moisture REAL,
                    conductivity REAL,
                    ph REAL,

                    nitrogen REAL,
                    phosphate REAL,
                    potassium REAL,

                    salinity REAL,
                    tds REAL,

                    tx_frame TEXT,
                    rx_frame TEXT,

                    raw_json TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_sensor_readings_sensor_id
                ON sensor_readings(sensor_id)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_sensor_readings_received_at
                ON sensor_readings(received_at)
                """
            )

    def insert_reading(
        self,
        data: dict,
    ):
        received_at = data.get(
            "received_at"
        )

        if received_at is None:
            received_at = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

        raw_json = json.dumps(
            data,
            ensure_ascii=False,
        )

        with sqlite3.connect(
            self.db_path
        ) as connection:

            connection.execute(
                """
                INSERT INTO sensor_readings (
                    sensor_id,
                    slave_id,
                    sensor_type,
                    received_at,
                    humidity,
                    temperature,
                    moisture,
                    conductivity,
                    ph,
                    nitrogen,
                    phosphate,
                    potassium,
                    salinity,
                    tds,
                    tx_frame,
                    rx_frame,
                    raw_json
                )
                VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?
                )
                """,
                (
                    data["sensor_id"],
                    data.get("slave_id"),
                    data.get("sensor_type"),
                    received_at,
                    data.get("humidity"),
                    data.get("temperature"),
                    data.get("moisture"),
                    data.get("conductivity"),
                    data.get("ph"),
                    data.get("nitrogen"),
                    data.get("phosphate"),
                    data.get("potassium"),
                    data.get("salinity"),
                    data.get("tds"),
                    data.get("tx_frame"),
                    data.get("rx_frame"),
                    raw_json,
                ),
            )

    def count_readings(
        self,
    ) -> int:
        with sqlite3.connect(
            self.db_path
        ) as connection:

            cursor = connection.execute(
                """
                SELECT COUNT(*)
                FROM sensor_readings
                """
            )

            return cursor.fetchone()[0]

    def get_latest(
        self,
        sensor_id: int,
    ):
        with sqlite3.connect(
            self.db_path
        ) as connection:

            connection.row_factory = (
                sqlite3.Row
            )

            cursor = connection.execute(
                """
                SELECT *
                FROM sensor_readings
                WHERE sensor_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    sensor_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return dict(row)

    def get_history(
        self,
        sensor_id: int,
        limit: int = 100,
    ) -> list:
        with sqlite3.connect(
            self.db_path
        ) as connection:

            connection.row_factory = (
                sqlite3.Row
            )

            cursor = connection.execute(
                """
                SELECT *
                FROM sensor_readings
                WHERE sensor_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    sensor_id,
                    limit,
                ),
            )

            rows = cursor.fetchall()

            return [
                dict(row)
                for row in rows
            ]
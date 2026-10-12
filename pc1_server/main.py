import threading
import tkinter as tk

from pc1_server.data_store import (
    SensorDataStore,
)

from pc1_server.database import (
    SensorDatabase,
)

from pc1_server.gui import (
    MonitoringGUI,
)

from pc1_server.tcp_server import (
    run_server,
)

from pc1_server.web_server import (
    run_web_server,
)


def main():
    data_store = SensorDataStore()

    database = SensorDatabase()

    database.initialize()

    server_thread = threading.Thread(
        target=run_server,
        kwargs={
            "data_store": data_store,
            "database": database,
        },
        daemon=True,
        name="pc1-tcp-server",
    )

    server_thread.start()

    web_thread = threading.Thread(
        target=run_web_server,
        kwargs={
            "data_store": data_store,
            "database": database,
            "host": "0.0.0.0",
            "port": 5000,
        },
        daemon=True,
        name="pc1-web-server",
    )

    web_thread.start()

    root = tk.Tk()

    MonitoringGUI(
        root,
        data_store,
    )

    root.mainloop()


if __name__ == "__main__":
    main()

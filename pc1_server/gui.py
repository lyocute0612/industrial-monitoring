import tkinter as tk

from collections import deque
from tkinter import ttk

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
)

from matplotlib.figure import Figure

from pc1_server.data_store import (
    SensorDataStore,
)

from pc1_server.tcp_server import (
    get_command_result,
    is_pc2_connected,
    send_write_register,
)

class MonitoringGUI:
    def __init__(
        self,
        root: tk.Tk,
        data_store: SensorDataStore,
    ):
        self.root = root
        self.data_store = data_store

        self.root.title(
            "PC1 Industrial Monitoring"
        )

        self.root.geometry(
            "1200x900"
        )

        self.root.minsize(
            1000,
            750,
        )

        self.max_points = 60

        self.history = {
            1: {
                "time": deque(
                    maxlen=self.max_points
                ),
                "humidity": deque(
                    maxlen=self.max_points
                ),
                "temperature": deque(
                    maxlen=self.max_points
                ),
            },

            2: {
                "time": deque(
                    maxlen=self.max_points
                ),
                "humidity": deque(
                    maxlen=self.max_points
                ),
                "temperature": deque(
                    maxlen=self.max_points
                ),
            },

            3: {
                "time": deque(
                    maxlen=self.max_points
                ),
                "moisture": deque(
                    maxlen=self.max_points
                ),
                "temperature": deque(
                    maxlen=self.max_points
                ),
                "conductivity": deque(
                    maxlen=self.max_points
                ),
                "ph": deque(
                    maxlen=self.max_points
                ),
                "nitrogen": deque(
                    maxlen=self.max_points
                ),
                "phosphate": deque(
                    maxlen=self.max_points
                ),
                "potassium": deque(
                    maxlen=self.max_points
                ),
                "salinity": deque(
                    maxlen=self.max_points
                ),
                "tds": deque(
                    maxlen=self.max_points
                ),
            },
        }

        self.last_received_at = {
            1: None,
            2: None,
            3: None,
        }

        self.sample_index = {
            1: 0,
            2: 0,
            3: 0,
        }        

        self.status_var = tk.StringVar(
            value="Waiting for sensor data..."
        )

        self.sensor_1_humidity = (
            tk.StringVar(value="--")
        )

        self.sensor_1_temperature = (
            tk.StringVar(value="--")
        )

        self.sensor_2_humidity = (
            tk.StringVar(value="--")
        )

        self.sensor_2_temperature = (
            tk.StringVar(value="--")
        )

        self.soil_moisture = (
            tk.StringVar(value="--")
        )

        self.soil_temperature = (
            tk.StringVar(value="--")
        )

        self.soil_conductivity = (
            tk.StringVar(value="--")
        )

        self.soil_ph = (
            tk.StringVar(value="--")
        )

        self.soil_nitrogen = (
            tk.StringVar(value="--")
        )

        self.soil_phosphate = (
            tk.StringVar(value="--")
        )

        self.soil_potassium = (
            tk.StringVar(value="--")
        )

        self.soil_salinity = (
            tk.StringVar(value="--")
        )

        self.soil_tds = (
            tk.StringVar(value="--")
        )

        # PC1 -> PC2 control panel state.
        self.control_sensor_var = (
            tk.StringVar(value="1")
        )

        self.control_slave_id_var = (
            tk.StringVar(value="4")
        )

        self.control_baudrate_var = (
            tk.StringVar(value="9600")
        )

        self.control_status_var = (
            tk.StringVar(
                value="Control: ready"
            )
        )

        self.pc2_connection_var = (
            tk.StringVar(
                value="PC2: disconnected"
            )
        )

        self.sensor_config_vars = {
            1: tk.StringVar(
                value="S1: Slave -- | Baud --"
            ),
            2: tk.StringVar(
                value="S2: Slave -- | Baud --"
            ),
            3: tk.StringVar(
                value="S3: Slave -- | Baud --"
            ),
        }

        self.command_history = deque(
            maxlen=50
        )

        self._pending_command_id = None
        self._pending_command_kind = None

        self._build_gui()
        self.refresh()


    def _build_gui(self):
        main_frame = ttk.Frame(
            self.root,
            padding=15,
        )

        main_frame.pack(
            fill="both",
            expand=True,
        )

        title = ttk.Label(
            main_frame,
            text=(
                "PC1 INDUSTRIAL "
                "MONITORING SYSTEM"
            ),
            font=(
                "Arial",
                18,
                "bold",
            ),
        )

        title.pack(
            pady=(
                0,
                10,
            )
        )

        status = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=(
                "Arial",
                10,
            ),
        )

        status.pack(
            pady=(
                0,
                15,
            )
        )

        self._build_control_panel(
            main_frame
        )

        sensors_frame = ttk.Frame(
            main_frame
        )

        sensors_frame.pack(
            fill="x"
        )

        sensors_frame.columnconfigure(
            0,
            weight=1,
        )

        sensors_frame.columnconfigure(
            1,
            weight=1,
        )

        self._build_sensor_1(
            sensors_frame
        )

        self._build_sensor_2(
            sensors_frame
        )

        self._build_soil_sensor(
            main_frame
        )

        self._build_charts(
            main_frame
        )

        self._build_frames_panel(
            main_frame
        )
    

    def _build_control_panel(
        self,
        parent,
    ):
        frame = ttk.LabelFrame(
            parent,
            text="PC1 -> PC2 Control (Modbus FC06)",
            padding=10,
        )

        frame.pack(
            fill="x",
            padx=5,
            pady=(
                0,
                10,
            ),
        )

        for column in range(8):
            frame.columnconfigure(
                column,
                weight=0,
            )

        frame.columnconfigure(
            7,
            weight=1,
        )

        connection_label = ttk.Label(
            frame,
            textvariable=(
                self.pc2_connection_var
            ),
            font=(
                "Arial",
                10,
                "bold",
            ),
        )

        connection_label.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=5,
            pady=5,
        )

        ttk.Label(
            frame,
            textvariable=(
                self.sensor_config_vars[1]
            ),
        ).grid(
            row=0,
            column=2,
            columnspan=2,
            sticky="w",
            padx=5,
            pady=5,
        )

        ttk.Label(
            frame,
            textvariable=(
                self.sensor_config_vars[2]
            ),
        ).grid(
            row=0,
            column=4,
            columnspan=2,
            sticky="w",
            padx=5,
            pady=5,
        )

        ttk.Label(
            frame,
            textvariable=(
                self.sensor_config_vars[3]
            ),
        ).grid(
            row=0,
            column=6,
            columnspan=2,
            sticky="w",
            padx=5,
            pady=5,
        )

        ttk.Separator(
            frame,
            orient="horizontal",
        ).grid(
            row=1,
            column=0,
            columnspan=8,
            sticky="ew",
            padx=5,
            pady=5,
        )

        ttk.Label(
            frame,
            text="Sensor",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.control_sensor_combo = (
            ttk.Combobox(
                frame,
                textvariable=(
                    self.control_sensor_var
                ),
                values=(
                    "1",
                    "2",
                    "3",
                ),
                state="readonly",
                width=7,
            )
        )

        self.control_sensor_combo.grid(
            row=2,
            column=1,
            sticky="w",
            padx=5,
            pady=5,
        )

        ttk.Label(
            frame,
            text="New Slave ID",
        ).grid(
            row=2,
            column=2,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.control_slave_entry = (
            ttk.Spinbox(
                frame,
                from_=1,
                to=247,
                textvariable=(
                    self.control_slave_id_var
                ),
                width=8,
            )
        )

        self.control_slave_entry.grid(
            row=2,
            column=3,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.write_slave_button = (
            ttk.Button(
                frame,
                text="WRITE SLAVE ID",
                command=(
                    self._send_slave_id_command
                ),
            )
        )

        self.write_slave_button.grid(
            row=2,
            column=4,
            sticky="w",
            padx=5,
            pady=5,
        )

        ttk.Label(
            frame,
            text="Baudrate",
        ).grid(
            row=2,
            column=5,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.control_baudrate_combo = (
            ttk.Combobox(
                frame,
                textvariable=(
                    self.control_baudrate_var
                ),
                values=(
                    "4800",
                    "9600",
                    "19200",
                    "38400",
                ),
                state="readonly",
                width=10,
            )
        )

        self.control_baudrate_combo.grid(
            row=2,
            column=6,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.write_baud_button = (
            ttk.Button(
                frame,
                text="WRITE BAUDRATE",
                command=(
                    self._send_baudrate_command
                ),
            )
        )

        self.write_baud_button.grid(
            row=2,
            column=7,
            sticky="w",
            padx=5,
            pady=5,
        )

        status_label = ttk.Label(
            frame,
            textvariable=(
                self.control_status_var
            ),
        )

        status_label.grid(
            row=3,
            column=0,
            columnspan=7,
            sticky="w",
            padx=5,
            pady=(
                5,
                0,
            ),
        )

        self.history_button = ttk.Button(
            frame,
            text="COMMAND HISTORY",
            command=(
                self._open_command_history
            ),
        )

        self.history_button.grid(
            row=3,
            column=7,
            sticky="e",
            padx=5,
            pady=(
                5,
                0,
            ),
        )

    def _set_control_buttons_state(
        self,
        state: str,
    ):
        self.write_slave_button.config(
            state=state
        )

        self.write_baud_button.config(
            state=state
        )

    def _update_control_connection(
        self,
    ):
        connected = is_pc2_connected()

        if connected:
            self.pc2_connection_var.set(
                "PC2: CONNECTED"
            )

            if self._pending_command_id is None:
                self._set_control_buttons_state(
                    "normal"
                )

        else:
            self.pc2_connection_var.set(
                "PC2: DISCONNECTED"
            )

            self._set_control_buttons_state(
                "disabled"
            )

    def _update_control_config(
        self,
        data,
    ):
        for sensor_id in (
            1,
            2,
            3,
        ):
            sensor = data.get(
                sensor_id
            )

            if sensor is None:
                continue

            slave_id = sensor.get(
                "slave_id",
                "--",
            )

            baudrate = sensor.get(
                "baudrate",
                "--",
            )

            self.sensor_config_vars[
                sensor_id
            ].set(
                f"S{sensor_id}: "
                f"Slave {slave_id} | "
                f"Baud {baudrate}"
            )

    def _append_command_history(
        self,
        result: dict,
    ):
        status = (
            "SUCCESS"
            if result.get("success")
            else "FAILED"
        )

        sensor_id = result.get(
            "sensor_id",
            "--",
        )

        register = result.get(
            "register"
        )

        if isinstance(
            register,
            int,
        ):
            register_text = (
                f"0x{register:04X}"
            )

        else:
            register_text = "--"

        value = result.get(
            "value",
            "--",
        )

        message = result.get(
            "message",
            "",
        )

        line = (
            f"{status} | "
            f"Sensor {sensor_id} | "
            f"Register {register_text} | "
            f"Value {value} | "
            f"{message}"
        )

        self.command_history.appendleft(
            line
        )

    def _open_command_history(
        self,
    ):
        window = tk.Toplevel(
            self.root
        )

        window.title(
            "FC06 Command History"
        )

        window.geometry(
            "900x350"
        )

        frame = ttk.Frame(
            window,
            padding=10,
        )

        frame.pack(
            fill="both",
            expand=True,
        )

        text = tk.Text(
            frame,
            wrap="word",
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=text.yview,
        )

        text.configure(
            yscrollcommand=(
                scrollbar.set
            )
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        text.pack(
            side="left",
            fill="both",
            expand=True,
        )

        if not self.command_history:
            text.insert(
                tk.END,
                "No command history yet.\n"
            )

        else:
            for line in self.command_history:
                text.insert(
                    tk.END,
                    line + "\n"
                )

        text.config(
            state="disabled"
        )

    def _send_slave_id_command(
        self,
    ):
        try:
            sensor_id = int(
                self.control_sensor_var.get()
            )

            new_slave_id = int(
                self.control_slave_id_var.get()
            )

        except ValueError:
            self.control_status_var.set(
                "Control error: "
                "Sensor and Slave ID "
                "must be integers."
            )
            return

        if not 1 <= new_slave_id <= 247:
            self.control_status_var.set(
                "Control error: "
                "Slave ID must be "
                "between 1 and 247."
            )
            return

        self._send_control_command(
            sensor_id=sensor_id,
            register=0x07D0,
            value=new_slave_id,
            command_kind="Slave ID",
        )

    def _send_baudrate_command(
        self,
    ):
        try:
            sensor_id = int(
                self.control_sensor_var.get()
            )

            baudrate = int(
                self.control_baudrate_var.get()
            )

        except ValueError:
            self.control_status_var.set(
                "Control error: "
                "Invalid sensor or baudrate."
            )
            return

        baudrate_codes = {
            4800: 1,
            9600: 2,
            19200: 3,
            38400: 4,
        }

        if baudrate not in baudrate_codes:
            self.control_status_var.set(
                "Control error: "
                "Unsupported baudrate."
            )
            return

        self._send_control_command(
            sensor_id=sensor_id,
            register=0x07D1,
            value=(
                baudrate_codes[
                    baudrate
                ]
            ),
            command_kind="Baudrate",
        )

    def _send_control_command(
        self,
        *,
        sensor_id: int,
        register: int,
        value: int,
        command_kind: str,
    ):
        if self._pending_command_id is not None:
            self.control_status_var.set(
                "Control: waiting for "
                "the previous command..."
            )
            return

        if not is_pc2_connected():
            self.control_status_var.set(
                "Control error: "
                "PC2 is not connected."
            )
            return

        try:
            command_id = (
                send_write_register(
                    sensor_id=sensor_id,
                    register=register,
                    value=value,
                )
            )

        except Exception as error:
            self.control_status_var.set(
                "Control error: "
                f"{error}"
            )
            return

        self._pending_command_id = (
            command_id
        )

        self._pending_command_kind = (
            command_kind
        )

        self._set_control_buttons_state(
            "disabled"
        )

        self.control_status_var.set(
            f"Control: {command_kind} "
            f"command sent to Sensor "
            f"{sensor_id}. Waiting..."
        )

        self.root.after(
            100,
            lambda: (
                self._check_command_result(
                    command_id,
                    0,
                )
            ),
        )

    def _check_command_result(
        self,
        command_id: str,
        attempts: int,
    ):
        if (
            self._pending_command_id
            != command_id
        ):
            return

        result = get_command_result(
            command_id
        )

        if result is None:
            if attempts >= 50:
                self.control_status_var.set(
                    "Control timeout: "
                    "no response from PC2."
                )

                self._pending_command_id = None
                self._pending_command_kind = None

                self._set_control_buttons_state(
                    "normal"
                )
                return

            self.root.after(
                100,
                lambda: (
                    self._check_command_result(
                        command_id,
                        attempts + 1,
                    )
                ),
            )
            return

        command_kind = (
            self._pending_command_kind
            or "Command"
        )

        self._append_command_history(
            result
        )

        self._pending_command_id = None
        self._pending_command_kind = None

        self._set_control_buttons_state(
            "normal"
        )

        if result.get(
            "success"
        ):
            self.control_status_var.set(
                f"{command_kind}: SUCCESS | "
                f"TX: "
                f"{result.get('tx_frame', '--')} | "
                f"RX: "
                f"{result.get('rx_frame', '--')}"
            )

        else:
            self.control_status_var.set(
                f"{command_kind}: FAILED | "
                f"{result.get('message', 'Unknown error')}"
            )

    def _build_charts(
        self,
        parent,
    ):
        charts_frame = ttk.LabelFrame(
            parent,
            text="Realtime Charts",
            padding=5,
        )

        charts_frame.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=10,
        )

        self.charts_notebook = (
            ttk.Notebook(
                charts_frame
            )
        )

        self.charts_notebook.pack(
            fill="both",
            expand=True,
        )

        self._build_shtc3_charts()
        self._build_soil_charts()

    def _build_shtc3_charts(
        self,
    ):
        tab = ttk.Frame(
            self.charts_notebook
        )

        self.charts_notebook.add(
            tab,
            text="Sensor 1 & 2",
        )

        self.shtc3_figure = Figure(
            figsize=(9, 3.2),
            dpi=100,
        )

        self.sensor_1_axis = (
            self.shtc3_figure.add_subplot(
                1,
                2,
                1,
            )
        )

        self.sensor_1_temp_axis = (
            self.sensor_1_axis.twinx()
        )

        self.sensor_2_axis = (
            self.shtc3_figure.add_subplot(
                1,
                2,
                2,
            )
        )

        self.sensor_2_temp_axis = (
            self.sensor_2_axis.twinx()
        )

        (
            self.sensor_1_humidity_line,
        ) = self.sensor_1_axis.plot(
            [],
            [],
            label="Humidity",
        )

        (
            self.sensor_1_temperature_line,
        ) = self.sensor_1_temp_axis.plot(
            [],
            [],
            label="Temperature",
        )

        (
            self.sensor_2_humidity_line,
        ) = self.sensor_2_axis.plot(
            [],
            [],
            label="Humidity",
        )

        (
            self.sensor_2_temperature_line,
        ) = self.sensor_2_temp_axis.plot(
            [],
            [],
            label="Temperature",
        )

        self.sensor_1_axis.set_title(
            "Sensor 1"
        )

        self.sensor_1_axis.set_xlabel(
            "Sample"
        )

        self.sensor_1_axis.set_ylabel(
            "Humidity (%RH)"
        )

        self.sensor_1_temp_axis.set_ylabel(
            "Temperature (°C)"
        )

        self.sensor_1_axis.grid(
            True
        )

        self.sensor_2_axis.set_title(
            "Sensor 2"
        )

        self.sensor_2_axis.set_xlabel(
            "Sample"
        )

        self.sensor_2_axis.set_ylabel(
            "Humidity (%RH)"
        )

        self.sensor_2_temp_axis.set_ylabel(
            "Temperature (°C)"
        )

        self.sensor_2_axis.grid(
            True
        )

        self.sensor_1_axis.legend(
            loc="upper left"
        )

        self.sensor_1_temp_axis.legend(
            loc="upper right"
        )

        self.sensor_2_axis.legend(
            loc="upper left"
        )

        self.sensor_2_temp_axis.legend(
            loc="upper right"
        )

        self.shtc3_figure.tight_layout()

        self.shtc3_canvas = (
            FigureCanvasTkAgg(
                self.shtc3_figure,
                master=tab,
            )
        )

        self.shtc3_canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
        )

    def _build_soil_charts(
        self,
    ):
        tab = ttk.Frame(
            self.charts_notebook
        )

        self.charts_notebook.add(
            tab,
            text="Sensor 3",
        )

        self.soil_figure = Figure(
            figsize=(9, 7),
            dpi=100,
        )

        metrics = [
            (
                "moisture",
                "Moisture (%)",
            ),
            (
                "temperature",
                "Temperature (°C)",
            ),
            (
                "conductivity",
                "Conductivity",
            ),
            (
                "ph",
                "pH",
            ),
            (
                "nitrogen",
                "Nitrogen",
            ),
            (
                "phosphate",
                "Phosphate",
            ),
            (
                "potassium",
                "Potassium",
            ),
            (
                "salinity",
                "Salinity",
            ),
            (
                "tds",
                "TDS",
            ),
        ]

        self.soil_axes = {}
        self.soil_lines = {}

        for index, (
            key,
            title,
        ) in enumerate(metrics):
            axis = (
                self.soil_figure.add_subplot(
                    3,
                    3,
                    index + 1,
                )
            )

            (
                line,
            ) = axis.plot(
                [],
                [],
            )

            axis.set_title(
                title,
                fontsize=9,
            )

            axis.set_xlabel(
                "Sample",
                fontsize=8,
            )

            axis.grid(
                True
            )

            axis.tick_params(
                labelsize=7
            )

            self.soil_axes[
                key
            ] = axis

            self.soil_lines[
                key
            ] = line

        self.soil_figure.tight_layout()

        self.soil_canvas = (
            FigureCanvasTkAgg(
                self.soil_figure,
                master=tab,
            )
        )

        self.soil_canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
        )
    
    
    

    

    def _create_value_row(
        self,
        parent,
        row,
        name,
        variable,
        unit="",
    ):
        ttk.Label(
            parent,
            text=name,
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=8,
            pady=5,
        )

        ttk.Label(
            parent,
            textvariable=variable,
            font=(
                "Arial",
                11,
                "bold",
            ),
        ).grid(
            row=row,
            column=1,
            sticky="e",
            padx=8,
            pady=5,
        )

        ttk.Label(
            parent,
            text=unit,
        ).grid(
            row=row,
            column=2,
            sticky="w",
            padx=8,
            pady=5,
        )

    def _build_sensor_1(
        self,
        parent,
    ):
        frame = ttk.LabelFrame(
            parent,
            text="Sensor 1 - SHTC3",
            padding=10,
        )

        frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=5,
            pady=5,
        )

        self._create_value_row(
            frame,
            0,
            "Humidity",
            self.sensor_1_humidity,
            "%RH",
        )

        self._create_value_row(
            frame,
            1,
            "Temperature",
            self.sensor_1_temperature,
            "°C",
        )

    def _build_sensor_2(
        self,
        parent,
    ):
        frame = ttk.LabelFrame(
            parent,
            text="Sensor 2 - SHTC3",
            padding=10,
        )

        frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=5,
            pady=5,
        )

        self._create_value_row(
            frame,
            0,
            "Humidity",
            self.sensor_2_humidity,
            "%RH",
        )

        self._create_value_row(
            frame,
            1,
            "Temperature",
            self.sensor_2_temperature,
            "°C",
        )

    def _build_soil_sensor(
        self,
        parent,
    ):
        frame = ttk.LabelFrame(
            parent,
            text="Sensor 3 - Soil 7-in-1",
            padding=10,
        )

        frame.pack(
            fill="x",
            padx=5,
            pady=10,
        )

        self._create_value_row(
            frame,
            0,
            "Moisture",
            self.soil_moisture,
            "%",
        )

        self._create_value_row(
            frame,
            1,
            "Temperature",
            self.soil_temperature,
            "°C",
        )

        self._create_value_row(
            frame,
            2,
            "Conductivity",
            self.soil_conductivity,
            "µS/cm",
        )

        self._create_value_row(
            frame,
            3,
            "pH",
            self.soil_ph,
        )

        self._create_value_row(
            frame,
            4,
            "Nitrogen",
            self.soil_nitrogen,
            "mg/kg",
        )

        self._create_value_row(
            frame,
            5,
            "Phosphate",
            self.soil_phosphate,
            "mg/kg",
        )

        self._create_value_row(
            frame,
            6,
            "Potassium",
            self.soil_potassium,
            "mg/kg",
        )

        self._create_value_row(
            frame,
            7,
            "Salinity",
            self.soil_salinity,
        )

        self._create_value_row(
            frame,
            8,
            "TDS",
            self.soil_tds,
        )

    def _build_frames_panel(
        self,
        parent,
    ):
        frame = ttk.LabelFrame(
            parent,
            text="Modbus TX / RX Frames",
            padding=10,
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5,
        )

        self.frames_text = tk.Text(
            frame,
            height=9,
            wrap="word",
        )

        self.frames_text.pack(
            fill="both",
            expand=True,
        )

        self.frames_text.config(
            state="disabled"
        )

    @staticmethod
    def _format_value(
        value,
        decimals=1,
    ):
        if value is None:
            return "--"

        if isinstance(
            value,
            float,
        ):
            return (
                f"{value:.{decimals}f}"
            )

        return str(value)
    

    def _append_history(
        self,
        data,
    ):
        for sensor_id in (
            1,
            2,
            3,
        ):
            sensor = data.get(
                sensor_id
            )

            if sensor is None:
                continue

            received_at = sensor.get(
                "received_at"
            )

            if (
                received_at
                == self.last_received_at[
                    sensor_id
                ]
            ):
                continue

            self.last_received_at[
                sensor_id
            ] = received_at

            self.sample_index[
                sensor_id
            ] += 1

            history = self.history[
                sensor_id
            ]

            history["time"].append(
                self.sample_index[
                    sensor_id
                ]
            )

            if sensor_id in (
                1,
                2,
            ):
                history[
                    "humidity"
                ].append(
                    sensor.get(
                        "humidity"
                    )
                )

                history[
                    "temperature"
                ].append(
                    sensor.get(
                        "temperature"
                    )
                )

            elif sensor_id == 3:
                for key in (
                    "moisture",
                    "temperature",
                    "conductivity",
                    "ph",
                    "nitrogen",
                    "phosphate",
                    "potassium",
                    "salinity",
                    "tds",
                ):
                    history[key].append(
                        sensor.get(
                            key
                        )
                    )


    def _refresh_shtc3_charts(
        self,
    ):
        sensor_1 = self.history[1]

        x1 = list(
            sensor_1["time"]
        )

        h1 = list(
            sensor_1["humidity"]
        )

        t1 = list(
            sensor_1["temperature"]
        )

        self.sensor_1_humidity_line.set_data(
            x1,
            h1,
        )

        self.sensor_1_temperature_line.set_data(
            x1,
            t1,
        )

        self.sensor_1_axis.relim()
        self.sensor_1_axis.autoscale_view()

        self.sensor_1_temp_axis.relim()
        self.sensor_1_temp_axis.autoscale_view()

        sensor_2 = self.history[2]

        x2 = list(
            sensor_2["time"]
        )

        h2 = list(
            sensor_2["humidity"]
        )

        t2 = list(
            sensor_2["temperature"]
        )

        self.sensor_2_humidity_line.set_data(
            x2,
            h2,
        )

        self.sensor_2_temperature_line.set_data(
            x2,
            t2,
        )

        self.sensor_2_axis.relim()
        self.sensor_2_axis.autoscale_view()

        self.sensor_2_temp_axis.relim()
        self.sensor_2_temp_axis.autoscale_view()

        self.shtc3_canvas.draw_idle()

    def _refresh_soil_charts(
        self,
    ):
        history = self.history[3]

        x = list(
            history["time"]
        )

        for key in (
            "moisture",
            "temperature",
            "conductivity",
            "ph",
            "nitrogen",
            "phosphate",
            "potassium",
            "salinity",
            "tds",
        ):
            y = list(
                history[key]
            )

            line = self.soil_lines[
                key
            ]

            axis = self.soil_axes[
                key
            ]

            line.set_data(
                x,
                y,
            )

            axis.relim()
            axis.autoscale_view()

        self.soil_canvas.draw_idle()    

    def refresh(self):
        data = (
            self.data_store.get_all()
        )

        self._update_status(
            data
        )

        self._update_sensor_1(
            data.get(1)
        )

        self._update_sensor_2(
            data.get(2)
        )

        self._update_soil_sensor(
            data.get(3)
        )

        self._update_frames(
            data
        )

        self._update_control_connection()

        self._update_control_config(
            data
        )

        self._append_history(
            data
        )

        self._refresh_shtc3_charts()

        self._refresh_soil_charts()

        self.root.after(
            500,
            self.refresh,
        )

    def _update_status(
        self,
        data,
    ):
        count = len(data)

        if count == 0:
            self.status_var.set(
                "Waiting for sensor data..."
            )

        elif count < 3:
            self.status_var.set(
                f"Receiving data: "
                f"{count}/3 sensors"
            )

        else:
            self.status_var.set(
                "Receiving data: "
                "3/3 sensors"
            )

    def _update_sensor_1(
        self,
        data,
    ):
        if data is None:
            return

        self.sensor_1_humidity.set(
            self._format_value(
                data.get("humidity")
            )
        )

        self.sensor_1_temperature.set(
            self._format_value(
                data.get("temperature")
            )
        )

    def _update_sensor_2(
        self,
        data,
    ):
        if data is None:
            return

        self.sensor_2_humidity.set(
            self._format_value(
                data.get("humidity")
            )
        )

        self.sensor_2_temperature.set(
            self._format_value(
                data.get("temperature")
            )
        )

    def _update_soil_sensor(
        self,
        data,
    ):
        if data is None:
            return

        self.soil_moisture.set(
            self._format_value(
                data.get("moisture")
            )
        )

        self.soil_temperature.set(
            self._format_value(
                data.get("temperature")
            )
        )

        self.soil_conductivity.set(
            self._format_value(
                data.get("conductivity")
            )
        )

        self.soil_ph.set(
            self._format_value(
                data.get("ph")
            )
        )

        self.soil_nitrogen.set(
            self._format_value(
                data.get("nitrogen")
            )
        )

        self.soil_phosphate.set(
            self._format_value(
                data.get("phosphate")
            )
        )

        self.soil_potassium.set(
            self._format_value(
                data.get("potassium")
            )
        )

        self.soil_salinity.set(
            self._format_value(
                data.get("salinity")
            )
        )

        self.soil_tds.set(
            self._format_value(
                data.get("tds")
            )
        )

    def _update_frames(
        self,
        data,
    ):
        lines = []

        for sensor_id in (
            1,
            2,
            3,
        ):
            sensor = data.get(
                sensor_id
            )

            if sensor is None:
                continue

            lines.append(
                f"Sensor {sensor_id}"
            )

            lines.append(
                f"TX: "
                f"{sensor.get('tx_frame', '--')}"
            )

            lines.append(
                f"RX: "
                f"{sensor.get('rx_frame', '--')}"
            )

            lines.append("")

        content = "\n".join(
            lines
        )

        self.frames_text.config(
            state="normal"
        )

        self.frames_text.delete(
            "1.0",
            tk.END,
        )

        self.frames_text.insert(
            tk.END,
            content,
        )

        self.frames_text.config(
            state="disabled"
        )
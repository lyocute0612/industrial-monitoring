const POLL_INTERVAL_MS = 1500;

function formatValue(
    value,
    digits = 1
) {
    if (
        value === null
        || value === undefined
    ) {
        return "--";
    }

    if (
        typeof value === "number"
        && !Number.isInteger(value)
    ) {
        return value.toFixed(digits);
    }

    return String(value);
}

function setText(
    id,
    value
) {
    const element =
        document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}

function updateConnection(
    connected
) {
    const dot =
        document.getElementById(
            "connection-dot"
        );

    const label =
        document.getElementById(
            "connection-status"
        );

    if (!dot || !label) {
        return;
    }

    dot.classList.toggle(
        "online",
        connected
    );

    dot.classList.toggle(
        "offline",
        !connected
    );

    label.textContent =
        connected
            ? "CONNECTED"
            : "DISCONNECTED";
}

function updateCommon(
    sensorId,
    sensor
) {
    if (!sensor) {
        return;
    }

    setText(
        `sensor-${sensorId}-slave`,
        `Slave ${
            formatValue(
                sensor.slave_id,
                0
            )
        }`
    );

    setText(
        `sensor-${sensorId}-baudrate`,
        formatValue(
            sensor.baudrate,
            0
        )
    );

    setText(
        `sensor-${sensorId}-tx`,
        sensor.tx_frame || "--"
    );

    setText(
        `sensor-${sensorId}-rx`,
        sensor.rx_frame || "--"
    );
}

function updateSensor1(
    sensor
) {
    if (!sensor) {
        return;
    }

    updateCommon(
        1,
        sensor
    );

    setText(
        "sensor-1-humidity",
        formatValue(
            sensor.humidity
        )
    );

    setText(
        "sensor-1-temperature",
        formatValue(
            sensor.temperature
        )
    );
}

function updateSensor2(
    sensor
) {
    if (!sensor) {
        return;
    }

    updateCommon(
        2,
        sensor
    );

    setText(
        "sensor-2-humidity",
        formatValue(
            sensor.humidity
        )
    );

    setText(
        "sensor-2-temperature",
        formatValue(
            sensor.temperature
        )
    );
}

function updateSensor3(
    sensor
) {
    if (!sensor) {
        return;
    }

    updateCommon(
        3,
        sensor
    );

    const fields = [
        "moisture",
        "temperature",
        "conductivity",
        "ph",
        "nitrogen",
        "phosphate",
        "potassium",
        "salinity",
        "tds",
    ];

    for (const field of fields) {
        setText(
            `sensor-3-${field}`,
            formatValue(
                sensor[field]
            )
        );
    }
}

async function refreshDashboard() {
    try {
        const response = await fetch(
            "/latest",
            {
                cache: "no-store",
            }
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const payload =
            await response.json();

        updateConnection(
            Boolean(
                payload.pc2_connected
            )
        );

        const sensors =
            payload.sensors || {};

        updateSensor1(
            sensors["1"]
        );

        updateSensor2(
            sensors["2"]
        );

        updateSensor3(
            sensors["3"]
        );

        setText(
            "last-refresh",
            new Date().toLocaleTimeString()
        );

    } catch (error) {
        updateConnection(false);

        setText(
            "last-refresh",
            `Error: ${error.message}`
        );
    }
}

refreshDashboard();

setInterval(
    refreshDashboard,
    POLL_INTERVAL_MS
);


const HISTORY_REFRESH_MS = 5000;

const HISTORY_METRICS = {
    "1": [
        ["humidity", "Humidity (%RH)"],
        ["temperature", "Temperature (°C)"],
    ],
    "2": [
        ["humidity", "Humidity (%RH)"],
        ["temperature", "Temperature (°C)"],
    ],
    "3": [
        ["moisture", "Moisture (%)"],
        ["temperature", "Temperature (°C)"],
        ["conductivity", "Conductivity (µS/cm)"],
        ["ph", "pH"],
        ["nitrogen", "Nitrogen (mg/kg)"],
        ["phosphate", "Phosphate (mg/kg)"],
        ["potassium", "Potassium (mg/kg)"],
        ["salinity", "Salinity"],
        ["tds", "TDS"],
    ],
};

function populateHistoryMetrics() {
    const sensorSelect = document.getElementById(
        "history-sensor"
    );

    const metricSelect = document.getElementById(
        "history-metric"
    );

    if (!sensorSelect || !metricSelect) {
        return;
    }

    const current = metricSelect.value;
    const options = HISTORY_METRICS[
        sensorSelect.value
    ] || [];

    metricSelect.innerHTML = "";

    for (const [value, label] of options) {
        const option = document.createElement(
            "option"
        );

        option.value = value;
        option.textContent = label;

        metricSelect.appendChild(
            option
        );
    }

    if (
        options.some(
            ([value]) => value === current
        )
    ) {
        metricSelect.value = current;
    }
}

function historyMetricLabel(
    sensorId,
    metric
) {
    const options = HISTORY_METRICS[
        String(sensorId)
    ] || [];

    const found = options.find(
        ([value]) => value === metric
    );

    return found
        ? found[1]
        : metric;
}

function formatHistoryTime(value) {
    if (!value) {
        return "--";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleTimeString();
}

function drawHistoryChart(
    readings,
    metric,
    label
) {
    const canvas = document.getElementById(
        "history-chart"
    );

    if (!canvas) {
        return;
    }

    const shell = canvas.parentElement;
    const rect = shell.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    const width = Math.max(
        320,
        Math.floor(rect.width - 20)
    );

    const height = Math.max(
        240,
        Math.floor(rect.height - 20)
    );

    canvas.width = Math.floor(
        width * dpr
    );

    canvas.height = Math.floor(
        height * dpr
    );

    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const context = canvas.getContext(
        "2d"
    );

    context.setTransform(
        dpr,
        0,
        0,
        dpr,
        0,
        0
    );

    context.clearRect(
        0,
        0,
        width,
        height
    );

    const points = readings
        .map((reading) => ({
            value: Number(
                reading[metric]
            ),
            time: reading.received_at,
        }))
        .filter((point) => (
            Number.isFinite(
                point.value
            )
        ));

    const padding = {
        left: 62,
        right: 22,
        top: 42,
        bottom: 45,
    };

    const plotWidth =
        width
        - padding.left
        - padding.right;

    const plotHeight =
        height
        - padding.top
        - padding.bottom;

    context.font =
        "12px system-ui, sans-serif";

    context.fillStyle = "#8fa3bb";
    context.fillText(
        label,
        padding.left,
        20
    );

    if (points.length === 0) {
        context.fillStyle = "#aebdd0";
        context.font =
            "14px system-ui, sans-serif";
        context.fillText(
            "No historical data for this metric.",
            padding.left,
            padding.top + 30
        );
        return;
    }

    let minValue = Math.min(
        ...points.map(
            (point) => point.value
        )
    );

    let maxValue = Math.max(
        ...points.map(
            (point) => point.value
        )
    );

    if (minValue === maxValue) {
        const delta = Math.max(
            Math.abs(minValue) * 0.05,
            1
        );

        minValue -= delta;
        maxValue += delta;
    } else {
        const margin =
            (maxValue - minValue) * 0.08;

        minValue -= margin;
        maxValue += margin;
    }

    context.strokeStyle = "#22384f";
    context.lineWidth = 1;
    context.fillStyle = "#7188a2";
    context.font =
        "11px system-ui, sans-serif";

    const gridLines = 5;

    for (
        let index = 0;
        index <= gridLines;
        index += 1
    ) {
        const ratio = index / gridLines;

        const y =
            padding.top
            + ratio * plotHeight;

        context.beginPath();
        context.moveTo(
            padding.left,
            y
        );
        context.lineTo(
            padding.left + plotWidth,
            y
        );
        context.stroke();

        const value =
            maxValue
            - ratio * (
                maxValue - minValue
            );

        context.fillText(
            value.toFixed(1),
            8,
            y + 4
        );
    }

    const xForIndex = (index) => {
        if (points.length === 1) {
            return (
                padding.left
                + plotWidth / 2
            );
        }

        return (
            padding.left
            + (
                index
                / (points.length - 1)
            ) * plotWidth
        );
    };

    const yForValue = (value) => (
        padding.top
        + (
            (maxValue - value)
            / (maxValue - minValue)
        ) * plotHeight
    );

    context.strokeStyle = "#66b8ff";
    context.lineWidth = 2;
    context.beginPath();

    points.forEach(
        (point, index) => {
            const x = xForIndex(
                index
            );

            const y = yForValue(
                point.value
            );

            if (index === 0) {
                context.moveTo(
                    x,
                    y
                );
            } else {
                context.lineTo(
                    x,
                    y
                );
            }
        }
    );

    context.stroke();

    context.fillStyle = "#d8ecff";

    points.forEach(
        (point, index) => {
            if (
                points.length > 80
                && index % 4 !== 0
                && index !== points.length - 1
            ) {
                return;
            }

            context.beginPath();
            context.arc(
                xForIndex(index),
                yForValue(point.value),
                2.4,
                0,
                Math.PI * 2
            );
            context.fill();
        }
    );

    const first = points[0];
    const last = points[
        points.length - 1
    ];

    context.fillStyle = "#7188a2";
    context.font =
        "11px system-ui, sans-serif";

    context.fillText(
        formatHistoryTime(
            first.time
        ),
        padding.left,
        height - 12
    );

    const lastText = formatHistoryTime(
        last.time
    );

    const lastWidth =
        context.measureText(
            lastText
        ).width;

    context.fillText(
        lastText,
        padding.left
            + plotWidth
            - lastWidth,
        height - 12
    );
}

async function refreshHistory() {
    const sensorSelect = document.getElementById(
        "history-sensor"
    );

    const metricSelect = document.getElementById(
        "history-metric"
    );

    const limitSelect = document.getElementById(
        "history-limit"
    );

    if (
        !sensorSelect
        || !metricSelect
        || !limitSelect
    ) {
        return;
    }

    const sensorId = sensorSelect.value;
    const metric = metricSelect.value;
    const limit = limitSelect.value;

    setText(
        "history-status",
        "Loading history..."
    );

    try {
        const response = await fetch(
            `/history/${sensorId}?limit=${limit}`,
            {
                cache: "no-store",
            }
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const payload =
            await response.json();

        const readings =
            payload.readings || [];

        const label = historyMetricLabel(
            sensorId,
            metric
        );

        drawHistoryChart(
            readings,
            metric,
            label
        );

        setText(
            "history-status",
            `${label} · ${readings.length} samples`
        );

        if (readings.length > 0) {
            const first = readings[0];
            const last = readings[
                readings.length - 1
            ];

            setText(
                "history-range",
                `${formatHistoryTime(first.received_at)} → ${formatHistoryTime(last.received_at)}`
            );
        } else {
            setText(
                "history-range",
                "No data"
            );
        }

    } catch (error) {
        setText(
            "history-status",
            `History error: ${error.message}`
        );

        setText(
            "history-range",
            "--"
        );
    }
}

const historySensor = document.getElementById(
    "history-sensor"
);

const historyMetric = document.getElementById(
    "history-metric"
);

const historyLimit = document.getElementById(
    "history-limit"
);

const historyRefresh = document.getElementById(
    "history-refresh"
);

if (historySensor) {
    historySensor.addEventListener(
        "change",
        () => {
            populateHistoryMetrics();
            refreshHistory();
        }
    );
}

if (historyMetric) {
    historyMetric.addEventListener(
        "change",
        refreshHistory
    );
}

if (historyLimit) {
    historyLimit.addEventListener(
        "change",
        refreshHistory
    );
}

if (historyRefresh) {
    historyRefresh.addEventListener(
        "click",
        refreshHistory
    );
}

window.addEventListener(
    "resize",
    refreshHistory
);

populateHistoryMetrics();
refreshHistory();

setInterval(
    refreshHistory,
    HISTORY_REFRESH_MS
);

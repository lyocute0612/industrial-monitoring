import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "gateway.json"


def load_gateway_config(path=None):
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Gateway configuration not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8-sig") as file:
        config = json.load(file)

    required_fields = {
        "shct3_port",
        "soil_port",
        "baudrate",
        "tcp_host",
        "tcp_port",
        "reconnect_interval",
    }

    missing = required_fields - config.keys()

    if missing:
        raise ValueError(
            f"Missing gateway configuration fields: {sorted(missing)}"
        )

    for key in ("shct3_port", "soil_port", "tcp_host"):
        if not isinstance(config[key], str) or not config[key].strip():
            raise ValueError(f"{key} must be a non-empty string")

    if config["shct3_port"] == config["soil_port"]:
        raise ValueError("SHCT3 and Soil must use different COM ports")

    if type(config["baudrate"]) is not int or config["baudrate"] <= 0:
        raise ValueError("baudrate must be a positive integer")

    if type(config["tcp_port"]) is not int or not 1 <= config["tcp_port"] <= 65535:
        raise ValueError("tcp_port must be between 1 and 65535")

    interval = config["reconnect_interval"]

    if type(interval) not in (int, float) or interval <= 0:
        raise ValueError("reconnect_interval must be a positive number")

    return config
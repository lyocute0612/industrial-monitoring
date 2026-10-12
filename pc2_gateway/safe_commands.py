
def build_safe_command_result(message: dict) -> dict | None:
    """Return a rejection response without accessing RS485 hardware."""
    if not isinstance(message, dict):
        return None

    if message.get("type") != "command":
        return None

    return {
        "type": "command_result",
        "command_id": message.get("command_id"),
        "command": message.get("command"),
        "sensor_id": message.get("sensor_id"),
        "register": message.get("register"),
        "value": message.get("value"),
        "success": False,
        "message": (
            "Hardware write commands are disabled "
            "during real-sensor testing"
        ),
    }

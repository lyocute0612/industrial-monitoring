from dataclasses import dataclass


@dataclass
class SHTC3Reading:
    humidity: float
    temperature: float


def decode_shtc3_registers(
    registers: list[int],
) -> SHTC3Reading:

    if len(registers) < 2:
        raise ValueError(
            "SHTC3 requires at least 2 registers"
        )

    humidity_raw = registers[0]
    temperature_raw = registers[1]

    humidity = humidity_raw / 10.0
    temperature = temperature_raw / 10.0

    return SHTC3Reading(
        humidity=humidity,
        temperature=temperature,
    )
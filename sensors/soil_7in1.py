from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Soil7In1Reading:
    moisture: float
    temperature: float
    conductivity: int
    ph: float
    nitrogen: int
    phosphate: int
    potassium: int
    salinity: int
    tds: int


def decode_soil_7in1_registers(
    registers: Sequence[int],
) -> Soil7In1Reading:
    if len(registers) != 9:
        raise ValueError(
            f"Soil 7-in-1 requires 9 registers, got {len(registers)}"
        )

    return Soil7In1Reading(
        moisture=registers[0] / 10.0,
        temperature=registers[1] / 10.0,
        conductivity=registers[2],
        ph=registers[3] / 10.0,
        nitrogen=registers[4],
        phosphate=registers[5],
        potassium=registers[6],
        salinity=registers[7],
        tds=registers[8],
    )
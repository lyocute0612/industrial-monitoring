from sensors.soil_7in1 import decode_soil_7in1_registers


def test_soil_7in1_values_from_report():
    registers = [
        0x0000,  # moisture
        0x00F3,  # temperature = 243
        0x0000,  # conductivity
        0x0046,  # pH = 70
        0x0000,  # nitrogen
        0x0000,  # phosphate
        0x0000,  # potassium
        0x0000,  # salinity
        0x0000,  # TDS
    ]

    reading = decode_soil_7in1_registers(registers)

    assert reading.moisture == 0.0
    assert reading.temperature == 24.3
    assert reading.conductivity == 0
    assert reading.ph == 7.0
    assert reading.nitrogen == 0
    assert reading.phosphate == 0
    assert reading.potassium == 0
    assert reading.salinity == 0
    assert reading.tds == 0


def test_soil_7in1_requires_exactly_9_registers():
    try:
        decode_soil_7in1_registers([1, 2, 3])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")
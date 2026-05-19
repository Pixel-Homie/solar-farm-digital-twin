from src.core.datatypes import CircuitDescription, IrradianceData
from src.simulation.calculator import EnergyCalculator


def test_energy_calculation():
    calc = EnergyCalculator()
    calc.require_wired_to_battery = False
    calc.base_load_kw = 0.0

    circuit_desc = CircuitDescription(
        circuit_id="test",
        panels=[{
            "instance_id": "p1",
            "panel_id": "p1",
            "rated_power_w": 1000.0,
            "quantity": 1,
        }],
        batteries=[],
        connections=[],
    )

    mock_data = IrradianceData(0, 0, 2020, 2020, [
        {"timestamp": "20200101:1200", "irradiance_wm2": 500.0, "temperature_c": 25.0},
        {"timestamp": "20200101:1300", "irradiance_wm2": 1000.0, "temperature_c": 25.0},
    ])

    res = calc.compute(mock_data, circuit_desc)

    # 500W/m2 -> 50% rated * 1000W * (1 - 0.14 loss) = 430W
    assert abs(res.hourly_production[0]["power_w"] - 430.0) < 0.1
    # 1000W/m2 -> 100% rated * 1000W * (1 - 0.14) = 860W
    assert abs(res.hourly_production[1]["power_w"] - 860.0) < 0.1
    assert res.effective_pv_w == 1000.0

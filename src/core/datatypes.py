from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class CircuitDescription:
    circuit_id: str
    panels: List[dict]  # {'panel_id': str, 'rated_power_w': float, 'quantity': int}
    batteries: List[dict]  # {'battery_id': str, 'capacity_wh': float, 'type': str}
    connections: List[dict]

@dataclass
class PvgisYearBounds:
    year_min: int
    year_max: int
    radiation_db: str

@dataclass
class SimulationParams:
    coordinates: List[tuple]  # list of (lat, lon)
    start_year: int
    end_year: int
    simulation_time: float

@dataclass
class GraphSelection:
    generate_graphs: bool
    selected_types: List[str]

@dataclass
class IrradianceData:
    lat: float
    lon: float
    start_year: int
    end_year: int
    hourly_values: List[dict]  # {'timestamp': str, 'irradiance_wm2': float, 'temperature_c': float}

@dataclass
class EnergyResult:
    hourly_production: List[dict]
    total_energy_kwh: float
    peak_power_w: float
    capacity_factor: float
    total_load_kwh: float = 0.0
    total_self_consumed_kwh: float = 0.0
    energy_from_battery_kwh: float = 0.0
    curtailed_kwh: float = 0.0
    unserved_kwh: float = 0.0
    effective_pv_w: float = 0.0
    battery_capacity_wh: float = 0.0
    topology_summary: dict = field(default_factory=dict)

@dataclass
class SimulationResult:
    energy_result: EnergyResult
    formatted_text: str
    graphs_generated: bool

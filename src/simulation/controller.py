from src.core.datatypes import CircuitDescription, SimulationParams, GraphSelection, SimulationResult
from src.core.preferences import AppPreferences
from src.acquisition.client import PVGISClient
from src.simulation.calculator import EnergyCalculator
from src.simulation.formatter import GraphGenerator, ResultFormatter


class SimulationController:
    def __init__(self):
        self.pvgis_client = PVGISClient()
        self.energy_calculator = EnergyCalculator()
        self.graph_generator = GraphGenerator()
        self.apply_preferences()

    def apply_preferences(self, prefs: AppPreferences = None):
        prefs = prefs or AppPreferences.load()
        self.pvgis_client.timeout_sec = prefs.pvgis_timeout_sec
        self.energy_calculator.system_loss_factor = prefs.system_loss_pct / 100.0
        self.energy_calculator.battery_idle_loss_pct = prefs.battery_idle_loss_pct
        self.energy_calculator.base_load_kw = prefs.base_load_kw
        self.energy_calculator.load_profile = prefs.load_profile
        self.energy_calculator.require_wired_to_battery = prefs.require_wired_to_battery
        self.energy_calculator.charge_efficiency = prefs.battery_charge_efficiency
        self.energy_calculator.discharge_efficiency = prefs.battery_discharge_efficiency
        self.energy_calculator.max_c_rate_per_hour = prefs.battery_max_c_rate

    def run(self, circuit_desc: CircuitDescription, params: SimulationParams, graph_sel: GraphSelection) -> tuple:
        prefs = AppPreferences.load()
        self.apply_preferences(prefs)

        lat, lon = params.coordinates[0]
        irradiance_data = self.pvgis_client.fetch_irradiance(
            lat=lat, lon=lon,
            start_year=params.start_year,
            end_year=params.end_year,
            loss_pct=prefs.system_loss_pct,
        )

        energy_result = self.energy_calculator.compute(irradiance_data, circuit_desc)

        # 3. Format and Generate Graphs
        formatted_text = ResultFormatter.format(energy_result)
        graphs = self.graph_generator.generate_figures(energy_result, graph_sel)

        sim_result = SimulationResult(
            energy_result=energy_result,
            formatted_text=formatted_text,
            graphs_generated=graph_sel.generate_graphs
        )

        return sim_result, graphs

from src.core.datatypes import CircuitDescription

class SolarPanel:
    def __init__(self, rated_power: float, efficiency: float):
        self.rated_power = rated_power
        self.efficiency = efficiency

class Battery:
    def __init__(self, capacity_wh: float):
        self.capacity_wh = capacity_wh
        self.max_charge = capacity_wh

class CircuitModel:
    def __init__(self):
        self.panels = []
        self.batteries =[]

    def build_from_description(self, desc: CircuitDescription):
        self.panels.clear()
        self.batteries.clear()
        for p in desc.panels:
            for _ in range(p.get('quantity', 1)):
                eff = float(p.get('efficiency', 0.18))
                self.panels.append(SolarPanel(p['rated_power_w'], eff))
        for b in desc.batteries:
            self.batteries.append(Battery(b['capacity_wh']))

    def get_total_rated_power(self) -> float:
        return sum(p.rated_power for p in self.panels)

    def get_total_storage_capacity(self) -> float:
        return sum(b.capacity_wh for b in self.batteries)

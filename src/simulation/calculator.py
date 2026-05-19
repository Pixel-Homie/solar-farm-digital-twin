from datetime import datetime

from src.core.datatypes import CircuitDescription, EnergyResult, IrradianceData
from src.simulation.topology import analyze_topology


def _parse_hour(ts: str) -> int:
    try:
        return datetime.strptime(ts.strip(), "%Y%m%d:%H%M").hour
    except Exception:
        return 12


def _hourly_load_w(base_kw: float, timestamp: str, profile: str) -> float:
    """Site consumption for one hour (W)."""
    base_w = max(0.0, base_kw) * 1000.0
    if base_w <= 0:
        return 0.0
    profile = (profile or "constant").lower()
    hour = _parse_hour(timestamp)
    if profile == "evening_peak":
        if 17 <= hour <= 22:
            return base_w * 1.55
        if 7 <= hour <= 9:
            return base_w * 1.15
        if 0 <= hour <= 6:
            return base_w * 0.35
        return base_w * 0.75
    if profile == "daytime_peak":
        if 9 <= hour <= 17:
            return base_w * 1.35
        if 18 <= hour <= 21:
            return base_w * 0.9
        return base_w * 0.45
    return base_w


class EnergyCalculator:
    def __init__(self):
        self.system_loss_factor = 0.14
        self.battery_idle_loss_pct = 0.0
        self.base_load_kw = 2.0
        self.load_profile = "constant"
        self.require_wired_to_battery = True
        self.charge_efficiency = 0.95
        self.discharge_efficiency = 0.95
        self.max_c_rate_per_hour = 0.5

    def compute(
        self,
        data: IrradianceData,
        circuit_desc: CircuitDescription,
    ) -> EnergyResult:
        topo = analyze_topology(
            circuit_desc.panels,
            circuit_desc.batteries,
            circuit_desc.connections,
            require_battery_link=self.require_wired_to_battery,
        )
        prated = topo["effective_pv_w"]
        capmax = topo["effective_battery_wh"]
        lsys = self.system_loss_factor

        idle_per_hour = 0.0
        if capmax > 0 and self.battery_idle_loss_pct > 0:
            idle_per_hour = capmax * (self.battery_idle_loss_pct / 100.0) / 24.0

        max_charge_wh = capmax * self.max_c_rate_per_hour if capmax > 0 else 0.0
        max_discharge_wh = max_charge_wh

        soc = 0.0
        results = []
        total_gen_kwh = 0.0
        total_load_kwh = 0.0
        total_self_kwh = 0.0
        total_from_battery_kwh = 0.0
        total_curtailed_kwh = 0.0
        total_unserved_kwh = 0.0
        peak_power = 0.0

        for hour in data.hourly_values:
            gi = hour["irradiance_wm2"]
            ts = hour["timestamp"]

            gen_w = (gi / 1000.0) * prated * (1.0 - lsys) if prated > 0 else 0.0
            load_w = _hourly_load_w(self.base_load_kw, ts, self.load_profile)

            gen_wh = gen_w
            load_wh = load_w
            surplus_wh = max(0.0, gen_wh - load_wh)
            deficit_wh = max(0.0, load_wh - gen_wh)

            self_consumed_wh = min(gen_wh, load_wh)
            from_battery_wh = 0.0
            curtailed_wh = 0.0
            unserved_wh = 0.0

            if surplus_wh > 0 and capmax > 0:
                charge_wh = min(
                    surplus_wh * self.charge_efficiency,
                    max_charge_wh,
                    capmax - soc,
                )
                charge_wh = max(0.0, charge_wh)
                soc += charge_wh
                curtailed_wh = surplus_wh - (charge_wh / self.charge_efficiency)
                curtailed_wh = max(0.0, curtailed_wh)
            elif surplus_wh > 0:
                curtailed_wh = surplus_wh

            if deficit_wh > 0 and capmax > 0 and soc > 0:
                deliver_wh = min(
                    deficit_wh,
                    soc,
                    max_discharge_wh / self.discharge_efficiency,
                )
                deliver_wh = max(0.0, deliver_wh)
                from_battery_wh = deliver_wh * self.discharge_efficiency
                soc -= deliver_wh
                unserved_wh = deficit_wh - from_battery_wh
            elif deficit_wh > 0:
                unserved_wh = deficit_wh

            if idle_per_hour > 0 and capmax > 0:
                soc = max(0.0, soc - idle_per_hour)

            results.append({
                "timestamp": ts,
                "power_w": gen_w,
                "load_w": load_w,
                "net_w": gen_w - load_w,
                "soc": soc,
                "curtailed_w": curtailed_wh,
                "unserved_w": unserved_wh,
            })

            total_gen_kwh += gen_wh / 1000.0
            total_load_kwh += load_wh / 1000.0
            total_self_kwh += self_consumed_wh / 1000.0
            total_from_battery_kwh += from_battery_wh / 1000.0
            total_curtailed_kwh += curtailed_wh / 1000.0
            total_unserved_kwh += unserved_wh / 1000.0
            if gen_w > peak_power:
                peak_power = gen_w

        capacity_factor = 0.0
        if prated > 0 and len(results) > 0:
            theoretical_max_kwh = (prated / 1000.0) * len(results)
            capacity_factor = (total_gen_kwh / theoretical_max_kwh) * 100.0

        return EnergyResult(
            hourly_production=results,
            total_energy_kwh=total_gen_kwh,
            peak_power_w=peak_power,
            capacity_factor=capacity_factor,
            total_load_kwh=total_load_kwh,
            total_self_consumed_kwh=total_self_kwh,
            energy_from_battery_kwh=total_from_battery_kwh,
            curtailed_kwh=total_curtailed_kwh,
            unserved_kwh=total_unserved_kwh,
            effective_pv_w=prated,
            battery_capacity_wh=capmax,
            topology_summary=topo,
        )

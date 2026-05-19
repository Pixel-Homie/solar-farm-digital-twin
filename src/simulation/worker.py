from PyQt5.QtCore import QThread, pyqtSignal

from src.core.datatypes import CircuitDescription, GraphSelection, SimulationParams
from src.core.exceptions import SolarTwinError
from src.simulation.controller import SimulationController


class SimulationWorker(QThread):
    progress = pyqtSignal(str)
    finished_ok = pyqtSignal(object, list)
    failed = pyqtSignal(object)

    def __init__(
        self,
        controller: SimulationController,
        circuit: CircuitDescription,
        params: SimulationParams,
        graph_sel: GraphSelection,
        parent=None,
    ):
        super().__init__(parent)
        self._controller = controller
        self._circuit = circuit
        self._params = params
        self._graph_sel = graph_sel

    def run(self):
        try:
            self.progress.emit("Fetching PVGIS data and computing energy…")
            sim_result, figures = self._controller.run(
                self._circuit, self._params, self._graph_sel
            )
            self.finished_ok.emit(sim_result, figures)
        except SolarTwinError as e:
            self.failed.emit(e)
        except Exception as e:
            self.failed.emit(e)

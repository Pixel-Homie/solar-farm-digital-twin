import sys
import os
import traceback

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")

def log(msg):
    print(msg, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

open(LOG, "w").close()
log("=== DIAGNOSTIC START ===")
log(f"Python: {sys.version}")
log(f"CWD: {os.getcwd()}")

try:
    log("Step 1: importing QApplication...")
    from PyQt5.QtWidgets import QApplication, QMainWindow
    log("Step 1: OK")

    log("Step 2: creating QApplication...")
    app = QApplication(sys.argv)
    log("Step 2: OK")

    log("Step 3: creating bare QMainWindow...")
    w = QMainWindow()
    w.setWindowTitle("PyQt5 Bare Test")
    w.resize(400, 200)
    log("Step 3: OK")

    log("Step 4: calling show()...")
    w.show()
    log("Step 4: OK — a window should be visible now")

    log("Step 5: event loop for 3 seconds...")
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(3000, app.quit)
    app.exec_()
    log("Step 5: event loop exited cleanly")

except Exception as e:
    log(f"EXCEPTION:\n{traceback.format_exc()}")
    sys.exit(1)

log("\n--- Testing src imports ---")

imports = [
    ("core.exceptions",       "from src.core.exceptions import SolarTwinError"),
    ("core.datatypes",        "from src.core.datatypes import SimulationParams"),
    ("acquisition.loader",    "from src.acquisition.loader import CatalogLoader"),
    ("acquisition.parser",    "from src.acquisition.parser import RequestBuilder"),
    ("acquisition.client",    "from src.acquisition.client import PVGISClient"),
    ("simulation.models",     "from src.simulation.models import CircuitModel"),
    ("simulation.calculator", "from src.simulation.calculator import EnergyCalculator"),
    ("simulation.formatter",  "from src.simulation.formatter import GraphGenerator"),
    ("simulation.controller", "from src.simulation.controller import SimulationController"),
    ("presentation.widgets",  "from src.presentation.widgets import TerminalView"),
    ("presentation.panels",   "from src.presentation.panels import CataloguePanel"),
    ("presentation.workspace","from src.presentation.workspace import WorkspaceCanvas"),
    ("presentation.dialogs",  "from src.presentation.dialogs import MapDialog"),
    ("presentation.title_bar", "from src.presentation.title_bar import AppChromeContainer"),
    ("presentation.main_window","from src.presentation.main_window import MainWindow"),
]

for name, stmt in imports:
    try:
        log(f"  importing {name}...")
        exec(stmt)
        log(f"  {name} OK")
    except Exception:
        log(f"  {name} FAILED:\n{traceback.format_exc()}")
        log("=== STOPPED ===")
        sys.exit(1)

log("\n--- Instantiating MainWindow ---")
try:
    from src.presentation.main_window import MainWindow
    app2 = QApplication.instance() or QApplication(sys.argv)
    log("  creating MainWindow()...")
    window = MainWindow()
    log("  MainWindow() OK")
    window.show()
    log("  show() OK")
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(5000, app2.quit)
    app2.exec_()
    log("  event loop exited cleanly")
except Exception:
    log(f"  FAILED:\n{traceback.format_exc()}")

log("=== DONE ===")
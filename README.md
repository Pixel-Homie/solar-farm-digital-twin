# ☀️ Solar Farm Digital Twin Platform

A free, open-source desktop simulation tool for photovoltaic (PV) systems,
built with Python and PyQt5. Design your solar farm visually, pick any location
on the map, and run a physics-based energy simulation powered by real historical
irradiance data from the PVGIS API.

> 4th Year IRIIA Project — Higher National School of Renewable Energies,
> Environment and Sustainable Development (ENSSRESD)  
> Authors: Redjechta Mustapha Aymen · Boukhezer Amar  
> Supervisor: Professor Athmani Samir · May 2026

---

## ✨ Features

- **Drag-and-drop circuit designer** — place solar panels and batteries on a canvas and connect them with wires
- **Interactive map** — click anywhere in North Africa or Europe to set the simulation location
- **PVGIS integration** — automatically fetches up to 19 years of real hourly irradiance data (SARAH3, 2005–2023)
- **Physics-based simulation** — hourly energy calculation with system losses, battery charge/discharge cycles, and site load
- **Circuit topology engine** — only panels wired to a battery contribute to production; disconnected components are flagged
- **Post-simulation charts** — PV output curve, battery state-of-charge, and monthly energy totals (exportable as PNG)
- **Result export** — saves a structured summary text file
- **Preferences system** — configure UI theme, simulation defaults, keyboard shortcuts, and chart options
- **Cross-platform** — runs on Windows and Linux without modification

---

## 🖥️ Screenshots

![Main Window](screen%20shots/workshop interface.png)
![Map Dialog](screen%20shots/select_farm_location.png)

 - You can find the other screen shots in the /screen shots folder

---

## 🚀 Getting Started

### Requirements

- Python 3.8 or higher
- Internet connection (for PVGIS data)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/solar-farm-digital-twin.git
cd solar-farm-digital-twin

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

### Dependencies

All listed in `requirements.txt`. Main ones:

| Package | Purpose |
|---|---|
| PyQt5 | GUI framework |
| Matplotlib | Chart generation |
| Requests | PVGIS API calls |

---

## 📖 How to Use

1. **Design your circuit** — drag panels and batteries from the catalogue onto the canvas. Connect them with wires using the Wire tool.
2. **Start the simulation** — click the **Simulate** button in the toolbar.
3. **Pick a location** — click on the map to set your farm's geographic coordinates.
4. **Configure the run** — set the year range, site load, and which charts to generate.
5. **View results** — charts and a text summary appear automatically after the simulation completes.

---

## 🏗️ Architecture

The application follows a strict three-layer architecture:
Presentation Layer   →   Simulation Layer   →   Data Acquisition Layer
(PyQt5 UI)              (Energy model,           (PVGIS API,
Topology engine)          CSV catalogue) 


All PVGIS API logic is isolated in a single module (`src/acquisition/client.py`), making it easy to update when new API versions are released.

---

## 🧪 Running Tests

```bash
python -m pytest tests/
```

---

## ⚡ Integration Test Result

| Parameter | Value |
|---|---|
| Location | 35.17°N, 5.01°E (northern Algeria) |
| Period | 2018–2023 (6 years) |
| Circuit | 1×250W + 2×400W panels · 2×10kWh + 1×5kWh batteries |
| Total PV Energy | 2,642.5 kWh |
| Peak Power | 332 W |
| Capacity Factor | 12.6% |
| Data fetch time | < 5 seconds |

---

## 🗺️ Roadmap

- [ ] Temperature coefficient model using T2m from PVGIS
- [ ] Multi-site simulation across distributed locations
- [ ] Economic analysis — LCOE and payback period
- [ ] PDF report export from within the application
- [ ] Grid-connected mode with net-billing simulation

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [PVGIS](https://joint-research-centre.ec.europa.eu/pvgis-photovoltaic-geographical-information-system_en) — European Commission Joint Research Centre
- [SARAH3 Dataset](https://doi.org/10.5676/EUM_SAF_CM/SARAH/V003) — CM SAF / EUMETSAT
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) — Riverbank Computing
- [Matplotlib](https://matplotlib.org/) — Hunter, J.D. (2007)
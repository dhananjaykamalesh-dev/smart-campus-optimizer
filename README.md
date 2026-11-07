# 🏫 Graph-Based Smart Campus Optimization System

> **Academic Project · Discrete Mathematics · November 2026**
> Intelligent navigation, scheduling, and resource allocation powered by graph theory and constraint programming.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red?logo=streamlit)](https://streamlit.io)
[![OR-Tools](https://img.shields.io/badge/Google%20OR--Tools-CP--SAT-green)](https://developers.google.com/optimization)
[![Tests](https://img.shields.io/badge/Tests-40%20passing-brightgreen)](tests/)
[![CI](https://github.com/dhananjaykamalesh-dev/smart-campus-optimizer/actions/workflows/tests.yml/badge.svg)](https://github.com/dhananjaykamalesh-dev/smart-campus-optimizer/actions)

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Features](#-features)
3. [Architecture](#-architecture)
4. [Installation](#-installation)
5. [Usage](#-usage)
6. [Testing](#-testing)
7. [Screenshots](#-screenshots)
8. [Limitations](#-limitations)
9. [Future Scope](#-future-scope)
10. [Academic Context](#-academic-context)

---

## 🔍 Project Overview

This system applies **Discrete Mathematics** concepts — specifically graph theory and combinatorial optimization — to solve three real-world campus management problems:

| Module | Problem | Algorithm / Method |
|--------|---------|-------------------|
| 🗺️ Campus Navigation | Find shortest walking route between buildings | Dijkstra's Algorithm, A\* Search |
| 📅 Classroom Scheduling | Assign courses to rooms and time slots without conflicts | Constraint Programming (CP-SAT) |
| 📊 Resource Allocation | Measure how efficiently rooms and facilities are being used | Utilization metrics, greedy allocation |

**Why graph theory?**
The campus is modeled as a weighted undirected graph $G = (V, E, w)$ where:
- $V$ = buildings (nodes)
- $E$ = walking paths between buildings (edges)
- $w : E \to \mathbb{R}^+$ = path distance in metres (weights)

All routing algorithms run on this graph, guaranteeing mathematically optimal shortest paths.

---

## ✨ Features

### Module 1 — Campus Navigation
- 🗺️ Interactive campus map built with Plotly
- ⚡ **Dijkstra vs A\*** live benchmark — compare route, distance, nodes explored, and computation time
- ♿ **Accessibility mode** — routes only via accessible (step-free) paths
- 🚧 **Pathway obstruction simulator** — block any path (maintenance/rain/construction) and see automatic rerouting with:
  - Original route shown as a ghost trace
  - Detour route highlighted in red
  - Distance difference and extra travel time
- 📥 CSV export of any calculated route

### Module 2 — Classroom Scheduling
- 🧩 **CP-SAT constraint solver** (Google OR-Tools) builds a conflict-free timetable
- Hard constraints enforced:
  - No room used by two courses at the same time
  - No instructor teaching two courses at the same time
  - Room capacity ≥ course enrolment
  - Lab courses assigned only to lab rooms
- 🏥 **Room unavailability simulator** — close any room and instantly see:
  - Affected courses
  - Top alternative room recommendations (ranked by walking distance + seat waste)
- 🔧 **Minimal perturbation repair** — fix the timetable by moving as few courses as possible
- 📥 CSV export of the full timetable

### Module 3 — Resource Allocation
- 📊 Room utilization percentages with color-coded bar chart
- 🔴🟡🟢 Traffic-light thresholds: under-utilized (<50%), normal, over-utilized (>90%)
- 🪑 Seat waste analysis (capacity − actual enrolment)
- 📋 Idle room identification
- 📥 CSV export of the full utilization report

### Sidebar Dashboard
- Live campus scale metrics: buildings, paths, rooms, courses, instructors, time slots
- Accessibility mode status badge

---

## 🏗️ Architecture

```
smart-campus-optimizer/
│
├── app.py                      ← Main Streamlit application (single entry point)
│
├── src/                        ← All Python source modules
│   ├── navigation/
│   │   ├── graph_builder.py    ← Loads CSVs → builds NetworkX graph
│   │   └── pathfinder.py       ← Dijkstra, A*, rerouting logic
│   ├── scheduling/
│   │   └── timetable_solver.py ← CP-SAT constraint solver + repair
│   ├── allocation/
│   │   └── resource_manager.py ← Utilization metrics & room allocation
│   └── utils/
│       └── visualizer.py       ← Plotly chart builders
│
├── data/                       ← Local CSV datasets (no database needed)
│   ├── buildings.csv           ← 10 campus buildings with GPS coordinates
│   ├── paths.csv               ← 15 walking paths with distances & accessibility flags
│   ├── rooms.csv               ← 7 classrooms/labs with capacity
│   ├── courses.csv             ← 7 courses with enrolment & lab requirement
│   ├── instructors.csv         ← 5 faculty members with available time slots
│   └── time_slots.csv          ← 15 slots across Monday–Friday
│
├── tests/                      ← Automated pytest test suite
│   ├── conftest.py             ← Path setup so tests can import src/
│   ├── test_navigation.py      ← 6 navigation tests
│   ├── test_scheduling.py      ← 5 scheduling tests
│   ├── test_ui_utilities.py    ← 3 UI utility tests
│   ├── test_dynamic_features.py← 5 dynamic feature tests (Phase B)
│   └── test_app_smoke.py       ← 5 Streamlit smoke tests (Phase C)
│
├── docs/
│   ├── architecture.md         ← System design & component diagram
│   ├── algorithms.md           ← Full mathematical treatment of all algorithms
│   └── viva_answers.md         ← 15 Q&A for academic viva/defence
│
├── .github/
│   └── workflows/
│       └── tests.yml           ← GitHub Actions CI (auto-runs tests on push)
│
├── requirements.txt            ← All Python dependencies
├── conftest.py                 ← Root-level pytest path configuration
├── run.bat                     ← One-click launcher for Windows
└── run.sh                      ← One-click launcher for Mac/Linux
```

### Data Flow Diagram

```
CSV Files (data/)
      │
      ▼
graph_builder.py ──── builds ──▶ NetworkX Graph G=(V,E,w)
      │                                  │
      │                           pathfinder.py
      │                          (Dijkstra / A*)
      │                                  │
      ├──────────────────────────────────┘
      │
      ▼
timetable_solver.py ─── CP-SAT ──▶ Schedule (room, slot, instructor)
      │
      ▼
resource_manager.py ──── metrics ──▶ Utilization report
      │
      ▼
visualizer.py ────── Plotly ──▶ Charts & maps
      │
      ▼
app.py ──── Streamlit ──▶ Interactive web dashboard
```

---

## 💻 Installation

### Prerequisites
- **Python 3.10 or higher** (tested on Python 3.12.10)
- **Git**
- A terminal (PowerShell on Windows, Terminal on Mac/Linux)

### Step-by-Step

```bash
# 1. Clone the repository
git clone https://github.com/dhananjaykamalesh-dev/smart-campus-optimizer.git

# 2. Navigate into the project folder
cd smart-campus-optimizer

# 3. (Recommended) Create a virtual environment
python -m venv venv

# 4. Activate the virtual environment
#    On Windows:
venv\Scripts\activate
#    On Mac/Linux:
source venv/bin/activate

# 5. Install all dependencies
pip install -r requirements.txt

# 6. Run the app
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

> **Windows quick start:** Double-click `run.bat` — it does steps 6 automatically.

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Make sure you ran `pip install -r requirements.txt` |
| `streamlit: command not found` | Try `python -m streamlit run app.py` |
| Port 8501 already in use | Run `streamlit run app.py --server.port 8502` |
| OR-Tools not installing | Make sure Python is 3.10–3.12 (OR-Tools has no 3.13 wheels yet) |

---

## 🚀 Usage

Once the app is running at `http://localhost:8501`:

### Tab 1 — Campus Navigation
1. Choose **source** and **destination** buildings from the dropdowns
2. Toggle **Accessibility Mode** to restrict routes to step-free paths
3. Click **Find Shortest Route** — the map highlights your route in blue
4. Expand **Dijkstra vs A\* Benchmark** to see the comparison table
5. Use **Pathway Obstruction Simulator** to block a path and watch the reroute
6. Click **Download Route as CSV** to save the route

### Tab 2 — Classroom Scheduling
1. Click **Generate Timetable** — CP-SAT solver runs (≤10 seconds)
2. View the full timetable table
3. Use **Room Unavailability Simulator** to close a room
4. See affected courses and recommended alternatives
5. Click **Repair Timetable (Minimal Change)** to auto-fix the schedule
6. Click **Download Timetable as CSV** to save

### Tab 3 — Resource Allocation
1. View the color-coded utilization bar chart
2. Check the seat waste analysis table
3. See idle rooms that could be repurposed
4. Click **Download Utilization Report as CSV**

### Tab 4 — Discrete Math Theory
Quick reference for the algorithms and formulas used in the project.

---

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run with Coverage Report
```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

### Run a Specific Test File
```bash
python -m pytest tests/test_navigation.py -v
python -m pytest tests/test_scheduling.py -v
python -m pytest tests/test_app_smoke.py -v
```

### Expected Output
```
tests/test_app_smoke.py::test_app_starts_without_exception    PASSED
tests/test_app_smoke.py::test_app_title_present               PASSED
tests/test_app_smoke.py::test_four_tabs_present               PASSED
tests/test_app_smoke.py::test_sidebar_has_content             PASSED
tests/test_app_smoke.py::test_no_missing_data_files           PASSED
tests/test_dynamic_features.py::test_blocked_subgraph_generation  PASSED
...
27 passed in X.XXs
```

### Continuous Integration
Every push to `main` automatically triggers the test suite on GitHub Actions.
View the latest CI run: [GitHub Actions](https://github.com/dhananjaykamalesh-dev/smart-campus-optimizer/actions)

---

## 📸 Screenshots

> **To add screenshots:** Run the app, take screenshots of each tab, save them to `docs/screenshots/`, and update the paths below.

| Module | Screenshot |
|--------|-----------|
| Navigation Map | *(run the app and screenshot Tab 1)* |
| Dijkstra vs A* Comparison | *(screenshot the benchmark table)* |
| Pathway Obstruction | *(screenshot the detour map)* |
| Timetable | *(screenshot the generated schedule)* |
| Utilization Chart | *(screenshot the color-coded bars)* |

---

## ⚠️ Limitations

1. **Small dataset** — Only 10 buildings and 7 courses. Real campuses have hundreds.
2. **No real GPS** — Building coordinates are approximate/synthetic, not real GPS positions.
3. **Simplified graph** — All edges are straight-line distances; real paths curve and have elevation.
4. **No real-time data** — Room occupancy, weather, and maintenance data are simulated, not live.
5. **No user authentication** — Anyone with access can modify the timetable. No login system.
6. **Static demand** — The scheduling solver uses fixed course data; it does not adapt to changing enrolment.
7. **Single-objective routing** — Routes minimize distance only, not time of day, weather, or crowd density.

---

## 🔭 Future Scope

1. **Real-time IoT integration** — Connect to door sensors to track actual room occupancy.
2. **Mobile app** — React Native front end with live indoor navigation using BLE beacons.
3. **Larger campus graph** — Import real OpenStreetMap data for actual campus layout.
4. **Multi-objective routing** — Balance distance vs. weather vs. crowd density using Pareto optimization.
5. **Dynamic enrolment** — Re-run the CP-SAT solver automatically when students add/drop courses.
6. **Demand prediction** — Use historical booking data to predict room demand (ML baseline model).
7. **Energy optimization** — Schedule classes to minimize the number of buildings needing heating/cooling.
8. **Accessibility audit** — Generate a report of paths that still lack accessibility features.

---

## 🎓 Academic Context

| Item | Detail |
|------|--------|
| Course | Discrete Mathematics |
| Project Type | Graph Theory Application |
| Key Concepts | Weighted graphs, shortest path algorithms, constraint satisfaction, optimization |
| Algorithms | Dijkstra ($O((V+E)\log V)$), A\* with Euclidean heuristic, CP-SAT (NP-complete scheduling) |
| Data Structures | Adjacency list (NetworkX), priority queue (heapq), constraint model |
| Language | Python 3.12 |
| Framework | Streamlit (web UI), Google OR-Tools (solver), NetworkX (graph), Plotly (charts) |

---

*Built with ❤️ for academic excellence — no paid APIs, no cloud services, runs entirely on your laptop.*

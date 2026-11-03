# 🏫 Graph-Based Smart Campus Optimization System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red.svg)](https://streamlit.io/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.0%2B-orange.svg)](https://networkx.org/)
[![OR--Tools](https://img.shields.io/badge/OR--Tools-CP--SAT-green.svg)](https://developers.google.com/optimization)
[![Tests](https://img.shields.io/badge/Pytest-17%2F17%20Passing-brightgreen.svg)](tests/)

A complete academic project applying **Discrete Mathematics** (Graph Theory, Heuristic Search, Constraint Satisfaction, and Resource Matching) to optimize campus operations.

---

## 🎯 System Modules & Features

### 📍 Module 1: Campus Navigation (Graph Theory)
- Models campus buildings and walkways as an undirected weighted graph $G = (V, E, w)$.
- Computes optimal paths using **Dijkstra's Algorithm** and **A\* Search**.
- Utilizes Euclidean distance as a mathematically proven **admissible heuristic** ($h(n) \le h^*(n)$).
- **Algorithm Benchmarking**: Live side-by-side performance metrics comparing Dijkstra vs. A* (distance, nodes explored, runtime in milliseconds).
- **Accessibility Subgraph**: Edge-induced subgraph filtering out stairs for wheelchair-friendly navigation with active mode indicator.
- **Plotly 2D Interactive Map**: Visualizes nodes, walkway connectivity, and highlighted routes.
- **Data Export**: 1-click CSV download of turn-by-turn route itineraries.

### 📅 Module 2: Classroom Scheduling (Constraint Satisfaction Problem)
- Formulates course timetabling as a Boolean CSP with variables $X_{c, r, s} \in \{0, 1\}$.
- Solved using **Google OR-Tools CP-SAT** in under 0.1 seconds.
- Enforces **hard propositional logic constraints**:
  - No course assigned more than once ($\sum_{r, s} X_{c,r,s} = 1$).
  - No room double-booking ($\sum_c X_{c,r,s} \le 1$).
  - No instructor clashes ($\sum_{c \in C_i} \sum_r X_{c,r,s} \le 1$).
  - Room capacity compliance ($\text{Capacity}(r) \ge \text{Enrolled}(c)$).
  - Specialized lab requirements ($\text{RequiresLab}(c) \implies \text{IsLab}(r)$).
- Minimizes wasted seats as an optimization objective.
- **Data Export**: 1-click CSV download of the conflict-free weekly schedule.

### 📊 Module 3: Space Allocation & Utilization Analytics
- Computes classroom seat utilization: $\text{Utilization Rate} = \frac{\text{Enrolled Students}}{\text{Room Capacity}} \times 100\%$.
- Classifies room allocations with clear threshold bands:
  - **Under-utilized (<50%)** (Amber)
  - **Optimal (50–90%)** (Teal)
  - **Near Peak (>90%)** (Coral/Red)
- Detects idle rooms that can be powered down to save campus energy.
- Generates interactive Plotly bar and grouped charts.
- **Data Export**: 1-click CSV download of space utilization analytics.

---

## 📂 Project Directory Structure

```
smart-campus-optimizer/
│
├── data/
│   ├── buildings.csv          # Vertices: ID, name, coordinates (x, y), category
│   ├── paths.csv              # Edges: source, target, distance_m, is_accessible, is_covered
│   ├── rooms.csv              # Classrooms: ID, capacity, building, lab equipment
│   ├── courses.csv            # Course demands: enrollment, instructor, lab flag
│   ├── instructors.csv        # Faculty details & department
│   └── time_slots.csv         # Weekly periods (Mon–Fri 09:00–15:00)
│
├── src/
│   ├── __init__.py
│   ├── navigation/
│   │   ├── __init__.py
│   │   ├── graph_builder.py   # Loads CSVs and constructs NetworkX Graph G = (V, E)
│   │   └── pathfinder.py      # Dijkstra, A*, and comparison benchmarking with timing
│   │
│   ├── scheduling/
│   │   ├── __init__.py
│   │   └── timetable_solver.py# CP-SAT constraint programming model for zero-conflict timetable
│   │
│   ├── allocation/
│   │   ├── __init__.py
│   │   └── resource_manager.py# Calculates room utilization % and detects idle rooms
│   │
│   └── utils/
│       ├── __init__.py
│       └── visualizer.py      # Plotly interactive 2D maps and utilization charts
│
├── tests/
│   ├── __init__.py
│   ├── test_navigation.py     # Dijkstra vs A* correctness, unreachable nodes, ramp filters
│   ├── test_scheduling.py     # Hard constraint validation (zero room/teacher overlaps)
│   ├── test_allocation.py     # Space utilization bounds and idle room checks
│   └── test_ui_utilities.py   # Benchmark tests, graph summary metrics, and CSV exports
│
├── docs/
│   ├── architecture.md        # Modular architecture, components, and design decisions
│   ├── algorithms.md          # Discrete mathematics theory (Dijkstra, A*, heuristics, CP-SAT)
│   ├── viva_answers.md        # Viva interview guide with 11 questions & simple answers
│   └── team_collaboration_guide.md # 1-click setup guide for team members
│
├── app.py                     # Streamlit multi-tab user interface with benchmarks and CSV downloads
├── conftest.py                # Pytest search path configuration
├── requirements.txt           # Python dependencies
├── run.bat                    # 1-click Windows launcher
├── run.sh                     # 1-click Mac/Linux launcher
└── README.md                  # Project overview & manual
```

---

## 🚀 Quickstart: Installation & Running

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Web Application
```bash
streamlit run app.py
```
Or simply double-click `run.bat` (Windows).

### 4. Run Automated Unit Tests
```bash
pytest tests/ -v
```
All 17 tests will run and pass in ~2 seconds.

---

## 🎓 Academic Defense & Viva Resources

- **Mathematical Foundations & Proofs**: [`docs/algorithms.md`](docs/algorithms.md)
- **Architecture & System Design**: [`docs/architecture.md`](docs/architecture.md)
- **Top Viva / Presentation Questions**: [`docs/viva_answers.md`](docs/viva_answers.md)
- **Team Collaboration Guide**: [`docs/team_collaboration_guide.md`](docs/team_collaboration_guide.md)

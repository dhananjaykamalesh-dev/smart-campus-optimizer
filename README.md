# 🏫 Graph-Based Smart Campus Optimization System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red.svg)](https://streamlit.io/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.0%2B-orange.svg)](https://networkx.org/)
[![OR--Tools](https://img.shields.io/badge/OR--Tools-CP--SAT-green.svg)](https://developers.google.com/optimization)
[![Tests](https://img.shields.io/badge/Pytest-14%2F14%20Passing-brightgreen.svg)](tests/)

A complete academic project applying **Discrete Mathematics** (Graph Theory, Heuristic Search, Constraint Satisfaction, and Resource Matching) to optimize campus operations.

---

## 🎯 System Modules

### 📍 Module 1: Campus Navigation (Graph Theory)
- Models campus buildings and walkways as an undirected weighted graph $G = (V, E, w)$.
- Computes optimal paths using **Dijkstra's Algorithm** and **A\* Search**.
- Utilizes Euclidean distance as a mathematically proven **admissible heuristic** ($h(n) \le h^*(n)$).
- **Accessibility Subgraph**: Edge-induced subgraph filtering out stairs for wheelchair-friendly navigation.
- **Plotly 2D Interactive Map**: Visualizes nodes, walkway connectivity, and highlighted routes.

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

### 📊 Module 3: Space Allocation & Utilization Analytics
- Computes classroom seat utilization: $\text{Utilization Rate} = \frac{\text{Enrolled Students}}{\text{Room Capacity}} \times 100\%$.
- Classifies room allocations into **Under-utilized (<50%)**, **Optimal (50–90%)**, and **Near Peak (>90%)**.
- Detects idle rooms that can be powered down to save energy and operational costs.
- Generates interactive Plotly bar and grouped charts.

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
│   │   └── pathfinder.py      # Dijkstra and A* pathfinding algorithms with metrics
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
│   └── test_allocation.py     # Space utilization bounds and idle room checks
│
├── docs/
│   ├── architecture.md        # Modular architecture, components, and design decisions
│   ├── algorithms.md          # Discrete mathematics theory (Dijkstra, A*, heuristics, CP-SAT)
│   └── viva_answers.md        # Viva interview guide with 11 questions & simple answers
│
├── app.py                     # Streamlit multi-tab user interface
├── conftest.py                # Pytest search path configuration
├── requirements.txt           # Python dependencies
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
Open your browser at `http://localhost:8501`.

### 4. Run Automated Unit Tests
```bash
pytest tests/ -v
```
All 14 tests will run and pass in ~1.5 seconds.

---

## 🎓 Academic Defense & Viva Resources

- **Mathematical Foundations & Proofs**: [`docs/algorithms.md`](docs/algorithms.md)
- **Architecture & System Design**: [`docs/architecture.md`](docs/architecture.md)
- **Top Viva / Presentation Questions**: [`docs/viva_answers.md`](docs/viva_answers.md)

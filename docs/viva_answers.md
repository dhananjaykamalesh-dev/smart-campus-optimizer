# Viva Preparation & Presentation Q&A Guide

This guide contains the most critical viva and presentation questions for this project, paired with concise, confident, and beginner-friendly answers.

---

### Q1: What is the main objective of your project?
**Answer:**
> "Our project optimizes physical campus operations using core Discrete Mathematics concepts:
> 1. Graph theory and pathfinding algorithms (Dijkstra and A*) for intelligent campus navigation and accessibility routing.
> 2. Propositional logic and Constraint Programming (Google OR-Tools CP-SAT) for automated, conflict-free classroom timetabling.
> 3. Space allocation analytics to compute classroom utilization and eliminate wasted energy and capacity."

---

### Q2: How is the campus represented mathematically?
**Answer:**
> "The campus is modeled as an undirected, weighted graph $G = (V, E, w)$:
> - **Vertices ($V$)**: 10 campus buildings with 2D Cartesian coordinates $(x, y)$.
> - **Edges ($E$)**: Walkways connecting adjacent buildings.
> - **Weights ($w$)**: Physical walking distance in meters, which are strictly positive ($w > 0$)."

---

### Q3: What is the difference between Dijkstra's algorithm and the A* algorithm?
**Answer:**
> - "Dijkstra is an **uninformed search**: it expands equally in all directions based solely on the distance traveled so far ($g(n)$).
> - A* is an **informed heuristic search**: it directs its search toward the target using an evaluation function $f(n) = g(n) + h(n)$, where $h(n)$ estimates the remaining distance to the goal.
> - Both return the exact same optimal distance, but A* explores fewer vertices and is faster on large maps."

---

### Q4: How does your UI empirically demonstrate that A* is more efficient than Dijkstra?
**Answer:**
> "In Module 1, we built a live **Algorithm Performance Benchmark**. When you query a route between two distant campus buildings, our system executes both algorithms simultaneously. The UI shows that:
> 1. Both return the exact same distance (verifying mathematical optimality).
> 2. A* examines up to 30–50% fewer nodes because the Euclidean heuristic guides the priority queue directly toward the destination coordinates."

---

### Q5: What heuristic does your A* algorithm use, and is it admissible?
**Answer:**
> "We use **Euclidean distance** (straight-line distance):
> $$h(u, v) = \sqrt{(x_u - x_v)^2 + (y_u - y_v)^2}$$
> Yes, it is **strictly admissible** because in 2D space, a straight line is the shortest distance between two points. Since the heuristic never overestimates the actual walking distance ($h(n) \le h^*(n)$), A* is mathematically guaranteed to find an optimal shortest path."

---

### Q6: Can Dijkstra's algorithm work with negative edge weights?
**Answer:**
> "No. Dijkstra assumes that adding an edge always increases path length (monotonicity). With negative edge weights, an already-visited vertex could later find a shorter path, breaking the greedy choice. For graphs with negative weights, the **Bellman-Ford algorithm** must be used. In our campus system, walking distances are physical measurements and therefore always positive."

---

### Q7: How does the accessibility / wheelchair mode work?
**Answer:**
> "In Discrete Math, this is an **edge-induced subgraph** $G' = (V, E')$.
> We filter the edge set $E$ to include only pathways marked with `is_accessible = True`. Edges containing staircases or steep slopes are removed. The pathfinder is then run on this subgraph, which automatically routes around the stairs via accessible ramps."

---

### Q8: What data structures did you use for the pathfinding algorithms?
**Answer:**
> - A **Min-Heap (Priority Queue)** using Python's `heapq` module to extract the node with the lowest distance in $\mathcal{O}(\log V)$ time.
> - A **Hash Map (Dictionary)** for distances $g(n)$ and predecessors (parent pointers) to reconstruct the final route in $\mathcal{O}(1)$ average lookup time."

---

### Q9: How does Module 2 (Classroom Scheduling) connect to Discrete Mathematics?
**Answer:**
> "Timetabling is a classic **Constraint Satisfaction Problem (CSP)** rooted in Propositional Logic and Boolean Satisfiability.
> We define binary decision variables $X_{c, r, s} \in \{0, 1\}$ representing whether course $c$ is scheduled in room $r$ at time slot $s$.
> We enforce logic constraints such that:
> - No two classes can occupy the same room at the same time period.
> - No instructor can be assigned to teach two classes simultaneously.
> - The room capacity must be $\ge$ course enrollment.
> - Lab courses are strictly matched to lab rooms.
> This is solved in milliseconds using Google OR-Tools CP-SAT."

---

### Q10: Why use Google OR-Tools CP-SAT instead of writing a recursive backtracking algorithm?
**Answer:**
> "Simple recursive backtracking suffers from combinatorial explosion $\mathcal{O}(R \times S \times C)$ and often freezes or takes minutes. Google OR-Tools CP-SAT utilizes modern SAT-solving techniques, conflict-driven clause learning (CDCL), and domain propagation, finding an optimal conflict-free schedule in under 0.1 seconds."

---

### Q11: How does Module 3 calculate Space Utilization and what do the color bands represent?
**Answer:**
> "Utilization is computed as:
> $$\text{Utilization Rate} = \frac{\text{Enrolled Students}}{\text{Room Capacity}} \times 100\%$$
> In the dashboard:
> - **Amber (<50%)**: Under-utilized room (energy and HVAC waste).
> - **Teal (50–90%)**: Optimal seating capacity.
> - **Coral (>90%)**: Peak capacity / potential crowding.
> We also detect unassigned idle rooms so facility managers can turn off lighting and cooling."

---

### Q12: How are results exported and integrated into real campus operations?
**Answer:**
> "All generated route itineraries, conflict-free weekly timetables, and room utilization reports can be exported directly via **1-click CSV download buttons**, allowing academic registrars and students to import them straight into Microsoft Excel, ERP systems, or student portals."


---

### Q13: How does your Continuous Integration (CI) pipeline work?
**Answer:**
> "We use **GitHub Actions** — a free automation service built into GitHub. We wrote a configuration file at `.github/workflows/tests.yml` that tells GitHub:
> 1. **When to run**: Every time anyone pushes code to the `main` branch, or opens a pull request.
> 2. **What to do**: Spin up a fresh Ubuntu virtual machine, install Python 3.12, install all our dependencies from `requirements.txt`, and run `pytest tests/ -v --cov=src`.
> 3. **What it ensures**: If any of our 27 tests fail after a code change, the push is flagged with a red ❌ on GitHub, so we catch bugs immediately before they reach others.
>
> The result is a green ✅ badge in our README — proof the project is always in a working state."

---

### Q14: What is test coverage and why does it matter?
**Answer:**
> "**Test coverage** is a percentage that answers: 'Of all the lines of code in our project, how many lines are actually executed by our test suite?'
>
> We measure it with `pytest-cov`. For example, if a function has 10 lines and our tests only exercise 8 of them, that function has 80% coverage — the other 2 lines are 'untested' and might contain hidden bugs.
>
> We run:
> ```bash
> python -m pytest tests/ --cov=src --cov-report=term-missing
> ```
> The `--cov-report=term-missing` flag shows exactly which line numbers are not yet tested, so we know where to add more tests.
>
> High coverage doesn't guarantee zero bugs, but low coverage is a warning sign that large parts of the system are never tested at all."

---

### Q15: What are smoke tests and how are they different from unit tests?
**Answer:**
> "A **unit test** tests a single, isolated function. For example, `test_dijkstra_shortest_path` calls only the Dijkstra function with specific inputs and checks the output.
>
> A **smoke test** tests the entire application from end to end — just enough to confirm it starts without crashing. The name comes from hardware engineering: 'turn it on and check if it smokes.'
>
> We use **Streamlit AppTest** (`from streamlit.testing.v1 import AppTest`) which runs `app.py` headlessly (no browser needed) and lets us assert that:
> - The app renders without exceptions
> - The correct 4 tabs appear
> - Sidebar metrics are populated
> - No 'file not found' errors appear
>
> If a bad import is added to `app.py`, or a CSV file is accidentally deleted, the smoke tests catch it in seconds — even on GitHub Actions, without any human running the app."


---

### Q16: How does your experimental demand-prediction module work?
**Answer:**
> "Our demand-prediction module (`src/prediction/demand_predictor.py`) uses an interpretable **Moving Average (MA) baseline model** computed over 4 weeks of historical attendance data across 15 campus time slots:
>
> $$\hat{D}_{s} = \frac{1}{K} \sum_{k=1}^K D_{s, W-k+1}$$
>
> Instead of using an opaque machine learning black box, this time-series moving average gives transparent, explainable predictions of student turnout for each slot. We categorize each time slot into **High Peak** ($\ge 50$ students), **Moderate**, or **Low Demand**."

---

### Q17: How is predicted demand integrated into the CP-SAT timetable solver without causing infeasibility?
**Answer:**
> "We integrate demand predictions as **linear soft preferences (penalties)** in the CP-SAT objective function rather than hard constraints:
>
> $$\min \sum_{c, r, s} X_{c,r,s} \cdot \Big( (\text{Capacity}_r - \text{Enrolled}_c) + \text{Penalty}_{c,r,s} \Big)$$
>
> - **Hard constraints** (room conflict-free, instructor conflict-free, lab requirements) are strictly enforced.
> - **Soft preferences** gently penalize assignments that place small courses into high-capacity rooms during peak demand time slots.
>
> This guarantees that the solver **always finds a mathematically valid schedule** without risking infeasibility, while prioritizing space efficiency."

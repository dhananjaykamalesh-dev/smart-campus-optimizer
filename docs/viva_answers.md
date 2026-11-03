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

### Q4: What heuristic does your A* algorithm use, and is it admissible?
**Answer:**
> "We use **Euclidean distance** (straight-line distance):
> $$h(u, v) = \sqrt{(x_u - x_v)^2 + (y_u - y_v)^2}$$
> Yes, it is **strictly admissible** because in 2D space, a straight line is the shortest distance between two points. Since the heuristic never overestimates the actual walking distance ($h(n) \le h^*(n)$), A* is mathematically guaranteed to find an optimal shortest path."

---

### Q5: Can Dijkstra's algorithm work with negative edge weights?
**Answer:**
> "No. Dijkstra assumes that adding an edge always increases path length (monotonicity). With negative edge weights, an already-visited vertex could later find a shorter path, breaking the greedy choice. For graphs with negative weights, the **Bellman-Ford algorithm** must be used. In our campus system, walking distances are physical measurements and therefore always positive."

---

### Q6: How does the accessibility / wheelchair mode work?
**Answer:**
> "In Discrete Math, this is an **edge-induced subgraph** $G' = (V, E')$.
> We filter the edge set $E$ to include only pathways marked with `is_accessible = True`. Edges containing staircases or steep slopes are removed. The pathfinder is then run on this subgraph, which automatically routes around the stairs via accessible ramps."

---

### Q7: What data structures did you use for the pathfinding algorithms?
**Answer:**
> - A **Min-Heap (Priority Queue)** using Python's `heapq` module to extract the node with the lowest distance in $\mathcal{O}(\log V)$ time.
> - A **Hash Map (Dictionary)** for distances $g(n)$ and predecessors (parent pointers) to reconstruct the final route in $\mathcal{O}(1)$ average lookup time."

---

### Q8: How does Module 2 (Classroom Scheduling) connect to Discrete Mathematics?
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

### Q9: Why use Google OR-Tools CP-SAT instead of writing a recursive backtracking algorithm?
**Answer:**
> "Simple recursive backtracking suffers from combinatorial explosion $\mathcal{O}(R \times S \times C)$ and often freezes or takes minutes. Google OR-Tools CP-SAT utilizes modern SAT-solving techniques, conflict-driven clause learning (CDCL), and domain propagation, finding an optimal conflict-free schedule in under 0.1 seconds."

---

### Q10: How does Module 3 calculate Space Utilization?
**Answer:**
> "Utilization is computed as:
> $$\text{Utilization Rate} = \frac{\text{Enrolled Students}}{\text{Room Capacity}} \times 100\%$$
> Since our CSP constraint guarantees $\text{Room Capacity} \ge \text{Enrolled Students}$, utilization is strictly between $0\%$ and $100\%$. The module also identifies idle rooms that can be powered down to save energy."

---

### Q11: Why did you use Streamlit and Plotly instead of a paid service or React?
**Answer:**
> "Streamlit allows us to build a responsive, reactive web application entirely in Python without complex frontend build chains. Plotly provides offline, GPU-accelerated 2D geometric visualization without needing paid external mapping APIs (like Google Maps API) or exposing API keys."

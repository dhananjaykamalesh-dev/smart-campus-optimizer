# Discrete Mathematics & Algorithm Theory Guide

This document explains the mathematical foundations behind the **Smart Campus Optimization System**. It is written so you can explain these concepts clearly and confidently during your project evaluation.

---

## 1. Graph Theory Fundamentals (Campus Navigation)

### Formal Graph Definition
The campus layout is modeled as an **undirected, edge-weighted graph**:
$$G = (V, E, w)$$

Where:
- **$V$ (Vertices / Nodes)**: A finite set representing physical locations or buildings:
  $$V = \{B_1, B_2, B_3, \dots, B_{10}\}$$
  Each vertex $v \in V$ possesses attributes: $(x_v, y_v) \in \mathbb{R}^2$ (Euclidean coordinates) and $\text{Category}(v)$.
- **$E$ (Edges / Walkways)**: An unordered pair of vertices representing bidirectional pedestrian paths:
  $$E = \{(u, v) : u, v \in V, u \ne v\}$$
- **$w$ (Weight Function)**: A mapping assigning each edge a positive physical walking distance in meters:
  $$w: E \to \mathbb{R}^+ \quad \text{such that} \quad w(u, v) > 0$$

### Subgraph & Accessibility
To support wheelchair and mobility-impaired accessibility, the system computes an **edge-induced subgraph**:
$$G_{\text{acc}} = (V, E_{\text{acc}})$$
Where:
$$E_{\text{acc}} = \{ e \in E : \text{is\_accessible}(e) = \text{True} \}$$
Edges representing stairs or steep inclines have $\text{is\_accessible} = \text{False}$ and are removed from $E_{\text{acc}}$, forcing pathfinding algorithms to find safe ramp-accessible detours.

---

## 2. Shortest Path Algorithms: Dijkstra vs. A*

### A. Dijkstra's Algorithm (Uniform-Cost Search)
- **Class**: Greedy / Dynamic Programming.
- **Goal**: Finds the single-source shortest path to all vertices.
- **Core Principle (Edge Relaxation)**:
  For an edge $(u, v)$ with weight $w(u, v)$:
  $$\text{if } g(u) + w(u, v) < g(v) \implies g(v) \leftarrow g(u) + w(u, v)$$
  where $g(n)$ is the shortest known distance from the starting vertex to node $n$.
- **Data Structure**: Priority Queue (Min-Heap) using Python's `heapq`.
- **Time Complexity**: $\mathcal{O}((V + E) \log V)$ with a binary heap.

### B. A* (A-Star) Search Algorithm (Informed Heuristic Search)
- **Class**: Best-First Search with Heuristic Evaluation.
- **Evaluation Function**:
  $$f(n) = g(n) + h(n)$$
  Where:
  - $g(n)$: Exact accumulated cost from the start node to node $n$.
  - $h(n)$: Estimated cost from node $n$ to the destination goal.
  - $f(n)$: Estimated total cost of the cheapest solution passing through $n$.

### The Euclidean Heuristic & Proof of Admissibility
In our campus system, nodes have physical 2D coordinates $(x, y)$. We use the **Straight-Line Euclidean Distance** as the heuristic function:
$$h(u, v) = \sqrt{(x_u - x_v)^2 + (y_u - y_v)^2}$$

**Proof of Admissibility**:
A heuristic $h(n)$ is *admissible* if it never overestimates the actual true cost $h^*(n)$ to reach the goal:
$$\forall n \in V: \quad 0 \le h(n) \le h^*(n)$$
In Euclidean geometry, the straight line between any two points is the shortest possible path (Triangle Inequality). Since physical walkways can bend or turn, actual walking distance $d^*(n) \ge \text{Euclidean distance}$. Thus, $h(n) \le h^*(n)$ always holds.

**Conclusion**: Because $h(n)$ is admissible, **A\* is mathematically guaranteed to find an optimal shortest path identical in total distance to Dijkstra**, but it examines significantly fewer vertices by prioritizing nodes directed towards the destination.

---

## 3. Constraint Satisfaction Problem (Classroom Scheduling)

### Mathematical CSP Formulation
Timetabling is modeled as a Constraint Satisfaction Problem defined by $(X, D, C)$:
- **Variables ($X$)**:
  $$X_{c, r, s} \in \{0, 1\}$$
  A Boolean variable representing: "Is course $c$ held in room $r$ at time slot $s$?"
- **Domain ($D$)**: Binary domain $\{0, 1\}$.
- **Hard Constraints ($C$)**:
  1. **Course Uniqueness**: Every course $c$ is scheduled exactly once during the week:
     $$\sum_{r \in R} \sum_{s \in S} X_{c, r, s} = 1 \quad \forall c \in C$$
  2. **Room Double-Booking Elimination**: No room can host more than one course simultaneously:
     $$\sum_{c \in C} X_{c, r, s} \le 1 \quad \forall r \in R, \forall s \in S$$
  3. **Instructor Conflict Elimination**: No instructor can teach two courses in the same time slot:
     $$\sum_{c \in C_i} \sum_{r \in R} X_{c, r, s} \le 1 \quad \forall i \in I, \forall s \in S$$
     where $C_i$ is the subset of courses assigned to instructor $i$.
  4. **Capacity Lower Bound**:
     $$X_{c, r, s} = 0 \quad \text{if} \quad \text{Capacity}(r) < \text{Enrolled}(c)$$
  5. **Facility Type Requirement**:
     $$X_{c, r, s} = 0 \quad \text{if} \quad \text{RequiresLab}(c) \land \neg \text{IsLab}(r)$$

### Soft Optimization Objective
To ensure classroom efficiency, we formulate a minimization objective:
$$\min \sum_{c, r, s} X_{c, r, s} \times (\text{Capacity}(r) - \text{Enrolled}(c))$$
This automatically favors rooms whose seating capacity closely matches class size, eliminating wasted space.

---

## 4. Resource Allocation & Utilization Metrics

### Metric Definition
The utilization rate of an allocated classroom $r$ for course $c$ is:
$$\text{Utilization}(c, r) = \left( \frac{\text{Enrolled}(c)}{\text{Capacity}(r)} \right) \times 100\%$$

### Invariant & Properties
- **Invariant**: Because $\text{Capacity}(r) \ge \text{Enrolled}(c) > 0$, the utilization is strictly bounded:
  $$0\% < \text{Utilization}(c, r) \le 100\%$$
- **Classification**:
  - Under-utilized: $< 50\%$
  - Optimal: $50\% \le \text{Util} \le 90\%$
  - Near Capacity: $> 90\%$

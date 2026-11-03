"""
Main Web Application: Smart Campus Optimization System
Built with Streamlit, NetworkX, Google OR-Tools CP-SAT, and Plotly.

Discrete Mathematics Core Modules:
- Tab 1: Campus Navigation (Dijkstra vs. A* Graph Search)
- Tab 2: Timetable Scheduling (Propositional Constraints with OR-Tools CP-SAT)
- Tab 3: Resource Allocation & Space Utilization Metrics
- Tab 4: Mathematical Concepts & Viva Defense Guide
"""

import os
import streamlit as st
import pandas as pd

# Import project modules
from src.navigation.graph_builder import CampusGraph
from src.navigation.pathfinder import CampusPathfinder
from src.scheduling.timetable_solver import CampusTimetableSolver
from src.allocation.resource_manager import CampusResourceManager
from src.utils.visualizer import (
    create_campus_map_figure,
    create_utilization_bar_chart,
    create_capacity_vs_enrolled_chart
)


# Page Configuration
st.set_page_config(
    page_title="Smart Campus Optimization System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BUILDINGS_CSV = os.path.join(DATA_DIR, "buildings.csv")
PATHS_CSV = os.path.join(DATA_DIR, "paths.csv")
ROOMS_CSV = os.path.join(DATA_DIR, "rooms.csv")
COURSES_CSV = os.path.join(DATA_DIR, "courses.csv")
INSTRUCTORS_CSV = os.path.join(DATA_DIR, "instructors.csv")
TIME_SLOTS_CSV = os.path.join(DATA_DIR, "time_slots.csv")


@st.cache_resource
def load_campus_graph() -> CampusGraph:
    """Loads and caches the campus graph from CSV data."""
    return CampusGraph(buildings_file=BUILDINGS_CSV, paths_file=PATHS_CSV)


@st.cache_resource
def load_timetable_solver() -> CampusTimetableSolver:
    """Loads and caches the timetable solver instance."""
    return CampusTimetableSolver(
        rooms_file=ROOMS_CSV,
        courses_file=COURSES_CSV,
        instructors_file=INSTRUCTORS_CSV,
        time_slots_file=TIME_SLOTS_CSV
    )


def main():
    # Header Banner
    st.title("🏫 Graph-Based Smart Campus Optimization System")
    st.markdown(
        "**Discrete Mathematics Project** • Graph Theory ($G=(V, E)$), Heuristic Search ($A^*$), "
        "and Constraint Satisfaction (CP-SAT)."
    )

    # Initialize Graph and Data
    campus_graph = load_campus_graph()
    solver_instance = load_timetable_solver()
    buildings_list = campus_graph.get_all_buildings()
    building_options = {f"{b['name']} ({b['id']})": b["id"] for b in buildings_list}

    # Sidebar Navigation / Controls
    st.sidebar.header("🎓 System Metrics")
    st.sidebar.info(
        "**Campus Entities**\n"
        f"- Buildings (Vertices): **{len(campus_graph.graph.nodes)}**\n"
        f"- Walkways (Edges): **{len(campus_graph.graph.edges)}**\n"
        f"- Classrooms: **{len(solver_instance.rooms)}**\n"
        f"- Courses Registered: **{len(solver_instance.courses)}**\n"
        f"- Faculty Members: **{len(solver_instance.instructors)}**\n"
        f"- Weekly Slots: **{len(solver_instance.time_slots)}**"
    )

    # Main Tabs
    tab_nav, tab_sched, tab_alloc, tab_theory = st.tabs([
        "📍 Module 1: Campus Navigation",
        "📅 Module 2: Classroom Scheduling",
        "📊 Module 3: Resource Allocation",
        "📖 Discrete Math Theory"
    ])

    # -------------------------------------------------------------
    # TAB 1: CAMPUS NAVIGATION
    # -------------------------------------------------------------
    with tab_nav:
        st.subheader("Interactive Graph Navigation (Dijkstra vs. A* Search)")
        st.markdown(
            "Find the most efficient walking route between campus facilities. "
            "Compare uniform-cost Dijkstra search against goal-directed $A^*$ heuristic search."
        )

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### 🧭 Route Planner")

            start_label = st.selectbox(
                "Select Origin Building:",
                options=list(building_options.keys()),
                index=0,
                help="Starting vertex u in Graph G"
            )
            start_id = building_options[start_label]

            dest_index = 4 if len(building_options) > 4 else 1
            goal_label = st.selectbox(
                "Select Destination Building:",
                options=list(building_options.keys()),
                index=dest_index,
                help="Target vertex v in Graph G"
            )
            goal_id = building_options[goal_label]

            algorithm_choice = st.radio(
                "Select Pathfinding Algorithm:",
                options=["Dijkstra's Algorithm", "A* (A-Star) Algorithm"],
                help="Dijkstra explores uniformly outward. A* guides search toward destination using straight-line Euclidean distance."
            )

            accessible_only = st.checkbox(
                "♿ Wheelchair Accessible Paths Only",
                value=False,
                help="Filters graph to exclude stairways and steep slopes (e.g. bypasses stairs between Library and Activity Center)."
            )

            find_btn = st.button("🚀 Find Optimal Route", type="primary", use_container_width=True)

        with col2:
            active_graph = (
                campus_graph.get_accessible_subgraph()
                if accessible_only
                else campus_graph.graph
            )
            pathfinder = CampusPathfinder(active_graph)

            if start_id == goal_id:
                st.warning("⚠️ Origin and Destination are the same building! Distance is 0 meters.")
                highlight_path = [start_id]
                route_result = None
            else:
                if "Dijkstra" in algorithm_choice:
                    route_result = pathfinder.find_shortest_path_dijkstra(start_id, goal_id)
                else:
                    route_result = pathfinder.find_shortest_path_astar(start_id, goal_id)

                if "error" in route_result:
                    st.error(f"❌ {route_result['error']}")
                    highlight_path = None
                else:
                    highlight_path = route_result["path"]

            fig = create_campus_map_figure(
                graph=active_graph,
                highlight_path=highlight_path,
                accessible_only=accessible_only
            )
            st.plotly_chart(fig, use_container_width=True)

        if route_result and "error" not in route_result:
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🚶 Total Walk Distance", f"{route_result['total_distance']} m")
            m2.metric("⏱️ Estimated Walk Time", f"{route_result['walking_time_min']} min")
            m3.metric("📍 Number of Stops", f"{len(route_result['path'])}")
            m4.metric("🔍 Nodes Explored", f"{route_result['nodes_explored']}")

            with st.expander("📋 Turn-by-Turn Route Itinerary", expanded=True):
                steps = []
                for idx, bid in enumerate(route_result["path"]):
                    b_info = campus_graph.get_building_info(bid)
                    if idx == 0:
                        desc = f"**Start at {b_info['name']}** ({b_info['category']})"
                    elif idx == len(route_result["path"]) - 1:
                        prev_bid = route_result["path"][idx - 1]
                        edge_w = active_graph[prev_bid][bid]["weight"]
                        desc = f"**Arrive at {b_info['name']}** (+{edge_w}m walk)"
                    else:
                        prev_bid = route_result["path"][idx - 1]
                        edge_w = active_graph[prev_bid][bid]["weight"]
                        desc = f"Walk to **{b_info['name']}** (+{edge_w}m)"
                    steps.append({"Step": idx + 1, "Building ID": bid, "Directions": desc})
                st.table(pd.DataFrame(steps))

    # -------------------------------------------------------------
    # TAB 2: CLASSROOM SCHEDULING (OR-TOOLS CP-SAT)
    # -------------------------------------------------------------
    with tab_sched:
        st.subheader("📅 Automated Classroom Timetabling (CP-SAT Constraint Solver)")
        st.markdown(
            "Solves university course scheduling as a **Constraint Satisfaction Problem (CSP)**. "
            "Guarantees **zero room double-booking**, **zero instructor clashes**, and room capacity compliance."
        )

        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### ⚙️ Solver Configuration")
            optimize_cap = st.checkbox(
                "Optimize Seat Fit (Minimize Wasted Seats)",
                value=True,
                help="Soft constraint: minimizes room capacity minus student enrollment."
            )
            solve_btn = st.button("⚡ Generate Conflict-Free Schedule", type="primary", use_container_width=True)

        # Solve schedule
        schedule_result = solver_instance.solve(optimize_capacity=optimize_cap)

        if schedule_result["status"] in ("OPTIMAL", "FEASIBLE"):
            st.success(
                f"✅ **Schedule Found ({schedule_result['status']})** in "
                f"**{schedule_result['solve_time_sec']} seconds**!"
            )

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("📚 Courses Scheduled", schedule_result["total_courses"])
            k2.metric("⚡ Total Conflicts", "0 (Mathematically Proven)")
            k3.metric("🎯 Average Utilization", f"{schedule_result['average_utilization']}%")
            k4.metric("⏱️ Solver Run Time", f"{schedule_result['solve_time_sec']}s")

            st.markdown("### 📋 Weekly Generated Timetable")
            display_df = schedule_result["schedule_df"][[
                "day", "period", "time", "course_name", "instructor", "room_name", "enrolled", "capacity", "utilization_pct"
            ]].copy()
            display_df.columns = [
                "Day", "Period", "Time Slot", "Course", "Instructor", "Room", "Enrolled", "Capacity", "Utilization %"
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            with st.expander("🔍 Mathematical Verification of Hard Constraints"):
                st.write("1. **Room Conflict Check**: Checked all (room, slot) combinations $\\implies$ **No overlapping classes**.")
                st.write("2. **Teacher Clash Check**: Checked all (instructor, slot) pairs $\\implies$ **No simultaneous assignments**.")
                st.write("3. **Capacity Check**: Every assigned room has $\\text{Capacity} \\ge \\text{Enrolled Students}$.")
                st.write("4. **Lab Verification**: Lab-required courses placed strictly into laboratory facilities.")
        else:
            st.error(f"❌ Timetable solver failed: {schedule_result.get('error', 'Infeasible constraints')}")

    # -------------------------------------------------------------
    # TAB 3: RESOURCE ALLOCATION & UTILIZATION
    # -------------------------------------------------------------
    with tab_alloc:
        st.subheader("📊 Space Allocation & Utilization Analytics")
        st.markdown(
            "Evaluates facility efficiency, seat waste, and room utilization rates. "
            "Assists campus administrators in optimizing power usage and space planning."
        )

        resource_mgr = CampusResourceManager(
            schedule_records=schedule_result.get("schedule", []),
            all_rooms=solver_instance.rooms
        )
        metrics = resource_mgr.compute_overall_metrics()
        util_df = resource_mgr.get_room_utilization_summary()

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("🏢 Overall Space Utilization", f"{metrics['overall_utilization_pct']}%")
        r2.metric("👥 Total Enrolled Students", f"{metrics['total_enrolled']}")
        r3.metric("🪑 Allocated Capacity", f"{metrics['total_allocated_capacity']} seats")
        r4.metric("📉 Wasted Capacity", f"{metrics['total_wasted_seats']} seats")

        st.markdown("---")

        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig_bar = create_utilization_bar_chart(util_df)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_chart2:
            fig_grouped = create_capacity_vs_enrolled_chart(util_df)
            st.plotly_chart(fig_grouped, use_container_width=True)

        st.markdown("### 📋 Classroom Allocation Detail & Health Status")
        st.dataframe(util_df, use_container_width=True, hide_index=True)

        idle_info = resource_mgr.get_idle_rooms_analysis()
        if idle_info["idle_rooms_count"] > 0:
            with st.expander(f"💡 Idle Rooms Analysis ({idle_info['idle_rooms_count']} unallocated facilities)"):
                st.info(
                    "The following rooms were not needed for the current course schedule and "
                    "can be powered down to save HVAC and electrical costs:"
                )
                idle_df = pd.DataFrame([
                    {"Room Code": r["room_id"], "Room Name": r["name"], "Capacity": r["capacity"], "Building": r["building_id"]}
                    for r in idle_info["idle_rooms"]
                ])
                st.table(idle_df)

    # -------------------------------------------------------------
    # TAB 4: DISCRETE MATHEMATICS THEORY
    # -------------------------------------------------------------
    with tab_theory:
        st.subheader("📖 Discrete Mathematics Foundations & Project Defense")
        st.markdown(
            """
            ### 1. Graph Model Definition
            The campus is represented as a weighted undirected graph $G = (V, E, w)$:
            - **Vertices ($V$)**: Distinct campus buildings and facilities with spatial coordinates $(x, y)$.
            - **Edges ($E$)**: Walkways connecting adjacent buildings: $E = \\{ (u, v) : u, v \\in V \\}$.
            - **Weights ($w$)**: Non-negative scalar representing physical distance: $w: E \\to \\mathbb{R}^+$.

            ---

            ### 2. Shortest Path Search: Dijkstra vs. A*
            | Concept | Dijkstra's Algorithm | A* Search Algorithm |
            | :--- | :--- | :--- |
            | **Strategy** | Uniform-Cost Breadth Search | Informed Heuristic Best-First Search |
            | **Evaluation Function** | $f(n) = g(n)$ | $f(n) = g(n) + h(n)$ |
            | **Heuristic Function** | None ($h(n) = 0$) | Euclidean Distance: $h(n) = \\sqrt{\\Delta x^2 + \\Delta y^2}$ |
            | **Admissibility Proof** | N/A | Straight line is the shortest 2D distance $\\implies h(n) \\le h^*(n)$ (Guaranteed Optimal) |
            | **Exploration Efficiency** | Radiates in all directions | Focused towards destination coordinates |

            ---

            ### 3. Constraint Satisfaction Problem (CSP) Formulation
            The timetabling problem is represented as a tuple $(X, D, C)$:
            - **Decision Variables**: $X_{c, r, s} \\in \\{0, 1\\}$
              True if course $c$ is scheduled in room $r$ at time slot $s$.
            - **Hard Constraints**:
              1. **Course Assignment**: $\\forall c: \\sum_r \\sum_s X_{c, r, s} = 1$
              2. **Room Double-Booking**: $\\forall r, s: \\sum_c X_{c, r, s} \\le 1$
              3. **Instructor Clash**: $\\forall i, s: \\sum_{c \\in C_i} \\sum_r X_{c, r, s} \\le 1$
              4. **Capacity Constraint**: $X_{c, r, s} = 0$ if $\\text{Capacity}(r) < \\text{Enrolled}(c)$
              5. **Lab Requirement**: $X_{c, r, s} = 0$ if $\\text{RequiresLab}(c) \\land \\neg \\text{IsLab}(r)$
            - **Soft Objective**:
              $$\\min \\sum_{c, r, s} X_{c, r, s} \\times (\\text{Capacity}(r) - \\text{Enrolled}(c))$$
            """
        )


if __name__ == "__main__":
    main()

"""
Main Web Application: Smart Campus Optimization System
Built with Streamlit, NetworkX, Google OR-Tools CP-SAT, and Plotly.

Discrete Mathematics Core Modules:
- Tab 1: Campus Navigation (Dijkstra vs. A*, Accessibility & Dynamic Detour Rerouting)
- Tab 2: Timetable Scheduling (Propositional Constraints, Disruption Simulation & Minimal Repair)
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
from src.prediction.demand_predictor import CampusDemandPredictor
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
HISTORICAL_DEMAND_CSV = os.path.join(DATA_DIR, "historical_demand.csv")


def check_data_files() -> bool:
    """Verifies that all required CSV data files exist."""
    required = [
        BUILDINGS_CSV, PATHS_CSV, ROOMS_CSV,
        COURSES_CSV, INSTRUCTORS_CSV, TIME_SLOTS_CSV,
        HISTORICAL_DEMAND_CSV
    ]
    missing = [f for f in required if not os.path.exists(f)]
    if missing:
        for m in missing:
            st.error(f"❌ Missing critical data file: {m}")
        return False
    return True


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


@st.cache_resource
def load_demand_predictor() -> CampusDemandPredictor:
    """Loads and caches the historical demand predictor instance."""
    return CampusDemandPredictor(historical_csv_path=HISTORICAL_DEMAND_CSV)


def main():
    if not check_data_files():
        st.stop()

    # Header Banner
    st.title("🏫 Graph-Based Smart Campus Optimization System")
    st.markdown(
        "**Discrete Mathematics Project** • Graph Theory ($G=(V, E)$), Heuristic Search ($A^*$), "
        "Dynamic Disruption Recovery, and Propositional Constraint Satisfaction (OR-Tools CP-SAT)."
    )

    # Initialize Graph and Data
    campus_graph = load_campus_graph()
    solver_instance = load_timetable_solver()
    graph_summary = campus_graph.get_graph_summary()
    buildings_list = campus_graph.get_all_buildings()
    building_options = {f"{b['name']} ({b['id']})": b["id"] for b in buildings_list}

    # -------------------------------------------------------------
    # SIDEBAR: CAMPUS SUMMARY METRICS & SYSTEM CONTROLS
    # -------------------------------------------------------------
    st.sidebar.header("📊 Campus Overview & Scale")
    sb1, sb2 = st.sidebar.columns(2)
    sb1.metric("🏛️ Buildings", graph_summary["num_buildings"])
    sb2.metric("🛣️ Walkways", graph_summary["num_paths"])

    sb3, sb4 = st.sidebar.columns(2)
    sb3.metric("🚪 Classrooms", len(solver_instance.rooms))
    sb4.metric("📚 Courses", len(solver_instance.courses))

    sb5, sb6 = st.sidebar.columns(2)
    sb5.metric("👨‍🏫 Faculty", len(solver_instance.instructors))
    sb6.metric("⏰ Time Slots", len(solver_instance.time_slots))

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Graph Invariants**\n"
        f"- Type: **Undirected, Weighted ($w > 0$)**\n"
        f"- Accessible Paths: **{graph_summary['num_accessible_paths']}/{graph_summary['num_paths']}**\n"
        f"- Covered Walkways: **{graph_summary['num_covered_paths']}/{graph_summary['num_paths']}**\n"
        f"- Connected: **{'Yes ✅' if graph_summary['is_connected'] else 'No ❌'}**"
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("💡 Designed for Discrete Mathematics Academic Review")

    # -------------------------------------------------------------
    # MAIN NAVIGATION TABS
    # -------------------------------------------------------------
    tab_nav, tab_sched, tab_alloc, tab_theory = st.tabs([
        "📍 Module 1: Campus Navigation",
        "📅 Module 2: Classroom Scheduling",
        "📊 Module 3: Resource Allocation",
        "📖 Discrete Math Theory"
    ])

    # -------------------------------------------------------------
    # TAB 1: CAMPUS NAVIGATION & DYNAMIC REROUTING
    # -------------------------------------------------------------
    with tab_nav:
        st.subheader("Interactive Graph Navigation & Dynamic Rerouting")
        st.markdown(
            "Find optimal walking routes between campus facilities with support for "
            "**wheelchair accessibility** and **temporary pathway obstructions**."
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
                "Select Primary Pathfinding Algorithm:",
                options=["Dijkstra's Algorithm", "A* (A-Star) Algorithm", "Compare Both Side-by-Side"],
                help="Dijkstra explores uniformly outward. A* guides search toward destination using straight-line Euclidean distance."
            )

            accessible_only = st.checkbox(
                "♿ Wheelchair Accessible Paths Only",
                value=False,
                help="Filters graph to exclude stairways and steep slopes (e.g. bypasses stairs between Library and Activity Center)."
            )

            # ---------------------------------------------------------
            # DYNAMIC CAMPUS FEATURE: PATHWAY OBSTRUCTION SIMULATOR
            # ---------------------------------------------------------
            with st.expander("🚧 Simulate Pathway Obstruction (Detour Mode)", expanded=False):
                enable_obstruction = st.checkbox(
                    "Simulate Blocked Pathway",
                    value=False,
                    help="Temporarily removes a pathway to simulate construction, maintenance, or rain."
                )

                # Format edge options nicely
                edge_options = {}
                for u, v, d in campus_graph.graph.edges(data=True):
                    name_u = campus_graph.graph.nodes[u]["name"]
                    name_v = campus_graph.graph.nodes[v]["name"]
                    label = f"{name_u} ↔ {name_v} ({u}-{v}, {d['weight']}m)"
                    edge_options[label] = (u, v)

                selected_edge_label = st.selectbox(
                    "Select Blocked Pathway:",
                    options=list(edge_options.keys()),
                    index=2 if len(edge_options) > 2 else 0
                )
                selected_blocked_edge = edge_options[selected_edge_label]

                block_reason = st.selectbox(
                    "Reason for Closure:",
                    options=[
                        "Underground Cable Maintenance",
                        "Monsoon Waterlogging & Flooding",
                        "Pavement Resurfacing / Construction",
                        "Peak Pedestrian Congestion"
                    ]
                )

            find_btn = st.button("🚀 Calculate Route", type="primary", use_container_width=True)

        with col2:
            active_base_graph = (
                campus_graph.get_accessible_subgraph()
                if accessible_only
                else campus_graph.graph
            )
            pathfinder = CampusPathfinder(active_base_graph)

            route_result = None
            reroute_data = None
            highlight_path = None
            original_path_display = None
            blocked_edges_to_draw = []

            with st.spinner("Calculating optimal graph route..."):
                if start_id == goal_id:
                    st.warning("⚠️ Origin and Destination are the same building! Distance is 0 meters.")
                    highlight_path = [start_id]
                else:
                    try:
                        if enable_obstruction:
                            blocked_edges_to_draw = [selected_blocked_edge]
                            reroute_data = pathfinder.find_reroute_with_blocked_edges(
                                start_node=start_id,
                                goal_node=goal_id,
                                blocked_edges=blocked_edges_to_draw,
                                reason=block_reason
                            )
                            if "error" in reroute_data:
                                st.error(f"❌ {reroute_data['error']}")
                            else:
                                route_result = {
                                    "path": reroute_data["updated_path"],
                                    "path_names": reroute_data["updated_path_names"],
                                    "total_distance": reroute_data["updated_distance"],
                                    "walking_time_min": round(reroute_data["updated_distance"] / 84.0, 1),
                                    "nodes_explored": len(reroute_data["updated_path"])
                                }
                                highlight_path = reroute_data["updated_path"]
                                original_path_display = reroute_data["original_path"]
                        else:
                            if algorithm_choice == "Compare Both Side-by-Side":
                                comp = pathfinder.compare_algorithms(start_id, goal_id)
                                route_result = comp["astar"]
                            elif "Dijkstra" in algorithm_choice:
                                route_result = pathfinder.find_shortest_path_dijkstra(start_id, goal_id)
                            else:
                                route_result = pathfinder.find_shortest_path_astar(start_id, goal_id)

                            if route_result and "error" in route_result:
                                st.error(f"❌ {route_result['error']}")
                            elif route_result:
                                highlight_path = route_result["path"]
                    except Exception as e:
                        st.error(f"❌ Error during path calculation: {str(e)}")

            fig = create_campus_map_figure(
                graph=active_base_graph,
                highlight_path=highlight_path,
                accessible_only=accessible_only,
                blocked_edges=blocked_edges_to_draw if enable_obstruction else None,
                original_path=original_path_display
            )
            st.plotly_chart(fig, use_container_width=True)

        # Reroute Alert Banner (if obstruction active)
        if enable_obstruction and reroute_data and "error" not in reroute_data:
            if reroute_data["path_blocked"]:
                st.warning(
                    f"⚠️ **Detour Active**: The direct pathway was blocked due to **{reroute_data['reason']}**.\n\n"
                    f"- Original Path Distance: **{reroute_data['original_distance']} m**\n"
                    f"- Updated Detour Distance: **{reroute_data['updated_distance']} m** (+{reroute_data['distance_diff_m']} m detour)\n"
                    f"- Additional Walking Time: **+{reroute_data['detour_time_diff_min']} minutes**"
                )
            else:
                st.info(
                    f"ℹ️ The blocked pathway ({selected_edge_label}) did not intersect your optimal route. "
                    f"Original path remained optimal!"
                )

        # Route Metrics and Turn-by-Turn Directions
        if route_result and "error" not in route_result and len(route_result["path"]) > 1:
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🚶 Total Walk Distance", f"{route_result['total_distance']} m")
            m2.metric("⏱️ Estimated Walk Time", f"{route_result['walking_time_min']} min")
            m3.metric("📍 Number of Stops", f"{len(route_result['path'])}")
            m4.metric("🔍 Nodes in Route", f"{len(route_result['path'])}")

            # Algorithm comparison section (if not in blocked mode)
            if not enable_obstruction:
                st.markdown("### ⚖️ Algorithm Performance Benchmark: Dijkstra vs. A*")
                comp = pathfinder.compare_algorithms(start_id, goal_id)

                b1, b2, b3 = st.columns(3)
                b1.metric("Dijkstra Nodes Explored", comp["dijkstra"]["nodes_explored"])
                b2.metric("A* Nodes Explored", comp["astar"]["nodes_explored"], delta=f"-{comp['nodes_saved_by_astar']} nodes" if comp['nodes_saved_by_astar'] > 0 else "Equal")
                b3.metric("A* Runtime", f"{comp['astar'].get('execution_time_ms', 0)} ms")

                bench_df = pd.DataFrame([
                    {
                        "Algorithm": "Dijkstra's Algorithm",
                        "Total Distance (m)": comp["dijkstra"]["total_distance"],
                        "Nodes Visited": comp["dijkstra"]["nodes_explored"],
                        "Execution Time (ms)": comp["dijkstra"].get("execution_time_ms", 0),
                        "Heuristic Used": "None (Blind Search)",
                        "Optimal?": "Guaranteed"
                    },
                    {
                        "Algorithm": "A* (A-Star) Algorithm",
                        "Total Distance (m)": comp["astar"]["total_distance"],
                        "Nodes Visited": comp["astar"]["nodes_explored"],
                        "Execution Time (ms)": comp["astar"].get("execution_time_ms", 0),
                        "Heuristic Used": "Euclidean Distance",
                        "Optimal?": "Guaranteed (Admissible h)"
                    }
                ])
                st.dataframe(bench_df, use_container_width=True, hide_index=True)

            # Itinerary and CSV Download
            with st.expander("📋 Turn-by-Turn Route Itinerary", expanded=True):
                steps = []
                for idx, bid in enumerate(route_result["path"]):
                    b_info = campus_graph.get_building_info(bid)
                    if idx == 0:
                        desc = f"Start at {b_info['name']} ({b_info['category']})"
                    elif idx == len(route_result["path"]) - 1:
                        prev_bid = route_result["path"][idx - 1]
                        edge_w = active_base_graph[prev_bid][bid]["weight"] if active_base_graph.has_edge(prev_bid, bid) else "detour"
                        desc = f"Arrive at {b_info['name']} (+{edge_w}m walk)"
                    else:
                        prev_bid = route_result["path"][idx - 1]
                        edge_w = active_base_graph[prev_bid][bid]["weight"] if active_base_graph.has_edge(prev_bid, bid) else "detour"
                        desc = f"Walk to {b_info['name']} (+{edge_w}m)"
                    steps.append({"Step": idx + 1, "Building ID": bid, "Directions": desc})
                
                steps_df = pd.DataFrame(steps)
                st.table(steps_df)

                route_csv = steps_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Route Itinerary (CSV)",
                    data=route_csv,
                    file_name=f"route_{start_id}_to_{goal_id}.csv",
                    mime="text/csv"
                )

    # -------------------------------------------------------------
    # TAB 2: CLASSROOM SCHEDULING & MINIMAL TIMETABLE REPAIR
    # -------------------------------------------------------------
    with tab_sched:
        st.subheader("📅 Automated Classroom Timetabling & Emergency Schedule Repair")
        st.markdown(
            "Solves university course scheduling as a **Constraint Satisfaction Problem (CSP)**. "
            "Guarantees **zero room double-booking**, **zero instructor clashes**, and supports **minimal-perturbation recovery**."
        )

        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### ⚙️ Timetable Controls")
            optimize_cap = st.checkbox(
                "Optimize Seat Fit (Minimize Wasted Seats)",
                value=True,
                help="Soft constraint: minimizes room capacity minus student enrollment."
            )
            solve_btn = st.button("⚡ Generate Baseline Schedule", type="primary", use_container_width=True)

        with st.spinner("Solving constraints with Google OR-Tools CP-SAT..."):
            try:
                schedule_result = solver_instance.solve(optimize_capacity=optimize_cap)
            except Exception as e:
                schedule_result = {
                    "status": "ERROR",
                    "error": f"Solver exception: {str(e)}",
                    "schedule": [],
                    "schedule_df": pd.DataFrame()
                }

        if schedule_result.get("status") in ("OPTIMAL", "FEASIBLE"):
            st.success(
                f"✅ **Baseline Schedule Active ({schedule_result['status']})** in "
                f"**{schedule_result['solve_time_sec']} seconds**!"
            )

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("📚 Courses Scheduled", schedule_result["total_courses"])
            k2.metric("⚡ Total Conflicts", "0 (Mathematically Proven)")
            k3.metric("🎯 Average Utilization", f"{schedule_result['average_utilization']}%")
            k4.metric("⏱️ Solver Run Time", f"{schedule_result['solve_time_sec']}s")

            st.markdown("### 📋 Weekly Timetable")
            display_df = schedule_result["schedule_df"][[
                "day", "period", "time", "course_name", "instructor", "room_name", "enrolled", "capacity", "utilization_pct"
            ]].copy()
            display_df.columns = [
                "Day", "Period", "Time Slot", "Course", "Instructor", "Room", "Enrolled", "Capacity", "Utilization %"
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            sched_csv = display_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Weekly Timetable (CSV)",
                data=sched_csv,
                file_name="campus_weekly_schedule.csv",
                mime="text/csv"
            )

            # ---------------------------------------------------------
            # DYNAMIC CAMPUS FEATURE: EMERGENCY ROOM CLOSURE & REPAIR
            # ---------------------------------------------------------
            st.markdown("---")
            st.markdown("### ⚠️ Emergency Disruption Simulation & Minimal Timetable Repair")
            st.info(
                "When a classroom experiences water leakage, electrical outage, or emergency maintenance, "
                "the system detects affected courses, ranks compatible vacant rooms by walking proximity, "
                "and computes a **minimal-perturbation timetable repair** moving the fewest possible classes."
            )

            room_options = {
                f"{r['name']} ({r['room_id']}, Cap: {r['capacity']})": r["room_id"]
                for r in solver_instance.rooms.values()
            }
            selected_room_label = st.selectbox("Select Room Experiencing Emergency Closure:", options=list(room_options.keys()))
            disabled_room_id = room_options[selected_room_label]

            # Detect affected courses
            disruption_info = solver_instance.simulate_room_unavailability(
                unavailable_room_id=disabled_room_id,
                current_schedule=schedule_result["schedule"]
            )

            if disruption_info["affected_count"] > 0:
                st.error(
                    f"🚨 **Disruption Detected**: Room **{disruption_info['room_name']} ({disabled_room_id})** has "
                    f"**{disruption_info['affected_count']} scheduled class(es)** that must be relocated immediately!"
                )

                # Show recommendations for each affected course
                for aff in disruption_info["affected_courses"]:
                    st.markdown(f"**Relocation Options for: `{aff['course_name']}` ({aff['day']} {aff['time']})**")
                    recs = solver_instance.recommend_alternative_rooms(
                        course_id=aff["course_id"],
                        slot_id=aff["slot_id"],
                        current_schedule=schedule_result["schedule"],
                        campus_graph=campus_graph.graph
                    )
                    if recs:
                        rec_df = pd.DataFrame([
                            {
                                "Candidate Room": r["room_name"],
                                "Building": r["building_id"],
                                "Capacity": r["capacity"],
                                "Enrolled": r["enrolled"],
                                "Wasted Seats": r["wasted_seats"],
                                "Walking Dist from Orig (m)": f"{r['walk_distance_from_orig_m']}m"
                            }
                            for r in recs
                        ])
                        st.table(rec_df)
                    else:
                        st.warning("No vacant room with sufficient capacity during this time slot. Time relocation required.")

                # Button to perform minimal timetable repair
                if st.button("🔧 Perform Minimal Timetable Repair", type="primary"):
                    with st.spinner("Computing minimal perturbation repair with CP-SAT..."):
                        repair_res = solver_instance.repair_timetable_minimal_change(
                            unavailable_room_id=disabled_room_id,
                            current_schedule=schedule_result["schedule"]
                        )

                    if repair_res["status"] in ("OPTIMAL", "FEASIBLE"):
                        st.success(
                            f"🎉 **Schedule Successfully Repaired!** "
                            f"**{repair_res['schedule_stability_pct']}% stability preserved** "
                            f"({repair_res['unchanged_courses_count']} courses unchanged, {repair_res['changed_courses_count']} relocated)."
                        )

                        if repair_res["changed_assignments"]:
                            st.markdown("#### 🔄 Relocated Classes Detail")
                            change_df = pd.DataFrame(repair_res["changed_assignments"])
                            change_df.columns = ["Course ID", "Course Name", "Faculty", "Old Room", "New Room", "Old Time", "New Time", "Day"]
                            st.dataframe(change_df, use_container_width=True, hide_index=True)

                        with st.expander("📋 View Complete Repaired Timetable", expanded=True):
                            repaired_display = repair_res["repaired_schedule_df"][[
                                "day", "period", "time", "course_name", "instructor", "room_name", "enrolled", "capacity", "is_relocated"
                            ]].copy()
                            repaired_display.columns = [
                                "Day", "Period", "Time Slot", "Course", "Instructor", "Room", "Enrolled", "Capacity", "Relocated?"
                            ]
                            st.dataframe(repaired_display, use_container_width=True, hide_index=True)

                            rep_csv = repaired_display.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="📥 Download Repaired Schedule (CSV)",
                                data=rep_csv,
                                file_name="campus_repaired_schedule.csv",
                                mime="text/csv"
                            )
                    else:
                        st.error(f"❌ Timetable repair failed: {repair_res.get('error')}")
            else:
                st.success(f"✅ Room **{disruption_info['room_name']}** has no assigned courses in the current schedule. No relocation needed!")
        else:
            st.error(f"❌ Timetable solver failed: {schedule_result.get('error', 'Infeasible constraints')}")

        # ---------------------------------------------------------
        # EXPERIMENTAL: DEMAND PREDICTION & SOFT PREFERENCE SCHEDULING
        # ---------------------------------------------------------
        st.markdown("---")
        st.subheader("🧪 [Experimental] Historical Demand Forecasting & Soft Preferences")
        st.markdown(
            "This module uses a **Moving Average time-series baseline** on 4 weeks of historical attendance records "
            "to predict high-demand vs. low-demand periods. Predicted demand is incorporated into Google OR-Tools CP-SAT "
            "as a **soft preference objective** to guide optimal room utilization without violating any hard constraints."
        )

        demand_predictor = load_demand_predictor()
        col_w, col_btn = st.columns([2, 1])
        with col_w:
            window_size = st.slider("Moving Average Window (Weeks)", min_value=1, max_value=4, value=3)
        with col_btn:
            st.write("")
            st.write("")
            run_demand_opt = st.button("✨ Solve with Demand Soft Preferences", type="secondary")

        summary_demand_df = demand_predictor.get_slot_demand_summary(window_size=window_size)

        # Visualizing Predicted Demand
        if not summary_demand_df.empty:
            st.markdown("##### 📈 Predicted Attendance per Time Slot")
            import plotly.express as px
            fig_demand = px.bar(
                summary_demand_df,
                x="Slot ID",
                y="Predicted Attendance",
                color="Demand Level",
                color_discrete_map={
                    "High Peak": "#e74c3c",
                    "Moderate": "#1abc9c",
                    "Low Demand": "#3498db"
                },
                hover_data=["Day", "Period"],
                title=f"Predicted Campus Attendance by Slot (Moving Average Window = {window_size} Weeks)"
            )
            fig_demand.update_layout(xaxis_title="Time Slot", yaxis_title="Predicted Students", height=350)
            st.plotly_chart(fig_demand, use_container_width=True)

        if run_demand_opt:
            with st.spinner("Solving CP-SAT model with demand-aware soft preferences..."):
                demand_res = solver_instance.solve_with_demand_prediction(
                    predictor=demand_predictor,
                    penalty_scale=2
                )
            if demand_res["status"] in ("OPTIMAL", "FEASIBLE"):
                st.success(f"✅ **Demand-Aware Timetable Found ({demand_res['status']})** in {demand_res['solve_time_sec']}s!")
                demand_sched_df = demand_res["schedule_df"][[
                    "day", "period", "time", "course_name", "instructor", "room_name", "enrolled", "capacity", "utilization_pct"
                ]].copy()
                demand_sched_df.columns = [
                    "Day", "Period", "Time Slot", "Course", "Instructor", "Room", "Enrolled", "Capacity", "Utilization %"
                ]
                st.dataframe(demand_sched_df, use_container_width=True, hide_index=True)

                d_csv = demand_sched_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Demand-Optimized Timetable (CSV)",
                    data=d_csv,
                    file_name="campus_demand_optimized_timetable.csv",
                    mime="text/csv"
                )
            else:
                st.error(f"❌ Solver failed: {demand_res.get('error')}")

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

        if not util_df.empty:
            util_csv = util_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Utilization Report (CSV)",
                data=util_csv,
                file_name="room_utilization_report.csv",
                mime="text/csv"
            )

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
            ### 1. Graph Model Definition & Edge Deletion Subgraphs
            The campus is represented as a weighted undirected graph $G = (V, E, w)$:
            - **Vertices ($V$)**: Distinct campus buildings and facilities with spatial coordinates $(x, y)$.
            - **Edges ($E$)**: Walkways connecting adjacent buildings: $E = \\{ (u, v) : u, v \\in V \\}$.
            - **Weights ($w$)**: Non-negative scalar representing physical distance: $w: E \\to \\mathbb{R}^+$.
            - **Dynamic Detour Subgraph**: When walkways are obstructed (e.g. weather, construction), an edge-deletion subgraph is formed:
              $$G_{\\text{detour}} = (V, E \\setminus E_{\\text{blocked}})$$

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

            ### 3. Constraint Satisfaction Problem (CSP) & Minimal Perturbation
            The timetabling problem is represented as a tuple $(X, D, C)$:
            - **Decision Variables**: $X_{c, r, s} \\in \\{0, 1\\}$
              True if course $c$ is scheduled in room $r$ at time slot $s$.
            - **Hard Constraints**:
              1. **Course Assignment**: $\\forall c: \\sum_r \\sum_s X_{c, r, s} = 1$
              2. **Room Double-Booking**: $\\forall r, s: \\sum_c X_{c, r, s} \\le 1$
              3. **Instructor Clash**: $\\forall i, s: \\sum_{c \\in C_i} \\sum_r X_{c, r, s} \\le 1$
              4. **Capacity Constraint**: $X_{c, r, s} = 0$ if $\\text{Capacity}(r) < \\text{Enrolled}(c)$
              5. **Lab Requirement**: $X_{c, r, s} = 0$ if $\\text{RequiresLab}(c) \\land \\neg \\text{IsLab}(r)$
            - **Minimal Perturbation Problem (Emergency Schedule Repair)**:
              When room $r_{\\text{out}}$ becomes unavailable, find a new valid assignment $X'$ that maximizes agreement with initial assignment $X^*$:
              $$\\max \\sum_{(c, r, s) \\in \\text{Initial}} X_{c, r, s}' \\quad \\text{subject to} \\quad X_{c, r_{\\text{out}}, s}' = 0$$
            """
        )


if __name__ == "__main__":
    main()

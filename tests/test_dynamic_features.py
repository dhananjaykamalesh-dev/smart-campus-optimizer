"""
Unit Tests for Phase B: Dynamic Campus Features
Tests Pathway Obstruction Rerouting, Room Unavailability Simulation,
Alternative Room Recommendations, and Minimal Timetable Repair.
"""

import os
import pytest
from src.navigation.graph_builder import CampusGraph
from src.navigation.pathfinder import CampusPathfinder
from src.scheduling.timetable_solver import CampusTimetableSolver

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
BUILDINGS_CSV = os.path.join(DATA_DIR, "buildings.csv")
PATHS_CSV = os.path.join(DATA_DIR, "paths.csv")
ROOMS_CSV = os.path.join(DATA_DIR, "rooms.csv")
COURSES_CSV = os.path.join(DATA_DIR, "courses.csv")
INSTRUCTORS_CSV = os.path.join(DATA_DIR, "instructors.csv")
TIME_SLOTS_CSV = os.path.join(DATA_DIR, "time_slots.csv")


@pytest.fixture
def campus_graph():
    return CampusGraph(buildings_file=BUILDINGS_CSV, paths_file=PATHS_CSV)


@pytest.fixture
def solver_instance():
    return CampusTimetableSolver(
        rooms_file=ROOMS_CSV,
        courses_file=COURSES_CSV,
        instructors_file=INSTRUCTORS_CSV,
        time_slots_file=TIME_SLOTS_CSV
    )


# -------------------------------------------------------------
# 1. NAVIGATION DYNAMIC REROUTING TESTS
# -------------------------------------------------------------
def test_blocked_subgraph_generation(campus_graph):
    """Verifies that blocked edges are successfully excised from the graph."""
    blocked = [("B2", "B3")]
    detour_g = campus_graph.get_blocked_subgraph(blocked_edges=blocked)

    assert detour_g.number_of_nodes() == campus_graph.graph.number_of_nodes()
    assert detour_g.number_of_edges() == campus_graph.graph.number_of_edges() - 1
    assert not detour_g.has_edge("B2", "B3")
    assert not detour_g.has_edge("B3", "B2")


def test_path_blocking_reroute_detour(campus_graph):
    """
    Tests dynamic rerouting when a key pathway on the optimal route is blocked.
    Original path from B1 to B5 traverses: B1 -> B2 -> B3 -> B5.
    If edge ('B2', 'B3') is blocked by construction, pathfinder must compute a detour.
    """
    pathfinder = CampusPathfinder(campus_graph.graph)
    reroute_res = pathfinder.find_reroute_with_blocked_edges(
        start_node="B1",
        goal_node="B5",
        blocked_edges=[("B2", "B3")],
        reason="Water Main Maintenance"
    )

    assert reroute_res["is_rerouted"] is True
    assert reroute_res["path_blocked"] is True
    assert reroute_res["reason"] == "Water Main Maintenance"

    # Verify original path traversed B2 -> B3
    assert "B2" in reroute_res["original_path"]
    assert "B3" in reroute_res["original_path"]

    # Verify updated detour does NOT traverse B2 <-> B3
    updated_path = reroute_res["updated_path"]
    for i in range(len(updated_path) - 1):
        edge = (updated_path[i], updated_path[i + 1])
        assert edge != ("B2", "B3") and edge != ("B3", "B2")

    # Detour distance should be longer or equal to original shortest path
    assert reroute_res["updated_distance"] >= reroute_res["original_distance"]
    assert reroute_res["distance_diff_m"] > 0


# -------------------------------------------------------------
# 2. SCHEDULING DISRUPTION & MINIMAL REPAIR TESTS
# -------------------------------------------------------------
def test_room_unavailability_simulation(solver_instance):
    """Verifies that affected courses are accurately detected when a room is closed."""
    initial_res = solver_instance.solve()
    assert initial_res["status"] in ("OPTIMAL", "FEASIBLE")

    # Pick a room currently holding courses
    used_room = initial_res["schedule"][0]["room_id"]
    sim_res = solver_instance.simulate_room_unavailability(used_room, initial_res["schedule"])

    assert sim_res["unavailable_room_id"] == used_room
    assert sim_res["affected_count"] >= 1
    for aff in sim_res["affected_courses"]:
        assert aff["room_id"] == used_room


def test_recommend_alternative_rooms(solver_instance, campus_graph):
    """
    Tests ranking of compatible alternative rooms based on capacity,
    facility equipment, and physical walking distance.
    """
    initial_res = solver_instance.solve()
    first_course = initial_res["schedule"][0]
    c_id = first_course["course_id"]
    s_id = first_course["slot_id"]

    recommendations = solver_instance.recommend_alternative_rooms(
        course_id=c_id,
        slot_id=s_id,
        current_schedule=initial_res["schedule"],
        campus_graph=campus_graph.graph
    )

    assert len(recommendations) > 0
    for cand in recommendations:
        # Candidate room must meet capacity
        assert cand["capacity"] >= first_course["enrolled"]
        # Candidate room must not be negative wasted seats
        assert cand["wasted_seats"] >= 0
        # Walking distance must be non-negative
        assert cand["walk_distance_from_orig_m"] >= 0.0


def test_minimal_timetable_repair(solver_instance):
    """
    Constraint Programming Minimal Perturbation Test:
    When a classroom is closed, CP-SAT repairs the timetable by moving affected
    courses while keeping the maximum number of other courses unchanged.
    """
    initial_res = solver_instance.solve()
    assert len(initial_res["schedule"]) > 0

    disrupted_room = initial_res["schedule"][0]["room_id"]
    disrupted_course = initial_res["schedule"][0]["course_id"]

    repair_res = solver_instance.repair_timetable_minimal_change(
        unavailable_room_id=disrupted_room,
        current_schedule=initial_res["schedule"]
    )

    assert repair_res["status"] in ("OPTIMAL", "FEASIBLE")
    assert repair_res["total_courses"] == len(initial_res["schedule"])

    # Invariant: Disrupted room must NEVER appear in repaired schedule
    repaired_rooms = {item["room_id"] for item in repair_res["repaired_schedule"]}
    assert disrupted_room not in repaired_rooms

    # Stability test: At least 70% of courses should remain in their original room
    assert repair_res["schedule_stability_pct"] >= 70.0
    assert repair_res["unchanged_courses_count"] >= 1
    assert repair_res["changed_courses_count"] >= 1

    # Verify no room double-booking in repaired schedule
    room_slots = [(item["room_id"], item["slot_id"]) for item in repair_res["repaired_schedule"]]
    assert len(room_slots) == len(set(room_slots)), "Repaired schedule must have zero room collisions"


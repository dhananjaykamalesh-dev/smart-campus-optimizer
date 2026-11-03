"""
Unit Tests for Phase A Enhancements:
Tests algorithm comparison benchmarking, graph summary metrics, and CSV export utilities.
"""

import os
import pytest
import pandas as pd
from src.navigation.graph_builder import CampusGraph
from src.navigation.pathfinder import CampusPathfinder
from src.scheduling.timetable_solver import CampusTimetableSolver

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
BUILDINGS_CSV = os.path.join(DATA_DIR, "buildings.csv")
PATHS_CSV = os.path.join(DATA_DIR, "paths.csv")


@pytest.fixture
def campus_graph():
    """Returns an initialized CampusGraph."""
    return CampusGraph(buildings_file=BUILDINGS_CSV, paths_file=PATHS_CSV)


def test_graph_summary_metrics(campus_graph):
    """Verifies that get_graph_summary returns accurate campus structural counts."""
    summary = campus_graph.get_graph_summary()

    assert summary["num_buildings"] == 10
    assert summary["num_paths"] >= 15
    assert summary["num_accessible_paths"] > 0
    assert summary["num_accessible_paths"] < summary["num_paths"]  # Some paths have stairs
    assert summary["is_connected"] is True


def test_compare_algorithms_benchmark(campus_graph):
    """
    Verifies that compare_algorithms properly runs both Dijkstra and A*,
    asserts optimal distance match, and provides execution time.
    """
    pathfinder = CampusPathfinder(campus_graph.graph)
    comp = pathfinder.compare_algorithms("B1", "B5")

    assert comp["optimal_match"] is True
    assert comp["dijkstra"]["total_distance"] == comp["astar"]["total_distance"]
    assert "execution_time_ms" in comp["dijkstra"]
    assert "execution_time_ms" in comp["astar"]
    assert comp["dijkstra"]["execution_time_ms"] >= 0.0
    assert comp["astar"]["execution_time_ms"] >= 0.0
    assert isinstance(comp["nodes_saved_by_astar"], int)


def test_route_and_timetable_csv_export():
    """Verifies that route itinerary and timetable DataFrames export to valid CSV bytes."""
    # Route DataFrame sample
    route_df = pd.DataFrame([
        {"Step": 1, "Building ID": "B1", "Directions": "Start at Main Gate"},
        {"Step": 2, "Building ID": "B2", "Directions": "Walk to Admin Block (+120m)"}
    ])
    csv_bytes = route_df.to_csv(index=False).encode("utf-8")
    assert b"Step,Building ID,Directions" in csv_bytes

    # Timetable DataFrame sample from solver
    solver = CampusTimetableSolver(
        rooms_file=os.path.join(DATA_DIR, "rooms.csv"),
        courses_file=os.path.join(DATA_DIR, "courses.csv"),
        instructors_file=os.path.join(DATA_DIR, "instructors.csv"),
        time_slots_file=os.path.join(DATA_DIR, "time_slots.csv")
    )
    result = solver.solve()
    assert not result["schedule_df"].empty
    sched_csv_bytes = result["schedule_df"].to_csv(index=False).encode("utf-8")
    assert b"course_id" in sched_csv_bytes or b"course_name" in sched_csv_bytes


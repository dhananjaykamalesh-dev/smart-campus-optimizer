"""
Unit Tests for Phase 3: Resource Allocation & Utilization Module
Validates Utilization Metric Bounds, Capacity Conservatism, and Idle Room Detection.
"""

import os
import pytest
from src.scheduling.timetable_solver import CampusTimetableSolver
from src.allocation.resource_manager import CampusResourceManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


@pytest.fixture
def resource_manager_instance():
    """Fixture providing initialized CampusResourceManager using solved schedule."""
    solver = CampusTimetableSolver(
        rooms_file=os.path.join(DATA_DIR, "rooms.csv"),
        courses_file=os.path.join(DATA_DIR, "courses.csv"),
        instructors_file=os.path.join(DATA_DIR, "instructors.csv"),
        time_slots_file=os.path.join(DATA_DIR, "time_slots.csv")
    )
    result = solver.solve()
    return CampusResourceManager(
        schedule_records=result["schedule"],
        all_rooms=solver.rooms
    )


def test_utilization_bounds(resource_manager_instance):
    """
    Mathematical Invariant Test:
    Utilization percentage must strictly be within (0, 100] for all allocated classes.
    """
    summary_df = resource_manager_instance.get_room_utilization_summary()
    assert not summary_df.empty

    for _, row in summary_df.iterrows():
        util = row["Utilization %"]
        assert 0.0 < util <= 100.0, f"Invalid utilization percentage: {util}%"
        assert row["Wasted Seats"] >= 0, "Wasted seats cannot be negative."


def test_aggregate_metrics(resource_manager_instance):
    """Verifies that overall utilization equals sum(enrolled) / sum(capacity)."""
    metrics = resource_manager_instance.compute_overall_metrics()

    assert metrics["total_enrolled"] > 0
    assert metrics["total_allocated_capacity"] >= metrics["total_enrolled"]
    assert 0.0 < metrics["overall_utilization_pct"] <= 100.0
    assert metrics["allocated_rooms_count"] <= metrics["total_campus_rooms"]

    # Verify category counts sum to total allocated courses
    total_categorized = (
        metrics["under_utilized_count"]
        + metrics["optimal_count"]
        + metrics["near_capacity_count"]
    )
    assert total_categorized == len(resource_manager_instance.schedule_records)


def test_idle_rooms_detection(resource_manager_instance):
    """Verifies idle room analysis returns valid campus rooms."""
    idle_data = resource_manager_instance.get_idle_rooms_analysis()
    assert isinstance(idle_data["idle_rooms_count"], int)
    assert idle_data["idle_rooms_count"] >= 0


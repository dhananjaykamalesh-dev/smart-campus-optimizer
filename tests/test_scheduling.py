"""
Unit Tests for Phase 2: Classroom Scheduling Module
Validates CP-SAT Constraint Satisfaction Timetable Formulation.
"""

import os
import pytest
from src.scheduling.timetable_solver import CampusTimetableSolver

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ROOMS_CSV = os.path.join(DATA_DIR, "rooms.csv")
COURSES_CSV = os.path.join(DATA_DIR, "courses.csv")
INSTRUCTORS_CSV = os.path.join(DATA_DIR, "instructors.csv")
TIME_SLOTS_CSV = os.path.join(DATA_DIR, "time_slots.csv")


@pytest.fixture
def solver_instance():
    """Fixture providing initialized CampusTimetableSolver."""
    return CampusTimetableSolver(
        rooms_file=ROOMS_CSV,
        courses_file=COURSES_CSV,
        instructors_file=INSTRUCTORS_CSV,
        time_slots_file=TIME_SLOTS_CSV
    )


def test_solver_finds_optimal_schedule(solver_instance):
    """Verifies that CP-SAT finds an OPTIMAL or FEASIBLE schedule."""
    result = solver_instance.solve(optimize_capacity=True)
    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert result["solve_time_sec"] < 5.0  # Solver should take under 5 seconds
    assert len(result["schedule"]) > 0


def test_all_courses_are_scheduled(solver_instance):
    """Verifies that 100% of courses from courses.csv are scheduled."""
    result = solver_instance.solve()
    scheduled_courses = {item["course_id"] for item in result["schedule"]}
    all_courses = set(solver_instance.courses.keys())

    assert scheduled_courses == all_courses, "All courses must be scheduled exactly once."


def test_no_room_collisions(solver_instance):
    """
    Propositional Hard Constraint Test:
    Ensures no room is assigned two different classes during the same time slot.
    """
    result = solver_instance.solve()
    room_slot_pairs = [(item["room_id"], item["slot_id"]) for item in result["schedule"]]

    # In a collision-free timetable, set length must equal list length (no duplicates)
    assert len(room_slot_pairs) == len(set(room_slot_pairs)), (
        "Room collision detected: A room was double-booked in the same time slot!"
    )


def test_no_instructor_collisions(solver_instance):
    """
    Propositional Hard Constraint Test:
    Ensures no instructor is assigned to teach two classes at the same time.
    """
    result = solver_instance.solve()
    instructor_slot_pairs = [(item["instructor"], item["slot_id"]) for item in result["schedule"]]

    assert len(instructor_slot_pairs) == len(set(instructor_slot_pairs)), (
        "Instructor clash detected: A professor was scheduled for two classes simultaneously!"
    )


def test_capacity_and_lab_invariants(solver_instance):
    """
    Verifies that for every scheduled class:
    1. Room capacity is greater than or equal to enrolled students.
    2. Lab courses are assigned to lab rooms.
    """
    result = solver_instance.solve()
    for item in result["schedule"]:
        c_id = item["course_id"]
        course_meta = solver_instance.courses[c_id]

        # Capacity check
        assert item["capacity"] >= item["enrolled"], (
            f"Capacity violation: Room {item['room_id']} ({item['capacity']} seats) "
            f"cannot hold course {c_id} ({item['enrolled']} students)!"
        )

        # Lab requirement check
        if course_meta["requires_lab"]:
            assert item["is_lab"] is True, (
                f"Facility violation: Course {c_id} requires a lab but was assigned to {item['room_id']}!"
            )


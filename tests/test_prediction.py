"""
Unit Tests for Phase D: Historical Demand Prediction & Soft Preference Module
Validates Moving Average, Day-of-Week profiling, and soft preference CP-SAT integration.
"""

import os
import pytest
import pandas as pd
from src.prediction.demand_predictor import CampusDemandPredictor
from src.scheduling.timetable_solver import CampusTimetableSolver

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORICAL_CSV = os.path.join(DATA_DIR, "historical_demand.csv")
ROOMS_CSV = os.path.join(DATA_DIR, "rooms.csv")
COURSES_CSV = os.path.join(DATA_DIR, "courses.csv")
INSTRUCTORS_CSV = os.path.join(DATA_DIR, "instructors.csv")
TIME_SLOTS_CSV = os.path.join(DATA_DIR, "time_slots.csv")


@pytest.fixture
def predictor_instance():
    """Provides an initialized CampusDemandPredictor."""
    return CampusDemandPredictor(historical_csv_path=HISTORICAL_CSV)


@pytest.fixture
def solver_instance():
    """Provides an initialized CampusTimetableSolver."""
    return CampusTimetableSolver(
        rooms_file=ROOMS_CSV,
        courses_file=COURSES_CSV,
        instructors_file=INSTRUCTORS_CSV,
        time_slots_file=TIME_SLOTS_CSV
    )


def test_load_historical_demand_data(predictor_instance):
    """Verifies that historical demand dataset loads with required columns."""
    df = predictor_instance.df
    assert not df.empty, "Historical demand data must not be empty."
    assert "week" in df.columns
    assert "slot_id" in df.columns
    assert "attendance_count" in df.columns
    assert df["attendance_count"].min() > 0, "Attendance count must be strictly positive."


def test_moving_average_prediction(predictor_instance):
    """
    Mathematical Invariant Test:
    Verifies that the moving average prediction is bounded by the min and max
    attendance observed in the moving window.
    """
    window = 2
    predictions = predictor_instance.predict_slot_demand_moving_average(window_size=window)
    assert len(predictions) > 0, "Must return predictions for time slots."

    df = predictor_instance.df
    recent_df = df[df["week"] >= (df["week"].max() - window + 1)]

    for slot_id, pred_val in predictions.items():
        slot_records = recent_df[recent_df["slot_id"] == slot_id]["attendance_count"]
        if not slot_records.empty:
            assert slot_records.min() <= pred_val <= slot_records.max(), (
                f"Predicted value {pred_val} must be within historical window bounds "
                f"[{slot_records.min()}, {slot_records.max()}]"
            )


def test_day_of_week_average(predictor_instance):
    """Verifies day-of-week demand aggregation produces valid day groupings."""
    day_avg = predictor_instance.predict_day_of_week_average()
    assert "Monday" in day_avg
    assert "Friday" in day_avg
    assert day_avg["Monday"] > 0.0
    assert day_avg["Friday"] > 0.0


def test_get_slot_demand_summary(predictor_instance):
    """Verifies summary DataFrame contains formatted metadata and demand classifications."""
    summary_df = predictor_instance.get_slot_demand_summary()
    assert not summary_df.empty
    assert "Slot ID" in summary_df.columns
    assert "Predicted Attendance" in summary_df.columns
    assert "Demand Level" in summary_df.columns
    assert set(summary_df["Demand Level"].unique()).issubset({"High Peak", "Moderate", "Low Demand"})


def test_soft_preference_penalties_generation(predictor_instance, solver_instance):
    """Verifies that soft preference penalty dictionary contains valid non-negative integer penalties."""
    penalties = predictor_instance.compute_soft_preference_penalties(
        courses=solver_instance.courses,
        rooms=solver_instance.rooms,
        time_slots=solver_instance.time_slots,
        penalty_scale=2
    )
    assert isinstance(penalties, dict)
    assert len(penalties) > 0

    for key, penalty_val in penalties.items():
        assert len(key) == 3  # (course_id, room_id, slot_id)
        assert isinstance(penalty_val, int)
        assert penalty_val >= 0, "Penalties must be non-negative."


def test_solve_with_demand_prediction_finds_valid_schedule(predictor_instance, solver_instance):
    """
    CP-SAT Integration Test:
    Ensures solving with soft demand preferences maintains all hard constraints:
    1. Status is OPTIMAL or FEASIBLE
    2. All courses are scheduled
    3. No room or instructor collisions
    """
    result = solver_instance.solve_with_demand_prediction(predictor=predictor_instance, penalty_scale=2)
    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(result["schedule"]) == len(solver_instance.courses)

    # Verify no room double-booking
    room_slots = [(item["room_id"], item["slot_id"]) for item in result["schedule"]]
    assert len(room_slots) == len(set(room_slots)), "No room may be double booked."

    # Verify no instructor double-booking
    inst_slots = [(item["instructor"], item["slot_id"]) for item in result["schedule"]]
    assert len(inst_slots) == len(set(inst_slots)), "No instructor may teach two classes simultaneously."

r"""
Module: demand_predictor.py
Purpose: Baseline room and time-slot demand prediction using synthetic historical attendance data.

Discrete Mathematics Relevance:
-------------------------------
1. Statistical Time-Series Baselines:
   - Moving Average (Window K):
     $$\hat{D}_{s} = \frac{1}{K} \sum_{k=1}^K D_{s, W-k+1}$$
     where $D_{s, w}$ is historical attendance in time slot $s$ at week $w$.
   - Day-of-Week Profiling:
     $$\bar{D}_{d} = \frac{1}{|S_d|} \sum_{s \in S_d} D_s$$
     Aggregating demand patterns across days (e.g. Monday-Thursday peak vs. Friday afternoon drop).

2. Soft-Constraint Penalty in Combinatorial Optimization:
   - Rather than introducing rigid hard constraints that risk rendering the CP-SAT model INFEASIBLE,
     predicted demand is converted into linear soft penalty terms added to the objective:
     $$\min \sum_{c, r, s} X_{c,r,s} \cdot (\text{Waste}_{c,r} + \text{Penalty}_{c,r,s})$$
   - If slot $s$ is predicted to experience high campus-wide demand, assigning small courses
     to large rooms in slot $s$ incurs a penalty, saving large rooms for high-demand needs.

Status:
-------
🧪 [EXPERIMENTAL ENHANCEMENT] — Academic baseline model.
"""

from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np


class CampusDemandPredictor:
    """
    Experimental baseline demand predictor that utilizes historical attendance records
    to forecast time-slot utilization trends and produce soft preference weights for scheduling.
    """

    def __init__(self, historical_csv_path: Optional[str] = None):
        """
        Initializes the demand predictor.

        Args:
            historical_csv_path: Path to the CSV containing historical booking/attendance records.
        """
        self.historical_csv_path = historical_csv_path
        self.df: pd.DataFrame = pd.DataFrame()
        if historical_csv_path:
            self.load_data(historical_csv_path)

    def load_data(self, csv_path: str) -> pd.DataFrame:
        """
        Loads and parses the historical attendance CSV.

        Args:
            csv_path: Path to historical_demand.csv

        Returns:
            pd.DataFrame of historical demand records.
        """
        self.df = pd.read_csv(csv_path)
        required_cols = {"week", "slot_id", "day", "period", "attendance_count"}
        missing = required_cols - set(self.df.columns)
        if missing:
            raise ValueError(f"Historical demand data is missing columns: {missing}")
        return self.df

    def predict_slot_demand_moving_average(self, window_size: int = 3) -> Dict[str, float]:
        r"""
        Forecasts average student attendance per time slot using a moving average of recent weeks.

        Formula:
            $$\hat{D}_{s} = \frac{1}{K} \sum_{k=1}^K D_{s, W-k+1}$$

        Args:
            window_size: Number of most recent weeks to include in the average (default: 3).

        Returns:
            Dictionary mapping slot_id (e.g. 'TS1') to predicted attendance (float).
        """
        if self.df.empty:
            return {}

        max_week = self.df["week"].max()
        min_week = max(1, max_week - window_size + 1)
        recent_df = self.df[self.df["week"] >= min_week]

        # Group by slot_id and compute mean attendance
        slot_means = recent_df.groupby("slot_id")["attendance_count"].mean().to_dict()
        # Round to 1 decimal place for clean interpretation
        return {slot: round(float(val), 1) for slot, val in slot_means.items()}

    def predict_day_of_week_average(self) -> Dict[str, float]:
        """
        Computes the aggregate mean attendance grouped by day of the week.

        Returns:
            Dictionary mapping day name ('Monday', 'Tuesday', etc.) to mean attendance.
        """
        if self.df.empty:
            return {}

        day_means = self.df.groupby("day")["attendance_count"].mean().to_dict()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        ordered_results = {}
        for d in day_order:
            if d in day_means:
                ordered_results[d] = round(float(day_means[d]), 1)
        return ordered_results

    def get_slot_demand_summary(self, window_size: int = 3) -> pd.DataFrame:
        """
        Builds a comprehensive DataFrame comparing time slot details with predicted demand.

        Returns:
            pd.DataFrame with columns: Slot ID, Day, Period, Predicted Attendance, Demand Classification.
        """
        if self.df.empty:
            return pd.DataFrame()

        predictions = self.predict_slot_demand_moving_average(window_size=window_size)
        slot_meta = self.df[["slot_id", "day", "period"]].drop_duplicates().set_index("slot_id")

        rows = []
        for slot_id, pred_att in predictions.items():
            day = slot_meta.loc[slot_id, "day"] if slot_id in slot_meta.index else "Unknown"
            period = slot_meta.loc[slot_id, "period"] if slot_id in slot_meta.index else "Unknown"

            if pred_att >= 60.0:
                level = "High Peak"
            elif pred_att >= 40.0:
                level = "Moderate"
            else:
                level = "Low Demand"

            rows.append({
                "Slot ID": slot_id,
                "Day": day,
                "Period": period,
                "Predicted Attendance": pred_att,
                "Demand Level": level
            })

        df_summary = pd.DataFrame(rows)
        # Sort by slot_id numeric order if possible
        if not df_summary.empty:
            df_summary["sort_key"] = df_summary["Slot ID"].apply(
                lambda s: int(s.replace("TS", "")) if s.startswith("TS") and s[2:].isdigit() else 999
            )
            df_summary = df_summary.sort_values("sort_key").drop(columns=["sort_key"])
        return df_summary

    def compute_soft_preference_penalties(
        self,
        courses: Dict[str, Dict[str, Any]],
        rooms: Dict[str, Dict[str, Any]],
        time_slots: Dict[str, Dict[str, Any]],
        penalty_scale: int = 2
    ) -> Dict[Tuple[str, str, str], int]:
        """
        Generates soft penalty coefficients for CP-SAT objective minimization.

        Concept:
        - If a slot is predicted to have HIGH demand (e.g. attendance >= 50),
          assigning a small course (enrolled < 40) to a large room (capacity >= 60)
          receives a soft penalty of `(capacity - enrolled) * penalty_scale`.
        - This guides the solver to reserve high-capacity rooms during high-demand slots
          for larger courses, without breaking any hard scheduling constraints.

        Args:
            courses: Dictionary of courses from CampusTimetableSolver.
            rooms: Dictionary of rooms from CampusTimetableSolver.
            time_slots: Dictionary of time slots.
            penalty_scale: Multiplier for soft penalty weighting (default: 2).

        Returns:
            Dictionary mapping (course_id, room_id, slot_id) to integer penalty weight.
        """
        slot_predictions = self.predict_slot_demand_moving_average()
        penalties: Dict[Tuple[str, str, str], int] = {}

        for c_id, course in courses.items():
            enrolled = course.get("enrolled_students", 0)
            for r_id, room in rooms.items():
                capacity = room.get("capacity", 0)
                for s_id in time_slots.keys():
                    pred_demand = slot_predictions.get(s_id, 40.0)

                    penalty = 0
                    # Peak slot with small class in oversized room
                    if pred_demand >= 50.0 and enrolled < 40 and capacity >= 60:
                        penalty = int((capacity - enrolled) * penalty_scale)
                    # Low demand slot (e.g. Friday P3) receives slight bonus (0 penalty)
                    elif pred_demand < 30.0 and capacity <= 40:
                        penalty = 0

                    penalties[(c_id, r_id, s_id)] = penalty

        return penalties

"""
Module: timetable_solver.py
Purpose: Solves the university course timetabling problem using Constraint Programming (CP).

Discrete Mathematics Relevance:
-------------------------------
Constraint Satisfaction Problem (CSP) & Propositional Logic:
A CSP is defined by a tuple (X, D, C):
- X = Set of variables: X_{c, r, s} in {0, 1}
      Represents Boolean proposition: "Course c is scheduled in Room r at Time Slot s".
- D = Domain: {0, 1} (Binary decision).
- C = Set of constraints (Hard propositional logic formulas):
  1. Exact Course Assignment:
     sum_{r} sum_{s} X_{c, r, s} = 1, for all courses c
  2. Room Conflict-Free (No double-booking):
     sum_{c} X_{c, r, s} <= 1, for all rooms r, time slots s
  3. Teacher Conflict-Free (No double-booking):
     sum_{c in C_i} sum_{r} X_{c, r, s} <= 1, for all instructors i, time slots s
  4. Room Capacity Invariant:
     X_{c, r, s} = 0 if Capacity(r) < Enrolled(c)
  5. Facility Requirement:
     X_{c, r, s} = 0 if RequiresLab(c) and not IsLab(r)

Engine: Google OR-Tools CP-SAT Solver (SAT-based finite domain constraint solver).
"""

import os
import csv
import time
from typing import Dict, List, Any, Optional
import pandas as pd
from ortools.sat.python import cp_model


class CampusTimetableSolver:
    """
    Formulates and solves classroom timetabling as a Constraint Satisfaction Problem.
    """

    def __init__(
        self,
        rooms_file: str,
        courses_file: str,
        instructors_file: str,
        time_slots_file: str
    ):
        """
        Initializes solver with file paths to CSV data files.

        Args:
            rooms_file: Path to rooms.csv
            courses_file: Path to courses.csv
            instructors_file: Path to instructors.csv
            time_slots_file: Path to time_slots.csv
        """
        self.rooms_file = rooms_file
        self.courses_file = courses_file
        self.instructors_file = instructors_file
        self.time_slots_file = time_slots_file

        # Data structures
        self.rooms: Dict[str, Dict[str, Any]] = {}
        self.courses: Dict[str, Dict[str, Any]] = {}
        self.instructors: Dict[str, Dict[str, Any]] = {}
        self.time_slots: Dict[str, Dict[str, Any]] = {}

        self.load_data()

    def load_data(self) -> None:
        """
        Reads CSV files and populates entity dictionaries.
        """
        # Load Rooms
        with open(self.rooms_file, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rid = row["room_id"].strip()
                self.rooms[rid] = {
                    "room_id": rid,
                    "building_id": row["building_id"].strip(),
                    "name": row["name"].strip(),
                    "capacity": int(row["capacity"]),
                    "is_lab": row["is_lab"].strip().lower() in ("true", "1", "yes")
                }

        # Load Instructors
        with open(self.instructors_file, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                iid = row["instructor_id"].strip()
                self.instructors[iid] = {
                    "instructor_id": iid,
                    "name": row["name"].strip(),
                    "department": row["department"].strip()
                }

        # Load Courses
        with open(self.courses_file, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = row["course_id"].strip()
                self.courses[cid] = {
                    "course_id": cid,
                    "name": row["name"].strip(),
                    "instructor_id": row["instructor_id"].strip(),
                    "enrolled_students": int(row["enrolled_students"]),
                    "requires_lab": row["requires_lab"].strip().lower() in ("true", "1", "yes")
                }

        # Load Time Slots
        with open(self.time_slots_file, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sid = row["slot_id"].strip()
                self.time_slots[sid] = {
                    "slot_id": sid,
                    "day": row["day"].strip(),
                    "period": row["period"].strip(),
                    "start_time": row["start_time"].strip(),
                    "end_time": row["end_time"].strip()
                }

    def solve(self, optimize_capacity: bool = True) -> Dict[str, Any]:
        """
        Builds the CP-SAT model, sets constraints, and finds an optimal conflict-free schedule.

        Args:
            optimize_capacity: If True, minimizes wasted seats in assigned rooms.

        Returns:
            Dictionary containing:
            - 'status': Solver status ('OPTIMAL', 'FEASIBLE', or 'INFEASIBLE')
            - 'solve_time_sec': Execution duration in seconds
            - 'schedule': List of scheduled assignments
            - 'schedule_df': Formatted pandas DataFrame
            - 'metrics': Summary metrics (utilization %, conflicts count)
        """
        model = cp_model.CpModel()
        start_time = time.time()

        # -------------------------------------------------------------
        # STEP 1: DEFINE DECISION VARIABLES
        # -------------------------------------------------------------
        # X[c, r, s] is a Boolean variable:
        # True (1) if course c is held in room r at time slot s; False (0) otherwise.
        x_vars = {}

        for c_id, course in self.courses.items():
            for r_id, room in self.rooms.items():
                # Pruning domain early (Node Consistency):
                # If room is too small or lacks required lab equipment, cannot assign.
                if room["capacity"] < course["enrolled_students"]:
                    continue
                if course["requires_lab"] and not room["is_lab"]:
                    continue

                for s_id in self.time_slots.keys():
                    var_name = f"X_{c_id}_{r_id}_{s_id}"
                    x_vars[(c_id, r_id, s_id)] = model.NewBoolVar(var_name)

        # -------------------------------------------------------------
        # STEP 2: HARD CONSTRAINT 1 - Every Course Must Be Scheduled Once
        # -------------------------------------------------------------
        # In Propositional Logic: ExactlyOne(X_{c, r, s}) across all valid (r, s)
        for c_id in self.courses.keys():
            valid_assignments_for_course = [
                x_vars[(c_id, r_id, s_id)]
                for r_id in self.rooms.keys()
                for s_id in self.time_slots.keys()
                if (c_id, r_id, s_id) in x_vars
            ]
            if not valid_assignments_for_course:
                return {
                    "status": "INFEASIBLE",
                    "error": f"Course '{self.courses[c_id]['name']}' cannot fit in any room with matching capacity and lab facilities.",
                    "schedule": [],
                    "schedule_df": pd.DataFrame(),
                    "solve_time_sec": round(time.time() - start_time, 3)
                }
            model.AddExactlyOne(valid_assignments_for_course)

        # -------------------------------------------------------------
        # STEP 3: HARD CONSTRAINT 2 - Room No Double-Booking
        # -------------------------------------------------------------
        # For each room and each time slot, at most 1 course can be present:
        # sum_{c} X_{c, r, s} <= 1
        for r_id in self.rooms.keys():
            for s_id in self.time_slots.keys():
                courses_in_room_slot = [
                    x_vars[(c_id, r_id, s_id)]
                    for c_id in self.courses.keys()
                    if (c_id, r_id, s_id) in x_vars
                ]
                if courses_in_room_slot:
                    model.AddAtMostOne(courses_in_room_slot)

        # -------------------------------------------------------------
        # STEP 4: HARD CONSTRAINT 3 - Instructor No Double-Booking
        # -------------------------------------------------------------
        # An instructor cannot teach two courses at the same time:
        # sum_{c in C_instructor} sum_{r} X_{c, r, s} <= 1
        for i_id in self.instructors.keys():
            # Get all courses taught by this instructor
            inst_courses = [
                c_id for c_id, c in self.courses.items()
                if c["instructor_id"] == i_id
            ]
            for s_id in self.time_slots.keys():
                assignments_for_instructor = [
                    x_vars[(c_id, r_id, s_id)]
                    for c_id in inst_courses
                    for r_id in self.rooms.keys()
                    if (c_id, r_id, s_id) in x_vars
                ]
                if assignments_for_instructor:
                    model.AddAtMostOne(assignments_for_instructor)

        # -------------------------------------------------------------
        # STEP 5: SOFT OBJECTIVE - Minimize Seat Wastage
        # -------------------------------------------------------------
        # Wasted Seats = Room Capacity - Course Enrollment
        # Minimizing this objective ensures tight, efficient room allocations.
        if optimize_capacity:
            wastage_terms = []
            for (c_id, r_id, s_id), var in x_vars.items():
                waste = self.rooms[r_id]["capacity"] - self.courses[c_id]["enrolled_students"]
                wastage_terms.append(var * waste)
            model.Minimize(sum(wastage_terms))

        # -------------------------------------------------------------
        # STEP 6: EXECUTE SOLVER
        # -------------------------------------------------------------
        solver = cp_model.CpSolver()
        # Give solver a 10-second limit (typically completes in 50ms)
        solver.parameters.max_time_in_seconds = 10.0
        status_code = solver.Solve(model)
        elapsed_time = round(time.time() - start_time, 4)

        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "MODEL_INVALID",
            cp_model.UNKNOWN: "UNKNOWN"
        }
        status_str = status_map.get(status_code, "UNKNOWN")

        if status_str not in ("OPTIMAL", "FEASIBLE"):
            return {
                "status": status_str,
                "solve_time_sec": elapsed_time,
                "error": "Could not find a feasible schedule satisfying all constraints.",
                "schedule": [],
                "schedule_df": pd.DataFrame()
            }

        # -------------------------------------------------------------
        # STEP 7: EXTRACT SOLUTION & COMPUTE METRICS
        # -------------------------------------------------------------
        schedule = []
        total_enrolled = 0
        total_capacity = 0

        for (c_id, r_id, s_id), var in x_vars.items():
            if solver.BooleanValue(var):
                c_data = self.courses[c_id]
                r_data = self.rooms[r_id]
                s_data = self.time_slots[s_id]
                i_data = self.instructors[c_data["instructor_id"]]

                cap = r_data["capacity"]
                enrolled = c_data["enrolled_students"]
                utilization = round((enrolled / cap) * 100.0, 1)

                total_enrolled += enrolled
                total_capacity += cap

                schedule.append({
                    "course_id": c_id,
                    "course_name": c_data["name"],
                    "instructor": i_data["name"],
                    "room_id": r_id,
                    "room_name": r_data["name"],
                    "building_id": r_data["building_id"],
                    "day": s_data["day"],
                    "period": s_data["period"],
                    "time": f"{s_data['start_time']} - {s_data['end_time']}",
                    "slot_id": s_id,
                    "enrolled": enrolled,
                    "capacity": cap,
                    "wasted_seats": cap - enrolled,
                    "utilization_pct": utilization,
                    "is_lab": r_data["is_lab"]
                })

        # Day order for natural weekly display
        day_order = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5}
        schedule.sort(key=lambda item: (day_order.get(item["day"], 9), item["period"], item["room_name"]))

        schedule_df = pd.DataFrame(schedule)
        avg_utilization = round((total_enrolled / total_capacity) * 100.0, 1) if total_capacity > 0 else 0.0

        return {
            "status": status_str,
            "solve_time_sec": elapsed_time,
            "total_courses": len(schedule),
            "average_utilization": avg_utilization,
            "schedule": schedule,
            "schedule_df": schedule_df
        }


"""
Module: timetable_solver.py
Purpose: Solves the university course timetabling problem using Constraint Programming (CP),
         with support for room disruption simulation, candidate recommendations,
         and minimal-perturbation timetable repair.

Discrete Mathematics Relevance:
-------------------------------
Constraint Satisfaction Problem (CSP) & Minimal Perturbation:
- Variables: X_{c, r, s} in {0, 1}
- Hard constraints eliminate collisions (no double-booking, capacity, lab requirements).
- Minimal Perturbation Problem (MPP):
  When an unexpected disruption occurs (e.g. room outage), the goal is to find a new
  consistent assignment X' that maximizes stability with respect to the initial assignment X*:
  max sum_{(c, r, s) in InitialSchedule} X_{c, r, s}
  subject to X_{c, unavailable_room, s} = 0
"""

import os
import csv
import time
from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import networkx as nx
from ortools.sat.python import cp_model


class CampusTimetableSolver:
    """
    Formulates and solves classroom timetabling as a Constraint Satisfaction Problem,
    including emergency disruption simulation and minimal-change timetable repair.
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

        self.rooms: Dict[str, Dict[str, Any]] = {}
        self.courses: Dict[str, Dict[str, Any]] = {}
        self.instructors: Dict[str, Dict[str, Any]] = {}
        self.time_slots: Dict[str, Dict[str, Any]] = {}

        self.load_data()

    def load_data(self) -> None:
        """Reads CSV files and populates entity dictionaries."""
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

        with open(self.instructors_file, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                iid = row["instructor_id"].strip()
                self.instructors[iid] = {
                    "instructor_id": iid,
                    "name": row["name"].strip(),
                    "department": row["department"].strip()
                }

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

    def solve(
        self,
        optimize_capacity: bool = True,
        forbidden_rooms: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Builds the CP-SAT model, sets constraints, and finds a conflict-free schedule.

        Args:
            optimize_capacity: If True, minimizes wasted seats in assigned rooms.
            forbidden_rooms: Optional set of room IDs excluded from assignment (out of service).

        Returns:
            Dictionary with solver status, runtime, metrics, and schedule list/DataFrame.
        """
        model = cp_model.CpModel()
        start_time = time.time()
        forbidden = forbidden_rooms or set()

        x_vars = {}
        for c_id, course in self.courses.items():
            for r_id, room in self.rooms.items():
                if r_id in forbidden:
                    continue
                if room["capacity"] < course["enrolled_students"]:
                    continue
                if course["requires_lab"] and not room["is_lab"]:
                    continue

                for s_id in self.time_slots.keys():
                    var_name = f"X_{c_id}_{r_id}_{s_id}"
                    x_vars[(c_id, r_id, s_id)] = model.NewBoolVar(var_name)

        # Hard Constraint 1: Exactly one assignment per course
        for c_id in self.courses.keys():
            valid_assignments = [
                x_vars[(c_id, r_id, s_id)]
                for r_id in self.rooms.keys()
                for s_id in self.time_slots.keys()
                if (c_id, r_id, s_id) in x_vars
            ]
            if not valid_assignments:
                return {
                    "status": "INFEASIBLE",
                    "error": f"Course '{self.courses[c_id]['name']}' cannot fit in any available room.",
                    "schedule": [],
                    "schedule_df": pd.DataFrame(),
                    "solve_time_sec": round(time.time() - start_time, 3)
                }
            model.AddExactlyOne(valid_assignments)

        # Hard Constraint 2: Room conflict-free
        for r_id in self.rooms.keys():
            if r_id in forbidden:
                continue
            for s_id in self.time_slots.keys():
                courses_in_room = [
                    x_vars[(c_id, r_id, s_id)]
                    for c_id in self.courses.keys()
                    if (c_id, r_id, s_id) in x_vars
                ]
                if courses_in_room:
                    model.AddAtMostOne(courses_in_room)

        # Hard Constraint 3: Teacher conflict-free
        for i_id in self.instructors.keys():
            inst_courses = [c_id for c_id, c in self.courses.items() if c["instructor_id"] == i_id]
            for s_id in self.time_slots.keys():
                teacher_assignments = [
                    x_vars[(c_id, r_id, s_id)]
                    for c_id in inst_courses
                    for r_id in self.rooms.keys()
                    if (c_id, r_id, s_id) in x_vars
                ]
                if teacher_assignments:
                    model.AddAtMostOne(teacher_assignments)

        # Soft Objective: Minimize wasted seats
        if optimize_capacity:
            wastage_terms = []
            for (c_id, r_id, s_id), var in x_vars.items():
                waste = self.rooms[r_id]["capacity"] - self.courses[c_id]["enrolled_students"]
                wastage_terms.append(var * waste)
            model.Minimize(sum(wastage_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        status_code = solver.Solve(model)
        elapsed_time = round(time.time() - start_time, 4)

        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE"
        }
        status_str = status_map.get(status_code, "INFEASIBLE")

        if status_str not in ("OPTIMAL", "FEASIBLE"):
            return {
                "status": status_str,
                "solve_time_sec": elapsed_time,
                "error": "Could not find a feasible schedule satisfying all constraints.",
                "schedule": [],
                "schedule_df": pd.DataFrame()
            }

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

    # -----------------------------------------------------------------
    # PHASE B DYNAMIC FEATURES: DISRUPTION, RECOMMENDATION & REPAIR
    # -----------------------------------------------------------------
    def simulate_room_unavailability(
        self,
        unavailable_room_id: str,
        current_schedule: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simulates an unexpected room outage and identifies all affected courses.

        Args:
            unavailable_room_id: ID of the room taken out of service (e.g. 'R101').
            current_schedule: Active schedule records.

        Returns:
            Dictionary with affected courses list, room metadata, and disruption metrics.
        """
        room_meta = self.rooms.get(unavailable_room_id, {})
        affected_courses = [
            item for item in current_schedule
            if item["room_id"] == unavailable_room_id
        ]

        return {
            "unavailable_room_id": unavailable_room_id,
            "room_name": room_meta.get("name", unavailable_room_id),
            "building_id": room_meta.get("building_id", ""),
            "affected_count": len(affected_courses),
            "affected_courses": affected_courses
        }

    def recommend_alternative_rooms(
        self,
        course_id: str,
        slot_id: str,
        current_schedule: List[Dict[str, Any]],
        campus_graph: Optional[nx.Graph] = None
    ) -> List[Dict[str, Any]]:
        """
        Recommends unoccupied, compatible alternative rooms for an affected course.

        Evaluation Criteria:
        1. Availability: Room is NOT occupied in slot_id by another course.
        2. Capacity: Room capacity >= course enrolled students.
        3. Equipment: Room is_lab satisfies course requires_lab.
        4. Proximity: Walking distance from the original building (if campus_graph provided).
        5. Seating Fit: Minimizes wasted seats.

        Args:
            course_id: Course needing relocation.
            slot_id: Time slot of the class.
            current_schedule: Active schedule to check occupied rooms.
            campus_graph: Optional campus graph to measure walking distance between buildings.

        Returns:
            List of ranked alternative room dictionaries.
        """
        course = self.courses.get(course_id)
        if not course:
            return []

        # Find rooms occupied in this slot (excluding this course itself)
        occupied_rooms = {
            item["room_id"] for item in current_schedule
            if item["slot_id"] == slot_id and item["course_id"] != course_id
        }

        # Find original building if known
        original_building = None
        for item in current_schedule:
            if item["course_id"] == course_id:
                original_building = item["building_id"]
                break

        candidates = []
        for r_id, room in self.rooms.items():
            if r_id in occupied_rooms:
                continue
            if room["capacity"] < course["enrolled_students"]:
                continue
            if course["requires_lab"] and not room["is_lab"]:
                continue

            # Calculate walking distance between buildings if graph is provided
            distance_m = 0.0
            if campus_graph and original_building and original_building in campus_graph:
                cand_b = room["building_id"]
                if cand_b in campus_graph:
                    try:
                        distance_m = round(
                            nx.shortest_path_length(campus_graph, original_building, cand_b, weight="weight"), 1
                        )
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        distance_m = 999.0

            wasted_seats = room["capacity"] - course["enrolled_students"]
            utilization = round((course["enrolled_students"] / room["capacity"]) * 100.0, 1)

            candidates.append({
                "room_id": r_id,
                "room_name": room["name"],
                "building_id": room["building_id"],
                "capacity": room["capacity"],
                "is_lab": room["is_lab"],
                "enrolled": course["enrolled_students"],
                "wasted_seats": wasted_seats,
                "utilization_pct": utilization,
                "walk_distance_from_orig_m": distance_m
            })

        # Rank candidates: prioritize closest distance, then lowest seat wastage
        candidates.sort(key=lambda x: (x["walk_distance_from_orig_m"], x["wasted_seats"]))
        return candidates

    def repair_timetable_minimal_change(
        self,
        unavailable_room_id: str,
        current_schedule: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Implements a Minimal Perturbation Problem (MPP) solver using OR-Tools CP-SAT.
        
        When a disruption occurs, rather than recalculating the entire timetable
        from scratch (which disturbs all professors and students), this solver
        forbids the unavailable room and maximizes the number of courses that
        keep their EXACT original room and time slot assignment.

        Args:
            unavailable_room_id: Room out of service.
            current_schedule: Existing schedule records to preserve.

        Returns:
            Dictionary with repaired schedule, stability metrics, and change details.
        """
        model = cp_model.CpModel()
        start_time = time.time()

        # Build set of original assignments: (course_id, room_id, slot_id)
        original_assignments = {
            (item["course_id"], item["room_id"], item["slot_id"])
            for item in current_schedule
        }

        x_vars = {}
        for c_id, course in self.courses.items():
            for r_id, room in self.rooms.items():
                if r_id == unavailable_room_id:
                    continue  # Forbid unavailable room
                if room["capacity"] < course["enrolled_students"]:
                    continue
                if course["requires_lab"] and not room["is_lab"]:
                    continue

                for s_id in self.time_slots.keys():
                    var_name = f"X_{c_id}_{r_id}_{s_id}"
                    x_vars[(c_id, r_id, s_id)] = model.NewBoolVar(var_name)

        # Hard Constraint 1: Exactly one assignment per course
        for c_id in self.courses.keys():
            valid_assignments = [
                x_vars[(c_id, r_id, s_id)]
                for r_id in self.rooms.keys()
                for s_id in self.time_slots.keys()
                if (c_id, r_id, s_id) in x_vars
            ]
            if not valid_assignments:
                return {
                    "status": "INFEASIBLE",
                    "error": f"Course '{self.courses[c_id]['name']}' cannot be placed without room {unavailable_room_id}.",
                    "repaired_schedule": [],
                    "repaired_schedule_df": pd.DataFrame()
                }
            model.AddExactlyOne(valid_assignments)

        # Hard Constraint 2: Room conflict-free
        for r_id in self.rooms.keys():
            if r_id == unavailable_room_id:
                continue
            for s_id in self.time_slots.keys():
                courses_in_room = [
                    x_vars[(c_id, r_id, s_id)]
                    for c_id in self.courses.keys()
                    if (c_id, r_id, s_id) in x_vars
                ]
                if courses_in_room:
                    model.AddAtMostOne(courses_in_room)

        # Hard Constraint 3: Teacher conflict-free
        for i_id in self.instructors.keys():
            inst_courses = [c_id for c_id, c in self.courses.items() if c["instructor_id"] == i_id]
            for s_id in self.time_slots.keys():
                teacher_assignments = [
                    x_vars[(c_id, r_id, s_id)]
                    for c_id in inst_courses
                    for r_id in self.rooms.keys()
                    if (c_id, r_id, s_id) in x_vars
                ]
                if teacher_assignments:
                    model.AddAtMostOne(teacher_assignments)

        # -------------------------------------------------------------
        # MINIMAL PERTURBATION OBJECTIVE
        # -------------------------------------------------------------
        # Reward keeping previous assignment with heavy weight (1000)
        # Penalize wasted seats with small weight (1)
        objective_terms = []
        for (c_id, r_id, s_id), var in x_vars.items():
            if (c_id, r_id, s_id) in original_assignments:
                # Strong incentive to maintain original placement
                objective_terms.append(var * 1000)
            else:
                waste = self.rooms[r_id]["capacity"] - self.courses[c_id]["enrolled_students"]
                objective_terms.append(var * (-waste))

        model.Maximize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        status_code = solver.Solve(model)
        elapsed_time = round(time.time() - start_time, 4)

        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE"
        }
        status_str = status_map.get(status_code, "INFEASIBLE")

        if status_str not in ("OPTIMAL", "FEASIBLE"):
            return {
                "status": status_str,
                "solve_time_sec": elapsed_time,
                "error": "No alternative timetable could satisfy constraints without room " + unavailable_room_id,
                "repaired_schedule": [],
                "repaired_schedule_df": pd.DataFrame()
            }

        repaired_schedule = []
        changed_assignments = []
        unchanged_count = 0

        # Build original course lookup: course_id -> (room_id, room_name, slot_id)
        orig_map = {
            item["course_id"]: item for item in current_schedule
        }

        for (c_id, r_id, s_id), var in x_vars.items():
            if solver.BooleanValue(var):
                c_data = self.courses[c_id]
                r_data = self.rooms[r_id]
                s_data = self.time_slots[s_id]
                i_data = self.instructors[c_data["instructor_id"]]

                cap = r_data["capacity"]
                enrolled = c_data["enrolled_students"]
                utilization = round((enrolled / cap) * 100.0, 1)

                is_changed = False
                prev_record = orig_map.get(c_id)
                if prev_record:
                    if prev_record["room_id"] != r_id or prev_record["slot_id"] != s_id:
                        is_changed = True
                        changed_assignments.append({
                            "course_id": c_id,
                            "course_name": c_data["name"],
                            "instructor": i_data["name"],
                            "old_room": prev_record["room_name"],
                            "new_room": r_data["name"],
                            "old_time": prev_record["time"],
                            "new_time": f"{s_data['start_time']} - {s_data['end_time']}",
                            "day": s_data["day"]
                        })
                    else:
                        unchanged_count += 1

                repaired_schedule.append({
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
                    "is_lab": r_data["is_lab"],
                    "is_relocated": is_changed
                })

        day_order = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5}
        repaired_schedule.sort(key=lambda item: (day_order.get(item["day"], 9), item["period"], item["room_name"]))

        repaired_df = pd.DataFrame(repaired_schedule)
        stability_pct = round((unchanged_count / len(repaired_schedule)) * 100.0, 1) if repaired_schedule else 0.0

        return {
            "status": status_str,
            "solve_time_sec": elapsed_time,
            "total_courses": len(repaired_schedule),
            "unchanged_courses_count": unchanged_count,
            "changed_courses_count": len(changed_assignments),
            "schedule_stability_pct": stability_pct,
            "changed_assignments": changed_assignments,
            "repaired_schedule": repaired_schedule,
            "repaired_schedule_df": repaired_df
        }

"""
Module: resource_manager.py
Purpose: Evaluates campus room allocation efficiency, space utilization, and resource bottlenecks.

Discrete Mathematics Relevance:
-------------------------------
1. Bipartite Matching & Resource Allocation:
   - A schedule represents a matching in a bipartite graph G = (C, R x S, E_match)
     where courses C are mapped to room-time resources (R x S).
2. Space Utilization Ratio:
   - Defined for each allocation (c, r) as:
     Utilization(c, r) = (Enrolled(c) / Capacity(r)) * 100%
   - Bounds: 0% < Utilization <= 100% (since Capacity >= Enrolled is strictly maintained).
3. Efficiency Classification:
   - "Under-utilized": Utilization < 50% (potential energy and heating/cooling waste).
   - "Optimal": 50% <= Utilization <= 90% (comfortable and space-efficient).
   - "Near Capacity": Utilization > 90% (tight seating, peak load).
"""

from typing import List, Dict, Any
import pandas as pd


class CampusResourceManager:
    """
    Computes space utilization statistics, idle room rates, and resource recommendations.
    """

    def __init__(self, schedule_records: List[Dict[str, Any]], all_rooms: Dict[str, Dict[str, Any]]):
        """
        Initializes the resource manager with an existing schedule and room registry.

        Args:
            schedule_records: List of dictionaries from the timetable solver.
            all_rooms: Dictionary of all campus rooms and their capacities.
        """
        self.schedule_records = schedule_records
        self.all_rooms = all_rooms

    def compute_overall_metrics(self) -> Dict[str, Any]:
        """
        Computes aggregate campus resource statistics.

        Returns:
            Dictionary containing overall utilization, total allocated seats,
            enrolled students, and efficiency categorizations.
        """
        if not self.schedule_records:
            return {
                "overall_utilization_pct": 0.0,
                "total_enrolled": 0,
                "total_allocated_capacity": 0,
                "total_wasted_seats": 0,
                "allocated_rooms_count": 0,
                "under_utilized_count": 0,
                "optimal_count": 0,
                "near_capacity_count": 0
            }

        total_enrolled = sum(r["enrolled"] for r in self.schedule_records)
        total_capacity = sum(r["capacity"] for r in self.schedule_records)
        wasted_seats = total_capacity - total_enrolled
        overall_utilization = round((total_enrolled / total_capacity) * 100.0, 1)

        under_utilized = 0
        optimal = 0
        near_capacity = 0

        for r in self.schedule_records:
            util = r["utilization_pct"]
            if util < 50.0:
                under_utilized += 1
            elif util <= 90.0:
                optimal += 1
            else:
                near_capacity += 1

        unique_rooms_used = len(set(r["room_id"] for r in self.schedule_records))

        return {
            "overall_utilization_pct": overall_utilization,
            "total_enrolled": total_enrolled,
            "total_allocated_capacity": total_capacity,
            "total_wasted_seats": wasted_seats,
            "allocated_rooms_count": unique_rooms_used,
            "total_campus_rooms": len(self.all_rooms),
            "under_utilized_count": under_utilized,
            "optimal_count": optimal,
            "near_capacity_count": near_capacity
        }

    def get_room_utilization_summary(self) -> pd.DataFrame:
        """
        Generates a DataFrame summarizing utilization metrics per scheduled class.

        Returns:
            pd.DataFrame with Course, Room, Enrolled, Capacity, Utilization %, Status.
        """
        rows = []
        for r in self.schedule_records:
            util = r["utilization_pct"]
            if util < 50.0:
                status = "Under-utilized (<50%)"
            elif util <= 90.0:
                status = "Optimal (50-90%)"
            else:
                status = "Near Capacity (>90%)"

            rows.append({
                "Course": r["course_name"],
                "Room": r["room_name"],
                "Type": "Lab" if r.get("is_lab") else "Lecture Hall",
                "Enrolled": r["enrolled"],
                "Capacity": r["capacity"],
                "Utilization %": util,
                "Wasted Seats": r["wasted_seats"],
                "Status": status
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values(by="Utilization %", ascending=False)
        return df

    def get_idle_rooms_analysis(self) -> Dict[str, Any]:
        """
        Identifies rooms that are never utilized in the current schedule.

        Returns:
            Dictionary with count and list of unassigned rooms.
        """
        used_room_ids = {r["room_id"] for r in self.schedule_records}
        idle_rooms = [
            room for rid, room in self.all_rooms.items()
            if rid not in used_room_ids
        ]

        return {
            "idle_rooms_count": len(idle_rooms),
            "idle_rooms": idle_rooms
        }

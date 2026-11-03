"""
Scheduling module for Graph-Based Smart Campus Optimization System.
Provides constraint-based classroom timetabling using Google OR-Tools CP-SAT.
"""

from .timetable_solver import CampusTimetableSolver

__all__ = ["CampusTimetableSolver"]


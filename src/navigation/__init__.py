"""
Navigation module for Graph-Based Smart Campus Optimization System.
Provides graph creation, Dijkstra's algorithm, and A* heuristic pathfinding.
"""

from .graph_builder import CampusGraph
from .pathfinder import CampusPathfinder

__all__ = ["CampusGraph", "CampusPathfinder"]


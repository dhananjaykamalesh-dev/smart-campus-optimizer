"""
Unit Tests for Phase 1: Campus Navigation Module
Tests Graph Construction, Dijkstra's Algorithm, A* Algorithm, and Accessibility Filters.
"""

import os
import pytest
from src.navigation.graph_builder import CampusGraph
from src.navigation.pathfinder import CampusPathfinder


# Resolve paths to sample CSV data relative to this test file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDINGS_CSV = os.path.join(BASE_DIR, "data", "buildings.csv")
PATHS_CSV = os.path.join(BASE_DIR, "data", "paths.csv")


@pytest.fixture
def campus_graph_instance():
    """Fixture providing an initialized CampusGraph instance."""
    return CampusGraph(buildings_file=BUILDINGS_CSV, paths_file=PATHS_CSV)


def test_graph_loading(campus_graph_instance):
    """
    Validates that:
    1. All 10 buildings from CSV are loaded as graph vertices.
    2. Node attributes (x, y, name, category) are properly attached.
    3. Edges contain positive distances and accessibility flags.
    """
    g = campus_graph_instance.graph
    assert len(g.nodes) == 10, f"Expected 10 buildings, got {len(g.nodes)}"
    assert len(g.edges) >= 15, f"Expected at least 15 pathways, got {len(g.edges)}"

    # Check node attributes for B1 (Main Gate)
    assert "B1" in g
    assert g.nodes["B1"]["name"] == "Main Gate"
    assert g.nodes["B1"]["x"] == 50.0
    assert g.nodes["B1"]["y"] == 50.0

    # Check edge attributes between B1 and B2
    edge_data = g.get_edge_data("B1", "B2")
    assert edge_data is not None
    assert edge_data["weight"] == 120.0
    assert edge_data["is_accessible"] is True


def test_dijkstra_shortest_path(campus_graph_instance):
    """
    Tests Dijkstra's algorithm from B1 (Main Gate) to B5 (CS Lab Complex).
    Expected path: B1 -> B2 -> B3 -> B5 (120 + 130 + 150 = 400m).
    """
    pathfinder = CampusPathfinder(campus_graph_instance.graph)
    result = pathfinder.find_shortest_path_dijkstra("B1", "B5")

    assert result["path"] == ["B1", "B2", "B3", "B5"]
    assert result["total_distance"] == 400.0
    assert result["walking_time_min"] > 0
    assert result["nodes_explored"] >= 4


def test_astar_admissibility_and_optimality(campus_graph_instance):
    """
    Discrete Mathematics Core Test:
    Verifies that A* produces the EXACT same optimal path distance as Dijkstra
    because Euclidean heuristic h(u, v) <= d(u, v) is admissible.
    """
    pathfinder = CampusPathfinder(campus_graph_instance.graph)

    # Test multiple source-target pairs across campus
    test_pairs = [("B1", "B5"), ("B1", "B10"), ("B2", "B9"), ("B7", "B8")]

    for start, goal in test_pairs:
        dijkstra_res = pathfinder.find_shortest_path_dijkstra(start, goal)
        astar_res = pathfinder.find_shortest_path_astar(start, goal)

        assert dijkstra_res["total_distance"] == astar_res["total_distance"], (
            f"A* distance ({astar_res['total_distance']}) must match "
            f"Dijkstra distance ({dijkstra_res['total_distance']}) for {start} -> {goal}"
        )


def test_same_start_and_goal(campus_graph_instance):
    """Verifies that selecting the same building as start and goal yields 0 distance."""
    pathfinder = CampusPathfinder(campus_graph_instance.graph)
    res = pathfinder.find_shortest_path_dijkstra("B3", "B3")

    assert res["path"] == ["B3"]
    assert res["total_distance"] == 0.0
    assert res["walking_time_min"] == 0.0


def test_accessible_subgraph_rerouting(campus_graph_instance):
    """
    Tests wheelchair/ramp accessibility constraint:
    Edge B3 -> B6 is a flight of stairs (is_accessible = False).
    In standard graph, direct path B3 -> B6 is 160m.
    In accessible subgraph, pathfinder must route around the stairs:
    e.g., via B3 -> B5 -> B9 -> B6 or B3 -> B2 -> B1 -> B7 -> B6.
    """
    full_pathfinder = CampusPathfinder(campus_graph_instance.graph)
    accessible_graph = campus_graph_instance.get_accessible_subgraph()
    accessible_pathfinder = CampusPathfinder(accessible_graph)

    standard_res = full_pathfinder.find_shortest_path_dijkstra("B3", "B6")
    accessible_res = accessible_pathfinder.find_shortest_path_dijkstra("B3", "B6")

    # Standard path can use the stairs directly
    assert standard_res["path"] == ["B3", "B6"]
    assert standard_res["total_distance"] == 160.0

    # Accessible route must NOT use the stairs
    assert "B3" in accessible_res["path"]
    assert "B6" in accessible_res["path"]
    assert accessible_res["path"] != ["B3", "B6"], "Accessible path cannot traverse inaccessible stairs edge"
    assert accessible_res["total_distance"] > 160.0


def test_invalid_node_raises_error(campus_graph_instance):
    """Verifies that querying nonexistent building IDs raises a clean ValueError."""
    pathfinder = CampusPathfinder(campus_graph_instance.graph)
    with pytest.raises(ValueError):
        pathfinder.find_shortest_path_dijkstra("INVALID_NODE", "B1")


"""
Module: graph_builder.py
Purpose: Loads campus spatial data from CSV files and constructs an undirected,
         weighted graph representation using NetworkX.

Discrete Mathematics Concept:
    A graph G is defined as an ordered pair G = (V, E), where:
    - V is a set of Vertices (campus buildings/landmarks).
    - E is a set of Edges (pathways/walkways connecting buildings).
    - Each edge e = (u, v) has an associated weight w(e) representing physical walking distance.
"""

import os
import csv
from typing import Dict, Any, List, Optional, Tuple, Set
import networkx as nx


class CampusGraph:
    """
    Manages campus graph construction, node lookups, and edge filtering.
    
    Attributes:
        buildings_file (str): Path to the CSV containing building/node information.
        paths_file (str): Path to the CSV containing pathway/edge information.
        graph (nx.Graph): The full NetworkX undirected weighted graph.
    """

    def __init__(self, buildings_file: str, paths_file: str):
        """
        Initializes the CampusGraph loader with file paths.

        Args:
            buildings_file: File path to buildings.csv
            paths_file: File path to paths.csv
        """
        self.buildings_file = buildings_file
        self.paths_file = paths_file
        self.graph = nx.Graph()
        self.buildings_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Automatically load and construct the graph upon instantiation
        self.load_and_build()

    def load_and_build(self) -> nx.Graph:
        """
        Reads CSV files and populates the NetworkX graph with vertices and weighted edges.

        Returns:
            nx.Graph: The fully constructed campus graph.
            
        Raises:
            FileNotFoundError: If either buildings.csv or paths.csv does not exist.
        """
        if not os.path.exists(self.buildings_file):
            raise FileNotFoundError(f"Buildings data file not found at: {self.buildings_file}")
        if not os.path.exists(self.paths_file):
            raise FileNotFoundError(f"Paths data file not found at: {self.paths_file}")

        # Clear any existing graph elements
        self.graph.clear()
        self.buildings_metadata.clear()

        # Step 1: Load Vertices (Buildings)
        with open(self.buildings_file, mode="r", encoding="utf-8") as bf:
            reader = csv.DictReader(bf)
            for row in reader:
                node_id = row["building_id"].strip()
                name = row["name"].strip()
                x_coord = float(row["x"])
                y_coord = float(row["y"])
                category = row["category"].strip()

                node_attributes = {
                    "name": name,
                    "x": x_coord,
                    "y": y_coord,
                    "pos": (x_coord, y_coord),
                    "category": category
                }

                self.graph.add_node(node_id, **node_attributes)
                self.buildings_metadata[node_id] = node_attributes

        # Step 2: Load Edges (Walkways/Paths)
        with open(self.paths_file, mode="r", encoding="utf-8") as pf:
            reader = csv.DictReader(pf)
            for row in reader:
                source = row["source"].strip()
                target = row["target"].strip()
                distance = float(row["distance_m"])
                is_accessible = row["is_accessible"].strip().lower() in ("true", "1", "yes")
                is_covered = row["is_covered"].strip().lower() in ("true", "1", "yes")

                if source in self.graph and target in self.graph:
                    self.graph.add_edge(
                        source,
                        target,
                        weight=distance,
                        distance_m=distance,
                        is_accessible=is_accessible,
                        is_covered=is_covered
                    )

        return self.graph

    def get_accessible_subgraph(self) -> nx.Graph:
        """
        Creates an induced edge subgraph containing only wheelchair/ramp accessible pathways.
        
        Discrete Math Concept:
            A subgraph G' = (V, E') is formed by selecting a subset of edges E' ⊆ E
            that satisfy a specific predicate (in this case: is_accessible == True).

        Returns:
            nx.Graph: A new graph with only accessible edges.
        """
        accessible_graph = nx.Graph()

        for node, data in self.graph.nodes(data=True):
            accessible_graph.add_node(node, **data)

        for u, v, data in self.graph.edges(data=True):
            if data.get("is_accessible", False):
                accessible_graph.add_edge(u, v, **data)

        return accessible_graph

    def get_blocked_subgraph(
        self,
        blocked_edges: List[Tuple[str, str]],
        accessible_only: bool = False
    ) -> nx.Graph:
        r"""
        Generates a dynamic subgraph representing campus walkways during temporary closures.

        Discrete Math Concept:
            Edge Deletion Subgraph: G_detour = (V, E \ E_blocked)
            Removing a set of edges temporarily simulates construction, weather, or congestion.

        Args:
            blocked_edges: List of edge tuples (u, v) that are temporarily impassable.
            accessible_only: If True, also filters out non-accessible edges.

        Returns:
            nx.Graph: Dynamic subgraph with blocked edges removed.
        """
        base_graph = self.get_accessible_subgraph() if accessible_only else self.graph
        detour_graph = nx.Graph()

        # Preserve all vertices
        for node, data in base_graph.nodes(data=True):
            detour_graph.add_node(node, **data)

        # Normalize blocked edges for undirected matching: (u, v) and (v, u)
        blocked_set: Set[Tuple[str, str]] = set()
        for u, v in blocked_edges:
            blocked_set.add((u, v))
            blocked_set.add((v, u))

        # Copy over only unblocked edges
        for u, v, data in base_graph.edges(data=True):
            if (u, v) not in blocked_set:
                detour_graph.add_edge(u, v, **data)

        return detour_graph

    def get_building_info(self, building_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns metadata for a specific building node.

        Args:
            building_id: Unique identifier (e.g., 'B1')

        Returns:
            Dictionary with name, coordinates, category, or None if not found.
        """
        return self.buildings_metadata.get(building_id)

    def get_all_buildings(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all buildings with their IDs and readable names.

        Returns:
            List of dictionaries containing 'id' and 'name'.
        """
        return [
            {"id": bid, "name": meta["name"], "category": meta["category"]}
            for bid, meta in self.buildings_metadata.items()
        ]

    def get_graph_summary(self) -> Dict[str, Any]:
        """
        Computes key structural metrics of the campus graph.

        Returns:
            Dictionary with vertices count, edges count, accessible edges count,
            covered walkways count, and connected components.
        """
        accessible_edges = sum(
            1 for _, _, d in self.graph.edges(data=True) if d.get("is_accessible", False)
        )
        covered_edges = sum(
            1 for _, _, d in self.graph.edges(data=True) if d.get("is_covered", False)
        )
        is_connected = nx.is_connected(self.graph) if len(self.graph) > 0 else False

        return {
            "num_buildings": self.graph.number_of_nodes(),
            "num_paths": self.graph.number_of_edges(),
            "num_accessible_paths": accessible_edges,
            "num_covered_paths": covered_edges,
            "is_connected": is_connected
        }

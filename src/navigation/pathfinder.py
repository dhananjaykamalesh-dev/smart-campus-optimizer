"""
Module: pathfinder.py
Purpose: Provides pathfinding algorithms (Dijkstra and A*) on the campus graph.

Discrete Mathematics Relevance:
-------------------------------
1. Dijkstra's Algorithm (Uniform-Cost Shortest Path):
   - Computes the shortest path from a start vertex to a destination vertex in a
     weighted graph with non-negative edge weights.
   - Operates greedily by expanding the vertex with the lowest tentative distance:
     g(v) = min(g(u) + w(u, v)).
   - Time Complexity: O((V + E) * log(V)) using a min-priority queue (min-heap).

2. A* (A-Star) Algorithm (Heuristic Search):
   - Evaluates nodes using the evaluation function:
     f(n) = g(n) + h(n)
     where:
       g(n) = exact cost from start node to node n.
       h(n) = estimated heuristic cost from node n to the goal.
   - Heuristic used here: Euclidean Distance on a 2D plane:
     h(u, v) = sqrt((x_u - x_v)^2 + (y_u - y_v)^2)
   - Admissibility: The straight-line Euclidean distance is always <= actual walking
     path distance. Because h(n) never overestimates the true cost, A* is GUARANTEED
     to return an optimal shortest path, just like Dijkstra, but typically explores
     fewer nodes!
"""

import math
import heapq
from typing import List, Dict, Tuple, Optional, Any
import networkx as nx


class CampusPathfinder:
    """
    Computes optimal paths on a campus graph using Dijkstra and A* algorithms.
    """

    def __init__(self, graph: nx.Graph):
        """
        Initializes the pathfinder with a NetworkX campus graph.

        Args:
            graph: A NetworkX Graph containing node coordinates ('x', 'y')
                   and edge weights ('weight').
        """
        self.graph = graph

    def euclidean_heuristic(self, node_a: str, node_b: str) -> float:
        """
        Calculates the straight-line Euclidean distance between two nodes.
        
        Formula:
            h(u, v) = sqrt( (x_u - x_v)^2 + (y_u - y_v)^2 )

        Discrete Math Note:
            This is an *admissible heuristic* because a straight line is the shortest
            possible distance in a 2D Euclidean space. It never overestimates.

        Args:
            node_a: First building ID.
            node_b: Second building ID.

        Returns:
            float: Euclidean distance in meters.
        """
        data_a = self.graph.nodes[node_a]
        data_b = self.graph.nodes[node_b]

        dx = data_a["x"] - data_b["x"]
        dy = data_a["y"] - data_b["y"]
        return math.sqrt(dx * dx + dy * dy)

    def find_shortest_path_dijkstra(
        self, start_node: str, goal_node: str
    ) -> Dict[str, Any]:
        """
        Computes the shortest path using Dijkstra's Algorithm.

        Algorithm Walkthrough:
        1. Initialize distances to all nodes as infinity, except start_node = 0.
        2. Push (0, start_node) to a min-priority queue (heap).
        3. Pop the node with the smallest distance.
        4. If it's the goal, reconstruct the path and return.
        5. Otherwise, relax all neighbor edges: if new_distance < current_distance,
           update distance and push to heap.

        Args:
            start_node: Origin building ID.
            goal_node: Target building ID.

        Returns:
            Dictionary with:
            - 'path': List of node IDs in traversal order.
            - 'path_names': List of human-readable building names.
            - 'total_distance': Total walking distance in meters.
            - 'walking_time_min': Estimated walking time in minutes.
            - 'nodes_explored': Total number of nodes expanded (visited).
            - 'algorithm': 'Dijkstra'
        """
        if start_node not in self.graph:
            raise ValueError(f"Start building '{start_node}' does not exist in graph.")
        if goal_node not in self.graph:
            raise ValueError(f"Goal building '{goal_node}' does not exist in graph.")

        # Special case: start is already goal
        if start_node == goal_node:
            name = self.graph.nodes[start_node].get("name", start_node)
            return {
                "path": [start_node],
                "path_names": [name],
                "total_distance": 0.0,
                "walking_time_min": 0.0,
                "nodes_explored": 1,
                "algorithm": "Dijkstra"
            }

        # Priority queue stores tuples of: (cumulative_distance, current_node)
        priority_queue: List[Tuple[float, str]] = []
        heapq.heappush(priority_queue, (0.0, start_node))

        # Track the shortest discovered distance to each node: g(n)
        distances: Dict[str, float] = {start_node: 0.0}

        # Track previous node to reconstruct the final path: predecessor mapping
        predecessors: Dict[str, Optional[str]] = {start_node: None}

        # Track set of visited/expanded nodes to measure search efficiency
        visited_nodes = set()

        while priority_queue:
            current_dist, current_node = heapq.heappop(priority_queue)

            # If node already settled with a smaller distance, skip it
            if current_node in visited_nodes:
                continue

            visited_nodes.add(current_node)

            # Goal reached! Early exit optimization
            if current_node == goal_node:
                break

            # Explore neighbors
            for neighbor in self.graph.neighbors(current_node):
                if neighbor in visited_nodes:
                    continue

                edge_data = self.graph.get_edge_data(current_node, neighbor)
                edge_weight = edge_data.get("weight", 1.0)
                tentative_dist = current_dist + edge_weight

                # Relaxation step: found a shorter path to neighbor?
                if tentative_dist < distances.get(neighbor, float("inf")):
                    distances[neighbor] = tentative_dist
                    predecessors[neighbor] = current_node
                    heapq.heappush(priority_queue, (tentative_dist, neighbor))

        # Check if goal was reachable
        if goal_node not in distances:
            return {
                "path": [],
                "path_names": [],
                "total_distance": float("inf"),
                "walking_time_min": 0.0,
                "nodes_explored": len(visited_nodes),
                "algorithm": "Dijkstra",
                "error": "No connected path exists between the selected buildings."
            }

        # Reconstruct path by backtracking from goal to start
        path = []
        curr: Optional[str] = goal_node
        while curr is not None:
            path.append(curr)
            curr = predecessors[curr]
        path.reverse()

        path_names = [self.graph.nodes[n].get("name", n) for n in path]
        total_dist = round(distances[goal_node], 2)
        # Average pedestrian walking speed is approximately 1.4 meters/second (~84 m/min)
        walking_time = round(total_dist / 84.0, 1)

        return {
            "path": path,
            "path_names": path_names,
            "total_distance": total_dist,
            "walking_time_min": walking_time,
            "nodes_explored": len(visited_nodes),
            "algorithm": "Dijkstra"
        }

    def find_shortest_path_astar(
        self, start_node: str, goal_node: str
    ) -> Dict[str, Any]:
        """
        Computes the shortest path using the A* (A-Star) Algorithm.

        Algorithm Walkthrough:
        1. Uses priority queue with priority key: f(n) = g(n) + h(n).
        2. g(n) is the exact cost from start to node n.
        3. h(n) is the Euclidean distance from node n to goal.
        4. Nodes closer to the goal direction are prioritized first.

        Args:
            start_node: Origin building ID.
            goal_node: Target building ID.

        Returns:
            Dictionary with path results and search metrics.
        """
        if start_node not in self.graph:
            raise ValueError(f"Start building '{start_node}' does not exist in graph.")
        if goal_node not in self.graph:
            raise ValueError(f"Goal building '{goal_node}' does not exist in graph.")

        if start_node == goal_node:
            name = self.graph.nodes[start_node].get("name", start_node)
            return {
                "path": [start_node],
                "path_names": [name],
                "total_distance": 0.0,
                "walking_time_min": 0.0,
                "nodes_explored": 1,
                "algorithm": "A*"
            }

        # Priority queue stores tuples of: (f_score, current_node)
        priority_queue: List[Tuple[float, str]] = []
        
        initial_h = self.euclidean_heuristic(start_node, goal_node)
        heapq.heappush(priority_queue, (initial_h, start_node))

        # g_score[node]: exact cost from start to node
        g_score: Dict[str, float] = {start_node: 0.0}

        # Predecessor mapping to reconstruct optimal path
        predecessors: Dict[str, Optional[str]] = {start_node: None}

        visited_nodes = set()

        while priority_queue:
            current_f, current_node = heapq.heappop(priority_queue)

            if current_node in visited_nodes:
                continue

            visited_nodes.add(current_node)

            # Reached destination
            if current_node == goal_node:
                break

            current_g = g_score[current_node]

            for neighbor in self.graph.neighbors(current_node):
                if neighbor in visited_nodes:
                    continue

                edge_data = self.graph.get_edge_data(current_node, neighbor)
                edge_weight = edge_data.get("weight", 1.0)
                tentative_g = current_g + edge_weight

                if tentative_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = tentative_g
                    predecessors[neighbor] = current_node
                    
                    # f(n) = g(n) + h(n)
                    h_val = self.euclidean_heuristic(neighbor, goal_node)
                    f_val = tentative_g + h_val
                    heapq.heappush(priority_queue, (f_val, neighbor))

        if goal_node not in g_score:
            return {
                "path": [],
                "path_names": [],
                "total_distance": float("inf"),
                "walking_time_min": 0.0,
                "nodes_explored": len(visited_nodes),
                "algorithm": "A*",
                "error": "No connected path exists between the selected buildings."
            }

        # Reconstruct path
        path = []
        curr: Optional[str] = goal_node
        while curr is not None:
            path.append(curr)
            curr = predecessors[curr]
        path.reverse()

        path_names = [self.graph.nodes[n].get("name", n) for n in path]
        total_dist = round(g_score[goal_node], 2)
        walking_time = round(total_dist / 84.0, 1)

        return {
            "path": path,
            "path_names": path_names,
            "total_distance": total_dist,
            "walking_time_min": walking_time,
            "nodes_explored": len(visited_nodes),
            "algorithm": "A*"
        }


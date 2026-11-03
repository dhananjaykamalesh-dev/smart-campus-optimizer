"""
Module: visualizer.py
Purpose: Renders interactive campus maps and analytics charts using Plotly.

Discrete Mathematics Relevance:
    Provides visual representations of:
    1. 2D geometric embedding of Campus Graph G = (V, E)
    2. Shortest paths computed by Dijkstra and A*
    3. Blocked edges E_blocked and detour paths G \ E_blocked
    4. Resource allocation utilization and capacity distribution
"""

from typing import List, Optional, Dict, Any, Tuple
import plotly.graph_objects as go
import pandas as pd
import networkx as nx


def create_campus_map_figure(
    graph: nx.Graph,
    highlight_path: Optional[List[str]] = None,
    accessible_only: bool = False,
    blocked_edges: Optional[List[Tuple[str, str]]] = None,
    original_path: Optional[List[str]] = None
) -> go.Figure:
    """
    Constructs an interactive Plotly Figure representing the campus graph,
    supporting accessibility indicators, blocked pathways, and detour route overlays.

    Args:
        graph: NetworkX campus graph with coordinates and attributes.
        highlight_path: Path node IDs to highlight (active route or detour).
        accessible_only: Flag indicating if wheelchair ramp mode is active.
        blocked_edges: List of (u, v) tuples representing closed walkways.
        original_path: Optional original route prior to obstruction for comparison.

    Returns:
        go.Figure: Interactive 2D campus map.
    """
    fig = go.Figure()

    category_colors = {
        "Entrance": "#E63946",       # Red
        "Administration": "#457B9D", # Steel Blue
        "Library": "#1D3557",        # Navy Blue
        "Academic": "#2A9D8F",       # Teal
        "Amenities": "#F4A261",      # Amber
        "Sports": "#E76F51",         # Coral
        "Auditorium": "#9B5DE5",     # Purple
        "Medical": "#00BBF9"         # Sky Blue
    }

    # Normalize blocked edges set
    blocked_set = set()
    if blocked_edges:
        for u, v in blocked_edges:
            blocked_set.add((u, v))
            blocked_set.add((v, u))

    # Fast lookup for active path edges
    path_edges_set = set()
    if highlight_path and len(highlight_path) > 1:
        for i in range(len(highlight_path) - 1):
            u, v = highlight_path[i], highlight_path[i + 1]
            path_edges_set.add((u, v))
            path_edges_set.add((v, u))

    # Fast lookup for original path edges
    original_edges_set = set()
    if original_path and len(original_path) > 1:
        for i in range(len(original_path) - 1):
            u, v = original_path[i], original_path[i + 1]
            original_edges_set.add((u, v))
            original_edges_set.add((v, u))

    # 1. Draw Normal Walkways
    normal_edge_x = []
    normal_edge_y = []

    for u, v, data in graph.edges(data=True):
        if (u, v) in blocked_set or (u, v) in path_edges_set or (u, v) in original_edges_set:
            continue
        pos_u = (graph.nodes[u]["x"], graph.nodes[u]["y"])
        pos_v = (graph.nodes[v]["x"], graph.nodes[v]["y"])
        normal_edge_x.extend([pos_u[0], pos_v[0], None])
        normal_edge_y.extend([pos_u[1], pos_v[1], None])

    walkway_label = "Accessible Paths (Ramps)" if accessible_only else "Standard Walkways"
    fig.add_trace(
        go.Scatter(
            x=normal_edge_x,
            y=normal_edge_y,
            mode="lines",
            line=dict(
                color="#0077B6" if accessible_only else "#CFD8DC",
                width=3.0 if accessible_only else 2.5,
                dash="solid"
            ),
            hoverinfo="none",
            name=walkway_label,
            showlegend=True
        )
    )

    # 2. Draw Original Route (if disrupted and rerouted)
    if original_path and len(original_path) > 1 and original_path != highlight_path:
        orig_x = [graph.nodes[n]["x"] for n in original_path]
        orig_y = [graph.nodes[n]["y"] for n in original_path]
        fig.add_trace(
            go.Scatter(
                x=orig_x,
                y=orig_y,
                mode="lines",
                line=dict(color="#78909C", width=3.5, dash="dash"),
                hoverinfo="text",
                text=[f"Original Path: {graph.nodes[n]['name']}" for n in original_path],
                name="Original Route (Disrupted)",
                showlegend=True
            )
        )

    # 3. Draw Blocked Edges
    if blocked_edges:
        blocked_x = []
        blocked_y = []
        for u, v in blocked_edges:
            if u in graph and v in graph:
                pos_u = (graph.nodes[u]["x"], graph.nodes[u]["y"])
                pos_v = (graph.nodes[v]["x"], graph.nodes[v]["y"])
                blocked_x.extend([pos_u[0], pos_v[0], None])
                blocked_y.extend([pos_u[1], pos_v[1], None])

        fig.add_trace(
            go.Scatter(
                x=blocked_x,
                y=blocked_y,
                mode="lines+markers",
                line=dict(color="#D90429", width=5.0, dash="dashdot"),
                marker=dict(size=10, color="#D90429", symbol="x"),
                hoverinfo="text",
                text=["🚫 Blocked Pathway" for _ in blocked_x],
                name="🚫 Closed Walkway",
                showlegend=True
            )
        )

    # 4. Draw Highlighted Active Route / Detour
    if highlight_path and len(highlight_path) > 1:
        path_x = [graph.nodes[n]["x"] for n in highlight_path]
        path_y = [graph.nodes[n]["y"] for n in highlight_path]

        route_label = "Detour Route" if (original_path and original_path != highlight_path) else "Calculated Route"
        fig.add_trace(
            go.Scatter(
                x=path_x,
                y=path_y,
                mode="lines+markers",
                line=dict(color="#FF6B35", width=5.5),
                marker=dict(size=12, color="#FF6B35", symbol="circle"),
                hoverinfo="text",
                text=[f"Step {idx + 1}: {graph.nodes[n]['name']} ({n})" for idx, n in enumerate(highlight_path)],
                name=route_label,
                showlegend=True
            )
        )

    # 5. Draw Nodes (Buildings)
    node_x = []
    node_y = []
    node_labels = []
    node_colors = []
    node_hover = []
    node_sizes = []

    highlight_set = set(highlight_path) if highlight_path else set()

    for node_id, data in graph.nodes(data=True):
        x = data["x"]
        y = data["y"]
        name = data.get("name", node_id)
        cat = data.get("category", "General")
        
        node_x.append(x)
        node_y.append(y)
        node_labels.append(f"<b>{name}</b><br>({node_id})")
        node_colors.append(category_colors.get(cat, "#333333"))
        
        if highlight_path and node_id == highlight_path[0]:
            node_sizes.append(26)
            status = " [START ORIGIN]"
        elif highlight_path and node_id == highlight_path[-1]:
            node_sizes.append(26)
            status = " [DESTINATION]"
        elif node_id in highlight_set:
            node_sizes.append(20)
            status = " [ROUTE WAYPOINT]"
        else:
            node_sizes.append(16)
            status = ""

        hover_info = (
            f"<b>{name}</b> ({node_id}){status}<br>"
            f"Category: {cat}<br>"
            f"Coordinates: ({x}, {y}) meters"
        )
        node_hover.append(hover_info)

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color="#FFFFFF")
            ),
            text=node_labels,
            textposition="top center",
            hoverinfo="text",
            hovertext=node_hover,
            name="Buildings",
            showlegend=False
        )
    )

    mode_title_suffix = " (♿ Wheelchair Mode)" if accessible_only else " (Standard Mode)"
    if blocked_edges:
        mode_title_suffix += " • ⚠️ Pathway Obstructions Active"

    fig.update_layout(
        title=dict(
            text=f"Interactive Campus Graph Navigation Map{mode_title_suffix}",
            x=0.5,
            xanchor="center",
            font=dict(size=17, color="#1D3557")
        ),
        paper_bgcolor="#F8F9FA",
        plot_bgcolor="#FFFFFF",
        hovermode="closest",
        margin=dict(b=30, l=30, r=30, t=55),
        xaxis=dict(
            title="Campus East-West Distance (Meters)",
            showgrid=True,
            gridcolor="#E0E0E0",
            zeroline=False
        ),
        yaxis=dict(
            title="Campus North-South Distance (Meters)",
            showgrid=True,
            gridcolor="#E0E0E0",
            zeroline=False,
            scaleanchor="x",
            scaleratio=1
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=620
    )

    return fig


def create_utilization_bar_chart(summary_df: pd.DataFrame) -> go.Figure:
    """
    Renders a bar chart comparing classroom seat utilization across courses
    with threshold guidelines.
    """
    if summary_df.empty:
        return go.Figure()

    colors = []
    category_labels = []
    for util in summary_df["Utilization %"]:
        if util < 50.0:
            colors.append("#E76F51")  # Coral / Under-utilized
            category_labels.append("Under-utilized (<50%)")
        elif util <= 90.0:
            colors.append("#2A9D8F")  # Teal / Optimal
            category_labels.append("Optimal (50-90%)")
        else:
            colors.append("#E63946")  # Red / Near Peak Capacity
            category_labels.append("Near Capacity (>90%)")

    fig = go.Figure(
        data=[
            go.Bar(
                x=summary_df["Course"],
                y=summary_df["Utilization %"],
                marker=dict(color=colors),
                text=[f"{u}%" for u in summary_df["Utilization %"]],
                textposition="auto",
                customdata=category_labels,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Utilization: %{y}%<br>"
                    "Health: %{customdata}<br>"
                    "<extra></extra>"
                )
            )
        ]
    )

    fig.add_hline(
        y=50,
        line_dash="dot",
        line_color="#E76F51",
        annotation_text="50% Under-utilized Threshold",
        annotation_position="bottom right"
    )
    fig.add_hline(
        y=90,
        line_dash="dot",
        line_color="#2A9D8F",
        annotation_text="90% Peak Capacity Threshold",
        annotation_position="top right"
    )

    fig.update_layout(
        title=dict(text="Classroom Space Utilization by Course (%)", x=0.5),
        yaxis=dict(title="Utilization Rate (%)", range=[0, 110]),
        xaxis=dict(title="Scheduled Courses"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8F9FA",
        height=450,
        margin=dict(l=30, r=30, t=50, b=30)
    )

    return fig


def create_capacity_vs_enrolled_chart(summary_df: pd.DataFrame) -> go.Figure:
    """
    Renders grouped bars showing Enrolled Students vs Room Capacity.
    """
    if summary_df.empty:
        return go.Figure()

    fig = go.Figure(
        data=[
            go.Bar(
                name="Enrolled Students",
                x=summary_df["Course"],
                y=summary_df["Enrolled"],
                marker_color="#1D3557"
            ),
            go.Bar(
                name="Allocated Room Capacity",
                x=summary_df["Course"],
                y=summary_df["Capacity"],
                marker_color="#457B9D"
            )
        ]
    )

    fig.update_layout(
        barmode="group",
        title=dict(text="Student Enrollment vs. Allocated Seating Capacity", x=0.5),
        yaxis=dict(title="Number of Students / Seats"),
        xaxis=dict(title="Course"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8F9FA",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=30, r=30, t=50, b=30)
    )

    return fig

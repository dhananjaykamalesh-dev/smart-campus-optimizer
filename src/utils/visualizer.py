"""
Module: visualizer.py
Purpose: Renders interactive campus maps and analytics charts using Plotly.

Discrete Mathematics Relevance:
    Provides visual representations of:
    1. 2D geometric embedding of Campus Graph G = (V, E)
    2. Shortest paths computed by Dijkstra and A*
    3. Resource allocation utilization and capacity distribution
"""

from typing import List, Optional, Dict, Any
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import networkx as nx


def create_campus_map_figure(
    graph: nx.Graph,
    highlight_path: Optional[List[str]] = None,
    accessible_only: bool = False
) -> go.Figure:
    """
    Constructs an interactive Plotly Figure representing the campus graph.

    Args:
        graph: The NetworkX campus graph with 'x', 'y', 'name', 'category' for nodes,
               and 'weight', 'is_accessible' for edges.
        highlight_path: Optional list of building IDs representing a path to highlight.
        accessible_only: Boolean flag indicating if only accessible edges are shown.

    Returns:
        go.Figure: Interactive 2D campus map with nodes, edges, and path overlays.
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

    # 1. Draw Normal Edges
    normal_edge_x = []
    normal_edge_y = []

    path_edges_set = set()
    if highlight_path and len(highlight_path) > 1:
        for i in range(len(highlight_path) - 1):
            u, v = highlight_path[i], highlight_path[i + 1]
            path_edges_set.add((u, v))
            path_edges_set.add((v, u))

    for u, v, data in graph.edges(data=True):
        pos_u = (graph.nodes[u]["x"], graph.nodes[u]["y"])
        pos_v = (graph.nodes[v]["x"], graph.nodes[v]["y"])

        if (u, v) in path_edges_set:
            continue

        normal_edge_x.extend([pos_u[0], pos_v[0], None])
        normal_edge_y.extend([pos_u[1], pos_v[1], None])

    fig.add_trace(
        go.Scatter(
            x=normal_edge_x,
            y=normal_edge_y,
            mode="lines",
            line=dict(color="#B0BEC5", width=2.5, dash="dot" if accessible_only else "solid"),
            hoverinfo="none",
            name="Walkways",
            showlegend=True
        )
    )

    # 2. Draw Highlighted Shortest Path
    if highlight_path and len(highlight_path) > 1:
        path_x = []
        path_y = []
        for node in highlight_path:
            path_x.append(graph.nodes[node]["x"])
            path_y.append(graph.nodes[node]["y"])

        fig.add_trace(
            go.Scatter(
                x=path_x,
                y=path_y,
                mode="lines+markers",
                line=dict(color="#FF6B35", width=5.5),
                marker=dict(size=12, color="#FF6B35", symbol="circle"),
                hoverinfo="text",
                text=[f"Step {idx + 1}: {graph.nodes[n]['name']} ({n})" for idx, n in enumerate(highlight_path)],
                name="Optimized Route",
                showlegend=True
            )
        )

    # 3. Draw Nodes (Buildings)
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

    fig.update_layout(
        title=dict(
            text="Interactive Campus Graph Navigation Map",
            x=0.5,
            xanchor="center",
            font=dict(size=18, color="#1D3557")
        ),
        paper_bgcolor="#F8F9FA",
        plot_bgcolor="#FFFFFF",
        hovermode="closest",
        margin=dict(b=30, l=30, r=30, t=50),
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
        height=600
    )

    return fig


def create_utilization_bar_chart(summary_df: pd.DataFrame) -> go.Figure:
    """
    Renders a bar chart comparing classroom seat utilization across courses.

    Args:
        summary_df: DataFrame containing 'Course', 'Utilization %', 'Enrolled', 'Capacity'.

    Returns:
        go.Figure: Interactive Plotly bar chart.
    """
    if summary_df.empty:
        return go.Figure()

    colors = []
    for util in summary_df["Utilization %"]:
        if util < 50.0:
            colors.append("#F4A261")  # Amber / Under-utilized
        elif util <= 90.0:
            colors.append("#2A9D8F")  # Teal / Optimal
        else:
            colors.append("#E76F51")  # Coral / Near Peak

    fig = go.Figure(
        data=[
            go.Bar(
                x=summary_df["Course"],
                y=summary_df["Utilization %"],
                marker=dict(color=colors),
                text=[f"{u}%" for u in summary_df["Utilization %"]],
                textposition="auto",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Utilization: %{y}%<br>"
                    "<extra></extra>"
                )
            )
        ]
    )

    fig.update_layout(
        title=dict(text="Classroom Space Utilization by Course (%)", x=0.5),
        yaxis=dict(title="Utilization Rate (%)", range=[0, 105]),
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

    Args:
        summary_df: DataFrame with 'Course', 'Enrolled', 'Capacity', 'Room'.

    Returns:
        go.Figure: Grouped bar chart.
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

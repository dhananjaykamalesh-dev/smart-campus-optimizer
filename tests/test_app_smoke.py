"""
test_app_smoke.py — Application-Level Smoke Tests
==================================================
Phase C: Engineering Quality

What are smoke tests?
    A "smoke test" is the simplest possible test — it checks that the
    application can start, its components can be loaded, and the data
    files it depends on are present and well-formed.
    The name comes from hardware engineering: "turn it on and check if
    it smokes."

Why not use Streamlit AppTest.from_file()?
    Streamlit's AppTest framework runs the entire app headlessly.
    However, it has a known threading deadlock on Windows when the app
    uses @st.cache_resource, heavy OR-Tools initialisation, or Pandas
    C-extensions — the ScriptRunner thread never signals completion.
    See: https://docs.streamlit.io/library/api-reference/app-testing

    Our approach instead tests the observable contract of the app at
    three levels:
      1. All Python source modules import cleanly (no import errors).
      2. All CSV data files exist and have the required columns.
      3. Core objects can be instantiated successfully.
    This gives equivalent confidence that "the app would start without
    crashing" without the OS-level threading limitations.

How to run:
    python -m pytest tests/test_app_smoke.py -v

Author: Smart Campus Optimizer Team
Phase: C — Engineering Quality
"""

import sys
import importlib
from pathlib import Path
import pytest
import pandas as pd

# -------------------------------------------------------------------
# Resolve the project root (parent of this tests/ directory).
# This is needed to import src modules and locate data/ files.
# -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent  # .../smart-campus-optimizer/
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"


# ===================================================================
# SMOKE TEST 1: All Source Modules Import Without Errors
# ===================================================================
@pytest.mark.parametrize("module_path", [
    "src.navigation.graph_builder",
    "src.navigation.pathfinder",
    "src.scheduling.timetable_solver",
    "src.allocation.resource_manager",
    "src.prediction.demand_predictor",
    "src.utils.visualizer",
])
def test_source_modules_import_cleanly(module_path):
    """
    Smoke Test: Verify every source module can be imported without raising
    an ImportError, SyntaxError, or any other exception.

    Why it matters:
        If a module has a broken import, a typo in a function signature,
        or references a deleted class, this test catches it immediately —
        before the user even opens the browser.

    What it checks:
        - No missing dependencies (e.g. 'No module named networkx')
        - No circular imports
        - No syntax errors introduced by recent edits
        - No typos in class or function definitions at module level

    Parameters:
        module_path — dot-separated module path (e.g. 'src.navigation.graph_builder')
    """
    try:
        module = importlib.import_module(module_path)
        assert module is not None, f"Module {module_path} imported as None"
    except ImportError as e:
        pytest.fail(
            f"ImportError for '{module_path}': {e}\n"
            f"Run: pip install -r requirements.txt"
        )
    except SyntaxError as e:
        pytest.fail(
            f"SyntaxError in '{module_path}': {e}\n"
            f"Check the file for typos."
        )


# ===================================================================
# SMOKE TEST 2: All Required CSV Data Files Exist
# ===================================================================
@pytest.mark.parametrize("csv_file", [
    "buildings.csv",
    "paths.csv",
    "rooms.csv",
    "courses.csv",
    "instructors.csv",
    "time_slots.csv",
    "historical_demand.csv",
])
def test_data_files_exist(csv_file):
    """
    Smoke Test: Verify every required CSV data file exists in the data/ folder.

    Why it matters:
        The app.py has a check_data_files() guard, but this test catches
        missing files BEFORE the app even runs — useful in CI where we
        verify the repository is self-contained.

    This test also serves as a "frictionless clone" check:
        If a new teammate clones the repository and runs the tests,
        missing CSVs are caught immediately with a clear error message.

    Parameters:
        csv_file — filename of the CSV to check (e.g. 'buildings.csv')
    """
    full_path = DATA_DIR / csv_file
    assert full_path.exists(), (
        f"Required data file not found: {full_path}\n"
        f"Make sure all CSV files are committed to the repository."
    )
    assert full_path.stat().st_size > 0, (
        f"Data file is empty: {full_path}"
    )


# ===================================================================
# SMOKE TEST 3: CSV Files Have the Required Columns
# ===================================================================
def test_buildings_csv_has_required_columns():
    """
    Smoke Test: buildings.csv has all columns that CampusGraph expects.

    The graph builder reads: building_id, name, x, y, category.
    If a column is renamed or deleted, the app crashes on startup.
    """
    df = pd.read_csv(DATA_DIR / "buildings.csv")
    required_cols = {"building_id", "name", "x", "y", "category"}
    missing = required_cols - set(df.columns)
    assert not missing, (
        f"buildings.csv is missing columns: {missing}\n"
        f"Found columns: {list(df.columns)}"
    )
    assert len(df) >= 2, "buildings.csv must have at least 2 buildings to form a graph"


def test_paths_csv_has_required_columns():
    """
    Smoke Test: paths.csv has all columns that CampusGraph expects.

    The graph builder reads: source, target, distance_m, is_accessible, is_covered.
    """
    df = pd.read_csv(DATA_DIR / "paths.csv")
    required_cols = {"source", "target", "distance_m", "is_accessible", "is_covered"}
    missing = required_cols - set(df.columns)
    assert not missing, (
        f"paths.csv is missing columns: {missing}\n"
        f"Found columns: {list(df.columns)}"
    )
    assert len(df) >= 1, "paths.csv must have at least 1 path"


def test_rooms_csv_has_required_columns():
    """
    Smoke Test: rooms.csv has all columns that the scheduling solver expects.
    """
    df = pd.read_csv(DATA_DIR / "rooms.csv")
    required_cols = {"room_id", "building_id", "name", "capacity", "is_lab"}
    missing = required_cols - set(df.columns)
    assert not missing, (
        f"rooms.csv is missing columns: {missing}\n"
        f"Found columns: {list(df.columns)}"
    )


def test_courses_csv_has_required_columns():
    """
    Smoke Test: courses.csv has all columns that the scheduling solver expects.
    """
    df = pd.read_csv(DATA_DIR / "courses.csv")
    required_cols = {"course_id", "name", "instructor_id", "enrolled_students", "requires_lab"}
    missing = required_cols - set(df.columns)
    assert not missing, (
        f"courses.csv is missing columns: {missing}\n"
        f"Found columns: {list(df.columns)}"
    )


# ===================================================================
# SMOKE TEST 4: Core Objects Instantiate Without Errors
# ===================================================================
def test_campus_graph_instantiates():
    """
    Smoke Test: CampusGraph can be created from the real CSV files.

    This is the closest we can get to "the app starts" — it verifies
    that the graph-builder reads the data correctly and builds a
    non-empty NetworkX graph.
    """
    from src.navigation.graph_builder import CampusGraph

    campus = CampusGraph(
        buildings_file=str(DATA_DIR / "buildings.csv"),
        paths_file=str(DATA_DIR / "paths.csv")
    )
    # The graph must have at least 2 nodes and 1 edge to be meaningful
    assert campus.graph.number_of_nodes() >= 2, (
        "CampusGraph has no nodes — check buildings.csv"
    )
    assert campus.graph.number_of_edges() >= 1, (
        "CampusGraph has no edges — check paths.csv"
    )


def test_timetable_solver_instantiates():
    """
    Smoke Test: CampusTimetableSolver can be created from the real CSV files.

    This verifies that all four scheduling CSVs (rooms, courses, instructors,
    time_slots) are readable and parsed without error.
    Note: this test does NOT run the CP-SAT solver — just instantiation.
    """
    from src.scheduling.timetable_solver import CampusTimetableSolver

    solver = CampusTimetableSolver(
        rooms_file=str(DATA_DIR / "rooms.csv"),
        courses_file=str(DATA_DIR / "courses.csv"),
        instructors_file=str(DATA_DIR / "instructors.csv"),
        time_slots_file=str(DATA_DIR / "time_slots.csv")
    )
    # Should have loaded courses and rooms dictionaries
    assert len(solver.courses) >= 1, (
        "TimetableSolver loaded 0 courses — check courses.csv"
    )
    assert len(solver.rooms) >= 1, (
        "TimetableSolver loaded 0 rooms — check rooms.csv"
    )


def test_resource_manager_instantiates():
    """
    Smoke Test: CampusResourceManager can be created using empty or dummy schedule records.

    This verifies the allocation module can initialize and operate on room data.
    """
    from src.allocation.resource_manager import CampusResourceManager

    # Test with dummy schedule record and room dictionary
    manager = CampusResourceManager(
        schedule_records=[],
        all_rooms={"R101": {"room_id": "R101", "name": "Room 101", "capacity": 50, "is_lab": False}}
    )
    assert manager.all_rooms is not None
    idle_analysis = manager.get_idle_rooms_analysis()
    assert idle_analysis["idle_rooms_count"] == 1

# Teammate Setup & Collaboration Guide

Welcome to the team! This guide explains how to set up, edit, and run the **Smart Campus Optimization System** on your laptop in under 3 minutes with zero hassle.

---

## ⚡ 1-Minute Quickstart (Running the Project)

### Prerequisites: Python
Every teammate needs Python installed:
1. Download Python (version 3.10, 3.11, or 3.12) from [python.org](https://www.python.org/downloads/).
2. **CRITICAL STEP (Windows Users)**: During installation, check the box that says:
   ✅ **"Add Python to PATH"** (at the bottom of the first installer screen).

### How to Run:
- **On Windows**: Just double-click the file named:
  👉 **`run.bat`**
  *(It will automatically check packages and open the app in your browser at `http://localhost:8501`)*.
- **On Mac / Linux**: Open Terminal in this folder and run:
  ```bash
  bash run.sh
  ```
- **Or via Terminal (Any OS)**:
  ```bash
  pip install -r requirements.txt
  streamlit run app.py
  ```

---

## 🤝 How to Collaborate & Share Changes

### Option A: Using GitHub (Recommended for Professional Teamwork)
1. **Host Repository**:
   - The team lead pushes this repo to GitHub.
   - Go to repo **Settings** $\to$ **Collaborators** $\to$ click **Add people** and enter your teammates' GitHub usernames.
2. **Teammates Clone**:
   ```bash
   git clone <REPO_URL>
   cd smart-campus-optimizer
   ```
3. **Sharing Updates**:
   - Before working: `git pull` (downloads the latest changes from teammates).
   - After making changes:
     ```bash
     git add .
     git commit -m "Explain what you changed (e.g., added new room data)"
     git push
     ```

### Option B: Using Google Drive / OneDrive / Zip File (Quickest Offline Method)
1. Zip the entire `smart-campus-optimizer` folder.
2. Share via Google Drive or WhatsApp group.
3. Teammates unzip it and double-click `run.bat`!

---

## ✏️ How Can Teammates Suggest & Make Edits?

1. **Changing Campus Map Data (Buildings & Walkways)**:
   - Edit [`data/buildings.csv`](../data/buildings.csv) in Excel or Notepad to add new buildings or change names/coordinates.
   - Edit [`data/paths.csv`](../data/paths.csv) to change walking distances or mark wheelchair ramps.
2. **Changing Courses, Rooms, & Schedules**:
   - Edit [`data/rooms.csv`](../data/rooms.csv) to modify seating capacities or add labs.
   - Edit [`data/courses.csv`](../data/courses.csv) to change class sizes or faculty.
3. **Modifying the UI or Presentation Text**:
   - Open [`app.py`](../app.py) in VS Code or Notepad to change titles, descriptions, or styling.
4. **Verifying Nothing Broke**:
   - Run the automated tests anytime by typing in your terminal:
     ```bash
     pytest
     ```
   - If all 14 tests pass, your changes are 100% mathematically consistent and bug-free!

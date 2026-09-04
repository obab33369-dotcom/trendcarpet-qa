"""
REFORMA Local Orchestrator Loop - Configuration Module
Defines directory paths, environment variable files, subprocess locations,
and configurable parameters for the background monitor.
"""

import os
import sys
from pathlib import Path

# --- Absolute Paths ---
# Project root directory
REFORMA_DIR = Path(__file__).resolve().parent.parent

# Orchestrator subfolder
ORCHESTRATOR_DIR = REFORMA_DIR / "orchestrator"

# Logs subfolder for workers
LOGS_DIR = ORCHESTRATOR_DIR / "logs"

# Subprocess paths
TURBOFLOW_DIR = REFORMA_DIR / "reforma-turboflow"
TURBOFLOW_RUN_PY = TURBOFLOW_DIR / "run.py"
TRIAGE_SCRIPT = ORCHESTRATOR_DIR / "triage.py"

# --- OneDrive Paths ---
# Base pictures folder
ONEDRIVE_PICTURES_DIR = Path(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures")

# Configurable list of OneDrive target subfolders to watch.
# The daemon monitors changes in these directories.
MONITOR_DIRS = [
    ONEDRIVE_PICTURES_DIR / "turboflow",
]

# --- Environment & Keys ---
# Path to the environment variables file containing the Gemini API Key
GEMINI_KEY_PATH = Path(r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env")

# --- Configurable Loop Parameters ---
# Sleep interval (seconds) between OneDrive directory scans
LOOP_SLEEP_INTERVAL = 15.0

# Path to the persisted scanner state file (tracks seen file modifications across loop restarts)
STATE_FILE_PATH = ORCHESTRATOR_DIR / "scanner_state.json"

# --- Logging Config ---
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

def get_gemini_api_key() -> str:
    """
    Utility function to load the Gemini API Key from the configured .env path
    or fallback to the current environment variable.
    """
    if GEMINI_KEY_PATH.exists():
        try:
            with open(GEMINI_KEY_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        k, v = line.split('=', 1)
                        if k.strip() == "GEMINI_API_KEY":
                            return v.strip().strip('"').strip("'")
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to read {GEMINI_KEY_PATH}: {e}\n")
    return os.environ.get("GEMINI_API_KEY", "")

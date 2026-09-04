"""
REFORMA Local Orchestrator Loop - Daemon Runner
Monitors target OneDrive product subfolders, triggers the turboflow pipeline
and triage scripts when changes occur, handles failures, and isolates execution
logs in individual worker log files.
"""

import os
import sys
import time
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# --- Path Injection for Portability ---
ORCHESTRATOR_DIR = Path(__file__).resolve().parent
REFORMA_DIR = ORCHESTRATOR_DIR.parent

if str(REFORMA_DIR) not in sys.path:
    sys.path.insert(0, str(REFORMA_DIR))
if str(ORCHESTRATOR_DIR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_DIR))

import config

logger = None

def scan_directories(dirs: list) -> dict:
    """
    Scans the configured list of directories recursively and builds a signature dict:
    { relative_path: { mtime: float, size: int } }
    """
    state = {}
    for d in dirs:
        path = Path(d)
        if not path.exists():
            continue
        try:
            # Recursively walk path
            for f in path.rglob("*"):
                if f.is_file():
                    # Ignore temporary / operating system files
                    if f.name.startswith(".") or f.name.startswith("~"):
                        continue
                    try:
                        stat = f.stat()
                        # Track using relative path from pictures parent to keep it stable
                        rel_path = str(f.relative_to(config.ONEDRIVE_PICTURES_DIR))
                        state[rel_path] = {
                            "mtime": stat.st_mtime,
                            "size": stat.st_size
                        }
                    except Exception:
                        pass
        except Exception as e:
            if logger:
                logger.error(f"Error scanning directory {d}: {e}")
    return state

def detect_changes(old_state: dict, new_state: dict) -> bool:
    """
    Detects if files are added, modified, or deleted between old and new state.
    """
    # Check for additions and modifications
    for path, info in new_state.items():
        if path not in old_state:
            return True
        if info["mtime"] != old_state[path]["mtime"] or info["size"] != old_state[path]["size"]:
            return True
    
    # Check for deletions
    for path in old_state:
        if path not in new_state:
            return True
            
    return False

def load_state() -> dict:
    """
    Loads the persisted scanner state from config.STATE_FILE_PATH.
    """
    if config.STATE_FILE_PATH.exists():
        try:
            with open(config.STATE_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            if logger:
                logger.error(f"Failed to load state from {config.STATE_FILE_PATH}: {e}")
    return {}

def save_state(state: dict):
    """
    Persists the scanner state dictionary to config.STATE_FILE_PATH.
    """
    try:
        config.STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(config.STATE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        if logger:
            logger.error(f"Failed to save state to {config.STATE_FILE_PATH}: {e}")

def run_pipeline(mode: str) -> bool:
    """
    Spawns the turboflow run.py pipeline and triage script in isolated subprocesses.
    Outputs are logged to a separate worker run file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = config.LOGS_DIR / f"worker_{timestamp}.log"
    
    logger.info(f"Spawning worker run. Worker log: {log_file}")
    
    # Prepare subprocess environment
    env = os.environ.copy()
    api_key = config.get_gemini_api_key()
    if api_key:
        env["GEMINI_API_KEY"] = api_key
        logger.info("Gemini API key loaded into subprocess environment.")
    else:
        logger.warning("Gemini API key not found. Subprocesses might fail visual tasks.")
        
    try:
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as lf:
            lf.write(f"=== REFORMA WORKER RUN STARTED AT {datetime.now().isoformat()} ===\n")
            lf.write(f"Mode: {mode.upper()}\n")
            lf.write(f"Turboflow Script: {config.TURBOFLOW_RUN_PY}\n")
            lf.write("=" * 60 + "\n\n")
            lf.flush()
            
            # --- STEP 1: Launch TurboFlow run.py ---
            turboflow_args = [sys.executable, str(config.TURBOFLOW_RUN_PY), mode]
            logger.info(f"Running Turboflow subprocess: {' '.join(turboflow_args)}")
            
            proc1 = subprocess.run(
                turboflow_args,
                cwd=str(config.TURBOFLOW_DIR),
                env=env,
                stdout=lf,
                stderr=lf,
                text=True
            )
            
            lf.write(f"\n\n=== TURBOFLOW EXIT CODE: {proc1.returncode} ===\n")
            lf.flush()
            
            if proc1.returncode != 0:
                logger.error(f"Turboflow pipeline execution failed with code {proc1.returncode}.")
                lf.write("❌ Turboflow failed. Aborting automated triage.\n")
                return False
                
            # --- STEP 2: Launch Triage module ---
            logger.info("Turboflow completed successfully. Spawning Triage module...")
            lf.write("\n" + "=" * 60 + "\n")
            lf.write(f"=== STARTING AUTOMATED TRIAGE AT {datetime.now().isoformat()} ===\n")
            lf.write("=" * 60 + "\n\n")
            lf.flush()
            
            # Triage script runs in 'dry' mode by default to verify outputs safely
            triage_args = [sys.executable, str(config.TRIAGE_SCRIPT), "--mode", "dry"]
            logger.info(f"Running Triage subprocess: {' '.join(triage_args)}")
            
            proc2 = subprocess.run(
                triage_args,
                cwd=str(config.ORCHESTRATOR_DIR),
                env=env,
                stdout=lf,
                stderr=lf,
                text=True
            )
            
            lf.write(f"\n\n=== TRIAGE EXIT CODE: {proc2.returncode} ===\n")
            lf.write(f"=== WORKER RUN FINISHED AT {datetime.now().isoformat()} ===\n")
            lf.flush()
            
            if proc2.returncode != 0:
                logger.error(f"Triage execution failed with code {proc2.returncode}.")
                return False
                
            logger.info("Worker run finished successfully (Turboflow + Triage logs combined).")
            return True
            
    except Exception as e:
        logger.exception(f"Exception during worker run execution: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="REFORMA Local Orchestrator Daemon Loop")
    parser.add_argument("--full", action="store_true", help="Run the turboflow pipeline in --full mode")
    parser.add_argument("--force", action="store_true", help="Force run the pipeline once immediately on startup")
    args = parser.parse_args()
    
    # Initialize directory structure
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Setup Daemon Logger
    global logger
    logging.basicConfig(
        level=logging.INFO,
        format=config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.ORCHESTRATOR_DIR / "orchestrator.log", encoding="utf-8")
        ]
    )
    logger = logging.getLogger("orchestrator")
    
    # Write PID file for process tracking
    pid_file = config.ORCHESTRATOR_DIR / "orchestrator.pid"
    try:
        pid_file.write_text(str(os.getpid()), encoding='utf-8')
    except Exception as e:
        logger.warning(f"Could not create PID file: {e}")
    
    logger.info("=" * 60)
    logger.info("      REFORMA LOCAL AUTOMATION ORCHESTRATOR DAEMON     ")
    logger.info("=" * 60)
    logger.info(f"Project root:      {config.REFORMA_DIR}")
    logger.info(f"Monitored paths:   {[str(d) for d in config.MONITOR_DIRS]}")
    logger.info(f"Sleep interval:    {config.LOOP_SLEEP_INTERVAL} seconds")
    logger.info(f"Target mode:       {'--full' if args.full else '--test'}")
    logger.info("-" * 60)
    
    # Verify critical entrypoints
    if not config.TURBOFLOW_RUN_PY.exists():
        logger.critical(f"Missing Turboflow runner script: {config.TURBOFLOW_RUN_PY}")
        sys.exit(1)
        
    if not config.TRIAGE_SCRIPT.exists():
        logger.critical(f"Missing Triage module script: {config.TRIAGE_SCRIPT}")
        sys.exit(1)
        
    # Check Gemini key path status
    key = config.get_gemini_api_key()
    if key:
        logger.info("Gemini API key successfully verified and loaded.")
    else:
        logger.warning("Gemini API key file not found! API calls will fail.")
        
    # Load state
    last_state = load_state()
    logger.info(f"Loaded database state with {len(last_state)} tracked files.")
    
    # Initial scan
    current_state = scan_directories(config.MONITOR_DIRS)
    logger.info(f"Initial folder scan found {len(current_state)} files.")
    
    # Prevent running immediately on startup if state file was missing
    if not last_state:
        logger.info("First run detected. Initializing state database with current files to prevent false alarm.")
        last_state = current_state
        save_state(last_state)
        
    # Handle force runs
    if args.force:
        logger.info("Force run requested. Spawning worker immediately...")
        run_pipeline("--full" if args.full else "--test")
        last_state = current_state
        save_state(last_state)
        
    logger.info("Daemon loop started. Press Ctrl+C to terminate.")
    
    try:
        while True:
            time.sleep(config.LOOP_SLEEP_INTERVAL)
            
            # Retrieve latest filesystem state
            scanned = scan_directories(config.MONITOR_DIRS)
            
            if detect_changes(last_state, scanned):
                logger.info("FileSystem changes detected! Initiating quiet-period settling delay...")
                
                # Settle loop to ensure files have finished copying/uploading
                current = scanned
                while True:
                    time.sleep(5.0)
                    probe = scan_directories(config.MONITOR_DIRS)
                    if probe == current:
                        logger.info("Directories have stabilized. Initiating run...")
                        break
                    else:
                        logger.info("File activity still detected. Resetting settle delay...")
                        current = probe
                
                # Trigger worker run
                success = run_pipeline("--full" if args.full else "--test")
                
                if success:
                    logger.info("Pipeline and triage run finished successfully.")
                else:
                    logger.error("Pipeline or triage run encountered errors.")
                    
                # Update saved state regardless of success to avoid infinite failure loops on bad files
                last_state = current
                save_state(last_state)
                logger.info("Daemon monitoring resumed. Waiting for changes...")
                
    except KeyboardInterrupt:
        logger.info("Termination signal received. Exiting daemon loop gracefully.")
    except Exception as e:
        logger.critical(f"Daemon loop crashed with exception: {e}", exc_info=True)
        sys.exit(1)
    finally:
        try:
            if pid_file.exists():
                pid_file.unlink()
        except Exception:
            pass

if __name__ == "__main__":
    main()

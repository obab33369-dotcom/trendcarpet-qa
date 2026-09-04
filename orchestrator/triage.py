import os
import sys
import json
import csv
import subprocess
import re
import logging
from datetime import datetime
from pathlib import Path

# Paths resolved relative to this script for portability on Windows
ORCHESTRATOR_DIR = Path(__file__).resolve().parent
REFORMA_DIR = ORCHESTRATOR_DIR.parent
TURBOFLOW_DIR = REFORMA_DIR / "reforma-turboflow"
ROOMS_JSON_PATH = TURBOFLOW_DIR / "rooms_turboflow.json"
READY_CSV_PATH = TURBOFLOW_DIR / "turboflow_ready.csv"
CLEANUP_SCRIPT_PATH = REFORMA_DIR / "clean_interiors_gemini.py"
STATUS_JSON_PATH = ORCHESTRATOR_DIR / "status.json"
LOG_FILE_PATH = ORCHESTRATOR_DIR / "triage.log"

# Setup robust logging
def setup_logger():
    # Make sure parent directory of log file exists
    ORCHESTRATOR_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("reforma_triage")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates if re-imported
    if logger.handlers:
        logger.handlers.clear()
        
    # Stream handler for console output (sys.stdout)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    logger.addHandler(sh)
    
    # File handler for consolidated logs
    try:
        fh = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        logger.addHandler(fh)
    except Exception as e:
        print(f"Warning: Could not create log file handler: {e}", file=sys.stderr)
        
    return logger

logger = setup_logger()

def verify_turboflow_outputs() -> dict:
    """
    Verifies the presence and structural integrity of turboflow pipeline outputs:
    1. rooms_turboflow.json (must exist, be valid JSON, not empty, and contain objects)
    2. turboflow_ready.csv (must exist, be valid CSV, not empty, and have expected headers)
    """
    logger.info("Starting integrity checks on turboflow output files...")
    report = {
        "rooms_turboflow_json": {
            "exists": False,
            "valid": False,
            "empty": True,
            "size_bytes": 0,
            "error": None
        },
        "turboflow_ready_csv": {
            "exists": False,
            "valid": False,
            "empty": True,
            "size_bytes": 0,
            "error": None
        }
    }

    # Verify rooms_turboflow.json
    try:
        p_json = Path(ROOMS_JSON_PATH)
        if p_json.exists():
            report["rooms_turboflow_json"]["exists"] = True
            size = p_json.stat().st_size
            report["rooms_turboflow_json"]["size_bytes"] = size
            if size > 0:
                report["rooms_turboflow_json"]["empty"] = False
                with open(p_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        report["rooms_turboflow_json"]["valid"] = True
                        logger.info(f"Integrity check PASSED for rooms_turboflow.json ({len(data)} items)")
                    else:
                        report["rooms_turboflow_json"]["error"] = "JSON is not a non-empty list of rooms"
                        logger.error("rooms_turboflow.json integrity FAILED: Not a non-empty list")
            else:
                report["rooms_turboflow_json"]["error"] = "File is empty (0 bytes)"
                logger.error("rooms_turboflow.json integrity FAILED: File is empty")
        else:
            report["rooms_turboflow_json"]["error"] = "File not found"
            logger.error(f"rooms_turboflow.json integrity FAILED: File not found at {ROOMS_JSON_PATH}")
    except json.JSONDecodeError as jde:
        report["rooms_turboflow_json"]["error"] = f"JSON malformed: {str(jde)}"
        logger.error(f"rooms_turboflow.json integrity FAILED: Malformed JSON: {jde}")
    except Exception as e:
        report["rooms_turboflow_json"]["error"] = str(e)
        logger.error(f"rooms_turboflow.json integrity FAILED with exception: {e}")

    # Verify turboflow_ready.csv
    try:
        p_csv = Path(READY_CSV_PATH)
        if p_csv.exists():
            report["turboflow_ready_csv"]["exists"] = True
            size = p_csv.stat().st_size
            report["turboflow_ready_csv"]["size_bytes"] = size
            if size > 0:
                report["turboflow_ready_csv"]["empty"] = False
                with open(p_csv, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if header:
                        # Normalize headers for case-insensitive verification
                        actual_headers = {h.strip().lower() for h in header}
                        expected_headers = {"prompt", "image_references", "image_tags", "aspect_ratio"}
                        
                        # Validate headers overlap
                        if "prompt" in actual_headers or expected_headers.issubset(actual_headers):
                            # Count the remaining data rows to verify it is not empty
                            row_count = sum(1 for _ in reader)
                            if row_count > 0:
                                report["turboflow_ready_csv"]["valid"] = True
                                logger.info(f"Integrity check PASSED for turboflow_ready.csv ({row_count} rows)")
                            else:
                                report["turboflow_ready_csv"]["error"] = "CSV contains only headers, no data rows"
                                logger.error("turboflow_ready.csv integrity FAILED: Contains only headers")
                        else:
                            report["turboflow_ready_csv"]["error"] = f"CSV header mismatch. Found: {header}"
                            logger.error(f"turboflow_ready.csv integrity FAILED: Header mismatch: {header}")
                    else:
                        report["turboflow_ready_csv"]["error"] = "CSV contains no headers or rows"
                        logger.error("turboflow_ready.csv integrity FAILED: No headers or rows found")
            else:
                report["turboflow_ready_csv"]["error"] = "File is empty (0 bytes)"
                logger.error("turboflow_ready.csv integrity FAILED: File is empty")
        else:
            report["turboflow_ready_csv"]["error"] = "File not found"
            logger.error(f"turboflow_ready.csv integrity FAILED: File not found at {READY_CSV_PATH}")
    except Exception as e:
        report["turboflow_ready_csv"]["error"] = str(e)
        logger.error(f"turboflow_ready.csv integrity FAILED with exception: {e}")

    return report

def run_quality_checks(
    mode: str = 'dry',
    folder_filter: str = '',
    limit_folders: int = None,
    limit_images: int = None,
    start_folder: int = 1
) -> dict:
    """
    Spawns clean_interiors_gemini.py in an isolated subprocess.
    Coordinates option input using standard input injection to support the interactive script.
    """
    logger.info(f"Preparing quality check pipeline (clean_interiors_gemini.py) in '{mode}' mode...")
    
    script_path = Path(CLEANUP_SCRIPT_PATH)
    if not script_path.exists():
        msg = f"Quality check script not found at {script_path}"
        logger.error(msg)
        return {
            "script_executed": False,
            "mode": mode,
            "total_analyzed": 0,
            "matches": 0,
            "mismatches": 0,
            "failures": 1,
            "exit_code": -1,
            "error_message": msg
        }

    # Map target modes to interactive prompt inputs
    mode_map = {
        "status": "1",
        "dry": "2",
        "sharp": "3"
    }
    choice = mode_map.get(mode.lower())
    if not choice:
        msg = f"Invalid mode '{mode}' specified. Must be 'status', 'dry', or 'sharp'."
        logger.error(msg)
        return {
            "script_executed": False,
            "mode": mode,
            "total_analyzed": 0,
            "matches": 0,
            "mismatches": 0,
            "failures": 1,
            "exit_code": -1,
            "error_message": msg
        }

    # Prepare input string representing answers to the 5 interactive prompts:
    # 1. Menu selection: '1', '2', or '3'
    # 2. Folder filter: substring/prefix
    # 3. Limit folders to process: number or empty (unlimited)
    # 4. Limit total images to analyze: number or empty (unlimited)
    # 5. Start from folder index: number or empty (default 1)
    folder_filter_str = str(folder_filter) if folder_filter else ""
    limit_folders_str = str(limit_folders) if limit_folders is not None else ""
    limit_images_str = str(limit_images) if limit_images is not None else ""
    start_folder_str = str(start_folder) if start_folder is not None else ""

    stdin_payload = f"{choice}\n{folder_filter_str}\n{limit_folders_str}\n{limit_images_str}\n{start_folder_str}\n"

    try:
        logger.info(f"Launching clean_interiors_gemini.py subprocess. Cwd: {REFORMA_DIR}")
        
        # Run process using sys.executable to preserve exact environment interpreter
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=stdin_payload,
            text=True,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            cwd=str(REFORMA_DIR)
        )

        stdout = result.stdout
        stderr = result.stderr

        # Capture stderr warnings if any
        if stderr.strip():
            logger.warning(f"Subprocess stderr output:\n{stderr}")

        logger.info(f"Subprocess finished with exit code {result.returncode}")

        # Parse final results block from stdout via regex
        analyzed = 0
        approved = 0
        rejected = 0
        errors = 0

        analyzed_match = re.search(r"Total analyzed:\s+(\d+)", stdout)
        approved_match = re.search(r"Approved \(kept\):\s+(\d+)", stdout)
        rejected_match = re.search(r"Rejected:\s+(\d+)", stdout)
        errors_match = re.search(r"Errors/Skipped:\s+(\d+)", stdout)

        if analyzed_match:
            analyzed = int(analyzed_match.group(1))
        if approved_match:
            approved = int(approved_match.group(1))
        if rejected_match:
            rejected = int(rejected_match.group(1))
        if errors_match:
            errors = int(errors_match.group(1))

        # Check for immediate fatal execution errors
        script_executed = True
        error_msg = None
        
        if result.returncode != 0:
            error_msg = f"Subprocess exited with failure code {result.returncode}"
            logger.error(error_msg)
            # If no stats parsed, mark as failure
            if not analyzed_match:
                errors += 1
                
        if "[ERROR]" in stdout:
            error_line = re.search(r"(\[ERROR\].*)", stdout)
            error_msg = error_line.group(1) if error_line else "Interiors check script raised an error."
            logger.error(f"Subprocess error output: {error_msg}")
            script_executed = False

        qc_report = {
            "script_executed": script_executed,
            "mode": mode,
            "total_analyzed": analyzed,
            "matches": approved,
            "mismatches": rejected,
            "failures": errors,
            "exit_code": result.returncode,
            "error_message": error_msg
        }

        logger.info(
            f"Quality Check Summary - Mode: {mode.upper()}, Analyzed: {analyzed}, "
            f"Matches: {approved}, Mismatches: {rejected}, Failures: {errors}"
        )
        return qc_report

    except Exception as e:
        msg = f"Failed to execute subprocess: {e}"
        logger.error(msg)
        return {
            "script_executed": False,
            "mode": mode,
            "total_analyzed": 0,
            "matches": 0,
            "mismatches": 0,
            "failures": 1,
            "exit_code": -1,
            "error_message": msg
        }

def run_triage(
    mode: str = 'dry',
    folder_filter: str = '',
    limit_folders: int = None,
    limit_images: int = None,
    start_folder: int = 1
) -> dict:
    """
    Primary orchestrator pipeline entrypoint:
    1. Verifies structural integrity of turboflow outputs (JSON/CSV).
    2. Spawns and coordinates clean_interiors_gemini.py subprocess checks.
    3. Consolidates check details and saves health report to status.json.
    """
    logger.info("==================================================")
    logger.info(f"STARTING AUTOMATED PIPELINE TRIAGE: {datetime.now().isoformat()}")
    logger.info("==================================================")

    # 1. Run Integrity Checks
    integrity = verify_turboflow_outputs()

    # 2. Run Subprocess Quality Checks
    quality = run_quality_checks(
        mode=mode,
        folder_filter=folder_filter,
        limit_folders=limit_folders,
        limit_images=limit_images,
        start_folder=start_folder
    )

    # 3. Evaluate health metrics
    json_healthy = integrity["rooms_turboflow_json"]["valid"]
    csv_healthy = integrity["turboflow_ready_csv"]["valid"]
    quality_healthy = quality["script_executed"] and quality["exit_code"] == 0 and quality["failures"] == 0

    healthy = json_healthy and csv_healthy and quality_healthy

    # Construct overall pipeline health message
    if healthy:
        health_msg = "Pipeline is healthy. All outputs verified and quality checks passed."
    else:
        reasons = []
        if not json_healthy:
            reasons.append(f"rooms_turboflow.json invalid: {integrity['rooms_turboflow_json']['error']}")
        if not csv_healthy:
            reasons.append(f"turboflow_ready.csv invalid: {integrity['turboflow_ready_csv']['error']}")
        if not quality["script_executed"]:
            reasons.append(f"Quality check execution failed: {quality['error_message']}")
        elif quality["exit_code"] != 0:
            reasons.append(f"Quality check subprocess failed with exit code {quality['exit_code']}")
        elif quality["failures"] > 0:
            reasons.append(f"Quality checks reported {quality['failures']} issues/errors")

        health_msg = f"Pipeline is unhealthy. Issues found: {'; '.join(reasons)}"
        logger.error(health_msg)

    # Consolidate status report
    report = {
        "timestamp": datetime.now().isoformat(),
        "turboflow_integrity": integrity,
        "quality_check": quality,
        "pipeline_health": {
            "healthy": healthy,
            "message": health_msg
        }
    }

    # Save consolidated report to status.json
    try:
        STATUS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STATUS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Consolidated run results successfully saved to: {STATUS_JSON_PATH}")
    except Exception as e:
        logger.error(f"Failed to save status report to {STATUS_JSON_PATH}: {e}")

    return report

def get_latest_status(status_file_path: str = None) -> dict:
    """
    Exposes a simple lightweight API function to return the pipeline status in real-time.
    Loads status.json if it exists, otherwise falls back to quick run-time integrity check.
    """
    target_path = Path(status_file_path) if status_file_path else STATUS_JSON_PATH
    if target_path.exists():
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "pipeline_health": {
                    "healthy": False,
                    "message": f"Failed to parse existing status JSON: {e}"
                }
            }
    
    # Fallback: perform fast integrity check only if status.json is not found
    integrity = verify_turboflow_outputs()
    json_healthy = integrity["rooms_turboflow_json"]["valid"]
    csv_healthy = integrity["turboflow_ready_csv"]["valid"]
    healthy = json_healthy and csv_healthy
    
    return {
        "timestamp": datetime.now().isoformat(),
        "turboflow_integrity": integrity,
        "quality_check": {
            "script_executed": False,
            "mode": None,
            "total_analyzed": 0,
            "matches": 0,
            "mismatches": 0,
            "failures": 0,
            "exit_code": None,
            "error_message": "No central status report found. Performed real-time integrity check fallback."
        },
        "pipeline_health": {
            "healthy": healthy,
            "message": (
                "Real-time integrity checks passed. Central status.json was missing." 
                if healthy else "Real-time integrity checks failed and central status.json was missing."
            )
        }
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="REFORMA Pipeline Quality Assurance & Triage")
    parser.add_argument(
        "--mode", choices=["status", "dry", "sharp"], default="dry",
        help="Subprocess run mode: 'status' (verify only), 'dry' (dry-run gemini checks), 'sharp' (execute cleanup)"
    )
    parser.add_argument(
        "--filter", type=str, default="",
        help="Subdirectory name prefix/substring filter for candidate images"
    )
    parser.add_argument(
        "--limit-folders", type=int, default=None,
        help="Limit the number of subdirectories to inspect"
    )
    parser.add_argument(
        "--limit-images", type=int, default=None,
        help="Limit the total number of candidate images to process"
    )
    parser.add_argument(
        "--start-folder", type=int, default=1,
        help="Folder index to start processing from (1-indexed)"
    )
    
    args = parser.parse_args()
    
    # Run triage orchestrator
    res = run_triage(
        mode=args.mode,
        folder_filter=args.filter,
        limit_folders=args.limit_folders,
        limit_images=args.limit_images,
        start_folder=args.start_folder
    )
    
    print("\n" + "=" * 50)
    print("TRIAGE PIPELINE RESULTS SUMMARY")
    print("=" * 50)
    print(f"Timestamp:       {res['timestamp']}")
    print(f"Pipeline Health: {'[HEALTHY]' if res['pipeline_health']['healthy'] else '[UNHEALTHY]'}")
    print(f"Message:         {res['pipeline_health']['message']}")
    print("=" * 50)

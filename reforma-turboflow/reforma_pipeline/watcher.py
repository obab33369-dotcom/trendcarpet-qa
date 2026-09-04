import os
import time
import shutil
import re
from pathlib import Path
from reforma_pipeline.config import NEW_WHITE_BG_DIR, TOPAZ_DIR, ORIG_DIR

# Base scratch directory for isolated file copies
script_dir = os.path.dirname(os.path.abspath(__file__))
turboflow_dir = os.path.dirname(script_dir)
SCRATCH_ACTIVE_DIR = os.path.join(turboflow_dir, "scratch", "active_downloads")

class FileWatcher:
    """
    Watches OneDrive folders for new product images/folders, implements
    a size-based debounce filter to ensure files are fully synched/written,
    and copies them to a local isolated scratch space for processing.
    """
    def __init__(self, check_interval_seconds=2, debounce_seconds=3):
        self.check_interval = check_interval_seconds
        self.debounce_seconds = debounce_seconds
        # Tracks file state: { file_path: { "size": int, "mtime": float, "last_changed": float, "stable": bool } }
        self.file_states = {}
        # Tracks active SKUs being processed to avoid double triggers: { sku: timestamp }
        self.active_skus = {}

    def extract_sku_and_slot(self, file_path):
        """
        Attempts to parse SKU and Slot from file paths.
        Examples:
          - TEST TOPAZ: 1200180_19791-black-oak-2-26U-wonder.webp -> SKU: 19791-black-oak, Slot: 2
          - Refoma white bg fix/19791-black-oak/19791-black-oak-2-w-wonder.jpg -> SKU: 19791-black-oak, Slot: 2
        """
        filename = os.path.basename(file_path)
        parent_dir = os.path.basename(os.path.dirname(file_path))
        
        # 1. Check parent folder name for SKU (common in white background fix / original folders)
        # Often the parent folder is like "19791-black-oak" or "19791-walnut (19791-walnut)"
        sku = None
        sku_match = re.search(r'\(([^)]+)\)', parent_dir)
        if sku_match:
            sku = sku_match.group(1).strip()
        elif re.match(r'^[a-zA-Z0-9_-]+$', parent_dir) and parent_dir.lower() != "artiklar" and parent_dir.lower() != "zoom":
            sku = parent_dir
            
        # 2. Check filename keywords/numbers if parent directory is generic (e.g. TEST TOPAZ, zoom, artiklar)
        if not sku or sku.lower() in ("artiklar", "zoom", "pictures"):
            # Try to match Topaz format: e.g. 1200180_19791-black-oak-2-26U-wonder.webp
            topaz_match = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder", filename, re.IGNORECASE)
            if topaz_match:
                sku = topaz_match.group(1).strip()
            else:
                # Fallback to standard digit groupings
                digit_match = re.search(r'^([a-zA-Z0-9_-]+)[-_](\d+)', filename)
                if digit_match:
                    sku = digit_match.group(1).strip()
        
        # Normalize SKU
        if sku:
            sku = sku.strip()
        return sku

    def scan_directories(self):
        """Scans the configured watch directories for files."""
        found_files = []
        
        # Helper to filter image files
        def is_image(name):
            return name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))

        # 1. Scan White Background Fix Dir
        if os.path.exists(NEW_WHITE_BG_DIR):
            for root, _, files in os.walk(NEW_WHITE_BG_DIR):
                for f in files:
                    if is_image(f):
                        found_files.append(os.path.join(root, f))
                        
        # 2. Scan TEST TOPAZ Dir
        if os.path.exists(TOPAZ_DIR):
            for f in os.listdir(TOPAZ_DIR):
                path = os.path.join(TOPAZ_DIR, f)
                if os.path.isfile(path) and is_image(f):
                    found_files.append(path)

        # 3. Scan Original Images Dir
        if os.path.exists(ORIG_DIR):
            for root, _, files in os.walk(ORIG_DIR):
                for f in files:
                    if is_image(f):
                        found_files.append(os.path.join(root, f))
                        
        return found_files

    def update_states(self, found_files):
        """Updates states of scanned files and returns lists of newly stabilized files."""
        now = time.time()
        stabilized_files = []

        # Remove files that are no longer present in watch directories
        missing_files = set(self.file_states.keys()) - set(found_files)
        for f in missing_files:
            del self.file_states[f]

        # Update and check each file
        for f in found_files:
            try:
                stat = os.stat(f)
                size = stat.st_size
                mtime = stat.st_mtime
            except Exception:
                # File might be locked or temporarily unreadable
                continue

            if f not in self.file_states:
                # First time seeing this file
                self.file_states[f] = {
                    "size": size,
                    "mtime": mtime,
                    "last_changed": now,
                    "stable": False
                }
            else:
                state = self.file_states[f]
                # If size or modify time has changed, update state and reset timer
                if state["size"] != size or state["mtime"] != mtime:
                    state["size"] = size
                    state["mtime"] = mtime
                    state["last_changed"] = now
                    state["stable"] = False
                elif not state["stable"]:
                    # File has not changed since last check. Check if debounce duration has elapsed
                    if now - state["last_changed"] >= self.debounce_seconds:
                        state["stable"] = True
                        stabilized_files.append(f)

        return stabilized_files

    def copy_to_scratch(self, file_path, sku):
        """Copies a stabilized file to the local isolated scratch directory."""
        if not sku:
            return None
            
        sku_scratch_dir = os.path.join(SCRATCH_ACTIVE_DIR, sku)
        os.makedirs(sku_scratch_dir, exist_ok=True)
        
        dest_path = os.path.join(sku_scratch_dir, os.path.basename(file_path))
        
        # Use safe overwrite copy
        try:
            shutil.copy2(file_path, dest_path)
            print(f"  [Debouncer] Debounced and copied: {os.path.basename(file_path)} -> Local Scratch")
            return dest_path
        except Exception as e:
            print(f"  [Debouncer Error] Failed to copy {file_path} to scratch: {e}")
            return None

    def run_tick(self):
        """Executes a single check pass."""
        found_files = self.scan_directories()
        stabilized = self.update_states(found_files)
        
        triggered_skus = set()
        
        for f in stabilized:
            sku = self.extract_sku_and_slot(f)
            if sku:
                copied_path = self.copy_to_scratch(f, sku)
                if copied_path:
                    triggered_skus.add(sku)
                    
        return list(triggered_skus)

    def watch_forever(self, on_sku_ready_callback):
        """Runs the watch loop continuously."""
        print(f"==================================================")
        print(f"   ONEDRIVE FILE WATCHER & DEBOUNCER STARTED      ")
        print(f"   Watching dirs: ")
        print(f"     - {NEW_WHITE_BG_DIR}")
        print(f"     - {TOPAZ_DIR}")
        print(f"     - {ORIG_DIR}")
        print(f"   Debounce period: {self.debounce_seconds} seconds")
        print(f"==================================================")
        
        os.makedirs(SCRATCH_ACTIVE_DIR, exist_ok=True)
        
        try:
            while True:
                ready_skus = self.run_tick()
                for sku in ready_skus:
                    # Callback to trigger task execution
                    on_sku_ready_callback(sku)
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print("\nWatcher stopped by user.")

if __name__ == "__main__":
    # Test execution
    def test_callback(sku):
        print(f"★ [Watcher Trigger] SKU is ready for execution: {sku}")
        
    watcher = FileWatcher(check_interval_seconds=1, debounce_seconds=3)
    watcher.watch_forever(test_callback)

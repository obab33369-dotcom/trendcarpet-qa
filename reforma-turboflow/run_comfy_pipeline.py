import sys
import os

# Ensure the parent directory is in the path for package resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reforma_pipeline.orchestrator import run_pipeline

if __name__ == "__main__":
    limit_sku = None
    limit_val = None
    dry_run = "--dry-run" in sys.argv
    
    for arg in sys.argv:
        if arg.startswith("--sku="):
            limit_sku = arg.split("=")[1].strip()
        elif arg.startswith("--limit="):
            try:
                limit_val = int(arg.split("=")[1].strip())
            except ValueError:
                pass
                
    run_pipeline(limit_sku=limit_sku, limit_val=limit_val, dry_run=dry_run)

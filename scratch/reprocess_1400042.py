import sys
import os

# Add reforma-turboflow directory to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
turboflow_dir = os.path.join(project_dir, "reforma-turboflow")
sys.path.insert(0, turboflow_dir)

from reforma_pipeline.orchestrator import run_pipeline

if __name__ == "__main__":
    print("Running pipeline for SKU 1400042...")
    run_pipeline(limit_sku="1400042", dry_run=False)
    print("Done reprocessing.")

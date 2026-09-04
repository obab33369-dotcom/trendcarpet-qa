import sys
import os

# Ensure the parent directory is in the path for package resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reforma_pipeline.orchestrator import run_pipeline

if __name__ == "__main__":
    target_skus = ["1200180", "T8044-white", "97828", "1311-L-S", "LINK-SM11-light"]

    print("Starting pipeline run for target SKUs...")
    for sku in target_skus:
        print(f"\n==================================================")
        print(f"Processing target SKU: {sku}")
        print(f"==================================================")
        try:
            run_pipeline(limit_sku=sku, dry_run=False)
        except Exception as e:
            print(f"Error processing SKU {sku}: {e}")

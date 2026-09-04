import sys
import os

# Ensure the parent directory is in the path for package resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reforma_pipeline.orchestrator import run_pipeline

if __name__ == "__main__":
    target_skus = ["37281105", "80777", "advent-star-white-10", "advent-star-white-2", "19798-grey"]

    print("Starting pipeline run for next batch of SKUs...")
    for sku in target_skus:
        print(f"\n==================================================")
        print(f"Processing SKU: {sku}")
        print(f"==================================================")
        try:
            run_pipeline(limit_sku=sku, dry_run=False)
        except Exception as e:
            print(f"Error processing SKU {sku}: {e}")

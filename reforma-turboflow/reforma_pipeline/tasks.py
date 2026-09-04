import os
import threading
from reforma_pipeline.config import REDIS_URL, USE_CELERY

# GPU VRAM Lock to prevent parallel GPU processes from causing CUDA OOM
gpu_lock = threading.Lock()

celery_app = None
if USE_CELERY:
    try:
        from celery import Celery
        celery_app = Celery("reforma_tasks", broker=REDIS_URL, backend=REDIS_URL)
        # Configure Celery (e.g. serialize tasks with json)
        celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='Europe/Stockholm',
            enable_utc=True,
        )
        print(f"[Queue Manager] Celery initialized with broker: {REDIS_URL}")
    except ImportError:
        print("[WARNING] Celery not installed. Falling back to local eager mode.")
        USE_CELERY = False

# Import modular orchestration components
# (These will be refactored and exposed in orchestrator.py)
try:
    from reforma_pipeline.orchestrator import (
        curate_sku,
        segment_sku_gpu,
        compose_sku_cpu
    )
except ImportError:
    # Pre-declare references for linting and dynamic imports during loading
    curate_sku = None
    segment_sku_gpu = None
    compose_sku_cpu = None

def run_sku_pipeline_eager(sku):
    """Runs the full SKU pipeline synchronously and locally (eager fallback)."""
    print(f"★ [Local Eager Mode] Running pipeline for SKU: {sku}")
    
    # Import locally to avoid circular dependencies if any
    from reforma_pipeline.orchestrator import curate_sku, segment_sku_gpu, compose_sku_cpu
    
    # Step 1: Curation
    curated_data = curate_sku(sku)
    if not curated_data:
        print(f"  [Local Eager Mode] Curation returned no data for SKU {sku}. Skipping.")
        return
        
    # Step 2: GPU-bound Segmentation (with GPU Lock Guardrail)
    print(f"  [Local Eager Mode] Acquiring GPU VRAM Lock...")
    with gpu_lock:
        segment_sku_gpu(sku, curated_data)
    print(f"  [Local Eager Mode] Released GPU VRAM Lock.")
    
    # Step 3: CPU-bound Composition & QA
    compose_sku_cpu(sku, curated_data)
    print(f"★ [Local Eager Mode] SKU {sku} completed successfully!")

if celery_app:
    @celery_app.task(name="reforma_pipeline.tasks.curate_sku_task")
    def curate_sku_task(sku):
        from reforma_pipeline.orchestrator import curate_sku
        curated_data = curate_sku(sku)
        if curated_data:
            segment_sku_gpu_task.delay(sku, curated_data)
        return sku

    @celery_app.task(name="reforma_pipeline.tasks.segment_sku_gpu_task")
    def segment_sku_gpu_task(sku, curated_data):
        from reforma_pipeline.orchestrator import segment_sku_gpu
        # Sequential VRAM Guard: run sequentially on the worker
        with gpu_lock:
            segment_sku_gpu(sku, curated_data)
        compose_sku_cpu_task.delay(sku, curated_data)
        return sku

    @celery_app.task(name="reforma_pipeline.tasks.compose_sku_cpu_task")
    def compose_sku_cpu_task(sku, curated_data):
        from reforma_pipeline.orchestrator import compose_sku_cpu
        compose_sku_cpu(sku, curated_data)
        return sku
else:
    # Fallback to local execution when Celery is not running
    def curate_sku_task(sku):
        run_sku_pipeline_eager(sku)
        return sku


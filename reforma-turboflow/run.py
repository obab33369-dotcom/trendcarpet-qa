import os
import sys
import subprocess

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_step(command: list) -> bool:
    print(f"\n🚀 Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            [sys.executable] + command,
            check=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing step: {e}")
        return False

def main():
    print("====================================================")
    print("      REFORMA AUTOMATION: TURBOFLOW STUDIO 2026     ")
    print("====================================================")
    
    # Check arguments
    mode = "--test"
    if "--full" in sys.argv:
        mode = "--full"
        
    limit_arg = None
    for arg in sys.argv:
        if arg.startswith("--limit="):
            limit_arg = arg
        
    print(f"Selected Mode: {mode.upper()}")
    if limit_arg:
        print(f"Limit Configured: {limit_arg}")
    
    # 1. Run Analyzer
    print("\n--- STEP 1: Starting Gemini Direct Visual Extractor ---")
    analyzer_command = ["analyzer.py"]
    if mode == "--full":
        analyzer_command.append("--full")
    if limit_arg:
        analyzer_command.append(limit_arg)
        
    success = run_step(analyzer_command)
    if not success:
        print("❌ Step 1 failed. Aborting pipeline.")
        sys.exit(1)
        
    # 2. Run Matcher & Exporter
    print("\n--- STEP 2: Running Scandinavian Design Pairing Engine ---")
    success = run_step(["engine.py"])
    if not success:
        print("❌ Step 2 failed. Aborting pipeline.")
        sys.exit(1)
        
    # 3. Run ComfyUI Cutout & Shadow Pipeline
    print("\n--- STEP 3: Running ComfyUI Cognitive Cutout & Shadow Pipeline ---")
    comfy_command = ["run_comfy_pipeline.py"]
    if mode == "--test":
        comfy_command.append("--dry-run")
    if limit_arg:
        comfy_command.append(limit_arg)
    success = run_step(comfy_command)
    if not success:
        print("❌ Step 3 failed. Aborting pipeline.")
        sys.exit(1)
        
    print("\n====================================================")
    print("🎉 SUCCESS: Pipeline completed successfully!")
    print("Your matched rooms are exported in:")
    print("  -> JSON format: rooms_turboflow.json")
    print("  -> TurboFlow Standard CSV: turboflow_ready.csv")
    print("====================================================")

if __name__ == "__main__":
    main()

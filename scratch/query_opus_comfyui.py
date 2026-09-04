import subprocess
import sys
import os

def main():
    # Configure stdout/stderr for UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    prompt = """Today's date is June 15, 2026.
We are designing a collaborative software factory / agentic developer loop for our project REFORMA.
We have a question regarding using ComfyUI to resolve our issues with furniture segmentation and shadow generation with SAM (Segment Anything) 3.0/3.1.

We are considering a headless API integration where our local Python-loop (running in loop.py/app.py) sends images to ComfyUI via its WebSocket/REST API, runs an optimized workflow (e.g., SAM + BirefNet + Mask Refiner + IC-Light for shadows), and receives the processed image back.

Please provide your architectural and technical assessment of this approach:
1. System Resources & Concurrency: How do we best manage running ComfyUI locally, which is GPU VRAM intensive, so it does not conflict with our other local or Gemini processes? Should we run ComfyUI as a separate local microservice with a queue mechanism in our SQLite database?
2. Pipeline Design: What node combination do you recommend in ComfyUI to achieve the best results for furniture (e.g., clean borders around chair legs/armrests) and to preserve or generate realistic floor shadows?
3. Error Handling (Fallback): If the ComfyUI service hangs, runs out of GPU memory, or crashes during a batch run, how should our FastAPI/Orchestrator loop handle this? What kind of fallback should we have?
4. Workflow Management: How do we best save and version-control the ComfyUI workflows (API JSON files) in our Git repository so that our Python code can easily update or switch workflows programmatically?
"""

    # Build the command using absolute path to native binary
    native_path = os.path.expanduser(r"~\.local\bin\claude.exe")
    if not os.path.exists(native_path):
        print("Error: claude.exe not found.")
        sys.exit(1)

    cmd = [
        native_path,
        "--print",
        "--model", "opus",
        "--permission-mode", "plan",
        "--tools", "Read"
    ]

    print("Sending ComfyUI inquiry to Claude Opus...")
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]

    res = subprocess.run(
        cmd,
        input=prompt,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='ignore',
        env=env,
        shell=(sys.platform == 'win32')
    )

    if res.returncode == 0:
        print("\n=== CLAUDE OPUS COMFYUI ARCHITECTURAL RESPONSE ===")
        print(res.stdout)
    else:
        print(f"\nError: Claude CLI exited with code {res.returncode}")
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()

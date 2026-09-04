import os
import subprocess
import sys

# Configure stdout/stderr for UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Remove the environment key
if 'ANTHROPIC_API_KEY' in os.environ:
    del os.environ['ANTHROPIC_API_KEY']

# Read the architecture document
arch_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\reforma_pipeline_architecture.md"
with open(arch_path, 'r', encoding='utf-8') as f:
    arch_content = f.read()

# Prepare prompt
prompt = f"""
We are designing the modular image processing pipeline for REFORMA.
Here is the proposed modular system architecture:
{arch_content}

We recently implemented the following changes in 'orchestrator.py' to resolve non-square outputs for studio views:
1. In Stage 1 curation, we disabled border-touch zoom heuristics for Slot 1 and raw original/Topaz folders (which naturally touch borders) so they route to Route 2 (Studio cleaning & scaling) instead of bypassing it.
2. In post-processing, if a studio/white-background view goes to Route 1 (either directly as a zoom/detail view, or as a fallback from QA failure), we now automatically pad the resized image centered on a pure white 2000x2000 square canvas.
3. Added a Stage 4 Audit validation loop at the end of the pipeline that opens all generated studio zoom images, verifies they are square (2000x2000), and halts the batch runner if any non-square studio images are detected.

As Fable 5, the high-reasoning model, we want you to review this architecture and make final decisions on guidelines, limits, and safety measures. Specifically:
1. **Race & Deadlock Analysis**: In this multi-stage decoupled pipeline, are there any potential concurrency locks or race conditions (e.g. Stage 2 writing to the BBox DB while Stage 3 CPU workers read it)?
2. **Loop Stability & QA Failure Fallbacks**: When a studio view fails QA, we currently fall back to Route 1 (which now pads the raw image to 2000x2000 square). Is this the safest fallback behavior, or should we flag these SKUs for manual intervention or run a local color-thresholding fallback instead of SAM3?
3. **Pasting / Alignment Offsets**: Does our centering math properly handle products that have asymmetric shadows, or is there a better way to center the visual bounding box while preserving the shadow's natural placement?
4. **Scale Factors Sharing**: We cache the scale factor of Slot 1 and reuse it for slots 2-6 to ensure a consistent size across all product views. Does this lead to any edge cases (e.g. if Slot 1 has a very narrow product and Slot 2 has a very wide one)?

Please provide your expert reasoning and recommendations.
"""

native_path = os.path.expanduser(r"~\.local\bin\claude.exe")
if not os.path.exists(native_path):
    print("Error: claude.exe not found.")
    sys.exit(1)

cmd = [
    native_path,
    "--print",
    "--model", "fable",
    "--permission-mode", "plan",
    "--tools", "Read"
]

print("Sending architecture specification to Claude Fable 5...")
env = os.environ.copy()
if "ANTHROPIC_API_KEY" in env:
    del env["ANTHROPIC_API_KEY"]
env["CLAUDE_CODE_EFFORT_LEVEL"] = "max"

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

# Write response to a text file for persistent review
output_file = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\fable5_architecture_review.md"
with open(output_file, 'w', encoding='utf-8') as out:
    out.write("# Claude Fable 5 Architecture Review\n\n")
    out.write(res.stdout)

print("\n=== CLAUDE FABLE 5 RESPONSE ===")
print(res.stdout)
if res.stderr:
    print("\n--- STDERR ---")
    print(res.stderr)

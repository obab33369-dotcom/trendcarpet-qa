import os
import subprocess
import sys

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Remove the environment key
if 'ANTHROPIC_API_KEY' in os.environ:
    del os.environ['ANTHROPIC_API_KEY']

# Read the architecture document
arch_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\reforma_pipeline_architecture.md"
with open(arch_path, 'r', encoding='utf-8') as f:
    arch_content = f.read()

# Prepare the prompt for Claude
prompt = f"""
Please perform a detailed architectural review of the REFORMA image processing pipeline.

Here is the current architectural specification:
{arch_content}

We recently implemented the following changes in 'orchestrator.py' to resolve non-square outputs for studio views:
1. In Stage 1 curation, we disabled border-touch zoom heuristics for Slot 1 and raw original/Topaz folders (which naturally touch borders) so they route to Route 2 (Studio cleaning & scaling) instead of bypassing it.
2. In post-processing, if a studio/white-background view goes to Route 1 (either directly as a zoom/detail view, or as a fallback from QA failure), we now automatically pad the resized image centered on a pure white 2000x2000 square canvas.
3. Added a Stage 4 Audit validation loop at the end of the pipeline that opens all generated studio zoom images, verifies they are square (2000x2000), and halts the batch runner if any non-square studio images are detected.

Please analyze:
- Is this staged architecture (GPU inference -> parallel CPU post-processing -> Stage 4 Audit) sound and scalable for 4,000+ images?
- Does our new padding logic in Route 1 / QA fallback robustly solve the non-square studio output issue?
- Do you see any bottlenecks, concurrency lockups, or edge cases in this design?
- Provide concrete recommendations or improvements.
"""

print("Sending architecture specification to Claude CLI for review...")
res = subprocess.run(
    ["claude", "-p", prompt],
    capture_output=True,
    text=True,
    encoding='utf-8'
)

# Write response to a text file for persistent review
output_file = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\claude_real_review.md"
with open(output_file, 'w', encoding='utf-8') as out:
    out.write("# Claude Real Architectural Review\n\n")
    out.write(res.stdout)

print("\n--- Response from Claude CLI ---")
print(res.stdout)
if res.stderr:
    print("\n--- STDERR ---")
    print(res.stderr)

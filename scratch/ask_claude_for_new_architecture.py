import os
import subprocess
import sys

def main():
    # Configure stdout/stderr for UTF-8 to prevent encoding issues on Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    # Output paths
    output_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\6932563d-9c3c-4234-9602-e39737c303fa\claude_architecture_response.md"

    # Prompt design for Claude Opus 4.8 (Lead Architect)
    prompt = """Today's date is June 17, 2026.
We need a new architecture and code to solve the core quality issues in our Reforma Image Pipeline (TurboFlow).
You are acting as our Lead Architect.

=========================================
IMPORTANT MODEL ALIAS INFORMATION
=========================================
In the source code of this project (e.g. session_runner.py and query_opus.py), the parameter "--model" "opus" is passed to the Claude CLI.
In the project's documentation and comments, this model is consistently referred to as Claude Opus 4.8 (or Opus 4.8).
By using the --model opus flag, we are calling you, the model referred to in this project as Claude Opus 4.8.

=========================================
REFORMA IMAGE PIPELINE (TURBOFLOW) - CURRENT SYSTEM & ISSUES
=========================================
Our image pipeline automates processing of product images for Reforma to meet a premium e-commerce standard.

Three Original Folders & Image Sources:
1. reforma_original_images_by_product: Original/fallback. Varied ratios, no shadows generally, varied slots.
2. TEST TOPAZ: Up-scaled via Topaz AI. Off-white/gray background, no shadows, varied slots.
3. Refoma white background fix: High-res fix images. Includes studio images on white background with preserved soft natural shadows (often ending in -W.jpg).

Image Categories:
- Studiobild (Hero) [Slot 1-4]: Furniture centered on white canvas. Must be square (2000x2000px).
- Närbild / Detaljbild (Zoom) [Slot 8 & 10]: Close-up. Must NOT be cropped or padded; kept rektangulär (e.g. 1333x2000px).
- Miljöbild / Livsstilsbild [Slot 5-7]: Style rooms. Copied entirely raw without changes.
- Måttskiss / Ritning: Blueprints. Copied without cropping; padded to square if background is already white.

IDENTIFIED PROBLEMS TO SOLVE:

A. Shadow Destruction (Förstörda originalskuggor):
- The pipeline used ACSS to separate furniture from shadow using a mask, discarded the shadow, and attempted to recreate a digital shadow with a luma mask and a feathering ramp.
- This destroyed the high-quality soft natural shadows retouched in the white background fix folder, causing them to be cut off, pixelated, or unnatural.
- Proposed Fix: Bypassing ACSS shadow masking via FORCE_ORIGINAL = "1". Keep the entire cropped area (including furniture + natural shadow) as a single solid layer, and disable edge-fading/feathering so the shadow bleeds naturally to the edges.

B. Off-Center Alignment (Felaktig centrering):
- Centering calculation included the width of the shadow (e.g. if a shadow extends to the right on the floor).
- This pushed the actual furniture off-center (to the left) on the square canvas.
- Proposed Fix: Visual Body-Centric Centering. Calculate the center based strictly on the SAM3 body bounding box (the furniture's physical structure, seats/backs) ignoring the shadow's extent.

C. Zoom Padding Seams (Vita kanter runt närbilder):
- Zoom/close-up views with gray studio backgrounds were classified as studio views and forced onto a square white canvas (padding). This created sharp seams between the gray background and the white canvas.
- Proposed Fix: Zoom View Padding Invalidation. Completely disable canvas padding for zoom views (is_zoom_view). Keep their natural rektangulär format (e.g. 1333x2000px) so the background is continuous.

=========================================
ARCHITECTURAL QUESTIONS & IMPLEMENTATION PLAN
=========================================
Please review these problems and provide:
1. A new, robust architectural design to handle these fixes gracefully within the pipeline.
2. Concrete code modifications (specifically targeting composition.py and orchestrator.py) to implement:
   - FORCE_ORIGINAL bypassing.
   - True body-centric visual horizontal/vertical centering (ignoring shadows).
   - Zoom-view bypass of white canvas padding.
3. Guidelines to ensure these changes do not break scalability, do not cause CUDA OOM (using RT3000 Ada with 8GB VRAM), and are stable under Windows 11.
"""

    # Locate claude.exe binary
    native_path = os.path.expanduser(r"~\.local\bin\claude.exe")
    if not os.path.exists(native_path):
        native_path = "claude" # fallback to PATH

    cmd = [
        native_path,
        "--print",
        "--model", "opus",
        "--permission-mode", "dontAsk",
        "--tools", "Read,Grep,Glob"
    ]

    print("Preparing command to run Claude CLI directly with --model opus...")
    env = os.environ.copy()
    env["CLAUDE_CODE_EFFORT_LEVEL"] = "max"
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]

    print("To execute this query to Claude Opus 4.8, run:")
    print("python scratch/ask_claude_for_new_architecture.py --run")
    print()

    # Only run if '--run' parameter is supplied
    if "--run" in sys.argv:
        print("Executing Claude CLI query...")
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
            print("\n=== CLAUDE OPUS RESPONSE ===")
            print(res.stdout)
            
            # Save response to brain folder
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(res.stdout)
            print(f"\nResponse successfully saved to: {output_path}")
            sys.exit(0)
        else:
            print(f"Error: Claude CLI exited with code {res.returncode}")
            if res.stdout:
                print("STDOUT:")
                print(res.stdout)
            if res.stderr:
                print("STDERR:")
                print(res.stderr)
            sys.exit(res.returncode)
    else:
        print("Script prepared. Run with '--run' flag to execute.")

if __name__ == "__main__":
    main()

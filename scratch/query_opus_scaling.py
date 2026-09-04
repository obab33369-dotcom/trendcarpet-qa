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
We are designing the ComfyUI background removal and shadow generation pipeline for our project REFORMA.
We need your architectural guidance on three key aspects of this pipeline:

1. Self-Review Triage (AI Feedback Loop):
   - To check if ComfyUI's background removal is clean and did not cut off parts of the product (e.g. thin chair legs), we want to use Gemini Vision API.
   - To make this check accurate, should we send the original image and the processed cutout side-by-side (or in the same payload) as reference, and what prompt instructions are best for comparing them?
   - How can we structure the parameter adjustment (e.g., threshold, blur, matting settings) if Gemini flags a failure?

2. Sizing & Scaling Consistency Across Perspectives (oblique/side vs front views):
   - We must maintain visual consistency for a single product SKU. If we hardcode a target width (e.g., a sofa must occupy 94% of the canvas width), then a side-view (oblique) photo will be scaled up massively compared to a front-facing photo, causing severe scaling distortion.
   - How can we mathematically or geometrically calculate a uniform scaling factor based on the main image (Slot 1) and apply it consistently to secondary images (Slots 2, 3, etc.) of the same product?
   - How do we handle uniform height/scale across product categories under this perspective-safe model?

3. Lifestyle vs Studio Image Separation:
   - We want to ensure that lifestyle/interior images (products shown in a decorated room) are kept completely untouched (no cutouts, no cropping), while studio images (on a white background) are processed with ComfyUI.
   - What is the most robust way to classify lifestyle vs studio images in our loop? Should we use a fast color histogram/luminance variance analysis, or let Gemini classify them?

Please provide your technical assessment, formulas/logic, and recommendations.
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

    print("Sending Scaling & Triage inquiry to Claude Opus...")
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
        print("\n=== CLAUDE OPUS SCALING & TRIAGE RESPONSE ===")
        print(res.stdout)
    else:
        print(f"\nError: Claude CLI exited with code {res.returncode}")
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()

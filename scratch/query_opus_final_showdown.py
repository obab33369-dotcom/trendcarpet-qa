import os
import subprocess
import sys

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    fable_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\fable5_extracted_design_review.md"
    opus_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\claude_fable5_assessment_opus.md"
    output_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\claude_final_specification_opus.md"

    if not os.path.exists(fable_path) or not os.path.exists(opus_path):
        print("Error: Required input files not found.")
        sys.exit(1)

    print("Reading Proposal 1 (Fable 5)...")
    with open(fable_path, 'r', encoding='utf-8') as f:
        proposal1 = f.read()

    print("Reading Proposal 2 (First Opus 4.8 response)...")
    with open(opus_path, 'r', encoding='utf-8') as f:
        proposal2 = f.read()

    prompt = f"""Today is June 16, 2026 (260616).
We want to resolve the final architecture for the REFORMA Developer Loop (Antigravity 2.0) using Claude Opus 4.8 at max reasoning capacity.

We have two different proposals:
- Proposal 1: The original Fable 5 design structure.
- Proposal 2: The initial Claude Opus 4.8 response that reviewed and refined it.

Below are the contents of both proposals.
================================================================================
PROPOSAL 1 (FABLE 5 ORIGINAL DESIGN):
{proposal1}
================================================================================
PROPOSAL 2 (CLAUDE OPUS 4.8 RESPONSE):
{proposal2}
================================================================================

Please act as our Lead Architect. Evaluate both proposals at absolute MAX effort/reasoning capacity:
1. Do you agree that Proposal 2 is more advanced and forward-looking than Proposal 1? Provide a detailed comparison.
2. Make the final technical decisions yourself. Optimize for speed of implementation and execution while avoiding unnecessary security risks on Windows. Do not ask the user for technical input — make the executive architect decisions now.
3. Write a single, complete, copy-pasteable markdown specification for `CLAUDE.md`. It must contain:
   - The final loop architecture (state machine, worktree-pinning, and merge process).
   - The security boundary specifications (the process split and bearer auth).
   - The offline verification command spec (how we will run offline tests in this repo).
   - The concrete code file changes required, step-by-step.
   - The phased roadmap for the coder to execute.
"""

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

    print("Sending showdown query to Claude CLI (model: opus) at MAX effort...")
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

    if res.returncode == 0:
        print("\n=== CLAUDE OPUS RESPONSE SUCCESSFULLY RECEIVED ===")
        with open(output_path, 'w', encoding='utf-8') as out:
            out.write("# Claude Opus 4.8 Lead Architect Final Spec\n\n")
            out.write(res.stdout)
        print(f"Saved final spec to {output_path}")
        print("\n--- Summary of Response ---")
        lines = res.stdout.split('\n')
        for line in lines[:100]:
            print(line)
        if len(lines) > 100:
            print("... (truncated for terminal output) ...")
    else:
        print(f"\nError: Claude CLI exited with code {res.returncode}")
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()

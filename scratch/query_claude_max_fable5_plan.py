import os
import subprocess
import sys

def main():
    # Configure stdout and stderr to use UTF-8 to prevent charmap encoding errors on Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    # Paths
    fable_plan_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\fable5_extracted_design_review.md"
    output_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\claude_fable5_assessment.md"

    if not os.path.exists(fable_plan_path):
        print(f"Error: Fable 5 plan not found at {fable_plan_path}")
        sys.exit(1)

    print(f"Reading Fable 5 plan from {fable_plan_path}...")
    with open(fable_plan_path, 'r', encoding='utf-8') as f:
        fable_plan_content = f.read()

    prompt = f"""Today is June 16, 2026.
We want to perform a deep architectural review of the Fable 5 developer loop design plan and assess the feasibility of implementing it in our system (which we refer to as Antigravity 2.0).

Here is the extracted Fable 5 design review and plan for the collaborative developer loop:
================================================================================
{fable_plan_content}
================================================================================

Please act as our Lead Architect. Evaluate this at the absolute MAX effort/reasoning capacity.
1. Is it possible to implement this entire developer loop (worktree-pinned apply, serialized merge queue, async tests, TTL leases, circuit breakers, hybrid sessions, attempts journal, and path validation) in our current local environment (Windows)?
2. What are the key architectural challenges, risks, or modifications needed for this implementation?
3. What design choices do you recommend or want to refine?
4. Do you have any other concerns or questions regarding this plan?
5. How should we partition the tasks between us (you as the Architect, me as the Coder) to build this out step-by-step?
"""

    # Build the command using absolute path to native binary
    native_path = os.path.expanduser(r"~\.local\bin\claude.exe")
    if not os.path.exists(native_path):
        print("Error: claude.exe not found.")
        sys.exit(1)

    cmd = [
        native_path,
        "--print",
        "--permission-mode", "plan",
        "--tools", "Read"
    ]

    print("Sending Fable 5 plan to Claude CLI at MAX effort...")
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]
    
    # Configure MAX effort level for Claude CLI
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
        print("\n=== CLAUDE RESPONSE SUCCESSFULLY RECEIVED ===")
        # Write to the destination file
        with open(output_path, 'w', encoding='utf-8') as out:
            out.write("# Claude Lead Architect Fable 5 Assessment\n\n")
            out.write(res.stdout)
        print(f"Saved assessment to {output_path}")
        print("\n--- Summary of Response ---")
        lines = res.stdout.split('\n')
        # Print the first 100 lines of output for verification
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

import subprocess
import sys
import os

def main():
    # Configure stdout and stderr to use UTF-8 to prevent charmap encoding errors on Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    prompt = """Today's date is June 12, 2026.
We are designing a collaborative software factory / agentic developer loop for our project REFORMA.
Here is our setup:
1. Antigravity 2.0 (Gemini) is the main AI assistant. It has a massive token pool (via a Google One AI Ultra subscription) and full access to workspace tools (reading/writing files, running terminal commands, managing subagents, executing background processes). It does the heavy lifting, code generation, script execution, and runs a local FastAPI control panel + folder-monitoring Orchestrator loop.
2. Claude Code CLI (installed locally, authenticated under our Cama Gruppen Team subscription) is available. It has advanced reasoning and iterative agentic capabilities. We want to use it for high-level architecture decisions, complex debugging, and refactoring strategies.
3. The User (Andronik) coordinates the work.

We want to build a "Control-Plane and Worker" pattern where Antigravity manages the workspace, file generation, and tests, but can invoke/query Claude Code programmatically to solve complex architectural or debugging problems.

Please address the following questions:
1. What is the optimal architecture and workflow for this three-way collaboration (Antigravity 2.0 + Claude Code + User)? How can we pass context between Antigravity and Claude Code efficiently?
2. How should we configure Claude Code's local settings (such as local MCP servers, CLAUDE.md files, or plugins) to maximize its integration with this workspace?
3. How should we configure Antigravity itself (e.g. system prompts, custom subagents, orchestrator hooks) to interact cleanly with Claude Code?
4. Today is June 12, 2026. Given the criticality of this developer loop architecture to our entire project, should we involve Fable 5 (high-reasoning model) to review this design? If so, what specific questions should we ask it?
5. Please ask us any clarifying questions or provide recommendations for our next steps.
"""

    # Build the command using absolute path to native binary
    native_path = os.path.expanduser(r"~\.local\bin\claude.exe")
    if not os.path.exists(native_path):
        print("Error: claude.exe not found at default location.")
        sys.exit(1)

    cmd = [
        native_path,
        "--print",
        "--model", "opus",
        "--permission-mode", "plan",
        "--tools", "Read"
    ]

    print("Sending request to Claude Opus...")
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
        print("\n=== CLAUDE OPUS RESPONSE ===")
        print(res.stdout)
    else:
        print(f"\nError: Claude CLI exited with code {res.returncode}")
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()

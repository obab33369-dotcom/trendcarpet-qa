import os
import subprocess
import sys

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]

    print("Running 'claude --help' to see model parameters...")
    res = subprocess.run(
        ["claude", "--help"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        env=env,
        shell=(sys.platform == 'win32')
    )
    print("STDOUT:")
    print(res.stdout)
    print("STDERR:")
    print(res.stderr)

if __name__ == "__main__":
    main()

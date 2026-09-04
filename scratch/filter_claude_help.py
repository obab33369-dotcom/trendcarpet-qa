import os
import subprocess
import sys

def main():
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]

    res = subprocess.run(
        ["claude", "--help"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        env=env,
        shell=(sys.platform == 'win32')
    )
    for line in res.stdout.split('\n'):
        if "model" in line.lower() or "fable" in line.lower() or "opus" in line.lower() or "sonnet" in line.lower():
            print(line)

if __name__ == "__main__":
    main()

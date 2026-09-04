import os
import subprocess
import sys

# Remove the key from the environment
if 'ANTHROPIC_API_KEY' in os.environ:
    del os.environ['ANTHROPIC_API_KEY']

print("--- Checking Claude Auth Status (without environment key) ---")
res_status = subprocess.run(
    ["claude", "auth", "status"],
    capture_output=True,
    text=True,
    encoding='utf-8'
)
print("STDOUT:")
print(res_status.stdout)
print("STDERR:")
print(res_status.stderr)

print("\n--- Running Test Prompt to Claude CLI (without environment key) ---")
res_prompt = subprocess.run(
    ["claude", "-p", "Hi! Respond with a single short sentence confirming you are Claude."],
    capture_output=True,
    text=True,
    encoding='utf-8'
)
print("STDOUT:")
print(res_prompt.stdout)
print("STDERR:")
print(res_prompt.stderr)

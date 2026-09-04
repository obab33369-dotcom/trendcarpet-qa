import os

env_path = os.path.expanduser(r"~\.env")

if os.path.exists(env_path):
    print(f"\n=================== .env File: {env_path} ===================")
    with open(env_path, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print(f".env file not found at: {env_path}")

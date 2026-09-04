import subprocess
import threading
import time
import os
import sys
import re
import json
import hatshop_server

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 8092
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_EXE = os.path.join(WORKSPACE_DIR, "cloudflared.exe")
VERCEL_JSON = os.path.join(WORKSPACE_DIR, "vercel.json")
LINK_FILE = os.path.join(WORKSPACE_DIR, "PUBLIC_LINK.txt")

PERMANENT_VERCEL_URL = "https://trendcarpet-qa.vercel.app"

def run_server():
    hatshop_server.start_server(PORT)

def update_vercel_config(new_tunnel_url):
    try:
        current_dest = None
        if os.path.exists(VERCEL_JSON):
            with open(VERCEL_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                rewrites = data.get("rewrites", []) or data.get("redirects", [])
                if rewrites:
                    current_dest = rewrites[0].get("destination", "")

        expected_dest = f"{new_tunnel_url}/$1"
        if current_dest == expected_dest:
            print("[*] Vercel-bryggan pekar redan pa ratt tunneladress.")
            return

        print(f"[*] Uppdaterar Vercel-bryggan till: {new_tunnel_url}...")
        config = {
            "name": "trendcarpet-qa",
            "cleanUrls": True,
            "rewrites": [
                {
                    "source": "/(.*)",
                    "destination": expected_dest
                }
            ]
        }
        with open(VERCEL_JSON, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        def push_git():
            try:
                subprocess.run(["git", "add", "vercel.json"], cwd=WORKSPACE_DIR, capture_output=True)
                subprocess.run(["git", "commit", "-m", f"Update tunnel destination: {new_tunnel_url}"], cwd=WORKSPACE_DIR, capture_output=True)
                res = subprocess.run(["git", "push", "origin", "main"], cwd=WORKSPACE_DIR, capture_output=True, text=True)
                if res.returncode == 0:
                    print("[✓] Vercel-bryggan synkad via GitHub (aktiv om ~10 sekunder).")
                else:
                    print("[!] Kunde inte pusha till GitHub:", res.stderr.strip())
            except Exception as e:
                print("[!] Fel vid git-synk:", e)

        threading.Thread(target=push_git, daemon=True).start()
    except Exception as e:
        print("[!] Fel vid uppdatering av vercel.json:", e)

def main():
    print("==================================================================")
    print(" QA FOTO- & RETUSCH-HUBB (PERMANENT VERCEL-LANK)")
    print("==================================================================")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1)
    print(f"[*] Lokal server kors pa: http://localhost:{PORT}")
    print(f"[*] Kontorsnatverk (Wi-Fi): http://192.168.2.33:{PORT}")

    with open(LINK_FILE, "w", encoding="utf-8") as f:
        f.write(PERMANENT_VERCEL_URL)

    print("\n" + "="*66)
    print(" FAST PERMANENT ADRESS FOR TEAMET (VERCEL):")
    print(f" >>> {PERMANENT_VERCEL_URL} <<<")
    print("="*66 + "\n")

    proc = None
    if os.path.exists(CLOUDFLARED_EXE):
        print("[*] Startar Cloudflare-tunnel (obegransad gratis bandbredd)...")
        proc = subprocess.Popen(
            [CLOUDFLARED_EXE, "tunnel", "--url", f"http://localhost:{PORT}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        def monitor_cloudflare(p):
            tunnel_found = False
            for line in p.stderr:
                match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if match and not tunnel_found:
                    tunnel_url = match.group(0)
                    tunnel_found = True
                    print(f"\n[✓] Cloudflare aktiv: {tunnel_url}")
                    update_vercel_config(tunnel_url)
                    print(f"[✓] Alla kollegor anvander alltid den fasta lanken: {PERMANENT_VERCEL_URL}\n")

        t = threading.Thread(target=monitor_cloudflare, args=(proc,), daemon=True)
        t.start()
    else:
        print(f"[!] cloudflared.exe hittades inte pa: {CLOUDFLARED_EXE}")

    try:
        while True:
            time.sleep(2)
            if proc and proc.poll() is not None:
                print("[!] Tunnel process avslutades, startar om automatiskt...")
                proc = subprocess.Popen(
                    [CLOUDFLARED_EXE, "tunnel", "--url", f"http://localhost:{PORT}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1
                )
                t = threading.Thread(target=monitor_cloudflare, args=(proc,), daemon=True)
                t.start()
    except KeyboardInterrupt:
        if proc:
            proc.terminate()
        print("\nStanger ner Photo Review Hub...")

if __name__ == "__main__":
    main()

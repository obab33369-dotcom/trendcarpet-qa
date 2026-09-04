import subprocess
import threading
import time
import os
import sys
import webbrowser
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
NGROK_EXE = r"C:\Users\AndronikLindgren\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
LINK_FILE = os.path.join(WORKSPACE_DIR, "PUBLIC_LINK.txt")

# 100% PERMANENT STATIC NGROK DOMAIN (NEVER CHANGES)
STATIC_DOMAIN = "runaround-goldfish-exemplify.ngrok-free.dev"
PERMANENT_URL = f"https://{STATIC_DOMAIN}"

def run_server():
    hatshop_server.start_server(PORT)

def main():
    print("==================================================================")
    print(" QA FOTO- & RETUSCH-HUBB (PERMANENT STATISK DOMAN)")
    print("==================================================================")

    # 1. Start Python HTTP server in thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1)
    print(f"[*] Lokal server kors pa: http://localhost:{PORT}")
    print(f"[*] Kontorsnatverk (Wi-Fi): http://192.168.2.33:{PORT}")

    # Write permanent static link to file
    with open(LINK_FILE, "w", encoding="utf-8") as f:
        f.write(PERMANENT_URL)

    print("\n" + "="*66)
    print(" FAST PERMANENT ADRESS FOR TEAMET & MICROSOFT TEAMS:")
    print(f" >>> {PERMANENT_URL} <<<")
    print("="*66 + "\n")

    # 2. Start ngrok daemon with permanent static domain
    proc = None
    if os.path.exists(NGROK_EXE):
        print(f"[*] Startar ngrok med fast doman: {STATIC_DOMAIN}...")
        proc = subprocess.Popen(
            [NGROK_EXE, "http", str(PORT), f"--url={STATIC_DOMAIN}", "--log=stdout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        def monitor_ngrok():
            for line in proc.stdout:
                if "client session established" in line or "tunnel session started" in line:
                    print(f"[*] Tunnel aktiv pa: {PERMANENT_URL}")

        t = threading.Thread(target=monitor_ngrok, daemon=True)
        t.start()
    else:
        print(f"[!] ngrok.exe hittades inte pa: {NGROK_EXE}")

    # Keep main process alive forever
    try:
        while True:
            time.sleep(2)
            if proc and proc.poll() is not None:
                print("[!] Tunnel process avslutades, startar om automatiskt...")
                proc = subprocess.Popen(
                    [NGROK_EXE, "http", str(PORT), f"--url={STATIC_DOMAIN}", "--log=stdout"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1
                )
    except KeyboardInterrupt:
        if proc:
            proc.terminate()
        print("\nStanger ner Photo Review Hub...")

if __name__ == "__main__":
    main()

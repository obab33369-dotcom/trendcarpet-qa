import http.server
import socketserver
import os
import json
import urllib.parse
import sys

PORT = 8088
CURRENT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors"

class RugComparisonHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=CURRENT_DIR, **kwargs)
        
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path in ["/", "/index.html"]:
            filepath = os.path.join(CURRENT_DIR, "index.html")
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
            
        elif path == "/api/carpets":
            json_path = os.path.join(CURRENT_DIR, "carpets_studio_metadata.json")
            if os.path.exists(json_path):
                with open(json_path, "rb") as f:
                    content = f.read()
            else:
                content = b"[]"
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
            
        else:
            return super().do_GET()

def start_server():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer(("", PORT), RugComparisonHandler)
    print(f"Server started on http://localhost:{PORT}", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    start_server()

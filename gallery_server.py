import http.server
import socketserver
import os
import json
import urllib.parse
import sys
import subprocess
import mimetypes

PORT = 8090
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors"
BASE_IMAGE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-08-27-Print-h-r-g-pt1-x"
METADATA_FILE = os.path.join(WORKSPACE_DIR, "pt1_gallery_metadata.json")

class GalleryHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKSPACE_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Main Web UI
        if path in ["/", "/index.html", "/gallery", "/gallery.html"]:
            html_path = os.path.join(WORKSPACE_DIR, "gallery.html")
            if os.path.exists(html_path):
                with open(html_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error(404, "gallery.html not found")
                return

        # Metadata API
        elif path == "/api/gallery":
            if os.path.exists(METADATA_FILE):
                with open(METADATA_FILE, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"{}")
                return

        # Open in Explorer API
        elif path == "/api/open-folder":
            subpath = query.get("path", [""])[0]
            full_path = os.path.normpath(os.path.join(BASE_IMAGE_DIR, subpath))
            if os.path.exists(full_path):
                if os.path.isfile(full_path):
                    subprocess.Popen(f'explorer /select,"{full_path}"')
                else:
                    subprocess.Popen(f'explorer "{full_path}"')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
                return
            else:
                self.send_error(404, "Directory or file does not exist")
                return

        # Serve Image Files from OneDrive directory
        elif path.startswith("/image/"):
            # URL unquote to handle %20, Swedish characters, etc.
            rel_path = urllib.parse.unquote(path[len("/image/"):])
            # Normalize path
            file_path = os.path.normpath(os.path.join(BASE_IMAGE_DIR, rel_path))

            # Security check: ensure path is inside BASE_IMAGE_DIR
            if not os.path.abspath(file_path).startswith(os.path.abspath(BASE_IMAGE_DIR)):
                self.send_error(403, "Access denied")
                return

            if os.path.exists(file_path) and os.path.isfile(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = "application/octet-stream"
                
                try:
                    file_size = os.path.getsize(file_path)
                    with open(file_path, "rb") as f:
                        self.send_response(200)
                        self.send_header("Content-Type", mime_type)
                        self.send_header("Content-Length", str(file_size))
                        self.send_header("Cache-Control", "public, max-age=86400")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        # Stream file in chunks
                        while True:
                            chunk = f.read(65536)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                    return
                except Exception as e:
                    self.send_error(500, f"Error reading file: {e}")
                    return
            else:
                self.send_error(404, f"Image not found: {rel_path}")
                return

        # Fallback to serving standard static files from workspace
        else:
            return super().do_GET()

def start_server(port=PORT):
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    try:
        server = socketserver.ThreadingTCPServer(("", port), GalleryHTTPRequestHandler)
    except OSError:
        # Fallback port if 8090 is in use
        port = port + 1
        server = socketserver.ThreadingTCPServer(("", port), GalleryHTTPRequestHandler)

    print(f"============================================================")
    print(f" Trendcarpet Image Gallery Server Running")
    print(f" Access URL: http://localhost:{port}")
    print(f" Image Root: {BASE_IMAGE_DIR}")
    print(f"============================================================", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    p = PORT
    if len(sys.argv) > 1:
        try:
            p = int(sys.argv[1])
        except ValueError:
            pass
    start_server(p)

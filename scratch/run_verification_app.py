import os
import sys
import json
import re
import shutil
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")
CLEAN_DIR_CARPETS = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
DISCARD_DIR_CARPETS = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")

PORT = 8500

# Setup DB mapping for actual product lookup
sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
try:
    from execute_full_catalog_sorting import resolve_anchor, load_db
    FULL_CATALOG_MAPPING = load_db("rooms_turboflow_full_catalog.json")
    print(f"Loaded {len(FULL_CATALOG_MAPPING)} prompts for product verification lookup.")
except Exception as e:
    print(f"Could not load full catalog DB: {e}")
    resolve_anchor = None
    FULL_CATALOG_MAPPING = {}

class VerificationHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # 1. Serve HTML Frontend
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
            return
            
        # 2. Serve JSON Image List
        elif path == "/api/images":
            images = self.get_discarded_images()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(images).encode("utf-8"))
            return
            
        # Serve reference images from reforma-original-images or ftp fallback
        elif path.startswith("/api/ref/"):
            sku = urllib.parse.unquote(path[9:])
            orig_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-original-images"
            ref_src_paths = [
                os.path.join(orig_dir, f"{sku}.jpg"),
                os.path.join(orig_dir, f"{sku}.png"),
                os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar", f"{sku}.jpg"),
                os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar", f"{sku}.png")
            ]
            
            ref_path = None
            for p in ref_src_paths:
                if os.path.exists(p) and os.path.isfile(p):
                    ref_path = p
                    break
                    
            if not ref_path and os.path.exists(orig_dir):
                # Fallback case-insensitive scan
                for f in os.listdir(orig_dir):
                    if sku.lower() in f.lower() and f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                        ref_path = os.path.join(orig_dir, f)
                        break
                        
            if ref_path and os.path.exists(ref_path):
                self.send_response(200)
                if ref_path.lower().endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                else:
                    self.send_header("Content-Type", "image/jpeg")
                self.end_headers()
                with open(ref_path, "rb") as f:
                    self.wfile.write(f.read())
                return
                
            self.send_error(404, "Reference photo not found")
            return
            
        # 3. Serve local images from OneDrive
        elif path.startswith("/media/"):
            rel_path = urllib.parse.unquote(path[7:])
            full_path = os.path.join(DISCARD_DIR, rel_path)
            
            if not os.path.exists(full_path):
                full_path = os.path.join(CLEAN_DIR, rel_path)
                
            if not os.path.exists(full_path):
                full_path = os.path.join(DISCARD_DIR_CARPETS, rel_path)
                
            if not os.path.exists(full_path):
                full_path = os.path.join(CLEAN_DIR_CARPETS, rel_path)
                
            if os.path.exists(full_path) and os.path.isfile(full_path):
                self.send_response(200)
                if full_path.lower().endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                else:
                    self.send_header("Content-Type", "image/jpeg")
                self.end_headers()
                with open(full_path, "rb") as f:
                    self.wfile.write(f.read())
                return
                
            self.send_error(404, "File not found")
            return
            
        self.send_error(404, "Not found")

    def do_POST(self):
        if self.path == "/api/keep":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode('utf-8'))
            
            filename = params.get("filename")
            folder = params.get("folder")
            in_reserv = params.get("in_reserv", False)
            
            success = self.move_file_back(folder, filename, in_reserv)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success}).encode("utf-8"))
            return
            
        self.send_error(404, "Not found")

    def get_discarded_images(self):
        images = []
        
        directories = [
            (DISCARD_DIR, "furniture"),
            (DISCARD_DIR_CARPETS, "carpets")
        ]
        
        for discard_path, cat in directories:
            if not os.path.exists(discard_path):
                continue
                
            folders = sorted([f for f in os.listdir(discard_path) if os.path.isdir(os.path.join(discard_path, f))])
            for folder in folders:
                folder_path = os.path.join(discard_path, folder)
                
                ref_image = None
                for item in os.listdir(folder_path):
                    if item.startswith("00_REFERENCE_") and os.path.isfile(os.path.join(folder_path, item)):
                        ref_image = item
                        break
                
                for item in os.listdir(folder_path):
                    path = os.path.join(folder_path, item)
                    if os.path.isfile(path) and not item.startswith("00_REFERENCE_") and item.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        actual_sku = None
                        actual_name = None
                        m = re.match(r"^(\d+)", item)
                        if m:
                            prefix = int(m.group(1))
                            if prefix in FULL_CATALOG_MAPPING and resolve_anchor:
                                refs = FULL_CATALOG_MAPPING[prefix]["refs"]
                                if refs:
                                    actual_sku, actual_name = resolve_anchor(refs[0])
                                    
                        images.append({
                            "filename": item,
                            "folder": folder,
                            "in_reserv": False,
                            "img_url": f"/media/{urllib.parse.quote(folder)}/{urllib.parse.quote(item)}",
                            "ref_url": f"/media/{urllib.parse.quote(folder)}/{urllib.parse.quote(ref_image)}" if ref_image else "",
                            "actual_sku": actual_sku,
                            "actual_name": actual_name,
                            "category": cat
                        })
                        
                reserv_path = os.path.join(folder_path, "reserv")
                if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
                    for item in os.listdir(reserv_path):
                        path = os.path.join(reserv_path, item)
                        if os.path.isfile(path) and not item.startswith("00_REFERENCE_") and item.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            actual_sku = None
                            actual_name = None
                            m = re.match(r"^(\d+)", item)
                            if m:
                                prefix = int(m.group(1))
                                if prefix in FULL_CATALOG_MAPPING and resolve_anchor:
                                    refs = FULL_CATALOG_MAPPING[prefix]["refs"]
                                    if refs:
                                        actual_sku, actual_name = resolve_anchor(refs[0])
                                        
                            images.append({
                                "filename": item,
                                "folder": folder,
                                "in_reserv": True,
                                "img_url": f"/media/{urllib.parse.quote(folder)}/reserv/{urllib.parse.quote(item)}",
                                "ref_url": f"/media/{urllib.parse.quote(folder)}/{urllib.parse.quote(ref_image)}" if ref_image else "",
                                "actual_sku": actual_sku,
                                "actual_name": actual_name,
                                "category": cat
                            })
        return images

    def move_file_back(self, folder, filename, in_reserv):
        if in_reserv:
            src = os.path.join(DISCARD_DIR, folder, "reserv", filename)
            curr_discard_dir = DISCARD_DIR
            curr_clean_dir = CLEAN_DIR
            if not os.path.exists(src):
                src = os.path.join(DISCARD_DIR_CARPETS, folder, "reserv", filename)
                curr_discard_dir = DISCARD_DIR_CARPETS
                curr_clean_dir = CLEAN_DIR_CARPETS
            dest_folder = os.path.join(curr_clean_dir, folder, "reserv")
        else:
            src = os.path.join(DISCARD_DIR, folder, filename)
            curr_discard_dir = DISCARD_DIR
            curr_clean_dir = CLEAN_DIR
            if not os.path.exists(src):
                src = os.path.join(DISCARD_DIR_CARPETS, folder, filename)
                curr_discard_dir = DISCARD_DIR_CARPETS
                curr_clean_dir = CLEAN_DIR_CARPETS
            dest_folder = os.path.join(curr_clean_dir, folder)
            
        dest = os.path.join(dest_folder, filename)
        
        if os.path.exists(src):
            try:
                os.makedirs(dest_folder, exist_ok=True)
                print(f"[KEEP] Moving {filename} back to clean folder...")
                shutil.move(src, dest)
                
                parent_dir = os.path.dirname(src)
                remaining = [f for f in os.listdir(parent_dir) if os.path.isfile(os.path.join(parent_dir, f)) and not f.startswith("00_REFERENCE_")]
                
                if in_reserv and not remaining:
                    try:
                        os.rmdir(parent_dir)
                    except Exception:
                        pass
                        
                main_discard = os.path.join(curr_discard_dir, folder)
                main_renders = [f for f in os.listdir(main_discard) if os.path.isfile(os.path.join(main_discard, f)) and not f.startswith("00_REFERENCE_")]
                reserv_exists = os.path.exists(os.path.join(main_discard, "reserv"))
                
                if not main_renders and not reserv_exists:
                    try:
                        shutil.rmtree(main_discard)
                    except Exception:
                        pass
                return True
            except Exception as e:
                print(f"[ERROR] Failed to move file: {e}")
                return False
        return False

HTML_CONTENT = """<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Turboflow Verifiering</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #080c14;
            --glass-bg: rgba(15, 22, 38, 0.7);
            --glass-border: rgba(255, 255, 255, 0.06);
            --text-main: #f8fafc;
            --text-muted: #64748b;
            --accent-green: #10b981;
            --accent-green-glow: rgba(16, 185, 129, 0.15);
            --accent-blue: #3b82f6;
            --accent-blue-glow: rgba(59, 130, 246, 0.15);
            --card-bg: rgba(255, 255, 255, 0.02);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        header {
            padding: 15px 40px;
            background: rgba(15, 22, 38, 0.4);
            border-bottom: 1px solid var(--glass-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
            height: 60px;
        }

        h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 1.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stats {
            font-family: 'Outfit', sans-serif;
            font-size: 1.05rem;
            color: var(--text-muted);
            font-weight: 600;
        }

        .stats span {
            color: #3b82f6;
        }

        main {
            flex: 1;
            display: flex;
            padding: 15px;
            gap: 15px;
            height: calc(100vh - 130px);
            min-height: 0; /* Important for flex child sizing */
        }

        .pane {
            flex: 1;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 15px 35px -5px rgba(0,0,0,0.5);
            position: relative;
            min-height: 0; /* Important for flex child sizing */
        }

        .pane-left {
            max-width: 380px;
        }

        .pane-title {
            font-family: 'Outfit', sans-serif;
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .image-container {
            width: 100%;
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            background: rgba(0, 0, 0, 0.25);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.02);
            position: relative;
            overflow: hidden;
            min-height: 0; /* Allow container to shrink */
        }

        .image-container img {
            max-width: 96%;
            max-height: 96%;
            object-fit: contain;
        }

        .meta-box {
            margin-top: 12px;
            width: 100%;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 8px;
            padding: 10px 15px;
            font-size: 0.85rem;
            line-height: 1.4;
            flex-shrink: 0; /* Keep text box size fixed */
        }

        .meta-label {
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 3px;
        }

        .meta-val {
            color: var(--text-main);
            word-break: break-all;
        }

        .meta-val-large {
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            font-weight: 700;
            color: #3b82f6;
            margin-bottom: 5px;
        }

        .badge {
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: inline-block;
            margin-top: 5px;
        }

        footer {
            height: 70px;
            background: rgba(15, 22, 38, 0.5);
            border-top: 1px solid var(--glass-border);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 40px;
            backdrop-filter: blur(10px);
            flex-shrink: 0;
        }

        .key-guide {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        kbd {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-main);
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.15);
            font-family: inherit;
            font-weight: 700;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .action-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            font-family: inherit;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-keep {
            background: var(--accent-green);
            color: white;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.25);
        }

        .btn-keep:hover {
            transform: translateY(-2px);
            filter: brightness(1.1);
        }

        .btn-skip {
            background: var(--accent-blue);
            color: white;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.25);
        }

        .btn-skip:hover {
            transform: translateY(-2px);
            filter: brightness(1.1);
        }

        .flash-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.12s ease-out;
            z-index: 10;
        }

        .flash-keep {
            background: radial-gradient(circle, rgba(16, 185, 129, 0.2) 0%, transparent 80%);
        }

        .flash-skip {
            background: radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 80%);
        }

        .flash-active {
            opacity: 1;
        }
        
        .no-images {
            font-family: 'Outfit', sans-serif;
            font-size: 1.4rem;
            color: var(--text-muted);
            text-align: center;
            margin: auto;
        }
    </style>
</head>
<body>
    <header>
        <h1>Turboflow Verifiering</h1>
        <div class="stats" id="stats-counter">Laddar bilder...</div>
    </header>

    <main id="main-content">
        <!-- Reference Pane -->
        <div class="pane pane-left">
            <div class="pane-title">Referensprodukt</div>
            <div class="image-container">
                <img id="ref-image" src="" alt="Referens">
            </div>
            <div class="meta-box">
                <div class="meta-label">Produktnamn</div>
                <div class="meta-val-large" id="ref-name">-</div>
                <div class="badge" id="ref-sku">-</div>
            </div>
        </div>

        <!-- Candidate Pane -->
        <div class="pane">
            <div class="pane-title">Rendering (Utgallrad)</div>
            <div class="flash-overlay flash-keep" id="flash-keep"></div>
            <div class="flash-overlay flash-skip" id="flash-skip"></div>
            <div class="image-container">
                <img id="cand-image" src="" alt="Rendering">
            </div>
            <div class="meta-box">
                <div id="actual-prod-container" style="margin-bottom: 8px; display: none;">
                    <div class="meta-label" style="color: #60a5fa; font-size: 0.75rem;">Visar egentligen</div>
                    <div class="meta-val" id="cand-actual-name" style="font-weight: 700; color: #93c5fd; font-size: 1.05rem;">-</div>
                </div>
                <div class="meta-label">Filnamn</div>
                <div class="meta-val" id="cand-filename">-</div>
                <div class="badge" id="cand-badge">Huvudmapp</div>
            </div>
        </div>
    </main>

    <footer>
        <div class="key-guide">
            <kbd>Enter</kbd> eller <button class="action-btn btn-keep" onclick="keepCurrent()"><span class="icon">✨</span> Spara och flytta tillbaka</button>
        </div>
        <div class="key-guide">
            <kbd>→</kbd> eller <button class="action-btn btn-skip" onclick="skipCurrent()"><span class="icon">⏩</span> Hoppa över</button>
        </div>
        <div class="key-guide">
            <kbd>←</kbd> Föregående
        </div>
    </footer>

    <script>
        let images = [];
        let currentIndex = 0;

        async function loadImages() {
            try {
                const res = await fetch("/api/images");
                images = await res.json();
                updateStats();
                if (images.length > 0) {
                    // Try to restore progress from localStorage
                    const savedFilename = localStorage.getItem("verification-last-filename");
                    let startIndex = 0;
                    if (savedFilename) {
                        const foundIdx = images.findIndex(item => item.filename === savedFilename);
                        if (foundIdx !== -1) {
                            startIndex = foundIdx;
                        }
                    }
                    showImage(startIndex);
                } else {
                    showEmptyState();
                }
            } catch (err) {
                console.error("Error loading images:", err);
            }
        }

        function showEmptyState() {
            document.getElementById("main-content").innerHTML = `
                <div class="no-images">
                    🎉 Alla bilder har gåtts igenom! Det finns inga borttagna bilder kvar.
                </div>
            `;
            document.getElementById("stats-counter").textContent = "Klar!";
        }

        function showImage(index) {
            if (index < 0 || index >= images.length) return;
            currentIndex = index;
            updateStats();

            const item = images[index];
            // 1. Left pane shows the FOLDER's product and its reference photo (never broken)
            document.getElementById("ref-image").src = item.ref_url || "";
            document.getElementById("cand-image").src = item.img_url;

            // Format folder name nicely for Left Pane
            const folderName = item.folder.replace(/\\\\/g, '/').split('(')[0].trim();
            document.getElementById("ref-name").textContent = folderName;
            
            // Extract folder SKU for Left Pane
            const folderSkuMatch = item.folder.match(/\\(([^)]+)\\)$/);
            const folderSku = folderSkuMatch ? folderSkuMatch[1] : "-";
            document.getElementById("ref-sku").textContent = folderSku;

            // 2. Right pane shows candidate filename and actual product if it is a mismatch
            document.getElementById("cand-filename").textContent = item.filename;
            
            const actualContainer = document.getElementById("actual-prod-container");
            const actualNameEl = document.getElementById("cand-actual-name");
            
            if (item.actual_name && item.actual_sku && item.actual_sku !== folderSku) {
                actualNameEl.textContent = `${item.actual_name.replace(/\\'/g, "'")} (${item.actual_sku})`;
                actualContainer.style.display = "block";
            } else {
                actualContainer.style.display = "none";
            }
            
            const badge = document.getElementById("cand-badge");
            let locationText = item.in_reserv ? "Reservmapp" : "Huvudmapp";
            
            // Highlight folder mismatches in red
            if (item.actual_sku && folderSku !== "-" && item.actual_sku !== folderSku) {
                badge.style.background = "rgba(239, 68, 68, 0.18)";
                badge.style.color = "#f87171";
            } else if (item.in_reserv) {
                badge.style.background = "rgba(139, 92, 246, 0.15)";
                badge.style.color = "#a78bfa";
            } else {
                badge.style.background = "rgba(59, 130, 246, 0.15)";
                badge.style.color = "#60a5fa";
            }
            badge.textContent = locationText;

            // Save progress
            localStorage.setItem("verification-last-filename", item.filename);
        }

        function updateStats() {
            const stats = document.getElementById("stats-counter");
            if (images.length === 0) {
                stats.textContent = "Inga bilder kvar";
            } else {
                stats.innerHTML = `Bild <span>${currentIndex + 1}</span> av <span>${images.length}</span>`;
            }
        }

        async function keepCurrent() {
            if (images.length === 0) return;
            const item = images[currentIndex];
            
            const flash = document.getElementById("flash-keep");
            flash.classList.add("flash-active");
            setTimeout(() => flash.classList.remove("flash-active"), 120);

            try {
                const response = await fetch("/api/keep", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        filename: item.filename,
                        folder: item.folder,
                        in_reserv: item.in_reserv
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    images.splice(currentIndex, 1);
                    if (images.length === 0) {
                        showEmptyState();
                    } else {
                        if (currentIndex >= images.length) {
                            currentIndex = images.length - 1;
                        }
                        showImage(currentIndex);
                    }
                }
            } catch (err) {
                console.error("Error keeping image:", err);
            }
        }

        function skipCurrent() {
            if (images.length === 0) return;
            
            const flash = document.getElementById("flash-skip");
            flash.classList.add("flash-active");
            setTimeout(() => flash.classList.remove("flash-active"), 120);

            if (currentIndex < images.length - 1) {
                showImage(currentIndex + 1);
            }
        }

        function prevImage() {
            if (currentIndex > 0) {
                showImage(currentIndex - 1);
            }
        }

        // Handle Keyboard Events
        window.addEventListener("keydown", (e) => {
            if (images.length === 0) return;
            
            if (e.key === "Enter") {
                keepCurrent();
            } else if (e.key === "ArrowRight") {
                skipCurrent();
            } else if (e.key === "ArrowLeft") {
                prevImage();
            }
        });

        loadImages();
    </script>
</body>
</html>
"""

def main():
    if not os.path.exists(DISCARD_DIR):
        print(f"Error: Discarded folder {DISCARD_DIR} does not exist!")
        sys.exit(1)
        
    server = HTTPServer(("localhost", PORT), VerificationHandler)
    url = f"http://localhost:{PORT}"
    
    print("\n" + "="*50)
    print(f"  SERVER KÖR PÅ: {url}")
    print(f"  Jämför utgallrade bilder med referenserna.")
    print("="*50)
    print("\nKortkommandon i webbläsaren:")
    print("  [Enter]      -> Godkänn bild (flyttas tillbaka till rena mappen)")
    print("  [Pil Höger]  -> Hoppa över (lämna kvar i borttagna, gå till nästa)")
    print("  [Pil Vänster] -> Gå tillbaka till föregående bild")
    print("\nStäng det här terminalfönstret (Ctrl+C) när du är helt klar.")
    
    webbrowser.open(url)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStänger ner servern. Klar!")
        sys.exit(0)

if __name__ == "__main__":
    main()

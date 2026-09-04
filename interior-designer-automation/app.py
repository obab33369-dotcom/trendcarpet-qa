import os
import base64
import json
import asyncio
import random
import logging
import re
import shutil
import urllib.request
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from playwright.async_api import async_playwright

import win32crypt
import win32file
import win32con
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def win32_copy_locked_file(src, dst):
    try:
        handle = win32file.CreateFile(
            src,
            win32con.GENERIC_READ,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None,
            win32con.OPEN_EXISTING,
            win32con.FILE_ATTRIBUTE_NORMAL,
            None
        )
        chunk_size = 64 * 1024
        with open(dst, "wb") as f_out:
            while True:
                err, chunk = win32file.ReadFile(handle, chunk_size)
                if not chunk:
                    break
                f_out.write(chunk)
        win32file.CloseHandle(handle)
        return True
    except Exception as e:
        logger.warning(f"win32_copy_locked_file failed for {src}: {e}")
        return False

def get_browser_channel() -> Optional[str]:
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for p in paths:
        if os.path.exists(p):
            return "chrome"
            
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    for p in edge_paths:
        if os.path.exists(p):
            return "msedge"
            
    return None

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("interior-automation")

app = FastAPI(title="Interior Designer Automation")

# Directory Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
PROFILE_DIR = os.path.join(BASE_DIR, "browser_profile")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# Create directories if they don't exist
os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Templates
templates = Jinja2Templates(directory=TEMPLATE_DIR)

def get_browser_cookies() -> List[Dict[str, Any]]:
    cookies_list = []
    browsers = {
        "Google Chrome": {
            "local_state": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Local State"),
            "profiles": [
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies"),
                *[os.path.expandvars(f"%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Profile {i}\\Network\\Cookies") for i in range(1, 10)]
            ]
        },
        "Microsoft Edge": {
            "local_state": os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Local State"),
            "profiles": [
                os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies"),
                *[os.path.expandvars(f"%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Profile {i}\\Network\\Cookies") for i in range(1, 10)]
            ]
        }
    }
    
    for name, paths in browsers.items():
        local_state_path = paths["local_state"]
        if not os.path.exists(local_state_path):
            continue
            
        logger.info(f"Hämtar DPAPI-krypteringsnyckel från {name}...")
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = json.loads(f.read())
            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            encrypted_key = encrypted_key[5:] # Ta bort DPAPI-prefixet (5 bytes)
            decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        except Exception as e:
            logger.warning(f"Kunde inte dekryptera nyckeln för {name}: {e}")
            continue
            
        for cookies_path in paths["profiles"]:
            if not os.path.exists(cookies_path):
                continue
                
            logger.info(f"Läser inloggningsfiler från: {cookies_path}")
            temp_path = os.path.join(os.getcwd(), f"temp_cookies_db_{random.randint(1000, 9999)}")
            try:
                copied = win32_copy_locked_file(cookies_path, temp_path)
                if not copied:
                    try:
                        # Försök med powershell Copy-Item som respekterar delad läsning även när filen är låst för skrivning
                        import subprocess
                        cmd = f'powershell -Command "Copy-Item -Path \'{cookies_path}\' -Destination \'{temp_path}\' -Force"'
                        subprocess.run(cmd, shell=True, capture_output=True)
                        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                            copied = True
                    except Exception:
                        pass
                        
                if not copied:
                    try:
                        # Fallback till cmd copy
                        subprocess.run(f'cmd /c copy "{cookies_path}" "{temp_path}"', shell=True, capture_output=True)
                        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                            copied = True
                    except Exception:
                        pass
                        
                if not copied:
                    # Sista utväg fallback
                    shutil.copyfile(cookies_path, temp_path)
                
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT host_key, name, path, encrypted_value, expires_utc, is_secure, is_httponly 
                    FROM cookies 
                    WHERE host_key LIKE '%google.com' OR host_key LIKE '%gemini.google.com'
                """)
                
                rows = cursor.fetchall()
                conn.close()
                
                count = 0
                for host_key, name_str, path_val, encrypted_value, expires_utc, is_secure, is_httponly in rows:
                    if not encrypted_value:
                        continue
                    try:
                        # Dekryptera med AES-GCM
                        if encrypted_value.startswith(b'v10') or encrypted_value.startswith(b'v11'):
                            iv = encrypted_value[3:15]
                            ciphertext = encrypted_value[15:]
                            aesgcm = AESGCM(decrypted_key)
                            value = aesgcm.decrypt(ciphertext, iv, None).decode('utf-8')
                        else:
                            # DPAPI Fallback för äldre versioner
                            value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
                            
                        # Konvertera Chrome-tid till Unix timestamp
                        expires = None
                        if expires_utc > 0:
                            expires = (expires_utc / 1000000.0) - 11644473600.0
                            
                        cookie_dict = {
                            "name": name_str,
                            "value": value,
                            "domain": host_key,
                            "path": path_val,
                            "secure": bool(is_secure),
                            "httpOnly": bool(is_httponly),
                            "sameSite": "Lax"
                        }
                        if expires is not None:
                            cookie_dict["expires"] = expires
                            
                        cookies_list.append(cookie_dict)
                        count += 1
                    except Exception:
                        pass
                logger.info(f"✓ Dekrypterade och läste in {count} cookies från {name}!")
            except Exception as e:
                logger.warning(f"Kunde inte läsa cookies från sökvägen: {e}")
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                        
    return cookies_list

# App State
state = {
    "status": "idle",  # idle, running, setup
    "progress": 0,
    "current_step": "System ready",
    "logs": ["System initialized."],
    "stop_requested": False,
    "browser_running": False
}

orchestrator_process = None

# Mount outputs for previewing
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# Log streaming generator
async def log_generator():
    log_index = 0
    while True:
        if log_index < len(state["logs"]):
            yield f"data: {json.dumps({'log': state['logs'][log_index], 'status': state['status'], 'progress': state['progress'], 'step': state['current_step']})}\n\n"
            log_index += 1
        await asyncio.sleep(0.1)

def add_log(msg: str):
    logger.info(msg)
    state["logs"].append(msg)
    state["current_step"] = msg

def parse_product_name(filename: str) -> str:
    # Pattern to strip leading index like "0001_" and trailing "-1-26U-wonder" or "-1"
    base, _ = os.path.splitext(filename)
    # Remove leading digits and underscore
    base = re.sub(r'^\d+_', '', base)
    # Remove trailing sequence suffix
    base = re.sub(r'-\d+-\w+-wonder$', '', base)
    base = re.sub(r'-\d+$', '', base)
    return base

def classify_product(name: str) -> str:
    name_lower = name.lower()
    if "soffa" in name_lower:
        return "soffa"
    elif "fåtölj" in name_lower:
        return "fåtölj"
    elif "stol" in name_lower or "pall" in name_lower:
        return "stol"
    elif "soffbord" in name_lower:
        return "soffbord"
    elif "matbord" in name_lower or "bord" in name_lower:
        if "sängbord" in name_lower:
            return "sängbord"
        elif "skrivbord" in name_lower:
            return "skrivbord"
        elif "sidobord" in name_lower:
            return "sidobord"
        return "matbord"
    elif "lampa" in name_lower:
        return "lampa"
    elif "byrå" in name_lower or "skänk" in name_lower or "tv-bänk" in name_lower or "hylla" in name_lower or "bokhylla" in name_lower:
        return "förvaring"
    return "andra"

def extract_style_keywords(name: str) -> List[str]:
    keywords = []
    name_lower = name.lower()
    # Wood types
    if "valnöt" in name_lower:
        keywords.append("valnöt")
    elif "ek" in name_lower:
        keywords.append("ek")
    elif "natur" in name_lower:
        keywords.append("natur")
    
    # Colors / Materials
    for color in ["vit", "svart", "grå", "beige", "brun", "grön", "röd", "orange", "bouclé", "marmor"]:
        if color in name_lower:
            keywords.append(color)
    return keywords

class ScanRequest(BaseModel):
    furniture_folder: str
    style_image_path: str
    ignore_keywords: Optional[str] = "interior, miljo, ambient, livsstil"

class StartRequest(BaseModel):
    furniture_folder: str
    style_image_path: str
    selected_items: List[str] = [] # If empty, use AI Curation
    prompt_template: str
    batch_count: int = 1
    items_per_room: int = 4
    ignore_keywords: Optional[str] = "interior, miljo, ambient, livsstil"

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/logs")
async def get_log_stream():
    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.get("/api/status")
async def get_status():
    return state

@app.post("/api/scan")
async def scan_folders(req: ScanRequest):
    if not os.path.exists(req.furniture_folder):
        raise HTTPException(status_code=400, detail="Möbelmappen finns inte.")
    if not os.path.exists(req.style_image_path):
        raise HTTPException(status_code=400, detail="Stilreferensbilden finns inte.")
    
    valid_exts = (".png", ".jpg", ".jpeg", ".webp")
    products_map = {}
    total_images = 0
    ignored_count = 0
    
    # Parse ignore keywords
    ignore_list = [k.strip().lower() for k in req.ignore_keywords.split(",") if k.strip()]
    
    for f in os.listdir(req.furniture_folder):
        if f.lower().endswith(valid_exts):
            # Check if filename contains any ignore keywords
            f_lower = f.lower()
            should_ignore = False
            for kw in ignore_list:
                if kw in f_lower:
                    should_ignore = True
                    break
            
            if should_ignore:
                ignored_count += 1
                continue
                
            prod_name = parse_product_name(f)
            if prod_name not in products_map:
                products_map[prod_name] = []
            products_map[prod_name].append(f)
            total_images += 1
            
    products_list = []
    for name, files in products_map.items():
        files.sort()  # Ensure primary image (usually suffix -1-) is first
        products_list.append({
            "name": name,
            "thumbnail": files[0],
            "image_count": len(files),
            "all_images": files,
            "category": classify_product(name),
            "styles": extract_style_keywords(name)
        })
        
    products_list.sort(key=lambda x: x["name"])
            
    # Serve preview folders
    try:
        app.mount("/furniture_preview", StaticFiles(directory=req.furniture_folder), name="furniture_preview")
    except Exception:
        pass
    
    style_dir = os.path.dirname(req.style_image_path)
    style_filename = os.path.basename(req.style_image_path)
    try:
        app.mount("/style_preview", StaticFiles(directory=style_dir), name="style_preview")
    except Exception:
        pass

    return {
        "products": products_list,
        "style_filename": style_filename,
        "product_count": len(products_list),
        "total_images": total_images,
        "ignored_count": ignored_count
    }

def clear_browser_locks():
    try:
        import subprocess
        if os.name == 'nt':
            cmd = "powershell -Command \"Get-Process -Name chrome -ErrorAction SilentlyContinue | Where Path -like '*ms-playwright*' | Stop-Process -Force\""
            subprocess.run(cmd, shell=True, capture_output=True)
            logger.info("Killed any orphaned Playwright browser processes to free locks.")
    except Exception as e:
        logger.warning(f"Could not kill orphaned Playwright browser processes: {e}")

    try:
        lock_file = os.path.join(PROFILE_DIR, "lockfile")
        if os.path.exists(lock_file):
            os.remove(lock_file)
            logger.info("Cleared browser profile lockfile.")
    except Exception as e:
        logger.warning(f"Could not clear browser profile lockfile: {e}")
        
    try:
        lock_file_default = os.path.join(PROFILE_DIR, "Default", "LOCK")
        if os.path.exists(lock_file_default):
            os.remove(lock_file_default)
            logger.info("Cleared Default browser profile LOCK.")
    except Exception as e:
        logger.warning(f"Could not clear Default browser profile LOCK: {e}")

@app.post("/api/setup-browser")
async def setup_browser():
    if state["browser_running"] or state["status"] == "setup":
        add_log("Webbläsaren körs redan eller håller på att startas.")
        return {"status": "already_running"}

    state["status"] = "setup"
    add_log("Startar webbläsare för inloggning...")
    
    async def run_setup():
        try:
            clear_browser_locks()
            async with async_playwright() as p:
                add_log("Skapar Playwright-instans...")
                try:
                    channel = get_browser_channel()
                    launch_kwargs = {
                        "user_data_dir": PROFILE_DIR,
                        "headless": False,
                        "args": ["--start-maximized", "--disable-blink-features=AutomationControlled"]
                    }
                    if channel:
                        launch_kwargs["channel"] = channel
                        add_log(f"Använder din ordinarie webbläsare: {channel.capitalize()} för inloggning.")
                    else:
                        add_log("Använder standard inbyggd Chromium-webbläsare.")
                        
                    context = await asyncio.wait_for(
                        p.chromium.launch_persistent_context(**launch_kwargs),
                        timeout=25.0
                    )
                except asyncio.TimeoutError:
                    add_log("🔴 Timeout: Det tog för lång tid att starta webbläsaren. Detta beror oftast på en låst profil. Frisläpper låsfiler...")
                    raise RuntimeError("Playwright start timeout. Browser profile was locked.")
                
                # HÄMTA OCH IMPORTERA DINA AKTIVA INLOGGNINGS-COOKIES
                add_log("Försöker hämta aktiva inloggningar från din ordinarie Chrome & Edge...")
                try:
                    active_cookies = get_browser_cookies()
                    if active_cookies:
                        await context.add_cookies(active_cookies)
                        add_log(f"🎉 Framgång! Importerade {len(active_cookies)} cookies. Du bör bli automatiskt inloggad!")
                    else:
                        add_log("⚠️ Inga cookies hittades. Du kan behöva logga in manuellt i fönstret.")
                except Exception as e_cookies:
                    add_log(f"⚠️ Fel vid automatisk cookie-import: {e_cookies}")
                
                page = await context.new_page()
                state["browser_running"] = True
                add_log("Öppnar Gemini Advanced. Du bör bli automatiskt inloggad!")
                
                await page.goto("https://gemini.google.com/app", timeout=60000)
                add_log("Låt webbläsaren vara öppen. När du är färdiginloggad, stäng webbläsarfönstret för att slutföra.")
                
                while state["status"] == "setup":
                    try:
                        if page.is_closed():
                            break
                    except Exception:
                        break
                    await asyncio.sleep(1)
                    
                await context.close()
                add_log("Inloggningswebbläsaren stängd.")
        except Exception as e:
            add_log(f"Inloggningswebbläsaren stängdes eller stötte på ett fel: {e}")
        finally:
            state["browser_running"] = False
            state["status"] = "idle"
            add_log("✅ System redo. Du kan starta batchkörningen.")

    asyncio.create_task(run_setup())
    return {"status": "started"}

def get_ollama_model() -> str:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            res_body = response.read().decode('utf-8')
            data = json.loads(res_body)
            models = [m["name"] for m in data.get("models", [])]
            for m in models:
                if "llama3.2-vision" in m:
                    return m
            for m in models:
                if "llama" in m or "mistral" in m:
                    return m
            if models:
                return models[0]
    except Exception:
        pass
    return "llama3.2-vision:latest"  # Fallback

def generate_rule_based_description(product_name: str) -> str:
    name_lower = product_name.lower()
    category = classify_product(product_name)
    
    # Parse materials/colors
    materials = []
    if "ek" in name_lower:
        materials.append("ljus ek")
    if "valnöt" in name_lower or "valnot" in name_lower:
        materials.append("mörk valnöt")
    if "svart" in name_lower:
        materials.append("svartlackad finish")
    if "vit" in name_lower:
        materials.append("vit finish")
    if "beige" in name_lower:
        materials.append("beige tyg")
    if "bouclé" in name_lower or "boucle" in name_lower:
        materials.append("lyxigt bouclé-tyg")
    if "marmor" in name_lower:
        materials.append("marmorskiva")
    
    material_str = " och ".join(materials) if materials else "stilrent material"
    
    if category == "soffa":
        return f"En elegant soffa i {material_str} med modern minimalistisk form."
    elif category == "fåtölj":
        return f"En bekväm och lyxig fåtölj i {material_str} med matchande stomme och ben."
    elif category == "stol":
        return f"En stilren stol/pall i {material_str} med matchande ben."
    elif category == "soffbord":
        return f"Ett vackert soffbord/kaffebord i {material_str} med moderna ben."
    elif category == "matbord":
        return f"Ett robust och elegant matbord i {material_str}."
    elif category == "lampa":
        return f"En dekorativ lampa i {material_str} som ger ett behagligt sken."
    elif category == "förvaring":
        return f"En funktionell och stilren förvaringsmöbel/skänk i {material_str}."
    return f"En vacker möbel ({product_name}) i {material_str}."

async def analyze_image_with_ollama(image_path: str, product_name: str) -> str:
    model_name = get_ollama_model()
    # Check if this is a vision model
    if "vision" not in model_name.lower():
        add_log(f"⚠️ Modellen '{model_name}' stöder inte bildanalys. Använder regelbaserad beskrivning.")
        return generate_rule_based_description(product_name)
        
    try:
        if not os.path.exists(image_path):
            return generate_rule_based_description(product_name)
            
        add_log(f"🤖 Ollama Vision analyserar: '{os.path.basename(image_path)}'...")
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
            
        prompt = (
            f"Du är en expert på möbeldesign. Beskriv den här möbeln '{product_name}' på svenska i en kort, "
            f"detaljerad mening (max 25 ord). Fokusera på dess exakta form (t.ex. runt, rektangulärt), "
            f"material (t.ex. ek, bouclé, metall), färg (t.ex. beige, svart) och ben (t.ex. tre runda ben, tunna svarta metallben)."
        )
        
        req_data = json.dumps({
            "model": model_name,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False
        }).encode('utf-8')
        
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            desc = res_json.get("response", "").strip()
            desc = desc.strip('"').strip("'")
            add_log(f"✓ Ollama Vision analys klar: '{desc[:60]}...'")
            return desc
    except Exception as e:
        logger.warning(f"Ollama Vision analysis failed: {e}. Falling back to rule-based description.")
        return generate_rule_based_description(product_name)

async def curate_with_ollama(products: List[Dict], theme: str, style_keywords: List[str] = None) -> List[str]:
    model_name = get_ollama_model()
    add_log(f"🤖 Använder Ollama-modell: '{model_name}' för AI-matchning...")
    
    style_str = ", ".join(style_keywords) if style_keywords else "generell modern och elegant inredning"
    prompt = f"""Du är en professionell inredningsarkitekt. Välj ut en matchande kombination på 3-4 möbler från listan nedan för att skapa ett vackert, lyxigt och stilrent '{theme}'.
Den valda möbelkombinationen MÅSTE matcha och harmonisera med den angivna stilreferensen som har följande karaktär: {style_str}.
Alla valda möbler måste matcha varandra och stilreferensen i stil, träslag (t.ex. ek med ek, valnöt med valnöt, natur med natur) samt färger.

Här är listan över tillgängliga produkter:
"""
    candidates = products[:100]
    for p in candidates:
        prompt += f"- {p['name']} (kategori: {p['category']}, stil: {', '.join(p['styles'])})\n"
    
    prompt += """
Välj exakt 3 eller 4 produkter som passar perfekt ihop och harmoniserar med stilreferensen. Svara ENDAST med en JSON-lista som innehåller produktnamnen, till exempel:
["soffbord-créme-natur", "bäddsoffa-texas-beige", "lampa-senigallia-s-vit-vit"]
Svara absolut inte med något annat än en ren JSON-lista. Svara inte med förklaringar eller markdown-block.
"""
    try:
        req_data = json.dumps({
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }).encode('utf-8')
        
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            content = res_json.get("response", "").strip()
            selected = json.loads(content)
            if isinstance(selected, list) and len(selected) >= 2:
                file_matches = []
                for sel_name in selected:
                    for p in products:
                        if p['name'].lower() == sel_name.lower():
                            file_matches.append(p['thumbnail'])
                            break
                if len(file_matches) >= 2:
                    add_log(f"🤖 Ollama lyckades kurera rummet ({theme}) med: {', '.join(selected)}")
                    return file_matches
    except Exception as e:
        logger.warning(f"Ollama curation failed or timed out: {e}. Falling back to rule-based matcher.")
    return []

def curate_with_rules(products: List[Dict], theme: str, items_needed: int, style_keywords: List[str] = None) -> List[str]:
    cat_map = {}
    for p in products:
        cat = p["category"]
        if cat not in cat_map:
            cat_map[cat] = []
        cat_map[cat].append(p)
        
    selected_items = []
    
    if theme == "Matsal (Dining Room)":
        primary_cat = "matbord"
        secondary_cats = ["stol", "lampa", "förvaring"]
    elif theme == "Vardagsrum (Living Room)":
        primary_cat = "soffa"
        secondary_cats = ["soffbord", "fåtölj", "lampa", "förvaring"]
    elif theme == "Arbetsrum (Office)":
        primary_cat = "skrivbord"
        secondary_cats = ["stol", "lampa", "förvaring"]
    else:
        primary_cat = "sängbord"
        secondary_cats = ["förvaring", "lampa", "stol"]
        
    if primary_cat in cat_map and cat_map[primary_cat]:
        options = cat_map[primary_cat]
        if style_keywords:
            matched_options = [opt for opt in options if any(style in style_keywords for style in opt["styles"])]
            primary_item = random.choice(matched_options) if matched_options else random.choice(options)
        else:
            primary_item = random.choice(options)
    else:
        candidates = [p for p in products if p["category"] != "andra"]
        primary_item = random.choice(candidates) if candidates else random.choice(products)
        
    selected_items.append(primary_item)
    
    style_constraints = list(set(primary_item["styles"] + (style_keywords or [])))
    
    for cat in secondary_cats:
        if len(selected_items) >= items_needed:
            break
        if cat in cat_map and cat_map[cat]:
            options = cat_map[cat]
            matched_options = []
            for opt in options:
                if opt["name"] == primary_item["name"]:
                    continue
                if any(style in style_constraints for style in opt["styles"]):
                    matched_options.append(opt)
            
            if matched_options:
                chosen = random.choice(matched_options)
            else:
                chosen = random.choice(options)
                
            selected_items.append(chosen)
            
    while len(selected_items) < items_needed:
        remaining = [p for p in products if p not in selected_items]
        if not remaining:
            break
        selected_items.append(random.choice(remaining))
        
    result_files = [item["thumbnail"] for item in selected_items]
    add_log(f"🎨 Regelbaserad inredare matchade ihop ({theme}) baserat på stilreferens: {', '.join([item['name'] for item in selected_items])}")
    return result_files

def assign_quantities(filenames: List[str], theme: str) -> List[Dict[str, Any]]:
    curated_items = []
    for fn in filenames:
        name = parse_product_name(fn)
        category = classify_product(name)
        
        # Default quantity is 1
        qty = 1
        
        if theme == "Matsal (Dining Room)":
            if category == "stol":
                qty = 6
        elif theme == "Vardagsrum (Living Room)":
            if category == "fåtölj" or category == "stol":
                qty = 2
        elif theme == "Sovrum (Bedroom)":
            if category == "sängbord" or category == "lampa":
                qty = 2
                
        curated_items.append({
            "filename": fn,
            "name": name,
            "quantity": qty
        })
    return curated_items

@app.post("/api/start")
async def start_generation(req: StartRequest):
    if state["status"] == "running":
        raise HTTPException(status_code=400, detail="Generering pågår redan.")
        
    state["status"] = "running"
    state["progress"] = 0
    state["stop_requested"] = False
    
    async def run_automation():
        try:
            # 1. Scan and parse products first
            valid_exts = (".png", ".jpg", ".jpeg", ".webp")
            products_map = {}
            ignore_list = [k.strip().lower() for k in req.ignore_keywords.split(",") if k.strip()]
            
            for f in os.listdir(req.furniture_folder):
                if f.lower().endswith(valid_exts):
                    f_lower = f.lower()
                    should_ignore = False
                    for kw in ignore_list:
                        if kw in f_lower:
                            should_ignore = True
                            break
                    if should_ignore:
                        continue
                    prod_name = parse_product_name(f)
                    if prod_name not in products_map:
                        products_map[prod_name] = []
                    products_map[prod_name].append(f)
                    
            products = []
            for name, files in products_map.items():
                files.sort()
                products.append({
                    "name": name,
                    "thumbnail": files[0],
                    "all_images": files,
                    "category": classify_product(name),
                    "styles": extract_style_keywords(name)
                })
            
            if not products:
                add_log("🔴 Inga giltiga möbelprodukter hittades i mappen efter filtrering.")
                state["status"] = "idle"
                return
                
            # Extract style keywords from the style reference image filename
            style_base = parse_product_name(os.path.basename(req.style_image_path))
            style_ref_keywords = extract_style_keywords(style_base)
            add_log(f"🎨 Identifierade stilnyckelord från stilreferens: {', '.join(style_ref_keywords) if style_ref_keywords else 'inga specifika'}")
            
            # 2. Launch playwright browser session once
 
            clear_browser_locks()
            async with async_playwright() as p:
                add_log("Startar inredningswebbläsare...")
                try:
                    channel = get_browser_channel()
                    launch_kwargs = {
                        "user_data_dir": PROFILE_DIR,
                        "headless": False,
                        "args": ["--start-maximized", "--disable-blink-features=AutomationControlled"]
                    }
                    if channel:
                        launch_kwargs["channel"] = channel
                        add_log(f"Använder din ordinarie webbläsare: {channel.capitalize()} för batchkörning.")
                    else:
                        add_log("Använder standard inbyggd Chromium-webbläsare.")
                        
                    context = await asyncio.wait_for(
                        p.chromium.launch_persistent_context(**launch_kwargs),
                        timeout=25.0
                    )
                except asyncio.TimeoutError:
                    add_log("🔴 Timeout: Det tog för lång tid att starta inredningswebbläsaren. Detta beror oftast på en låst profil. Frisläpper låsfiler...")
                    raise RuntimeError("Playwright start timeout. Browser profile was locked.")
                
                # HÄMTA OCH IMPORTERA DINA AKTIVA INLOGGNINGS-COOKIES
                add_log("Försöker hämta aktiva inloggningar från din ordinarie Chrome & Edge...")
                try:
                    active_cookies = get_browser_cookies()
                    if active_cookies:
                        await context.add_cookies(active_cookies)
                        add_log(f"🎉 Framgång! Importerade {len(active_cookies)} cookies. Du bör bli automatiskt inloggad!")
                    else:
                        add_log("⚠️ Inga cookies hittades. Du kan behöva logga in manuellt i fönstret.")
                except Exception as e_cookies:
                    add_log(f"⚠️ Fel vid automatisk cookie-import: {e_cookies}")
                
                page = await context.new_page()
                page.set_default_timeout(120000)
                
                add_log("Navigerar till Gemini Advanced...")
                await page.goto("https://gemini.google.com/app")
                await asyncio.sleep(8)
                
                # Check if redirected to login page (Swedish or English)
                current_url = page.url.lower()
                is_logged_in = True
                if "accounts.google.com" in current_url or "signin" in current_url:
                    is_logged_in = False
                
                if is_logged_in:
                    for sign_in_selector in [
                        "a:has-text('Logga in')", "a:has-text('Sign in')",
                        "button:has-text('Logga in')", "button:has-text('Sign in')",
                        "div:has-text('Logga in för att ladda upp')", "div:has-text('Sign in to upload')"
                    ]:
                        try:
                            if await page.locator(sign_in_selector).count() > 0:
                                is_logged_in = False
                                add_log(f"Inloggningsmarkör upptäckt via selektor: '{sign_in_selector}'")
                                break
                        except Exception:
                            pass
                    
                if not is_logged_in:
                    add_log("⚠️ Inte inloggad! Webbläsaren omdirigerades till Googles inloggningssida.")
                    add_log("👉 Tips: Klicka på 'Starta inloggningswebbläsare' i verktyget, logga in, vänta tills Gemini Advanced har laddats helt (ca 5 sekunder), och stäng sedan fönstret.")
                    await context.close()
                    state["status"] = "idle"
                    add_log("✅ System redo. Du kan starta en ny batchkörning.")
                    return
 
                # 3. Determine loop configurations
                total_batches = req.batch_count
                for batch_idx in range(total_batches):
                    if state["stop_requested"]:
                        add_log("🛑 Batch-loop avbruten av användaren.")
                        break
                        
                    batch_num = batch_idx + 1
                    add_log(f"--- STARTAR BATCH {batch_num} av {total_batches} ---")
                    state["progress"] = int((batch_idx / total_batches) * 100)
                    
                    # 4. Curate furniture items
                    theme = random.choice([
                        "Matsal (Dining Room)", 
                        "Vardagsrum (Living Room)", 
                        "Arbetsrum (Office)", 
                        "Sovrum (Bedroom)"
                    ])
                    
                    if req.selected_items:
                        # Manual curation - use user selection
                        curated_filenames = req.selected_items
                        add_log(f"Använder manuellt valda möbler: {', '.join(curated_filenames)}")
                    else:
                        # Automated Curation Mode
                        add_log(f"🤖 Automatiskt AI-val pågår för rumstyp: {theme}...")
                        curated_filenames = await curate_with_ollama(products, theme, style_ref_keywords)
                        if not curated_filenames:
                            # Fallback to rule matcher
                            curated_filenames = curate_with_rules(products, theme, req.items_per_room, style_ref_keywords)
                            
                    # Assign quantities to create curated_items
                    curated_items = assign_quantities(curated_filenames, theme)
                    
                    # Construct absolute file paths
                    upload_paths = [req.style_image_path]
                    curated_product_names = []
                    for item in curated_items:
                        upload_paths.append(os.path.join(req.furniture_folder, item["filename"]))
                        curated_product_names.append(f"{item['quantity']}st {item['name']}")
                        
                    # Create structured output folder
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    batch_dir_name = f"rum_{timestamp}_{random.randint(100, 999)}"
                    batch_output_dir = os.path.join(OUTPUT_DIR, batch_dir_name)
                    os.makedirs(batch_output_dir, exist_ok=True)
                    
                    # Copy used furniture images into output/furniture/
                    furniture_copy_dir = os.path.join(batch_output_dir, "furniture")
                    os.makedirs(furniture_copy_dir, exist_ok=True)
                    for item in curated_items:
                        src_f = os.path.join(req.furniture_folder, item["filename"])
                        shutil.copy(src_f, os.path.join(furniture_copy_dir, item["filename"]))
                    
                    add_log(f"Laddar upp stilbild + {len(curated_items)} möbler till Gemini...")
                    
                    # Robust upload flow
                    uploaded_successfully = False
                    
                    # Method 1: The standard menu-based file chooser (most reliable for Gemini Advanced)
                    try:
                        add_log("Letar efter uppladdningsknapp...")
                        upload_btn = page.locator(
                            "button[aria-label*='upload' i], button[aria-label*='ladda upp' i], "
                            "button[aria-label*='attach' i], button[aria-label*='bifoga' i], "
                            "button[aria-label*='add file' i], button[aria-label*='lägg till' i], "
                            "button[aria-label*='fil' i], button[aria-label*='plus' i], "
                            "button:has-text('+')"
                        ).first
                        
                        if await upload_btn.count() > 0:
                            add_log("Hittade uppladdningsknapp. Klickar på den...")
                            try:
                                await upload_btn.click(force=True, timeout=5000)
                            except Exception as e_click:
                                add_log("Standardklick misslyckades, använder JS-klick...")
                                await upload_btn.evaluate("el => el.click()")
                            await asyncio.sleep(3.0) # Vänta på att menyn visas
                            
                            # DIAGNOSTIK: Dumpa alla synliga element i menyn för att se vad som faktiskt finns
                            add_log("--- DIAGNOSTIK: Söker efter menyalternativ i DOM ---")
                            try:
                                scanned_els = await page.locator("li, [role='menuitem'], [role='option'], button, g-menu-item, a, span, div").all()
                                logged_count = 0
                                for idx, el in enumerate(scanned_els):
                                    if await el.is_visible():
                                        txt = (await el.inner_text() or "").strip().replace('\n', ' ')
                                        aria_lbl = await el.get_attribute("aria-label")
                                        role = await el.get_attribute("role")
                                        tag = await el.evaluate("el => el.tagName")
                                        classes = await el.get_attribute("class")
                                        # Only log interesting elements to avoid cluttering logs
                                        if any(kw in txt.lower() or (aria_lbl and kw in aria_lbl.lower()) for kw in ["dator", "computer", "ladda upp", "upload", "fil", "file", "enhet", "drive"]):
                                            add_log(f"🔍 Matchande element: <{tag}> role='{role}' class='{classes}' text='{txt}' aria='{aria_lbl}'")
                                            logged_count += 1
                                        elif role in ["menuitem", "option"] or (classes and "menu" in classes.lower()):
                                            add_log(f"📋 Meny-element: <{tag}> role='{role}' class='{classes}' text='{txt}' aria='{aria_lbl}'")
                                            logged_count += 1
                                if logged_count == 0:
                                    add_log("⚠️ Inga uppenbara meny- eller matchande element hittades i dom-skanningen.")
                            except Exception as diag_err:
                                add_log(f"⚠️ Diagnostiksökning misslyckades: {diag_err}")
                            add_log("--- DIAGNOSTIK SLUT ---")
                            
                            computer_upload_btn = None
                             
                            # Försök 1: Enskilda, giltiga text- och CSS-selektorer
                            selectors_to_try = [
                                "text=Ladda upp från datorn",
                                "text=Ladda upp från dator",
                                "text=Upload from computer",
                                "text=Från datorn",
                                "text=Från din dator",
                                "text=Från den här enheten",
                                "text=Ladda upp filer",
                                "text=Välj filer",
                                "text=Enhet",
                                "text=Dator",
                                "text=Computer",
                                "[aria-label*='computer' i]",
                                "[aria-label*='dator' i]",
                                "[aria-label*='enhet' i]",
                                "[aria-label*='device' i]",
                                "button:has-text('dator')",
                                "button:has-text('computer')",
                                "[role='menuitem']:has-text('dator')",
                                "[role='menuitem']:has-text('computer')",
                                "[role='menuitem']:has-text('device')",
                                "[role='menuitem']:has-text('enhet')",
                                ".menu-item:has-text('dator')",
                                ".menu-item:has-text('computer')"
                            ]
                            for selector in selectors_to_try:
                                loc_all = page.locator(selector)
                                count = await loc_all.count()
                                for idx in range(count):
                                    el = loc_all.nth(idx)
                                    if await el.is_visible():
                                        computer_upload_btn = el
                                        add_log(f"Hittade datorval med selektor: '{selector}' (element {idx})")
                                        break
                                if computer_upload_btn is not None:
                                    break
                                     
                            # Försök 2: Dynamisk textsökning (delvis matchning) om det inte hittades via selektorer
                            if computer_upload_btn is None:
                                for keyword in ["dator", "computer", "enhet", "device", "fil", "file", "ladda upp", "upload", "från", "from"]:
                                    loc_all = page.get_by_text(keyword, exact=False)
                                    count = await loc_all.count()
                                    for idx in range(count):
                                        el = loc_all.nth(idx)
                                        if await el.is_visible():
                                            txt = (await el.inner_text() or "").strip().replace('\n', ' ')
                                            computer_upload_btn = el
                                            add_log(f"Hittade datorval via textsökning '{keyword}' (element {idx}): '{txt[:50]}'")
                                            break
                                    if computer_upload_btn is not None:
                                        break
                                         
                            if computer_upload_btn is not None:
                                 add_log("Klickar på 'Ladda upp från dator' och väljer filer...")
                                 async with page.expect_file_chooser(timeout=15000) as fc_info:
                                     try:
                                         await computer_upload_btn.click(force=True, timeout=5000)
                                     except Exception:
                                         await computer_upload_btn.evaluate("el => el.click()")
                                 file_chooser = await fc_info.value
                                 await file_chooser.set_files(upload_paths)
                                 uploaded_successfully = True
                                 add_log("Filer överförda till filväljaren!")
                            else:
                                 add_log("Kunde inte hitta dropdown-valet för dator. Försöker direktklick på uppladdningsknappen via expect_file_chooser...")
                                 try:
                                     async with page.expect_file_chooser(timeout=5000) as fc_info:
                                         try:
                                             await upload_btn.click(force=True, timeout=3000)
                                         except Exception:
                                             await upload_btn.evaluate("el => el.click()")
                                     file_chooser = await fc_info.value
                                     await file_chooser.set_files(upload_paths)
                                     uploaded_successfully = True
                                     add_log("Filer överförda via direktklick på huvudknapp!")
                                 except Exception:
                                     pass
                    except Exception as e_upload:
                        add_log(f"⚠️ Metod 1 (meny) misslyckades: {e_upload}. Försöker med fallback...")
                    
                    # Method 2: Fallback to direct hidden input locator (original logic but with shorter timeout)
                    if not uploaded_successfully:
                        try:
                            file_inputs = page.locator("input[type='file']")
                            count_inputs = await file_inputs.count()
                            add_log(f"Metod 2: Söker efter filinput-element i DOM (hittade {count_inputs})...")
                            if count_inputs > 0:
                                await file_inputs.first.set_input_files(upload_paths, timeout=10000)
                                uploaded_successfully = True
                                add_log("Filer uppladdade via direkt DOM-input!")
                        except Exception as e_fallback:
                            add_log(f"⚠️ Metod 2 (direkt input) misslyckades också: {e_fallback}")
                            
                    if not uploaded_successfully:
                        raise RuntimeError("Kunde inte ladda upp filerna till Gemini med någon av metoderna. Avbryter.")
                        
                    add_log("Väntar på att bilderna laddas upp i chatten...")
                    await asyncio.sleep(8)
                    
                    # Prepare prompt with Ollama Vision descriptions and image index mapping
                    prompt_items = []
                    for idx, item in enumerate(curated_items):
                        img_path = os.path.join(req.furniture_folder, item["filename"])
                        desc = await analyze_image_with_ollama(img_path, item["name"])
                        # Image index: style reference is Image 1, so furniture items start from Image 2
                        image_index = idx + 2
                        prompt_items.append(
                            f"{item['quantity']}st '{item['name']}' (visas på Bild {image_index}, som har utseendet: {desc})"
                        )
                    
                    furniture_list_str = ", ".join(prompt_items)
                    prompt = req.prompt_template.replace("{furniture_list}", furniture_list_str)
                    
                    # Append strict directive to ensure Gemini links the names to the uploaded files and requests high fidelity
                    prompt += (
                        f"\n\nVIKTIGT: Den första uppladdade bilden (Bild 1) är enbart en stilreferens för rummets estetik. "
                        f"De efterföljande bilderna (Bild 2 och framåt) visar de exakta möbler du MÅSTE placera i rummet. "
                        f"Du får absolut inte byta ut dem mot slumpmässiga möbler. Studera Bild 2 och framåt noga och återskapa "
                        f"möblernas ben, träslag, tyg och form helt identiskt i rummet."
                        f"\n\nGenerera den färdiga interiörsbilden med absolut högsta möjliga realism, detaljrikedom och upplösning. "
                        f"Bilden ska ha tidningskvalitet (som ett exklusivt inredningsmagasin) med perfekt fotorealistisk ljussättning, "
                        f"skuggor och knivskarpa texturer. Använd den senaste tillgängliga högkvalitativa bildgenereringsmodellen."
                    )
                    
                    add_log(f"Skickar prompt: '{prompt[:110]}...'")
                    
                    input_area = page.locator("div[contenteditable='true'], textarea[placeholder*='Gemini']").first
                    await input_area.click()
                    await input_area.fill(prompt)
                    await asyncio.sleep(1)
                    
                    send_btn = page.locator("button[aria-label*='Send'], button[aria-label*='Skicka']").first
                    if await send_btn.count() > 0:
                        await send_btn.click()
                    else:
                        await input_area.press("Enter")
                        
                    add_log("Generering startad! Väntar på Gemini-visualisering (ca 45-80s)...")
                    await asyncio.sleep(55)
                    
                    # Search and download the generated images
                    images_found = []
                    add_log("Söker efter genererade designbilder i Geminis svar...")
                    
                    for attempt in range(15): # 15 försök * 6s = 90 sekunder max väntetid
                        latest_response = None
                        # Lokalisera den sista modellresponsens text/innehåll-behållare
                        for selector in ["message-content[role='model']", "message-content", ".message-content", ".model-response", "div.chat-entry[role='model']"]:
                            loc = page.locator(selector).last
                            if await loc.count() > 0:
                                latest_response = loc
                                break
                                
                        if latest_response is not None:
                            # Sök ENBART inuti den faktiska modellresponsen! Ingen global sökning som kan kapa uppladdade bilder.
                            response_images = latest_response.locator("img[src*='googleusercontent.com']")
                            count = await response_images.count()
                            
                            if count > 0:
                                temp_found = []
                                for idx in range(count):
                                    src = await response_images.nth(idx).get_attribute("src")
                                    if src:
                                        # Filtrera bort små UI-ikoner (t.ex. kopieringsikoner, profilbilder) som har små storleksparametrar
                                        is_icon = False
                                        for tiny_size in ["=s16", "=s24", "=s32", "=s48", "=s64", "=w16", "=w24", "=w32"]:
                                            if tiny_size in src:
                                                is_icon = True
                                                break
                                                
                                        if is_icon:
                                            continue
                                            
                                        # Rensa storleksparametrar för att hämta bilden i dess absoluta fulla originalupplösning (=s0)
                                        high_res_src = src
                                        if "=" in src:
                                            base_url = src.split("=")[0]
                                            high_res_src = f"{base_url}=s0"
                                            
                                        if high_res_src not in temp_found:
                                            temp_found.append(high_res_src)
                                            
                                if temp_found:
                                    images_found = temp_found
                                    add_log(f"✓ Hittade {len(images_found)} genererade rumsvarianter i svaret!")
                                    break
                                    
                        await asyncio.sleep(6)
                        
                    if images_found:
                        add_log(f"Hittade {len(images_found)} genererade rumsvarianter. Laddar ner högupplösta bilder...")
                        dl_count = 0
                        for i, src in enumerate(images_found[:2]): # Download up to 2 variations
                            try:
                                img_name = f"rum_design_{i+1}.png"
                                img_path = os.path.join(batch_output_dir, img_name)
                                urllib.request.urlretrieve(src, img_path)
                                add_log(f"✓ Nedladdad: {batch_dir_name}/{img_name} (originalupplösning =s0)")
                                dl_count += 1
                            except Exception as dl_err:
                                add_log(f"× Kunde inte spara bild {i+1}: {dl_err}")
                                
                        # Save metadata.json
                        meta_data = {
                            "timestamp": datetime.now().isoformat(),
                            "theme": theme,
                            "furniture_items": curated_product_names,
                            "style_reference": os.path.basename(req.style_image_path),
                            "prompt": prompt,
                            "images": [f"rum_design_{i+1}.png" for i in range(dl_count)]
                        }
                        with open(os.path.join(batch_output_dir, "metadata.json"), "w", encoding="utf-8") as meta_f:
                            json.dump(meta_data, meta_f, indent=4, ensure_ascii=False)
                            
                        add_log(f"🎉 Batch {batch_num} slutförd framgångsrikt!")
                    else:
                        add_log("⚠️ Kunde inte hämta genererade bilder från chatten automatiskt.")
                        # Save empty metadata to record the attempt
                        meta_data = {
                            "timestamp": datetime.now().isoformat(),
                            "theme": theme,
                            "furniture_items": curated_product_names,
                            "style_reference": os.path.basename(req.style_image_path),
                            "prompt": prompt,
                            "images": []
                        }
                        with open(os.path.join(batch_output_dir, "metadata.json"), "w", encoding="utf-8") as meta_f:
                            json.dump(meta_data, meta_f, indent=4, ensure_ascii=False)
                            
                    # Clean up conversation / Start a new chat for the next batch to keep context clean
                    try:
                        new_chat_btn = page.locator("a[href='/app'], button[aria-label*='New chat'], button[aria-label*='Ny chatt']").first
                        if await new_chat_btn.count() > 0:
                            await new_chat_btn.click()
                            add_log("Startar ny ren chattinför nästa batch...")
                            await asyncio.sleep(4)
                    except Exception:
                        pass
                        
                    # Cooldown delay between loops to prevent throttling
                    if batch_idx < total_batches - 1:
                        cooldown_secs = 20
                        add_log(f"Låter Gemini svalna. Väntar {cooldown_secs} sekunder inför nästa rum...")
                        await asyncio.sleep(cooldown_secs)
                
                state["progress"] = 100
                await asyncio.sleep(4)
                await context.close()
                state["status"] = "idle"
                add_log("🎉 Automatiseringsprocess slutförd!")
                
        except Exception as e:
            add_log(f"🔴 Fel under batchkörning: {str(e)}")
        finally:
            state["status"] = "idle"
            state["progress"] = 0
            state["browser_running"] = False
            add_log("✅ System redo. Du kan starta en ny batchkörning.")

    asyncio.create_task(run_automation())
    return {"status": "started"}

@app.post("/api/stop")
async def stop_generation_endpoint():
    state["stop_requested"] = True
    state["status"] = "idle"
    add_log("Användaren avbröt batch-processen.")
    return {"status": "stopping"}

@app.get("/api/outputs")
async def get_outputs():
    # Scan outputs folders dynamically and read metadata
    batches = []
    if os.path.exists(OUTPUT_DIR):
        for entry in os.listdir(OUTPUT_DIR):
            entry_path = os.path.join(OUTPUT_DIR, entry)
            if os.path.isdir(entry_path) and entry.startswith("rum_"):
                meta_path = os.path.join(entry_path, "metadata.json")
                
                # Default values
                meta_data = {
                    "theme": "Interiör",
                    "timestamp": entry,
                    "furniture_items": [],
                    "images": []
                }
                
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta_data = json.load(f)
                    except Exception:
                        pass
                
                # Check for actual images in the directory
                valid_exts = (".png", ".jpg", ".jpeg", ".webp")
                actual_images = [f for f in os.listdir(entry_path) if f.lower().endswith(valid_exts) and not f.startswith("00")]
                
                # List of furniture thumbs copied
                furniture_dir = os.path.join(entry_path, "furniture")
                furniture_thumbs = []
                if os.path.exists(furniture_dir):
                    furniture_thumbs = [f for f in os.listdir(furniture_dir) if f.lower().endswith(valid_exts)]
                
                batches.append({
                    "id": entry,
                    "theme": meta_data.get("theme", "Interiör"),
                    "timestamp": meta_data.get("timestamp", entry),
                    "furniture_items": meta_data.get("furniture_items", []),
                    "furniture_thumbs": furniture_thumbs,
                    "images": actual_images
                })
                
    # Sort by directory creation time (newest first)
    batches.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x["id"])), reverse=True)
    return {"batches": batches}

def is_orchestrator_running() -> bool:
    # 1. Check our subprocess object
    global orchestrator_process
    if orchestrator_process and orchestrator_process.returncode is None:
        return True
    
    # 2. Check PID file and verify process is active on Windows
    pid_file = os.path.join(os.path.dirname(BASE_DIR), "orchestrator", "orchestrator.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r', encoding='utf-8') as f:
                pid = int(f.read().strip())
            # Query process using ctypes
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
        except Exception:
            pass
    return False

def get_orchestrator_logs(num_lines: int = 15) -> List[str]:
    log_path = os.path.join(os.path.dirname(BASE_DIR), "orchestrator", "orchestrator.log")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-num_lines:]]
        except Exception:
            pass
    return []

def get_triage_status() -> Optional[Dict[str, Any]]:
    status_path = os.path.join(os.path.dirname(BASE_DIR), "orchestrator", "status.json")
    if os.path.exists(status_path):
        try:
            with open(status_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None

@app.get("/api/orchestrator/status")
async def get_orchestrator_status_endpoint():
    return {
        "running": is_orchestrator_running(),
        "logs": get_orchestrator_logs(),
        "triage": get_triage_status()
    }

@app.post("/api/orchestrator/start")
async def start_orchestrator_endpoint():
    global orchestrator_process
    if is_orchestrator_running():
        return {"status": "already_running"}
        
    python_exe = r"C:\Users\AndronikLindgren\miniconda3\python.exe"
    if not os.path.exists(python_exe):
        python_exe = "python"
        
    orchestrator_dir = os.path.join(os.path.dirname(BASE_DIR), "orchestrator")
    loop_py = os.path.join(orchestrator_dir, "loop.py")
    
    try:
        # Start loop runner in background asynchronously without blocking FastAPI
        # Cwd is the project root to ensure loop configs resolve config.py properly
        orchestrator_process = await asyncio.create_subprocess_exec(
            python_exe, loop_py,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=orchestrator_dir
        )
        return {"status": "started", "pid": orchestrator_process.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kunde inte starta loop: {e}")

@app.post("/api/orchestrator/stop")
async def stop_orchestrator_endpoint():
    global orchestrator_process
    
    terminated = False
    if orchestrator_process and orchestrator_process.returncode is None:
        try:
            orchestrator_process.terminate()
            await orchestrator_process.wait()
            terminated = True
        except Exception:
            pass
            
    # Try backup kill using PID file
    pid_file = os.path.join(os.path.dirname(BASE_DIR), "orchestrator", "orchestrator.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r', encoding='utf-8') as f:
                pid = int(f.read().strip())
            import os
            import signal
            os.kill(pid, signal.SIGTERM)
            terminated = True
        except Exception:
            pass
            
    if terminated:
        return {"status": "stopped"}
    return {"status": "not_running"}


import os
import sys
import base64
import json
import asyncio
import sqlite3
import random
import logging
import shutil
import urllib.request
import re
from playwright.async_api import async_playwright
import win32crypt
import win32file
import win32con
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Reconfigure stdout/stderr to UTF-8 to prevent encoding crashes on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("gemini-recovery")

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

def get_browser_cookies():
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
            
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = json.loads(f.read())
            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            encrypted_key = encrypted_key[5:]
            decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        except Exception as e:
            logger.warning(f"Could not decrypt key for {name}: {e}")
            continue
            
        for cookies_path in paths["profiles"]:
            if not os.path.exists(cookies_path):
                continue
                
            temp_path = os.path.join(os.getcwd(), f"temp_cookies_db_{random.randint(1000, 9999)}")
            try:
                copied = win32_copy_locked_file(cookies_path, temp_path)
                if not copied:
                    # try powershell fallback
                    import subprocess
                    cmd = f'powershell -Command "Copy-Item -Path \'{cookies_path}\' -Destination \'{temp_path}\' -Force"'
                    subprocess.run(cmd, shell=True, capture_output=True)
                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        copied = True
                if not copied:
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
                        if encrypted_value.startswith(b'v10') or encrypted_value.startswith(b'v11'):
                            iv = encrypted_value[3:15]
                            ciphertext = encrypted_value[15:]
                            aesgcm = AESGCM(decrypted_key)
                            value = aesgcm.decrypt(ciphertext, iv, None).decode('utf-8')
                        else:
                            value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
                            
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
                logger.info(f"Read {count} cookies from {name}!")
            except Exception as e:
                logger.warning(f"Could not read cookies from path: {e}")
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                        
    return cookies_list

async def run_recovery():
    print("="*60)
    print("RECOVERY OF GENERATED IMAGES FROM GEMINI ADVANCED HISTORY")
    print("="*60)
    
    async with async_playwright() as p:
        # Launch browser headfully
        launch_kwargs = {
            "headless": False,
            "args": ["--start-maximized", "--disable-blink-features=AutomationControlled"]
        }
        
        # Check if Chrome is available
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        for p_chk in paths:
            if os.path.exists(p_chk):
                launch_kwargs["channel"] = "chrome"
                break
                
        context = await p.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.getcwd(), "temp_browser_profile"),
            **launch_kwargs
        )
        
        # Try loading cookies
        cookies = get_browser_cookies()
        if cookies:
            await context.add_cookies(cookies)
            print(f"Loaded {len(cookies)} cookies into the browser context.")
            
        page = await context.new_page()
        page.set_default_timeout(60000)
        
        print("Navigating to Gemini Advanced...")
        await page.goto("https://gemini.google.com/app")
        
        # Inject a instructions banner at the top
        try:
            await page.evaluate("""() => {
                const checkExist = setInterval(() => {
                    if (document.body) {
                        clearInterval(checkExist);
                        const banner = document.createElement('div');
                        banner.id = 'recovery-banner';
                        banner.style.position = 'fixed';
                        banner.style.top = '0';
                        banner.style.left = '0';
                        banner.style.width = '100%';
                        banner.style.backgroundColor = '#d9534f';
                        banner.style.color = 'white';
                        banner.style.textAlign = 'center';
                        banner.style.padding = '15px';
                        banner.style.fontSize = '18px';
                        banner.style.fontWeight = 'bold';
                        banner.style.zIndex = '99999';
                        banner.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
                        banner.innerHTML = 'ÅTERSTÄLLNING PÅGÅR: Vänligen logga in på ditt Google-konto i detta fönster, stäng eventuella popup-rutor, och låt din chatthistorik laddas i sidomenyn.';
                        document.body.appendChild(banner);
                    }
                }, 100);
            }""")
        except Exception as e_banner:
            print(f"Could not inject banner: {e_banner}")

        # Wait for user to be logged in and chat history to load
        print("Waiting for chat history sidebar and chat links to load...")
        chat_links = []
        for attempt in range(120): # Wait up to 4 minutes
            # Check URL to see if logged in
            url = page.url
            if "accounts.google.com" in url or "signin" in url:
                print(f"  [Waiting] Please log in to Google (Attempt {attempt+1}/120)...")
                await asyncio.sleep(3)
                continue
                
            # Scan for links in the sidebar
            links = await page.locator("a[href*='/chat/']").all()
            if len(links) > 0:
                print(f"Detected {len(links)} chat links in the sidebar!")
                for l in links:
                    href = await l.get_attribute("href")
                    text = (await l.inner_text()).strip()
                    aria_lbl = await l.get_attribute("aria-label")
                    clean_text = text.replace('\n', ' ').strip()
                    
                    if href not in [c["href"] for c in chat_links]:
                        chat_links.append({
                            "href": href,
                            "text": clean_text or aria_lbl or href.split('/')[-1]
                        })
                if len(chat_links) > 0:
                    break
            else:
                print(f"  [Waiting] Loading chat history (Attempt {attempt+1}/120)...")
            await asyncio.sleep(3)
            
        if not chat_links:
            print("No chat sessions found in history. Sidebar might be collapsed or empty. Aborting.")
            await context.close()
            return
            
        print(f"Found {len(chat_links)} chat sessions in history:")
        for idx, chat in enumerate(chat_links):
            print(f"[{idx+1}] Href: {chat['href']} | Text: {chat['text']}")

        output_root = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-Full-Catalog-sortering\recovered_images"
        os.makedirs(output_root, exist_ok=True)
        print(f"Created output directory: {output_root}")
        
        # Loop through and scan each chat
        print("\nStarting image recovery from chats...")
        total_recovered = 0
        
        for i, chat in enumerate(chat_links[:40]):
            href = chat["href"]
            title = chat["text"]
            title_clean = "".join(c for c in title if c.isalnum() or c in " -_()").strip()
            if not title_clean:
                title_clean = f"Chat_{i+1}"
                
            print(f"\n[{i+1}/{len(chat_links)}] Accessing chat: '{title_clean}' ({href})")
            
            chat_url = f"https://gemini.google.com{href}"
            try:
                await page.goto(chat_url)
                await asyncio.sleep(6)
                
                images = await page.locator("img[src*='googleusercontent.com']").all()
                print(f"  Found {len(images)} total images in this page.")
                
                img_urls = []
                for img in images:
                    src = await img.get_attribute("src")
                    if src:
                        is_icon = False
                        for tiny_size in ["=s16", "=s24", "=s32", "=s48", "=s64", "=w16", "=w24", "=w32"]:
                            if tiny_size in src:
                                is_icon = True
                                break
                        if not is_icon:
                            high_res = src
                            if "=" in src:
                                high_res = src.split("=")[0] + "=s0"
                            if high_res not in img_urls:
                                img_urls.append(high_res)
                                
                if img_urls:
                    print(f"  Found {len(img_urls)} high-res generated images in chat '{title_clean}':")
                    chat_folder = os.path.join(output_root, title_clean)
                    os.makedirs(chat_folder, exist_ok=True)
                    
                    for img_idx, url in enumerate(img_urls):
                        try:
                            file_name = f"recovered_{img_idx+1}.png"
                            dest_path = os.path.join(chat_folder, file_name)
                            
                            print(f"    Downloading {file_name}...")
                            urllib.request.urlretrieve(url, dest_path)
                            total_recovered += 1
                        except Exception as e_dl:
                            print(f"    [!] Error downloading {url}: {e_dl}")
                else:
                    print("  No high-res generated images found in this chat.")
                    
            except Exception as e_chat:
                print(f"  [!] Error loading chat: {e_chat}")
                
        print("\n" + "="*60)
        print(f"RECOVERY COMPLETE! Recovered {total_recovered} images.")
        print(f"Stored in: {output_root}")
        print("="*60)
        
        await asyncio.sleep(5)
        await context.close()

if __name__ == "__main__":
    asyncio.run(run_recovery())

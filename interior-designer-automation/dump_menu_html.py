import asyncio
import os
import sys
from playwright.async_api import async_playwright

PROFILE_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\interior-designer-automation\browser_profile"
OUTPUT_TXT = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\interior-designer-automation\menu_html_output.txt"

def clear_browser_locks():
    try:
        lock_file = os.path.join(PROFILE_DIR, "lockfile")
        if os.path.exists(lock_file):
            os.remove(lock_file)
            print("Cleared browser profile lockfile.")
    except Exception as e:
        print(f"Could not clear browser profile lockfile: {e}")
        
    try:
        lock_file_default = os.path.join(PROFILE_DIR, "Default", "LOCK")
        if os.path.exists(lock_file_default):
            os.remove(lock_file_default)
            print("Cleared Default browser profile LOCK.")
    except Exception as e:
        print(f"Could not clear Default browser profile LOCK: {e}")

async def main():
    clear_browser_locks()
    
    async with async_playwright() as p:
        print("Launching persistent context (headless=False)...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        page.set_default_timeout(30000)
        
        print("Navigating to Gemini...")
        await page.goto("https://gemini.google.com/app")
        await asyncio.sleep(8)
        
        current_url = page.url.lower()
        print(f"Current URL: {current_url}")
        
        # Let's locate the upload button
        upload_btn = page.locator(
            "button[aria-label*='upload' i], button[aria-label*='ladda upp' i], "
            "button[aria-label*='attach' i], button[aria-label*='bifoga' i], "
            "button[aria-label*='add file' i], button[aria-label*='lägg till' i], "
            "button[aria-label*='fil' i], button[aria-label*='plus' i], "
            "button:has-text('+')"
        ).first
        
        with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
            f.write(f"Diagnostics run at: {current_url}\n")
            
            if await upload_btn.count() > 0:
                aria = await upload_btn.get_attribute("aria-label")
                f.write(f"Found upload button with aria-label: '{aria}'\n")
                print(f"Found upload button with aria-label: '{aria}'. Clicking it...")
                await upload_btn.click()
                await asyncio.sleep(4)
                
                # Get the HTML of the body
                html_content = await page.content()
                f.write("\n--- HTML content of the page ---\n")
                f.write(html_content)
                
                print("HTML content dumped successfully.")
            else:
                f.write("Could not find upload button!\n")
                print("Could not find upload button!")
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())

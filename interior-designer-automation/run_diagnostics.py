import asyncio
import os
import sys
from playwright.async_api import async_playwright

PROFILE_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\interior-designer-automation\browser_profile"
OUTPUT_TXT = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\interior-designer-automation\diagnostics_output.txt"

async def main():
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
        
        # Check if we are signed in
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
                
                # Capture all elements in the DOM that are part of the menu
                f.write("\n--- Dump of elements in the DOM ---\n")
                
                # Check for dialogs, overlays, menus, role='menuitem', etc.
                elements = await page.locator("div, button, li, a, span, g-menu-item").all()
                f.write(f"Total elements scanned: {len(elements)}\n")
                
                menu_elements = []
                for idx, el in enumerate(elements):
                    try:
                        # Check if visible
                        visible = await el.is_visible()
                        if not visible:
                            continue
                            
                        txt = await el.inner_text()
                        aria_lbl = await el.get_attribute("aria-label")
                        role = await el.get_attribute("role")
                        tag = await el.evaluate("el => el.tagName")
                        classes = await el.get_attribute("class")
                        
                        txt_strip = txt.strip().replace('\n', ' ') if txt else ""
                        
                        # We want elements that are likely part of the dropdown
                        # Usually, when a menu opens, new elements appear, or elements have role='menuitem'
                        # or contain words like 'dator', 'computer', 'upload', 'ladda upp'
                        is_likely_menu = False
                        if role in ['menuitem', 'option', 'button']:
                            is_likely_menu = True
                        if any(kw in txt_strip.lower() for kw in ['dator', 'computer', 'ladda upp', 'upload', 'enhet', 'drive', 'photo']):
                            is_likely_menu = True
                        if classes and any(c in classes.lower() for c in ['menu', 'dropdown', 'popup', 'dialog']):
                            is_likely_menu = True
                            
                        if is_likely_menu:
                            menu_elements.append({
                                "tag": tag,
                                "class": classes,
                                "role": role,
                                "text": txt_strip,
                                "aria": aria_lbl
                            })
                    except Exception as e:
                        pass
                
                f.write(f"Found {len(menu_elements)} likely menu/upload elements:\n")
                for me in menu_elements:
                    f.write(f"Tag: {me['tag']}, Role: {me['role']}, Class: {me['class']}, Text: '{me['text']}', Aria: '{me['aria']}'\n")
                    
                # Take a screenshot to verify
                screenshot_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\interior-designer-automation\outputs\diag_after_click.png"
                await page.screenshot(path=screenshot_path)
                f.write(f"\nScreenshot saved to: {screenshot_path}\n")
                print("Diagnostics done, screenshot saved.")
            else:
                f.write("Could not find upload button!\n")
                print("Could not find upload button!")
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())

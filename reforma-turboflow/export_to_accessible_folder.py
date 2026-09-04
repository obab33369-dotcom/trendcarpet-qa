import os
import shutil
import sys
import re

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_short_filename(filename: str) -> str:
    """
    Generates a short filename based on the leading numeric ID.
    E.g. "0257_matbord-fager-135cm-natur-1-26U-wonder.webp" -> "0257.webp"
    """
    base, ext = os.path.splitext(filename)
    match = re.match(r'^(\d+)_', base)
    if match:
        return f"{match.group(1)}{ext}"
    return filename

def main():
    src_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_furniture"
    csv_src = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready.csv"
    json_src = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready.json"
    txt_src = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready.txt"
    prompts_only_src = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\prompts_only.txt"
    prompt_28_src = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\prompt_28.txt"
    log_src = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_tracking_log.csv"
    dest_dir = r"C:\Users\AndronikLindgren\reforma_automation\turboflow_test_batch"

    print(f"🚀 Creating accessible TurboFlow export directory: {dest_dir}")
    os.makedirs(dest_dir, exist_ok=True)

    # Clear destination folder first to prevent old long-named clutter
    print(f"🧹 Clearing destination folder to prevent file clutter...")
    for filename in os.listdir(dest_dir):
        file_path = os.path.join(dest_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"⚠️ Failed to delete {file_path}. Reason: {e}")

    # Copy CSV
    dest_csv = os.path.join(dest_dir, "turboflow_ready.csv")
    print(f"📦 Copying CSV file: {csv_src} -> {dest_csv}")
    if os.path.exists(csv_src):
        shutil.copy(csv_src, dest_csv)
    else:
        print(f"❌ Warning: CSV source file not found at {csv_src}!")

    # Copy Flat JSON
    dest_json = os.path.join(dest_dir, "turboflow_ready.json")
    print(f"📦 Copying Flat JSON file: {json_src} -> {dest_json}")
    if os.path.exists(json_src):
        shutil.copy(json_src, dest_json)
    else:
        print(f"❌ Warning: JSON source file not found at {json_src}!")

    # Copy TXT
    dest_txt = os.path.join(dest_dir, "turboflow_ready.txt")
    print(f"📦 Copying TXT file: {txt_src} -> {dest_txt}")
    if os.path.exists(txt_src):
        shutil.copy(txt_src, dest_txt)
    else:
        print(f"❌ Warning: TXT source file not found at {txt_src}!")
        
    # Copy Prompts-Only TXT
    dest_prompts_only = os.path.join(dest_dir, "prompts_only.txt")
    print(f"📦 Copying Prompts-Only TXT file: {prompts_only_src} -> {dest_prompts_only}")
    if os.path.exists(prompts_only_src):
        shutil.copy(prompts_only_src, dest_prompts_only)
    else:
        print(f"❌ Warning: Prompts-Only source file not found at {prompts_only_src}!")

    # Copy Prompt 28 TXT
    dest_prompt_28 = os.path.join(dest_dir, "prompt_28.txt")
    print(f"📦 Copying Prompt 28 file: {prompt_28_src} -> {dest_prompt_28}")
    if os.path.exists(prompt_28_src):
        shutil.copy(prompt_28_src, dest_prompt_28)
    else:
        print(f"❌ Warning: Prompt 28 source file not found at {prompt_28_src}!")

    # Copy 10 prompt partition chunks
    print("📦 Copying the 10 prompt partition chunk files...")
    for part in range(1, 11):
        chunk_fname = f"prompts_chunk_{part}.txt"
        chunk_src = os.path.join(r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow", chunk_fname)
        chunk_dest = os.path.join(dest_dir, chunk_fname)
        if os.path.exists(chunk_src):
            shutil.copy(chunk_src, chunk_dest)
            print(f"   ✓ Copied {chunk_fname} -> {chunk_dest}")
        else:
            print(f"   ❌ Warning: {chunk_fname} not found at {chunk_src}!")

    # Copy Tracking Log spreadsheet
    dest_log = os.path.join(dest_dir, "turboflow_tracking_log.csv")
    print(f"📦 Copying Excel-compatible Tracking Spreadsheet: {log_src} -> {dest_log}")
    if os.path.exists(log_src):
        try:
            shutil.copy(log_src, dest_log)
        except PermissionError:
            fallback_dest = os.path.join(dest_dir, "turboflow_tracking_log_NEW.csv")
            print(f"⚠️ Warning: The spreadsheet file at '{dest_log}' is locked (probably open in Microsoft Excel).")
            print(f"   Saving a copy to fallback file: '{fallback_dest}'")
            shutil.copy(log_src, fallback_dest)
        except Exception as e:
            print(f"❌ Failed to copy tracking spreadsheet: {e}")
    else:
        print(f"❌ Warning: Tracking log source file not found at {log_src}!")

    # Copy Auto-Tagging script helper
    js_src = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\autotag_script.js"
    dest_js = os.path.join(dest_dir, "autotag_script.js")
    dest_txt_script = os.path.join(dest_dir, "autotag_script.txt")
    print(f"📦 Copying Auto-Tagging JS script: {js_src} -> {dest_js} & {dest_txt_script}")
    if os.path.exists(js_src):
        shutil.copy(js_src, dest_js)
        shutil.copy(js_src, dest_txt_script)
    else:
        print(f"❌ Warning: Auto-tagging JS source not found at {js_src}!")

    # Copy and rename all images
    print("🖼️ Copying and renaming furniture images to short [ID].webp format...")
    copied_count = 0
    if not os.path.exists(src_dir):
        print(f"❌ Error: Source images directory not found at {src_dir}!")
        sys.exit(1)
        
    for filename in os.listdir(src_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            short_name = get_short_filename(filename)
            src_file = os.path.join(src_dir, filename)
            dest_file = os.path.join(dest_dir, short_name)
            shutil.copy(src_file, dest_file)
            copied_count += 1

    # Copy and rename all rugs
    rugs_src_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_rugs"
    print("🖼️ Copying and renaming rug images to short [ID].webp format...")
    rugs_copied_count = 0
    if os.path.exists(rugs_src_dir):
        for filename in os.listdir(rugs_src_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                short_name = get_short_filename(filename)
                src_file = os.path.join(rugs_src_dir, filename)
                dest_file = os.path.join(dest_dir, short_name)
                shutil.copy(src_file, dest_file)
                rugs_copied_count += 1
                copied_count += 1
    else:
        print(f"⚠️ Warning: Rugs source directory not found at {rugs_src_dir}!")

    print(f"\n🎉 SUCCESS!")
    print(f"All {copied_count} test images ({copied_count - rugs_copied_count} furniture, {rugs_copied_count} rugs) renamed to short IDs and TurboFlow batch files copied to:")
    print(f"👉 {dest_dir}")
    print("\nThis folder is fully visible and non-hidden. You can now:")
    print("1. Empty your TurboFlow Image Library.")
    print("2. Drag and drop the newly renamed short webp files (e.g. 0217.webp, 0257.webp) into TurboFlow.")
    print("3. Upload 'turboflow_ready.txt' (or .csv/.json) for perfect auto-matching without manual tagging!")
    print("4. Open 'turboflow_tracking_log.csv' directly in Excel to trace which furniture is on which row!")

if __name__ == "__main__":
    main()

import os
import json
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
prompt_db_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'rooms_turboflow_full_catalog.json')
carpet_debug_path = os.path.join(WORKSPACE_DIR, 'scratch', 'carpet_debug_details.txt')

# We want to read carpet_debug_details.txt and extract specific sections.
with open(carpet_debug_path, 'r', encoding='utf-8') as f:
    content = f.read()

sections = content.split("=" * 100)
flagged_folders = [
    "Matta Belden - Grön (RG01-74)",
    "Matta Aureline - BeigeBrun (RG01-8)",
    "Matta Avendo - Röd (RG01-75)",
    "Matta Aureline BeigeGrå (RG01-7)",
    "Matta Belden - Röd (RG01-73)",
    "Matta Aureline - Grön (RG01-9)",
    "Matta Arvella - RödGrön (RG01-65)",
    "Matta Calvera - Grå (RG01-35)",
    "Matta Avendo - GulBeige (RG01-76)",
    "Matta Aravelle - Multi (RG01-20)",
    "Matta Carrano - SvartVit (RG01-70)",
    "Matta Calvera - Röd (RG01-34)",
    "Matta Ventaro - GrönGul (RG01-91)",
    "Matta Carrano - GråVit (RG01-72)",
    "Matta Ventaro - RosaBrun (RG01-90)",
    "Matta Ventaro - Multi (RG01-87)",
    "Matta Ängelholm - GråBlå (RG002)",
    "Matta Ängelholm - Grön (RG00)",
    "Matta Carrano - Grön (RG01-71)",
    "Matta Ängelholm - Mörkbrun (RG001)",
    "Ryamatta Aranga Super Soft Fur Rosa (H100017)"
]

for folder in flagged_folders:
    found = False
    for sec in sections:
        if folder in sec:
            print("=" * 60)
            print(sec.strip()[:1500]) # print first 1500 chars of section
            print("...")
            found = True
            break
    if not found:
        print(f"Folder {folder} not found in debug details.")

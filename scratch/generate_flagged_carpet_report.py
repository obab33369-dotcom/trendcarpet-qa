import os
import json

PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ARTIFACTS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec"

def main():
    json_path = os.path.join(PROJECT_DIR, "scratch", "carpet_mismatch_report.json")
    if not os.path.exists(json_path):
        print(f"JSON data not found at {json_path}")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        mismatches = json.load(f)
        
    md_path = os.path.join(ARTIFACTS_DIR, "carpet_flagged_folders_report.md")
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Rapport: Flaggade Mattmappar med Felaktiga Referenser\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> Följande **21 mattmappar** fick **0 godkända bilder** efter Geminis granskning. ")
        f.write("Detta beror på att referensbilden i mappen inte stämmer överens med de rumsscener ")
        f.write("som faktiskt renderades av Turboflow. Detta är en sammanställning av de visuella granskningarna ")
        f.write("gjorda av Gemini för att visa vad som blev fel.\n\n")
        
        f.write("## Sammanfattningstabell\n\n")
        f.write("| Produktmapp | Förväntad SKU | Analys av renderat innehåll | Status |\n")
        f.write("| :--- | :---: | :--- | :---: |\n")
        
        for folder, analysis in sorted(mismatches.items()):
            # Extract SKU
            import re
            m = re.search(r'\(([^)]+)\)', folder)
            sku = m.group(1) if m else "Okänd"
            
            # Short summary of the analysis for the table
            short_desc = "Okänd avvikelse"
            analysis_lower = analysis.lower()
            if "completely different designs" in analysis_lower or "helt olika" in analysis_lower or "different designs" in analysis_lower:
                short_desc = "Helt annan design renderad"
            elif "color mismatch" in analysis_lower or "färgavvikelse" in analysis_lower or "mismatch is primarily in color" in analysis_lower:
                short_desc = "Rätt design, fel färg"
            elif "scalloped" in analysis_lower or "wavy" in analysis_lower:
                short_desc = "Visar vågig/skalloperad matta (Aureline/Arvella)"
            elif "checkerboard" in analysis_lower:
                short_desc = "Visar schackrutigt mönster (Carrano)"
            elif "geometric" in analysis_lower:
                short_desc = "Visar geometriskt mönster (Arvella/Sorvento)"
                
            f.write(f"| {folder} | `{sku}` | {short_desc} | 🚩 Flaggad |\n")
            
        f.write("\n---\n\n## Detaljerad granskning per mapp\n\n")
        
        for folder, analysis in sorted(mismatches.items()):
            f.write(f"### 🚩 {folder}\n\n")
            
            # Highlight key parts of the analysis with markdown formatting
            formatted_analysis = analysis.replace("1.", "\n* **Förväntad referensdesign:**").replace("2.", "* **Faktiskt renderad design i bild:**").replace("3.", "* **Mönster- / färgavvikelse:**").replace("4.", "* **Slutsats:**")
            
            f.write(formatted_analysis + "\n\n")
            f.write("*(Bilderna har flyttats till borttagna-mappen i väntan på korrigering av källmaterialet)*\n\n")
            f.write("---\n\n")
            
    print(f"Created markdown report at {md_path}")

if __name__ == "__main__":
    main()

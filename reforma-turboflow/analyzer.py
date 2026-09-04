import os
import sys
import json
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from PIL import Image

# Configure standard streams to use UTF-8 to prevent Unicode encoding issues in Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Define Pydantic schema for structured Gemini API response
class FurnitureMetadata(BaseModel):
    typ_av_möbel: str = Field(
        description="Categorization of the furniture. Must be one of: 'bord', 'stol', 'matta', 'förvaring'."
    )
    träslag: str = Field(
        description="Wood type or primary structural material. Use one of these specific values: 'ek' (oak), 'valnöt' (walnut), 'furu' (pine), 'ask' (ash), 'svart metall' (black metal/steel), 'marmor' (marble), 'natur' (light natural wood), 'mörkbrun' (dark brown), 'vit' (painted white), 'inget' (no wood/structural visible)."
    )
    tyg_material: str = Field(
        description="Fabric, upholstery, or texture material. Use one of: 'bouclé', 'rotting' (rattan/caning), 'läder' (leather), 'ull' (wool/rug fabric), 'inget' (no fabric), 'sammet' (velvet), 'textil' (generic fabric/linen)."
    )
    färgton: str = Field(
        description="Color temperature / harmony. Must be either 'varm' (warm colors like cream, brown, gold, walnut, beige) or 'kall' (cool colors like grey, black, white, steel, blue, cool green)."
    )
    stil_estetik: str = Field(
        description="Interior design aesthetic style. Choose the most fitting: 'nordisk modern' (clean Scandinavian modern), 'rustik' (rustic, raw wood, industrial), 'klassisk' (traditional bistro or classic curves), 'minimalistisk' (ultra-sleek, clean geometric lines)."
    )

def main():
    # Load API key
    env_path = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"
    if not os.path.exists(env_path):
        print(f"Error: API key file not found at {env_path}")
        sys.exit(1)
        
    load_dotenv(env_path)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in env variables.")
        sys.exit(1)
        
    # Initialize modern Google GenAI Client
    print("Initializing Gemini API Client...")
    client = genai.Client(api_key=api_key)
    
    # Get target directory from arguments or default to test_furniture
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(script_dir, "test_furniture")
    if "--full" in sys.argv:
        target_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
        
    print(f"Scanning directory: {target_dir}")
    if not os.path.exists(target_dir):
        print(f"Error: Directory {target_dir} does not exist.")
        sys.exit(1)
        
    # Load existing database if present to support resuming
    db_path = os.path.join(script_dir, "furniture_db.json")
    database = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                database = json.load(f)
            print(f"Loaded existing database with {len(database)} analyzed items.")
        except Exception as e:
            print(f"Warning: Could not parse database {db_path}: {e}. Starting fresh.")
            
    valid_exts = ('.png', '.jpg', '.jpeg', '.webp')
    all_files = [f for f in os.listdir(target_dir) if f.lower().endswith(valid_exts)]
    
    # Filter files to analyze (skip already analyzed ones)
    files_to_analyze = [f for f in all_files if f not in database]
    
    # Check for limit argument
    limit_val = None
    for arg in sys.argv:
        if arg.startswith("--limit="):
            try:
                limit_val = int(arg.split("=")[1].strip())
            except ValueError:
                pass
                
    if limit_val is not None:
        files_to_analyze = files_to_analyze[:limit_val]
        print(f"Limiting analysis to first {limit_val} new images.")
        
    print(f"Found {len(all_files)} total images. {len(files_to_analyze)} need to be analyzed.")
    
    if not files_to_analyze:
        print("No new images to analyze or already at limit. Done!")
        return
        
    # Start analysis loop
    print("Starting visual analysis batch via Gemini 2.5 Flash...")
    count = 0
    total = len(files_to_analyze)
    
    for filename in files_to_analyze:
        filepath = os.path.join(target_dir, filename)
        count += 1
        print(f"[{count}/{total}] Analyzing: {filename}...")
        
        try:
            # Load image with Pillow
            img = Image.open(filepath)
            
            # Formulate detailed prompt for Gemini vision
            prompt = (
                "You are an expert Scandinavian interior designer and product catalog curator. "
                "Analyze this product image and extract its properties precisely. "
                "Classify the category (typ_av_möbel), wood or structural material type (träslag), "
                "upholstery or texture material (tyg_material), color temperature tone (färgton), "
                "and design style (stil_estetik). Use only the allowed values described in the schema."
            )
            
            # Send direct content generation request with structured Pydantic schema
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[img, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FurnitureMetadata,
                    temperature=0.1
                )
            )
            
            # The response.text is guaranteed to be a valid JSON matching our Pydantic schema
            result_dict = json.loads(response.text)
            
            # Store in database
            database[filename] = {
                "filename": filename,
                "parsed_name": filename, # Setup placeholder
                "metadata": result_dict,
                "timestamp": time.time()
            }
            
            # Real-time database flushing to prevent data loss
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(database, f, ensure_ascii=False, indent=2)
                
            print(f"  -> Extracted: {result_dict}")
            
            # Polite rate-limiting to be safe
            time.sleep(1.0)
            
        except Exception as e:
            print(f"❌ Error analyzing {filename}: {e}")
            # Optional: Sleep slightly longer on error to recover from potential rate-limiting
            time.sleep(3.0)
            
    print(f"✓ Analysis complete! Database saved with {len(database)} items to {db_path}")

if __name__ == "__main__":
    main()

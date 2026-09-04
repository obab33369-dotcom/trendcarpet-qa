import os
import zipfile

zip_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\cut out-cowhide.zip"
extract_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cut_out_cowhide"

os.makedirs(extract_dir, exist_ok=True)

if not os.path.exists(zip_path):
    print(f"Error: Zip file not found at {zip_path}")
    sys.exit(1)

print(f"Extracting {zip_path} to {extract_dir}...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

print("Extraction completed successfully!")

# List the extracted files to see what they look like
extracted_files = []
for root, dirs, files in os.walk(extract_dir):
    for f in files:
        if not f.startswith('.'):
            extracted_files.append(os.path.join(root, f))

print(f"Total files extracted: {len(extracted_files)}")
print("First 15 files:")
for f in sorted(extracted_files)[:15]:
    rel = os.path.relpath(f, extract_dir)
    # Get file stats
    size = os.path.getsize(f)
    print(f"  {rel} ({size/1024:.1f} KB)")

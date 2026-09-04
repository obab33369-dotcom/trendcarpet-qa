import os
import urllib.request

sku = "1100476"
base_url = "https://www.reformasthlm.se/bilder/artiklar/zoom/"

print("Downloading other slots for Lionel Chair from Reforma site...")
for slot in range(4, 9):
    filename = f"{sku}_{slot}.jpg"
    url = f"{base_url}{filename}"
    dest_path = f"downloaded_{filename}"
    try:
        print(f"Fetching {url} -> {dest_path}...")
        # Add a standard user agent to avoid blocking
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req) as response:
            with open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
        print(f"Successfully downloaded {filename}")
    except Exception as e:
        print(f"Failed to download slot {slot}: {e}")

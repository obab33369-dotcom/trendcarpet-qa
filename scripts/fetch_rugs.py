import urllib.request
import re

url = "https://www.reformasthlm.se/sv/inredning/mattor"
req = urllib.request.Request(
    url, 
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
)

try:
    print(f"Fetching URL: {url}...")
    with urllib.request.urlopen(req, timeout=10) as response:
        html = response.read().decode('utf-8')
    print(f"Success! HTML length: {len(html)}")
    
    # Save a snippet of HTML to look at the product structure
    with open("rugs_snippet.html", "w", encoding="utf-8") as f:
        f.write(html[:100000])
    print("Saved first 100k of HTML to rugs_snippet.html")
    
    # Look for image tags or product card elements in the first 100k
    # Simple regex search to find some image or product indicators
    img_urls = re.findall(r'src="([^"]+)"', html)
    print(f"Found {len(img_urls)} image URLs in total html.")
    for url in img_urls[:10]:
        print(f"  - {url}")

except Exception as e:
    print(f"Error: {e}")

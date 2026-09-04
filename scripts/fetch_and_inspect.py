import urllib.request
import re

url = "https://www.reformasthlm.se/sv/inredning/mattor"
req = urllib.request.Request(
    url, 
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
)

print("Fetching page...")
try:
    with urllib.request.urlopen(req, timeout=15) as response:
        html = response.read().decode('utf-8')
    print(f"Successfully fetched {len(html)} bytes of HTML.")
    
    # Save the html
    with open("reforma_mattor.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved HTML to reforma_mattor.html")
    
    # Find all anchor links
    anchors = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>', html)
    print(f"Total anchor tags found: {len(anchors)}")
    
    # Print sample of anchor links
    print("\nSample anchors (first 50):")
    for a in anchors[:50]:
        print(f"  - {a}")
        
    # Search for image tags
    img_tags = re.findall(r'<img\s+[^>]*src="([^"]+)"[^>]*>', html)
    print(f"\nTotal simple img src found: {len(img_tags)}")
    for img in img_tags[:15]:
        print(f"  - {img}")
        
    # Let's search for lazy-loading image sources
    # Try finding attributes with image file extensions in any tag attribute
    img_urls = re.findall(r'src="([^"]+\.(?:jpg|png|webp|jpeg)[^"]*)"', html)
    print(f"\nTotal src=images found: {len(img_urls)}")
    for iu in img_urls[:15]:
        print(f"  - {iu}")
        
    data_srcs = re.findall(r'data-[a-zA-Z0-9_-]+="([^"]+\.(?:jpg|png|webp|jpeg)[^"]*)"', html)
    print(f"\nTotal data-images found: {len(data_srcs)}")
    for ds in data_srcs[:15]:
        print(f"  - {ds}")
        
except Exception as e:
    print(f"Error: {e}")

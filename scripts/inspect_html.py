import urllib.request
import re

url = "https://www.reformasthlm.se/sv/inredning/mattor"
req = urllib.request.Request(
    url, 
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
)

with urllib.request.urlopen(req, timeout=10) as response:
    html = response.read().decode('utf-8')

# Find all links ending with .html inside /sv/artiklar/
all_links = re.findall(r'href="([^"]*/artiklar/[^"]*\.html)"', html)
print(f"Found {len(all_links)} total links ending in .html")

# Filter out index pages (which represent categories)
product_links = [l for l in all_links if "index.html" not in l]
product_links = list(set(product_links)) # Uniquify

print(f"Found {len(product_links)} unique individual product links!")
print("\nSample Product Links:")
for pl in product_links[:20]:
    print(f"  - {pl}")

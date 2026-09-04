import urllib.request
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

urls = [
    "https://www.reformasthlm.se/sv/stol-midnatt-sammet",
    "https://www.reformasthlm.se/sv/stol-midnatt",
    "https://www.reformasthlm.se/sv/stol-midnatt-svart"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

for url in urls:
    print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        sku = None
        m = re.search(r'itemprop="sku"\s+content="([^"]+)"', html, re.IGNORECASE)
        if m:
            sku = m.group(1)
        if not sku:
            m = re.search(r'"sku":\s*"([^"]+)"', html, re.IGNORECASE)
            if m:
                sku = m.group(1)
                
        if sku:
            print(f"  FOUND SKU: {sku}")
            break
        else:
            print("  SKU not found on page.")
    except Exception as e:
        print(f"  Error: {e}")

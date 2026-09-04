import urllib.request
import re
import sys

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

urls = {
    # Montmartre chairs
    "Montmartre Silver Matt": "https://www.reformasthlm.se/sv/stol-montmartre-silver-matt",
    "Montmartre Svart Patina": "https://www.reformasthlm.se/sv/stol-montmartre-svart-patina",
    "Montmartre Vintage Svart": "https://www.reformasthlm.se/sv/stol-montmartre-vintage-svart",
    "Montmartre Vintage Svart Antik": "https://www.reformasthlm.se/sv/stol-montmartre-vintage-svart-antik",
    "Montmartre Vintage Koppar": "https://www.reformasthlm.se/sv/stol-montmartre-vintage-koppar",
    "Montmartre Vit Lackad": "https://www.reformasthlm.se/sv/stol-montmartre-vit-lackad",
    "Montmartre Rod Lackad": "https://www.reformasthlm.se/sv/stol-montmartre-rod-lackad",
    "Montmartre Rustik Stal": "https://www.reformasthlm.se/sv/stol-montmartre-rustik-stal",
    "Montmartre Gul Lackad": "https://www.reformasthlm.se/sv/stol-montmartre-gul-lackad",
    "Montmartre Svart Lack": "https://www.reformasthlm.se/sv/stol-montmartre-svart-lack",
    "Montmartre Orange Lack": "https://www.reformasthlm.se/sv/stol-montmartre-orange-lack",
    
    # Hydra shelves
    "Hydra 24cm": "https://www.reformasthlm.se/sv/vagghylla-hydra-24-cm-svart",
    "Hydra 114cm": "https://www.reformasthlm.se/sv/vagghylla-hydra-114-cm-svart",
    
    # Oslo stars
    "Oslo 60cm Vit": "https://www.reformasthlm.se/sv/adventstjarna-oslo-60cm-vit",
    "Oslo 60cm Vit Alt": "https://www.reformasthlm.se/sv/adventstjarna-oslo-60-cm-vit",
    "Oslo 65cm Vit": "https://www.reformasthlm.se/sv/adventstjarna-sofie-vit",
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print("--- FETCHING ONLINE SKUs ---")
for name, url in urls.items():
    print(f"\nFetching {name}...")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        # Try to find SKU in JSON-LD or meta tags
        # Format 1: "sku": "..."
        # Format 2: itemprop="sku" content="..."
        # Format 3: data-sku="..."
        
        sku = None
        
        # Look for itemprop="sku"
        m = re.search(r'itemprop="sku"\s+content="([^"]+)"', html, re.IGNORECASE)
        if m:
            sku = m.group(1)
            
        if not sku:
            m = re.search(r'"sku":\s*"([^"]+)"', html, re.IGNORECASE)
            if m:
                sku = m.group(1)
                
        if not sku:
            m = re.search(r'data-sku="([^"]+)"', html, re.IGNORECASE)
            if m:
                sku = m.group(1)
                
        if not sku:
            m = re.search(r'"model":\s*"([^"]+)"', html, re.IGNORECASE)
            if m:
                sku = m.group(1)
                
        if sku:
            print(f"  FOUND SKU: {sku} | URL: {url}")
        else:
            print(f"  Page loaded successfully, but SKU not found in HTML. Check URL: {url}")
            # print some title if possible
            title = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            if title:
                print(f"  Title: {title.group(1)}")
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason} | URL: {url}")
    except Exception as e:
        print(f"  Error: {e} | URL: {url}")

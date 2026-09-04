import re

with open("reforma_mattor.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's find occurrences of class="img-slider test"
product_blocks = re.findall(r'<a\s+class="img-slider test"[^>]*href="([^"]+)"', html)
print(f"Found {len(product_blocks)} products matching class='img-slider test'")

# Let's inspect the HTML of the first 3 product blocks in detail
matches = [m.start() for m in re.finditer(r'<a\s+class="img-slider test"', html)]
for idx, m_start in enumerate(matches[:3]):
    print(f"\n--- Product {idx+1} Block ---")
    print(html[m_start:m_start+1500])

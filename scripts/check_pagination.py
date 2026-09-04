import re

with open("reforma_mattor.html", "r", encoding="latin-1") as f:
    html = f.read()

# Look for pagination links or references to "page" or "p=" or "sida"
pagination_links = re.findall(r'href="([^"]*[\?&](?:page|p|sida)=\d+[^"]*)"', html)
print(f"Pagination links found: {len(pagination_links)}")
for l in list(set(pagination_links)):
    print(f"  - {l}")

# Let's search for any number links or next page buttons
next_pages = re.findall(r'href="([^"]*(?:/mattor|/inredning/mattor)[^"]*(?:\?|\&)[^"]*)"', html)
print(f"Related query links: {len(next_pages)}")
for l in list(set(next_pages))[:15]:
    print(f"  - {l}")

# Let's search for "p=" in the HTML
p_matches = re.findall(r'href="([^"]*[\?&]p=\d+[^"]*)"', html)
print(f"Links with p=: {len(p_matches)}")
for l in list(set(p_matches))[:10]:
    print(f"  - {l}")

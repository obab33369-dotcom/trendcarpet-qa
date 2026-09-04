import re

with open("reforma_mattor.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's search for links that contain "/artiklar/"
artiklar_links = re.findall(r'href="([^"]*/artiklar/[^"]*)"', html)
print(f"Links containing /artiklar/: {len(artiklar_links)}")
for l in list(set(artiklar_links))[:30]:
    print(f"  - {l}")

# Let's inspect the surrounding HTML of one of the /bilder/artiklar/ images to understand the structure
# We can find a product block, which typically contains a link to the product, a title, and an image.
# Let's print out lines around "/bilder/artiklar/" in the HTML
matches = [m.start() for m in re.finditer(r'/bilder/artiklar/[a-zA-Z0-9_-]+\.jpg', html)]
print(f"\nFound {len(matches)} occurrences of /bilder/artiklar/*.jpg")
if matches:
    # Print the 200 characters before and after the first match
    idx = matches[0]
    print("\nSurrounding HTML for first image match:")
    print(html[max(0, idx-500):min(len(html), idx+500)])

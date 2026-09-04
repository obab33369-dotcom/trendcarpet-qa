import re

path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\.system_generated\steps\6975\content.md"
with open(path, errors='ignore') as f:
    content = f.read()

# Find all images in the /bilder/artiklar/ directory
images = set(re.findall(r'/bilder/artiklar/[^\s\"\'\>]+', content))
print("Found images in HTML:")
for img in sorted(images):
    print(img)

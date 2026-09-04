import urllib.request

url = "https://www.reformasthlm.se/sv/inredning/mattor"
req = urllib.request.Request(
    url, 
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
)

with urllib.request.urlopen(req, timeout=10) as response:
    raw = response.read()

# Let's try decoding with latin-1
text_latin1 = raw.decode('latin-1')
print("Latin-1 snippet:")
for m in text_latin1.split('\n'):
    if "Jutematta" in m:
        print(m[:150])
        break

# Let's try decoding with utf-8
text_utf8 = raw.decode('utf-8', errors='replace')
print("UTF-8 snippet:")
for m in text_utf8.split('\n'):
    if "Jutematta" in m:
        print(m[:150])
        break

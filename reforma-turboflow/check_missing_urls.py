import urllib.request
import urllib.error
import ssl

slugs = [
    "karmstol-ebba-brun-2",
    "matgrupp-hornstull-elsa-1-bord-4-stolar",
    "matta-valora-brun",
    "matta-seronis-svart-beige",
    "matbord-pesaro-svart",
    "fatolj-paris-beige"
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("Checking URLs on Reforma...")
for slug in slugs:
    url = f"https://www.reformasthlm.se/sv/{slug}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, context=ctx)
        print(f"EXISTS (200 OK): {slug}")
    except urllib.error.HTTPError as e:
        print(f"FAILED ({e.code}): {slug}")
    except Exception as e:
        print(f"ERROR: {slug} - {e}")

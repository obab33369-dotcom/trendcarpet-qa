import urllib.request
import json

url = "http://localhost:8500/api/start"
payload = {
    "furniture_folder": r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ",
    "style_image_path": r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ\Ryamatta-Zebra-Tufted-Wool-Premium-beige-svart-carpet-teppich-01-Interior-0210.jpg",
    "selected_items": [],
    "prompt_template": "Ett vackert och lyxigt inrett rum med följande möbler: {furniture_list}. Placera dem naturligt och smakfullt.",
    "batch_count": 1,
    "items_per_room": 4,
    "ignore_keywords": "interior, miljo, ambient, livsstil"
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        print("Response status:", response.status)
        print("Response body:", response.read().decode("utf-8"))
except Exception as e:
    print("Failed to trigger start:", e)

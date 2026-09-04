"""
Verify that the fixes in vision_auto_corrector.py are correct:
1. get_target_size() returns correct sizes for each slot
2. ensure_square_canvas() correctly creates square images at target dimensions with category-aware alignment
3. process_and_correct() uses correct canvas sizes
4. check call sites count (expected 8)
"""
import sys
import os
sys.path.insert(0, r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow")

from PIL import Image, ImageDraw
import tempfile

# Test 1: get_target_size
from vision_auto_corrector import get_target_size, ensure_square_canvas

print("=== TEST 1: get_target_size() ===")
tests = [
    (r"C:\test\artiklar\19791.jpg", 1000),
    (r"C:\test\artiklar\liten\19791_S.jpg", 400),
    (r"C:\test\artiklar\zoom\19791_1.jpg", 2000),
    (r"C:/test/artiklar/zoom/19791_2.jpg", 2000),
    (r"C:\test\artiklar\liten\test.jpg", 400),
]
all_pass = True
for path, expected in tests:
    result = get_target_size(path)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  {status}: get_target_size('{os.path.basename(path)}') = {result} (expected {expected})")
print(f"  {'ALL PASSED' if all_pass else 'SOME FAILED'}\n")

# Test 2: ensure_square_canvas with category alignment
print("=== TEST 2: ensure_square_canvas() alignment ===")
test_cases = [
    # (name, w, h, target, category, expected_y_red)
    ("lamp_pendant_top", 1200, 800, 1000, "lamp_pendant", 350), # red should be at y ~ 350
    ("default_centered", 1200, 800, 1000, "default", 500),      # red should be at y ~ 500
    ("sofa_bottom", 1200, 800, 1000, "sofa_3_seat", 660),       # red should be at y ~ 660
]

all_pass = True
for name, w, h, target, category, check_y in test_cases:
    tmp_path = os.path.join(tempfile.gettempdir(), f"test_{name}.jpg")
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw a red horizontal stripe in the vertical center of the image (y: 350-450)
    draw.rectangle([0, 350, w, 450], fill=(255, 0, 0))
    img.save(tmp_path, "JPEG", quality=92)
    
    # Apply ensure_square_canvas with category
    ensure_square_canvas(tmp_path, target, category=category)
    
    # Verify result
    result_img = Image.open(tmp_path)
    rw, rh = result_img.size
    is_square = rw == rh
    is_correct_size = rw == target
    
    # Check pixel color at check_y in the center of the image (x = 500)
    pixel = result_img.getpixel((500, check_y))
    is_red = (pixel[0] > 200 and pixel[1] < 50 and pixel[2] < 50)
    
    status = "PASS" if (is_square and is_correct_size and is_red) else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  {status}: {name} ({category}) -> size {rw}x{rh}, pixel at y={check_y} is red: {is_red} (RGB: {pixel})")
    
    result_img.close()
    os.remove(tmp_path)

print(f"  {'ALL PASSED' if all_pass else 'SOME FAILED'}\n")

# Test 3: Verify SAM3 and edge fading are disabled in process_and_correct
print("=== TEST 3: Simplified logic verification ===")
with open(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\vision_auto_corrector.py", 'r', encoding='utf-8') as f:
    content = f.read()

# Extract process_and_correct body
start_idx = content.find("def process_and_correct(")
end_idx = content.find("def process_single_main_image(")
pac_body = content[start_idx:end_idx]

if "get_sam_predictor" in pac_body or "apply_edge_fading_np" in pac_body:
    print("  FAIL: SAM3 or edge fading is still referenced inside process_and_correct")
else:
    print("  PASS: process_and_correct is simplified (no SAM3 or edge fading)")

# Test 4: Verify canvas size uses get_target_size
if "target_size = get_target_size(dest_path)" in content:
    print("  PASS: process_and_correct uses get_target_size()")
else:
    print("  FAIL: process_and_correct does NOT use get_target_size()")

if "max_dim = max(w_orig, h_orig)" in content:
    print("  FAIL: Old max_dim logic still present")
else:
    print("  PASS: Old max_dim logic removed")

# Count ensure_square_canvas calls
count = content.count("ensure_square_canvas(")
# Subtract 1 for the function definition
call_count = count - 1  # definition
print(f"\n  ensure_square_canvas() call sites: {call_count} (expected 8)")
if call_count == 8:
    print("  PASS: Exactly 8 call sites found.")
else:
    print(f"  FAIL: Expected 8 call sites, found {call_count}.")

print("\n=== ALL TESTS COMPLETE ===")

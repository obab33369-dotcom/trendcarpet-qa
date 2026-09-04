import os
import json
import collections
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
TARGET_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")

# Dictionary mapping carpet name to its list of database indices
carpet_indices = {
    "Matta 'Aureline' - Grön (RG01-9)": [11, 30, 61, 74, 75, 140, 141, 152, 153, 154, 155, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580],
    "Matta 'Carrano' - Svart/Vit (RG01-70)": [20, 21, 67, 68, 81, 82, 178, 179, 180, 181, 182, 183, 184, 390, 391, 392, 393, 394, 395, 396, 397, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480],
    "Matta 'Forma' - Beige (RG01-33)": [617, 623, 624, 629, 630, 713, 714, 719, 720, 741, 742, 747, 748, 749, 750, 770, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820],
    "Matta 'Lorano' - Multi (RG01-77)": [1223, 1267, 1272, 1287, 1292, 1356, 1361, 1378, 1383, 1404, 1409, 1410, 1551, 1552, 1553, 1554, 1555, 1608, 1609, 1610, 1611, 1612, 1754, 1755, 1756, 1757, 1758, 1769, 1770],
    "Matta 'Marionae' - Brun/Beige (RG01-43)": [1228, 1262, 1277, 1282, 1297, 1351, 1366, 1367, 1394, 1395, 1416, 1417, 1536, 1537, 1573, 1574, 1579, 1580, 1585, 1586, 1591, 1592, 1772, 1773, 1785, 1786, 1787, 1788, 1789],
    "Matta 'Rivetta' - Beige/Grön (RG01-37)": [1816, 1841, 1852, 1904, 1915, 1924, 1962, 1969, 1987, 1998, 2005, 2006, 2061, 2062, 2083, 2084, 2123, 2124, 2125, 2235, 2236, 2237, 2261, 2262, 2263, 2360, 2361, 2362, 2373, 2374, 2390, 2399, 2400],
    "Matta 'Savelle' - Grön (RG01-97)": [1820, 1837, 1856, 1879, 1880, 1971, 1972, 1977, 1978, 1983, 1984, 2050, 2051, 2066, 2067, 2112, 2113, 2116, 2117, 2243, 2244, 2247, 2248, 2259, 2260, 2363, 2364, 2365, 2366, 2384, 2385, 2386, 2387],
    "Matta 'Savena' - Gul/Grå (RG01-22)": [1802, 1803, 1806, 1807, 1810, 1861, 1864, 1865, 1868, 1869, 2168, 2169, 2172, 2173, 2176, 2177, 2180, 2181, 2204, 2205, 2208, 2209, 2212, 2213, 2216, 2217, 2220, 2221],
    "Matta 'Sorvento' - Svart/Grå (RG01-51)": [2402, 2439, 2442, 2479, 2482, 2519, 2522, 2559, 2562, 2599, 2602, 2639, 2642, 2679, 2682, 2719, 2752, 2789, 2792, 2829, 2832, 2869, 2872, 2909, 2912, 2949, 2952, 2989, 2992],
    "Matta 'Striped Sand' - Natur 160x230 (Jute-Striped-160.230)": [2403, 2438, 2443, 2478, 2483, 2518, 2523, 2558, 2563, 2598, 2603, 2638, 2643, 2678, 2683, 2718, 2753, 2788, 2793, 2828, 2833, 2868, 2873, 2908, 2913, 2948, 2953, 2988, 2993],
    "Matta 'Taliana' - Rosa/Röd (RG01-80)": [2405, 2436, 2445, 2476, 2485, 2516, 2525, 2556, 2565, 2596, 2605, 2636, 2645, 2676, 2685, 2716, 2755, 2786, 2795, 2826, 2835, 2866, 2875, 2906, 2915, 2946, 2955, 2986, 2995],
    "Matta 'Velenna' 160x230 cm - Blå (RG016)": [2412, 2429, 2452, 2469, 2492, 2509, 2532, 2549, 2572, 2589, 2612, 2629, 2652, 2669, 2692, 2709, 2762, 2779, 2802, 2819, 2842, 2859, 2882, 2899, 2922, 2939, 2962, 2979],
    "Matta 'Ventaro' - Beige (RG01-89)": [2419, 2422, 2459, 2462, 2499, 2502, 2539, 2542, 2579, 2582, 2619, 2622, 2659, 2662, 2699, 2702, 2769, 2772, 2809, 2812, 2849, 2852, 2889, 2892, 2929, 2932, 2969, 2972]
}

# Scan sorted directory on OneDrive to map index -> actual folder path
index_to_folders = collections.defaultdict(list)

print("Scanning sorted folders on OneDrive...")
if os.path.exists(TARGET_DIR):
    for item in os.listdir(TARGET_DIR):
        path = os.path.join(TARGET_DIR, item)
        if not os.path.isdir(path):
            continue
        
        # Scan files in main folder
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                m = re.match(r'^(\d+)-', f)
                if m:
                    idx = int(m.group(1))
                    index_to_folders[idx].append((item, "main", f))
                    
        # Scan files in reserv folder
        reserv_path = os.path.join(path, "reserv")
        if os.path.exists(reserv_path):
            for f in os.listdir(reserv_path):
                if os.path.isfile(os.path.join(reserv_path, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    m = re.match(r'^(\d+)-', f)
                    if m:
                        idx = int(m.group(1))
                        index_to_folders[idx].append((item, "reserv", f))

print("\n=== FINDING MISCLASSIFIED RENDERS ON ONEDRIVE ===")
mismatch_count = 0
for carpet_name, indices in carpet_indices.items():
    print(f"\nCarpet: {carpet_name}")
    found_any = False
    for idx in indices:
        if idx in index_to_folders:
            for folder, sub, filename in index_to_folders[idx]:
                # Check if it was placed in a folder different from the carpet name
                # Extracted carpet SKU: e.g. "RG01-9" or "RG016" or "Jute-Striped-160.230"
                sku_in_name = carpet_name.split('(')[-1].replace(')', '').strip()
                if sku_in_name not in folder:
                    mismatch_count += 1
                    print(f"  * DB Index {idx} ({filename}) was sorted into:")
                    print(f"    - Folder: {folder} ({sub})")
                    found_any = True
    if not found_any:
        print("  All renders sorted correctly (or no renders found on disk).")

print(f"\nTotal misclassified files located on OneDrive: {mismatch_count}")

import os
import json

PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def main():
    plan_path = os.path.join(PROJECT_DIR, "scratch", "furniture_redirection_plan.json")
    if not os.path.exists(plan_path):
        print("Plan not found.")
        return
        
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
        
    total_files = 0
    matched_count = 0
    none_count = 0
    error_count = 0
    
    sku_distribution = {}
    
    for folder, files in plan.items():
        for fn, res in files.items():
            total_files += 1
            if "error" in res:
                error_count += 1
            elif res.get("matched_sku") is None:
                none_count += 1
            else:
                matched_count += 1
                sku = res["matched_sku"]
                name = res["matched_name"]
                sku_distribution[sku] = sku_distribution.get(sku, 0) + 1
                
    print("=== Furniture Redirection Plan Analysis ===")
    print(f"Total files processed: {total_files}")
    print(f"  * Matched successfully: {matched_count} ({matched_count/total_files*100:.1f}%)")
    print(f"  * Matched to None (No match): {none_count} ({none_count/total_files*100:.1f}%)")
    print(f"  * Errors: {error_count} ({error_count/total_files*100:.1f}%)")
    
    print("\nTop Matched Targets:")
    sorted_skus = sorted(sku_distribution.items(), key=lambda x: x[1], reverse=True)
    for sku, cnt in sorted_skus[:15]:
        print(f"  * SKU: {sku} -> {cnt} times")
        
    # Let's print some examples of redirections
    print("\nSample Redirections:")
    sample_count = 0
    for folder, files in plan.items():
        for fn, res in files.items():
            if "matched_sku" in res and res["matched_sku"] is not None and sample_count < 10:
                print(f"  * {folder}/{fn} -> Visual Match: {res['matched_name']} ({res['matched_sku']})")
                print(f"    Reason: {res.get('explanation')}")
                sample_count += 1
                
if __name__ == "__main__":
    main()

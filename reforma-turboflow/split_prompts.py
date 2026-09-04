import os

prompts_file = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\prompts_only.txt"
output_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow"

with open(prompts_file, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"Total non-empty prompts found: {len(lines)}")

# Let's split into 4 parts
chunk_size = 55
for i in range(0, len(lines), chunk_size):
    part_num = (i // chunk_size) + 1
    chunk = lines[i:i+chunk_size]
    output_path = os.path.join(output_dir, f"prompts_part{part_num}.txt")
    with open(output_path, 'w', encoding='utf-8') as out_f:
        out_f.write("\n".join(chunk))
    print(f"Wrote {len(chunk)} prompts to C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\prompts_part{part_num}.txt")

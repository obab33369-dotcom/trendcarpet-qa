import os
import glob

# Remove old part files first to avoid confusion
for old_file in glob.glob('*_part*.txt') + glob.glob('*_part*.csv'):
    try:
        os.remove(old_file)
    except:
        pass

def split_file(filepath, lines_per_chunk, prefix):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # If it's a CSV, keep the header in each chunk
    is_csv = filepath.endswith('.csv')
    header = lines[0] if is_csv else ""
    data_lines = lines[1:] if is_csv else lines
    
    chunks = [data_lines[i:i + lines_per_chunk] for i in range(0, len(data_lines), lines_per_chunk)]
    
    output_files = []
    for i, chunk in enumerate(chunks):
        out_name = f"{prefix}_batch{i+1}{os.path.splitext(filepath)[1]}"
        with open(out_name, 'w', encoding='utf-8') as out:
            if is_csv:
                out.write(header)
            out.writelines(chunk)
        output_files.append(out_name)
    return output_files

print("Splitting TXT files into chunks of 190...")
split_file('turboflow_ready_full_catalog.txt', 190, 'turboflow_ready_full_catalog')

print("Splitting CSV tracking files into chunks of 190...")
split_file('turboflow_tracking_log_full_catalog.csv', 190, 'turboflow_tracking_log_full_catalog')

print("Splitting Prompts Only TXT files into chunks of 190...")
split_file('prompts_only_full_catalog.txt', 190, 'prompts_only_full_catalog')

print("Done!")

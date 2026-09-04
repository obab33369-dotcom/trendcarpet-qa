import os

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
        out_name = f"{prefix}_part{i+1}{os.path.splitext(filepath)[1]}"
        with open(out_name, 'w', encoding='utf-8') as out:
            if is_csv:
                out.write(header)
            out.writelines(chunk)
        output_files.append(out_name)
    return output_files

print("Splitting TXT files...")
split_file('turboflow_ready_full_catalog.txt', 900, 'turboflow_ready_full_catalog')

print("Splitting CSV tracking files...")
split_file('turboflow_tracking_log_full_catalog.csv', 900, 'turboflow_tracking_log_full_catalog')

print("Splitting Prompts Only TXT files...")
split_file('prompts_only_full_catalog.txt', 900, 'prompts_only_full_catalog')

print("Done!")

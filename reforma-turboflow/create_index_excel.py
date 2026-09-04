import csv
import os

directory = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
output_file = os.path.join(directory, "turboflow_batches_index.csv")

with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(["Batch Number", "Prompts TXT File Path", "Tracking CSV File Path", "Directory Path"])
    
    for i in range(1, 17):
        txt_file = os.path.join(directory, f"turboflow_ready_full_catalog_batch{i}.txt")
        csv_file = os.path.join(directory, f"turboflow_tracking_log_full_catalog_batch{i}.csv")
        
        writer.writerow([
            f"Batch {i}", 
            txt_file, 
            csv_file, 
            directory
        ])

print(f"Created index file: {output_file}")

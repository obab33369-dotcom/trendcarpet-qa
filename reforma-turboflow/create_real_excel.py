import os
import openpyxl
from openpyxl.styles import Font

directory = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
output_file = os.path.join(directory, "turboflow_batches_index.xlsx")

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Batches"

# Headers
headers = ["Batch Number", "Prompts TXT File (Click to Open)", "Tracking CSV File", "Folder Path (Click to Open)"]
for col_num, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col_num)
    cell.value = header
    cell.font = Font(bold=True)

# Data
for i in range(1, 17):
    txt_file = os.path.join(directory, f"turboflow_ready_full_catalog_batch{i}.txt")
    csv_file = os.path.join(directory, f"turboflow_tracking_log_full_catalog_batch{i}.csv")
    
    ws.cell(row=i+1, column=1, value=f"Batch {i}")
    
    # TXT link
    txt_cell = ws.cell(row=i+1, column=2)
    txt_cell.value = "Öppna TXT-fil"
    txt_cell.hyperlink = txt_file
    txt_cell.font = Font(color="0000FF", underline="single")
    
    # CSV link
    csv_cell = ws.cell(row=i+1, column=3)
    csv_cell.value = csv_file
    
    # Folder link
    folder_cell = ws.cell(row=i+1, column=4)
    folder_cell.value = "Öppna Mappen"
    folder_cell.hyperlink = directory
    folder_cell.font = Font(color="0000FF", underline="single")

# Adjust column widths
ws.column_dimensions['A'].width = 15
ws.column_dimensions['B'].width = 30
ws.column_dimensions['C'].width = 80
ws.column_dimensions['D'].width = 30

wb.save(output_file)
print(f"Created real Excel file: {output_file}")

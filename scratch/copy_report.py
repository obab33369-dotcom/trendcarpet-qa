import shutil

src = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\060226f5-ac6f-4874-8f31-be11e430672f\architect_analysis_report.md"
dst = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\architect_analysis_report.md"

try:
    shutil.copy2(src, dst)
    print("Successfully copied architect report to parent conversation directory!")
except Exception as e:
    print(f"Error copying report: {e}")

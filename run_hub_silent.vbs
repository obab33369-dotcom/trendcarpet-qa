Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors"
WshShell.Run "python start_hub_with_tunnel.py", 0, False

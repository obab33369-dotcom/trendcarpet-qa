import os

# Common locations for PowerShell profile
possible_profiles = [
    os.path.expanduser(r"~\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"),
    os.path.expanduser(r"~\OneDrive - CaMa Gruppen AB\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"),
    os.path.expanduser(r"~\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1")
]

found = False
for p in possible_profiles:
    if os.path.exists(p):
        print(f"\n=================== FOUND PROFILE: {p} ===================")
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            print(f.read())
        found = True
        break

if not found:
    print("No profile files found.")

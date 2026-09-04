import winreg

def check_registry(hive, path):
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
            i = 0
            while True:
                name, value, type_ = winreg.EnumValue(key, i)
                if "ANTHROPIC" in name or "CLAUDE" in name:
                    print(f"Found in {path}: {name} = {value[:10]}...")
                i += 1
    except OSError:
        pass

print("Checking registry...")
check_registry(winreg.HKEY_CURRENT_USER, "Environment")
check_registry(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
print("Check complete.")

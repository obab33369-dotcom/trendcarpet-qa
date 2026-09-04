import urllib.request
import json
import os
import subprocess

try:
    print("Fetching latest RustDesk release info from GitHub API...")
    req = urllib.request.Request(
        'https://api.github.com/repos/rustdesk/rustdesk/releases/latest',
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    
    download_url = None
    file_name = None
    for asset in data['assets']:
        name = asset['name']
        if name.endswith('.exe') and ('x86_64' in name or 'x64' in name) and 'sciter' not in name:
            download_url = asset['browser_download_url']
            file_name = name
            break
            
    if not download_url:
        for asset in data['assets']:
            if asset['name'].endswith('.exe'):
                download_url = asset['browser_download_url']
                file_name = asset['name']
                break
                
    if download_url:
        print(f"Found asset: {file_name}")
        downloads_dir = r"C:\Users\AndronikLindgren\Downloads"
        if not os.path.exists(downloads_dir):
            downloads_dir = os.path.dirname(os.getcwd())
        dest_path = os.path.join(downloads_dir, file_name)
        
        print(f"Downloading to: {dest_path} ...")
        urllib.request.urlretrieve(download_url, dest_path)
        print("Download complete!")
        
        print("Launching RustDesk installer/client...")
        subprocess.Popen([dest_path], shell=True)
        print("RustDesk launched. Check your screen/taskbar for the RustDesk window.")
    else:
        print("Error: Could not find any Windows .exe asset in the latest RustDesk release.")
except Exception as e:
    print(f"An error occurred: {e}")

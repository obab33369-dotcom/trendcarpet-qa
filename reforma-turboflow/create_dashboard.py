import os
import glob
import base64

project_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
output_html = os.path.join(project_dir, 'turboflow_dashboard.html')

batch_files = glob.glob(os.path.join(project_dir, 'turboflow_tracking_log_full_catalog_batch*[a-z].csv'))

# Parse batch names (only match sub-batches ending in 'a'-'z')
batch_names = []
for bf in batch_files:
    import re
    m = re.search(r"batch(\d+[a-z])\.csv$", bf)
    if m:
        batch_names.append(m.group(1))

def get_sort_key(s):
    import re
    match = re.match(r'(\d+)([a-z]?)', s)
    if match:
        return (int(match.group(1)), match.group(2))
    return (999, s)

batch_names = sorted(batch_names, key=get_sort_key)
num_batches = len(batch_names)

batches_data = []
total_prompts = 0
total_images = 0

for b_name in batch_names:
    prompt_file = os.path.join(project_dir, f'prompts_only_full_catalog_batch{b_name}.txt')
    
    # Image folder is based on the numeric base (e.g. '1a' -> '1')
    m_base = re.match(r"^(\d+)", b_name)
    base_num = m_base.group(1) if m_base else b_name
    img_folder = os.path.join(project_dir, f'batch{base_num}_images')
    
    prompts_text = ''
    num_prompts = 0
    if os.path.exists(prompt_file):
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompts_text = f.read()
            num_prompts = len([l for l in prompts_text.splitlines() if l.strip()])
            
    num_images = 0
    if os.path.exists(img_folder):
        num_images = len([f for f in os.listdir(img_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        
    total_prompts += num_prompts
    total_images += num_images
    
    b64_content = base64.b64encode(prompts_text.encode('utf-8')).decode('utf-8')
    
    batches_data.append({
        'batch': b_name,
        'num_prompts': num_prompts,
        'num_images': num_images,
        'b64': b64_content,
        'folder': img_folder.replace('\\', '\\\\')
    })

html_content = f"""<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Turboflow Batch Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --glass-bg: rgba(20, 25, 40, 0.6);
            --glass-border: rgba(255, 255, 255, 0.08);
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #60a5fa;
            --accent-gradient: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.2);
            --btn-secondary: rgba(255, 255, 255, 0.1);
            --btn-secondary-hover: rgba(255, 255, 255, 0.15);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{ 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.15) 0%, transparent 50%);
            background-attachment: fixed;
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            padding: 40px 20px;
        }}

        .container {{ 
            width: 100%;
            max-width: 1200px;
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 24px; 
            padding: 40px;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); 
            animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
            transform: translateY(20px);
        }}

        @keyframes fadeUp {{
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        header {{
            text-align: center;
            margin-bottom: 40px;
        }}

        h1 {{ 
            font-family: 'Outfit', sans-serif;
            font-size: 3rem;
            font-weight: 800;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15px;
            letter-spacing: -1px;
        }}

        .subtitle {{
            font-size: 1.1rem;
            color: var(--text-muted);
            max-width: 600px;
            margin: 0 auto 10px;
            line-height: 1.6;
        }}

        .stats-row {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 30px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 20px 30px;
            text-align: center;
            min-width: 150px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
            border-color: rgba(255,255,255,0.1);
        }}

        .stat-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 5px;
        }}

        .stat-label {{
            font-size: 0.9rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}

        .table-wrapper {{
            overflow-x: auto;
            border-radius: 16px;
            border: 1px solid var(--glass-border);
            background: rgba(0, 0, 0, 0.2);
        }}

        table {{ 
            width: 100%; 
            border-collapse: collapse; 
        }}

        th, td {{ 
            padding: 20px; 
            text-align: left; 
            border-bottom: 1px solid var(--glass-border); 
        }}

        th {{ 
            background-color: rgba(255, 255, 255, 0.02); 
            font-weight: 600; 
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 1px;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tbody tr {{
            transition: background-color 0.2s ease;
        }}

        tbody tr:hover {{
            background-color: rgba(255, 255, 255, 0.03);
        }}

        .batch-name {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.2rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .batch-name::before {{
            content: '';
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent-gradient);
        }}

        .number-badge {{
            background: rgba(255,255,255,0.05);
            padding: 4px 10px;
            border-radius: 8px;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 1rem;
        }}

        .btn {{ 
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: var(--accent-gradient); 
            color: white; 
            border: none; 
            padding: 10px 18px; 
            border-radius: 10px; 
            cursor: pointer; 
            font-size: 0.9rem; 
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }}

        .btn:hover {{ 
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
            filter: brightness(1.1);
        }}

        .btn:active {{
            transform: translateY(0);
        }}

        .btn-secondary {{ 
            background: var(--btn-secondary); 
            box-shadow: none;
        }}

        .btn-secondary:hover {{ 
            background: var(--btn-secondary-hover);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}

        .btn.copied {{ 
            background: var(--success);
            box-shadow: 0 4px 15px var(--success-glow);
        }}

        .toggle-wrapper {{
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
        }}

        .toggle-checkbox {{
            display: none;
        }}

        .toggle-bg {{
            width: 44px;
            height: 24px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            position: relative;
            transition: all 0.3s ease;
        }}

        .toggle-knob {{
            width: 18px;
            height: 18px;
            background-color: white;
            border-radius: 50%;
            position: absolute;
            top: 3px;
            left: 3px;
            transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }}

        .toggle-checkbox:checked + .toggle-bg {{
            background-color: var(--success);
            box-shadow: 0 0 10px var(--success-glow);
        }}

        .toggle-checkbox:checked + .toggle-bg .toggle-knob {{
            transform: translateX(20px);
        }}

        tr.done {{ 
            background-color: rgba(16, 185, 129, 0.05); 
        }}
        tr.done td {{
            opacity: 0.6;
        }}
        tr.done:hover {{
            background-color: rgba(16, 185, 129, 0.1); 
        }}
        
        .icon {{
            font-size: 1.1em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Turboflow Dashboard</h1>
            <p class="subtitle">Hantera generering för {total_images} unika referensbilder uppdelade i perfekta batcher för Turboflow.</p>
            
            <div class="stats-row">
                <div class="stat-card">
                    <div class="stat-value">{num_batches}</div>
                    <div class="stat-label">Batcher</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_prompts}</div>
                    <div class="stat-label">Totala Prompter</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_images}</div>
                    <div class="stat-label">Unika Bilder</div>
                </div>
            </div>
        </header>
        
        <div class="table-wrapper">
            <table id="batchTable">
                <thead>
                    <tr>
                        <th>Batch</th>
                        <th>Antal Prompter</th>
                        <th>Antal Bilder</th>
                        <th>Kopiera Prompter</th>
                        <th>Bildmapp</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""

for bd in batches_data:
    folder_js = bd['folder']
    html_content += f"""
                    <tr id="row-{bd['batch']}">
                        <td><div class="batch-name">Batch {bd['batch']}</div></td>
                        <td><span class="number-badge">{bd['num_prompts']}</span></td>
                        <td><span class="number-badge">{bd['num_images']}</span></td>
                        <td>
                            <button class="btn" onclick="copyPrompts('{bd['batch']}', this)" data-prompts="{bd['b64']}">
                                <span class="icon">📋</span> Kopiera
                            </button>
                        </td>
                        <td>
                            <button class="btn btn-secondary" onclick="copyText('{folder_js}', this)">
                                <span class="icon">📁</span> Kopiera sökväg
                            </button>
                        </td>
                        <td>
                            <label class="toggle-wrapper" for="check-{bd['batch']}">
                                <input type="checkbox" class="toggle-checkbox" id="check-{bd['batch']}" onchange="toggleDone('{bd['batch']}')">
                                <div class="toggle-bg"><div class="toggle-knob"></div></div>
                                <span style="font-weight:500; font-size:0.9rem;">Klar</span>
                            </label>
                        </td>
                    </tr>
"""

html_content += """
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function copyPrompts(batchId, btn) {
            const b64 = btn.getAttribute('data-prompts');
            const text = decodeURIComponent(escape(window.atob(b64)));
            copyToClipboard(text, btn);
        }

        function copyText(text, btn) {
            copyToClipboard(text, btn);
        }
        
        function copyToClipboard(text, btn) {
            navigator.clipboard.writeText(text).then(() => {
                showCopiedState(btn);
            }).catch(err => {
                const ta = document.createElement('textarea');
                ta.value = text;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                showCopiedState(btn);
            });
        }
        
        function showCopiedState(btn) {
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '<span class="icon">✅</span> Kopierad!';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.classList.remove('copied');
            }, 2000);
        }

        function toggleDone(id) {
            const isChecked = document.getElementById(`check-${id}`).checked;
            localStorage.setItem(`batch-${id}-done`, isChecked);
            updateRowStyle(id, isChecked);
        }

        function updateRowStyle(id, isChecked) {
            const row = document.getElementById(`row-${id}`);
            if (isChecked) {
                row.classList.add('done');
            } else {
                row.classList.remove('done');
            }
        }

        window.onload = function() {
            // Animate rows stagger
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach((row, index) => {
                row.style.opacity = '0';
                row.style.transform = 'translateX(-20px)';
                row.style.animation = `fadeUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) ${0.2 + (index * 0.1)}s forwards`;
            });
            
            const checkboxes = document.querySelectorAll('.toggle-checkbox');
            checkboxes.forEach(cb => {
                const id = cb.id.split('-')[1];
                const isDone = localStorage.getItem(`batch-${id}-done`) === 'true';
                cb.checked = isDone;
                updateRowStyle(id, isDone);
            });
        };
    </script>
</body>
</html>
"""

with open(output_html, 'w', encoding='utf-8') as f:
    f.write(html_content)
    
print('Total batches:', num_batches)
print('Total prompts:', total_prompts)
print('Total images:', total_images)
for b in batches_data:
    print(f"Batch {b['batch']}: {b['num_prompts']} products, {b['num_images']} images")

# Also write to create_dashboard.py
with open(os.path.join(project_dir, 'create_dashboard.py'), 'w', encoding='utf-8') as f:
    f.write(open(__file__, encoding='utf-8').read())

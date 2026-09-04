import os
import re
import urllib.parse

TARGET_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-26-06"
OUTPUT_HTML = os.path.join(TARGET_DIR, "visual_review.html")

def generate():
    if not os.path.exists(TARGET_DIR):
        print(f"Error: Target directory {TARGET_DIR} does not exist.")
        return

    # Scan directories
    entries = []
    for entry in os.listdir(TARGET_DIR):
        entry_path = os.path.join(TARGET_DIR, entry)
        if not os.path.isdir(entry_path):
            continue
        
        # Parse Name and SKU: "Name (SKU)"
        m = re.search(r"^(.*?)\s*\(([^)]+)\)$", entry)
        if m:
            name = m.group(1).strip()
            sku = m.group(2).strip()
        else:
            name = entry
            sku = "Unknown"

        # List all image files in this subfolder
        files = [f for f in os.listdir(entry_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        
        # Identify reference image (starts with 00_REFERENCE_)
        ref_image = None
        renders = []
        for f in files:
            if f.startswith("00_REFERENCE_"):
                ref_image = f
            else:
                renders.append(f)
                
        # Sort renders alphabetically
        renders.sort()
        
        entries.append({
            'folder_name': entry,
            'name': name,
            'sku': sku,
            'ref_image': ref_image,
            'renders': renders
        })

    # Sort entries by product name
    entries.sort(key=lambda x: x['name'])

    # Count statistics
    total_products = len(entries)
    total_renders = sum(len(e['renders']) for e in entries)
    products_with_ref = sum(1 for e in entries if e['ref_image'] is not None)

    html_content = f"""<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reforma Sorterade Interiörsbilder - Granskning</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(20, 25, 45, 0.5);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --accent-gradient: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            --ref-badge: #0284c7;
            --render-badge: #7c3aed;
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
                radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.12) 0%, transparent 40%);
            background-attachment: fixed;
            color: var(--text-main);
            padding: 40px 20px;
            min-height: 100vh;
        }}

        .wrapper {{
            max-width: 1600px;
            margin: 0 auto;
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
            max-width: 800px;
            margin: 0 auto 30px;
            line-height: 1.6;
        }}

        /* Stats dashboard */
        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }}

        .stat-card {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 15px 30px;
            text-align: center;
            min-width: 200px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }}

        .stat-val {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 5px;
        }}

        .stat-lbl {{
            font-size: 0.85rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}

        /* Sticky Search and filters */
        .controls {{
            position: sticky;
            top: 20px;
            z-index: 100;
            background: rgba(11, 15, 25, 0.85);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }}

        .search-box {{
            flex: 1;
            position: relative;
        }}

        .search-box input {{
            width: 100%;
            padding: 14px 20px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            background: rgba(0,0,0,0.2);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            transition: all 0.3s ease;
        }}

        .search-box input:focus {{
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.25);
            background: rgba(0,0,0,0.4);
        }}

        .search-box::after {{
            content: '🔍';
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.2rem;
            opacity: 0.5;
            pointer-events: none;
        }}

        /* Cards Grid */
        .grid {{
            display: flex;
            flex-direction: column;
            gap: 40px;
        }}

        .product-card {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        .product-card:hover {{
            border-color: rgba(255,255,255,0.15);
            box-shadow: 0 12px 40px rgba(0,0,0,0.3);
        }}

        .product-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 25px;
            border-bottom: 1px dashed var(--border-color);
            padding-bottom: 15px;
            flex-wrap: wrap;
            gap: 15px;
        }}

        .product-title-group {{
            flex: 1;
        }}

        .product-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.6rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 5px;
        }}

        .product-sku {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.05rem;
            font-weight: 600;
            color: var(--text-muted);
            background: rgba(255,255,255,0.04);
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
        }}

        .images-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }}

        /* Image item card */
        .img-card {{
            position: relative;
            background: rgba(0,0,0,0.3);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            overflow: hidden;
            aspect-ratio: 1 / 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            cursor: zoom-in;
            transition: all 0.3s ease;
        }}

        .img-card:hover {{
            transform: scale(1.02);
            border-color: rgba(255,255,255,0.2);
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        }}

        .img-card img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: filter 0.3s ease;
        }}

        .img-card.ref-card {{
            border-left: 4px solid var(--accent-blue);
        }}

        /* Badges */
        .badge {{
            position: absolute;
            top: 15px;
            left: 15px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            z-index: 5;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }}

        .badge.ref {{
            background: var(--ref-badge);
            color: #fff;
        }}

        .badge.render {{
            background: var(--render-badge);
            color: #fff;
        }}

        .img-label {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%);
            padding: 20px 15px 10px;
            font-size: 0.8rem;
            color: var(--text-main);
            text-align: center;
            opacity: 0;
            transition: opacity 0.3s ease;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .img-card:hover .img-label {{
            opacity: 1;
        }}

        .empty-renders {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 150px;
            border: 2px dashed rgba(255,255,255,0.04);
            border-radius: 16px;
            color: var(--text-muted);
            font-style: italic;
        }}

        /* Premium Lightbox Modal */
        .lightbox {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(7, 10, 18, 0.95);
            backdrop-filter: blur(15px);
            z-index: 1000;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            padding: 40px;
        }}

        .lightbox.active {{
            opacity: 1;
            pointer-events: auto;
        }}

        .lightbox-close {{
            position: absolute;
            top: 30px;
            right: 40px;
            background: none;
            border: none;
            color: #fff;
            font-size: 2.5rem;
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s ease;
        }}

        .lightbox-close:hover {{
            opacity: 1;
        }}

        .lightbox-content {{
            max-width: 90%;
            max-height: 80vh;
            box-shadow: 0 10px 50px rgba(0,0,0,0.8);
            border-radius: 8px;
            overflow: hidden;
        }}

        .lightbox-content img {{
            display: block;
            max-width: 100%;
            max-height: 80vh;
            object-fit: contain;
        }}

        .lightbox-info {{
            margin-top: 20px;
            text-align: center;
        }}

        .lightbox-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .lightbox-subtitle {{
            color: var(--text-muted);
            font-size: 0.95rem;
        }}

        /* Responsive styling */
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2.2rem;
            }}
            .controls {{
                flex-direction: column;
                align-items: stretch;
            }}
            .product-header {{
                flex-direction: column;
                align-items: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <header>
            <h1>Reforma Sorteringsgranskning</h1>
            <p class="subtitle">Granska AI-genererade interiörsbilder sida-vid-sida med de faktiska studio-referensbilderna på vit bakgrund. Rätt produkt ska finnas med i alla renderingar under respektive kort.</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-val">{total_products}</div>
                    <div class="stat-lbl">Produkter</div>
                </div>
                <div class="stat-card">
                    <div class="stat-val">{total_renders}</div>
                    <div class="stat-lbl">Renderingar</div>
                </div>
                <div class="stat-card">
                    <div class="stat-val">{products_with_ref}/{total_products}</div>
                    <div class="stat-lbl">Med Studio-referens</div>
                </div>
            </div>
        </header>

        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Sök efter produktnamn eller SKU..." onkeyup="filterProducts()">
            </div>
        </div>

        <div class="grid" id="productsGrid">
"""

    for entry in entries:
        folder_escaped = urllib.parse.quote(entry['folder_name'])
        
        html_content += f"""
            <div class="product-card" data-name="{entry['name'].lower()}" data-sku="{entry['sku'].lower()}">
                <div class="product-header">
                    <div class="product-title-group">
                        <h2 class="product-title">{entry['name']}</h2>
                        <span class="product-sku">{entry['sku']}</span>
                    </div>
                </div>
                
                <div class="images-container">
        """

        # Append reference photo
        if entry['ref_image']:
            ref_path_escaped = f"{folder_escaped}/{urllib.parse.quote(entry['ref_image'])}"
            html_content += f"""
                    <div class="img-card ref-card" onclick="openLightbox('{ref_path_escaped}', '{entry['name']}', 'STUDIO REFERENS ({entry['sku']})')">
                        <span class="badge ref">Referens</span>
                        <img src="{ref_path_escaped}" alt="Studio-referens" loading="lazy">
                        <div class="img-label">{entry['ref_image']}</div>
                    </div>
            """
        else:
            html_content += f"""
                    <div class="img-card ref-card" style="opacity: 0.3; pointer-events: none; border-style: dashed;">
                        <span class="badge ref" style="background:#475569;">Ingen ref</span>
                        <span style="font-size: 2rem;">🖼️</span>
                        <span style="font-size:0.8rem; margin-top:10px;">Saknar studio-referens</span>
                    </div>
            """

        # Append room renders
        for render in entry['renders']:
            render_path_escaped = f"{folder_escaped}/{urllib.parse.quote(render)}"
            html_content += f"""
                    <div class="img-card" onclick="openLightbox('{render_path_escaped}', '{entry['name']}', 'AI RENDERING ({render})')">
                        <span class="badge render">Rendering</span>
                        <img src="{render_path_escaped}" alt="AI-genererad rendering" loading="lazy">
                        <div class="img-label">{render}</div>
                    </div>
            """
            
        if not entry['renders']:
            html_content += f"""
                    <div class="empty-renders">Inga renderingar hittades i denna mapp</div>
            """

        html_content += """
                </div>
            </div>
        """

    html_content += """
        </div>
    </div>

    <!-- Lightbox Modal -->
    <div class="lightbox" id="lightboxModal" onclick="closeLightbox()">
        <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
        <div class="lightbox-content" onclick="event.stopPropagation()">
            <img id="lightboxImg" src="" alt="Förstoring">
        </div>
        <div class="lightbox-info">
            <div class="lightbox-title" id="lightboxTitle"></div>
            <div class="lightbox-subtitle" id="lightboxSubtitle"></div>
        </div>
    </div>

    <script>
        function filterProducts() {
            const query = document.getElementById('searchInput').value.toLowerCase().trim();
            const cards = document.querySelectorAll('.product-card');
            
            cards.forEach(card => {
                const name = card.getAttribute('data-name');
                const sku = card.getAttribute('data-sku');
                
                if (name.includes(query) || sku.includes(query)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function openLightbox(src, title, subtitle) {
            const modal = document.getElementById('lightboxModal');
            const img = document.getElementById('lightboxImg');
            const t = document.getElementById('lightboxTitle');
            const s = document.getElementById('lightboxSubtitle');
            
            img.src = src;
            t.innerText = title;
            s.innerText = subtitle;
            
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function toggleDone(id) {
            const isChecked = document.getElementById(`check-${id}`).checked;
            localStorage.setItem(`batch-${id}-done`, isChecked);
            updateRowStyle(id, isChecked);
        }

        function closeLightbox() {
            const modal = document.getElementById('lightboxModal');
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }

        // Close on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeLightbox();
            }
        });
    </script>
</body>
</html>
"""

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"[OK] Generated review dashboard at: {OUTPUT_HTML}")
    print(f"     Total products: {total_products}")
    print(f"     Total renders listed: {total_renders}")

if __name__ == '__main__':
    generate()

import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors"
METADATA_FILE = os.path.join(WORKSPACE_DIR, "pt1_gallery_metadata.json")
OUTPUT_HTML = os.path.join(WORKSPACE_DIR, "gallery.html")

with open(METADATA_FILE, "r", encoding="utf-8") as f:
    catalog_json = f.read()

html_content = r'''<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trendcarpet - Print Mattor Bildgalleri (26-08-27-Print-h-r-g-pt1-x)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0c0e14;
            --bg-panel: #141722;
            --bg-card: #1b202e;
            --bg-card-hover: #262c3e;
            --bg-input: #11141d;
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.35);
            --accent-hover: #60a5fa;
            --purple: #8b5cf6;
            --emerald: #10b981;
            --amber: #f59e0b;
            --rose: #f43f5e;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --border: #232838;
            --border-hover: #333a50;
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --radius-xl: 20px;
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.4);
            --shadow-md: 0 6px 20px rgba(0, 0, 0, 0.5);
            --shadow-lg: 0 12px 35px rgba(0, 0, 0, 0.7);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            user-select: none;
        }

        /* Top Header */
        header {
            background-color: var(--bg-panel);
            border-bottom: 1px solid var(--border);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 100;
            flex-shrink: 0;
            gap: 16px;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-logo {
            font-size: 1.2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .brand-logo svg {
            color: var(--accent);
        }

        .batch-badge {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15));
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #93c5fd;
            font-size: 0.75rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            padding: 4px 10px;
            border-radius: var(--radius-sm);
        }

        .header-stats {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .stat-chip {
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 5px 12px;
            border-radius: var(--radius-md);
            font-size: 0.8rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .stat-chip strong {
            color: var(--text-main);
            font-weight: 700;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .btn-header {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 7px 14px;
            border-radius: var(--radius-md);
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }

        .btn-header:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-hover);
            transform: translateY(-1px);
        }

        .btn-header.primary {
            background: linear-gradient(135deg, var(--accent), #2563eb);
            border-color: transparent;
            box-shadow: 0 4px 12px var(--accent-glow);
        }

        .btn-header.primary:hover {
            background: linear-gradient(135deg, var(--accent-hover), #3b82f6);
        }

        /* Layout */
        .app-container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        /* Sidebar (Rug list) */
        aside.sidebar {
            width: 320px;
            background: var(--bg-panel);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            overflow: hidden;
        }

        .sidebar-header {
            padding: 16px 18px 12px;
            border-bottom: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .search-box {
            position: relative;
            width: 100%;
        }

        .search-box input {
            width: 100%;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            color: var(--text-main);
            padding: 9px 12px 9px 34px;
            font-size: 0.85rem;
            outline: none;
            transition: all 0.2s;
        }

        .search-box input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }

        .search-box svg {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-dim);
            pointer-events: none;
        }

        .rug-list {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .rug-list::-webkit-scrollbar {
            width: 6px;
        }
        .rug-list::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 3px;
        }

        .rug-card-nav {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 8px 10px;
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
        }

        .rug-card-nav:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-hover);
            transform: translateX(2px);
        }

        .rug-card-nav.active {
            background: rgba(59, 130, 246, 0.12);
            border-color: var(--accent);
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.15);
        }

        .rug-nav-thumb {
            width: 48px;
            height: 48px;
            border-radius: var(--radius-sm);
            background: var(--bg-input);
            object-fit: cover;
            border: 1px solid var(--border);
            flex-shrink: 0;
        }

        .rug-nav-info {
            flex: 1;
            min-width: 0;
        }

        .rug-nav-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-main);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .rug-nav-meta {
            font-size: 0.73rem;
            color: var(--text-dim);
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 3px;
        }

        .rug-nav-badge {
            background: var(--bg-input);
            border: 1px solid var(--border);
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }

        /* Main Content Area */
        main.content-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-main);
            overflow: hidden;
        }

        /* Top Filter Toolbar */
        .filter-toolbar {
            background: var(--bg-panel);
            border-bottom: 1px solid var(--border);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
        }

        .tab-group {
            display: flex;
            align-items: center;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 3px;
            gap: 3px;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 6px 14px;
            border-radius: var(--radius-md);
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .tab-btn:hover {
            color: var(--text-main);
        }

        .tab-btn.active {
            background: var(--accent);
            color: #ffffff;
            box-shadow: 0 2px 8px var(--accent-glow);
        }

        .filter-chip-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .filter-chip {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .filter-chip:hover {
            border-color: var(--border-hover);
            color: var(--text-main);
        }

        .filter-chip.active {
            background: rgba(59, 130, 246, 0.15);
            border-color: var(--accent);
            color: #93c5fd;
            font-weight: 600;
        }

        .view-controls {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .grid-size-btn {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 6px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .grid-size-btn:hover, .grid-size-btn.active {
            background: var(--bg-card-hover);
            color: var(--text-main);
            border-color: var(--border-hover);
        }

        /* Gallery Grid */
        .gallery-scroll {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
        }

        .gallery-scroll::-webkit-scrollbar {
            width: 8px;
        }
        .gallery-scroll::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }

        .gallery-header-info {
            margin-bottom: 20px;
            display: flex;
            align-items: baseline;
            justify-content: space-between;
        }

        .gallery-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }

        .gallery-grid.size-sm {
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 14px;
        }

        .gallery-grid.size-lg {
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 24px;
        }

        /* Image Card */
        .image-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            cursor: pointer;
            position: relative;
        }

        .image-card:hover {
            transform: translateY(-4px);
            border-color: var(--border-hover);
            box-shadow: var(--shadow-md);
        }

        .card-img-wrapper {
            position: relative;
            width: 100%;
            padding-top: 100%;
            background-color: #080a0f;
            overflow: hidden;
        }

        .card-img-wrapper img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.35s ease;
        }

        .image-card:hover .card-img-wrapper img {
            transform: scale(1.04);
        }

        .card-badge-top-left {
            position: absolute;
            top: 10px;
            left: 10px;
            display: flex;
            gap: 6px;
            z-index: 2;
        }

        .card-badge-top-right {
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 2;
        }

        .type-badge {
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            padding: 3px 8px;
            border-radius: 4px;
            backdrop-filter: blur(8px);
        }

        .type-badge.studio {
            background: rgba(16, 185, 129, 0.85);
            color: #ffffff;
        }

        .type-badge.interior {
            background: rgba(139, 92, 246, 0.85);
            color: #ffffff;
        }

        .cat-badge {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #cbd5e1;
            font-size: 0.68rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            padding: 3px 8px;
            border-radius: 4px;
            backdrop-filter: blur(8px);
        }

        .card-body {
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            background: var(--bg-card);
        }

        .card-filename {
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-main);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-family: 'JetBrains Mono', monospace;
        }

        .card-meta-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.73rem;
            color: var(--text-dim);
        }

        .card-actions {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 4px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 8px;
        }

        .card-btn {
            flex: 1;
            background: var(--bg-input);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 4px 8px;
            border-radius: var(--radius-sm);
            font-size: 0.72rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            transition: all 0.2s;
        }

        .card-btn:hover {
            background: var(--bg-card-hover);
            color: var(--text-main);
            border-color: var(--border-hover);
        }

        /* Lightbox Modal */
        .lightbox-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(6, 8, 12, 0.95);
            backdrop-filter: blur(12px);
            z-index: 999;
            display: none;
            flex-direction: column;
            overflow: hidden;
        }

        .lightbox-modal.active {
            display: flex;
        }

        .lightbox-header {
            padding: 12px 24px;
            background: rgba(20, 23, 34, 0.85);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            z-index: 10;
        }

        .lightbox-title-area {
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
        }

        .lightbox-filename {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-main);
            font-family: 'JetBrains Mono', monospace;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .lightbox-controls {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .lightbox-btn {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 6px 12px;
            border-radius: var(--radius-md);
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }

        .lightbox-btn:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-hover);
        }

        .lightbox-btn.active {
            background: var(--accent);
            border-color: transparent;
        }

        .lightbox-btn-close {
            background: rgba(244, 63, 94, 0.15);
            border: 1px solid rgba(244, 63, 94, 0.3);
            color: #fda4af;
            padding: 6px 14px;
            border-radius: var(--radius-md);
            font-size: 0.85rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }

        .lightbox-btn-close:hover {
            background: var(--rose);
            color: white;
        }

        /* Lightbox Main Stage */
        .lightbox-stage {
            flex: 1;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            cursor: grab;
        }

        .lightbox-stage:active {
            cursor: grabbing;
        }

        .lightbox-img-container {
            max-width: 92vw;
            max-height: 75vh;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.1s ease-out;
            transform-origin: center center;
        }

        .lightbox-img {
            max-width: 100%;
            max-height: 75vh;
            object-fit: contain;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            pointer-events: none;
        }

        /* Navigation Arrows */
        .lightbox-nav-arrow {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            width: 52px;
            height: 52px;
            border-radius: 50%;
            background: rgba(20, 23, 34, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            z-index: 20;
            backdrop-filter: blur(6px);
        }

        .lightbox-nav-arrow:hover {
            background: var(--accent);
            border-color: transparent;
            transform: translateY(-50%) scale(1.1);
            box-shadow: 0 0 20px var(--accent-glow);
        }

        .lightbox-nav-arrow.prev {
            left: 24px;
        }

        .lightbox-nav-arrow.next {
            right: 24px;
        }

        /* Lightbox Bottom Strip */
        .lightbox-bottom {
            background: rgba(20, 23, 34, 0.85);
            border-top: 1px solid var(--border);
            padding: 10px 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 10;
        }

        .lightbox-filmstrip {
            display: flex;
            align-items: center;
            gap: 8px;
            overflow-x: auto;
            padding: 4px 0;
            scroll-behavior: smooth;
        }

        .lightbox-filmstrip::-webkit-scrollbar {
            height: 4px;
        }
        .lightbox-filmstrip::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 2px;
        }

        .filmstrip-item {
            width: 54px;
            height: 54px;
            border-radius: var(--radius-sm);
            background: var(--bg-input);
            border: 2px solid transparent;
            object-fit: cover;
            cursor: pointer;
            flex-shrink: 0;
            opacity: 0.6;
            transition: all 0.2s;
        }

        .filmstrip-item:hover {
            opacity: 1;
            transform: scale(1.05);
        }

        .filmstrip-item.active {
            opacity: 1;
            border-color: var(--accent);
            box-shadow: 0 0 10px var(--accent-glow);
            transform: scale(1.08);
        }

        .lightbox-info-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .keyboard-shortcuts {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.72rem;
            color: var(--text-dim);
        }

        .kbd {
            background: var(--bg-input);
            border: 1px solid var(--border);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-muted);
        }

        /* Toast notification */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #1e293b;
            border: 1px solid var(--accent);
            color: #ffffff;
            padding: 10px 18px;
            border-radius: var(--radius-md);
            font-size: 0.85rem;
            font-weight: 600;
            box-shadow: var(--shadow-lg);
            z-index: 9999;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
    </style>
</head>
<body>

    <!-- Top Header -->
    <header>
        <div class="header-brand">
            <div class="brand-logo">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <polyline points="21 15 16 10 5 21"/>
                </svg>
                Trendcarpet Print Gallery
            </div>
            <span class="batch-badge">26-08-27-Print-h-r-g-pt1-x</span>
        </div>

        <div class="header-stats">
            <div class="stat-chip">
                <span>Modeller:</span>
                <strong id="stat-rug-count">10</strong>
            </div>
            <div class="stat-chip">
                <span>Totalt bilder:</span>
                <strong id="stat-total-imgs">234</strong>
            </div>
            <div class="stat-chip">
                <span>Aktuell vy:</span>
                <strong id="stat-showing-count">0</strong>
            </div>
        </div>

        <div class="header-actions">
            <button class="btn-header" onclick="openFolderInExplorer('')" title="Öppna mappen i Utforskaren">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                Öppna Mapp
            </button>
            <button class="btn-header primary" onclick="refreshCatalog()" title="Uppdatera lista">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23 4 23 10 17 10"/>
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
                Uppdatera
            </button>
        </div>
    </header>

    <!-- Main Workspace -->
    <div class="app-container">

        <!-- Left Sidebar: Rugs -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <div class="search-box">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                    <input type="text" id="searchInput" placeholder="Sök matta eller filnamn..." oninput="handleSearch()">
                </div>
            </div>

            <div class="rug-list" id="rugNavList">
                <!-- Dynamically populated -->
            </div>
        </aside>

        <!-- Center Main Content -->
        <main class="content-area">

            <!-- Filter Toolbar -->
            <div class="filter-toolbar">
                <!-- Resolution Switcher -->
                <div class="tab-group" id="resTabs">
                    <button class="tab-btn active" data-res="1500px" onclick="setResolution('1500px')">1500px</button>
                    <button class="tab-btn" data-res="1500px iphone" onclick="setResolution('1500px iphone')">1500px iPhone</button>
                    <button class="tab-btn" data-res="Original" onclick="setResolution('Original')">Original</button>
                    <button class="tab-btn" data-res="ALL" onclick="setResolution('ALL')">Alla Upplösningar</button>
                </div>

                <!-- Type Filters -->
                <div class="filter-chip-group">
                    <button class="filter-chip active" data-type="ALL" onclick="setTypeFilter('ALL')">Alla Bilder</button>
                    <button class="filter-chip" data-type="studio" onclick="setTypeFilter('studio')">Endast Studio (-01, -02...)</button>
                    <button class="filter-chip" data-type="interior" onclick="setTypeFilter('interior')">Endast Miljö / Interiör</button>
                </div>

                <!-- Grid Size View Controls -->
                <div class="view-controls">
                    <button class="grid-size-btn" onclick="setGridSize('sm', event)" title="Liten rutnätsvy">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="7" height="7"/>
                            <rect x="14" y="3" width="7" height="7"/>
                            <rect x="3" y="14" width="7" height="7"/>
                            <rect x="14" y="14" width="7" height="7"/>
                        </svg>
                    </button>
                    <button class="grid-size-btn active" onclick="setGridSize('md', event)" title="Normal rutnätsvy">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="8" height="8"/>
                            <rect x="13" y="3" width="8" height="8"/>
                            <rect x="3" y="13" width="8" height="8"/>
                            <rect x="13" y="13" width="8" height="8"/>
                        </svg>
                    </button>
                    <button class="grid-size-btn" onclick="setGridSize('lg', event)" title="Stor detaljvy">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="18" height="18" rx="2"/>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Gallery Scroll Area -->
            <div class="gallery-scroll" id="galleryScroll">
                <div class="gallery-header-info">
                    <h2 class="gallery-title" id="activeRugTitle">
                        Alla Mattor
                    </h2>
                    <span style="font-size:0.85rem; color:var(--text-muted);" id="activeRugSummary">
                        Visar bilder
                    </span>
                </div>

                <div class="gallery-grid" id="galleryGrid">
                    <!-- Image cards inserted dynamically -->
                </div>
            </div>
        </main>
    </div>

    <!-- Lightbox Modal -->
    <div class="lightbox-modal" id="lightboxModal">
        <div class="lightbox-header">
            <div class="lightbox-title-area">
                <span class="type-badge" id="lbTypeBadge">STUDIO</span>
                <span class="lightbox-filename" id="lbFilename">Filename.jpg</span>
            </div>

            <div class="lightbox-controls">
                <!-- Resolution Quick Switch in Lightbox -->
                <div class="tab-group" style="padding:2px; margin-right: 12px;">
                    <button class="tab-btn" id="lbRes1500" onclick="switchLightboxResolution('1500px')">1500px</button>
                    <button class="tab-btn" id="lbResIphone" onclick="switchLightboxResolution('1500px iphone')">iPhone</button>
                    <button class="tab-btn" id="lbResOrig" onclick="switchLightboxResolution('Original')">Original</button>
                </div>

                <button class="lightbox-btn" onclick="toggleZoom()" title="Zooma in (Z)">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                        <line x1="11" y1="8" x2="11" y2="14"/>
                        <line x1="8" y1="11" x2="14" y2="11"/>
                    </svg>
                    <span id="lbZoomText">Zooma</span>
                </button>

                <button class="lightbox-btn" onclick="openCurrentImageInNewTab()" title="Öppna i ny flik">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                        <polyline points="15 3 21 3 21 9"/>
                        <line x1="10" y1="14" x2="21" y2="3"/>
                    </svg>
                </button>

                <button class="lightbox-btn" onclick="copyCurrentPath()" title="Kopiera filsökväg">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                </button>

                <button class="lightbox-btn-close" onclick="closeLightbox()" title="Stäng (Esc)">
                    ✕ Stäng
                </button>
            </div>
        </div>

        <div class="lightbox-stage" id="lbStage" onwheel="handleWheelZoom(event)" onmousedown="startPan(event)">
            <button class="lightbox-nav-arrow prev" onclick="prevLightboxImage(event)">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="15 18 9 12 15 6"/>
                </svg>
            </button>

            <div class="lightbox-img-container" id="lbImgContainer">
                <img src="" alt="" class="lightbox-img" id="lbImage">
            </div>

            <button class="lightbox-nav-arrow next" onclick="nextLightboxImage(event)">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="9 18 15 12 9 6"/>
                </svg>
            </button>
        </div>

        <div class="lightbox-bottom">
            <div class="lightbox-filmstrip" id="lbFilmstrip">
                <!-- Filmstrip thumbnails -->
            </div>

            <div class="lightbox-info-bar">
                <div id="lbMetaText">1500 x 1500 px • 1.2 MB</div>
                <div class="keyboard-shortcuts">
                    <span>Navigering: <span class="kbd">←</span> <span class="kbd">→</span> <span class="kbd">Mellanslag</span></span>
                    <span>Kvalitet: <span class="kbd">1</span> <span class="kbd">2</span> <span class="kbd">3</span></span>
                    <span>Stäng: <span class="kbd">Esc</span></span>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toast">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span id="toastMsg">Meddelande</span>
    </div>

    <script>
        // Embedded Fallback Data
        const EMBEDDED_CATALOG = __CATALOG_PLACEHOLDER__;

        // State
        let catalogData = EMBEDDED_CATALOG;
        let activeRug = "ALL";
        let activeResolution = "1500px";
        let activeTypeFilter = "ALL";
        let searchQuery = "";
        let visibleImages = [];
        let currentLightboxIndex = 0;
        let zoomScale = 1;
        let isPanning = false;
        let panStart = { x: 0, y: 0 };
        let panOffset = { x: 0, y: 0 };

        // Fetch catalog on init
        async function init() {
            try {
                if (window.location.protocol.startsWith('http')) {
                    const res = await fetch('/api/gallery');
                    if (res.ok) {
                        catalogData = await res.json();
                    }
                }
            } catch (err) {
                console.warn("Using embedded metadata catalog.");
            }
            renderSidebar();
            updateGallery();
        }

        function getImageUrl(relPath) {
            if (window.location.protocol.startsWith('http')) {
                return "/image/" + encodeURIComponent(relPath);
            } else {
                return "file:///C:/Users/AndronikLindgren/OneDrive%20-%20CaMa%20Gruppen%20AB/Pictures/26-08-27-Print-h-r-g-pt1-x/" + encodeURIComponent(relPath);
            }
        }

        // Render Sidebar Rug List
        function renderSidebar() {
            const listEl = document.getElementById('rugNavList');
            if (!listEl) return;
            listEl.innerHTML = "";

            if (!catalogData || !catalogData.rugs) return;

            const rugCountEl = document.getElementById('stat-rug-count');
            const totalImgsEl = document.getElementById('stat-total-imgs');
            if (rugCountEl) rugCountEl.textContent = Object.keys(catalogData.rugs).length;
            if (totalImgsEl) totalImgsEl.textContent = catalogData.all_images.length;

            const allCard = document.createElement('div');
            allCard.className = "rug-card-nav " + (activeRug === 'ALL' ? 'active' : '');
            allCard.onclick = () => selectRug('ALL');
            allCard.innerHTML = `
                <div class="rug-nav-thumb" style="display:flex;align-items:center;justify-content:center;background:#1e2436;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2">
                        <rect x="3" y="3" width="7" height="7"/>
                        <rect x="14" y="3" width="7" height="7"/>
                        <rect x="3" y="14" width="7" height="7"/>
                        <rect x="14" y="14" width="7" height="7"/>
                    </svg>
                </div>
                <div class="rug-nav-info">
                    <div class="rug-nav-title">Alla Mattor</div>
                    <div class="rug-nav-meta">
                        <span>Visa hela samlingen</span>
                    </div>
                </div>
                <span class="rug-nav-badge">${catalogData.all_images.length}</span>
            `;
            listEl.appendChild(allCard);

            for (const [rugName, rugData] of Object.entries(catalogData.rugs)) {
                let previewImgUrl = "";
                const items1500 = rugData.categories["1500px"] || [];
                if (items1500.length > 0) {
                    previewImgUrl = getImageUrl(items1500[0].rel_path);
                } else if (rugData.categories["Original"] && rugData.categories["Original"].length > 0) {
                    previewImgUrl = getImageUrl(rugData.categories["Original"][0].rel_path);
                }

                let cleanName = rugName.replace(/^Rund matta-/, '').replace(/-carpet-teppich$/, '');
                cleanName = cleanName.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');

                const card = document.createElement('div');
                card.className = "rug-card-nav " + (activeRug === rugName ? 'active' : '');
                card.onclick = () => selectRug(rugName);
                card.innerHTML = `
                    <img class="rug-nav-thumb" src="${previewImgUrl}" loading="lazy" alt="${cleanName}">
                    <div class="rug-nav-info">
                        <div class="rug-nav-title" title="${rugName}">${cleanName}</div>
                        <div class="rug-nav-meta">
                            <span>${rugData.total_images} bilder</span>
                        </div>
                    </div>
                    <span class="rug-nav-badge">${(rugData.categories["1500px"] || []).length} st</span>
                `;
                listEl.appendChild(card);
            }
        }

        function selectRug(rugName) {
            activeRug = rugName;
            renderSidebar();
            updateGallery();
        }

        function setResolution(res) {
            activeResolution = res;
            document.querySelectorAll('#resTabs .tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.res === res);
            });
            updateGallery();
        }

        function setTypeFilter(type) {
            activeTypeFilter = type;
            document.querySelectorAll('.filter-chip-group .filter-chip').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.type === type);
            });
            updateGallery();
        }

        function setGridSize(size, ev) {
            const grid = document.getElementById('galleryGrid');
            if (grid) grid.className = "gallery-grid size-" + size;
            document.querySelectorAll('.view-controls .grid-size-btn').forEach(btn => btn.classList.remove('active'));
            if (ev && ev.currentTarget) ev.currentTarget.classList.add('active');
        }

        function handleSearch() {
            searchQuery = document.getElementById('searchInput').value.trim().toLowerCase();
            updateGallery();
        }

        function updateGallery() {
            if (!catalogData) return;

            let images = [];
            if (activeRug === "ALL") {
                images = catalogData.all_images;
            } else if (catalogData.rugs[activeRug]) {
                const rug = catalogData.rugs[activeRug];
                for (const [cat, catImages] of Object.entries(rug.categories)) {
                    images = images.concat(catImages);
                }
            }

            if (activeResolution !== "ALL") {
                images = images.filter(img => img.category === activeResolution);
            }

            if (activeTypeFilter !== "ALL") {
                images = images.filter(img => img.type === activeTypeFilter);
            }

            if (searchQuery) {
                images = images.filter(img => 
                    img.filename.toLowerCase().includes(searchQuery) ||
                    img.rug_name.toLowerCase().includes(searchQuery) ||
                    img.category.toLowerCase().includes(searchQuery)
                );
            }

            visibleImages = images;

            const countEl = document.getElementById('stat-showing-count');
            if (countEl) countEl.textContent = visibleImages.length;
            
            const titleEl = document.getElementById('activeRugTitle');
            const summaryEl = document.getElementById('activeRugSummary');

            if (activeRug === "ALL") {
                if (titleEl) titleEl.textContent = "Alla Mattor";
                if (summaryEl) summaryEl.textContent = visibleImages.length + " bilder visas";
            } else {
                let cleanName = activeRug.replace(/^Rund matta-/, '').replace(/-carpet-teppich$/, '');
                cleanName = cleanName.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
                if (titleEl) titleEl.textContent = cleanName;
                if (summaryEl) summaryEl.textContent = visibleImages.length + " bilder (" + (activeResolution === 'ALL' ? 'Alla versioner' : activeResolution) + ")";
            }

            const gridEl = document.getElementById('galleryGrid');
            if (!gridEl) return;
            gridEl.innerHTML = "";

            if (visibleImages.length === 0) {
                gridEl.innerHTML = `
                    <div style="grid-column: 1/-1; text-align:center; padding: 60px 20px; color: var(--text-dim);">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:12px;">
                            <circle cx="11" cy="11" r="8"/>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                        </svg>
                        <p style="font-size:1.1rem; font-weight:600; color:var(--text-muted);">Inga bilder matchar sökningen</p>
                        <p style="font-size:0.85rem; margin-top:4px;">Prova att ändra filter eller sökord</p>
                    </div>
                `;
                return;
            }

            visibleImages.forEach((img, idx) => {
                const card = document.createElement('div');
                card.className = 'image-card';
                card.onclick = () => openLightbox(idx);

                const imgUrl = getImageUrl(img.rel_path);
                const typeBadgeClass = img.type === 'studio' ? 'studio' : 'interior';
                const typeLabel = img.type === 'studio' ? 'Studio' : 'Miljö';

                const safeRelPath = img.rel_path.replace(/'/g, "\\'");

                card.innerHTML = `
                    <div class="card-img-wrapper">
                        <div class="card-badge-top-left">
                            <span class="type-badge ${typeBadgeClass}">${typeLabel}</span>
                        </div>
                        <div class="card-badge-top-right">
                            <span class="cat-badge">${img.category}</span>
                        </div>
                        <img src="${imgUrl}" loading="lazy" alt="${img.filename}">
                    </div>
                    <div class="card-body">
                        <div class="card-filename" title="${img.filename}">${img.filename}</div>
                        <div class="card-meta-row">
                            <span>${img.width > 0 ? `${img.width}×${img.height}` : ''}</span>
                            <span>${img.file_size_formatted}</span>
                        </div>
                        <div class="card-actions" onclick="event.stopPropagation()">
                            <button class="card-btn" onclick="openLightbox(${idx})">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                                Granska
                            </button>
                            <button class="card-btn" onclick="copyPath('${safeRelPath}')" title="Kopiera sökväg">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                            </button>
                            <button class="card-btn" onclick="openFolderInExplorer('${safeRelPath}')" title="Visa i Utforskaren">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                            </button>
                        </div>
                    </div>
                `;
                gridEl.appendChild(card);
            });
        }

        // Lightbox Functions
        function openLightbox(index) {
            currentLightboxIndex = index;
            const modal = document.getElementById('lightboxModal');
            if (modal) modal.classList.add('active');
            resetZoom();
            updateLightboxContent();
            renderLightboxFilmstrip();
        }

        function closeLightbox() {
            const modal = document.getElementById('lightboxModal');
            if (modal) modal.classList.remove('active');
            resetZoom();
        }

        function updateLightboxContent() {
            if (!visibleImages || visibleImages.length === 0) return;
            if (currentLightboxIndex < 0) currentLightboxIndex = 0;
            if (currentLightboxIndex >= visibleImages.length) currentLightboxIndex = visibleImages.length - 1;

            const img = visibleImages[currentLightboxIndex];
            const imgEl = document.getElementById('lbImage');
            const imgUrl = getImageUrl(img.rel_path);

            if (imgEl) imgEl.src = imgUrl;
            const fnEl = document.getElementById('lbFilename');
            if (fnEl) fnEl.textContent = img.filename;
            
            const typeBadge = document.getElementById('lbTypeBadge');
            if (typeBadge) {
                typeBadge.className = "type-badge " + (img.type === 'studio' ? 'studio' : 'interior');
                typeBadge.textContent = img.type === 'studio' ? 'STUDIO' : 'MILJÖ';
            }

            const btn1500 = document.getElementById('lbRes1500');
            const btnIphone = document.getElementById('lbResIphone');
            const btnOrig = document.getElementById('lbResOrig');
            if (btn1500) btn1500.classList.toggle('active', img.category === '1500px');
            if (btnIphone) btnIphone.classList.toggle('active', img.category === '1500px iphone');
            if (btnOrig) btnOrig.classList.toggle('active', img.category === 'Original');

            let dimText = img.width > 0 ? `${img.width} × ${img.height} px` : '';
            const metaEl = document.getElementById('lbMetaText');
            if (metaEl) metaEl.textContent = dimText + " • " + img.file_size_formatted + " • Modell: " + img.rug_name;

            document.querySelectorAll('.filmstrip-item').forEach((thumb, idx) => {
                thumb.classList.toggle('active', idx === currentLightboxIndex);
            });

            const activeThumb = document.querySelector('.filmstrip-item.active');
            if (activeThumb) {
                activeThumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
        }

        function renderLightboxFilmstrip() {
            const strip = document.getElementById('lbFilmstrip');
            if (!strip) return;
            strip.innerHTML = "";

            visibleImages.forEach((img, idx) => {
                const thumb = document.createElement('img');
                thumb.className = "filmstrip-item " + (idx === currentLightboxIndex ? 'active' : '');
                thumb.src = getImageUrl(img.rel_path);
                thumb.onclick = () => {
                    currentLightboxIndex = idx;
                    resetZoom();
                    updateLightboxContent();
                };
                strip.appendChild(thumb);
            });
        }

        function prevLightboxImage(e) {
            if (e) e.stopPropagation();
            if (currentLightboxIndex > 0) {
                currentLightboxIndex--;
            } else {
                currentLightboxIndex = visibleImages.length - 1;
            }
            resetZoom();
            updateLightboxContent();
        }

        function nextLightboxImage(e) {
            if (e) e.stopPropagation();
            if (currentLightboxIndex < visibleImages.length - 1) {
                currentLightboxIndex++;
            } else {
                currentLightboxIndex = 0;
            }
            resetZoom();
            updateLightboxContent();
        }

        function switchLightboxResolution(targetCategory) {
            const currentImg = visibleImages[currentLightboxIndex];
            if (!currentImg || !catalogData) return;

            const rug = catalogData.rugs[currentImg.rug_name];
            if (rug && rug.categories[targetCategory]) {
                const match = rug.categories[targetCategory].find(i => i.filename.toLowerCase() === currentImg.filename.toLowerCase());
                if (match) {
                    visibleImages[currentLightboxIndex] = match;
                    resetZoom();
                    updateLightboxContent();
                    showToast("Bytte till " + targetCategory);
                    return;
                }
            }
            showToast("Ingen " + targetCategory + "-version hittades.");
        }

        function toggleZoom() {
            if (zoomScale > 1) {
                resetZoom();
            } else {
                setZoom(2.5);
            }
        }

        function setZoom(scale) {
            zoomScale = Math.max(1, Math.min(5, scale));
            const container = document.getElementById('lbImgContainer');
            if (container) {
                container.style.transform = "scale(" + zoomScale + ") translate(" + (panOffset.x / zoomScale) + "px, " + (panOffset.y / zoomScale) + "px)";
            }
            const zText = document.getElementById('lbZoomText');
            if (zText) zText.textContent = zoomScale > 1 ? Math.round(zoomScale * 100) + "%" : 'Zooma';
        }

        function resetZoom() {
            zoomScale = 1;
            panOffset = { x: 0, y: 0 };
            const container = document.getElementById('lbImgContainer');
            if (container) {
                container.style.transform = "scale(1) translate(0px, 0px)";
            }
            const zText = document.getElementById('lbZoomText');
            if (zText) zText.textContent = 'Zooma';
        }

        function handleWheelZoom(e) {
            e.preventDefault();
            const delta = e.deltaY * -0.002;
            const newScale = zoomScale + delta;
            setZoom(newScale);
        }

        function startPan(e) {
            if (zoomScale <= 1) return;
            isPanning = true;
            panStart = { x: e.clientX - panOffset.x, y: e.clientY - panOffset.y };

            const onMouseMove = (ev) => {
                if (!isPanning) return;
                panOffset.x = ev.clientX - panStart.x;
                panOffset.y = ev.clientY - panStart.y;
                setZoom(zoomScale);
            };

            const onMouseUp = () => {
                isPanning = false;
                window.removeEventListener('mousemove', onMouseMove);
                window.removeEventListener('mouseup', onMouseUp);
            };

            window.addEventListener('mousemove', onMouseMove);
            window.addEventListener('mouseup', onMouseUp);
        }

        function openCurrentImageInNewTab() {
            const img = visibleImages[currentLightboxIndex];
            if (img) {
                window.open(getImageUrl(img.rel_path), '_blank');
            }
        }

        function copyCurrentPath() {
            const img = visibleImages[currentLightboxIndex];
            if (img) {
                copyPath(img.rel_path);
            }
        }

        window.addEventListener('keydown', (e) => {
            const modal = document.getElementById('lightboxModal');
            if (!modal || !modal.classList.contains('active')) {
                if (e.key === '/') {
                    const searchInput = document.getElementById('searchInput');
                    if (searchInput) {
                        e.preventDefault();
                        searchInput.focus();
                    }
                }
                return;
            }

            if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
                prevLightboxImage();
            } else if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D' || e.key === ' ') {
                e.preventDefault();
                nextLightboxImage();
            } else if (e.key === 'Escape') {
                closeLightbox();
            } else if (e.key === '1') {
                switchLightboxResolution('1500px');
            } else if (e.key === '2') {
                switchLightboxResolution('1500px iphone');
            } else if (e.key === '3') {
                switchLightboxResolution('Original');
            } else if (e.key === 'z' || e.key === 'Z') {
                toggleZoom();
            } else if (e.key === 'c' || e.key === 'C') {
                copyCurrentPath();
            }
        });

        function copyPath(relPath) {
            const fullPath = "C:\\Users\\AndronikLindgren\\OneDrive - CaMa Gruppen AB\\Pictures\\26-08-27-Print-h-r-g-pt1-x\\" + relPath.replace(/\//g, '\\');
            navigator.clipboard.writeText(fullPath).then(() => {
                showToast("Sökväg kopierad till urklipp!");
            }).catch(() => {
                showToast("Kunde inte kopiera.");
            });
        }

        async function openFolderInExplorer(subpath) {
            try {
                const res = await fetch('/api/open-folder?path=' + encodeURIComponent(subpath));
                if (res.ok) {
                    showToast("Öppnade i Utforskaren!");
                } else {
                    showToast("Kunde inte öppna mappen.");
                }
            } catch (e) {
                showToast("Fel vid anrop till Utforskaren.");
            }
        }

        async function refreshCatalog() {
            showToast("Läser in katalog på nytt...");
            await init();
            showToast("Katalogen uppdaterad!");
        }

        function showToast(msg) {
            const t = document.getElementById('toast');
            if (!t) return;
            const msgEl = document.getElementById('toastMsg');
            if (msgEl) msgEl.textContent = msg;
            t.classList.add('show');
            setTimeout(() => {
                t.classList.remove('show');
            }, 2500);
        }

        window.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
'''

final_html = html_content.replace("__CATALOG_PLACEHOLDER__", catalog_json)

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(final_html)

print("Generated clean gallery.html successfully!")

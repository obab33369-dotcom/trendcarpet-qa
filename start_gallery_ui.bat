@echo off
title Trendcarpet Image Gallery
echo ============================================================
echo Starting Trendcarpet Image Gallery UI...
echo ============================================================

cd /d "c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors"
start "" http://localhost:8090/gallery.html
python gallery_server.py 8090
pause

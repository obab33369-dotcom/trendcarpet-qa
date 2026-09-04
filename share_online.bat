@echo off
title Hatshop Black River - Dela Gransknings-UI Online
echo ========================================================
echo Startar delning av Hatshop Review UI...
echo ========================================================
echo.
echo 1. Se till att hatshop_server.py körs (t.ex. via start_hatshop_ui.bat).
echo 2. Skapar en säker offentlig HTTPS-länk till dina kollegor...
echo.

npx --yes localtunnel --port 8092

pause

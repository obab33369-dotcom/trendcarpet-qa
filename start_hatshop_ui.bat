@echo off
title Hatshop Black River - Retouch & Angle Review UI
echo ========================================================
echo Starting Hatshop Black River Image Review Server...
echo ========================================================

cd /d "%~dp0"
start "" http://localhost:8092
python hatshop_server.py 8092

pause

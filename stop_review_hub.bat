@echo off
title Stoppa Foto QA Hub
echo Stoppar alla aktiva processer for Foto QA Hub...
taskkill /f /im cloudflared.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8092 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
echo Foto QA Hub har stoppats.
pause

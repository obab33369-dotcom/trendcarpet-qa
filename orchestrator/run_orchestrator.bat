@echo off
:: REFORMA Local Orchestrator Startup Script
:: Spawns the background monitor loop daemon in the workspace environment.

title REFORMA Local Orchestrator Loop

:: Ensure execution is relative to the REFORMA root folder
set "REFORMA_DIR=c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
cd /d "%REFORMA_DIR%"

:: Determine Python executable path (Miniconda base environment)
set "PYTHON_EXE=C:\Users\AndronikLindgren\miniconda3\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [WARNING] Conda Python not found at %PYTHON_EXE%
    echo Falling back to default system 'python'...
    set "PYTHON_EXE=python"
)

echo ====================================================
echo  REFORMA AUTOMATION: STARTING LOCAL ORCHESTRATOR
echo ====================================================
echo  Workspace:  %REFORMA_DIR%
echo  Python:     %PYTHON_EXE%
echo  Log File:   %REFORMA_DIR%\orchestrator\orchestrator.log
echo ====================================================
echo.

:: Launch the daemon loop.
:: By default, we launch in --test mode to process a subset of files safely.
:: To run in full production mode, change the argument below to --full.
"%PYTHON_EXE%" "%REFORMA_DIR%\orchestrator\loop.py" --test

if %ERRORLEVEL% neq 0 (
    echo.
    echo [CRITICAL] Orchestrator loop terminated with error code %ERRORLEVEL%.
    echo Check the orchestrator.log file for error tracebacks.
    echo.
    pause
)

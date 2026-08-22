@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 src\deskpilot\app.py
) else (
    python src\deskpilot\app.py
)
if errorlevel 1 pause

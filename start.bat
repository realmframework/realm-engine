@echo off
cd /d "%~dp0"

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: 'uv' is not installed. Install it from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

uv run python main.py --desktop %*
if %errorlevel% neq 0 (
    echo.
    echo REALM Engine exited with error code %errorlevel%.
    pause
    exit /b %errorlevel%
)

@echo off
title d4bot - DEBUG VIEW (sends no keys)
cd /d "%~dp0"
call "%~dp0setup.bat" || goto :end
.venv\Scripts\python.exe main.py debug
:end
echo.
pause

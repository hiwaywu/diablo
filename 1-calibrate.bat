@echo off
title d4bot - CALIBRATE
cd /d "%~dp0"
call "%~dp0setup.bat" || goto :end
.venv\Scripts\python.exe main.py calibrate
:end
echo.
pause

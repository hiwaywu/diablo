@echo off
title d4bot - RUN  (F9 start/pause, F8 re-summon, F12 quit)
cd /d "%~dp0"
call "%~dp0setup.bat" || goto :end
.venv\Scripts\python.exe main.py run
:end
echo.
pause

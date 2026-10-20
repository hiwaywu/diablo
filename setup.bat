@echo off
rem Installs the bot's Python packages the first time. Called by the numbered .bat files.
cd /d "%~dp0"
if exist .venv\Scripts\python.exe exit /b 0
echo First run: installing what the bot needs (takes about a minute)...
python -m venv .venv || (echo Python is not installed. & exit /b 1)
.venv\Scripts\python.exe -m pip install -q -r requirements.txt || exit /b 1
exit /b 0

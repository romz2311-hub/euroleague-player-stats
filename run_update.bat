@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python update_all.py >> update_log.txt 2>&1

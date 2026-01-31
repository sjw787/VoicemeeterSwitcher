@echo off
REM Voicemeeter Settings Switcher - Quick Launch Script
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python main.py

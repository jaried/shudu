@echo off
cd /d "%~dp0"
python sudoku_gui.py %*
if errorlevel 1 pause

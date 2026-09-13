@echo off
cd /d "%~dp0"
uv run python sudoku_gui.py %*
if errorlevel 1 pause

@echo off
chcp 65001 > nul
echo 🔧 ИСПРАВЛЕНИЕ ДУБЛИКАТОВ
echo =========================
echo.
python fix_duplicates.py
echo.
echo Нажмите любую клавишу для выхода...
pause > nul 
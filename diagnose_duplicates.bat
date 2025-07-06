@echo off
chcp 65001 > nul
echo 🔍 ДИАГНОСТИКА ДУБЛИКАТОВ
echo ========================
echo.
python diagnose_duplicates.py
echo.
echo Нажмите любую клавишу для выхода...
pause > nul 
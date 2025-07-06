@echo off
echo Очистка базы данных отправленных постов...
echo ВНИМАНИЕ: После этого бот отправит ВСЕ посты заново!
echo.

cd /d "%~dp0"
venv\Scripts\python.exe clear_database.py

echo.
pause 
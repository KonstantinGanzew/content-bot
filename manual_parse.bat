@echo off
echo Ручной запуск цикла парсинга...
echo Это запустит ОДИН полный цикл парсинга и отправки постов
echo.

cd /d "%~dp0"
venv\Scripts\python.exe manual_run.py

echo.
pause 
#!/usr/bin/env python3
"""
Парсер-бот для JoyReactor и отправки постов в Telegram.
Модульная архитектура позволяет легко добавлять новые ресурсы.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
import os
import platform

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем модули проекта
from config.settings import settings
from scheduler import ParserScheduler
from utils.logger import setup_logging
from utils.database import database

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Глобальный флаг для корректного завершения
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения."""
    logger.info(f"Получен сигнал {signum}. Завершение работы...")
    shutdown_event.set()

def is_process_running(pid):
    """Проверяет, запущен ли процесс с данным PID (кроссплатформенно)."""
    try:
        if platform.system() == "Windows":
            # На Windows используем tasklist
            import subprocess
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return str(pid) in result.stdout
        else:
            # На Unix системах используем os.kill с сигналом 0
            os.kill(pid, 0)
            return True
    except (OSError, ProcessLookupError, subprocess.SubprocessError):
        return False

async def check_single_instance():
    """Проверяет что запущен только один экземпляр бота."""
    lock_file = Path("data/bot.lock")
    
    try:
        # Создаем директорию если её нет
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Проверяем есть ли уже lock файл
        if lock_file.exists():
            # Читаем PID из файла
            try:
                with open(lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Проверяем активен ли процесс
                if is_process_running(old_pid):
                    logger.error(f"❌ Бот уже запущен (PID: {old_pid})")
                    logger.error("   Завершите предыдущий экземпляр или удалите файл data/bot.lock")
                    return False
                else:
                    # Процесс не найден, файл блокировки устарел
                    logger.info("Найден устаревший файл блокировки, удаляем...")
                    lock_file.unlink()
                    
            except (ValueError, FileNotFoundError):
                # Файл поврежден, удаляем
                lock_file.unlink()
        
        # Создаем новый lock файл
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info(f"✅ Создан файл блокировки: {lock_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке блокировки: {e}")
        return False

async def cleanup_on_exit():
    """Очистка при выходе."""
    lock_file = Path("data/bot.lock")
    
    try:
        if lock_file.exists():
            lock_file.unlink()
            logger.info("✅ Файл блокировки удален")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось удалить файл блокировки: {e}")

async def main():
    """Основная функция программы."""
    logger.info("🚀 Запуск Parser Bot")
    
    # Проверяем единственность экземпляра
    if not await check_single_instance():
        return 1
    
    try:
        # Загружаем базу данных
        await database.load()
        
        # Создаем и запускаем планировщик
        scheduler = ParserScheduler()
        
        # Настраиваем обработчики сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Запускаем планировщик
        logger.info("⏰ Запуск планировщика")
        start_task = asyncio.create_task(scheduler.start())
        
        # Ждем сигнал завершения
        await shutdown_event.wait()
        
        # Корректное завершение
        logger.info("🛑 Завершение работы...")
        await scheduler.stop()
        
        # Ждем завершения задач
        if not start_task.done():
            start_task.cancel()
            try:
                await start_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Parser Bot завершен")
        return 0
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        return 1
    finally:
        # Очистка при выходе
        await cleanup_on_exit()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Получен Ctrl+C, завершение...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}")
        sys.exit(1) 
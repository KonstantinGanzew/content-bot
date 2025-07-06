#!/usr/bin/env python3
"""
Парсер-бот для JoyReactor и отправки постов в Telegram.
Модульная архитектура позволяет легко добавлять новые ресурсы.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logging
from config.settings import settings
from scheduler import ParserScheduler
import logging

logger = logging.getLogger(__name__)

class ParserBot:
    """Главный класс приложения."""
    
    def __init__(self):
        self.scheduler = None
        self.running = False
    
    async def start(self):
        """Запускает бота."""
        try:
            # Настраиваем логирование
            setup_logging()
            logger.info("🚀 Запуск парсер-бота")
            
            # Проверяем настройки
            settings.validate()
            logger.info("✓ Настройки проверены")
            
            # Создаем планировщик
            self.scheduler = ParserScheduler()
            
            # Настраиваем обработчики сигналов
            self._setup_signal_handlers()
            
            # Запускаем планировщик
            logger.info("Запуск планировщика...")
            self.running = True
            await self.scheduler.start()
            
        except Exception as e:
            logger.error(f"Ошибка при запуске: {e}")
            return False
        
        return True
    
    async def stop(self):
        """Останавливает бота."""
        if self.running:
            logger.info("🛑 Остановка парсер-бота")
            self.running = False
            
            if self.scheduler:
                await self.scheduler.stop()
            
            logger.info("Бот остановлен")
    
    def _setup_signal_handlers(self):
        """Настраивает обработчики сигналов."""
        def signal_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}")
            # Создаем задачу для остановки
            asyncio.create_task(self.stop())
        
        # Обработчики для graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Главная функция."""
    bot = ParserBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await bot.stop()

def run():
    """Точка входа в приложение."""
    try:
        # Для Windows совместимости
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Запускаем основной цикл
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\nПрерывание пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run() 
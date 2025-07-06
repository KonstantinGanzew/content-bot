#!/usr/bin/env python3
"""
Ручной запуск цикла парсинга
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logging
from config.settings import settings
from scheduler import ParserScheduler
import logging

async def manual_run():
    print("🚀 Ручной запуск цикла парсинга...")
    
    # Настраиваем логирование
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Проверяем настройки
        settings.validate()
        print("✓ Настройки проверены")
        
        # Создаем планировщик
        scheduler = ParserScheduler()
        
        # Загружаем базу данных
        from utils.database import database
        await database.load()
        print("✓ База данных загружена")
        
        # Запускаем ОДИН цикл парсинга
        print("🔄 Запуск цикла парсинга...")
        stats = await scheduler.run_parsing_cycle()
        
        print("\n📊 Результаты:")
        print(f"  📥 Парсено постов: {stats['parsed_posts']}")
        print(f"  🆕 Новых постов: {stats['new_posts']}")
        print(f"  📤 Отправлено: {stats['sent_posts']}")
        print(f"  ❌ Ошибок: {stats['errors']}")
        print(f"  ⏱️ Время выполнения: {(stats.get('end_time', stats['start_time']) - stats['start_time']).total_seconds():.1f}с")
        
        # Закрываем соединения
        await scheduler.stop()
        print("\n✅ Ручной цикл завершен!")
        
    except Exception as e:
        logger.error(f"Ошибка при ручном запуске: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(manual_run()) 
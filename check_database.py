#!/usr/bin/env python3
"""
Проверка состояния базы данных.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from utils.database import database

async def check_database():
    """Проверяет состояние базы данных."""
    print("📊 Проверка базы данных")
    print("=" * 30)
    
    await database.load()
    stats = await database.get_stats()
    
    print(f"✅ База данных работает!")
    print(f"📝 Отправленных постов: {stats['total_sent_posts']}")
    print(f"🔗 URL медиа: {stats['total_sent_media_urls']}")
    print(f"🔐 Хешей медиа: {stats['total_sent_media_hashes']}")
    print(f"💾 Файл БД: {stats['database_file']}")
    print(f"📁 Файл существует: {stats['file_exists']}")
    
    # Проверим несколько последних URL
    print(f"\n🔍 Примеры сохраненных URL:")
    count = 0
    for url in list(database.sent_media_urls)[-5:]:
        count += 1
        print(f"  {count}. {url[:60]}...")
    
    print(f"\n🔐 Примеры сохраненных хешей:")
    count = 0
    for hash_val in list(database.sent_media_hashes)[-5:]:
        count += 1
        print(f"  {count}. {hash_val[:16]}...")

if __name__ == "__main__":
    asyncio.run(check_database()) 
#!/usr/bin/env python3
"""
Тест полного цикла Reddit -> Telegram с проверкой дубликатов.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from parsers.reddit_parser import RedditParser
from telegram.bot import TelegramSender
from utils.database import database
from utils.logger import setup_logging

# Настройка логирования
setup_logging()

async def test_full_cycle():
    """Тестирует полный цикл отправки Reddit поста в Telegram."""
    print("🔄 Тест полного цикла Reddit -> Telegram")
    print("=" * 50)
    
    try:
        # Загружаем базу данных
        await database.load()
        stats = await database.get_stats()
        print(f"📊 База данных: {stats['total_sent_media_urls']} URL, {stats['total_sent_media_hashes']} хешей")
        
        # Создаем компоненты
        telegram_sender = TelegramSender()
        
        print("🔍 Парсинг Reddit постов...")
        
        async with RedditParser() as parser:
            posts = await parser.parse_posts(limit=1)  # Берем только 1 пост
            
            if not posts:
                print("❌ Нет постов для тестирования")
                return
            
            post = posts[0]
            print(f"📝 Пост: {post.title[:50]}...")
            print(f"🔗 URL медиа: {post.media_url}")
            print(f"📱 Тип: {post.media_type}")
            
            # Проверяем URL в базе ДО отправки
            url_before = await database.is_media_url_sent(post.media_url)
            print(f"🔄 URL в базе до отправки: {url_before}")
            
            # Отправляем пост (БЕЗ реальной отправки в Telegram)
            print("📤 Симуляция отправки...")
            
            # Вместо реального send_post делаем только обработку медиа
            from utils.image_manager import image_manager
            
            # Скачиваем файл
            file_path = await image_manager.download_and_save_media(
                post.media_url, post.post_id, post.media_type
            )
            
            if file_path:
                print(f"💾 Файл сохранен: {Path(file_path).name}")
                
                # Вычисляем хеш
                file_hash = image_manager.calculate_file_hash(file_path)
                if file_hash:
                    print(f"🔐 Хеш файла: {file_hash[:16]}...")
                    
                    # Проверяем хеш в базе
                    hash_before = await database.is_media_hash_sent(file_hash)
                    print(f"🔄 Хеш в базе до добавления: {hash_before}")
                    
                    if not hash_before and not url_before:
                        # Добавляем в базу (симулируем успешную отправку)
                        await database.add_media_url(post.media_url)
                        await database.add_media_hash(file_hash)
                        print("✅ Добавлено в базу данных")
                        
                        # Проверяем что добавилось
                        url_after = await database.is_media_url_sent(post.media_url)
                        hash_after = await database.is_media_hash_sent(file_hash)
                        print(f"🔄 URL в базе после добавления: {url_after}")
                        print(f"🔄 Хеш в базе после добавления: {hash_after}")
                        
                    else:
                        print("🔄 Это дубликат - не добавляем в базу")
                        
                else:
                    print("❌ Не удалось вычислить хеш")
            else:
                print("❌ Не удалось скачать файл")
        
        print("\n" + "="*50)
        print("🔄 Повторный тест - проверяем обнаружение дубликата...")
        
        async with RedditParser() as parser:
            posts = await parser.parse_posts(limit=1)  # Тот же пост
            
            if posts:
                post = posts[0]
                print(f"📝 Пост: {post.title[:50]}...")
                
                # Проверяем URL
                url_duplicate = await database.is_media_url_sent(post.media_url)
                print(f"🔄 URL дубликат: {url_duplicate}")
                
                if url_duplicate:
                    print("✅ ДУБЛИКАТ ОБНАРУЖЕН ПО URL!")
                else:
                    print("❌ URL дубликат НЕ обнаружен")
                
                # Проверяем хеш файла
                file_path = await image_manager.download_and_save_media(
                    post.media_url, post.post_id, post.media_type
                )
                
                if file_path:
                    file_hash = image_manager.calculate_file_hash(file_path)
                    if file_hash:
                        hash_duplicate = await database.is_media_hash_sent(file_hash)
                        print(f"🔄 Хеш дубликат: {hash_duplicate}")
                        
                        if hash_duplicate:
                            print("✅ ДУБЛИКАТ ОБНАРУЖЕН ПО ХЕШУ!")
                        else:
                            print("❌ Хеш дубликат НЕ обнаружен")
        
        # Финальная статистика
        stats_final = await database.get_stats()
        print(f"\n📊 Финальная база данных: {stats_final['total_sent_media_urls']} URL, {stats_final['total_sent_media_hashes']} хешей")
        
        print("\n🎯 РЕЗУЛЬТАТ:")
        if url_duplicate or hash_duplicate:
            print("✅ Система проверки дубликатов РАБОТАЕТ!")
        else:
            print("❌ Система проверки дубликатов НЕ РАБОТАЕТ!")
            
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_cycle()) 
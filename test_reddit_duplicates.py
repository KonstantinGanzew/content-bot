#!/usr/bin/env python3
"""
Тест системы проверки дубликатов для Reddit парсера.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from parsers.reddit_parser import RedditParser
from telegram.bot import TelegramSender
from utils.database import database
from utils.logger import setup_logging
from utils.image_manager import image_manager

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

async def test_reddit_duplicates():
    """Тестирует систему проверки дубликатов для Reddit."""
    print("🧪 Тест системы проверки дубликатов для Reddit")
    print("=" * 60)
    
    # Загружаем базу данных
    await database.load()
    
    print(f"📊 Текущая база данных:")
    stats = await database.get_stats()
    print(f"   Постов: {stats['total_sent_posts']}")
    print(f"   URL медиа: {stats['total_sent_media_urls']}")
    print(f"   Хешей медиа: {stats['total_sent_media_hashes']}")
    print()
    
    # Создаем телеграм отправщик для имитации полного процесса
    telegram_sender = TelegramSender()
    
    print("🔍 Первый запуск - парсим посты из Reddit...")
    
    async with RedditParser() as parser:
        posts = await parser.parse_posts(limit=3)  # Берем только 3 поста для теста
        
        if not posts:
            print("❌ Нет постов для тестирования")
            return
        
        print(f"✅ Найдено {len(posts)} постов")
        
        # Обрабатываем каждый пост как если бы отправляли в Telegram
        for i, post in enumerate(posts, 1):
            print(f"\n📤 Обработка поста {i}: {post.title[:50]}...")
            
            # Симулируем процесс отправки (скачивание + проверка дубликатов)
            media_url = post.media_url
            media_type = post.media_type
            
            print(f"   🔗 URL: {media_url}")
            print(f"   📱 Тип: {media_type}")
            
            # Проверяем URL в базе
            url_already_sent = await database.is_media_url_sent(media_url)
            print(f"   🔄 URL уже отправлен: {url_already_sent}")
            
            if not url_already_sent:
                # Скачиваем и сохраняем
                file_path = await image_manager.download_and_save_media(
                    media_url, post.post_id, media_type
                )
                
                if file_path:
                    print(f"   💾 Файл сохранен: {Path(file_path).name}")
                    
                    # Вычисляем хеш
                    file_hash = image_manager.calculate_file_hash(file_path)
                    if file_hash:
                        print(f"   🔐 Хеш: {file_hash[:16]}...")
                        
                        # Проверяем хеш в базе
                        hash_already_sent = await database.is_media_hash_sent(file_hash)
                        print(f"   🔄 Хеш уже отправлен: {hash_already_sent}")
                        
                        if not hash_already_sent:
                            # Добавляем в базу (имитируем успешную отправку)
                            await database.add_media_url(media_url)
                            await database.add_media_hash(file_hash)
                            print(f"   ✅ Добавлено в базу данных")
                        else:
                            print(f"   🔄 Пропускаем - дубликат по хешу")
                    else:
                        print(f"   ❌ Не удалось вычислить хеш")
                else:
                    print(f"   ❌ Не удалось скачать файл")
            else:
                print(f"   🔄 Пропускаем - URL уже в базе")
    
    print(f"\n📊 База данных после первого запуска:")
    stats = await database.get_stats()
    print(f"   Постов: {stats['total_sent_posts']}")
    print(f"   URL медиа: {stats['total_sent_media_urls']}")
    print(f"   Хешей медиа: {stats['total_sent_media_hashes']}")
    
    print(f"\n" + "="*60)
    print("🔄 Второй запуск - проверяем обнаружение дубликатов...")
    
    async with RedditParser() as parser:
        posts = await parser.parse_posts(limit=3)  # Те же посты
        
        duplicates_found = 0
        
        for i, post in enumerate(posts, 1):
            print(f"\n📤 Повторная обработка поста {i}: {post.title[:50]}...")
            
            media_url = post.media_url
            media_type = post.media_type
            
            # Проверяем URL в базе
            url_already_sent = await database.is_media_url_sent(media_url)
            print(f"   🔄 URL уже отправлен: {url_already_sent}")
            
            if url_already_sent:
                duplicates_found += 1
                print(f"   ✅ ДУБЛИКАТ ОБНАРУЖЕН ПО URL!")
                continue
                
            # Если URL новый, проверяем хеш файла
            file_path = await image_manager.download_and_save_media(
                media_url, post.post_id, media_type
            )
            
            if file_path:
                file_hash = image_manager.calculate_file_hash(file_path)
                if file_hash:
                    hash_already_sent = await database.is_media_hash_sent(file_hash)
                    print(f"   🔄 Хеш уже отправлен: {hash_already_sent}")
                    
                    if hash_already_sent:
                        duplicates_found += 1
                        print(f"   ✅ ДУБЛИКАТ ОБНАРУЖЕН ПО ХЕШУ!")
    
    print(f"\n🎯 РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ:")
    print(f"   Дубликатов найдено: {duplicates_found}")
    print(f"   Ожидалось: {len(posts) if posts else 0}")
    
    if duplicates_found == len(posts):
        print("✅ Система проверки дубликатов работает ОТЛИЧНО!")
    else:
        print("❌ Система проверки дубликатов НЕ РАБОТАЕТ!")
        print("🔧 Возможные проблемы:")
        print("   - Хеши не сохраняются в базу данных")
        print("   - Проверка хешей не выполняется")
        print("   - Разные URL указывают на одинаковые файлы")

async def main():
    try:
        await test_reddit_duplicates()
    except Exception as e:
        logger.error(f"💥 Ошибка в тесте: {e}", exc_info=True)
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
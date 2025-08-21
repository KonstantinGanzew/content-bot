#!/usr/bin/env python3
"""
Демонстрация Reddit парсера для r/KafkaFPS.
Простой скрипт для показа найденных постов без отправки в Telegram.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from parsers.reddit_parser import RedditParser

async def demo_reddit_parser():
    """Демонстрация Reddit парсера."""
    print("🎮 Демо Reddit парсера для r/KafkaFPS")
    print("=" * 50)
    print("Этот скрипт покажет найденные посты без отправки в Telegram")
    print()
    
    try:
        async with RedditParser() as parser:
            print("🔍 Ищу последние посты...")
            posts = await parser.parse_posts(limit=5)
            
            if not posts:
                print("❌ Посты не найдены")
                print("Возможные причины:")
                print("- Нет новых постов с изображениями/видео")
                print("- Проблемы с доступом к Reddit")
                return
            
            print(f"✅ Найдено {len(posts)} постов с медиа контентом:")
            print()
            
            for i, post in enumerate(posts, 1):
                print(f"🎯 Пост {i}:")
                print(f"   📝 Заголовок: {post.title}")
                print(f"   🔗 Ссылка: {post.post_url}")
                print(f"   🎥 Медиа: {post.media_type} - {post.media_url}")
                
                if post.has_multiple_media():
                    print(f"   📸 Дополнительно: {len(post.all_media) - 1} файлов")
                
                print()
            
            print("✨ Демонстрация завершена!")
            print("💡 Для полного тестирования используйте: test_reddit_parser.bat")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(demo_reddit_parser()) 
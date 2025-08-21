#!/usr/bin/env python3
"""
Ручное тестирование Reddit парсера для r/KafkaFPS.
Этот скрипт позволяет протестировать парсер без запуска планировщика.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from parsers.reddit_parser import RedditParser
from utils.logger import setup_logging
from config.constants import PARSERS

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

async def test_reddit_parser():
    """Тестирует Reddit парсер."""
    print("🔧 Тестирование Reddit парсера для r/KafkaFPS")
    print("=" * 60)
    
    try:
        # Создаем парсер
        async with RedditParser() as parser:
            print(f"📡 Конфигурация парсера:")
            print(f"   Subreddit: {parser.subreddit}")
            print(f"   JSON URL: {parser.json_url}")
            print(f"   HTML URL: {parser.html_url}")
            print(f"   Использовать JSON API: {parser.use_json_api}")
            print()
            
            # Парсим посты
            print("🔍 Начинаю парсинг постов...")
            posts = await parser.parse_posts(limit=10)
            
            print(f"📊 Результаты парсинга:")
            print(f"   Найдено постов: {len(posts)}")
            print()
            
            if not posts:
                print("❌ Посты не найдены. Возможные причины:")
                print("   - Subreddit недоступен")
                print("   - Нет постов с медиа контентом")
                print("   - Проблемы с сетью")
                print("   - Reddit заблокировал запросы")
                return
            
            # Показываем детали найденных постов
            for i, post in enumerate(posts, 1):
                print(f"📝 Пост {i}:")
                print(f"   ID: {post.post_id}")
                print(f"   Заголовок: {post.title[:80]}{'...' if len(post.title) > 80 else ''}")
                print(f"   URL поста: {post.post_url}")
                print(f"   Основное медиа: {post.media_url}")
                print(f"   Тип медиа: {post.media_type}")
                print(f"   Теги: {', '.join(post.tags)}")
                
                if post.has_multiple_media():
                    print(f"   Всего медиа файлов: {len(post.all_media)}")
                    for j, media in enumerate(post.all_media[:3], 1):  # Показываем первые 3
                        print(f"     {j}. {media['type']}: {media['url'][:60]}...")
                    if len(post.all_media) > 3:
                        print(f"     ... и ещё {len(post.all_media) - 3} файлов")
                
                print()
            
            # Тестируем детали поста
            if posts:
                first_post = posts[0]
                print(f"🔍 Тестирую получение деталей первого поста...")
                post_details = await parser.get_post_details(first_post.post_url)
                
                if post_details:
                    print("✅ Детали поста успешно получены:")
                    print(f"   ID: {post_details.post_id}")
                    print(f"   Заголовок: {post_details.title[:80]}...")
                    print(f"   Медиа: {len(post_details.all_media) if post_details.all_media else 1} файл(ов)")
                else:
                    print("❌ Не удалось получить детали поста")
                
                print()
            
            print("✅ Тестирование завершено успешно!")
            print("\n💡 Для запуска с реальной отправкой в Telegram используйте manual_parse.bat")
            
    except Exception as e:
        logger.error(f"💥 Ошибка при тестировании: {e}", exc_info=True)
        print(f"❌ Произошла ошибка: {e}")
        return False
    
    return True

async def test_json_vs_html():
    """Сравнивает результаты JSON и HTML парсинга."""
    print("\n🔬 Сравнение JSON и HTML парсинга")
    print("=" * 40)
    
    try:
        async with RedditParser() as parser:
            # JSON парсинг
            print("📡 Тестируем JSON API...")
            json_posts = await parser._parse_from_json(5)
            print(f"   JSON API: {len(json_posts)} постов")
            
            # HTML парсинг
            print("🌐 Тестируем HTML парсинг...")
            html_posts = await parser._parse_from_html(5)
            print(f"   HTML: {len(html_posts)} постов")
            
            print(f"\n📊 Результат сравнения:")
            print(f"   JSON API более надежен: {'✅' if len(json_posts) >= len(html_posts) else '❌'}")
            print(f"   HTML fallback работает: {'✅' if len(html_posts) > 0 else '❌'}")
            
    except Exception as e:
        print(f"❌ Ошибка при сравнении: {e}")

def main():
    """Главная функция."""
    print("🚀 Reddit Parser Test Tool")
    print("Для subreddit: r/KafkaFPS")
    print()
    
    # Основной тест
    success = asyncio.run(test_reddit_parser())
    
    if success:
        # Дополнительный тест сравнения
        asyncio.run(test_json_vs_html())
    
    print("\n🏁 Тестирование завершено")

if __name__ == "__main__":
    main() 
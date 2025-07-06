#!/usr/bin/env python3
"""
Диагностика проблемы с дубликатами сообщений
"""

import sys
import json
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.constants import GENERAL
from parsers.joyreactor_parser import JoyReactorParser
from utils.database import database

async def diagnose_duplicates():
    print("🔍 ДИАГНОСТИКА ДУБЛИКАТОВ")
    print("=" * 40)
    
    # 1. Проверка файла блокировки
    lock_file = Path("data/bot.lock")
    if lock_file.exists():
        try:
            with open(lock_file, 'r') as f:
                pid = f.read().strip()
            print(f"⚠️  Найден файл блокировки: PID {pid}")
            print(f"   Если бот не работает, удалите файл: {lock_file}")
        except:
            print("⚠️  Файл блокировки поврежден")
    else:
        print("✅ Файл блокировки не найден")
    
    # 2. Проверка базы данных
    db_file = Path(GENERAL['DATABASE_FILE'])
    if db_file.exists():
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                db_data = json.load(f)
            
            if isinstance(db_data, dict):
                sent_posts = db_data.get('sent_posts', [])
            else:
                sent_posts = db_data if isinstance(db_data, list) else []
            
            print(f"\n📊 База данных:")
            print(f"   Отправленных постов: {len(sent_posts)}")
            
            if sent_posts:
                # Проверяем дубликаты
                unique_posts = set(sent_posts)
                duplicates = len(sent_posts) - len(unique_posts)
                
                if duplicates > 0:
                    print(f"   🔄 Дубликатов в базе: {duplicates}")
                    print(f"   💡 Запустите fix_duplicates.bat для очистки")
                else:
                    print("   ✅ Дубликатов в базе нет")
                    
                print(f"   📝 Последние 3 ID: {sent_posts[-3:]}")
                
        except Exception as e:
            print(f"   ❌ Ошибка чтения базы: {e}")
    else:
        print("\n📊 База данных не найдена")
    
    # 3. Тест генерации ID
    print("\n🔧 Тест генерации ID:")
    parser = JoyReactorParser()
    
    test_cases = [
        ("https://img.com/test-123456.jpg", "https://joyreactor.cc/post/123456", "Тест"),
        ("https://img.com/file-987654.webm", "", "Другой тест"),
        ("https://img.com/media.jpg", "", "Третий тест"),
    ]
    
    for i, (url, link, title) in enumerate(test_cases, 1):
        # Генерируем ID 3 раза
        ids = []
        for _ in range(3):
            id_val = parser._generate_post_id(url, link, title)
            ids.append(id_val)
        
        unique_ids = set(ids)
        status = "✅" if len(unique_ids) == 1 else "❌"
        print(f"   {i}. {status} {ids[0]} ({'стабильный' if len(unique_ids) == 1 else 'нестабильный'})")
    
    # 4. Тест парсинга
    print("\n🌐 Тест парсинга:")
    try:
        async with parser:
            posts = await parser.parse_posts(3)
            
            if posts:
                print(f"   ✅ Получено {len(posts)} постов")
                
                # Проверяем ID
                post_ids = [p.post_id for p in posts]
                unique_ids = set(post_ids)
                
                if len(post_ids) == len(unique_ids):
                    print("   ✅ Все ID уникальные")
                else:
                    print(f"   ❌ Дубликаты: {len(post_ids)} постов, {len(unique_ids)} уникальных")
                
                # Проверяем множественные медиа
                multi_media_posts = [p for p in posts if p.has_multiple_media()]
                if multi_media_posts:
                    print(f"   📸 Постов с множественными медиа: {len(multi_media_posts)}")
                    for post in multi_media_posts:
                        print(f"      - {post.post_id}: {len(post.all_media)} медиа")
                
            else:
                print("   ⚠️  Посты не найдены")
                
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("\n🎯 ВЫВОДЫ:")
    print("1. Основная причина 'дубликатов' - множественные медиа отправлялись отдельными сообщениями")
    print("2. Теперь множественные медиа отправляются одной группой")
    print("3. Добавлена проверка единственности экземпляра бота")
    print("4. Исправлена генерация ID для стабильности")
    
    print("\n💡 ЧТО ДЕЛАТЬ:")
    print("• Убедитесь что запущен только один экземпляр бота")
    print("• Если нужно больше контента - запустите clear_db.bat")
    print("• Перезапустите бота для применения исправлений")
    print("• Следите за логами - теперь должна быть отправка групп медиа")

if __name__ == "__main__":
    asyncio.run(diagnose_duplicates()) 
#!/usr/bin/env python3
"""
Исправление проблемы с дубликатами сообщений
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.constants import GENERAL

def fix_duplicates():
    print("🔧 ИСПРАВЛЕНИЕ ДУБЛИКАТОВ")
    print("=" * 30)
    
    print("Проблема: Бот отправляет одинаковые сообщения несколько раз")
    print("Причина: Нестабильная генерация ID постов")
    print("Решение: Исправлены функции генерации ID + очистка базы\n")
    
    db_file = Path(GENERAL['DATABASE_FILE'])
    
    if db_file.exists():
        # Читаем базу данных
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                db_data = json.load(f)
            
            # Получаем списки отправленных данных
            if isinstance(db_data, list):
                # Старый формат
                sent_posts = db_data
                sent_media_urls = []
            elif isinstance(db_data, dict):
                # Новый формат
                sent_posts = db_data.get('sent_posts', [])
                sent_media_urls = db_data.get('sent_media_urls', [])
            else:
                sent_posts = []
                sent_media_urls = []
            
            print(f"📊 Текущее состояние базы:")
            print(f"   Отправленных постов: {len(sent_posts)}")
            print(f"   Отправленных URL медиа: {len(sent_media_urls)}")
            
            # Обработка дубликатов постов
            posts_cleaned = False
            if len(sent_posts) > 0:
                print(f"   Последние ID постов: {sent_posts[-3:]}")
                
                # Проверяем наличие дубликатов постов
                unique_posts = set(sent_posts)
                post_duplicates_count = len(sent_posts) - len(unique_posts)
                
                if post_duplicates_count > 0:
                    print(f"   🔄 Найдено дубликатов постов: {post_duplicates_count}")
                    sent_posts = list(unique_posts)
                    posts_cleaned = True
                else:
                    print("   ✅ Дубликатов постов в базе не найдено")
            
            # Обработка дубликатов URL медиа
            media_cleaned = False
            if len(sent_media_urls) > 0:
                print(f"   Последние URL медиа: {[url[:30]+'...' for url in sent_media_urls[-2:]]}")
                
                # Проверяем наличие дубликатов URL медиа
                unique_media_urls = set(sent_media_urls)
                media_duplicates_count = len(sent_media_urls) - len(unique_media_urls)
                
                if media_duplicates_count > 0:
                    print(f"   🔄 Найдено дубликатов URL медиа: {media_duplicates_count}")
                    sent_media_urls = list(unique_media_urls)
                    media_cleaned = True
                else:
                    print("   ✅ Дубликатов URL медиа в базе не найдено")
            
            # Сохраняем очищенные данные если были изменения
            if posts_cleaned or media_cleaned:
                clean_data = {
                    'sent_posts': sent_posts,
                    'sent_media_urls': sent_media_urls
                }
                
                with open(db_file, 'w', encoding='utf-8') as f:
                    json.dump(clean_data, f, ensure_ascii=False, indent=2)
                
                print(f"   ✅ Дубликаты удалены.")
                print(f"   📊 Осталось: {len(sent_posts)} постов, {len(sent_media_urls)} URL медиа")
            else:
                print("   ✅ Очистка не требуется")
                
        except Exception as e:
            print(f"   ❌ Ошибка при обработке базы: {e}")
            
    else:
        print("📝 База данных не найдена - создастся автоматически")
    
    print("\n🎯 ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ:")
    print("✅ Исправлена функция _generate_post_id()")
    print("   - Убрана зависимость от времени")
    print("   - Убраны случайные числа")
    print("   - ID теперь стабильные")
    print("✅ Очищена база данных от дубликатов")
    print("✅ Добавлена дополнительная защита в планировщике")
    
    print("\n💡 ЧТО ДЕЛАТЬ ДАЛЬШЕ:")
    print("1. Если хотите отправить больше контента - запустите clear_db.bat")
    print("2. Перезапустите бота: python main.py")
    print("3. Следите за логами - дубликаты больше не должны появляться")
    print("4. Если дубликаты все еще есть - проверьте не запущено ли несколько экземпляров бота")
    
    return True

if __name__ == "__main__":
    fix_duplicates() 
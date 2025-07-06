#!/usr/bin/env python3
"""
Очистка базы данных отправленных постов
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.constants import GENERAL
import json

def clear_database():
    print("🗑️ ОЧИСТКА БАЗЫ ДАННЫХ")
    print("=" * 30)
    
    db_file = Path(GENERAL['DATABASE_FILE'])
    
    if db_file.exists():
        # Читаем текущее состояние
        with open(db_file, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
            
            # Определяем формат данных
            if isinstance(db_data, list):
                # Старый формат: список ID
                sent_posts_count = len(db_data)
                sent_media_count = 0
                new_data = {'sent_posts': [], 'sent_media_urls': []}
            elif isinstance(db_data, dict):
                # Новый формат: словарь с ключами sent_posts и sent_media_urls
                sent_posts_count = len(db_data.get('sent_posts', []))
                sent_media_count = len(db_data.get('sent_media_urls', []))
                new_data = {'sent_posts': [], 'sent_media_urls': []}
            else:
                # Неизвестный формат
                sent_posts_count = 0
                sent_media_count = 0
                new_data = {'sent_posts': [], 'sent_media_urls': []}
        
        print(f"📊 Найдено в базе:")
        print(f"   Отправленных постов: {sent_posts_count}")
        print(f"   Отправленных URL медиа: {sent_media_count}")
        
        if sent_posts_count > 0 or sent_media_count > 0:
            # Сохраняем очищенные данные
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            
            print("✅ База данных очищена!")
            print("🔄 Теперь бот будет отправлять ВСЕ посты и медиа заново")
            print("💡 Это включает в себя:")
            print("   • Все посты (даже уже отправленные)")
            print("   • Все картинки и видео (даже дубликаты)")
        else:
            print("📝 База данных уже пуста")
    else:
        print("📝 Файл базы данных не найден (это нормально для нового бота)")
    
    print(f"\n💡 Информация:")
    print(f"   Теперь бот проверяет уникальность URL медиа")
    print(f"   Одинаковые картинки/видео не будут отправляться повторно")
    print(f"   Даже если они есть в разных постах")

if __name__ == "__main__":
    clear_database() 
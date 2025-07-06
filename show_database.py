#!/usr/bin/env python3
"""
Просмотр содержимого базы данных отправленных постов
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.constants import GENERAL
import json
from datetime import datetime

def show_database():
    print("📊 СОДЕРЖИМОЕ БАЗЫ ДАННЫХ")
    print("=" * 40)
    
    db_file = Path(GENERAL['DATABASE_FILE'])
    
    if not db_file.exists():
        print("📝 Файл базы данных не существует")
        print("   Это означает что бот еще не отправлял посты")
        return
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
        
        # Поддержка разных форматов
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
        
        print(f"📁 Файл: {db_file}")
        print(f"📊 Отправленных постов: {len(sent_posts)}")
        print(f"🔗 Отправленных URL медиа: {len(sent_media_urls)}")
        
        if sent_posts:
            print(f"\n📝 Последние 5 отправленных постов:")
            for i, post_id in enumerate(sent_posts[-5:], 1):
                print(f"   {i:2d}. {post_id}")
            
            if len(sent_posts) > 5:
                print(f"   ... и еще {len(sent_posts) - 5} постов")
        
        if sent_media_urls:
            print(f"\n🔗 Последние 3 отправленных URL медиа:")
            for i, url in enumerate(sent_media_urls[-3:], 1):
                # Показываем только часть URL для читаемости
                short_url = url[:60] + "..." if len(url) > 60 else url
                print(f"   {i}. {short_url}")
            
            if len(sent_media_urls) > 3:
                print(f"   ... и еще {len(sent_media_urls) - 3} URL")
        
        print(f"\n💡 Объяснение:")
        print(f"   • Посты: {len(sent_posts)} - количество обработанных постов")
        print(f"   • URL медиа: {len(sent_media_urls)} - уникальные картинки/видео")
        print(f"   • Бот НЕ отправит повторно одинаковые картинки/видео")
        print(f"   • Даже если они появятся в новых постах")
        
        print(f"\n🔧 Действия:")
        print(f"   clear_db.bat - очистить всю базу для повторной отправки")
        print(f"   fix_duplicates.bat - исправить дубликаты в базе")
        
    except Exception as e:
        print(f"❌ Ошибка при чтении базы: {e}")

if __name__ == "__main__":
    show_database() 
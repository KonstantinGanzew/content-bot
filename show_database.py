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
        
        sent_posts = db_data.get('sent_posts', [])
        stats = db_data.get('stats', {})
        
        print(f"📁 Файл: {db_file}")
        print(f"📊 Всего отправленных постов: {len(sent_posts)}")
        print(f"📈 Статистика: {stats}")
        
        if sent_posts:
            print(f"\n📝 Последние 10 отправленных постов:")
            for i, post_id in enumerate(sent_posts[-10:], 1):
                print(f"   {i:2d}. {post_id}")
            
            if len(sent_posts) > 10:
                print(f"   ... и еще {len(sent_posts) - 10} постов")
        
        print(f"\n💡 Если хотите чтобы бот отправил больше картинок:")
        print(f"   1. Запустите clear_db.bat для очистки базы")
        print(f"   2. Или дождитесь новых постов на сайте")
        
    except Exception as e:
        print(f"❌ Ошибка при чтении базы: {e}")

if __name__ == "__main__":
    show_database() 
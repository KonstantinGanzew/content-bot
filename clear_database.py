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
                sent_count = len(db_data)
                new_data = {'sent_posts': []}
            elif isinstance(db_data, dict):
                # Новый формат: словарь с ключом sent_posts
                sent_count = len(db_data.get('sent_posts', []))
                new_data = {'sent_posts': []}
            else:
                # Неизвестный формат
                sent_count = 0
                new_data = {'sent_posts': []}
        
        print(f"📊 Найдено отправленных постов: {sent_count}")
        
        if sent_count > 0:
            # Сохраняем очищенные данные
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            
            print("✅ База данных очищена!")
            print("🔄 Теперь бот будет отправлять ВСЕ посты заново")
        else:
            print("📝 База данных уже пуста")
    else:
        print("📝 Файл базы данных не найден (это нормально для нового бота)")
    
    print("\n💡 После очистки запустите:")
    print("   manual_parse.bat - для немедленной отправки постов")
    print("   или перезапустите основного бота")

if __name__ == "__main__":
    clear_database() 
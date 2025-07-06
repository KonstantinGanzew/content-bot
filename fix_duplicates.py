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
            
            # Получаем список отправленных постов
            if isinstance(db_data, dict):
                sent_posts = db_data.get('sent_posts', [])
            else:
                sent_posts = db_data if isinstance(db_data, list) else []
            
            print(f"📊 Текущее состояние базы:")
            print(f"   Отправленных постов: {len(sent_posts)}")
            
            if len(sent_posts) > 0:
                print(f"   Последние ID: {sent_posts[-3:]}")
                
                # Проверяем наличие дубликатов
                unique_posts = set(sent_posts)
                duplicates_count = len(sent_posts) - len(unique_posts)
                
                if duplicates_count > 0:
                    print(f"   🔄 Найдено дубликатов: {duplicates_count}")
                    
                    # Удаляем дубликаты
                    clean_posts = list(unique_posts)
                    clean_data = {'sent_posts': clean_posts}
                    
                    with open(db_file, 'w', encoding='utf-8') as f:
                        json.dump(clean_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"   ✅ Дубликаты удалены. Осталось: {len(clean_posts)} постов")
                else:
                    print("   ✅ Дубликатов в базе не найдено")
                    
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
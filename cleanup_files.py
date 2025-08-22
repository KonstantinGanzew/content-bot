#!/usr/bin/env python3
"""
Ручное управление очисткой файлов.
"""

import sys
import argparse
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from utils.image_manager import image_manager
from config.constants import IMAGE_STORAGE

def main():
    parser = argparse.ArgumentParser(description="Управление очисткой сохраненных медиа файлов")
    
    parser.add_argument('--cleanup', action='store_true', 
                       help='Выполнить очистку файлов')
    parser.add_argument('--hours', type=int, default=None,
                       help='Удалить файлы старше указанного количества часов')
    parser.add_argument('--days', type=int, default=None, 
                       help='Удалить файлы старше указанного количества дней')
    parser.add_argument('--max-files', type=int, default=None,
                       help='Максимальное количество файлов в день')
    parser.add_argument('--stats', action='store_true',
                       help='Показать статистику файлов')
    parser.add_argument('--config', action='store_true',
                       help='Показать настройки автоочистки')
    
    args = parser.parse_args()
    
    print("🗑️ Управление очисткой медиа файлов")
    print("=" * 50)
    
    # Показать настройки
    if args.config:
        print("⚙️ НАСТРОЙКИ АВТООЧИСТКИ:")
        print(f"   AUTO_CLEANUP_ENABLED: {IMAGE_STORAGE.get('AUTO_CLEANUP_ENABLED')}")
        print(f"   CLEANUP_INTERVAL_HOURS: {IMAGE_STORAGE.get('CLEANUP_INTERVAL_HOURS')}ч")
        print(f"   FILES_KEEP_HOURS: {IMAGE_STORAGE.get('FILES_KEEP_HOURS')}ч")
        print(f"   MAX_FILES_PER_DAY: {IMAGE_STORAGE.get('MAX_FILES_PER_DAY')}")
        print(f"   IMAGES_DIR: {IMAGE_STORAGE.get('IMAGES_DIR')}")
        print()
    
    # Показать статистику
    if args.stats or not any([args.cleanup, args.config]):
        media_info = image_manager.get_saved_media_info()
        print("📊 СТАТИСТИКА ФАЙЛОВ:")
        print(f"   📁 Всего файлов: {media_info['total_files']}")
        print(f"   💾 Общий размер: {media_info['total_size_mb']} МБ")
        print(f"   📂 Директория: {media_info['base_directory']}")
        print()
    
    # Выполнить очистку
    if args.cleanup:
        print("🗑️ ВЫПОЛНЕНИЕ ОЧИСТКИ...")
        
        # Определяем параметры очистки
        hours = args.hours or IMAGE_STORAGE.get('FILES_KEEP_HOURS', 48)
        days = args.days
        max_files = args.max_files or IMAGE_STORAGE.get('MAX_FILES_PER_DAY')
        
        if hours and not days:
            print(f"   Удаляем файлы старше {hours} часов")
        elif days:
            print(f"   Удаляем файлы старше {days} дней")
            hours = None
        
        if max_files:
            print(f"   Лимит файлов в день: {max_files}")
        
        # Выполняем очистку
        result = image_manager.cleanup_old_files(
            hours_to_keep=hours,
            days_to_keep=days, 
            max_files_per_day=max_files
        )
        
        print("\n📊 РЕЗУЛЬТАТ ОЧИСТКИ:")
        print(f"   🗑️ Удалено файлов: {result['deleted_files']}")
        print(f"   💾 Освобождено места: {result['freed_space_mb']} МБ")
        
        if result['deleted_files'] == 0:
            print("   ✅ Файлы для удаления не найдены")
        else:
            print(f"   ✅ Очистка завершена успешно")
            
            # Показываем обновленную статистику
            media_info = image_manager.get_saved_media_info()
            print(f"\n📊 СТАТИСТИКА ПОСЛЕ ОЧИСТКИ:")
            print(f"   📁 Осталось файлов: {media_info['total_files']}")
            print(f"   💾 Общий размер: {media_info['total_size_mb']} МБ")
    
    # Если ничего не указано, показываем помощь
    if not any([args.cleanup, args.stats, args.config]):
        print("💡 ИСПОЛЬЗОВАНИЕ:")
        print("   python cleanup_files.py --stats          # Показать статистику")
        print("   python cleanup_files.py --config         # Показать настройки") 
        print("   python cleanup_files.py --cleanup        # Очистка (стандартные настройки)")
        print("   python cleanup_files.py --cleanup --hours 24  # Удалить файлы старше 24ч")
        print("   python cleanup_files.py --cleanup --days 7    # Удалить файлы старше 7 дней")

if __name__ == "__main__":
    main() 
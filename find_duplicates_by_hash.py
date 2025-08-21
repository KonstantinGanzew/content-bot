#!/usr/bin/env python3
"""
Скрипт для поиска и удаления дубликатов медиа файлов по хешу.
"""

import sys
import argparse
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from utils.image_manager import image_manager
from config.constants import IMAGE_STORAGE

def main():
    """Основная функция для поиска и удаления дубликатов."""
    parser = argparse.ArgumentParser(description='Поиск и удаление дубликатов медиа файлов по хешу')
    parser.add_argument('--remove', action='store_true', help='Удалить найденные дубликаты')
    parser.add_argument('--keep-newest', action='store_true', help='Оставить самый новый файл (по умолчанию оставляется самый старый)')
    parser.add_argument('--dry-run', action='store_true', help='Показать что будет удалено, но не удалять')
    
    args = parser.parse_args()
    
    print("🔍 Поиск дубликатов медиа файлов по хешу")
    print("=" * 50)
    
    if not IMAGE_STORAGE['SAVE_IMAGES']:
        print("❌ Сохранение медиа файлов отключено")
        print("   Включите параметр SAVE_IMAGES в config/constants.py")
        return
    
    # Проверяем существует ли директория с медиа
    if not image_manager.base_dir.exists():
        print("❌ Директория с медиа файлами не найдена")
        print(f"   Ожидаемая директория: {image_manager.base_dir.absolute()}")
        return
    
    # Находим дубликаты
    duplicates = image_manager.find_duplicates_by_hash()
    
    if not duplicates:
        print("✅ Дубликаты не найдены!")
        return
    
    print(f"📊 Найдено {len(duplicates)} групп дубликатов:")
    print()
    
    total_duplicates = 0
    total_size_saved = 0
    
    for file_hash, files in duplicates.items():
        print(f"🔄 Группа дубликатов (хеш: {file_hash[:16]}...):")
        files_info = []
        
        for file_path in files:
            try:
                path_obj = Path(file_path)
                file_size = path_obj.stat().st_size
                create_time = path_obj.stat().st_ctime
                files_info.append({
                    'path': file_path,
                    'name': path_obj.name,
                    'size': file_size,
                    'time': create_time
                })
            except Exception as e:
                print(f"   ⚠️ Ошибка доступа к файлу {file_path}: {e}")
                continue
        
        if len(files_info) <= 1:
            continue
        
        # Сортируем по времени
        files_info.sort(key=lambda x: x['time'])
        
        # Определяем какой файл оставить
        if args.keep_newest:
            keep_file = files_info[-1]
            remove_files = files_info[:-1]
        else:
            keep_file = files_info[0]
            remove_files = files_info[1:]
        
        print(f"   💾 Оставить: {keep_file['name']} ({keep_file['size']} байт)")
        
        for remove_file in remove_files:
            print(f"   🗑️ Удалить: {remove_file['name']} ({remove_file['size']} байт)")
            total_duplicates += 1
            total_size_saved += remove_file['size']
        
        print()
    
    print(f"📊 Итого к удалению: {total_duplicates} файлов")
    print(f"💾 Освободится места: {total_size_saved / (1024*1024):.2f} МБ")
    
    if args.remove and not args.dry_run:
        print("\n❓ Удалить дубликаты? (y/n): ", end="")
        response = input().lower()
        
        if response in ['y', 'yes', 'да', 'д']:
            print("\n🧹 Удаление дубликатов...")
            removed_count = image_manager.remove_duplicate_files(keep_oldest=not args.keep_newest)
            print(f"✅ Удалено {removed_count} дубликатов")
        else:
            print("❌ Операция отменена")
    elif args.dry_run:
        print("\n🔍 Режим dry-run: файлы не были удалены")
    elif not args.remove:
        print("\n💡 Используйте --remove для удаления дубликатов")
        print("💡 Используйте --dry-run для предпросмотра без удаления")
        print("💡 Используйте --keep-newest чтобы оставить самые новые файлы")

if __name__ == "__main__":
    main() 
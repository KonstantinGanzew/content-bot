#!/usr/bin/env python3
"""
Скрипт для показа статистики сохраненных медиа файлов.
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from utils.image_manager import image_manager
from config.constants import IMAGE_STORAGE

def main():
    """Показывает статистику сохраненных медиа файлов."""
    print("📊 Статистика сохраненных медиа файлов")
    print("=" * 50)
    
    if not IMAGE_STORAGE['SAVE_IMAGES']:
        print("❌ Сохранение медиа файлов отключено")
        print("   Включите параметр SAVE_IMAGES в config/constants.py")
        return
    
    # Получаем информацию о файлах
    media_info = image_manager.get_saved_media_info()
    
    if media_info['total_files'] == 0:
        print("📭 Нет сохраненных медиа файлов")
        print(f"📂 Директория: {media_info['base_directory']}")
        return
    
    print(f"📂 Директория: {media_info['base_directory']}")
    print(f"📁 Всего файлов: {media_info['total_files']}")
    print(f"💾 Общий размер: {media_info['total_size_mb']} МБ")
    print(f"📊 Средний размер файла: {media_info['total_size_mb'] / media_info['total_files']:.2f} МБ")
    
    # Показываем структуру директорий если организация по датам включена
    if IMAGE_STORAGE['ORGANIZE_BY_DATE']:
        print("\n📅 Файлы по датам:")
        base_dir = Path(media_info['base_directory'])
        
        for date_dir in sorted(base_dir.iterdir()):
            if date_dir.is_dir():
                file_count = len(list(date_dir.glob('*')))
                if file_count > 0:
                    print(f"  📆 {date_dir.name}: {file_count} файлов")
    
    print("\n💡 Используйте этот скрипт для мониторинга дискового пространства")

if __name__ == "__main__":
    main() 
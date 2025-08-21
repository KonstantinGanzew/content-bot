import os
import asyncio
import aiofiles
import aiohttp
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Set, List
from urllib.parse import urlparse, quote, urlunparse

from config.constants import IMAGE_STORAGE

logger = logging.getLogger(__name__)

class ImageManager:
    """Класс для управления загрузкой и сохранением изображений на ПК."""
    
    def __init__(self):
        self.base_dir = Path(IMAGE_STORAGE['IMAGES_DIR'])
        self.organize_by_date = IMAGE_STORAGE['ORGANIZE_BY_DATE']
        self.max_filename_length = IMAGE_STORAGE['MAX_FILENAME_LENGTH']
        self.save_images = IMAGE_STORAGE['SAVE_IMAGES']
        
        # Кеш хешей для текущей сессии (чтобы не пересчитывать)
        self._hash_cache: Dict[str, str] = {}
        
        # Создаем базовую директорию если её нет
        if self.save_images:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📂 Директория для изображений: {self.base_dir.absolute()}")
    
    def get_save_directory(self) -> Path:
        """Получает директорию для сохранения с учетом организации по датам."""
        if not self.organize_by_date:
            return self.base_dir
        
        # Создаем папку по текущей дате
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.base_dir / today
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir
    
    def generate_filename(self, media_url: str, post_id: str, media_type: str) -> str:
        """Генерирует уникальное имя файла."""
        # Получаем расширение из URL
        extension = self._get_file_extension(media_url, media_type)
        
        # Создаем базовое имя файла
        base_name = f"{post_id}_{hash(media_url) % 10000}"
        
        # Ограничиваем длину имени файла
        max_base_length = self.max_filename_length - len(extension) - 10  # резерв для счетчика
        if len(base_name) > max_base_length:
            base_name = base_name[:max_base_length]
        
        filename = f"{base_name}{extension}"
        
        # Проверяем на дубликаты и добавляем счетчик если нужно
        save_dir = self.get_save_directory()
        file_path = save_dir / filename
        counter = 1
        
        while file_path.exists():
            counter_str = f"_{counter}"
            max_name_length = self.max_filename_length - len(extension) - len(counter_str)
            if len(base_name) > max_name_length:
                truncated_base = base_name[:max_name_length]
            else:
                truncated_base = base_name
                
            filename = f"{truncated_base}{counter_str}{extension}"
            file_path = save_dir / filename
            counter += 1
            
            if counter > 999:  # Защита от бесконечного цикла
                break
        
        return filename
    
    def _get_file_extension(self, url: str, media_type: str) -> str:
        """Определяет расширение файла из URL."""
        url_lower = url.lower()
        
        if media_type == "video":
            if '.mp4' in url_lower:
                return '.mp4'
            elif '.webm' in url_lower:
                return '.webm'
            elif '.avi' in url_lower:
                return '.avi'
            elif '.mov' in url_lower:
                return '.mov'
            elif '.mkv' in url_lower:
                return '.mkv'
            elif '.flv' in url_lower:
                return '.flv'
            else:
                return '.mp4'  # по умолчанию для видео
        else:  # image
            if '.jpg' in url_lower or '.jpeg' in url_lower:
                return '.jpg'
            elif '.png' in url_lower:
                return '.png'
            elif '.gif' in url_lower:
                return '.gif'
            elif '.webp' in url_lower:
                return '.webp'
            else:
                return '.jpg'  # по умолчанию для изображений
    
    async def download_and_save_media(self, media_url: str, post_id: str, media_type: str) -> Optional[str]:
        """Скачивает и сохраняет медиа файл на ПК."""
        if not self.save_images:
            logger.debug("Сохранение изображений отключено")
            return None
        
        try:
            # Генерируем имя файла
            filename = self.generate_filename(media_url, post_id, media_type)
            save_dir = self.get_save_directory()
            file_path = save_dir / filename
            
            # Если файл уже существует, возвращаем путь к нему
            if file_path.exists():
                logger.info(f"📁 Файл уже существует: {file_path}")
                return str(file_path)
            
            # Кодируем URL для правильной обработки кириллических символов
            encoded_url = self._encode_url(media_url)
            
            logger.info(f"🔽 Скачиваю медиа: {filename}")
            
            # Скачиваем файл
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=60)
                
                async with session.get(encoded_url, timeout=timeout) as response:
                    if response.status == 200:
                        # Сохраняем файл
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        # Проверяем что файл создался корректно
                        if file_path.exists() and file_path.stat().st_size > 0:
                            # Проверяем на дубликат по хешу
                            duplicate_path = self.is_file_duplicate(str(file_path))
                            if duplicate_path:
                                logger.info(f"🔄 Найден дубликат по хешу: {Path(duplicate_path).name}")
                                logger.info(f"🗑️ Удаляем новый файл, используем существующий")
                                
                                # Удаляем только что скачанный файл
                                try:
                                    file_path.unlink()
                                except Exception:
                                    pass
                                
                                return duplicate_path
                            
                            logger.info(f"✅ Медиа сохранено: {file_path}")
                            return str(file_path)
                        else:
                            logger.error(f"❌ Файл не создался или пустой: {file_path}")
                            return None
                    
                    elif response.status == 404:
                        # Пробуем оригинальный URL без кодирования
                        logger.warning(f"⚠️ Файл не найден (404), пробуем оригинальный URL")
                        async with session.get(media_url, timeout=timeout) as fallback_response:
                            if fallback_response.status == 200:
                                async with aiofiles.open(file_path, 'wb') as f:
                                    async for chunk in fallback_response.content.iter_chunked(8192):
                                        await f.write(chunk)
                                
                                if file_path.exists() and file_path.stat().st_size > 0:
                                    # Проверяем на дубликат по хешу (fallback)
                                    duplicate_path = self.is_file_duplicate(str(file_path))
                                    if duplicate_path:
                                        logger.info(f"🔄 Найден дубликат по хешу (fallback): {Path(duplicate_path).name}")
                                        logger.info(f"🗑️ Удаляем новый файл, используем существующий")
                                        
                                        # Удаляем только что скачанный файл
                                        try:
                                            file_path.unlink()
                                        except Exception:
                                            pass
                                        
                                        return duplicate_path
                                    
                                    logger.info(f"✅ Медиа сохранено (fallback): {file_path}")
                                    return str(file_path)
                                else:
                                    logger.error(f"❌ Файл не создался или пустой (fallback): {file_path}")
                                    return None
                            else:
                                logger.error(f"❌ Fallback URL тоже не работает: HTTP {fallback_response.status}")
                                return None
                    else:
                        logger.error(f"❌ Ошибка скачивания: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"💥 Ошибка при скачивании и сохранении {media_url}: {e}")
            return None
    
    def _encode_url(self, media_url: str) -> str:
        """Кодирует URL для правильной обработки кириллических символов."""
        try:
            parsed = urlparse(media_url)
            encoded_path = quote(parsed.path.encode('utf-8'), safe='/')
            encoded_url = urlunparse((
                parsed.scheme, parsed.netloc, encoded_path,
                parsed.params, parsed.query, parsed.fragment
            ))
            return encoded_url
        except Exception:
            return media_url
    
    def get_saved_media_info(self) -> Dict:
        """Получает информацию о сохраненных медиа файлах."""
        if not self.save_images or not self.base_dir.exists():
            return {'total_files': 0, 'total_size': 0}
        
        total_files = 0
        total_size = 0
        
        for file_path in self.base_dir.rglob('*'):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'base_directory': str(self.base_dir.absolute())
        }
    
    def cleanup_old_files(self, days_to_keep: int = 30):
        """Очищает старые файлы (опционально)."""
        if not self.save_images or not self.base_dir.exists():
            return
        
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for file_path in self.base_dir.rglob('*'):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось удалить старый файл {file_path}: {e}")
        
        if deleted_count > 0:
            logger.info(f"🗑️ Удалено {deleted_count} старых файлов")
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Вычисляет SHA256 хеш файла."""
        if file_path in self._hash_cache:
            return self._hash_cache[file_path]
        
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Читаем файл блоками для экономии памяти
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_sha256.update(chunk)
            
            file_hash = hash_sha256.hexdigest()
            self._hash_cache[file_path] = file_hash
            return file_hash
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления хеша для {file_path}: {e}")
            return None
    
    async def calculate_file_hash_async(self, file_path: str) -> Optional[str]:
        """Асинхронно вычисляет SHA256 хеш файла."""
        if file_path in self._hash_cache:
            return self._hash_cache[file_path]
        
        try:
            hash_sha256 = hashlib.sha256()
            async with aiofiles.open(file_path, 'rb') as f:
                # Читаем файл блоками для экономии памяти
                while chunk := await f.read(8192):
                    hash_sha256.update(chunk)
            
            file_hash = hash_sha256.hexdigest()
            self._hash_cache[file_path] = file_hash
            return file_hash
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления хеша для {file_path}: {e}")
            return None
    
    def find_duplicates_by_hash(self) -> Dict[str, List[str]]:
        """Находит дубликаты файлов по хешу."""
        if not self.save_images or not self.base_dir.exists():
            return {}
        
        hash_to_files: Dict[str, List[str]] = {}
        duplicates: Dict[str, List[str]] = {}
        
        logger.info("🔍 Поиск дубликатов по хешу...")
        
        for file_path in self.base_dir.rglob('*'):
            if file_path.is_file():
                file_hash = self.calculate_file_hash(str(file_path))
                if file_hash:
                    if file_hash not in hash_to_files:
                        hash_to_files[file_hash] = []
                    hash_to_files[file_hash].append(str(file_path))
        
        # Находим хеши с несколькими файлами (дубликаты)
        for file_hash, files in hash_to_files.items():
            if len(files) > 1:
                duplicates[file_hash] = files
                logger.info(f"🔄 Найден дубликат: {len(files)} файлов с хешем {file_hash[:16]}...")
        
        logger.info(f"📊 Найдено {len(duplicates)} групп дубликатов")
        return duplicates
    
    def is_file_duplicate(self, file_path: str) -> Optional[str]:
        """Проверяет является ли файл дубликатом существующего. Возвращает путь к оригиналу."""
        if not self.save_images or not self.base_dir.exists():
            return None
        
        file_hash = self.calculate_file_hash(file_path)
        if not file_hash:
            return None
        
        # Ищем файлы с таким же хешем в директории сохранения
        for existing_file in self.base_dir.rglob('*'):
            if existing_file.is_file() and str(existing_file) != file_path:
                existing_hash = self.calculate_file_hash(str(existing_file))
                if existing_hash == file_hash:
                    return str(existing_file)
        
        return None
    
    def remove_duplicate_files(self, keep_oldest: bool = True) -> int:
        """Удаляет дубликаты, оставляя один файл из группы."""
        duplicates = self.find_duplicates_by_hash()
        removed_count = 0
        
        for file_hash, files in duplicates.items():
            if len(files) <= 1:
                continue
            
            # Сортируем файлы по времени создания
            files_with_time = []
            for file_path in files:
                try:
                    path_obj = Path(file_path)
                    create_time = path_obj.stat().st_ctime
                    files_with_time.append((file_path, create_time))
                except Exception:
                    continue
            
            if not files_with_time:
                continue
                
            # Сортируем по времени
            files_with_time.sort(key=lambda x: x[1])
            
            # Определяем какой файл оставить
            if keep_oldest:
                keep_file = files_with_time[0][0]  # Самый старый
                remove_files = [f[0] for f in files_with_time[1:]]
            else:
                keep_file = files_with_time[-1][0]  # Самый новый
                remove_files = [f[0] for f in files_with_time[:-1]]
            
            # Удаляем дубликаты
            for remove_file in remove_files:
                try:
                    Path(remove_file).unlink()
                    logger.info(f"🗑️ Удален дубликат: {Path(remove_file).name}")
                    removed_count += 1
                    
                    # Убираем из кеша
                    if remove_file in self._hash_cache:
                        del self._hash_cache[remove_file]
                        
                except Exception as e:
                    logger.error(f"❌ Не удалось удалить дубликат {remove_file}: {e}")
            
            logger.info(f"💾 Оставлен файл: {Path(keep_file).name}")
        
        if removed_count > 0:
            logger.info(f"🧹 Удалено {removed_count} дубликатов")
        else:
            logger.info("✅ Дубликатов не найдено")
            
        return removed_count

# Создаем глобальный экземпляр
image_manager = ImageManager() 
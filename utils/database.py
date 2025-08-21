import json
import asyncio
import aiofiles
from typing import Set, List, Optional
import logging
from pathlib import Path

from config.settings import settings

logger = logging.getLogger(__name__)

class PostDatabase:
    """Класс для управления базой данных отправленных постов."""
    
    def __init__(self, db_file: Optional[str] = None):
        self.db_file = Path(db_file or settings.DATABASE_FILE or 'data/sent_posts.json')
        self.sent_posts: Set[str] = set()
        self.sent_media_urls: Set[str] = set()  # Новое: отслеживание URL медиа
        self.sent_media_hashes: Set[str] = set()  # Хеши медиа файлов для предотвращения дубликатов
        self._lock = asyncio.Lock()
    
    async def load(self) -> bool:
        """Загружает базу данных из файла."""
        async with self._lock:
            try:
                # Создаем директорию если её нет
                self.db_file.parent.mkdir(parents=True, exist_ok=True)
                
                if not self.db_file.exists():
                    logger.info("Файл базы данных не существует, создаем новый")
                    await self._save_to_file([], [], [])
                    return True
                
                async with aiofiles.open(self.db_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content) if content.strip() else {}
                    
                    # Поддержка разных форматов данных
                    if isinstance(data, list):
                        # Старый формат: список ID
                        self.sent_posts = set(data)
                        self.sent_media_urls = set()
                        self.sent_media_hashes = set()
                    elif isinstance(data, dict):
                        # Новый формат: словарь с ключами sent_posts, sent_media_urls и sent_media_hashes
                        self.sent_posts = set(data.get('sent_posts', []))
                        self.sent_media_urls = set(data.get('sent_media_urls', []))
                        self.sent_media_hashes = set(data.get('sent_media_hashes', []))
                    else:
                        # Пустой или неизвестный формат
                        self.sent_posts = set()
                        self.sent_media_urls = set()
                        self.sent_media_hashes = set()
                
                logger.info(f"Загружено {len(self.sent_posts)} постов, {len(self.sent_media_urls)} URL медиа, {len(self.sent_media_hashes)} хешей")
                return True
                
            except Exception as e:
                logger.error(f"Ошибка при загрузке базы данных: {e}")
                self.sent_posts = set()
                self.sent_media_urls = set()
                self.sent_media_hashes = set()
                return False
    
    async def save(self) -> bool:
        """Сохраняет базу данных в файл."""
        async with self._lock:
            try:
                await self._save_to_file(list(self.sent_posts), list(self.sent_media_urls), list(self.sent_media_hashes))
                logger.debug(f"База данных сохранена: {len(self.sent_posts)} постов, {len(self.sent_media_urls)} URL медиа, {len(self.sent_media_hashes)} хешей")
                return True
                
            except Exception as e:
                logger.error(f"Ошибка при сохранении базы данных: {e}")
                return False
    
    async def _save_to_file(self, posts: List[str], media_urls: List[str], media_hashes: List[str]):
        """Сохраняет данные в файл."""
        # Сохраняем в новом формате (словарь с отдельными массивами)
        save_data = {
            'sent_posts': posts,
            'sent_media_urls': media_urls,
            'sent_media_hashes': media_hashes
        }
        async with aiofiles.open(self.db_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(save_data, indent=2, ensure_ascii=False))
    
    async def add_post(self, post_id: str) -> bool:
        """Добавляет пост в базу отправленных."""
        async with self._lock:
            if post_id not in self.sent_posts:
                self.sent_posts.add(post_id)
                await self._save_to_file(list(self.sent_posts), list(self.sent_media_urls), list(self.sent_media_hashes))
                logger.debug(f"Добавлен пост в базу: {post_id}")
                return True
            return False
    
    async def add_media_url(self, media_url: str) -> bool:
        """Добавляет URL медиа в базу отправленных."""
        async with self._lock:
            if media_url not in self.sent_media_urls:
                self.sent_media_urls.add(media_url)
                await self._save_to_file(list(self.sent_posts), list(self.sent_media_urls), list(self.sent_media_hashes))
                logger.debug(f"Добавлен URL медиа в базу: {media_url}")
                return True
            return False
    
    async def add_media_hash(self, media_hash: str) -> bool:
        """Добавляет хеш медиа в базу отправленных."""
        async with self._lock:
            if media_hash not in self.sent_media_hashes:
                self.sent_media_hashes.add(media_hash)
                await self._save_to_file(list(self.sent_posts), list(self.sent_media_urls), list(self.sent_media_hashes))
                logger.debug(f"Добавлен хеш медиа в базу: {media_hash[:16]}...")
                return True
            return False
    
    async def is_post_sent(self, post_id: str) -> bool:
        """Проверяет был ли пост уже отправлен."""
        return post_id in self.sent_posts
    
    async def is_media_url_sent(self, media_url: str) -> bool:
        """Проверяет был ли URL медиа уже отправлен."""
        return media_url in self.sent_media_urls
    
    async def is_media_hash_sent(self, media_hash: str) -> bool:
        """Проверяет был ли хеш медиа уже отправлен."""
        return media_hash in self.sent_media_hashes
    
    async def remove_post(self, post_id: str) -> bool:
        """Удаляет пост из базы (для тестирования)."""
        async with self._lock:
            if post_id in self.sent_posts:
                self.sent_posts.remove(post_id)
                await self._save_to_file(list(self.sent_posts), list(self.sent_media_urls), list(self.sent_media_hashes))
                logger.debug(f"Удален пост из базы: {post_id}")
                return True
            return False
    
    async def remove_media_url(self, media_url: str) -> bool:
        """Удаляет URL медиа из базы (для тестирования)."""
        async with self._lock:
            if media_url in self.sent_media_urls:
                self.sent_media_urls.remove(media_url)
                await self._save_to_file(list(self.sent_posts), list(self.sent_media_urls), list(self.sent_media_hashes))
                logger.debug(f"Удален URL медиа из базы: {media_url}")
                return True
            return False
    
    async def remove_media_hash(self, media_hash: str) -> bool:
        """Удаляет хеш медиа из базы (для тестирования)."""
        async with self._lock:
            if media_hash in self.sent_media_hashes:
                self.sent_media_hashes.remove(media_hash)
                await self._save_to_file(list(self.sent_posts), list(self.sent_media_urls), list(self.sent_media_hashes))
                logger.debug(f"Удален хеш медиа из базы: {media_hash[:16]}...")
                return True
            return False
    
    async def filter_new_posts(self, posts: List) -> List:
        """Фильтрует только новые посты."""
        new_posts = []
        
        for post in posts:
            post_id = getattr(post, 'post_id', str(post))
            if not await self.is_post_sent(post_id):
                new_posts.append(post)
        
        logger.info(f"Из {len(posts)} постов, {len(new_posts)} новых")
        return new_posts
    
    async def add_multiple_posts(self, post_ids: List[str]) -> int:
        """Добавляет несколько постов в базу."""
        async with self._lock:
            added_count = 0
            
            for post_id in post_ids:
                if post_id not in self.sent_posts:
                    self.sent_posts.add(post_id)
                    added_count += 1
            
            if added_count > 0:
                await self._save_to_file(list(self.sent_posts), list(self.sent_media_urls), list(self.sent_media_hashes))
                logger.info(f"Добавлено {added_count} постов в базу")
            
            return added_count
    
    async def get_stats(self) -> dict:
        """Возвращает статистику базы данных."""
        return {
            'total_sent_posts': len(self.sent_posts),
            'total_sent_media_urls': len(self.sent_media_urls),
            'total_sent_media_hashes': len(self.sent_media_hashes),
            'database_file': str(self.db_file),
            'file_exists': self.db_file.exists()
        }
    
    async def clear(self) -> bool:
        """Очищает базу данных (для тестирования)."""
        async with self._lock:
            try:
                self.sent_posts.clear()
                self.sent_media_urls.clear()
                self.sent_media_hashes.clear()
                await self._save_to_file(list(self.sent_posts), list(self.sent_media_urls), list(self.sent_media_hashes))
                logger.warning("База данных очищена")
                return True
            except Exception as e:
                logger.error(f"Ошибка при очистке базы данных: {e}")
                return False

# Глобальный экземпляр базы данных
database = PostDatabase() 
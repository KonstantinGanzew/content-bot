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
        self._lock = asyncio.Lock()
    
    async def load(self) -> bool:
        """Загружает базу данных из файла."""
        async with self._lock:
            try:
                # Создаем директорию если её нет
                self.db_file.parent.mkdir(parents=True, exist_ok=True)
                
                if not self.db_file.exists():
                    logger.info("Файл базы данных не существует, создаем новый")
                    await self._save_to_file([])
                    return True
                
                async with aiofiles.open(self.db_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content) if content.strip() else []
                    
                    # Поддержка разных форматов данных
                    if isinstance(data, list):
                        # Старый формат: список ID
                        self.sent_posts = set(data)
                    elif isinstance(data, dict):
                        # Новый формат: словарь с ключом sent_posts
                        self.sent_posts = set(data.get('sent_posts', []))
                    else:
                        # Пустой или неизвестный формат
                        self.sent_posts = set()
                
                logger.info(f"Загружено {len(self.sent_posts)} отправленных постов")
                return True
                
            except Exception as e:
                logger.error(f"Ошибка при загрузке базы данных: {e}")
                self.sent_posts = set()
                return False
    
    async def save(self) -> bool:
        """Сохраняет базу данных в файл."""
        async with self._lock:
            try:
                await self._save_to_file(list(self.sent_posts))
                logger.debug(f"База данных сохранена: {len(self.sent_posts)} постов")
                return True
                
            except Exception as e:
                logger.error(f"Ошибка при сохранении базы данных: {e}")
                return False
    
    async def _save_to_file(self, data: List[str]):
        """Сохраняет данные в файл."""
        # Всегда сохраняем в новом формате (словарь)
        save_data = {'sent_posts': data}
        async with aiofiles.open(self.db_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(save_data, indent=2, ensure_ascii=False))
    
    async def add_post(self, post_id: str) -> bool:
        """Добавляет пост в базу отправленных."""
        async with self._lock:
            if post_id not in self.sent_posts:
                self.sent_posts.add(post_id)
                await self._save_to_file(list(self.sent_posts))
                logger.debug(f"Добавлен пост в базу: {post_id}")
                return True
            return False
    
    async def is_post_sent(self, post_id: str) -> bool:
        """Проверяет был ли пост уже отправлен."""
        return post_id in self.sent_posts
    
    async def remove_post(self, post_id: str) -> bool:
        """Удаляет пост из базы (для тестирования)."""
        async with self._lock:
            if post_id in self.sent_posts:
                self.sent_posts.remove(post_id)
                await self._save_to_file(list(self.sent_posts))
                logger.debug(f"Удален пост из базы: {post_id}")
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
                await self._save_to_file(list(self.sent_posts))
                logger.info(f"Добавлено {added_count} постов в базу")
            
            return added_count
    
    async def get_stats(self) -> dict:
        """Возвращает статистику базы данных."""
        return {
            'total_sent_posts': len(self.sent_posts),
            'database_file': str(self.db_file),
            'file_exists': self.db_file.exists()
        }
    
    async def clear(self) -> bool:
        """Очищает базу данных (для тестирования)."""
        async with self._lock:
            try:
                self.sent_posts.clear()
                await self._save_to_file(list(self.sent_posts))
                logger.warning("База данных очищена")
                return True
            except Exception as e:
                logger.error(f"Ошибка при очистке базы данных: {e}")
                return False

# Глобальный экземпляр базы данных
database = PostDatabase() 
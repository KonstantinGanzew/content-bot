import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging
from urllib.parse import urljoin, urlparse
import os

from config.constants import DEFAULT_HEADERS

logger = logging.getLogger(__name__)

class PostData:
    """Класс для хранения данных поста."""
    
    def __init__(self, post_id: str, media_url: str = "", title: str = "", description: str = "", 
                 post_url: str = "", tags: Optional[List[str]] = None, media_type: str = "image",
                 all_media: Optional[List[Dict]] = None):
        self.post_id = post_id
        self.media_url = media_url  # URL для основного медиа (для обратной совместимости)
        self.title = title
        self.description = description
        self.post_url = post_url
        self.tags = tags or []
        self.media_type = media_type  # "image" или "video" для основного медиа
        self.all_media = all_media or []  # Список всех медиа [{url, type}, ...]
        
        # Если all_media пустой, но есть основное медиа, добавляем его
        if not self.all_media and self.media_url:
            self.all_media = [{'url': self.media_url, 'type': self.media_type}]
    
    # Для обратной совместимости
    @property
    def image_url(self):
        return self.media_url if self.media_type == "image" else None
    
    @property
    def video_url(self):
        return self.media_url if self.media_type == "video" else None
    
    def is_video(self) -> bool:
        return self.media_type == "video"
    
    def is_image(self) -> bool:
        return self.media_type == "image"
    
    def has_multiple_media(self) -> bool:
        """Проверяет есть ли несколько медиа файлов."""
        return len(self.all_media) > 1
    
    def get_images(self) -> List[Dict]:
        """Возвращает только изображения."""
        return [media for media in self.all_media if media['type'] == 'image']
    
    def get_videos(self) -> List[Dict]:
        """Возвращает только видео."""
        return [media for media in self.all_media if media['type'] == 'video']
    
    def get_primary_media(self) -> Dict:
        """Возвращает основное медиа (первое видео или первое изображение)."""
        if self.all_media:
            # Приоритет видео
            videos = self.get_videos()
            if videos:
                return videos[0]
            # Иначе первое изображение
            images = self.get_images()
            if images:
                return images[0]
            # Иначе первое любое медиа
            return self.all_media[0]
        return {'url': self.media_url, 'type': self.media_type}
    
    def __dict__(self):
        return {
            'post_id': self.post_id,
            'media_url': self.media_url,
            'media_type': self.media_type,
            'title': self.title,
            'description': self.description,
            'post_url': self.post_url,
            'tags': self.tags,
            'all_media': self.all_media
        }

class BaseParser(ABC):
    """Базовый класс для всех парсеров."""
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url
        self.headers = headers or DEFAULT_HEADERS
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> str:
        """Получает HTML страницы."""
        if not self.session:
            logger.error("Сессия не инициализирована")
            return ""
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Ошибка при получении страницы {url}: статус {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Ошибка при запросе к {url}: {e}")
            return ""
    
    async def fetch_image_info(self, image_url: str) -> Optional[Dict]:
        """Получает информацию о изображении."""
        if not self.session:
            logger.error("Сессия не инициализирована")
            return None
        
        try:
            async with self.session.head(image_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = int(response.headers.get('content-length', 0))
                    
                    return {
                        'url': image_url,
                        'content_type': content_type,
                        'size': content_length
                    }
        except Exception as e:
            logger.error(f"Ошибка при получении информации об изображении {image_url}: {e}")
        
        return None
    
    def resolve_url(self, url: str) -> str:
        """Преобразует относительный URL в абсолютный."""
        if url.startswith('http'):
            return url
        return urljoin(self.base_url, url)
    
    def is_valid_image_url(self, url: str) -> bool:
        """Проверяет является ли URL изображением."""
        if not url:
            return False
        
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Проверяем расширение файла
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        return any(path.endswith(ext) for ext in image_extensions)
    
    def is_valid_video_url(self, url: str) -> bool:
        """Проверяет является ли URL видео."""
        if not url:
            return False
        
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Проверяем расширение файла
        video_extensions = ['.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv', '.m4v', '.3gp']
        return any(path.endswith(ext) for ext in video_extensions)
    
    def get_media_type(self, url: str) -> str:
        """Определяет тип медиа (image/video) по URL."""
        if self.is_valid_video_url(url):
            return "video"
        elif self.is_valid_image_url(url):
            return "image"
        else:
            return "unknown"
    
    @abstractmethod
    async def parse_posts(self, limit: int = 10) -> List[PostData]:
        """Парсит посты с ресурса. Должен быть реализован в наследниках."""
        pass
    
    @abstractmethod
    async def get_post_details(self, post_url: str) -> Optional[PostData]:
        """Получает детальную информацию о посте. Должен быть реализован в наследниках."""
        pass 
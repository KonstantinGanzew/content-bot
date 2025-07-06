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
    
    def __init__(self, post_id: str, image_url: str, title: str = "", description: str = "", 
                 post_url: str = "", tags: Optional[List[str]] = None):
        self.post_id = post_id
        self.image_url = image_url
        self.title = title
        self.description = description
        self.post_url = post_url
        self.tags = tags or []
    
    def __dict__(self):
        return {
            'post_id': self.post_id,
            'image_url': self.image_url,
            'title': self.title,
            'description': self.description,
            'post_url': self.post_url,
            'tags': self.tags
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
    
    @abstractmethod
    async def parse_posts(self, limit: int = 10) -> List[PostData]:
        """Парсит посты с ресурса. Должен быть реализован в наследниках."""
        pass
    
    @abstractmethod
    async def get_post_details(self, post_url: str) -> Optional[PostData]:
        """Получает детальную информацию о посте. Должен быть реализован в наследниках."""
        pass 
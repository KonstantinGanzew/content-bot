import json
import re
import asyncio
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging
import aiohttp

from .base_parser import BaseParser, PostData
from config.constants import PARSERS, CONTENT_FILTERS

logger = logging.getLogger(__name__)

class RedditParser(BaseParser):
    """Парсер для Reddit subreddit"""
    
    def __init__(self):
        self.config = PARSERS['REDDIT']
        super().__init__(self.config['BASE_URL'])
        
        # Переопределяем заголовки для Reddit
        self.headers = self.config['HEADERS'].copy()
        self.headers['User-Agent'] = self.config['USER_AGENT']
        
        self.subreddit = self.config['SUBREDDIT']
        self.json_url = self.config['JSON_URL']
        self.html_url = self.config['HTML_URL']
        self.use_json_api = self.config['USE_JSON_API']
        self.request_delay = self.config['REQUEST_DELAY']
        self.image_selectors = self.config['IMAGE_SELECTORS']
        
        self.logger = logging.getLogger(__name__)
    
    async def parse_posts(self, limit: int = 10) -> List[PostData]:
        """Парсинг постов с Reddit"""
        posts = []
        
        try:
            # Пробуем сначала JSON API
            if self.use_json_api:
                posts = await self._parse_from_json(limit)
                if posts:
                    self.logger.info(f"✅ Успешно получено {len(posts)} постов через JSON API")
                    return posts
                else:
                    self.logger.warning("⚠️ JSON API не вернул результатов, пробуем HTML")
            
            # Fallback на HTML парсинг
            posts = await self._parse_from_html(limit)
            self.logger.info(f"✅ Успешно получено {len(posts)} постов через HTML парсинг")
            
        except Exception as e:
            self.logger.error(f"💥 Ошибка при парсинге Reddit: {e}")
            
        return posts
    
    async def _parse_from_json(self, limit: int) -> List[PostData]:
        """Парсинг постов через Reddit JSON API"""
        posts = []
        seen_ids = set()
        
        try:
            # Добавляем параметры для JSON запроса
            json_url_with_params = f"{self.json_url}?limit={min(limit * 2, 50)}&raw_json=1"
            
            self.logger.info(f"📡 Загружаю JSON с Reddit: {json_url_with_params}")
            
            html_content = await self.fetch_page(json_url_with_params)
            if not html_content:
                return posts
            
            # Парсим JSON
            try:
                data = json.loads(html_content)
                if not isinstance(data, dict) or 'data' not in data:
                    self.logger.error("❌ Неверная структура JSON ответа от Reddit")
                    return posts
                
                children = data['data'].get('children', [])
                self.logger.info(f"📊 Найдено {len(children)} постов в JSON")
                
                for child in children[:limit * 2]:  # Берем больше для фильтрации
                    if len(posts) >= limit:
                        break
                        
                    if child.get('kind') != 't3':  # t3 = пост
                        continue
                    
                    post_data_raw = child.get('data', {})
                    post_obj = await self._extract_post_from_json(post_data_raw)
                    
                    if post_obj and post_obj.post_id not in seen_ids:
                        # Фильтрация контента
                        if not self._should_filter_post(post_obj):
                            posts.append(post_obj)
                            seen_ids.add(post_obj.post_id)
                            self.logger.info(f"✅ Добавлен пост: {post_obj.title[:50]}...")
                        else:
                            self.logger.debug(f"🚫 Отфильтрован пост: {post_obj.title[:50]}...")
                
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ Ошибка парсинга JSON: {e}")
                return posts
                
        except Exception as e:
            self.logger.error(f"💥 Ошибка при JSON парсинге: {e}")
        
        return posts
    
    async def _extract_post_from_json(self, post_data: Dict) -> Optional[PostData]:
        """Извлечение данных поста из JSON"""
        try:
            post_id = post_data.get('id')
            if not post_id:
                return None
            
            title = post_data.get('title', 'Без заголовка')
            description = post_data.get('selftext', '').strip()  # Описание поста
            permalink = post_data.get('permalink', '')
            post_url = f"{self.base_url}{permalink}" if permalink else ''
            
            # Проверяем различные типы контента
            media_items = []
            seen_file_ids = set()  # Для отслеживания дубликатов по ID файла
            is_video_post = post_data.get('is_video', False)  # Определяем тип поста сразу
            
            # 1. Прямые изображения Reddit (исключаем превью для видео постов)
            url = post_data.get('url', '')
            if url and self._is_reddit_image_url(url):
                # Для видео постов не добавляем external-preview (это превью к видео)
                if is_video_post and 'external-preview.redd.it' in url:
                    pass  # Пропускаем превью для видео постов
                else:
                    file_id = self._extract_reddit_file_id(url)
                    if file_id and file_id not in seen_file_ids:
                        media_items.append({'url': url, 'type': 'image'})
                        seen_file_ids.add(file_id)
            
            # 2. Reddit video
            if is_video_post and 'media' in post_data and post_data['media']:
                reddit_video = post_data['media'].get('reddit_video', {})
                if reddit_video and 'fallback_url' in reddit_video:
                    video_url = reddit_video['fallback_url']
                    
                    # Попытаемся получить версию со звуком
                    # Reddit DASH видео часто без звука, попробуем найти лучшую версию
                    if 'DASH_' in video_url and '?source=fallback' in video_url:
                        # Убираем source=fallback чтобы получить оригинальное качество
                        better_video_url = video_url.replace('?source=fallback', '')
                        media_items.append({'url': better_video_url, 'type': 'video'})
                    else:
                        media_items.append({'url': video_url, 'type': 'video'})
            
            # 3. Preview изображения (только если НЕ видео пост и оригинал не найден)
            preview = post_data.get('preview', {})
            if not is_video_post and preview and 'images' in preview:
                for image in preview['images']:
                    if 'source' in image and 'url' in image['source']:
                        img_url = image['source']['url']
                        # Декодируем HTML entities
                        img_url = img_url.replace('&amp;', '&')
                        if self.is_valid_image_url(img_url):
                            file_id = self._extract_reddit_file_id(img_url)
                            if file_id and file_id not in seen_file_ids:
                                media_items.append({'url': img_url, 'type': 'image'})
                                seen_file_ids.add(file_id)
            
            # 4. Галерея изображений
            if post_data.get('is_gallery') and 'media_metadata' in post_data:
                gallery_metadata = post_data['media_metadata']
                gallery_data = post_data.get('gallery_data', {}).get('items', [])
                
                for item in gallery_data:
                    media_id = item.get('media_id')
                    if media_id in gallery_metadata:
                        media_info = gallery_metadata[media_id]
                        if 's' in media_info and 'u' in media_info['s']:
                            img_url = media_info['s']['u'].replace('&amp;', '&')
                            if self.is_valid_image_url(img_url):
                                media_items.append({'url': img_url, 'type': 'image'})
            
            # 5. Внешние изображения (imgur, etc.)
            if url and not media_items:
                if self.is_valid_image_url(url):
                    media_items.append({'url': url, 'type': 'image'})
                elif self.is_valid_video_url(url):
                    media_items.append({'url': url, 'type': 'video'})
                elif 'imgur.com' in url and not url.endswith('.gifv'):
                    # Попробуем конвертировать imgur ссылку
                    img_url = self._convert_imgur_url(url)
                    if img_url:
                        media_items.append({'url': img_url, 'type': 'image'})
            
            if not media_items:
                return None
            
            # Берем первый медиа файл как основной
            primary_media = media_items[0]
            
            return PostData(
                post_id=f"reddit_{post_id}",
                media_url=primary_media['url'],
                title=title,
                description=description,
                post_url=post_url,
                tags=[f"r/{self.subreddit}"],
                media_type=primary_media['type'],
                all_media=media_items
            )
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения поста из JSON: {e}")
            return None
    
    def _is_reddit_image_url(self, url: str) -> bool:
        """Проверяет является ли URL изображением Reddit"""
        reddit_image_domains = ['i.redd.it', 'preview.redd.it', 'external-preview.redd.it']
        return any(domain in url for domain in reddit_image_domains) and self.is_valid_image_url(url)
    
    def _extract_reddit_file_id(self, url: str) -> Optional[str]:
        """Извлекает ID файла из Reddit URL для дедупликации"""
        try:
            if 'redd.it' not in url:
                return None
            
            # Извлекаем имя файла из URL
            # Для i.redd.it/filename.ext или preview.redd.it/filename.ext?params
            filename = url.split('/')[-1].split('?')[0]  # Убираем GET параметры
            file_id = filename.split('.')[0]  # Убираем расширение
            
            return file_id if file_id else None
            
        except Exception:
            return None
    
    def _convert_imgur_url(self, url: str) -> Optional[str]:
        """Конвертирует Imgur URL в прямую ссылку на изображение"""
        try:
            if 'imgur.com' in url:
                # Извлекаем ID из различных форматов Imgur URL
                if '/a/' in url or '/gallery/' in url:
                    return None  # Альбомы пропускаем
                
                # Прямая ссылка на изображение
                if url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    return url
                
                # Конвертируем ссылку на страницу в прямую ссылку
                match = re.search(r'imgur\.com/([a-zA-Z0-9]+)', url)
                if match:
                    img_id = match.group(1)
                    return f"https://i.imgur.com/{img_id}.jpg"  # Пробуем .jpg по умолчанию
            
            return None
        except Exception:
            return None
    
    async def _parse_from_html(self, limit: int) -> List[PostData]:
        """Fallback парсинг через HTML"""
        posts = []
        seen_ids = set()
        
        try:
            self.logger.info(f"🌐 Загружаю HTML с Reddit: {self.html_url}")
            
            html_content = await self.fetch_page(self.html_url)
            if not html_content:
                return posts
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Ищем контейнеры постов
            post_containers = soup.select(self.image_selectors['POST_CONTAINER'])
            self.logger.info(f"📊 Найдено {len(post_containers)} потенциальных контейнеров постов")
            
            for container in post_containers[:limit * 2]:
                if len(posts) >= limit:
                    break
                    
                try:
                    post_data = await self._extract_post_from_html(container)
                    if post_data and post_data.post_id not in seen_ids:
                        if not self._should_filter_post(post_data):
                            posts.append(post_data)
                            seen_ids.add(post_data.post_id)
                            self.logger.info(f"✅ Добавлен пост: {post_data.title[:50]}...")
                        else:
                            self.logger.debug(f"🚫 Отфильтрован пост: {post_data.title[:50]}...")
                            
                except Exception as e:
                    self.logger.error(f"❌ Ошибка при извлечении поста из HTML: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"💥 Ошибка при HTML парсинге: {e}")
        
        return posts
    
    async def _extract_post_from_html(self, container) -> Optional[PostData]:
        """Извлечение данных поста из HTML контейнера"""
        try:
            # Ищем ссылку на пост для получения ID
            post_link_elem = container.select_one(self.image_selectors['POST_LINK'])
            if not post_link_elem:
                return None
            
            post_url = post_link_elem.get('href', '')
            if post_url.startswith('/'):
                post_url = self.base_url + post_url
            
            # Извлекаем ID поста из URL
            post_id_match = re.search(r'/comments/([a-zA-Z0-9]+)/', post_url)
            if not post_id_match:
                return None
            
            post_id = post_id_match.group(1)
            
            # Заголовок поста
            title_elem = container.select_one(self.image_selectors['TITLE'])
            title = title_elem.get_text(strip=True) if title_elem else "Без заголовка"
            
            # Описание поста (из HTML сложнее извлечь, оставляем пустым)
            description = ""
            
            # Ищем медиа
            media_items = []
            
            # Изображения
            images = container.select(self.image_selectors['IMAGE'])
            for img in images:
                src = img.get('src') or img.get('data-src')
                if src and self.is_valid_image_url(src):
                    if not src.startswith('http'):
                        src = self.base_url + src if src.startswith('/') else src
                    media_items.append({'url': src, 'type': 'image'})
            
            # Видео
            videos = container.select(self.image_selectors['VIDEO'])
            for video in videos:
                src = video.get('src')
                if src and self.is_valid_video_url(src):
                    if not src.startswith('http'):
                        src = self.base_url + src if src.startswith('/') else src
                    media_items.append({'url': src, 'type': 'video'})
            
            if not media_items:
                return None
            
            # Берем первый медиа файл как основной
            primary_media = media_items[0]
            
            return PostData(
                post_id=f"reddit_{post_id}",
                media_url=primary_media['url'],
                title=title,
                description=description,
                post_url=post_url,
                tags=[f"r/{self.subreddit}"],
                media_type=primary_media['type'],
                all_media=media_items
            )
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения поста из HTML: {e}")
            return None
    
    def _should_filter_post(self, post_data: PostData) -> bool:
        """Проверяет нужно ли отфильтровать пост"""
        filter_config = CONTENT_FILTERS.get('REDDIT', {})
        if not filter_config.get('FILTER_ENABLED', False):
            return False
        
        title = post_data.title.lower()
        blocked_phrases = filter_config.get('BLOCKED_PHRASES', [])
        
        # Проверяем заблокированные фразы
        for phrase in blocked_phrases:
            if phrase.lower() in title:
                self.logger.info(f"🚫 Фильтруем пост с заголовком: '{post_data.title}'")
                return True
        
        return False
    
    async def get_post_details(self, post_url: str) -> Optional[PostData]:
        """Получает детальную информацию о посте"""
        self.logger.info(f"📄 Получаю детали поста: {post_url}")
        
        try:
            # Пробуем получить JSON версию поста
            if '.json' not in post_url:
                json_url = post_url.rstrip('/') + '.json'
            else:
                json_url = post_url
            
            html_content = await self.fetch_page(json_url)
            if html_content:
                try:
                    data = json.loads(html_content)
                    if isinstance(data, list) and len(data) > 0:
                        post_data_raw = data[0]['data']['children'][0]['data']
                        return await self._extract_post_from_json(post_data_raw)
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
            
            # Fallback на HTML
            html_content = await self.fetch_page(post_url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Ищем основной контейнер поста
            post_container = soup.select_one('[data-testid="post-container"], .Post, .thing')
            if post_container:
                return await self._extract_post_from_html(post_container)
            
        except Exception as e:
            self.logger.error(f"💥 Ошибка при получении деталей поста: {e}")
        
        return None 
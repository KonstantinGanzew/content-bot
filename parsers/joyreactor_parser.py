import re
import asyncio
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging

from .base_parser import BaseParser, PostData
from config.constants import PARSERS, CONTENT_FILTERS

logger = logging.getLogger(__name__)

class JoyReactorParser(BaseParser):
    """Парсер для сайта JoyReactor"""
    
    def __init__(self):
        self.config = PARSERS['JOYREACTOR']
        super().__init__(self.config['BASE_URL'])
        self.tag_url = self.config['TAG_URL']
        self.request_delay = self.config['REQUEST_DELAY']
        self.image_selectors = self.config['IMAGE_SELECTORS']
        self.logger = logging.getLogger(__name__)
    
    async def parse_posts(self, limit: int = 10) -> List[PostData]:
        """Парсинг постов с изображениями"""
        posts = []
        seen_ids = set()
        seen_images = set()
        
        try:
            html_content = await self.fetch_page(self.tag_url)
            if not html_content:
                self.logger.error("Не удалось получить HTML контент")
                return posts
                
            self.logger.info(f"HTML получен: {len(html_content)} символов")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Пробуем разные стратегии поиска постов
            post_containers = self._find_post_containers(soup)
            self.logger.info(f"Найдено потенциальных контейнеров постов: {len(post_containers)}")
            
            # Увеличиваем лимит контейнеров чтобы найти больше уникальных постов
            for container in post_containers[:limit * 3]:
                if len(posts) >= limit:  # Остановимся когда найдем достаточно уникальных постов
                    break
                    
                try:
                    post_data = await self._extract_post_data(container)
                    if post_data and post_data.get('media_url'):
                        # Проверяем фильтрацию нежелательного контента
                        if self._should_filter_post(post_data):
                            self.logger.debug(f"🚫 Пропускаем отфильтрованный пост: {post_data.get('title', 'Без названия')}")
                            continue
                        
                        post_id = post_data['id']
                        media_url = post_data['media_url']
                        
                        # Проверяем дубликаты по ID
                        if post_id in seen_ids:
                            self.logger.debug(f"🔄 Пропускаем дубликат по ID: {post_id}")
                            continue
                        
                        # Проверяем дубликаты по медиа
                        if media_url in seen_images:
                            self.logger.debug(f"🖼️ Пропускаем дубликат по медиа: {post_data.get('title', 'Без названия')}")
                            continue
                        
                        # Добавляем в множества для отслеживания
                        seen_ids.add(post_id)
                        seen_images.add(media_url)
                        
                        # Конвертируем в PostData объект
                        post_obj = PostData(
                            post_id=post_id,
                            media_url=post_data['media_url'],
                            title=post_data['title'],
                            post_url=post_data.get('link', ''),
                            tags=[],
                            media_type=post_data['media_type'],
                            all_media=post_data.get('all_media', [])
                        )
                        posts.append(post_obj)
                        self.logger.info(f"✅ Найден уникальный пост: {post_data.get('title', 'Без названия')}")
                        
                except Exception as e:
                    self.logger.error(f"Ошибка при извлечении данных поста: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге постов: {e}")
            
        self.logger.info(f"🎯 Итого обработано уникальных постов: {len(posts)}")
        return posts
    
    def _find_post_containers(self, soup: BeautifulSoup) -> List:
        """Поиск контейнеров постов с использованием различных стратегий"""
        containers = []
        
        # Стратегия 1: Поиск div с изображениями
        divs_with_images = soup.find_all('div', recursive=True)
        for div in divs_with_images:
            images = div.find_all('img')
            links = div.find_all('a', href=re.compile(r'/post/'))
            
            # Если есть изображения и ссылки на посты, это похоже на контейнер поста
            if images and links:
                containers.append(div)
        
        self.logger.info(f"Стратегия 1 (div с изображениями): {len(containers)} контейнеров")
        
        # Стратегия 2: Поиск по классам связанным с постами
        post_classes = ['.post', '.uhead', '.postContainer', '[class*="post"]', '.entry']
        for selector in post_classes:
            try:
                elements = soup.select(selector)
                if elements:
                    self.logger.info(f"Селектор {selector}: найдено {len(elements)} элементов")
                    containers.extend(elements)
            except Exception as e:
                self.logger.debug(f"Ошибка с селектором {selector}: {e}")
        
        # Убираем дубликаты сохраняя порядок
        unique_containers = []
        seen = set()
        filtered_comments = 0
        
        for container in containers:
            if id(container) not in seen:
                seen.add(id(container))
                
                # Исключаем контейнеры с комментариями
                if self._is_comment_container(container):
                    filtered_comments += 1
                    continue
                    
                unique_containers.append(container)
        
        if filtered_comments > 0:
            self.logger.info(f"🚫 Отфильтровано контейнеров-комментариев: {filtered_comments}")
        
        self.logger.info(f"Найдено потенциальных контейнеров постов: {len(unique_containers)}")
        return unique_containers[:100]  # Увеличиваем лимит для обработки всей страницы
    
    def _is_comment_container(self, container) -> bool:
        """Проверяет является ли контейнер комментарием"""
        # Проверяем наличие div с классом comment-content
        comment_divs = container.find_all('div', class_='comment-content')
        if comment_divs:
            return True
        
        # Проверяем является ли сам контейнер div с классом comment-content
        if container.name == 'div' and container.get('class'):
            classes = container.get('class')
            if isinstance(classes, list):
                if 'comment-content' in classes:
                    return True
            elif isinstance(classes, str):
                if 'comment-content' in classes:
                    return True
        
        return False
    
    async def _extract_post_data(self, container) -> Optional[Dict]:
        """Извлечение данных поста из контейнера"""
        try:
            # Ищем медиа контент (изображения и видео)
            valid_media = []
            
            # 1. Ищем изображения
            images = container.find_all('img')
            for img in images:
                src = img.get('src') or img.get('data-src')
                if src and self._is_valid_media(src, img, 'image'):
                    if not src.startswith('http'):
                        src = self.base_url + src if src.startswith('/') else self.base_url + '/' + src
                    # Проверяем дубликаты
                    if not any(media['url'] == src for media in valid_media):
                        valid_media.append({'url': src, 'type': 'image'})
            
            # 2. Ищем видео теги
            videos = container.find_all('video')
            for video in videos:
                # Проверяем source теги внутри video
                sources = video.find_all('source')
                for source in sources:
                    src = source.get('src')
                    if src and self.is_valid_video_url(src):
                        if not src.startswith('http'):
                            src = self.base_url + src if src.startswith('/') else self.base_url + '/' + src
                        # Проверяем дубликаты
                        if not any(media['url'] == src for media in valid_media):
                            valid_media.append({'url': src, 'type': 'video'})
                        break  # Берем первый подходящий источник
                
                # Если нет source тегов, проверяем src атрибут video
                if not sources:
                    src = video.get('src')
                    if src and self.is_valid_video_url(src):
                        if not src.startswith('http'):
                            src = self.base_url + src if src.startswith('/') else self.base_url + '/' + src
                        # Проверяем дубликаты
                        if not any(media['url'] == src for media in valid_media):
                            valid_media.append({'url': src, 'type': 'video'})
            
            # 3. Ищем ссылки на видео файлы
            links = container.find_all('a')
            for link in links:
                href = link.get('href')
                if href and self.is_valid_video_url(href):
                    if not href.startswith('http'):
                        href = self.base_url + href if href.startswith('/') else self.base_url + '/' + href
                    # Проверяем дубликаты
                    if not any(media['url'] == href for media in valid_media):
                        valid_media.append({'url': href, 'type': 'video'})
            
            # 4. Ищем видео в data-атрибутах изображений (JoyReactor специфика)
            for img in images:
                # Проверяем различные data-атрибуты которые могут содержать видео
                data_attrs = ['data-video', 'data-webm', 'data-mp4', 'data-original', 'data-fullsize']
                for attr in data_attrs:
                    data_src = img.get(attr)
                    if data_src and self.is_valid_video_url(data_src):
                        if not data_src.startswith('http'):
                            data_src = self.base_url + data_src if data_src.startswith('/') else self.base_url + '/' + data_src
                        # Проверяем дубликаты
                        if not any(media['url'] == data_src for media in valid_media):
                            valid_media.append({'url': data_src, 'type': 'video'})
                
                # Также проверяем src и data-src на наличие видео файлов
                for attr in ['src', 'data-src']:
                    src = img.get(attr)
                    if src and self.is_valid_video_url(src):
                        if not src.startswith('http'):
                            src = self.base_url + src if src.startswith('/') else self.base_url + '/' + src
                        # Проверяем дубликаты
                        if not any(media['url'] == src for media in valid_media):
                            valid_media.append({'url': src, 'type': 'video'})
            
            # 5. Ищем все элементы с атрибутами указывающими на видео
            all_elements = container.find_all(attrs={"data-webm": True})
            all_elements.extend(container.find_all(attrs={"data-mp4": True}))
            all_elements.extend(container.find_all(attrs={"data-video": True}))
            
            for element in all_elements:
                for attr in ['data-webm', 'data-mp4', 'data-video']:
                    video_src = element.get(attr)
                    if video_src and self.is_valid_video_url(video_src):
                        if not video_src.startswith('http'):
                            video_src = self.base_url + video_src if video_src.startswith('/') else self.base_url + '/' + video_src
                        # Проверяем дубликаты
                        if not any(media['url'] == video_src for media in valid_media):
                            valid_media.append({'url': video_src, 'type': 'video'})
            
            # 6. Поиск видео файлов в тексте HTML (агрессивный поиск)
            html_text = str(container)
            video_extensions = ['.webm', '.mp4', '.avi', '.mov', '.mkv', '.flv']
            
            for ext in video_extensions:
                # Ищем URL с расширениями видео в HTML тексте
                import re
                pattern = rf'https?://[^\s\'"<>]+{re.escape(ext)}(?:\?[^\s\'"<>]*)?'
                matches = re.findall(pattern, html_text, re.IGNORECASE)
                
                for match in matches:
                    if self.is_valid_video_url(match):
                        # Избегаем дубликатов
                        if not any(media['url'] == match for media in valid_media):
                            valid_media.append({'url': match, 'type': 'video'})
                            self.logger.debug(f"🎥 Найден видео URL в HTML: {match}")
            
            if not valid_media:
                return None
            
            # Логируем найденные медиа файлы для отладки
            video_count = sum(1 for media in valid_media if media['type'] == 'video')
            image_count = sum(1 for media in valid_media if media['type'] == 'image')
            self.logger.debug(f"Найдено медиа: {video_count} видео, {image_count} изображений")
            
            # Ищем ссылку на пост
            post_link = None
            post_links = container.find_all('a', href=re.compile(r'/post/'))
            if post_links:
                href = post_links[0].get('href')
                if href:
                    post_link = self.base_url + href if href.startswith('/') else href
            
            # Ищем заголовок или описание
            title = self._extract_title(container)
            
            # Берем первый найденный медиа файл (приоритет видео > изображения)
            primary_media = None
            for media in valid_media:
                if media['type'] == 'video':
                    primary_media = media
                    break
            if not primary_media:
                primary_media = valid_media[0]
            
            return {
                'id': self._generate_post_id(primary_media['url'], post_link, title),
                'title': title,
                'media_url': primary_media['url'],
                'media_type': primary_media['type'],
                'all_media': valid_media,  # Все найденные медиа
                'link': post_link,
                'source': 'JoyReactor'
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения данных поста: {e}")
            return None
    
    def _is_valid_media(self, src: str, tag, media_type: str) -> bool:
        """Проверка валидности медиа (изображения или видео)"""
        if not src:
            return False
            
        # Исключаем системные файлы
        exclude_patterns = [
            'avatar', 'icon', 'logo', 'button', 'arrow', 'smile', 'emoji',
            '/static/', '/css/', '/js/', 'loading'
        ]
        
        src_lower = src.lower()
        for pattern in exclude_patterns:
            if pattern in src_lower:
                return False
        
        # Проверяем тип медиа
        if media_type == 'image':
            if not self.is_valid_image_url(src):
                return False
            
            # Проверяем размеры если доступны (только для изображений)
            width = tag.get('width')
            height = tag.get('height')
            
            if width and height:
                try:
                    w, h = int(width), int(height)
                    if w < 100 or h < 100:  # Исключаем маленькие изображения
                        return False
                except (ValueError, TypeError):
                    pass
        elif media_type == 'video':
            if not self.is_valid_video_url(src):
                return False
        
        return True
    
    def _extract_title(self, container) -> str:
        """Извлечение заголовка поста"""
        # Ищем в различных возможных местах
        title_selectors = ['h1', 'h2', 'h3', '.title', '.post-title', 'a[href*="/post/"]']
        
        for selector in title_selectors:
            elements = container.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 5:  # Минимальная длина заголовка
                    return text[:100]  # Ограничиваем длину
        
        return "Пост без заголовка"
    
    def _should_filter_post(self, post_data: Dict) -> bool:
        """Проверяет нужно ли отфильтровать пост"""
        # Проверяем включена ли фильтрация
        filter_config = CONTENT_FILTERS.get('JOYREACTOR', {})
        if not filter_config.get('FILTER_ENABLED', False):
            return False
        
        title = post_data.get('title', '').lower()
        blocked_phrases = filter_config.get('BLOCKED_PHRASES', [])
        
        # Проверяем содержится ли заблокированная фраза в заголовке
        for phrase in blocked_phrases:
            if phrase.lower() in title:
                self.logger.info(f"🚫 Фильтруем пост с заголовком: '{post_data.get('title')}'")
                return True
        
        return False
    
    def _generate_post_id(self, media_url: str, post_link: Optional[str], title: str = "") -> str:
        """Генерация уникального ID поста с улучшенной дедупликацией"""
        import hashlib
        
        # Первый приоритет: ID из ссылки на пост
        if post_link:
            match = re.search(r'/post/(\d+)', post_link)
            if match:
                return f"joyreactor_{match.group(1)}"
        
        # Второй приоритет: ID из имени файла медиа
        if media_url:
            filename = media_url.split('/')[-1].split('?')[0]  # Убираем параметры
            
            # Если есть числовой ID в имени файла (6+ цифр), используем его
            file_id_match = re.search(r'(\d{6,})', filename)
            if file_id_match:
                return f"joyreactor_{file_id_match.group(1)}"
        
        # Третий приоритет: стабильный хеш от URL медиа + заголовка
        if media_url:
            # Создаем стабильный ключ БЕЗ времени
            content_key = f"{media_url}_{title}"
            content_hash = hashlib.md5(content_key.encode()).hexdigest()[:12]
            return f"joyreactor_{content_hash}"
        
        # Последний резерв: хеш от заголовка
        if title:
            title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
            return f"joyreactor_{title_hash}"
        
        # Если совсем ничего нет - используем константу
        return "joyreactor_unknown"
    
    async def get_post_details(self, post_url: str) -> Optional[PostData]:
        """Получает детальную информацию о посте."""
        logger.info(f"Получаю детали поста: {post_url}")
        
        html = await self.fetch_page(post_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            post_id = self._extract_post_id(post_url)
            if not post_id:
                return None
            
            # Ищем главное изображение поста
            image_url = None
            
            # Попробуем найти изображение в разных местах
            selectors_to_try = [
                '.post_content img',
                '.image img',
                '.post img',
                'img'
            ]
            
            for selector in selectors_to_try:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src and isinstance(src, str) and self.is_valid_image_url(src):
                        image_url = self.resolve_url(src)
                        break
                if image_url:
                    break
            
            if not image_url:
                return None
            
            # Получаем заголовок
            title = self._extract_title_from_detail_page(soup)
            
            # Получаем описание
            description = self._extract_description(soup)
            
            # Получаем теги
            tags = self._extract_tags_from_detail_page(soup)
            
            return PostData(
                post_id=post_id,
                media_url=image_url,
                title=title,
                description=description,
                post_url=post_url,
                tags=tags,
                media_type="image",
                all_media=[{'url': image_url, 'type': 'image'}]
            )
            
        except Exception as e:
            logger.error(f"Ошибка при получении деталей поста: {e}")
            return None
    
    def _extract_post_id(self, post_url: str) -> Optional[str]:
        """Извлекает ID поста из URL."""
        match = re.search(r'/post/(\d+)', post_url)
        return match.group(1) if match else None
    
    def _extract_title_from_detail_page(self, soup) -> str:
        """Извлекает заголовок со страницы деталей поста."""
        # Пробуем разные селекторы
        selectors = [
            'h1.post_title',
            '.post_title',
            'h1',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # Убираем "JoyReactor" и другие лишние части
                text = re.sub(r'\s*::\s*JoyReactor.*$', '', text)
                return text
        
        return ""
    
    def _extract_description(self, soup) -> str:
        """Извлекает описание поста."""
        # Пробуем найти описание
        desc_selectors = [
            '.post_content .txt',
            '.post_content',
            '.post_text',
            '.description'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                # Убираем изображения и лишние теги
                for img in element.find_all('img'):
                    img.decompose()
                
                text = element.get_text(strip=True)
                # Ограничиваем длину
                if len(text) > 300:
                    text = text[:300] + "..."
                return text
        
        return ""
    
    def _extract_tags_from_detail_page(self, soup) -> List[str]:
        """Извлекает теги со страницы деталей."""
        tags = []
        
        # Ищем теги на странице деталей
        tag_elements = soup.select('.taglist a, .post_tag, .tag a')
        
        for tag_elem in tag_elements:
            tag_text = tag_elem.get_text(strip=True)
            if tag_text and tag_text not in tags:
                tags.append(tag_text)
        
        return tags 
import asyncio
import aiohttp
import logging
from typing import Optional, Dict, List
import aiofiles
from pathlib import Path
import tempfile
import os

from aiogram import Bot, types
from aiogram.exceptions import TelegramAPIError

from config.settings import settings
from config.constants import TELEGRAM
from parsers.base_parser import PostData

logger = logging.getLogger(__name__)

class TelegramSender:
    """Класс для отправки сообщений в Telegram."""
    
    def __init__(self):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
        if not settings.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CHAT_ID не установлен")
            
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.max_image_size = TELEGRAM['MAX_IMAGE_SIZE']
        self.supported_formats = TELEGRAM['SUPPORTED_FORMATS']
        
        # Создаем временную папку для изображений
        self.temp_dir = Path(tempfile.gettempdir()) / "parser_bot_images"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def send_post(self, post_data: PostData) -> bool:
        """Отправляет пост в Telegram группу."""
        local_file_path = None
        try:
            
            # 1. Проверяем информацию об изображении
            image_info = await self._get_image_info(post_data.image_url)
            if not image_info:
                logger.error(f"❌ Не удалось получить информацию об изображении: {post_data.image_url}")
                return False
            
            # 2. Проверяем размер
            if image_info['size'] > self.max_image_size:
                logger.warning(f"⚠️ Изображение слишком большое ({image_info['size']/1024/1024:.1f} MB): {post_data.image_url}")
                return False
            
            # 3. Проверяем формат
            content_type = image_info.get('content_type', '').lower()
            supported_mime_types = [
                'image/jpeg', 'image/jpg', 'image/png', 
                'image/gif', 'image/webp'
            ]
            if not any(mime_type in content_type for mime_type in supported_mime_types):
                logger.warning(f"⚠️ Неподдерживаемый формат изображения ({content_type}): {post_data.image_url}")
                return False
            
            # 4. Скачиваем изображение
            local_file_path = await self._download_image(post_data.image_url, post_data.post_id)
            if not local_file_path:
                logger.error(f"❌ Не удалось скачать изображение: {post_data.image_url}")
                return False
            
            # 5. Формируем подпись
            caption = self._format_caption(post_data)
            
            # 6. Отправляем изображение
            success = await self._send_local_image(local_file_path, caption)
            
            return success
            
        except Exception as e:
            logger.error(f"💥 Ошибка при отправке поста {post_data.post_id}: {e}")
            return False
        finally:
            # 7. Всегда удаляем временный файл
            if local_file_path and os.path.exists(local_file_path):
                try:
                    os.remove(local_file_path)
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить временный файл {local_file_path}: {e}")
    
    async def _download_image(self, image_url: str, post_id: str) -> Optional[str]:
        """Скачивает изображение и сохраняет локально."""
        try:
            # Определяем расширение файла из URL или content-type
            file_extension = self._get_file_extension(image_url)
            
            # Создаем уникальное имя файла
            filename = f"{post_id}_{hash(image_url) % 10000}{file_extension}"
            file_path = self.temp_dir / filename
            
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=30)  # 30 секунд таймаут
                async with session.get(image_url, timeout=timeout) as response:
                    if response.status != 200:
                        logger.error(f"❌ Ошибка скачивания: HTTP {response.status}")
                        return None
                    
                    # Проверяем размер еще раз
                    content_length = int(response.headers.get('content-length', 0))
                    if content_length > self.max_image_size:
                        logger.error(f"❌ Изображение слишком большое: {content_length} bytes")
                        return None
                    
                    # Скачиваем файл
                    async with aiofiles.open(file_path, 'wb') as f:
                        downloaded_size = 0
                        async for chunk in response.content.iter_chunked(8192):  # 8KB chunks
                            await f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Проверяем размер во время скачивания
                            if downloaded_size > self.max_image_size:
                                logger.error(f"❌ Превышен лимит размера при скачивании")
                                await f.close()
                                if file_path.exists():
                                    file_path.unlink()
                                return None
                    
                    # Проверяем что файл создался
                    if not file_path.exists() or file_path.stat().st_size == 0:
                        logger.error(f"❌ Файл не создался или пустой")
                        return None
                    
                    return str(file_path)
                    
        except Exception as e:
            logger.error(f"💥 Ошибка при скачивании изображения {image_url}: {e}")
            return None
    
    def _get_file_extension(self, url: str) -> str:
        """Определяет расширение файла из URL."""
        url_lower = url.lower()
        
        if '.jpg' in url_lower or '.jpeg' in url_lower:
            return '.jpg'
        elif '.png' in url_lower:
            return '.png'
        elif '.gif' in url_lower:
            return '.gif'
        elif '.webp' in url_lower:
            return '.webp'
        else:
            return '.jpg'  # по умолчанию
    
    async def _send_local_image(self, file_path: str, caption: str) -> bool:
        """Отправляет локальное изображение в чат."""
        try:
            # Создаем InputFile из локального файла
            input_file = types.FSInputFile(file_path)
            
            # Отправляем фото
            await self.bot.send_photo(
                chat_id=self.chat_id,
                photo=input_file,
                caption=caption,
                parse_mode=TELEGRAM['PARSE_MODE'],
                disable_notification=TELEGRAM['DISABLE_NOTIFICATION']
            )
            
            return True
            
        except TelegramAPIError as e:
            logger.error(f"❌ Telegram API ошибка при отправке изображения: {e}")
            return False
        except Exception as e:
            logger.error(f"💥 Неожиданная ошибка при отправке изображения: {e}")
            return False
    
    async def _get_image_info(self, image_url: str) -> Optional[Dict]:
        """Получает информацию об изображении."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(image_url) as response:
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
    
    def _format_caption(self, post_data: PostData) -> str:
        """Форматирует подпись для поста."""
        caption_parts = []
        
        # Добавляем заголовок
        if post_data.title:
            caption_parts.append(f"<b>{self._escape_html(post_data.title)}</b>")
        
        # Добавляем описание
        if post_data.description:
            caption_parts.append(self._escape_html(post_data.description))
        
        # Убираем теги (закомментировано по запросу)
        # if post_data.tags:
        #     tags_text = " ".join([f"#{self._clean_tag(tag)}" for tag in post_data.tags[:5]])  # Максимум 5 тегов
        #     caption_parts.append(tags_text)
        
        # Добавляем ссылку на источник (без текста "Источник")
        if post_data.post_url:
            caption_parts.append(f"<a href='{post_data.post_url}'>🔗</a>")
        
        # Объединяем части
        caption = "\n\n".join(caption_parts)
        
        # Ограничиваем длину подписи (Telegram лимит 1024 символа)
        if len(caption) > 1000:
            caption = caption[:1000] + "..."
        
        return caption
    
    def _escape_html(self, text: str) -> str:
        """Экранирует HTML символы."""
        if not text:
            return ""
        
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;'))
    
    def _clean_tag(self, tag: str) -> str:
        """Очищает тег для использования в Telegram."""
        # Убираем пробелы и специальные символы
        cleaned = ''.join(c for c in tag if c.isalnum() or c in ['_'])
        return cleaned[:20]  # Ограничиваем длину тега
    
    async def test_connection(self) -> bool:
        """Тестирует соединение с Telegram API."""
        try:
            me = await self.bot.get_me()
            logger.info(f"Бот подключен: @{me.username}")
            
            # Проверяем возможность отправки в чат (без сообщения)
            # await self.bot.send_message(
            #     chat_id=self.chat_id,
            #     text="🤖 Бот-парсер запущен и готов к работе!",
            #     disable_notification=True
            # )
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при тестировании соединения с Telegram: {e}")
            return False
    
    async def close(self):
        """Закрывает соединение с ботом."""
        await self.bot.session.close()
    
    async def send_multiple_posts(self, posts: List[PostData], delay: float = 2.0) -> int:
        """Отправляет несколько постов с задержкой."""
        sent_count = 0
        
        logger.info(f"🚀 Начинаю отправку {len(posts)} постов с задержкой {delay} сек")
        
        for i, post in enumerate(posts, 1):
            try:
                logger.info(f"📤 Отправляю пост {i}/{len(posts)}: {post.post_id}")
                
                if await self.send_post(post):
                    sent_count += 1
                    logger.info(f"✅ Успешно ({sent_count}/{len(posts)})")
                else:
                    logger.error(f"❌ Не удалось отправить пост {post.post_id}")
                
                # Задержка между отправками (кроме последнего поста)
                if i < len(posts):
                    logger.info(f"⏱️ Задержка {delay} секунд...")
                    await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"💥 Ошибка при отправке поста {post.post_id}: {e}")
                continue
        
        logger.info(f"🏁 Завершено: отправлено {sent_count} из {len(posts)} постов")
        return sent_count 
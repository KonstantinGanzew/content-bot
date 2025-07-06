import asyncio
import logging
import os
import aiohttp
import aiofiles
from typing import Optional, List, Dict
from urllib.parse import urlparse, quote, urlunparse

from aiogram import Bot, types
from aiogram.exceptions import TelegramAPIError

from config.settings import settings
from config.constants import TELEGRAM
from parsers.base_parser import PostData

logger = logging.getLogger(__name__)

class TelegramSender:
    """Класс для отправки сообщений в Telegram."""
    
    def __init__(self):
        """Инициализация Telegram бота."""
        if not settings.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
        if not settings.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CHAT_ID не установлен")
            
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.max_image_size = TELEGRAM['MAX_IMAGE_SIZE']
        self.max_video_size = TELEGRAM['MAX_VIDEO_SIZE']
        self.supported_image_formats = TELEGRAM['SUPPORTED_IMAGE_FORMATS']
        self.supported_video_formats = TELEGRAM['SUPPORTED_VIDEO_FORMATS']
        
        # Создаем временную директорию
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
    
    async def send_post(self, post_data: PostData) -> bool:
        """Отправляет пост в Telegram чат."""
        logger.info(f"📤 Отправляю пост: {post_data.post_id}")
        
        local_file_paths = []
        
        try:
            # Получаем все медиа файлы
            if post_data.has_multiple_media():
                media_list = post_data.all_media[:10]  # Ограничиваем до 10 медиа
                logger.info(f"📸 Найдено {len(media_list)} медиа файлов в посте")
            else:
                # Одно медиа - создаем список для единообразной обработки
                media_list = [{'url': post_data.media_url, 'type': post_data.media_type}]
                logger.info(f"📸 Найдено 1 медиа файл в посте")
            
            # Скачиваем все медиа файлы
            valid_media_files = []
            
            for i, media in enumerate(media_list):
                media_url = media['url']
                media_type = media['type']
                
                # Получаем информацию о медиа файле
                media_info = await self._get_media_info(media_url)
                if not media_info:
                    logger.warning(f"⚠️ Пропускаем медиа {i+1}/{len(media_list)} - файл недоступен")
                    continue
                
                # Проверяем размер в зависимости от типа медиа
                max_size = self.max_video_size if media_type == "video" else self.max_image_size
                if media_info['size'] > max_size:
                    logger.warning(f"⚠️ Пропускаем медиа {i+1}/{len(media_list)} - слишком большой размер")
                    continue
                
                # Проверяем формат
                if not self._is_supported_format(media_info.get('content_type', ''), media_type):
                    logger.warning(f"⚠️ Пропускаем медиа {i+1}/{len(media_list)} - неподдерживаемый формат")
                    continue
                
                # Скачиваем медиа файл
                local_file_path = await self._download_media(media_url, f"{post_data.post_id}_{i}", media_type)
                if not local_file_path:
                    logger.warning(f"⚠️ Пропускаем медиа {i+1}/{len(media_list)} - не удалось скачать")
                    continue
                
                local_file_paths.append(local_file_path)
                valid_media_files.append({
                    'file_path': local_file_path,
                    'media_type': media_type,
                    'is_first': i == 0
                })
            
            # Проверяем что есть хотя бы один файл для отправки
            if not valid_media_files:
                logger.error(f"❌ Нет доступных медиа файлов для отправки")
                return False
            
            # Отправляем все медиа одной группой
            if len(valid_media_files) == 1:
                # Одно медиа - отправляем обычным способом
                media_file = valid_media_files[0]
                caption = self._format_caption(post_data)
                
                if media_file['media_type'] == "video":
                    success = await self._send_local_video(media_file['file_path'], caption)
                else:
                    success = await self._send_local_image(media_file['file_path'], caption)
                
                if success:
                    logger.info(f"✅ Успешно отправлено 1 медиа файл")
                    return True
                else:
                    logger.error(f"❌ Не удалось отправить медиа файл")
                    return False
            else:
                # Множественные медиа - отправляем группой
                success = await self._send_media_group(valid_media_files, post_data)
                
                if success:
                    logger.info(f"✅ Успешно отправлена группа из {len(valid_media_files)} медиа файлов")
                    return True
                else:
                    logger.error(f"❌ Не удалось отправить группу медиа файлов")
                    return False
            
        except Exception as e:
            logger.error(f"💥 Ошибка при отправке поста {post_data.post_id}: {e}")
            return False
        finally:
            # Всегда удаляем временные файлы
            for file_path in local_file_paths:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось удалить временный файл {file_path}: {e}")
    
    async def _download_media(self, media_url: str, post_id: str, media_type: str) -> Optional[str]:
        """Скачивает медиа файл и сохраняет локально."""
        try:
            # Кодируем URL для правильной обработки кириллических символов
            parsed = urlparse(media_url)
            encoded_path = quote(parsed.path.encode('utf-8'), safe='/')
            encoded_url = urlunparse((
                parsed.scheme, parsed.netloc, encoded_path,
                parsed.params, parsed.query, parsed.fragment
            ))
            
            logger.debug(f"🔗 Скачивание с URL: {encoded_url}")
            
            # Определяем расширение файла из URL или content-type
            file_extension = self._get_media_file_extension(media_url, media_type)
            
            # Создаем уникальное имя файла
            filename = f"{post_id}_{hash(media_url) % 10000}{file_extension}"
            file_path = os.path.join(self.temp_dir, filename)
            
            max_size = self.max_video_size if media_type == "video" else self.max_image_size
            
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=60)  # 60 секунд для видео
                
                # Пробуем основной закодированный URL
                async with session.get(encoded_url, timeout=timeout) as response:
                    if response.status == 200:
                        # Проверяем размер еще раз
                        content_length = int(response.headers.get('content-length', 0))
                        if content_length > max_size:
                            logger.error(f"❌ Медиа файл слишком большой: {content_length} bytes")
                            return None
                        
                        # Скачиваем файл
                        return await self._download_from_response(response, file_path, max_size)
                    
                    elif response.status == 404:
                        logger.warning(f"⚠️ Файл не найден (404): {encoded_url}")
                        
                        # Пробуем оригинальный URL без кодирования
                        logger.debug(f"🔄 Пробуем оригинальный URL для скачивания...")
                        async with session.get(media_url, timeout=timeout) as fallback_response:
                            if fallback_response.status == 200:
                                logger.info(f"✅ Fallback скачивание работает: {media_url}")
                                
                                content_length = int(fallback_response.headers.get('content-length', 0))
                                if content_length > max_size:
                                    logger.error(f"❌ Медиа файл слишком большой: {content_length} bytes")
                                    return None
                                
                                return await self._download_from_response(fallback_response, file_path, max_size)
                            else:
                                logger.warning(f"⚠️ Fallback URL тоже не работает: HTTP {fallback_response.status}")
                                logger.info(f"📄 Файл может быть удален или перемещен с сервера")
                                logger.info(f"🔗 Проблемный URL: {media_url}")
                                return None
                    else:
                        logger.error(f"❌ Ошибка скачивания: HTTP {response.status}")
                        return None
                    
        except Exception as e:
            logger.error(f"💥 Ошибка при скачивании медиа {media_url}: {e}")
            return None
    
    async def _download_from_response(self, response, file_path, max_size):
        """Скачивает файл из HTTP response."""
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                downloaded_size = 0
                async for chunk in response.content.iter_chunked(8192):  # 8KB chunks
                    await f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # Проверяем размер во время скачивания
                    if downloaded_size > max_size:
                        logger.error(f"❌ Превышен лимит размера при скачивании")
                        await f.close()
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return None
            
            # Проверяем что файл создался
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                logger.error(f"❌ Файл не создался или пустой")
                return None
            
            return file_path
            
        except Exception as e:
            logger.error(f"💥 Ошибка при сохранении файла: {e}")
            return None
    
    def _get_media_file_extension(self, url: str, media_type: str) -> str:
        """Определяет расширение медиа файла из URL."""
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
    
    def _format_caption(self, post_data: PostData) -> str:
        """Форматирует подпись для поста."""
        # Отправляем медиа без подписи по запросу пользователя
        return ""
    
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
    
    def _is_supported_format(self, content_type: str, media_type: str) -> bool:
        """Проверяет поддерживается ли формат медиа."""
        content_type_lower = content_type.lower()
        
        if media_type == "video":
            supported_video_mime_types = [
                'video/mp4', 'video/webm', 'video/avi', 'video/mov', 
                'video/quicktime', 'video/x-msvideo', 'video/x-flv'
            ]
            return any(mime_type in content_type_lower for mime_type in supported_video_mime_types)
        else:  # image
            supported_image_mime_types = [
                'image/jpeg', 'image/jpg', 'image/png', 
                'image/gif', 'image/webp'
            ]
            return any(mime_type in content_type_lower for mime_type in supported_image_mime_types)
    
    async def _get_media_info(self, media_url: str) -> Optional[Dict]:
        """Получает информацию о медиа файле."""
        try:
            # Кодируем URL для правильной обработки кириллических символов
            parsed = urlparse(media_url)
            # Кодируем путь, сохраняя протокол и домен
            encoded_path = quote(parsed.path.encode('utf-8'), safe='/')
            encoded_url = urlunparse((
                parsed.scheme, parsed.netloc, encoded_path,
                parsed.params, parsed.query, parsed.fragment
            ))
            
            logger.debug(f"🔗 Оригинальный URL: {media_url}")
            logger.debug(f"🔗 Закодированный URL: {encoded_url}")
            
            async with aiohttp.ClientSession() as session:
                # Пробуем основной закодированный URL
                async with session.head(encoded_url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        content_length = int(response.headers.get('content-length', 0))
                        
                        logger.debug(f"📊 Медиа информация: тип={content_type}, размер={content_length}")
                        
                        return {
                            'url': media_url,  # Возвращаем оригинальный URL
                            'content_type': content_type,
                            'size': content_length
                        }
                    elif response.status == 404:
                        logger.warning(f"⚠️ Файл не найден (404): {encoded_url}")
                        
                        # Пробуем оригинальный URL без кодирования
                        logger.debug(f"🔄 Пробуем оригинальный URL без кодирования...")
                        async with session.head(media_url) as fallback_response:
                            if fallback_response.status == 200:
                                content_type = fallback_response.headers.get('content_type', '')
                                content_length = int(fallback_response.headers.get('content-length', 0))
                                
                                logger.info(f"✅ Fallback URL работает: {media_url}")
                                
                                return {
                                    'url': media_url,
                                    'content_type': content_type,
                                    'size': content_length
                                }
                            else:
                                logger.warning(f"⚠️ Fallback URL тоже не работает: HTTP {fallback_response.status}")
                                logger.info(f"📄 Файл может быть удален или перемещен с сервера")
                                logger.info(f"🔗 Проблемный URL: {media_url}")
                                return None
                    else:
                        logger.warning(f"⚠️ HTTP {response.status} для {encoded_url}")
                        
        except Exception as e:
            logger.error(f"❌ Не удалось получить информацию о медиа: {media_url}")
            logger.debug(f"Подробности ошибки: {e}")
        
        return None
    
    async def _send_local_video(self, file_path: str, caption: str) -> bool:
        """Отправляет локальное видео в чат."""
        try:
            # Создаем InputFile из локального файла
            input_file = types.FSInputFile(file_path)
            
            # Отправляем видео
            await self.bot.send_video(
                chat_id=self.chat_id,
                video=input_file,
                caption=caption,
                parse_mode=TELEGRAM['PARSE_MODE'],
                disable_notification=TELEGRAM['DISABLE_NOTIFICATION']
            )
            
            return True
            
        except TelegramAPIError as e:
            logger.error(f"❌ Telegram API ошибка при отправке видео: {e}")
            return False
        except Exception as e:
            logger.error(f"💥 Неожиданная ошибка при отправке видео: {e}")
            return False

    async def _send_media_group(self, media_files: List[Dict], post_data: PostData) -> bool:
        """Отправляет группу медиа файлов одним сообщением."""
        try:
            from aiogram.types import InputMediaPhoto, InputMediaVideo
            
            media_group = []
            caption = self._format_caption(post_data)
            
            for i, media_file in enumerate(media_files):
                file_path = media_file['file_path']
                media_type = media_file['media_type']
                
                # Создаем InputFile
                input_file = types.FSInputFile(file_path)
                
                # Добавляем подпись только к первому медиа
                file_caption = caption if i == 0 else ""
                
                # Создаем соответствующий InputMedia
                if media_type == "video":
                    media_item = InputMediaVideo(
                        media=input_file,
                        caption=file_caption,
                        parse_mode=TELEGRAM['PARSE_MODE']
                    )
                else:
                    media_item = InputMediaPhoto(
                        media=input_file,
                        caption=file_caption,
                        parse_mode=TELEGRAM['PARSE_MODE']
                    )
                
                media_group.append(media_item)
            
            # Отправляем группу медиа
            await self.bot.send_media_group(
                chat_id=self.chat_id,
                media=media_group,
                disable_notification=TELEGRAM['DISABLE_NOTIFICATION']
            )
            
            logger.info(f"📤 Отправлена группа из {len(media_group)} медиа файлов")
            return True
            
        except Exception as e:
            logger.error(f"💥 Ошибка при отправке группы медиа: {e}")
            return False 
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from parsers.joyreactor_parser import JoyReactorParser
from parsers.reddit_parser import RedditParser
from parsers.base_parser import PostData
from telegram.bot import TelegramSender
from utils.database import database
from config.settings import settings
from config.constants import GENERAL

logger = logging.getLogger(__name__)

class ParserScheduler:
    """Планировщик для парсинга и отправки постов."""
    
    def __init__(self):
        self.telegram_sender = TelegramSender()
        self.parsers = {
            'joyreactor': JoyReactorParser(),
            'reddit': RedditParser()
        }
        self.running = False
        self.stats = {
            'total_parsed': 0,
            'total_sent': 0,
            'last_run': None,
            'errors': 0
        }
    
    async def start(self):
        """Запускает планировщик."""
        logger.info("Запуск планировщика парсера")
        
        # Загружаем базу данных
        await database.load()
        
        # Тестируем соединения
        if not await self._test_connections():
            logger.error("Не удалось установить соединения")
            return False
        
        self.running = True
        
        # Запускаем основной цикл
        await self._main_loop()
        
        return True
    
    async def stop(self):
        """Останавливает планировщик."""
        logger.info("Остановка планировщика")
        self.running = False
        await self.telegram_sender.close()
    
    async def _main_loop(self):
        """Главный цикл планировщика."""
        logger.info(f"Запущен главный цикл с интервалом {settings.PARSER_INTERVAL} секунд")
        
        while self.running:
            try:
                await self.run_parsing_cycle()
                
                # Ждем до следующего цикла
                if self.running:
                    await asyncio.sleep(settings.PARSER_INTERVAL)
                    
            except asyncio.CancelledError:
                logger.info("Главный цикл был отменен")
                break
            except Exception as e:
                logger.error(f"Ошибка в главном цикле: {e}")
                self.stats['errors'] += 1
                
                # Ждем меньше при ошибке
                if self.running:
                    await asyncio.sleep(60)
    
    async def run_parsing_cycle(self) -> Dict[str, Any]:
        """Выполняет один цикл парсинга."""
        cycle_start = datetime.now()
        cycle_stats = {
            'start_time': cycle_start,
            'parsed_posts': 0,
            'new_posts': 0,
            'sent_posts': 0,
            'errors': 0
        }
        
        logger.info("Начинаем цикл парсинга")
        
        try:
            # Парсим все источники
            all_posts = []
            
            for parser_name, parser in self.parsers.items():
                try:
                    logger.info(f"Парсинг {parser_name}")
                    
                    async with parser:
                        posts = await parser.parse_posts(GENERAL['MAX_POSTS_PER_RUN'])
                        all_posts.extend(posts)
                        cycle_stats['parsed_posts'] += len(posts)
                        
                        logger.info(f"Получено {len(posts)} постов от {parser_name}")
                        
                except Exception as e:
                    logger.error(f"Ошибка при парсинге {parser_name}: {e}")
                    cycle_stats['errors'] += 1
                    continue
            
            # Фильтруем новые посты
            new_posts = await database.filter_new_posts(all_posts)
            cycle_stats['new_posts'] = len(new_posts)
            
            if not new_posts:
                logger.info("Новых постов не найдено")
            else:
                # Отправляем новые посты
                sent_count = await self._send_posts(new_posts)
                cycle_stats['sent_posts'] = sent_count
                
                # Обновляем статистику
                self.stats['total_parsed'] += cycle_stats['parsed_posts']
                self.stats['total_sent'] += sent_count
            
            self.stats['last_run'] = cycle_start
            
            cycle_duration = datetime.now() - cycle_start
            logger.info(f"Цикл завершен за {cycle_duration.total_seconds():.1f}с. "
                       f"Парсено: {cycle_stats['parsed_posts']}, "
                       f"новых: {cycle_stats['new_posts']}, "
                       f"отправлено: {cycle_stats['sent_posts']}")
            
            return cycle_stats
            
        except Exception as e:
            logger.error(f"Ошибка в цикле парсинга: {e}")
            cycle_stats['errors'] += 1
            self.stats['errors'] += 1
            return cycle_stats
    
    async def _send_posts(self, posts: List[PostData]) -> int:
        """Отправляет посты в Telegram с дополнительной защитой от дубликатов."""
        logger.info(f"🚀 Отправляю {len(posts)} постов через Telegram")
        
        sent_count = 0
        sent_in_session = set()  # Дополнительная защита от дубликатов в одной сессии
        
        for i, post in enumerate(posts):
            try:
                # Дополнительная проверка на дубликаты в рамках сессии
                if post.post_id in sent_in_session:
                    logger.warning(f"🔄 Пропускаем дубликат в сессии: {post.post_id}")
                    continue
                
                # Проверяем не был ли пост добавлен в БД после фильтрации
                if await database.is_post_sent(post.post_id):
                    logger.warning(f"🔄 Пост {post.post_id} уже отправлен (проверка перед отправкой)")
                    continue
                
                logger.info(f"📤 Отправка поста {i+1}/{len(posts)}: {post.post_id}")
                logger.info(f"   📝 Заголовок: {post.title}")
                
                # Отправляем пост (новая логика: скачивание -> отправка -> удаление)
                success = await self.telegram_sender.send_post(post)
                
                if success:
                    # Добавляем в базу отправленных
                    await database.add_post(post.post_id)
                    sent_in_session.add(post.post_id)
                    sent_count += 1
                    logger.info(f"✅ Пост {post.post_id} успешно отправлен и добавлен в БД ({sent_count}/{len(posts)})")
                else:
                    logger.error(f"❌ Не удалось отправить пост {post.post_id}")
                
                # Задержка между отправками для избежания лимитов Telegram
                if i < len(posts) - 1:  # Не делаем задержку после последнего поста
                    logger.info(f"⏱️ Задержка 2 секунды перед следующим постом...")
                    await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"💥 Ошибка при отправке поста {post.post_id}: {e}")
                continue
        
        logger.info(f"🏁 Завершена отправка: {sent_count} из {len(posts)} постов успешно отправлено")
        return sent_count
    
    async def _test_connections(self) -> bool:
        """Тестирует соединения с внешними сервисами."""
        logger.info("Тестирование соединений")
        
        # Тестируем Telegram
        try:
            if not await self.telegram_sender.test_connection():
                logger.error("Не удалось подключиться к Telegram")
                return False
            logger.info("✓ Telegram соединение работает")
        except Exception as e:
            logger.error(f"Ошибка при тестировании Telegram: {e}")
            return False
        
        # Тестируем парсеры
        for parser_name, parser in self.parsers.items():
            try:
                async with parser:
                    test_posts = await parser.parse_posts(1)
                    if test_posts:
                        logger.info(f"✓ Парсер {parser_name} работает")
                    else:
                        logger.warning(f"⚠ Парсер {parser_name} не вернул данные")
            except Exception as e:
                logger.error(f"Ошибка при тестировании парсера {parser_name}: {e}")
                return False
        
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику работы."""
        db_stats = await database.get_stats()
        
        return {
            'scheduler': self.stats,
            'database': db_stats,
            'running': self.running,
            'parsers': list(self.parsers.keys())
        }
    
    async def manual_run(self) -> Dict[str, Any]:
        """Запускает парсинг вручную."""
        logger.info("Запуск ручного парсинга")
        return await self.run_parsing_cycle() 
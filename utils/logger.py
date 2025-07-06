import logging
import logging.handlers
from pathlib import Path
import sys
from datetime import datetime

from config.settings import settings
from config.constants import GENERAL

def setup_logging():
    """Настраивает систему логирования."""
    
    # Создаем директорию для логов
    log_dir = Path(GENERAL['LOGS_FOLDER'])
    log_dir.mkdir(exist_ok=True)
    
    # Определяем уровень логирования
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Удаляем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Создаем обработчик для файла (с ротацией)
    log_file = log_dir / f"parser_bot_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Создаем отдельный обработчик для ошибок
    error_log_file = log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Настраиваем логгеры для внешних библиотек
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logging.info("Система логирования настроена")
    logging.info(f"Уровень логирования: {settings.LOG_LEVEL}")
    logging.info(f"Файлы логов: {log_dir}")

def get_logger(name: str) -> logging.Logger:
    """Возвращает настроенный логгер."""
    return logging.getLogger(name) 
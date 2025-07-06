import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Settings:
    """Класс для управления настройками приложения."""
    
    # Telegram Bot настройки
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # ID группы куда отправлять
    
    # Настройки парсинга
    PARSER_ENABLED = os.getenv('PARSER_ENABLED', 'true').lower() == 'true'
    PARSER_INTERVAL = int(os.getenv('PARSER_INTERVAL', '300'))  # 5 минут по умолчанию
    
    # Настройки логирования
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Настройки базы данных
    DATABASE_FILE = os.getenv('DATABASE_FILE', 'data/sent_posts.json')
    
    @classmethod
    def validate(cls):
        """Проверяет наличие обязательных настроек."""
        required_settings = [
            ('TELEGRAM_BOT_TOKEN', cls.TELEGRAM_BOT_TOKEN),
            ('TELEGRAM_CHAT_ID', cls.TELEGRAM_CHAT_ID)
        ]
        
        missing_settings = []
        for name, value in required_settings:
            if not value:
                missing_settings.append(name)
        
        if missing_settings:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_settings)}")
        
        return True

# Создаем экземпляр настроек
settings = Settings() 
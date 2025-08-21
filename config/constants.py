# Константы для парсеров
PARSERS = {
    'JOYREACTOR': {
        'BASE_URL': 'https://joyreactor.cc',
        'TAG_URL': 'https://joyreactor.cc/tag/%D0%BF%D1%80%D0%B8%D0%BA%D0%BE%D0%BB%D1%8B%20%D0%B4%D0%BB%D1%8F%20%D0%BF%D0%BE%D0%BB%D0%BD%D1%8B%D1%85%20%D0%B4%D0%B5%D0%B3%D0%B5%D0%BD%D0%B5%D1%80%D0%B0%D1%82%D0%BE%D0%B2',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'REQUEST_DELAY': 2,  # Задержка между запросами в секундах
        'IMAGE_SELECTORS': {
            'POST_CONTAINER': 'div',  # Попробуем найти все div элементы
            'IMAGE': 'img',
            'POST_LINK': 'a[href*="/post/"]'
        }
    },
    'REDDIT': {
        'BASE_URL': 'https://www.reddit.com',
        'SUBREDDIT': 'KafkaFPS',  # Название subreddit без r/
        'JSON_URL': 'https://www.reddit.com/r/KafkaFPS/.json',
        'HTML_URL': 'https://www.reddit.com/r/KafkaFPS/',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 RedditParser/1.0',
        'REQUEST_DELAY': 3,  # Reddit более строг к частоте запросов
        'USE_JSON_API': True,  # Предпочитаем JSON API
        'IMAGE_SELECTORS': {
            'POST_CONTAINER': '[data-testid="post-container"], .Post, .thing',
            'IMAGE': 'img[src*="i.redd.it"], img[src*="preview.redd.it"], img[src*="external-preview.redd.it"]',
            'VIDEO': 'video, source[src*=".mp4"]',
            'POST_LINK': 'a[href*="/r/"][href*="/comments/"], .title > a',
            'TITLE': '[data-testid="post-content"] h3, .Post h3, .title a, .thing .title'
        },
        'HEADERS': {
            'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    }
}

# Telegram настройки
TELEGRAM = {
    'MAX_IMAGE_SIZE': 10 * 1024 * 1024,  # 10MB
    'MAX_VIDEO_SIZE': 50 * 1024 * 1024,  # 50MB для видео
    'SUPPORTED_IMAGE_FORMATS': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'SUPPORTED_VIDEO_FORMATS': ['.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv'],
    'PARSE_MODE': 'HTML',
    'DISABLE_NOTIFICATION': False
}

# Общие настройки
GENERAL = {
    'PARSER_INTERVAL': 120,  # Интервал парсинга в секундах (2 минуты)
    'MAX_POSTS_PER_RUN': 50,  # Максимум постов за один раз (увеличено для всей страницы)
    'DATABASE_FILE': 'data/sent_posts.json',  # Файл для хранения отправленных постов
    'LOGS_FOLDER': 'logs',
    'DATA_FOLDER': 'data'
}

# Фильтрация контента
CONTENT_FILTERS = {
    'JOYREACTOR': {
        'FILTER_ENABLED': True,
        'BLOCKED_PHRASES': [
            'отличный комментарий',
            'отличный комментарий!',
            'отличный комментарий.',
            'прекрасный комментарий',
            'замечательный комментарий',
            'хороший комментарий',
            'годный комментарий',
            'топовый комментарий',
            'крутой комментарий'
        ]
    },
    'REDDIT': {
        'FILTER_ENABLED': False,  # По умолчанию отключено для Reddit
        'BLOCKED_PHRASES': [
            '[deleted]',
            '[removed]'
        ],
        'MIN_SCORE': 1,  # Минимальный рейтинг поста
        'FILTER_NSFW': False  # Фильтровать NSFW контент (если нужно)
    }
}

# Заголовки для HTTP запросов
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Настройки для сохранения изображений на ПК
IMAGE_STORAGE = {
    'SAVE_IMAGES': True,  # Включить сохранение изображений на ПК
    'IMAGES_DIR': 'downloaded_images',  # Папка для сохранения изображений
    'ORGANIZE_BY_DATE': True,  # Организовать по датам (YYYY-MM-DD)
    'MAX_FILENAME_LENGTH': 100  # Максимальная длина имени файла
} 
# ⚙️ Переменные окружения Parser Bot

## 🔧 Настройка .env файла

Parser Bot использует файл `.env` для хранения всех настроек. Docker Compose автоматически загружает переменные из этого файла.

### Быстрое создание .env
```bash
# Windows  
docker.bat setup

# Linux/Mac
make setup-volumes
```

### Ручное создание
```bash
cp env.example .env
notepad .env  # Редактировать файл
```

## 📝 Обязательные переменные

```bash
# Токен Telegram бота (получить у @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCDEF_your_bot_token_here

# ID канала куда отправлять посты (с минусом для каналов)
TELEGRAM_CHANNEL_ID=-1001234567890
```

## ⚙️ Основные настройки

### Режим работы
```bash
BOT_MODE=scheduler          # scheduler, test или cleanup
PARSER_INTERVAL=300         # Интервал парсинга (секунды)
```

### Логирование
```bash
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE=true            # Писать в файл
```

### Медиа файлы
```bash
SAVE_IMAGES=true            # Сохранять на диск
AUTO_CLEANUP_ENABLED=true   # Автоочистка 
FILES_KEEP_HOURS=48         # Хранить 48 часов
```

### Reddit парсер
```bash
REDDIT_SUBREDDIT=KafkaFPS   # Название subreddit
REDDIT_USE_JSON_API=true    # Использовать JSON API
REDDIT_REQUEST_DELAY=3      # Задержка между запросами
```

## ✅ Проверка настроек

### Проверить .env файл
```bash
# Windows
type .env

# Linux/Mac  
cat .env
```

### Проверить загрузку в Docker
```bash
# Проверить синтаксис compose файла
docker-compose config --quiet

# Тестовый запуск с выводом переменных
docker run --env-file .env parser-bot:latest printenv | grep TELEGRAM
```

### Тестовый режим
```bash
# Запустить проверку конфигурации
docker run --env-file .env -e BOT_MODE=test parser-bot:latest
```

## 🚨 Безопасность

### ⚠️ НЕ КОММИТЬТЕ .env файл!
Файл `.env` содержит секретные токены и уже добавлен в `.gitignore`.

### ✅ Используйте разные .env для разных сред
```bash
.env                    # Локальная разработка
.env.production         # Продакшн
.env.staging           # Тестовая среда
```

### 🔐 Безопасное хранение токенов
- Используйте переменные окружения системы
- Используйте Docker Secrets в продакшне
- Не передавайте токены в логах

## 🐳 Docker Compose интеграция

Docker Compose автоматически:
- ✅ Читает `.env` файл из той же директории
- ✅ Загружает переменные в контейнер
- ✅ Подставляет переменные в docker-compose.yml (если используется синтаксис `${VARIABLE}`)

### Пример использования в compose
```yaml
services:
  parser-bot:
    image: parser-bot:latest
    env_file:
      - .env                 # ← Автоматическая загрузка
    environment:
      - DEBUG=${DEBUG:-false}  # ← Подстановка из .env
```

## 📋 Полный список переменных

Все доступные переменные см. в файле [env.example](env.example)

## 🔧 Устранение проблем

### Проблема: "Файл .env не найден"
```bash
# Создать из шаблона
cp env.example .env
```

### Проблема: "Invalid token"
```bash  
# Проверить токен у @BotFather в Telegram
# Убедиться что токен скопирован полностью
```

### Проблема: "Cannot send to channel"
```bash
# Проверить что бот добавлен в канал
# Проверить что ID канала правильный (с минусом)
# Проверить что у бота есть права на отправку сообщений
``` 
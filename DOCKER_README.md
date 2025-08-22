# 🐳 Parser Bot Docker Setup

Инструкция по запуску Parser Bot в Docker контейнере.

## 🚀 Быстрый старт

### 1. Подготовка окружения

```bash
# Клонируем репозиторий
git clone <your-repo-url>
cd parser-bot

# Создаем директории для данных
make setup-volumes

# Копируем пример конфигурации
cp env.example .env
```

### 2. Настройка переменных окружения

Docker Compose автоматически загружает переменные из файла `.env`. Отредактируйте его:

```bash
# Обязательные настройки
TELEGRAM_BOT_TOKEN=1234567890:ABCDEF_your_bot_token_here
TELEGRAM_CHANNEL_ID=-1001234567890

# Остальные настройки можно оставить по умолчанию
```

### 3. Запуск

```bash
# Сборка образа
make build

# Запуск в фоновом режиме
make up

# Проверка статуса
make status

# Просмотр логов
make logs
```

## 📦 Структура проекта

```
parser-bot/
├── 🐳 Docker файлы
│   ├── Dockerfile              # Основной Docker образ
│   ├── docker-compose.yml      # Оркестрация сервисов
│   ├── docker-entrypoint.sh    # Скрипт запуска
│   └── .dockerignore           # Исключения для сборки
│
├── 📁 Конфигурация
│   ├── env.example             # Пример переменных окружения
│   └── config/                 # Настройки приложения
│
├── 💾 Постоянные данные
│   └── docker-volumes/         # Монтируемые директории
│       ├── images/             # Сохраненные медиа файлы
│       ├── logs/               # Логи приложения
│       └── data/               # База данных (JSON)
│
└── 🛠️ Управление
    ├── Makefile                # Команды управления
    └── DOCKER_README.md        # Эта документация
```

## 🛠️ Команды управления

### 📦 Сборка и запуск
```bash
make build              # Собрать Docker образ
make up                 # Запустить сервисы
make down               # Остановить сервисы
make restart            # Перезапустить сервисы
```

### 📊 Мониторинг
```bash
make logs               # Показать логи всех сервисов
make logs-bot           # Показать логи только бота
make status             # Показать статус контейнеров
make stats              # Показать статистику ресурсов
```

### 🔧 Разработка
```bash
make shell              # Зайти в контейнер
make shell-root         # Зайти в контейнер как root
make test               # Запустить тесты
```

### 🗑️ Управление файлами
```bash
make cleanup            # Запустить очистку файлов
make media-stats        # Показать статистику медиа файлов
```

### 🧹 Очистка системы
```bash
make clean              # Удалить контейнеры и образы
make clean-all          # Полная очистка (включая volumes)
```

## ⚙️ Режимы работы

Parser Bot поддерживает несколько режимов работы через переменную `BOT_MODE`:

### 📅 Scheduler (по умолчанию)
```bash
BOT_MODE=scheduler      # Планировщик - автоматический парсинг
```

### 🧪 Test
```bash
BOT_MODE=test           # Тестовый режим - проверка конфигурации
```

### 🗑️ Cleanup
```bash
BOT_MODE=cleanup        # Режим очистки - удаление старых файлов
```

## 🔧 Настройка переменных окружения

### 📺 Telegram Bot
```bash
TELEGRAM_BOT_TOKEN=     # Токен бота от @BotFather
TELEGRAM_CHANNEL_ID=    # ID канала (с минусом для каналов)
```

### ⏰ Планировщик
```bash
PARSER_INTERVAL=300     # Интервал парсинга (секунды)
MAX_POSTS_PER_CYCLE=10  # Максимум постов за цикл
```

### 📊 Логирование
```bash
LOG_LEVEL=INFO          # Уровень логирования
LOG_TO_FILE=true        # Запись в файл
```

### 💾 Медиа файлы
```bash
SAVE_IMAGES=true        # Сохранять на диск
ORGANIZE_BY_DATE=true   # Организация по датам
AUTO_CLEANUP_ENABLED=true   # Автоочистка
FILES_KEEP_HOURS=48     # Хранить 48 часов
```

### 🌐 Reddit парсер
```bash
REDDIT_SUBREDDIT=KafkaFPS       # Название subreddit
REDDIT_USE_JSON_API=true        # Использовать JSON API
REDDIT_REQUEST_DELAY=3          # Задержка между запросами
```

## 📊 Мониторинг

### Просмотр логов в реальном времени
```bash
# Все сервисы
docker-compose logs -f

# Только основной бот
docker-compose logs -f parser-bot

# Последние 100 строк
docker-compose logs --tail=100 parser-bot
```

### Статистика ресурсов
```bash
# Использование CPU/Memory
docker stats parser-bot

# Размер образа
docker images parser-bot
```

### Проверка здоровья контейнера
```bash
# Статус health check
docker inspect parser-bot | grep -A 5 "Health"
```

## 💾 Резервное копирование

### Создание бекапа
```bash
make backup             # Создает архив в ./backups/
```

### Восстановление из бекапа
```bash
# Остановить сервисы
make down

# Восстановить данные
tar -xzf ./backups/parser-bot-backup-YYYYMMDD-HHMMSS.tar.gz

# Запустить сервисы
make up
```

## 🚨 Устранение неисправностей

### Проблемы с запуском
```bash
# Проверить логи
make logs-bot

# Проверить конфигурацию
docker run --rm -e BOT_MODE=test parser-bot

# Пересобрать образ
make build-no-cache
```

### Проблемы с правами доступа
```bash
# Зайти в контейнер как root
make shell-root

# Проверить владельца файлов
ls -la /app/

# Исправить права
chown -R botuser:botuser /app/
```

### Проблемы с местом на диске
```bash
# Показать использование диска
du -sh ./docker-volumes/

# Запустить очистку
make cleanup

# Показать статистику файлов  
make media-stats
```

### Очистка Docker системы
```bash
# Удалить неиспользуемые образы
docker image prune -f

# Удалить неиспользуемые контейнеры
docker container prune -f

# Полная очистка системы
docker system prune -f --volumes
```

## 🔄 Обновление

```bash
# Остановить текущие сервисы
make down

# Получить обновления кода
git pull

# Пересобрать образ
make build-no-cache

# Запустить с новым образом
make up
```

## 📝 Логи и отладка

### Расположение логов
- **Внутри контейнера**: `/app/logs/`
- **На хосте**: `./docker-volumes/logs/`

### Экспорт логов
```bash
# Экспортировать в файл
make export-logs

# Найти в ./exported-logs/
```

### Отладка
```bash
# Запуск в интерактивном режиме
docker run -it --rm parser-bot /bin/bash

# Тестирование конфигурации
docker run --rm -e BOT_MODE=test parser-bot
```

## 🌐 Production развертывание

### Рекомендации для продакшена
1. **Используйте .env файл** для секретных данных
2. **Настройте логирование** с ротацией файлов
3. **Мониторьте ресурсы** контейнера
4. **Регулярно создавайте бекапы**
5. **Обновляйте образы** для безопасности

### Развертывание на сервере
```bash
# Клонирование на сервер
git clone <repo-url> /opt/parser-bot
cd /opt/parser-bot

# Настройка
cp env.example .env
# Отредактировать .env

# Создание директорий
make setup-volumes

# Запуск
make build
make up

# Настройка автозапуска (systemd)
sudo systemctl enable docker
```

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи**: `make logs-bot`
2. **Проверьте статус**: `make status`
3. **Проверьте конфигурацию**: файл `.env`
4. **Пересоберите образ**: `make build-no-cache`
5. **Очистите систему**: `make clean && make build` 
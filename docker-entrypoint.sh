#!/bin/bash
set -e

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🚀 Запуск Parser Bot..."

# Создаем необходимые директории если их нет
mkdir -p /app/downloaded_images
mkdir -p /app/logs  
mkdir -p /app/data

log "📂 Директории созданы"

# Проверяем наличие конфигурации
if [[ ! -f "/app/config/settings.py" ]]; then
    log "⚠️  Внимание: файл настроек config/settings.py не найден"
    log "📝 Используются настройки по умолчанию"
fi

# Проверяем переменные окружения
if [[ -z "$TELEGRAM_BOT_TOKEN" ]]; then
    log "❌ ОШИБКА: не указан TELEGRAM_BOT_TOKEN"
    log "💡 Установите переменную окружения или создайте .env файл"
    exit 1
fi

if [[ -z "$TELEGRAM_CHANNEL_ID" ]]; then
    log "❌ ОШИБКА: не указан TELEGRAM_CHANNEL_ID"  
    log "💡 Установите переменную окружения или создайте .env файл"
    exit 1
fi

log "✅ Telegram настройки проверены"

# Проверяем соединение с интернетом
log "🌐 Проверка соединения с интернетом..."
if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    log "✅ Соединение с интернетом установлено"
else
    log "⚠️  Предупреждение: проблемы с интернет соединением"
fi

# Выводим информацию о режиме запуска
BOT_MODE=${BOT_MODE:-scheduler}
log "⚙️  Режим работы: $BOT_MODE"

# Выводим статистику медиа файлов
if [[ -d "/app/downloaded_images" ]]; then
    file_count=$(find /app/downloaded_images -type f 2>/dev/null | wc -l)
    if [[ $file_count -gt 0 ]]; then
        log "📊 Найдено сохраненных медиа файлов: $file_count"
    else
        log "📁 Директория медиа файлов пуста"
    fi
fi

# Запуск различных режимов
case "$BOT_MODE" in
    "scheduler")
        log "🔄 Запуск в режиме планировщика..."
        exec python main.py
        ;;
    "test")
        log "🧪 Запуск в тестовом режиме..."
        python -c "
import asyncio
from utils.database import database
from config.constants import IMAGE_STORAGE

async def test():
    print('🔍 Тестирование конфигурации...')
    await database.load()
    stats = await database.get_stats()
    print(f'📊 База данных: {stats}')
    
    print(f'⚙️  Настройки медиа: SAVE_IMAGES={IMAGE_STORAGE.get(\"SAVE_IMAGES\")}')
    print(f'🗑️  Автоочистка: {IMAGE_STORAGE.get(\"AUTO_CLEANUP_ENABLED\")}')
    print('✅ Тест завершен успешно')

asyncio.run(test())
"
        ;;
    "cleanup")
        log "🗑️ Запуск очистки файлов..."
        python cleanup_files.py --cleanup
        ;;
    *)
        log "❌ Неизвестный режим: $BOT_MODE"
        log "💡 Доступные режимы: scheduler, test, cleanup"
        exit 1
        ;;
esac

log "🏁 Завершение работы Parser Bot" 
# 🐳 Parser Bot - Quick Docker Start

## ⚡ Быстрый старт (3 шага)

### 1️⃣ Настройка окружения
```bash
# Создать необходимые папки и .env файл
docker.bat setup

# Заполнить настройки Telegram в файле .env
notepad .env
```

### 2️⃣ Сборка и запуск  
```bash
# Собрать образ
docker.bat build

# Запустить бота
docker.bat up
```

### 3️⃣ Проверка работы
```bash
# Посмотреть статус
docker.bat status

# Посмотреть логи
docker.bat logs
```

## 🔧 Основные команды

| Команда | Описание |
|---------|----------|
| `docker.bat setup` | Создать папки и .env файл |
| `docker.bat build` | Собрать Docker образ |
| `docker.bat up` | Запустить бота |
| `docker.bat down` | Остановить бота |
| `docker.bat logs` | Посмотреть логи |
| `docker.bat status` | Проверить статус |
| `docker.bat shell` | Зайти в контейнер |
| `docker.bat cleanup` | Очистить старые файлы |

## ⚙️ Настройки в .env файле

**Обязательные:**
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCDEF_your_bot_token_here
TELEGRAM_CHANNEL_ID=-1001234567890
```

**Опциональные (уже настроены):**
```bash
BOT_MODE=scheduler           # Автоматический режим
PARSER_INTERVAL=300          # Каждые 5 минут  
AUTO_CLEANUP_ENABLED=true    # Автоочистка включена
FILES_KEEP_HOURS=48          # Хранить файлы 48 часов
```

## 📊 Что делает бот

1. **Парсит Reddit** (r/KafkaFPS) каждые 5 минут
2. **Скачивает видео со звуком** + изображения
3. **Сохраняет на диск** в `docker-volumes/images/`
4. **Отправляет в Telegram** с описанием
5. **Удаляет дубликаты** по хешу
6. **Очищает старые файлы** каждый час

## 🚨 Если что-то не работает

```bash
# Посмотреть логи ошибок
docker.bat logs

# Остановить и перезапустить
docker.bat down
docker.bat up

# Пересобрать образ (при обновлении кода)
docker.bat build
```

## 📁 Структура файлов

```
parser bot/
├── 🐳 Docker
│   ├── Dockerfile
│   ├── docker-compose.yml  
│   └── docker.bat
├── ⚙️ Настройки
│   ├── .env               # ← ЗДЕСЬ ТОКЕНЫ!
│   └── config/
└── 💾 Данные
    └── docker-volumes/
        ├── images/        # Скачанные медиа
        ├── logs/          # Логи бота
        └── data/          # База данных
```

## 🎯 Результат

✅ **Бот работает в фоне**  
✅ **Reddit видео со звуком**  
✅ **Автоматическая очистка**  
✅ **Без дубликатов**  
✅ **Организация по датам**  

---

**📞 Проблемы?** Смотри полную документацию в [DOCKER_README.md](DOCKER_README.md) 
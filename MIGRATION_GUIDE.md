# 🚀 Parser Bot - Миграция на сервер

Краткое руководство по развертыванию Parser Bot на удаленном сервере за 5 минут.

## ⚡ Быстрая миграция (рекомендуется)

### 1️⃣ Подготовка
```bash
# На локальной машине - убедитесь что у вас есть:
ls -la server-migrate.sh server-deploy.sh SERVER_README.md

# Проверьте SSH соединение с сервером
ssh user@your-server.com
```

### 2️⃣ Автоматическая миграция

#### **С SSH ключами (рекомендуется):**
```bash
# Запускаем миграцию (замените на ваш сервер)
bash server-migrate.sh user@your-server.com
```

#### **С паролем SSH:**
```bash
# Для серверов где требуется пароль
bash server-migrate-password.sh user@your-server.com
# Скрипт будет запрашивать пароль на каждом этапе
```

**Скрипт выполнит:**
- ✅ Копирование файлов
- ✅ Установку Docker
- ✅ Создание пользователя и директорий  
- ✅ Настройку systemd сервиса
- ✅ Запуск Parser Bot

### 3️⃣ Настройка Telegram токенов
```bash
# Подключитесь к серверу
ssh user@your-server.com

# Настройте .env файл
sudo cp /opt/parser-bot/.env.example /opt/parser-bot/.env
sudo nano /opt/parser-bot/.env

# Заполните обязательные поля:
# TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
# TELEGRAM_CHANNEL_ID=ваш_канал_ID

# Перезапустите сервис
sudo systemctl restart parser-bot
```

### 4️⃣ Проверка работы
```bash
# Проверить статус
systemctl status parser-bot

# Посмотреть логи
parser-bot logs

# Полный мониторинг
bash /opt/parser-bot/server-monitor.sh
```

## 🔧 Ручная миграция

### Если автоматическая миграция не подходит:

#### На локальной машине:
```bash
# Скопируйте файлы на сервер
scp server-deploy.sh user@your-server.com:/tmp/
scp SERVER_README.md user@your-server.com:/tmp/
scp env.example user@your-server.com:/tmp/
```

#### На сервере:
```bash
# Запустите развертывание
sudo bash /tmp/server-deploy.sh

# Настройте переменные окружения
sudo cp /opt/parser-bot/.env.example /opt/parser-bot/.env
sudo nano /opt/parser-bot/.env

# Запустите сервис
sudo systemctl enable parser-bot
sudo systemctl start parser-bot
```

## 🔐 Работа с SSH паролями

### **Вариант 1: Интерактивный ввод пароля**
```bash
# Используйте специальный скрипт для работы с паролями
bash server-migrate-password.sh user@your-server.com

# При каждом подключении будет запрос:
# user@your-server.com's password: [введите пароль]
```

### **Вариант 2: Настройка SSH ключей (рекомендуется)**
```bash
# 1. Генерируем SSH ключ (если его нет)
ssh-keygen -t rsa -b 4096

# 2. Копируем на сервер (введите пароль в последний раз)
ssh-copy-id user@your-server.com

# 3. Теперь подключение без пароля
ssh user@your-server.com
```

### **Вариант 3: Проверка подключения**
```bash
# Сначала проверьте что можете подключиться
ssh user@your-server.com
# Если подключение работает, запускайте миграцию

# Для принудительного запроса пароля
ssh -o PasswordAuthentication=yes -o PubkeyAuthentication=no user@your-server.com
```

## 🌐 Требования к серверу

### Минимальные требования:
- **ОС**: Ubuntu 18.04+ / Debian 10+ / CentOS 8+
- **RAM**: 1GB (рекомендуется 2GB+)
- **CPU**: 1 core (рекомендуется 2+)
- **Диск**: 10GB свободного места
- **Сеть**: SSH доступ, интернет

### Поддерживаемые дистрибутивы:
- ✅ Ubuntu 20.04, 22.04
- ✅ Debian 11, 12
- ✅ CentOS Stream 8, 9
- ✅ Red Hat Enterprise Linux 8+
- ✅ Amazon Linux 2

## 📊 Управление на сервере

### Основные команды:
```bash
# Статус и управление
systemctl status parser-bot       # Статус systemd сервиса
parser-bot start                  # Запуск
parser-bot stop                   # Остановка
parser-bot restart                # Перезапуск
parser-bot logs                   # Логи
parser-bot status                 # Статус контейнера

# Обслуживание
parser-bot update                 # Обновление образа
parser-bot cleanup                # Очистка старых файлов
parser-bot backup                 # Резервная копия

# Мониторинг
bash server-monitor.sh            # Полный мониторинг
bash server-monitor.sh -i         # Интерактивный мониторинг
htop                              # Системные ресурсы
df -h                             # Место на диске
```

### Docker команды:
```bash
docker ps                         # Запущенные контейнеры
docker logs -f parser-bot          # Логи в реальном времени
docker stats parser-bot           # Статистика ресурсов
docker exec -it parser-bot bash   # Вход в контейнер
```

## 🔄 Структура на сервере

После развертывания на сервере будет создана следующая структура:

```
/opt/parser-bot/                  # Основная директория
├── docker-compose.yml            # Конфигурация Docker Compose
├── .env                          # Переменные окружения ← НАСТРОИТЬ!
├── .env.example                  # Пример настроек
├── manage.sh                     # Скрипт управления
├── downloaded_images/            # Скачанные медиа файлы
├── logs/                         # Логи приложения
└── data/                         # База данных (JSON)

/etc/systemd/system/
└── parser-bot.service            # Systemd сервис

/usr/local/bin/
└── parser-bot -> /opt/parser-bot/manage.sh  # Глобальная команда
```

## 🚨 Быстрое устранение проблем

### Сервис не запускается:
```bash
# Проверить статус и логи
systemctl status parser-bot -l
journalctl -u parser-bot -f

# Проверить Docker
sudo systemctl status docker
docker version

# Проверить конфигурацию
cd /opt/parser-bot
docker-compose config
```

### Контейнер не работает:
```bash
# Перезапуск
systemctl restart parser-bot

# Обновление образа
parser-bot update

# Проверить .env файл
sudo nano /opt/parser-bot/.env
```

### Нехватка места на диске:
```bash
# Очистить старые файлы
parser-bot cleanup

# Очистить Docker
docker system prune -f

# Проверить использование диска
du -sh /opt/parser-bot/*
```

## 📞 Получение помощи

### Диагностическая информация:
```bash
# Создать отчет для диагностики
{
    echo "=== System Info ==="
    uname -a
    echo "=== Docker Version ==="
    docker version
    echo "=== Service Status ==="
    systemctl status parser-bot
    echo "=== Container Status ==="
    docker ps -a
    echo "=== Logs ==="
    docker logs parser-bot --tail=50
    echo "=== Disk Usage ==="
    df -h
    echo "=== Memory Usage ==="
    free -h
} > debug-report.txt

# Отправить debug-report.txt для анализа
```

### Контакты для поддержки:
- 📖 Подробная документация: `SERVER_README.md`
- 🔍 Мониторинг: `bash server-monitor.sh`
- 🐛 GitHub Issues: (добавьте ссылку на ваш репозиторий)

## ✅ Проверочный список

После миграции убедитесь что:

- [ ] ✅ Сервер доступен по SSH
- [ ] ✅ Docker установлен и работает
- [ ] ✅ Образ `kureed/parser-bot:latest` скачан
- [ ] ✅ Файл `/opt/parser-bot/.env` настроен
- [ ] ✅ Сервис `parser-bot` активен
- [ ] ✅ Контейнер запущен: `docker ps | grep parser-bot`
- [ ] ✅ Логи не показывают ошибки: `parser-bot logs`
- [ ] ✅ Telegram бот отвечает на сообщения
- [ ] ✅ Посты парсятся и отправляются в канал

## 🎯 Результат

После успешной миграции у вас будет:

🚀 **Parser Bot работает на сервере 24/7**  
📦 **Docker контейнер с автоперезапуском**  
🔄 **Systemd сервис с автозапуском**  
📊 **Мониторинг и логирование**  
🗑️ **Автоматическая очистка файлов**  
💾 **Резервное копирование данных**  
🔧 **Удобное управление через команды**  

Ваш Parser Bot готов к production использованию! 🎉 
# 🚀 Parser Bot - Развертывание на сервере

Полное руководство по развертыванию Parser Bot на удаленном сервере.

## 📋 Требования к серверу

### Минимальные требования:
- **ОС**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM**: 1GB (рекомендуется 2GB+)
- **CPU**: 1 core (рекомендуется 2+ cores)
- **Диск**: 10GB свободного места
- **Сеть**: Доступ к интернету

### Рекомендуемые требования:
- **RAM**: 4GB+
- **CPU**: 2+ cores
- **Диск**: 50GB+ (для медиа файлов)
- **SSD**: для быстрой работы с базой данных

## 🔧 Методы развертывания

### Метод 1: Автоматическое развертывание (рекомендуется)

#### На локальной машине:
```bash
# Копируем скрипт на сервер
scp server-deploy.sh user@your-server.com:/tmp/

# Подключаемся к серверу
ssh user@your-server.com
```

#### На сервере:
```bash
# Запускаем автоматическое развертывание
sudo bash /tmp/server-deploy.sh

# Настраиваем переменные окружения
sudo cp /opt/parser-bot/.env.example /opt/parser-bot/.env
sudo nano /opt/parser-bot/.env

# Запускаем сервис
sudo systemctl enable parser-bot
sudo systemctl start parser-bot

# Проверяем статус
systemctl status parser-bot
parser-bot logs
```

### Метод 2: Ручное развертывание

#### 1. Установка Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl enable docker
sudo systemctl start docker

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Создание структуры проекта
```bash
# Создаем директории
sudo mkdir -p /opt/parser-bot/{logs,data,downloaded_images}
sudo useradd -r parser-bot
sudo chown -R parser-bot:parser-bot /opt/parser-bot

# Переходим в директорию
cd /opt/parser-bot
```

#### 3. Создание файлов конфигурации
```bash
# docker-compose.yml
sudo tee docker-compose.yml << 'EOF'
services:
  parser-bot:
    image: kureed/parser-bot:latest
    container_name: parser-bot
    restart: unless-stopped
    
    env_file:
      - .env
      
    volumes:
      - ./downloaded_images:/app/downloaded_images
      - ./logs:/app/logs
      - ./data:/app/data
    
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
EOF

# Переменные окружения
sudo cp .env.example .env
sudo nano .env  # Заполните ваши данные
```

#### 4. Создание systemd сервиса
```bash
sudo tee /etc/systemd/system/parser-bot.service << 'EOF'
[Unit]
Description=Parser Bot
After=docker.service
Requires=docker.service

[Service]
Type=forking
RemainAfterExit=yes
WorkingDirectory=/opt/parser-bot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart
User=parser-bot
Group=parser-bot
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable parser-bot
sudo systemctl start parser-bot
```

## ⚙️ Конфигурация .env файла

### Обязательные параметры:
```bash
# Telegram бот (получить у @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCDEF_your_bot_token_here

# ID канала (с минусом для каналов)
TELEGRAM_CHANNEL_ID=-1001234567890
```

### Дополнительные настройки:
```bash
# Режим работы
BOT_MODE=scheduler
PARSER_INTERVAL=300  # 5 минут

# Логирование
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Медиа файлы
SAVE_IMAGES=true
AUTO_CLEANUP_ENABLED=true
FILES_KEEP_HOURS=48

# Reddit настройки
REDDIT_SUBREDDIT=KafkaFPS
REDDIT_USE_JSON_API=true
REDDIT_REQUEST_DELAY=3
```

## 🛠️ Управление сервисом

### Systemctl команды:
```bash
# Статус сервиса
systemctl status parser-bot

# Запуск/остановка/перезапуск
systemctl start parser-bot
systemctl stop parser-bot
systemctl restart parser-bot

# Автозапуск
systemctl enable parser-bot   # Включить
systemctl disable parser-bot  # Отключить

# Логи systemd
journalctl -u parser-bot -f
```

### Команды parser-bot:
```bash
# Основные команды
parser-bot start        # Запуск
parser-bot stop         # Остановка  
parser-bot restart      # Перезапуск
parser-bot status       # Статус
parser-bot logs         # Логи

# Обслуживание
parser-bot update       # Обновление образа
parser-bot cleanup      # Очистка файлов
parser-bot backup       # Резервная копия
```

### Docker команды:
```bash
# Статус контейнеров
docker ps
docker-compose ps

# Логи
docker-compose logs -f parser-bot

# Обновление образа
docker-compose pull
docker-compose up -d

# Вход в контейнер
docker exec -it parser-bot /bin/bash
```

## 📊 Мониторинг

### Проверка работы:
```bash
# Статус всех компонентов
systemctl status parser-bot
docker ps
parser-bot status

# Использование ресурсов  
htop
docker stats parser-bot

# Место на диске
df -h
du -sh /opt/parser-bot/downloaded_images/
```

### Логи:
```bash
# Логи приложения
parser-bot logs

# Системные логи
journalctl -u parser-bot -f

# Docker логи
docker logs -f parser-bot
```

### Мониторинг медиа файлов:
```bash
# Количество файлов
find /opt/parser-bot/downloaded_images -type f | wc -l

# Размер директории
du -sh /opt/parser-bot/downloaded_images/

# Очистка старых файлов
parser-bot cleanup
```

## 💾 Резервное копирование

### Автоматическое резервное копирование:
```bash
# Создание бэкапа
parser-bot backup

# Настройка cron для ежедневных бэкапов
sudo crontab -e
# Добавить: 0 2 * * * /usr/local/bin/parser-bot backup
```

### Ручное резервное копирование:
```bash
# Полный бэкап
sudo tar -czf "/tmp/parser-bot-full-$(date +%Y%m%d).tar.gz" \
    /opt/parser-bot

# Только данные
sudo tar -czf "/tmp/parser-bot-data-$(date +%Y%m%d).tar.gz" \
    /opt/parser-bot/data \
    /opt/parser-bot/.env \
    /opt/parser-bot/logs
```

### Восстановление из бэкапа:
```bash
# Остановить сервис
systemctl stop parser-bot

# Восстановить данные
sudo tar -xzf parser-bot-backup-20231225.tar.gz -C /

# Исправить права доступа
sudo chown -R parser-bot:parser-bot /opt/parser-bot

# Запустить сервис
systemctl start parser-bot
```

## 🔄 Обновления

### Обновление образа:
```bash
# Простое обновление
parser-bot update

# Ручное обновление
cd /opt/parser-bot
sudo -u parser-bot docker-compose pull
sudo -u parser-bot docker-compose up -d
```

### Обновление системы:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y

# Перезагрузка при необходимости
sudo reboot
```

## 🔐 Безопасность

### Настройка файрвола:
```bash
# UFW (Ubuntu/Debian)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80   # если нужен веб-интерфейс
sudo ufw allow 443  # если нужен HTTPS

# Проверка
sudo ufw status
```

### Ограничение доступа:
```bash
# Права доступа к .env
sudo chmod 600 /opt/parser-bot/.env
sudo chown parser-bot:parser-bot /opt/parser-bot/.env

# Ограничение SSH доступа (в /etc/ssh/sshd_config)
PermitRootLogin no
PasswordAuthentication no
AllowUsers your-username
```

### Мониторинг безопасности:
```bash
# Проверка логов аутентификации
sudo tail -f /var/log/auth.log

# Активные соединения
sudo netstat -tulpn

# Запущенные сервисы
sudo systemctl list-units --type=service --state=running
```

## 🚨 Устранение неисправностей

### Сервис не запускается:
```bash
# Проверить статус
systemctl status parser-bot -l

# Проверить логи
journalctl -u parser-bot -n 50

# Проверить Docker
sudo systemctl status docker
docker version
```

### Контейнер не запускается:
```bash
# Проверить образ
docker images kureed/parser-bot

# Скачать образ заново
docker pull kureed/parser-bot:latest

# Проверить конфигурацию
cd /opt/parser-bot
docker-compose config
```

### Проблемы с правами доступа:
```bash
# Исправить права
sudo chown -R parser-bot:parser-bot /opt/parser-bot
sudo chmod -R 755 /opt/parser-bot
sudo chmod 600 /opt/parser-bot/.env
```

### Проблемы с местом на диске:
```bash
# Проверить место
df -h

# Очистить старые файлы
parser-bot cleanup

# Очистить Docker
docker system prune -f

# Удалить старые логи
sudo journalctl --vacuum-time=7d
```

## 📞 Поддержка

### Проверочный список:
1. ✅ Docker установлен и запущен
2. ✅ Образ `kureed/parser-bot:latest` скачан
3. ✅ Файл `.env` настроен с корректными токенами
4. ✅ Сервис `parser-bot` включен и запущен
5. ✅ Нет ошибок в логах
6. ✅ Контейнер работает: `docker ps`

### Получение помощи:
```bash
# Сбор диагностической информации
echo "=== System Info ===" > debug.log
uname -a >> debug.log
echo "=== Docker Info ===" >> debug.log
docker version >> debug.log
echo "=== Service Status ===" >> debug.log
systemctl status parser-bot >> debug.log
echo "=== Container Status ===" >> debug.log
docker ps -a >> debug.log
echo "=== Logs ===" >> debug.log
docker logs parser-bot --tail=50 >> debug.log
```

### Полезные команды для диагностики:
```bash
# Проверка сети
curl -I https://api.telegram.org/
curl -I https://reddit.com/

# Проверка ресурсов
free -h
df -h
docker stats parser-bot --no-stream

# Проверка процессов
ps aux | grep parser-bot
``` 
#!/bin/bash

# Parser Bot - Миграция на сервер (с поддержкой пароля)
# Использование: bash server-migrate-password.sh user@server.com

set -e

# Переменные
SERVER=$1
LOCAL_DIR="$(pwd)"
SSH_OPTS="-o PasswordAuthentication=yes -o PubkeyAuthentication=no"

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Проверка параметров
check_params() {
    if [ -z "$SERVER" ]; then
        log_error "Не указан сервер!"
        echo "Использование: bash server-migrate-password.sh user@server.com"
        echo
        echo "Примеры:"
        echo "  bash server-migrate-password.sh root@192.168.1.100"
        echo "  bash server-migrate-password.sh ubuntu@myserver.com"
        exit 1
    fi
}

# Проверка SSH соединения с паролем
check_ssh_with_password() {
    log_info "Проверка SSH соединения с $SERVER..."
    log_warning "Потребуется ввести пароль для SSH подключения"
    
    if ssh $SSH_OPTS -o ConnectTimeout=10 "$SERVER" 'exit'; then
        log_success "SSH соединение установлено"
    else
        log_error "Не удается подключиться к серверу"
        echo
        log_info "Возможные решения:"
        echo "1. Проверьте что сервер доступен: ping $(echo $SERVER | cut -d'@' -f2)"
        echo "2. Проверьте правильность логина и пароля"
        echo "3. Попробуйте подключиться вручную: ssh $SERVER"
        echo "4. Убедитесь что SSH сервис запущен на сервере"
        exit 1
    fi
}

# Создание пакета для развертывания
create_deployment_package() {
    log_info "Создание пакета для развертывания..."
    
    # Создаем временную директорию
    TEMP_DIR=$(mktemp -d)
    PACKAGE_DIR="$TEMP_DIR/parser-bot-deploy"
    mkdir -p "$PACKAGE_DIR"
    
    # Копируем необходимые файлы
    cp server-deploy.sh "$PACKAGE_DIR/"
    cp SERVER_README.md "$PACKAGE_DIR/"
    cp env.example "$PACKAGE_DIR/.env.example"
    
    # Создаем docker-compose.yml для сервера
    cat > "$PACKAGE_DIR/docker-compose.yml" << 'EOF'
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
    
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
EOF

    # Создаем README для быстрого старта
    cat > "$PACKAGE_DIR/QUICKSTART.md" << 'EOF'
# 🚀 Быстрый старт на сервере

## 1. Автоматическое развертывание
```bash
sudo bash server-deploy.sh
```

## 2. Настройка конфигурации
```bash
sudo cp /opt/parser-bot/.env.example /opt/parser-bot/.env
sudo nano /opt/parser-bot/.env
# Заполните TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID
```

## 3. Запуск сервиса
```bash
sudo systemctl enable parser-bot
sudo systemctl start parser-bot
```

## 4. Проверка работы
```bash
systemctl status parser-bot
parser-bot logs
```

Подробная документация: SERVER_README.md
EOF

    # Создаем архив
    cd "$TEMP_DIR"
    tar -czf "parser-bot-deploy.tar.gz" parser-bot-deploy/
    
    # Возвращаем путь к архиву
    echo "$TEMP_DIR/parser-bot-deploy.tar.gz"
}

# Копирование файлов на сервер с паролем
copy_files_with_password() {
    log_info "Создание пакета развертывания..."
    PACKAGE_PATH=$(create_deployment_package)
    
    log_info "Копирование файлов на сервер $SERVER..."
    log_warning "Введите пароль для копирования файлов:"
    
    # Копируем архив на сервер
    scp $SSH_OPTS "$PACKAGE_PATH" "$SERVER:/tmp/"
    
    log_info "Распаковка файлов на сервере..."
    log_warning "Введите пароль для выполнения команд на сервере:"
    
    # Распаковываем на сервере
    ssh $SSH_OPTS "$SERVER" "
        cd /tmp && 
        tar -xzf parser-bot-deploy.tar.gz &&
        chmod +x parser-bot-deploy/server-deploy.sh
    "
    
    # Очищаем временные файлы
    rm -rf "$(dirname "$PACKAGE_PATH")"
    
    log_success "Файлы скопированы в /tmp/parser-bot-deploy/"
}

# Запуск развертывания на сервере с паролем
deploy_on_server_with_password() {
    log_info "Запуск развертывания на сервере..."
    log_warning "Потребуются права sudo на сервере"
    log_warning "Введите пароль для SSH подключения:"
    
    ssh $SSH_OPTS -t "$SERVER" "
        cd /tmp/parser-bot-deploy &&
        sudo ./server-deploy.sh
    "
}

# Настройка конфигурации с паролем
configure_env_with_password() {
    log_info "Настройка переменных окружения..."
    
    # Проверяем есть ли локальный .env файл
    if [ -f "$LOCAL_DIR/.env" ]; then
        log_info "Найден локальный .env файл"
        read -p "Скопировать локальные настройки на сервер? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Копирование .env файла..."
            log_warning "Введите пароль для копирования .env файла:"
            scp $SSH_OPTS "$LOCAL_DIR/.env" "$SERVER:/opt/parser-bot/.env"
            
            log_info "Установка прав доступа..."
            log_warning "Введите пароль для изменения прав доступа:"
            ssh $SSH_OPTS "$SERVER" "sudo chown parser-bot:parser-bot /opt/parser-bot/.env"
            log_success ".env файл скопирован"
        else
            log_info "Настройте .env файл вручную на сервере:"
            echo "ssh $SERVER"
            echo "sudo cp /opt/parser-bot/.env.example /opt/parser-bot/.env"
            echo "sudo nano /opt/parser-bot/.env"
        fi
    else
        log_warning "Локальный .env файл не найден"
        log_info "Настройте .env файл на сервере:"
        echo "ssh $SERVER"
        echo "sudo cp /opt/parser-bot/.env.example /opt/parser-bot/.env" 
        echo "sudo nano /opt/parser-bot/.env"
    fi
}

# Запуск сервиса с паролем
start_service_with_password() {
    log_info "Запуск сервиса на сервере..."
    log_warning "Введите пароль для запуска сервиса:"
    
    ssh $SSH_OPTS "$SERVER" "
        sudo systemctl enable parser-bot &&
        sudo systemctl start parser-bot
    "
    
    log_success "Сервис запущен!"
    
    # Проверяем статус
    log_info "Проверка статуса сервиса..."
    log_warning "Введите пароль для проверки статуса:"
    ssh $SSH_OPTS "$SERVER" "systemctl status parser-bot --no-pager"
}

# Проверка результатов с паролем
verify_deployment_with_password() {
    log_info "Проверка развертывания..."
    log_warning "Введите пароль для проверки:"
    
    ssh $SSH_OPTS "$SERVER" "
        echo '=== Проверка Docker контейнера ==='
        docker ps | grep parser-bot || echo 'Контейнер не найден'
        echo
        echo '=== Статус systemd сервиса ==='
        systemctl is-active parser-bot || echo 'Сервис не активен'
        echo
        echo '=== Последние логи ==='
        docker logs parser-bot --tail=10 2>/dev/null || echo 'Логи недоступны'
    "
}

# Основная функция
main() {
    echo "🚀 Parser Bot - Миграция на сервер (с поддержкой пароля)"
    echo "========================================================="
    echo
    
    check_params
    log_info "Запуск миграции на $SERVER с интерактивным вводом пароля"
    
    check_ssh_with_password
    copy_files_with_password
    deploy_on_server_with_password
    configure_env_with_password
    start_service_with_password
    verify_deployment_with_password
    
    log_success "Миграция завершена!"
    echo
    echo "🎯 Полезные команды на сервере:"
    echo "  systemctl status parser-bot    # Статус сервиса"
    echo "  parser-bot logs               # Логи"
    echo "  parser-bot status             # Статус контейнера"
    echo "  parser-bot update             # Обновление"
    echo
    echo "📖 SSH подключение с паролем:"
    echo "  ssh $SERVER"
}

# Запуск
main "$@" 
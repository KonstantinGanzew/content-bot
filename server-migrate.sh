#!/bin/bash

# Parser Bot - Миграция на сервер
# Использование: bash server-migrate.sh user@server.com

set -e

# Переменные
SERVER=$1
LOCAL_DIR="$(pwd)"
REMOTE_DIR="/tmp/parser-bot-deploy"

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
        echo "Использование: bash server-migrate.sh user@server.com"
        echo
        echo "Примеры:"
        echo "  bash server-migrate.sh root@192.168.1.100"
        echo "  bash server-migrate.sh ubuntu@myserver.com"
        echo "  bash server-migrate.sh user@server.com -p 2222"
        exit 1
    fi
}

# Проверка SSH соединения
check_ssh() {
    log_info "Проверка SSH соединения с $SERVER..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER" 'exit' 2>/dev/null; then
        log_success "SSH соединение установлено"
    else
        log_error "Не удается подключиться к серверу"
        log_info "Убедитесь что:"
        log_info "1. Сервер доступен по сети"
        log_info "2. SSH ключи настроены или введите пароль"
        log_info "3. Пользователь имеет права доступа"
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

# Копирование файлов на сервер
copy_files() {
    log_info "Создание пакета развертывания..."
    PACKAGE_PATH=$(create_deployment_package)
    
    log_info "Копирование файлов на сервер $SERVER..."
    
    # Копируем архив на сервер
    scp "$PACKAGE_PATH" "$SERVER:/tmp/"
    
    # Распаковываем на сервере
    ssh "$SERVER" "
        cd /tmp && 
        tar -xzf parser-bot-deploy.tar.gz &&
        chmod +x parser-bot-deploy/server-deploy.sh
    "
    
    # Очищаем временные файлы
    rm -rf "$(dirname "$PACKAGE_PATH")"
    
    log_success "Файлы скопированы в /tmp/parser-bot-deploy/"
}

# Запуск развертывания на сервере
deploy_on_server() {
    log_info "Запуск развертывания на сервере..."
    log_warning "Потребуются права sudo на сервере"
    
    ssh -t "$SERVER" "
        cd /tmp/parser-bot-deploy &&
        sudo ./server-deploy.sh
    "
}

# Настройка конфигурации
configure_env() {
    log_info "Настройка переменных окружения..."
    
    # Проверяем есть ли локальный .env файл
    if [ -f "$LOCAL_DIR/.env" ]; then
        log_info "Найден локальный .env файл"
        read -p "Скопировать локальные настройки на сервер? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Копирование .env файла..."
            scp "$LOCAL_DIR/.env" "$SERVER:/opt/parser-bot/.env"
            ssh "$SERVER" "sudo chown parser-bot:parser-bot /opt/parser-bot/.env"
            log_success ".env файл скопирован"
        else
            log_info "Откройте SSH сессию и настройте .env файл:"
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

# Запуск сервиса
start_service() {
    log_info "Запуск сервиса на сервере..."
    
    ssh "$SERVER" "
        sudo systemctl enable parser-bot &&
        sudo systemctl start parser-bot
    "
    
    log_success "Сервис запущен!"
    
    # Проверяем статус
    log_info "Проверка статуса сервиса..."
    ssh "$SERVER" "systemctl status parser-bot --no-pager"
}

# Проверка результатов
verify_deployment() {
    log_info "Проверка развертывания..."
    
    echo "=== Проверка Docker контейнера ==="
    ssh "$SERVER" "docker ps | grep parser-bot || echo 'Контейнер не найден'"
    
    echo
    echo "=== Статус systemd сервиса ==="
    ssh "$SERVER" "systemctl is-active parser-bot || echo 'Сервис не активен'"
    
    echo
    echo "=== Последние логи ==="
    ssh "$SERVER" "docker logs parser-bot --tail=10 2>/dev/null || echo 'Логи недоступны'"
}

# Интерактивное меню
interactive_menu() {
    echo "🚀 Parser Bot - Миграция на сервер"
    echo "=================================="
    echo
    echo "Что вы хотите сделать?"
    echo "1) Полная миграция (рекомендуется)"
    echo "2) Только копирование файлов"
    echo "3) Только развертывание (файлы уже на сервере)"
    echo "4) Только настройка .env"
    echo "5) Проверка развертывания"
    echo "6) Выход"
    echo
    read -p "Выберите вариант (1-6): " choice
    
    case $choice in
        1)
            log_info "Запуск полной миграции..."
            check_ssh
            copy_files
            deploy_on_server
            configure_env
            start_service
            verify_deployment
            ;;
        2)
            check_ssh
            copy_files
            ;;
        3)
            check_ssh
            deploy_on_server
            ;;
        4)
            check_ssh
            configure_env
            ;;
        5)
            check_ssh
            verify_deployment
            ;;
        6)
            exit 0
            ;;
        *)
            log_error "Неверный выбор"
            exit 1
            ;;
    esac
}

# Основная функция
main() {
    if [ -z "$SERVER" ]; then
        interactive_menu
    else
        check_params
        log_info "Запуск автоматической миграции на $SERVER"
        check_ssh
        copy_files
        deploy_on_server
        configure_env
        start_service
        verify_deployment
    fi
    
    log_success "Миграция завершена!"
    echo
    echo "🎯 Полезные команды на сервере:"
    echo "  systemctl status parser-bot    # Статус сервиса"
    echo "  parser-bot logs               # Логи"
    echo "  parser-bot status             # Статус контейнера"
    echo "  parser-bot update             # Обновление"
    echo
    echo "📖 SSH подключение:"
    echo "  ssh $SERVER"
}

# Запуск
main "$@" 
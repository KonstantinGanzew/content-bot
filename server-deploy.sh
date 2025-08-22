#!/bin/bash

# Parser Bot - Автоматическое развертывание на сервере
# Использование: bash server-deploy.sh

set -e

echo "🚀 Parser Bot - Развертывание на сервере"
echo "========================================"

# Переменные
APP_NAME="parser-bot"
APP_DIR="/opt/$APP_NAME"
APP_USER="parser-bot"
SERVICE_NAME="parser-bot"

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка прав root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Этот скрипт должен запускаться от root"
        log_info "Выполните: sudo bash server-deploy.sh"
        exit 1
    fi
}

# Установка Docker и Docker Compose
install_docker() {
    log_info "Установка Docker..."
    
    if command -v docker >/dev/null 2>&1; then
        log_success "Docker уже установлен: $(docker --version)"
    else
        # Обновляем пакеты
        apt-get update
        apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
        
        # Добавляем официальный GPG ключ Docker
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        
        # Добавляем репозиторий Docker
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Устанавливаем Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
        # Запускаем Docker
        systemctl start docker
        systemctl enable docker
        
        log_success "Docker установлен: $(docker --version)"
    fi
    
    # Проверяем Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        log_success "Docker Compose уже установлен: $(docker-compose --version)"
    else
        log_info "Установка Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        log_success "Docker Compose установлен: $(docker-compose --version)"
    fi
}

# Создание пользователя приложения
create_app_user() {
    log_info "Создание пользователя приложения..."
    
    if id "$APP_USER" &>/dev/null; then
        log_success "Пользователь $APP_USER уже существует"
    else
        useradd -r -s /bin/false -d "$APP_DIR" "$APP_USER"
        usermod -aG docker "$APP_USER"
        log_success "Пользователь $APP_USER создан"
    fi
}

# Создание структуры директорий
create_directories() {
    log_info "Создание директорий..."
    
    mkdir -p "$APP_DIR"
    mkdir -p "$APP_DIR/logs"
    mkdir -p "$APP_DIR/data" 
    mkdir -p "$APP_DIR/downloaded_images"
    mkdir -p "/var/log/$APP_NAME"
    
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    chown -R "$APP_USER:$APP_USER" "/var/log/$APP_NAME"
    
    log_success "Директории созданы"
}

# Копирование файлов конфигурации
copy_config_files() {
    log_info "Копирование файлов конфигурации..."
    
    # Создаем минимальный docker-compose.yml
    cat > "$APP_DIR/docker-compose.yml" << 'EOF'
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
      - /var/log/parser-bot:/app/logs
    
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

    # Создаем пример .env файла
    cat > "$APP_DIR/.env.example" << 'EOF'
# Обязательные настройки
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here

# Режим работы
BOT_MODE=scheduler
PARSER_INTERVAL=300

# Логирование
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Медиа файлы
SAVE_IMAGES=true
AUTO_CLEANUP_ENABLED=true
FILES_KEEP_HOURS=48

# Reddit парсер
REDDIT_SUBREDDIT=KafkaFPS
REDDIT_USE_JSON_API=true
REDDIT_REQUEST_DELAY=3
EOF

    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    log_success "Файлы конфигурации созданы"
}

# Создание systemd сервиса
create_systemd_service() {
    log_info "Создание systemd сервиса..."
    
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Parser Bot - Telegram Bot for Parsing Reddit and JoyReactor
After=docker.service
Requires=docker.service

[Service]
Type=forking
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart
TimeoutStartSec=300
User=$APP_USER
Group=$APP_USER

# Restart policy
Restart=always
RestartSec=30

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR /var/log/$APP_NAME

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    log_success "Systemd сервис создан"
}

# Установка дополнительных утилит
install_utilities() {
    log_info "Установка дополнительных утилит..."
    
    apt-get update
    apt-get install -y \
        htop \
        ncdu \
        wget \
        curl \
        unzip \
        logrotate \
        cron
    
    log_success "Утилиты установлены"
}

# Настройка logrotate
setup_logrotate() {
    log_info "Настройка ротации логов..."
    
    cat > "/etc/logrotate.d/$APP_NAME" << EOF
/var/log/$APP_NAME/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    create 644 $APP_USER $APP_USER
}
EOF

    log_success "Ротация логов настроена"
}

# Создание управляющих скриптов
create_management_scripts() {
    log_info "Создание управляющих скриптов..."
    
    # Скрипт управления
    cat > "$APP_DIR/manage.sh" << 'EOF'
#!/bin/bash

APP_NAME="parser-bot"

case "$1" in
    start)
        echo "🚀 Запуск Parser Bot..."
        docker-compose up -d
        ;;
    stop)
        echo "🛑 Остановка Parser Bot..."
        docker-compose down
        ;;
    restart)
        echo "🔄 Перезапуск Parser Bot..."
        docker-compose restart
        ;;
    status)
        echo "📊 Статус Parser Bot..."
        docker-compose ps
        ;;
    logs)
        echo "📋 Логи Parser Bot..."
        docker-compose logs -f --tail=100
        ;;
    update)
        echo "🔄 Обновление Parser Bot..."
        docker-compose pull
        docker-compose up -d
        ;;
    cleanup)
        echo "🗑️ Очистка старых файлов..."
        docker-compose exec parser-bot python cleanup_files.py --cleanup
        ;;
    backup)
        echo "💾 Создание резервной копии..."
        tar -czf "/tmp/parser-bot-backup-$(date +%Y%m%d-%H%M%S).tar.gz" \
            ./data ./downloaded_images ./logs ./.env
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update|cleanup|backup}"
        exit 1
        ;;
esac
EOF

    chmod +x "$APP_DIR/manage.sh"
    
    # Символическая ссылка для глобального доступа
    ln -sf "$APP_DIR/manage.sh" "/usr/local/bin/parser-bot"
    
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    log_success "Управляющие скрипты созданы"
}

# Основная функция развертывания
main() {
    log_info "Начало развертывания Parser Bot на сервере..."
    
    check_root
    install_docker
    create_app_user  
    create_directories
    copy_config_files
    create_systemd_service
    install_utilities
    setup_logrotate
    create_management_scripts
    
    log_success "Развертывание завершено!"
    echo
    echo "📋 Следующие шаги:"
    echo "1. Отредактируйте файл: $APP_DIR/.env"
    echo "   cp $APP_DIR/.env.example $APP_DIR/.env"
    echo "   nano $APP_DIR/.env"
    echo
    echo "2. Запустите сервис:"
    echo "   systemctl enable $SERVICE_NAME"
    echo "   systemctl start $SERVICE_NAME"
    echo
    echo "3. Проверьте статус:"
    echo "   systemctl status $SERVICE_NAME"
    echo "   parser-bot logs"
    echo
    echo "🎯 Управление сервисом:"
    echo "   parser-bot start|stop|restart|status|logs|update|cleanup|backup"
}

# Запуск
main "$@" 
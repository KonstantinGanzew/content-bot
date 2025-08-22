#!/bin/bash

# Parser Bot - Скрипт мониторинга на сервере
# Использование: bash server-monitor.sh

# Переменные
APP_NAME="parser-bot"
APP_DIR="/opt/$APP_NAME"

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Проверка статуса systemd сервиса
check_systemd_service() {
    echo "=== SYSTEMD СЕРВИС ==="
    if systemctl is-active --quiet $APP_NAME; then
        log_success "Сервис $APP_NAME активен"
        systemctl status $APP_NAME --no-pager --lines=5
    else
        log_error "Сервис $APP_NAME не активен"
        systemctl status $APP_NAME --no-pager --lines=10
    fi
    echo
}

# Проверка Docker контейнера
check_docker_container() {
    echo "=== DOCKER КОНТЕЙНЕР ==="
    if docker ps | grep -q $APP_NAME; then
        log_success "Контейнер $APP_NAME работает"
        docker ps --filter "name=$APP_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo
        
        # Статистика ресурсов
        echo "Использование ресурсов:"
        docker stats $APP_NAME --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    else
        log_error "Контейнер $APP_NAME не работает"
        echo "Все контейнеры:"
        docker ps -a --filter "name=$APP_NAME"
    fi
    echo
}

# Проверка логов
check_logs() {
    echo "=== ПОСЛЕДНИЕ ЛОГИ ==="
    if docker ps | grep -q $APP_NAME; then
        log_info "Последние 20 строк логов:"
        docker logs $APP_NAME --tail=20 --timestamps
    else
        log_warning "Контейнер не запущен, показываю логи systemd:"
        journalctl -u $APP_NAME -n 20 --no-pager
    fi
    echo
}

# Проверка дискового пространства
check_disk_space() {
    echo "=== ДИСКОВОЕ ПРОСТРАНСТВО ==="
    
    # Общее место на диске
    echo "Общая информация о дисках:"
    df -h | grep -E "(Filesystem|/dev/)"
    echo
    
    # Место в директории приложения
    if [ -d "$APP_DIR" ]; then
        echo "Использование в $APP_DIR:"
        du -sh "$APP_DIR"/* 2>/dev/null | sort -hr || echo "Директория пуста"
        
        # Детализация медиа файлов
        if [ -d "$APP_DIR/downloaded_images" ]; then
            images_count=$(find "$APP_DIR/downloaded_images" -type f 2>/dev/null | wc -l)
            images_size=$(du -sh "$APP_DIR/downloaded_images" 2>/dev/null | cut -f1)
            echo "Медиа файлов: $images_count ($images_size)"
        fi
        
        # Детализация логов
        if [ -d "$APP_DIR/logs" ]; then
            logs_size=$(du -sh "$APP_DIR/logs" 2>/dev/null | cut -f1)
            echo "Логи: $logs_size"
        fi
    else
        log_warning "Директория $APP_DIR не найдена"
    fi
    echo
}

# Проверка сетевых соединений
check_network() {
    echo "=== СЕТЕВЫЕ СОЕДИНЕНИЯ ==="
    
    # Проверка соединения с Telegram API
    echo -n "Telegram API: "
    if curl -s --max-time 5 https://api.telegram.org/bot > /dev/null 2>&1; then
        log_success "Доступен"
    else
        log_error "Недоступен"
    fi
    
    # Проверка соединения с Reddit
    echo -n "Reddit API: "
    if curl -s --max-time 5 https://www.reddit.com/.json > /dev/null 2>&1; then
        log_success "Доступен"
    else
        log_error "Недоступен"
    fi
    
    # Проверка Docker Hub
    echo -n "Docker Hub: "
    if curl -s --max-time 5 https://registry-1.docker.io/v2/ > /dev/null 2>&1; then
        log_success "Доступен"
    else
        log_warning "Недоступен (не критично)"
    fi
    echo
}

# Проверка системных ресурсов
check_system_resources() {
    echo "=== СИСТЕМНЫЕ РЕСУРСЫ ==="
    
    # Использование CPU
    echo "CPU:"
    top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "Использование: " (100 - $1) "%"}'
    
    # Использование памяти
    echo "Память:"
    free -h | awk 'NR==2{printf "Использовано: %s/%s (%.1f%%)\n", $3, $2, ($3/$2)*100}'
    
    # Load average
    echo "Load average:"
    uptime | awk -F'load average:' '{print $2}'
    
    # Uptime
    echo "Uptime:"
    uptime -p
    echo
}

# Проверка конфигурации
check_configuration() {
    echo "=== КОНФИГУРАЦИЯ ==="
    
    # Проверка .env файла
    if [ -f "$APP_DIR/.env" ]; then
        log_success ".env файл существует"
        
        # Проверяем ключевые переменные (без показа значений)
        if grep -q "TELEGRAM_BOT_TOKEN=" "$APP_DIR/.env"; then
            echo "✅ TELEGRAM_BOT_TOKEN настроен"
        else
            log_error "TELEGRAM_BOT_TOKEN не настроен"
        fi
        
        if grep -q "TELEGRAM_CHANNEL_ID=" "$APP_DIR/.env"; then
            echo "✅ TELEGRAM_CHANNEL_ID настроен"
        else
            log_error "TELEGRAM_CHANNEL_ID не настроен"
        fi
        
        # Показываем режим работы
        bot_mode=$(grep "BOT_MODE=" "$APP_DIR/.env" | cut -d'=' -f2)
        echo "Режим работы: ${bot_mode:-scheduler}"
        
        # Показываем интервал парсинга
        interval=$(grep "PARSER_INTERVAL=" "$APP_DIR/.env" | cut -d'=' -f2)
        echo "Интервал парсинга: ${interval:-300} секунд"
    else
        log_error ".env файл не найден в $APP_DIR"
    fi
    
    # Проверка docker-compose.yml
    if [ -f "$APP_DIR/docker-compose.yml" ]; then
        log_success "docker-compose.yml существует"
    else
        log_error "docker-compose.yml не найден"
    fi
    echo
}

# Здоровье приложения
check_health() {
    echo "=== ЗДОРОВЬЕ ПРИЛОЖЕНИЯ ==="
    
    if docker ps | grep -q $APP_NAME; then
        # Проверяем health check
        health=$(docker inspect $APP_NAME --format='{{.State.Health.Status}}' 2>/dev/null)
        if [ "$health" = "healthy" ]; then
            log_success "Контейнер здоров"
        elif [ "$health" = "unhealthy" ]; then
            log_error "Контейнер нездоров"
        else
            log_warning "Health check не настроен или недоступен"
        fi
        
        # Проверяем время запуска
        started=$(docker inspect $APP_NAME --format='{{.State.StartedAt}}' 2>/dev/null)
        if [ -n "$started" ]; then
            echo "Запущен: $started"
        fi
        
        # Проверяем количество перезапусков
        restart_count=$(docker inspect $APP_NAME --format='{{.RestartCount}}' 2>/dev/null)
        echo "Перезапусков: ${restart_count:-0}"
    else
        log_error "Контейнер не запущен"
    fi
    echo
}

# Автоматические проверки и уведомления
check_alerts() {
    echo "=== ПРЕДУПРЕЖДЕНИЯ ==="
    
    alerts=0
    
    # Проверяем место на диске (< 1GB)
    available_space=$(df /opt | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 1048576 ]; then  # < 1GB в KB
        log_warning "Мало места на диске: $(($available_space / 1024))MB осталось"
        alerts=$((alerts + 1))
    fi
    
    # Проверяем использование памяти (> 90%)
    memory_usage=$(free | grep Mem | awk '{printf "%.0f", ($3/$2)*100}')
    if [ "$memory_usage" -gt 90 ]; then
        log_warning "Высокое использование памяти: ${memory_usage}%"
        alerts=$((alerts + 1))
    fi
    
    # Проверяем количество файлов (> 10000)
    if [ -d "$APP_DIR/downloaded_images" ]; then
        file_count=$(find "$APP_DIR/downloaded_images" -type f 2>/dev/null | wc -l)
        if [ "$file_count" -gt 10000 ]; then
            log_warning "Много медиа файлов: $file_count (рекомендуется очистка)"
            alerts=$((alerts + 1))
        fi
    fi
    
    # Проверяем статус сервиса
    if ! systemctl is-active --quiet $APP_NAME; then
        log_error "Сервис не активен!"
        alerts=$((alerts + 1))
    fi
    
    # Проверяем статус контейнера
    if ! docker ps | grep -q $APP_NAME; then
        log_error "Контейнер не запущен!"
        alerts=$((alerts + 1))
    fi
    
    if [ $alerts -eq 0 ]; then
        log_success "Предупреждений нет"
    else
        echo "Найдено предупреждений: $alerts"
    fi
    echo
}

# Быстрые команды для исправления проблем
show_quick_fixes() {
    echo "=== БЫСТРЫЕ ИСПРАВЛЕНИЯ ==="
    echo "Перезапуск сервиса:        systemctl restart $APP_NAME"
    echo "Перезапуск контейнера:     docker-compose restart"
    echo "Просмотр логов:            parser-bot logs"
    echo "Обновление образа:         parser-bot update"
    echo "Очистка файлов:            parser-bot cleanup"
    echo "Очистка Docker:            docker system prune -f"
    echo "Проверка конфигурации:     docker-compose config"
    echo
}

# Основная функция мониторинга
main_monitor() {
    echo "🔍 Parser Bot - Мониторинг системы"
    echo "==================================="
    echo "Время: $(date)"
    echo
    
    check_systemd_service
    check_docker_container
    check_system_resources
    check_disk_space
    check_network
    check_configuration
    check_health
    check_alerts
    
    if [ "$1" = "--logs" ]; then
        check_logs
    fi
    
    if [ "$1" = "--help" ]; then
        show_quick_fixes
    fi
    
    echo "Мониторинг завершен: $(date)"
}

# Интерактивный режим
interactive_monitor() {
    while true; do
        clear
        main_monitor
        echo
        echo "Нажмите Enter для обновления, 'q' для выхода, 'l' для логов..."
        read -n 1 -t 30 key
        
        case $key in
            'q'|'Q')
                echo "Выход из мониторинга"
                break
                ;;
            'l'|'L')
                clear
                check_logs
                echo "Нажмите Enter для возврата..."
                read
                ;;
            '')
                continue
                ;;
        esac
    done
}

# Определяем режим работы
case "$1" in
    "--interactive"|"-i")
        interactive_monitor
        ;;
    "--logs"|"-l")
        main_monitor --logs
        ;;
    "--help"|"-h")
        echo "Использование: $0 [опции]"
        echo "  --interactive, -i    Интерактивный режим"
        echo "  --logs, -l          Показать логи"
        echo "  --help, -h          Эта справка"
        echo
        show_quick_fixes
        ;;
    *)
        main_monitor
        ;;
esac 
# Makefile для управления Parser Bot Docker контейнерами

# Переменные
IMAGE_NAME = kureed/parser-bot
CONTAINER_NAME = parser-bot
DOCKER_COMPOSE_FILE = docker-compose.yml
DOCKER_BUILD_FILE = docker-compose.build.yml

# Цели по умолчанию
.PHONY: help build up down logs clean restart status test shell

# Помощь
help:
	@echo "🐳 Parser Bot Docker Management"
	@echo "================================"
	@echo ""
	@echo "📦 Сборка и запуск:"
	@echo "  make build        - Собрать Docker образ"
	@echo "  make up           - Запустить сервисы"
	@echo "  make down         - Остановить сервисы"
	@echo "  make restart      - Перезапустить сервисы"
	@echo ""
	@echo "📊 Мониторинг:"
	@echo "  make logs         - Показать логи"
	@echo "  make status       - Показать статус контейнеров"
	@echo "  make stats        - Показать статистику ресурсов"
	@echo ""
	@echo "🔧 Разработка:"
	@echo "  make shell        - Зайти в контейнер"
	@echo "  make test         - Запустить тесты"
	@echo "  make cleanup      - Запустить очистку файлов"
	@echo ""
	@echo "🗑️ Очистка:"
	@echo "  make clean        - Удалить контейнеры и образы"
	@echo "  make clean-all    - Полная очистка (volumes, networks)"

# Сборка образа
build:
	@echo "🔨 Сборка Docker образа..."
	docker-compose -f $(DOCKER_BUILD_FILE) build
	@echo "✅ Образ собран успешно!"

# Сборка без кеша
build-no-cache:
	@echo "🔨 Сборка Docker образа (без кеша)..."
	docker-compose -f $(DOCKER_BUILD_FILE) build --no-cache
	@echo "✅ Образ собран успешно!"

# Запуск сервисов
up:
	@echo "🚀 Запуск сервисов..."
	@if [ ! -f ".env" ]; then \
		echo "❌ ОШИБКА: Файл .env не найден!"; \
		echo "💡 Сначала выполните: make setup-volumes && cp env.example .env"; \
		echo "💡 Затем отредактируйте .env файл с вашими настройками"; \
		exit 1; \
	fi
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d
	@echo "✅ Сервисы запущены!"
	@make status

# Запуск в foreground режиме
up-fg:
	@echo "🚀 Запуск сервисов (foreground)..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) up

# Остановка сервисов
down:
	@echo "🛑 Остановка сервисов..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down
	@echo "✅ Сервисы остановлены!"

# Перезапуск сервисов
restart:
	@echo "🔄 Перезапуск сервисов..."
	@if [ ! -f ".env" ]; then \
		echo "❌ ОШИБКА: Файл .env не найден!"; \
		echo "💡 Сначала выполните: make setup-volumes && cp env.example .env"; \
		exit 1; \
	fi
	docker-compose -f $(DOCKER_COMPOSE_FILE) restart
	@echo "✅ Сервисы перезапущены!"
	@make status

# Просмотр логов
logs:
	@echo "📋 Логи сервисов:"
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f --tail=100

# Логи только основного сервиса
logs-bot:
	@echo "📋 Логи Parser Bot:"
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f --tail=100 parser-bot

# Статус контейнеров
status:
	@echo "📊 Статус контейнеров:"
	@docker-compose -f $(DOCKER_COMPOSE_FILE) ps
	@echo ""
	@echo "🔍 Детальная информация:"
	@docker ps --filter "name=$(CONTAINER_NAME)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Size}}"

# Статистика ресурсов
stats:
	@echo "📊 Статистика использования ресурсов:"
	docker stats $(CONTAINER_NAME) --no-stream

# Зайти в контейнер
shell:
	@echo "🐚 Вход в контейнер..."
	docker exec -it $(CONTAINER_NAME) /bin/bash

# Зайти в контейнер как root
shell-root:
	@echo "🐚 Вход в контейнер (root)..."
	docker exec -it --user root $(CONTAINER_NAME) /bin/bash

# Запустить тесты
test:
	@echo "🧪 Запуск тестов..."
	docker run --rm \
		-e BOT_MODE=test \
		-e TELEGRAM_BOT_TOKEN=test_token \
		-e TELEGRAM_CHANNEL_ID=-100123456789 \
		$(IMAGE_NAME)

# Запустить очистку файлов
cleanup:
	@echo "🗑️ Запуск очистки файлов..."
	docker exec $(CONTAINER_NAME) python cleanup_files.py --cleanup

# Показать статистику медиа файлов
media-stats:
	@echo "📊 Статистика медиа файлов:"
	docker exec $(CONTAINER_NAME) python cleanup_files.py --stats

# Создать директории для volumes
setup-volumes:
	@echo "📁 Создание директорий для volumes..."
	mkdir -p ./docker-volumes/images
	mkdir -p ./docker-volumes/logs  
	mkdir -p ./docker-volumes/data
	@if [ ! -f ".env" ]; then \
		echo "📝 Создание .env файла из шаблона..."; \
		cp env.example .env; \
		echo "⚠️  ВАЖНО: Отредактируйте .env файл с вашими настройками!"; \
		echo "   - TELEGRAM_BOT_TOKEN"; \
		echo "   - TELEGRAM_CHANNEL_ID"; \
	else \
		echo "✅ Файл .env уже существует"; \
	fi
	@echo "✅ Настройка завершена!"

# Очистка контейнеров и образов
clean:
	@echo "🗑️ Очистка контейнеров и образов..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down --rmi all
	docker image prune -f
	@echo "✅ Очистка завершена!"

# Полная очистка (включая volumes и networks)
clean-all:
	@echo "🗑️ Полная очистка..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down --rmi all --volumes --remove-orphans
	docker system prune -f --volumes
	@echo "✅ Полная очистка завершена!"

# Показать размер образа
image-size:
	@echo "📦 Размер Docker образа:"
	@docker images $(IMAGE_NAME) --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"

# Экспорт логов
export-logs:
	@echo "📤 Экспорт логов..."
	@mkdir -p ./exported-logs
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs --no-color > ./exported-logs/docker-logs-$(shell date +%Y%m%d-%H%M%S).log
	@echo "✅ Логи экспортированы в ./exported-logs/"

# Резервное копирование данных
backup:
	@echo "💾 Создание резервной копии..."
	@mkdir -p ./backups
	tar -czf ./backups/parser-bot-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz ./docker-volumes/
	@echo "✅ Резервная копия создана в ./backups/"

# Обновление образа
update:
	@echo "🔄 Обновление образа..."
	@make down
	@make build-no-cache
	@make up
	@echo "✅ Обновление завершено!"

# Быстрый старт (первичная настройка)
quickstart:
	@echo "🚀 Быстрый старт Parser Bot..."
	@make setup-volumes
	@make build
	@echo ""
	@echo "⚠️  ВАЖНО: Отредактируйте .env файл!"
	@echo "1. Заполните TELEGRAM_BOT_TOKEN"
	@echo "2. Заполните TELEGRAM_CHANNEL_ID"  
	@echo "3. Запустите: make up"
	@echo ""

# По умолчанию показываем help
.DEFAULT_GOAL := help 
# Используем официальный образ Python
FROM python:3.11-slim

# Метаданные
LABEL maintainer="Parser Bot"
LABEL description="Telegram bot для парсинга Reddit и JoyReactor"
LABEL version="1.0"

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Создаем необходимые директории
RUN mkdir -p \
    /app/downloaded_images \
    /app/logs \
    /app/data \
    /app/config \
    && chown -R botuser:botuser /app

# Копируем код приложения
COPY --chown=botuser:botuser . .

# Копируем и настраиваем entrypoint скрипт
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh && chown botuser:botuser /app/docker-entrypoint.sh

# Переключаемся на непривилегированного пользователя
USER botuser

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Открываем порт (если нужен для веб-интерфейса в будущем)
EXPOSE 8000

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Создаем volume для данных
VOLUME ["/app/downloaded_images", "/app/logs", "/app/data"]

# Точка входа через entrypoint скрипт
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD [] 
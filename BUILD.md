# 🔨 Сборка Parser Bot Docker образа

## Быстрая сборка

### Windows
```bash
docker.bat build
```

### Linux/Mac  
```bash
make build
```

## Альтернативные способы

### Прямая сборка через Docker
```bash
docker build -t parser-bot:latest .
```

### Сборка через Docker Compose
```bash
docker-compose -f docker-compose.build.yml build
```

### Сборка без кеша
```bash
# Windows
docker.bat build --no-cache

# Linux/Mac
make build-no-cache

# Прямо
docker build --no-cache -t parser-bot:latest .
```

## Проверка образа

```bash
# Просмотр образов
docker images parser-bot

# Информация об образе
docker inspect parser-bot:latest

# Тестовый запуск
docker run --rm parser-bot:latest
```

## Размер образа

Оптимизированный образ занимает приблизительно:
- **Базовый размер**: ~150-200 MB
- **С зависимостями**: ~250-300 MB

## Экспорт/Импорт образа

### Экспорт образа в файл
```bash
docker save parser-bot:latest > parser-bot.tar
```

### Импорт образа из файла
```bash
docker load < parser-bot.tar
```

## Отправка в реестр

### Docker Hub
```bash
# Тегирование
docker tag parser-bot:latest username/parser-bot:latest

# Отправка
docker push username/parser-bot:latest
```

### Приватный реестр
```bash
# Тегирование
docker tag parser-bot:latest registry.example.com/parser-bot:latest

# Отправка  
docker push registry.example.com/parser-bot:latest
``` 
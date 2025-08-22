# 🔐 SSH пароли - Полное руководство

Подробное руководство по работе с SSH паролями при миграции Parser Bot на сервер.

## 🚨 **Проблема: "Не удается подключиться к серверу"**

### **Симптомы:**
```
❌ Не удается подключиться к серверу
ℹ️  Убедитесь что:
ℹ️  1. Сервер доступен по сети
ℹ️  2. SSH ключи настроены или введите пароль  
ℹ️  3. Пользователь имеет права доступа
```

### **Решение:**

## 🔧 **Способ 1: Использование специального скрипта (самый простой)**

```bash
# Используйте скрипт с поддержкой паролей
bash server-migrate-password.sh user@your-server.com

# Вы увидите запросы пароля:
# ⚠️  Введите пароль для SSH подключения:
# user@your-server.com's password: [введите пароль]
```

### **Что делает этот скрипт:**
- ✅ Принудительно запрашивает пароль при каждом подключении
- ✅ Отключает проверку SSH ключей  
- ✅ Показывает понятные сообщения когда нужен пароль
- ✅ Выполняет полную миграцию с паролем

## 🔑 **Способ 2: Настройка SSH ключей (рекомендуется)**

### **Шаг 1: Создание SSH ключа**
```bash
# Генерируем новый SSH ключ (если его нет)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Нажмите Enter для всех вопросов (стандартные настройки)
# Ключ сохранится в ~/.ssh/id_rsa
```

### **Шаг 2: Копирование ключа на сервер**
```bash
# Автоматическое копирование (введите пароль в последний раз)
ssh-copy-id user@your-server.com

# Если ssh-copy-id недоступен:
cat ~/.ssh/id_rsa.pub | ssh user@your-server.com "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### **Шаг 3: Проверка**
```bash
# Теперь подключение должно работать без пароля
ssh user@your-server.com
exit

# Запускаем обычную миграцию
bash server-migrate.sh user@your-server.com
```

## 🧪 **Способ 3: Тестирование подключения**

### **Проверьте базовое подключение:**
```bash
# Простое подключение
ssh user@your-server.com
# Если работает - выходим и запускаем миграцию
exit

# Принудительный запрос пароля
ssh -o PasswordAuthentication=yes -o PubkeyAuthentication=no user@your-server.com

# Подключение с таймаутом
ssh -o ConnectTimeout=10 user@your-server.com
```

### **Диагностика проблем:**
```bash
# Подробная диагностика SSH
ssh -vvv user@your-server.com

# Проверка доступности сервера
ping your-server.com

# Проверка порта SSH (обычно 22)
telnet your-server.com 22
# или
nmap -p 22 your-server.com
```

## 📝 **Способ 4: Пошаговая миграция**

Если автоматическая миграция не работает, выполните вручную:

### **Шаг 1: Копирование файлов**
```bash
# Скопируйте скрипт развертывания
scp server-deploy.sh user@your-server.com:/tmp/

# Скопируйте документацию
scp SERVER_README.md user@your-server.com:/tmp/
scp env.example user@your-server.com:/tmp/.env.example
```

### **Шаг 2: Подключение к серверу**
```bash
# Подключитесь к серверу
ssh user@your-server.com

# Проверьте что файлы скопированы
ls -la /tmp/server-deploy.sh
```

### **Шаг 3: Развертывание**
```bash
# На сервере выполните:
chmod +x /tmp/server-deploy.sh
sudo /tmp/server-deploy.sh
```

### **Шаг 4: Настройка**
```bash
# Настройте .env файл
sudo cp /opt/parser-bot/.env.example /opt/parser-bot/.env
sudo nano /opt/parser-bot/.env

# Заполните:
# TELEGRAM_BOT_TOKEN=ваш_токен
# TELEGRAM_CHANNEL_ID=ваш_канал_id
```

### **Шаг 5: Запуск**
```bash
# Запустите сервис
sudo systemctl enable parser-bot
sudo systemctl start parser-bot

# Проверьте статус
systemctl status parser-bot
```

## ⚡ **Быстрое решение проблем**

### **Проблема: Permission denied (publickey)**
```bash
# Решение: принудительный запрос пароля
ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no user@your-server.com
```

### **Проблема: Connection timed out**
```bash
# Проверьте сеть и порт
ping your-server.com
nmap -p 22 your-server.com

# Попробуйте другой порт SSH (если настроен)
ssh -p 2222 user@your-server.com
```

### **Проблема: Host key verification failed**
```bash
# Очистите старые ключи хоста
ssh-keygen -R your-server.com

# Или отключите проверку (небезопасно)
ssh -o StrictHostKeyChecking=no user@your-server.com
```

### **Проблема: Too many authentication failures**
```bash
# Ограничьте попытки аутентификации
ssh -o IdentitiesOnly=yes user@your-server.com
```

## 🔒 **Безопасность паролей**

### **Рекомендации:**
- 🚫 **Не используйте** простые пароли
- ✅ **Используйте** сильные пароли (12+ символов)
- ✅ **Настройте** SSH ключи после первого подключения
- ✅ **Отключите** парольную аутентификацию после настройки ключей

### **Сильный пароль:**
```
# Хорошие примеры:
MyServer#2024!Strong
Parse_Bot_Secure_123$
Deploy2024#SafePassword!

# Плохие примеры:
123456
password
admin
qwerty
```

## 📞 **Поддержка**

### **Не получается подключиться?**

1. **Проверьте основы:**
   ```bash
   ping your-server.com      # Сервер доступен?
   nmap -p 22 your-server.com # SSH порт открыт?
   ssh -v user@your-server.com # Подробная диагностика
   ```

2. **Попробуйте альтернативы:**
   ```bash
   # Другой порт SSH
   ssh -p 2222 user@your-server.com
   
   # Без проверки ключей
   ssh -o StrictHostKeyChecking=no user@your-server.com
   
   # Только пароль
   ssh -o PreferredAuthentications=password user@your-server.com
   ```

3. **Используйте пошаговую миграцию:**
   - Скопируйте файлы вручную
   - Подключитесь к серверу отдельно
   - Выполните развертывание на сервере

### **Все еще проблемы?**

Создайте диагностический отчет:
```bash
{
    echo "=== Network Test ==="
    ping -c 4 your-server.com
    echo "=== SSH Port Test ==="
    nmap -p 22 your-server.com
    echo "=== SSH Debug ==="
    ssh -vvv -o ConnectTimeout=10 user@your-server.com
} > ssh-debug.log 2>&1
```

Отправьте файл `ssh-debug.log` для анализа проблемы.

## ✅ **Проверочный список**

После успешного подключения:

- [ ] ✅ SSH подключение работает: `ssh user@your-server.com`
- [ ] ✅ Файлы скопированы на сервер
- [ ] ✅ Развертывание выполнено: `sudo /tmp/server-deploy.sh`
- [ ] ✅ .env файл настроен: `sudo nano /opt/parser-bot/.env`
- [ ] ✅ Сервис запущен: `systemctl status parser-bot`
- [ ] ✅ Контейнер работает: `docker ps | grep parser-bot`
- [ ] ✅ Логи без ошибок: `parser-bot logs`

**🎉 Миграция завершена успешно!** 
# 🚀 Руководство по настройке WinRM

## 📋 Обзор

WinRM (Windows Remote Management) необходим для выполнения PowerShell команд на Windows сервере из нашего Linux приложения. Это позволяет полностью имитировать работу оригинальных PowerShell скриптов.

**Примечание**: WinRM уже настроен на Windows сервере, поэтому настройка сервера не требуется.

## 🔧 Настройка приложения

### 1. Установка зависимостей

```bash
# Установка pywinrm
poetry add pywinrm

# Или через pip
pip install pywinrm
```

### 2. Настройка переменных окружения

В файле `.env`:

```env
# Настройки WinRM (использует тот же сервер что и AD)
WINRM_SERVER=dc.central.st-ing.com
WINRM_PORT=5985

# Настройки Exchange
EXCHANGE_SERVER=dc.central.st-ing.com
EXCHANGE_DATABASE=Mailbox Database

# Настройки SMTP
SMTP_SERVER=smtp.st-ing.com
SMTP_PORT=587
SMTP_USERNAME=noreply@st-ing.com
SMTP_PASSWORD=your_password
```

## 🔧 Тестирование

### Запуск теста WinRM

```bash
# Тестирование подключения
python test_winrm.py
```

### Проверка в приложении

```bash
# Пересборка Docker
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f app
```

## 🔍 Диагностика проблем

### Проблема: "Connection refused"

**Решение:**
1. Проверьте сетевую доступность к Windows серверу
2. Убедитесь, что WinRM работает на сервере

```bash
# Проверка доступности
telnet dc.central.st-ing.com 5985
```

### Проблема: "Authentication failed"

**Решение:**
1. Проверьте учетные данные в `.env`
2. Убедитесь, что пользователь имеет права администратора
3. Проверьте домен

### Проблема: "Access denied"

**Решение:**
1. Проверьте, что учетные данные корректны
2. Убедитесь в правах доступа пользователя

## 📊 Мониторинг

### Проверка статуса WinRM:

```bash
# Тест подключения
python test_winrm.py
```

## 🚀 Готовые команды

### Проверка настройки:

```bash
# В Linux контейнере
python test_winrm.py
```

## ✅ Чек-лист готовности

- [ ] pywinrm установлен в приложении
- [ ] Переменные окружения настроены
- [ ] Тест подключения прошел успешно
- [ ] Docker пересобран
- [ ] Приложение запущено без ошибок

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи приложения: `docker-compose logs -f app`
2. Запустите тест: `python test_winrm.py`
3. Убедитесь в сетевой доступности к Windows серверу
4. Проверьте учетные данные в `.env`

---

**После выполнения всех шагов ваше приложение будет полностью функционально и идентично PowerShell скриптам!** 🎉

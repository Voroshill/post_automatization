# 🔧 Настройка переменных окружения

## 📋 Обзор

Файл `.env` содержит все настройки приложения. Скопируйте `.env.example` в `.env` и настройте параметры под вашу среду.

## 🗂️ Структура файла .env

```bash
# Основные настройки приложения
DOMAIN=user-management.yourdomain.com
API_BASE_URL=https://user-management.yourdomain.com/api
DATABASE_URL=sqlite:///./data/users.db

# Настройки логирования
LOG_FILE=logs/application.log
LOG_MAX_SIZE_MB=10
LOG_MAX_FILES=5
LOG_LEVEL=INFO

# Настройки пагинации
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

# Настройки экспорта
EXPORT_MAX_RECORDS=10000

# Настройки CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Настройки 1C интеграции
ONEC_ALLOWED_ORIGINS=http://localhost:8080,http://your-1c-server.com

# Аутентификация веб-приложения
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
DEFAULT_USER_PASSWORD=User123456

# Настройки Active Directory
AD_DOMAIN=central
AD_SERVER=dc.central.st-ing.com
LDAP_SEARCH_BASE=DC=central,DC=st-ing,DC=com
LDAP_USER_OU=OU=Users,DC=central,DC=st-ing,DC=com
LDAP_DISMISSED_OU=OU=Уволенные сотрудники,DC=central,DC=st-ing,DC=com

# Настройки Exchange
EXCHANGE_SERVER=mailzone.central.st-ing.com
EXCHANGE_DATABASE=STI_Mailbox

# Настройки SMTP
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=noreply@st-ing.com
SMTP_PASSWORD=your-smtp-password

# Настройки WinRM
WINRM_SERVER=dc.central.st-ing.com
WINRM_PORT=5985
```

## 🔍 Подробное описание параметров

### 🌐 Основные настройки

| **Параметр** | **Описание** | **Пример** | **Обязательный** |
|---|---|---|---|
| `DOMAIN` | Домен приложения | `user-management.yourdomain.com` | ✅ |
| `API_BASE_URL` | Базовый URL API | `https://user-management.yourdomain.com/api` | ✅ |
| `DATABASE_URL` | URL базы данных SQLite | `sqlite:///./data/users.db` | ✅ |

### 📊 Логирование

| **Параметр** | **Описание** | **Значение по умолчанию** |
|---|---|---|
| `LOG_FILE` | Путь к файлу логов | `logs/application.log` |
| `LOG_MAX_SIZE_MB` | Максимальный размер файла (MB) | `10` |
| `LOG_MAX_FILES` | Количество файлов ротации | `5` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

### 🔐 Аутентификация

| **Параметр** | **Описание** | **Значение по умолчанию** |
|---|---|---|
| `ADMIN_USERNAME` | Логин администратора | `admin` |
| `ADMIN_PASSWORD` | Пароль администратора | `admin123` |
| `DEFAULT_USER_PASSWORD` | Пароль по умолчанию для новых пользователей | `User123456` |

### 🏢 Active Directory

| **Параметр** | **Описание** | **Пример** | **Обязательный** |
|---|---|---|---|
| `AD_DOMAIN` | Домен Active Directory | `central` | ✅ |
| `AD_SERVER` | Сервер Active Directory | `dc.central.st-ing.com` | ✅ |
| `LDAP_SEARCH_BASE` | Базовая OU для поиска | `DC=central,DC=st-ing,DC=com` | ✅ |
| `LDAP_USER_OU` | OU для новых пользователей | `OU=Users,DC=central,DC=st-ing,DC=com` | ✅ |
| `LDAP_DISMISSED_OU` | OU для уволенных | `OU=Уволенные сотрудники,DC=central,DC=st-ing,DC=com` | ✅ |

### 📧 Exchange и SMTP

| **Параметр** | **Описание** | **Пример** | **Обязательный** |
|---|---|---|---|
| `EXCHANGE_SERVER` | Сервер Exchange | `mailzone.central.st-ing.com` | ✅ |
| `EXCHANGE_DATABASE` | База данных почтовых ящиков | `STI_Mailbox` | ✅ |
| `SMTP_SERVER` | SMTP сервер | `smtp.office365.com` | ✅ |
| `SMTP_PORT` | Порт SMTP | `587` | ✅ |
| `SMTP_USERNAME` | Логин SMTP | `noreply@st-ing.com` | ✅ |
| `SMTP_PASSWORD` | Пароль SMTP | `your-smtp-password` | ✅ |

### 🔌 WinRM

| **Параметр** | **Описание** | **Значение по умолчанию** |
|---|---|---|
| `WINRM_SERVER` | WinRM сервер (если не указан, используется AD_SERVER) | `dc.central.st-ing.com` |
| `WINRM_PORT` | Порт WinRM | `5985` |

### 🌍 CORS и интеграция

| **Параметр** | **Описание** | **Пример** |
|---|---|---|
| `CORS_ORIGINS` | Разрешенные домены для CORS | `http://localhost:3000,http://localhost:8080` |
| `ONEC_ALLOWED_ORIGINS` | Разрешенные домены для 1C | `http://localhost:8080,http://your-1c-server.com` |

## ⚙️ Настройка для разных сред

### 🏠 Локальная разработка

```bash
DOMAIN=localhost
API_BASE_URL=http://localhost:8000/api
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
ONEC_ALLOWED_ORIGINS=http://localhost:8080
```

### 🚀 Продакшн

```bash
DOMAIN=user-management.company.com
API_BASE_URL=https://user-management.company.com/api
CORS_ORIGINS=https://user-management.company.com
ONEC_ALLOWED_ORIGINS=https://1c.company.com
```

### 🧪 Тестирование

```bash
DOMAIN=test-user-management.company.com
API_BASE_URL=https://test-user-management.company.com/api
DATABASE_URL=sqlite:///./data/test_users.db
LOG_LEVEL=DEBUG
```

## 🔒 Безопасность

### ⚠️ Важные моменты

1. **Никогда не коммитьте `.env` в git**
2. **Используйте сложные пароли** для продакшн
3. **Ограничьте доступ** к файлу `.env`
4. **Регулярно меняйте пароли** администратора

### 🔐 Рекомендуемые пароли

```bash
# Минимальная длина: 12 символов
ADMIN_PASSWORD=AdminSecurePass2025!
DEFAULT_USER_PASSWORD=UserSecurePass2025!
SMTP_PASSWORD=SecureSmtpPass2025!
```

## 🚨 Проверка настроек

### Тест конфигурации

```bash
# Проверка загрузки переменных
python -c "
from app.core.config.settings import settings
print(f'AD Server: {settings.ad_server}')
print(f'Exchange Server: {settings.exchange_server}')
print(f'SMTP Server: {settings.smtp_server}')
"
```

### Проверка подключений

```bash
# Тест AD подключения
python test_integration.py

# Проверка логов
tail -f logs/application.log
```

## 📝 Примеры конфигураций

### 🏢 Для компании СТИ

```bash
DOMAIN=user-management.st-ing.com
AD_DOMAIN=central
AD_SERVER=dc.central.st-ing.com
EXCHANGE_SERVER=mailzone.central.st-ing.com
SMTP_SERVER=smtp.office365.com
SMTP_USERNAME=noreply@st-ing.com
```

### 🏢 Для компании ДТТермо

```bash
DOMAIN=user-management.dttermo.ru
AD_DOMAIN=central
AD_SERVER=dc.central.st-ing.com
EXCHANGE_SERVER=mailzone.central.st-ing.com
SMTP_SERVER=smtp.office365.com
SMTP_USERNAME=noreply@dttermo.ru
```

## 🔧 Устранение неполадок

### ❌ Ошибки конфигурации

| **Ошибка** | **Решение** |
|---|---|
| `module has no attribute` | Проверьте правильность имен переменных |
| `invalid server address` | Проверьте доступность серверов |
| `authentication failed` | Проверьте учетные данные AD |
| `connection refused` | Проверьте порты и firewall |

### 🔍 Диагностика

```bash
# Проверка доступности серверов
ping dc.central.st-ing.com
telnet dc.central.st-ing.com 389
telnet dc.central.st-ing.com 5985

# Проверка DNS
nslookup dc.central.st-ing.com
nslookup mailzone.central.st-ing.com
```

---

*Последнее обновление: Январь 2025*
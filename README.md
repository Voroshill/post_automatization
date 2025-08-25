# 🚀 Система управления пользователями

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.3.4-blue.svg)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Современная система управления пользователями с интеграцией 1С, Active Directory и Exchange Server**

## ✨ Возможности

- 🔄 **Интеграция с 1С** - Автоматический прием данных о новых сотрудниках
- 🏢 **Active Directory** - Создание пользователей, групп и OU
- 📧 **Exchange Server** - Автоматическое создание почтовых ящиков
- 🎯 **Веб-интерфейс** - Современный UI на Vue.js с бесконечной прокруткой
- ⚡ **Высокая производительность** - Оптимизировано для 10,000+ записей
- 🔐 **Безопасность** - Аутентификация и авторизация
- 📊 **Экспорт данных** - Excel и JSON форматы
- 🏗️ **Создание объектов** - Автоматизация для строительных проектов

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   1C System     │    │   Web Frontend  │    │   Mobile App    │
│                 │    │   (Vue.js)      │    │   (Future)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      FastAPI Backend      │
                    │   (Clean Architecture)    │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
│   SQLite DB       │  │  Active Directory │  │  Exchange Server  │
│   (Users Data)    │  │  (User Mgmt)      │  │  (Mailboxes)      │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

## 🚀 Быстрый старт

### Docker (рекомендуется)

```bash
# Клонирование репозитория
git clone <repository-url>
cd user-management-system

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл под ваше окружение

# Запуск
docker-compose up --build
```

### Локальная разработка

```bash
# Backend
poetry install
poetry run uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 📋 Требования

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Active Directory Server**
- **Exchange Server** (опционально)

## 🔧 Конфигурация

Основные настройки в файле `.env`:

```env
# Active Directory
AD_SERVER=dc.central.st-ing.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-password

# Exchange Server
EXCHANGE_SERVER=mailzone.central.st-ing.com
SMTP_SERVER=mailzone.central.st-ing.com

# 1C Integration
ONEC_ALLOWED_ORIGINS=172.17.177.47:3048,localhost:3048
```

📖 **Подробная документация**: [docs/ENV_SETUP.md](docs/ENV_SETUP.md)

## 📊 Производительность

| Метрика | Значение |
|---------|----------|
| **Первая загрузка** | < 100ms |
| **Подгрузка страницы** | < 50ms |
| **Поиск (10K+ записей)** | < 200ms |
| **Экспорт Excel** | < 5s |

## 🔌 API Endpoints

### Основные
- `POST /api/oneC/receive` - Прием данных из 1С
- `GET /api/users/pending` - Пользователи на одобрении
- `PUT /api/users/{id}/approve` - Одобрение пользователя

### Администрирование
- `POST /api/users/admin/create-object` - Создание объекта
- `PUT /api/users/admin/change-password` - Смена пароля
- `POST /api/users/admin/export-ad` - Экспорт из AD

📖 **Полная API документация**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

## 🎯 Основные функции

### 1. Интеграция с 1С
```json
POST /api/oneC/receive
{
  "unique": "#00584",
  "firstname": "Иван",
  "secondname": "Иванов",
  "company": "СТРОЙ ТЕХНО ИНЖЕНЕРИНГ ООО",
  "department": "Отдел ИТ",
  "status": "Работает"
}
```

### 2. Создание в Active Directory
- ✅ Автоматическая транслитерация имен
- ✅ Определение OU по локации и отделу
- ✅ Создание почтовых ящиков
- ✅ Добавление в группы
- ✅ Назначение менеджеров

### 3. Создание строительных объектов
- ✅ Создание OU для объекта
- ✅ Создание групп доступа (read/write)
- ✅ Создание структуры папок (15 папок)
- ✅ Настройка прав доступа

## 🛠️ Технологический стек

### Backend
- **FastAPI** - Современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **LDAP3** - Интеграция с Active Directory
- **PyWinRM** - Удаленное выполнение PowerShell
- **Pydantic** - Валидация данных

### Frontend
- **Vue.js 3** - Прогрессивный JavaScript фреймворк
- **Composition API** - Современный подход к разработке
- **Infinite Scroll** - Бесконечная прокрутка
- **Responsive Design** - Адаптивный дизайн

### DevOps
- **Docker** - Контейнеризация
- **Nginx** - Веб-сервер и прокси
- **SQLite** - Легковесная БД
- **Poetry** - Управление зависимостями Python

## 📁 Структура проекта

```
├── app/                    # Backend (Clean Architecture)
│   ├── api/               # API endpoints
│   ├── core/              # Конфигурация и логирование
│   ├── domain/            # Бизнес-логика
│   └── infrastructure/    # Внешние сервисы (AD, Exchange)
├── frontend/              # Vue.js приложение
├── docs/                  # Документация
├── scripts/               # PowerShell скрипты
└── docker-compose.yml     # Docker конфигурация
```

## 🔒 Безопасность

- ✅ Аутентификация администратора
- ✅ Валидация входных данных
- ✅ Безопасное подключение к AD
- ✅ Логирование всех операций
- ✅ CORS настройки

## 📈 Мониторинг

- 📊 Логирование всех API запросов
- 🔍 Отслеживание ошибок PowerShell
- ⏱️ Мониторинг производительности
- 📋 История операций в UI

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 📞 Поддержка

- 📧 **Email**: support@company.com
- 📖 **Документация**: [docs/](docs/)
- 🐛 **Issues**: [GitLab Issues](https://gitlab.com/project/issues)

---

<div align="center">

**Сделано для автоматизации управления пользователями**

[![GitLab](https://img.shields.io/badge/GitLab-330F63?style=for-the-badge&logo=gitlab&logoColor=white)](https://gitlab.com/)
[![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

</div>

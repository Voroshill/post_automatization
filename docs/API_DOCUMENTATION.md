# 🔌 API Документация

## 📋 Обзор

API системы управления пользователями построен на FastAPI и предоставляет RESTful endpoints для всех операций с пользователями, Active Directory и внешними системами.

### 🌐 Базовый URL
```
https://user-management.yourdomain.com/api
```

### 🔐 Аутентификация
- **Тип**: Простая форма входа
- **Сессии**: Cookies
- **Админ**: `admin` / `admin123` (настраивается в .env)

---

## 📊 Endpoints

### 🔐 Аутентификация

#### 1. Получение конфигурации аутентификации
```http
GET /api/users/auth-config
```

**Ответ:**
```json
{
  "auth_enabled": true,
  "login_url": "/api/users/auth/login"
}
```

#### 2. Вход в систему
```http
POST /api/users/auth/login
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Вход выполнен успешно",
  "user": {
    "username": "admin",
    "role": "admin"
  }
}
```

---

### 👥 Управление пользователями

#### 3. Получение всех пользователей
```http
GET /api/users/?cursor={cursor}&limit={limit}&search={search}&status={status}
```

**Параметры:**
- `cursor` (опционально): Курсор для пагинации
- `limit` (опционально): Количество записей (1-100, по умолчанию 20)
- `search` (опционально): Поисковый запрос
- `status` (опционально): Фильтр по статусу (PENDING, APPROVED, REJECTED, DISMISSED)

**Ответ:**
```json
{
  "users": [
    {
      "id": 1,
      "unique_id": "#USER001",
      "firstname": "Иван",
      "secondname": "Иванов",
      "thirdname": "Иванович",
      "company": "ООО СтройТехноИнженеринг",
      "department": "IT отдел",
      "appointment": "Разработчик",
      "status": "PENDING",
      "created_at": "2025-08-25T10:00:00Z"
    }
  ],
  "has_more": true,
  "total_count": 32,
  "next_cursor": "eyJpZCI6MjB9"
}
```

#### 4. Получение pending пользователей
```http
GET /api/users/pending?cursor={cursor}&limit={limit}&search={search}
```

**Ответ:** Аналогично GET /api/users/ с фильтром по статусу PENDING

#### 5. Получение dismissed пользователей
```http
GET /api/users/dismissed?cursor={cursor}&limit={limit}&search={search}
```

**Ответ:** Аналогично GET /api/users/ с фильтром по статусу DISMISSED

#### 6. Одобрение пользователя
```http
PUT /api/users/{user_id}/approve
```

**Ответ:**
```json
{
  "id": 1,
  "unique_id": "#USER001",
  "status": "APPROVED",
  "updated_at": "2025-08-25T10:00:00Z"
}
```

#### 7. Отклонение пользователя
```http
PUT /api/users/{user_id}/reject
```

#### 8. Увольнение пользователя
```http
PUT /api/users/{user_id}/dismiss
```

#### 9. Ручное создание пользователя
```http
POST /api/users/manual
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "unique_id": "#USER001",
  "firstname": "Иван",
  "secondname": "Иванов",
  "thirdname": "Иванович",
  "company": "ООО СтройТехноИнженеринг",
  "department": "IT отдел",
  "appointment": "Разработчик",
  "mobile_phone": "+7 (999) 123-45-67",
  "work_phone": "+7 (495) 123-45-67",
  "current_location_id": "Москва",
  "boss_id": "#BOSS001",
  "birth_date": "1990-01-01",
  "is_engineer": true
}
```

---

### 🔧 Административные функции

#### 10. Создание технического пользователя
```http
POST /api/users/create-technical-user
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "firstname": "Тест",
  "secondname": "Пользователь",
  "unique_id": "TEST123",
  "company": "ООО СтройТехноИнженеринг",
  "department": "Тестирование",
  "appointment": "Тестировщик",
  "current_location_id": "Москва",
  "work_phone": "+7(495)999-99-99",
  "technical": "technical"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Пользователь успешно создан",
  "data": {
    "sam_account_name": "Test.Polzovatel",
    "email": "Test.Polzovatel@st-ing.com",
    "ou": "OU=Технические логины,DC=central,DC=st-ing,DC=com",
    "password": "User123456"
  }
}
```

#### 11. Смена пароля пользователя
```http
PUT /api/users/admin/change-password
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "username": "test.user",
  "new_password": "NewSecurePass2025!"
}
```

#### 12. Смена номера телефона
```http
PUT /api/users/admin/change-phone
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "pager": "TEST123",
  "new_phone": "+7(495)123-45-67"
}
```

#### 13. Полная блокировка пользователя
```http
PUT /api/users/admin/block-complete
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "unique_id": "TEST123"
}
```

#### 14. Экспорт пользователей из AD
```http
POST /api/users/admin/export-ad
```

**Ответ:**
```json
{
  "success": true,
  "message": "Пользователи успешно экспортированы из Active Directory",
  "details": {
    "users": [
      {
        "displayName": "Иван Иванов",
        "mail": "ivan.ivanov@st-ing.com",
        "sAMAccountName": "ivan.ivanov",
        "department": "IT отдел",
        "company": "ООО СтройТехноИнженеринг",
        "pager": "USER001",
        "telephoneNumber": "+7(495)123-45-67"
      }
    ],
    "count": 150
  }
}
```

#### 15. Создание нового объекта
```http
POST /api/users/admin/create-object
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "object_name": "Новый объект"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Объект Новый объект создан успешно",
  "details": {
    "ou_created": true,
    "groups_created": 32,
    "folders_created": 16
  }
}
```

#### 16. Обновление тестовых атрибутов
```http
POST /api/users/admin/update-test-attributes
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "pager": "TEST123",
  "test_type": "anykey"
}
```

---

### 📊 Экспорт данных

#### 17. Экспорт в Excel
```http
GET /api/users/export/xlsx?status={status}&search={search}
```

**Параметры:**
- `status` (опционально): Фильтр по статусу
- `search` (опционально): Поисковый запрос

**Ответ:** Файл Excel для скачивания

---

### 🔗 Интеграция с 1C

#### 18. Получение пользователей от 1C (один пользователь)
```http
POST /api/onec/users
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "unique": "#00585",
  "firstname": "Иван",
  "secondname": "Петров",
  "thirdname": "Сергеевич",
  "company": "СТРОЙ ТЕХНО ИНЖЕНЕРИНГ ООО",
  "Department": "Департамент обеспечения",
  "Otdel": "Отдел информационных технологий",
  "appointment": "Системный администратор",
  "MobilePhone": "+7 (903) 123-45-67",
  "WorkPhone": "+7 (495) 123-45-67",
  "current_location_id": "Медовый",
  "boss_id": "#04564",
  "BirthDate": "1990-05-15",
  "object_date_vihod": "2025-01-20",
  "dismissal_date": null,
  "worktype_id": "1",
  "is_engeneer": 1,
  "o_id": "376.8",
  "UploadDate": "2025-01-20T10:30:00",
  "status": "Работает"
}
```

#### 19. Получение пользователей от 1C (пакет)
```http
POST /api/onec/users/batch
Content-Type: application/json
```

**Тело запроса:**
```json
[
  {
    "unique": "#00585",
    "firstname": "Иван",
    "secondname": "Петров",
    "thirdname": "Сергеевич",
    "company": "СТРОЙ ТЕХНО ИНЖЕНЕРИНГ ООО",
    "Department": "Департамент обеспечения",
    "Otdel": "Отдел информационных технологий",
    "appointment": "Системный администратор",
    "MobilePhone": "+7 (903) 123-45-67",
    "WorkPhone": "+7 (495) 123-45-67",
    "current_location_id": "Медовый",
    "boss_id": "#04564",
    "BirthDate": "1990-05-15",
    "object_date_vihod": "2025-01-20",
    "dismissal_date": null,
    "worktype_id": "1",
    "is_engeneer": 1,
    "o_id": "376.8",
    "UploadDate": "2025-01-20T10:30:00",
    "status": "Работает"
  },
  {
    "unique": "#00586",
    "firstname": "Мария",
    "secondname": "Сидорова",
    "thirdname": "Александровна",
    "company": "СТРОЙ ТЕХНО ИНЖЕНЕРИНГ ООО",
    "Department": "Сметная документация",
    "Otdel": "Отдел смет",
    "appointment": "Сметчик",
    "MobilePhone": "+7 (903) 987-65-43",
    "WorkPhone": "+7 (495) 987-65-43",
    "current_location_id": "Санкт-Петербург",
    "boss_id": "#04565",
    "BirthDate": "1985-12-10",
    "object_date_vihod": "2025-01-21",
    "dismissal_date": null,
    "worktype_id": "1",
    "is_engeneer": 0,
    "o_id": "376.9",
    "UploadDate": "2025-01-21T14:15:00",
    "status": "Работает"
  }
]
```

#### 20. Статус интеграции с 1C
```http
GET /api/onec/status
```

**Ответ:**
```json
{
  "success": true,
  "status": "active",
  "endpoint": "/api/onec/receive",
  "allowed_origins": ["http://localhost:8080", "http://your-1c-server.com"],
  "message": "1C интеграция работает"
}
```

---

### 🌐 Веб-интерфейс

#### 21. Главная страница
```http
GET /
```

**Ответ:** HTML страница с Vue.js приложением

#### 22. Проверка здоровья системы
```http
GET /health
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-25T10:00:00Z"
}
```

---

## 📝 Схемы данных

### User (Пользователь)
```json
{
  "id": 1,
  "unique_id": "#USER001",
  "firstname": "Иван",
  "secondname": "Иванов",
  "thirdname": "Иванович",
  "company": "ООО СтройТехноИнженеринг",
  "department": "IT отдел",
  "otdel": "Разработка",
  "appointment": "Разработчик",
  "boss_id": "#BOSS001",
  "current_location_id": "Москва",
  "mobile_phone": "+7 (999) 123-45-67",
  "work_phone": "+7 (495) 123-45-67",
  "birth_date": "1990-01-01",
  "object_date_vihod": "2024-01-01",
  "dismissal_date": null,
  "worktype_id": "1",
  "is_engineer": true,
  "o_id": "123.1",
  "upload_date": "2025-08-20T10:00:00Z",
  "status": "PENDING",
  "created_at": "2025-08-25T10:00:00Z",
  "updated_at": "2025-08-25T10:00:00Z"
}
```

### OneCUserData (Данные от 1C)
```json
{
  "unique": "#00585",
  "firstname": "Иван",
  "secondname": "Петров",
  "thirdname": "Сергеевич",
  "company": "СТРОЙ ТЕХНО ИНЖЕНЕРИНГ ООО",
  "Department": "Департамент обеспечения",
  "Otdel": "Отдел информационных технологий",
  "appointment": "Системный администратор",
  "MobilePhone": "+7 (903) 123-45-67",
  "WorkPhone": "+7 (495) 123-45-67",
  "current_location_id": "Медовый",
  "boss_id": "#04564",
  "BirthDate": "1990-05-15",
  "object_date_vihod": "2025-01-20",
  "dismissal_date": null,
  "worktype_id": "1",
  "is_engeneer": 1,
  "o_id": "376.8",
  "UploadDate": "2025-01-20T10:30:00",
  "status": "Работает"
}
```

### TechnicalUserRequest
```json
{
  "firstname": "Тест",
  "secondname": "Пользователь",
  "unique_id": "TEST123",
  "company": "ООО СтройТехноИнженеринг",
  "department": "Тестирование",
  "appointment": "Тестировщик",
  "current_location_id": "Москва",
  "work_phone": "+7(495)999-99-99",
  "technical": "technical"
}
```

### CreateObjectRequest
```json
{
  "object_name": "Новый объект"
}
```

### UpdateTestAttributesRequest
```json
{
  "pager": "TEST123",
  "test_type": "anykey"
}
```

---

## 🔄 Статусы пользователей

| **Статус** | **Описание** |
|---|---|
| `PENDING` | Ожидает одобрения |
| `APPROVED` | Одобрен |
| `REJECTED` | Отклонен |
| `DISMISSED` | Уволен |

---

## ❌ Обработка ошибок

### Формат ошибок
```json
{
  "success": false,
  "error_type": "error_type",
  "message": "Человекочитаемое сообщение об ошибке",
  "details": "Детальная информация об ошибке"
}
```

### Типы ошибок

| **Тип** | **Описание** |
|---|---|
| `auth_error` | Ошибка аутентификации |
| `validation_error` | Ошибка валидации данных |
| `not_found` | Ресурс не найден |
| `duplicate_user` | Пользователь уже существует |
| `ldap_error` | Ошибка Active Directory |
| `exchange_error` | Ошибка Exchange |
| `winrm_error` | Ошибка WinRM |
| `export_error` | Ошибка экспорта |

### Примеры ошибок

#### 401 Unauthorized
```json
{
  "success": false,
  "error_type": "auth_error",
  "message": "Неверное имя пользователя или пароль",
  "details": "Попробуйте повторить операцию позже"
}
```

#### 422 Validation Error
```json
{
  "success": false,
  "error_type": "validation_error",
  "message": "Ошибка валидации данных",
  "details": [
    {
      "loc": ["body", "firstname"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "success": false,
  "error_type": "ldap_error",
  "message": "Ошибка подключения к Active Directory",
  "details": "Не удалось подключиться к серверу dc.central.st-ing.com"
}
```

---

## 🔐 Безопасность

### CORS
- Настраивается через `CORS_ORIGINS` в .env
- Поддерживает множественные домены
- Автоматическая обработка preflight запросов

### Rate Limiting
- Ограничение на количество запросов
- Защита от DDoS атак
- Логирование подозрительной активности

### Валидация данных
- Pydantic схемы для всех запросов
- Автоматическая валидация типов
- Санитизация входных данных

---

## 📊 Мониторинг

### Логирование
- Все API запросы логируются
- Время выполнения запросов
- IP адреса клиентов
- Статусы ответов

### Метрики
- Количество запросов в секунду
- Время отклика API
- Количество ошибок
- Использование ресурсов

---

## 🧪 Тестирование

### Swagger UI
```
http://localhost/api/docs
```

### ReDoc
```
http://localhost/api/redoc
```

### Примеры запросов
```bash
# Тест аутентификации
curl -X POST "http://localhost/api/users/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Получение пользователей
curl -X GET "http://localhost/api/users/pending?limit=10"

# Создание технического пользователя
curl -X POST "http://localhost/api/users/create-technical-user" \
  -H "Content-Type: application/json" \
  -d '{
    "firstname": "Тест",
    "secondname": "Пользователь",
    "unique_id": "TEST123",
    "company": "ООО СтройТехноИнженеринг",
    "department": "Тестирование",
    "appointment": "Тестировщик",
    "current_location_id": "Москва",
    "work_phone": "+7(495)999-99-99",
    "technical": "technical"
  }'
```

---

*Последнее обновление: Август 2025*


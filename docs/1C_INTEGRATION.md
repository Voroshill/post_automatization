# 🔗 Интеграция с 1C

## 📋 Обзор

Система получает данные о пользователях от 1C через REST API. Поддерживаются как одиночные пользователи, так и пакетная обработка.

### 🌐 Endpoints
- **Один пользователь**: `POST /api/onec/users`
- **Пакет пользователей**: `POST /api/onec/users/batch`
- **Статус интеграции**: `GET /api/onec/status`

---

## 📊 Структура данных от 1C

### **Обязательные поля**

| **Поле** | **Тип** | **Описание** | **Пример** |
|---|---|---|---|
| `unique` | string | Табельный номер (уникальный ID) | `"#00585"` |
| `firstname` | string | Имя | `"Иван"` |
| `secondname` | string | Фамилия | `"Петров"` |
| `company` | string | Компания | `"СТРОЙ ТЕХНО ИНЖЕНЕРИНГ ООО"` |
| `Department` | string | Департамент | `"Департамент обеспечения"` |
| `Otdel` | string | Отдел | `"Отдел информационных технологий"` |
| `appointment` | string | Должность | `"Системный администратор"` |
| `current_location_id` | string | Локация | `"Медовый"` |
| `UploadDate` | datetime | Дата загрузки | `"2025-01-20T10:30:00"` |

### **Опциональные поля**

| **Поле** | **Тип** | **Описание** | **Пример** |
|---|---|---|---|
| `thirdname` | string | Отчество | `"Сергеевич"` |
| `MobilePhone` | string | Мобильный телефон | `"+7 (903) 123-45-67"` |
| `WorkPhone` | string | Рабочий телефон | `"+7 (495) 123-45-67"` |
| `boss_id` | string | ID руководителя | `"#04564"` |
| `BirthDate` | date | Дата рождения | `"1990-05-15"` |
| `object_date_vihod` | date | Дата выхода на объект | `"2025-01-20"` |
| `dismissal_date` | date | Дата увольнения | `null` |
| `worktype_id` | string | Тип работы | `"1"` |
| `is_engeneer` | integer | Инженер (1/0) | `1` |
| `o_id` | string | ID объекта | `"376.8"` |
| `status` | string | Статус работы | `"Работает"` |

---

## 📝 Примеры запросов

### **1. Один пользователь**

```http
POST /api/onec/users
Content-Type: application/json
```

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

**Успешный ответ:**
```json
{
  "success": true,
  "message": "Сотрудник успешно добавлен в систему",
  "user_id": 123
}
```

### **2. Пакет пользователей**

```http
POST /api/onec/users/batch
Content-Type: application/json
```

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

**Успешный ответ:**
```json
{
  "success": true,
  "message": "Обработка завершена: 2 создано, 0 ошибок",
  "total_received": 2,
  "created": 2,
  "failed": 0,
  "created_users": [
    {
      "unique_id": "#00585",
      "user_id": 123,
      "status": "created"
    },
    {
      "unique_id": "#00586",
      "user_id": 124,
      "status": "created"
    }
  ],
  "failed_users": []
}
```

---

## 🔄 Преобразование данных

### **Маппинг полей**

| **1C поле** | **Внутреннее поле** | **Описание** |
|---|---|---|
| `unique` | `unique_id` | Табельный номер |
| `firstname` | `firstname` | Имя |
| `secondname` | `secondname` | Фамилия |
| `thirdname` | `thirdname` | Отчество |
| `company` | `company` | Компания |
| `Department` | `department` | Департамент |
| `Otdel` | `otdel` | Отдел |
| `appointment` | `appointment` | Должность |
| `MobilePhone` | `mobile_phone` | Мобильный телефон |
| `WorkPhone` | `work_phone` | Рабочий телефон |
| `current_location_id` | `current_location_id` | Локация |
| `boss_id` | `boss_id` | ID руководителя |
| `BirthDate` | `birth_date` | Дата рождения |
| `object_date_vihod` | `object_date_vihod` | Дата выхода на объект |
| `dismissal_date` | `dismissal_date` | Дата увольнения |
| `worktype_id` | `worktype_id` | Тип работы |
| `is_engeneer` | `is_engineer` | Инженер |
| `o_id` | `o_id` | ID объекта |
| `UploadDate` | `upload_date` | Дата загрузки |

### **Преобразование статуса**

| **1C статус** | **Внутренний статус** |
|---|---|
| `"Работает"` | `PENDING` |
| `"Уволен"` | `DISMISSED` |
| Любой другой | `PENDING` |

---

## ❌ Обработка ошибок

### **Дубликат пользователя**

**Ошибка:**
```json
{
  "success": false,
  "error_type": "duplicate_user",
  "message": "Сотрудник с табельным номером #00585 уже существует в системе",
  "details": "Попробуйте использовать другой табельный номер или обновите существующую запись"
}
```

### **Ошибка валидации**

**Ошибка:**
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

### **Пакетная обработка с ошибками**

**Ответ:**
```json
{
  "success": true,
  "message": "Обработка завершена: 1 создано, 1 ошибок",
  "total_received": 2,
  "created": 1,
  "failed": 1,
  "created_users": [
    {
      "unique_id": "#00585",
      "user_id": 123,
      "status": "created"
    }
  ],
  "failed_users": [
    {
      "unique_id": "#00586",
      "error": "Сотрудник с табельным номером #00586 уже существует в системе",
      "status": "failed"
    }
  ]
}
```

---

## 🔐 Безопасность

### **CORS настройки**
- Разрешенные домены настраиваются в `ONEC_ALLOWED_ORIGINS`
- Поддерживаются множественные домены через запятую
- Автоматическая проверка Origin заголовка

### **Валидация данных**
- Все поля проверяются на соответствие типам
- Обязательные поля должны быть заполнены
- Автоматическая санитизация входных данных

### **Логирование**
- Все запросы от 1C логируются
- Ошибки записываются с деталями
- Успешные операции также логируются

---

## 🧪 Тестирование

### **cURL примеры**

```bash
# Тест одного пользователя
curl -X POST "http://localhost/api/onec/users" \
  -H "Content-Type: application/json" \
  -d '{
    "unique": "#TEST001",
    "firstname": "Тест",
    "secondname": "Пользователь",
    "company": "СТРОЙ ТЕХНО ИНЖЕНЕРИНГ ООО",
    "Department": "Тестирование",
    "Otdel": "Отдел тестов",
    "appointment": "Тестировщик",
    "current_location_id": "Москва",
    "UploadDate": "2025-08-25T10:00:00"
  }'

# Тест пакета пользователей
curl -X POST "http://localhost/api/onec/users/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "unique": "#TEST002",
      "firstname": "Тест2",
      "secondname": "Пользователь2",
      "company": "СТРОЙ ТЕХНО ИНЖЕНЕРИНГ ООО",
      "Department": "Тестирование",
      "Otdel": "Отдел тестов",
      "appointment": "Тестировщик",
      "current_location_id": "Москва",
      "UploadDate": "2025-08-25T10:00:00"
    }
  ]'

# Проверка статуса
curl -X GET "http://localhost/api/onec/status"
```

### **Python примеры**

```python
import requests
import json

# Данные пользователя
user_data = {
    "unique": "#TEST001",
    "firstname": "Тест",
    "secondname": "Пользователь",
    "company": "СТРОЙ ТЕХНО ИНЖЕНЕРИНГ ООО",
    "Department": "Тестирование",
    "Otdel": "Отдел тестов",
    "appointment": "Тестировщик",
    "current_location_id": "Москва",
    "UploadDate": "2025-08-25T10:00:00"
}

# Отправка одного пользователя
response = requests.post(
    "http://localhost/api/onec/users",
    json=user_data,
    headers={"Content-Type": "application/json"}
)
print(response.json())

# Отправка пакета пользователей
users_batch = [user_data, user_data2]
response = requests.post(
    "http://localhost/api/onec/users/batch",
    json=users_batch,
    headers={"Content-Type": "application/json"}
)
print(response.json())
```

---

## 📊 Мониторинг

### **Статус интеграции**
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

### **Логи интеграции**
- Все запросы от 1C логируются в `logs/application.log`
- Уровень логирования: INFO для успешных, WARNING для дубликатов, ERROR для ошибок
- Включает время, IP адрес, количество обработанных пользователей

---

## 🔧 Настройка

### **Переменные окружения**
```bash
# Разрешенные домены для 1C
ONEC_ALLOWED_ORIGINS=http://localhost:8080,http://your-1c-server.com

# Endpoint для получения данных
ONEC_ENDPOINT=/api/onec/receive
```

### **Проверка настроек**
```bash
# Проверка CORS настроек
curl -H "Origin: http://your-1c-server.com" \
  -X GET "http://localhost/api/onec/status"

# Проверка доступности endpoint
curl -X GET "http://localhost/api/onec/status"
```

---

*Последнее обновление: Август 2025*

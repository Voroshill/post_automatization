# Frontend - Система управления пользователями

Vue.js приложение для управления пользователями.

## Технологии

- Vue 3 (Composition API)
- Vite
- Bootstrap 5
- Axios

## Установка и запуск

```bash
# Установка зависимостей
npm install

# Запуск в режиме разработки
npm run dev

# Сборка для продакшена
npm run build
```

## Структура проекта

```
src/
├── components/     # Vue компоненты
├── services/       # API сервисы
└── styles/         # CSS стили
```

## API интеграция

Фронтенд взаимодействует с бэкендом через API:

- `GET /api/users/pending` - Получение пользователей на одобрение
- `PUT /api/users/{id}/approve` - Одобрение пользователя
- `PUT /api/users/{id}/reject` - Отклонение пользователя

## Разработка

При локальной разработке используйте `npm run dev` для запуска с hot reload.

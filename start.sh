#!/bin/bash

# Запуск nginx в фоне
#nginx

# Запуск FastAPI приложения
cd /app
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload

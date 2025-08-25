# Этап 1: Сборка фронтенда
FROM node:18-alpine as frontend-build

WORKDIR /app/frontend


COPY frontend/package*.json ./


RUN npm install


COPY frontend/ .


RUN npm run build && ls -la dist/

FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    gcc \
    nginx \
    wget \
    apt-transport-https \
    ca-certificates \
    gnupg \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*


COPY pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main --no-root

COPY . .

COPY --from=frontend-build /app/frontend/dist/* /app/static/

RUN mkdir -p /app/scripts


COPY nginx.conf /etc/nginx/sites-available/default


RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    mkdir -p /app/logs && \
    mkdir -p /run/nginx && \
    mkdir -p /var/log/nginx && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /var/log/nginx && \
    chown -R appuser:appuser /var/lib/nginx && \
    chown -R appuser:appuser /run/nginx && \
    chmod 755 /app/logs && \
    chmod 755 /run/nginx && \
    chmod 777 /run/nginx && \
    chmod 777 /var/log/nginx

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh && chown appuser:appuser /app/start.sh

EXPOSE 8000 80

CMD ["/app/start.sh"]

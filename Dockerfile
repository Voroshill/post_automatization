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

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app && \
    chmod 755 /app/logs && \
    true

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh && chown appuser:appuser /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]

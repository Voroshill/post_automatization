# syntax=docker/dockerfile:1.4
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

# Faster and reliable pip/poetry installs
ENV PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10 \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=https://pypi.org/simple

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-compile poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi --no-root --sync

COPY . .

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

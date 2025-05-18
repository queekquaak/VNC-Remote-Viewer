# Используем официальный образ Python
FROM python:3.11-slim

# Метаданные образа (стандартные и кастомные)
LABEL maintainer="queekquaak@proton.me" \
      org.opencontainers.image.title="VNC Remote Viewer API" \
      org.opencontainers.image.description="API сервер для управления VNC соединениями" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="MPSU"

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt || true

# Копируем весь проект
COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/data/log

# Переменные окружения из config.py с значениями по умолчанию
ENV PYTHONUNBUFFERED=1 \
    API_SERVER_PORT=8080 \
    API_AUTH_TOKEN=moneyprintergobrrr \
    METRICS_UPDATE_INTERVAL=60 \
    LOG_WHEN=D \
    LOG_INTERVAL=1 \
    LOG_COUNT=30

# Порт по-умолчанию, который будет слушать сервер
EXPOSE ${API_SERVER_PORT}

# Команда для запуска приложения
CMD ["python", "__main__.py"]

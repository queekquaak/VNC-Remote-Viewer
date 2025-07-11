# Используем официальный образ Python
FROM python:3.11-slim

# Метаданные образа
LABEL maintainer="queekquaak@proton.me" \
      org.opencontainers.image.title="VNC Remote Viewer API" \
      org.opencontainers.image.description="Веб-приложение для управления VNC соединениями" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="MPSU"

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Переменные окружения со значениями по умолчанию
ENV FRONTEND_PORT=5000 \
    API_SERVER_ADDR=localhost:8080 \
    VIEW_ONLY_PASS=password \
    VNC_COMPRESSION=9 \
    VNC_TILE_QUALITY=1 \
    VNC_TILE_SCALE=0.5 \
    VNC_FULLSCREEN_QUALITY=5 \
    VNC_FULLSCREEN_SCALE=0.8

# Открываем порт, на котором работает приложение
EXPOSE ${FRONTEND_PORT}

# Запускаем приложение
ENTRYPOINT ["python", "__main__.py"]

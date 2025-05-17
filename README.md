# VNC Remote Viewer

**VNC Remote Viewer** — это система удаленного мониторинга и управления компьютерами в локальной сети через VNC. Проект состоит из трёх компонентов:

- **Агент** — устанавливается на управляемые хосты, регистрирует их в системе.
- **API-сервер** — получает данные от агентов, хранит и предоставляет их фронтенду.
- **Frontend-сервер** — позволяет просматривать и взаимодействовать с хостами в реальном времени.

## 🛠️ Требования

### Операционная система

- **Linux** дистрибутивы на базе Debian, Ubuntu, CentOS, RHEL и др.
- Поддержка `systemd` (для работы демона)

### Рабочее окружение (на управляемых хостах)

Для успешного запуска VNC-сессий необходимы:

- **Рабочее окружение (DE / WM)**:
  - Полноценные DE: `Xfce`, `LXDE`, `MATE`, `GNOME`, `KDE Plasma`
  - Лёгкие оконные менеджеры: `Openbox`, `Fluxbox`, `i3` — также поддерживаются

- **Дисплейные менеджеры (DM)**:
  - Совместимые: `lightdm`, `gdm`, `sddm`, `xdm`
  - Не совместимы: headless-среды без входа в X-сессию (если не настроено автологирование и запуск DE вручную)

> **Рекомендуемое окружение:** `Xfce` + `lightdm` (минимальная нагрузка, хорошая совместимость)

## 📦 Структура проекта

```
VNC-Remote-Viewer/
├── agent/              # Агент для управляемых хостов
├── api-server/         # API-сервер
├── frontend-server/    # Веб-интерфейс для наблюдателя
└── README.md
```

## 🚀 Быстрый запуск

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/queekquaak/VNC-Remote-Viewer.git
cd VNC-Remote-Viewer
```

### 2. Сборка и запуск API и Frontend серверов

В директориях `api-server` и `frontend-server` приведены **примеры** `docker-compose.yml` и `.env`.

Вы можете использовать их в качестве шаблона. Cборку и настройку рекомендуется выполнять самостоятельно:
#### Пример развертывания API-сервера:
```bash
cd api-server
sudo docker build -t vnc-rm-server .
docker run -d \
  -p 8080:8080 \
  -e API_SERVER_PORT=8080 \
  -e METRICS_UPDATE_INTERVAL=60 \
  -e LOG_WHEN=D \
  -e LOG_INTERVAL=1 \
  -e LOG_COUNT=30 \
  -v ./vnc-rm-server/data:/app/data \
  --name vnc-rm-server \
  --restart unless-stopped \
  vnc-rm-server
```
#### Пример развертывания веб-интерфейса:
```bash
cd frontend-server
sudo docker build -t vnc-rm-app .
# Подготовьте директорию для монтирования
sudo mkdir -p /opt/vnc-rm-app/data
# Скопируйте шаблоны docker-compose и .env в /opt/vnc-rm-app
sudo cp frontend-server/env /opt/vnc-rm-app/.env
sudo cp frontend-server/docker-compose.yml /opt/vnc-rm-app
# Отредактируйте их по своему желанию
# Перейдите в созданную директорию
sudo cd /opt/vnc-rm-app/data
# И запустите сборку
sudo docker compose up -d
```

Веб-интерфейс доступен по заданному порту на адресе вашего сервера [http://vnc-rm-app-ip:port](http://vnc-rm-app-ip:port)

### 3. Установка агента на хост

На каждом хосте выполните:

```bash
cd agent
# Пример для Debian-based Linux
bash install.sh --apt
```
В конце установки следуйте рекомендациям для настройки и запуска.

> Агент запускается в виде демона `vnc-rm-agent`, и взаимодействует с API-сервером.

### API-сервер хранит данные в:

```
./data/servers.json
```

### Frontend обращается к API-серверу и отображает VNC iframe’ы по каждому хосту.

## 📡 Особенности

- Поддержка `noVNC` через iframe (режим просмотра и управления).
- Регистрация агентов без базы данных — только JSON.
- Метки `excluded: true` для исключения хостов из мониторинга.
- Простая интеграция с systemd и Docker.

## 📁 Компоненты

### 🖥 Agent

- Написан на Python.
- Определяет IP и текущего пользователя.
- Автоматически подбирает порты прослушивания.
- Передаёт данные на API `/api/servers/register`.
- Использует `websockify` и `noVNC`.

### 🧠 API-сервер

- Предоставляет следующие маршруты:

| Метод | Путь                     | Назначение                        |
|-------|--------------------------|-----------------------------------|
| GET   | /api/servers             | Получение списка серверов        |
| POST  | /api/servers/register    | Регистрация агента                |
| POST  | /api/servers/exclude     | Исключение хоста из списка       |
| POST  | /api/servers/include     | Возврат хоста в мониторинг       |

### 🌐 Frontend

- Показывает плитки хостов.
- Позволяет управлять и фильтровать хосты.
- Позволяет создавать пользовательские списки.
- Использует docker-окружение для запуска в изоляции.

## 🐳 Зависимости

- Docker, Docker Compose
- Python 3.7+
- x11vnc, websockify, noVNC, Snap (устанавливаются через агент)

## 📜 Лицензия

Проект распространяется под лицензией GNU General Public License v3. Подробнее см. в файле [LICENSE](./LICENSE).

---

## 📬 Обратная связь

Если вы нашли баг или хотите предложить улучшение — пишите на queekquaak@proton.me

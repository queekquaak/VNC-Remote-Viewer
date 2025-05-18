import sys
from pathlib import Path
from modules.logger import ServerLogger
from modules.config import API_SERVER_PORT, API_AUTH_TOKEN, METRICS_UPDATE_INTERVAL, LOG_WHEN, LOG_INTERVAL, LOG_COUNT
from modules.api import (
    ServerRepository,
    ServerManager,
    ServerHTTPServer,
    ServerRequestHandler
)


def main():
    # Конфигурация путей
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    LOG_DIR = DATA_DIR / "log"
    LOG_FILE = LOG_DIR / "server.log"
    SERVERS_FILE = DATA_DIR / "servers.json"

    # Инициализация стартового логгера
    logger = ServerLogger(str(LOG_FILE), level='INFO')

    try:

        # Создание директорий
        try:
            DATA_DIR.mkdir(exist_ok=True)
            LOG_DIR.mkdir(exist_ok=True)
        except OSError as e:
            logger.critical(f"Failed to create directories: {e}")
            sys.exit(1)

        # Реконфигурация логгера в основной режим
        try:
            logger = logger.reconfigure(
                level='DEBUG',
                fmt=ServerLogger.DEFAULT_FORMAT,
                when=str(LOG_WHEN),
                interval=int(LOG_INTERVAL),
                count=int(LOG_COUNT))
            metrics_thread = logger.start_metrics_reporter(int(METRICS_UPDATE_INTERVAL))
        except Exception as e:
            logger.critical(f"Failed to configure logger: {e}")
            sys.exit(1)

        # Инициализация компонентов сервера
        repository = ServerRepository(str(SERVERS_FILE), logger)
        manager = ServerManager(repository, logger.metrics)
        port = int(API_SERVER_PORT)
        auth_token = str(API_AUTH_TOKEN)

        # Запуск сервера
        server = ServerHTTPServer(
            manager=manager,
            metrics=logger.metrics,
            server_address=("", port),
            auth_token=auth_token,
            RequestHandlerClass=ServerRequestHandler
        )

        logger.info(f"Starting server on port {port}")
        logger.info(f"Servers data file: {SERVERS_FILE}")
        logger.info(f"Log file: {LOG_FILE}")

        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("Server shutdown by user request")
    except Exception as e:
        logger.critical(f"Server critical error: {e}")
        sys.exit(1)
    finally:
        logger.info("Server stopped")


if __name__ == "__main__":
    main()

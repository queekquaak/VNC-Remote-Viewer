from modules.agent import Agent
from modules.logger import Logger
from modules.config import ConfigLoader
from pathlib import Path
import sys
import signal


# Конфигурация путей
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / 'log'
CONF_DIR = BASE_DIR / 'conf'
LOG_FILE = LOG_DIR / 'vnc-rm-agent.log'
CONF_FILE = CONF_DIR / 'config.yaml'

# Инициализация временного логгера для старта
temp_logger = Logger(str(LOG_FILE), level='INFO')
temp_logger.info("Starting VNC RM Agent initialization")


def shutdown(signum, frame):
    """Обработчик сигналов завершения"""
    logger = Logger.get_logger(str(LOG_FILE))
    (logger or temp_logger).info("Agent stopped by signal")
    sys.exit(0)


def main():
    try:
        # Загрузка конфигурации
        config_loader = ConfigLoader(str(CONF_FILE), temp_logger)
        config = config_loader.load_config()

        # Инициализация основного логгера
        main_logger = Logger.get_logger(str(LOG_FILE))

        main_logger.reconfigure(
            level=config.get('LOG_LEVEL', 'DEBUG'),
            fmt=config.get('LOG_FORMAT', Logger.DEFAULT_FORMAT),
            when=config.get('LOG_WHEN', 'D'),
            interval=config.get('LOG_INTERVAL', 1),
            count=config.get('LOG_COUNT', 30)
        )

        agent = Agent(logger=main_logger, config=config)
        agent.run()

    except KeyboardInterrupt:
        (Logger.get_logger(str(LOG_FILE)) or temp_logger).info("Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        (Logger.get_logger(str(LOG_FILE)) or temp_logger).critical(f"Startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    main()

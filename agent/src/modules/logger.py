import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Optional, ClassVar, Dict


class Logger:
    """
    Класс логгера с поддержкой ротации логов и реестром экземпляров.
    Позволяет получать доступ к существующим логгерам и изменять их параметры.
    """
    DEFAULT_FORMAT: ClassVar[str] = '%(asctime)s - %(levelname)s - %(message)s'
    _global_fallback_configured = False  # Статический флаг для fallback логирования
    _registry: Dict[str, 'Logger'] = {}  # Реестр созданных логгеров

    @classmethod
    def get_logger(cls, log_file: str) -> Optional['Logger']:
        """
        Получить существующий экземпляр логгера по имени файла.
        Args:
            log_file: Путь к файлу логов
        Returns:
            Logger или None, если логгер не найден
        """
        return cls._registry.get(log_file)

    def __init__(self, log_file: str, level: str = 'DEBUG', fmt: str = DEFAULT_FORMAT,
                 when: Optional[str] = None, interval: Optional[int] = None, count: Optional[int] = None):
        """
        Инициализация логгера с опциональной ротацией логов.

        Args:
            log_file: Путь к файлу логов
            level: Уровень логирования (default: DEBUG)
            fmt: Формат строк логов (default: DEFAULT_FORMAT)
            when: Время ротации логов ('D', 'H', 'M', 'W0-W6', 'midnight')
            interval: Интервал ротации логов
            count: Количество хранимых лог-файлов
        """
        self.log_file = log_file
        self.level = getattr(logging, level.upper(), logging.DEBUG)
        self.format = fmt
        self.when = when
        self.interval = interval
        self.count = count

        self.logger_name = f"file_logger_{hash(log_file)}"

        try:
            self.logger = self._configure_logger()
            self._registry[log_file] = self
        except Exception as e:
            self._configure_fallback()
            self.logger.exception(f"Failed to initialize file logger, using fallback: {e}")

    def _configure_logger(self) -> logging.Logger:
        """Основная конфигурация логгера с опциональной ротацией"""
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(self.level)

        # Предотвращаем дублирование сообщений
        logger.propagate = False

        # Очищаем существующие обработчики
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Настройка ротации логов, если указаны параметры
        if self.when and self.count:
            try:
                handler = TimedRotatingFileHandler(
                    filename=self.log_file,
                    when=self.when,
                    interval=self.interval,
                    backupCount=self.count,
                    encoding='utf-8',
                    utc=False
                )
                print(f"Log rotation configured: every {self.interval}{self.when}, up to {self.count} archives")
            except Exception as e:
                # В случае ошибки при настройке ротации переходим к простому логгеру
                print(f"Failed to configure log rotation: {e}. Using simple file logging")
                handler = logging.FileHandler(self.log_file, encoding='utf-8')
        else:
            handler = logging.FileHandler(self.log_file, encoding='utf-8')
            print("Using simple file logging...")

        handler.setFormatter(logging.Formatter(self.format))
        logger.addHandler(handler)

        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(self.format))
        logger.addHandler(console_handler)

        return logger

    def _configure_fallback(self):
        """Fallback-конфигурация при ошибках"""
        if not Logger._global_fallback_configured:
            logging.basicConfig(
                level=self.level,
                format=self.format
            )
            Logger._global_fallback_configured = True
        self.logger = logging.getLogger(f"fallback_{self.logger_name}")

    def reconfigure(self, level: Optional[str] = None, fmt: Optional[str] = None,
                    when: Optional[str] = None, interval: Optional[int] = None,
                    count: Optional[int] = None) -> 'Logger':
        """
        Изменить конфигурацию существующего логгера.

        Args:
            level: Новый уровень логирования
            fmt: Новый формат сообщений
            when: Новое время ротации
            interval: Новый интервал ротации
            count: Новое количество хранимых файлов
        Returns:
            self для цепочки вызовов
        """
        if level:
            self.level = getattr(logging, level.upper(), logging.DEBUG)
        if fmt:
            self.format = fmt
        if when is not None:
            self.when = when
        if interval is not None:
            self.interval = interval
        if count is not None:
            self.count = count

        try:
            self.logger = self._configure_logger()
        except Exception as e:
            self._configure_fallback()
            self.logger.exception(f"Failed to reconfigure logger: {e}")

        return self

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        self.logger.exception(msg, *args, **kwargs)

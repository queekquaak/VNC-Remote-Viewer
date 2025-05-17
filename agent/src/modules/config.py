import yaml
from typing import Dict, Any


class ConfigLoader:
    """Загрузчик конфигурации агента"""

    def __init__(self, conf_file: str, logger):
        self.logger = logger
        self.conf_file = conf_file

    def load_config(self) -> Dict[str, Any]:
        try:
            if self.logger:
                self.logger.debug(f"Attempting to load config from {self.conf_file}")

            with open(self.conf_file, 'r') as file:
                config = yaml.safe_load(file)
                if self.logger:
                    self.logger.info("Configuration successfully loaded")
                return config

        except FileNotFoundError as e:
            if self.logger:
                self.logger.critical(f"Config file not found: {self.conf_file}")
            raise
        except yaml.YAMLError as e:
            if self.logger:
                self.logger.error(f"Invalid YAML syntax in config: {str(e)}")
            raise
        except Exception as e:
            if self.logger:
                self.logger.exception(f"Unexpected error while loading config")
            raise

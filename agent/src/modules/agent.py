import os
import subprocess
import time
from typing import Optional, Dict, Any
from .register import ServerRegister
from .vnc import PortManager, VNCSession


class Agent:
    """Класс агента для регистрации"""

    def __init__(self, logger, config: Dict[str, Any]):
        self.logger = logger
        self.config = config
        self.server_register = ServerRegister(logger)

        self.vnc_config = config.get('VNC', {})

        self.vnc_session = VNCSession(
            logger,
            self.vnc_config.get('VNC_BINARY', '/usr/bin/x11vnc'),
            self.vnc_config.get('WEBSOCKIFY_BINARY', '/usr/bin/websockify'),
            self.vnc_config.get('ADMIN_PASS', 'password'),
            self.vnc_config.get('VIEW_ONLY_PASS', 'password')
        )

        self.SERVER_API_URL = self.build_api_url()
        self.API_AUTH_TOKEN = str(self.config.get("API_AUTH_TOKEN"))
        self.SCAN_INTERVAL = int(self.config.get('SCAN_INTERVAL', 30))
        self.RETRY_INTERVAL = int(self.config.get('RETRY_INTERVAL', 60))

    def build_api_url(self) -> str:
        """Получить URL для регистрации сервера"""
        server_ip = self.config.get('SERVER_IP', 'localhost:8080')
        return f"http://{server_ip}/api/servers/register"

    def get_current_user(self) -> Optional[str]:
        """Получить имя пользователя активной сессии"""
        try:
            cmd = ["cat", "/sys/class/tty/tty0/active"]
            tty_result = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()
            if not tty_result:
                return None
        except subprocess.CalledProcessError as e:
            self.logger.error(f"File /sys/class/tty/tty0/active not found or inaccessible: {e}")
            return None

        try:
            cmd = [
                "sh", "-c",
                f"loginctl list-sessions --no-legend | grep '{tty_result}' | awk '{{print $3}}'"
            ]
            user_result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            ).stdout.strip()
            return user_result if user_result else None
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Unable to get username: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return None

    def get_ip_address(self) -> Optional[str]:
        """Получить основной IPv4-адрес агента"""
        try:
            result = subprocess.run(
                ["hostname", "-I"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            return result.stdout.strip().split()[0]
        except (subprocess.SubprocessError, IndexError) as e:
            self.logger.error(f"IP address detection failed: {e}")
            return None

    def is_home_exist(self, username: str) -> bool:
        """Проверка наличия директории пользователя"""
        try:
            home_path = os.path.join('/home', username)
            return os.path.isdir(home_path)
        except (OSError, TypeError) as e:
            self.logger.error(f"Unable to check directory: {e}")
            return False

    def register_agent(self, username, ip, ws_port) -> bool:
        """Регистрация агента с информацией о портах"""

        if not ip or not username:
            self.logger.warning("Registration skipped - missing IP or username")
            return False

        result = self.server_register.register_server(
            server_api_url=self.SERVER_API_URL,
            ip=ip,
            username=username,
            websockify_port=ws_port,
            auth_token=self.API_AUTH_TOKEN
        )

        if result is None:
            return False

        self.logger.debug(f"Registration result: {result}")
        return True

    def run(self) -> None:
        """Основной цикл работы агента"""
        self.logger.info("Starting agent with VNC management")
        last_user = ""
        while True:
            try:
                username = self.get_current_user()
                ip = self.get_ip_address()
                if username and ip and username.lower() != last_user.lower():
                    if self.is_home_exist(username):
                        self.vnc_session.stop()
                        try:
                            vnc_display = PortManager.get_current_display(username)
                            ports = PortManager.calculate_ports(self.vnc_config)
                            self.logger.debug(f"Using display: {vnc_display}")
                            max_retries = 5  # Максимальное количество попыток запуска vnc
                            for attempt in range(1, max_retries + 1):
                                if self.vnc_session.start(username, vnc_display, ports['vnc'], ports['web']):
                                    if self.register_agent(username, ip, ports['web']):
                                        last_user = username.lower()
                                        self.logger.info(f"Agent successfully registered for user {username}")
                                        time.sleep(self.SCAN_INTERVAL)
                                        break  # Успех, выходим из цикла
                                    self.logger.warning("Registration failed, retrying...")
                                else:
                                    self.logger.warning(f"VNC start failed, attempt {attempt}/{max_retries}")
                                # Ждем перед следующей попыткой (кроме случая успешного завершения)
                                if attempt < max_retries:  # Не ждем после последней попытки
                                    time.sleep(self.RETRY_INTERVAL)
                            else:  # Этот блок выполнится, если цикл не был прерван break
                                self.logger.error(f"Failed to start VNC after {max_retries} attempts")
                                time.sleep(self.RETRY_INTERVAL)
                        except Exception as e:
                            self.logger.error(f"VNC startup error: {e}")
                            time.sleep(self.RETRY_INTERVAL)
                    else:
                        time.sleep(self.RETRY_INTERVAL)
                else:
                    time.sleep(self.SCAN_INTERVAL)
            except Exception as e:
                self.logger.exception(f"Critical error in agent loop: {e}")
                time.sleep(self.RETRY_INTERVAL)

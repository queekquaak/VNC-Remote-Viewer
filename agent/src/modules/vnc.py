import subprocess
import socket
import re
import os
import psutil
from typing import Dict, Any


class PortManager:
    """Менеджер динамического выделения интерфейсов"""

    @staticmethod
    def get_current_display(username: str) -> str:
        """
        Определяет дисплей пользователя.
        Args:
            username: Пользователь
        Returns:
            Строку ':0' или fallback значение из окружения
        """
        try:
            # Получаем информацию о текущих сессиях
            who_output = subprocess.run(
                ['who', '-u'],
                capture_output=True,
                text=True,
                check=True
            ).stdout
            disp_re = re.compile(r'\((:[0-9]+(?:\.[0-9]+)?)\)')
            for line in who_output.splitlines():
                parts = line.split()
                # Точное совпадение имени в первом столбце
                if parts and parts[0] == username:
                    m = disp_re.search(line)
                    if m:
                        return m.group(1)
                    if parts[1].startswith(':'):
                        return parts[1]
            # Fallback: переменная окружения DISPLAY
            display = os.getenv('DISPLAY', ':0')
            if display:
                if not display.startswith(':'):
                    display = f":{display}"
                return display
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Ошибка при запуске `who -u`: {e}")
        except Exception as e:
            raise RuntimeError(f"Cannot determine display: {e}")

    @staticmethod
    def calculate_ports(vnc_config: Dict[str, Any]) -> Dict[str, int]:
        """
        Вычисление свободных портов
        Args:
            vnc_config: словарь файла конфигурации
        Returns:
            result где ['vnc'] и ['web'] - соответствующие порты
        """
        MAX_PORT_ATTEMPTS = 100

        def find_available_ports(base_port: int, web_port: int, increment: int = 0) -> Dict[str, int]:
            return {
                'vnc': base_port + increment,
                'web': web_port + increment
            }

        try:
            base_vnc_port = vnc_config.get('VNC_PORT', 5900)
            base_web_port = vnc_config.get('WEBSOCKIFY_PORT', 6080)
            increment = 0
            while increment < MAX_PORT_ATTEMPTS:
                ports = find_available_ports(base_vnc_port, base_web_port, increment)
                if (PortManager.is_port_available(ports['vnc']) and
                        PortManager.is_port_available(ports['web'])):
                    return ports
                increment += 1
            raise RuntimeError(f"Could not find available ports after {MAX_PORT_ATTEMPTS} attempts")
        except ValueError as e:
            raise ValueError(f"Error: {e}")

    @staticmethod
    def is_port_available(port: int) -> bool:
        """Проверка занятости порта"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0


class VNCSession:
    """Класс управления сессией VNC"""

    def __init__(self, logger, vnc_binary: str, websockify_binary: str,
                 passwd: str, vo_passwd: str):
        self.logger = logger
        self.vnc_binary = vnc_binary
        self.websockify_binary = websockify_binary
        self.passwd = passwd
        self.vo_passwd = vo_passwd
        self.processes = []

    def start(self, username: str, vnc_display: str, vnc_port: int, websockify_port: int) -> bool:
        """Запуск vnc и websockify"""
        try:
            vnc_cmd = [
                'sudo', '-u', str(username), 'env',
                self.vnc_binary,
                '-display', str(vnc_display),
                '-rfbport', str(vnc_port),
                '-passwd', str(self.passwd),
                '-viewpasswd', str(self.vo_passwd),
                '-forever',
                '-shared'
            ]

            vnc_proc = subprocess.Popen(vnc_cmd)
            self.processes.append(vnc_proc)

            if not PortManager.is_port_available(vnc_port):
                self.logger.error(f"Failed to start VNC session on port {vnc_port}")
                self.stop()
                return False

            ws_cmd = [
                self.websockify_binary,
                '--listen', str(websockify_port),
                '--vnc', f"localhost:{vnc_port}"
            ]

            ws_proc = subprocess.Popen(ws_cmd)
            self.processes.append(ws_proc)

            if not PortManager.is_port_available(websockify_port):
                self.logger.error(f"Failed to start Websockify on port {websockify_port}")
                self.stop()
                return False

            self.logger.info(
                f"Started VNC for {username} on ports VNC: {vnc_port} with Websockify on {websockify_port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start VNC session: {e}")
            self.stop()
            return False

    def stop(self) -> None:
        """Остановить сессии"""
        for proc in self.processes[:]:  # Используем копию списка для безопасной итерации
            try:
                if proc.poll() is None:  # Проверяем, работает ли процесс
                    proc.terminate()
                    proc.wait(timeout=5)
            except (psutil.NoSuchProcess, subprocess.TimeoutExpired):
                try:
                    if proc.poll() is None:
                        proc.kill()
                except Exception as e:
                    self.logger.error(f"Error killing process: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error stopping process: {e}")
        self.processes.clear()
        self.logger.info("Stopped VNC session.")

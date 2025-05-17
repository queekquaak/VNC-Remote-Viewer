import json
import urllib.request
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any, Optional
from http.server import BaseHTTPRequestHandler, HTTPServer
from .logger import ServerLogger, ConnectionMetrics


class ServerRepository:
    """Класс для работы с хранилищем данных сервера"""

    def __init__(self, servers_file: str, logger: ServerLogger):
        """
        Args:
            servers_file: Путь к файлу с данными серверов
            logger: Экземпляр ServerLogger для логирования
        """
        self.servers_file = servers_file
        self.logger = logger

    def load_servers(self) -> List[Dict[str, Any]]:
        """Загрузка списка серверов из файла"""
        try:
            with open(self.servers_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {self.servers_file}: {e}")
            return []

    def save_servers(self, servers: List[Dict[str, Any]]) -> bool:
        """Сохранение списка серверов в файл"""
        try:
            with open(self.servers_file, "w") as f:
                json.dump(servers, f, indent=4)
            return True
        except IOError as e:
            self.logger.error(f"Failed to save to {self.servers_file}: {e}")
            return False


class ServerManager:
    """Класс для управления серверами"""

    def __init__(self, repository: ServerRepository, metrics: ConnectionMetrics):
        """
        Args:
            repository: Экземпляр ServerRepository
            metrics: Экземпляр ConnectionMetrics для сбора статистики
        """
        self.repository = repository
        self.metrics = metrics
        self.logger = repository.logger

    def register_server(self, server_data: Dict[str, Any]) -> bool:
        """Регистрация нового сервера"""
        try:
            servers = self.repository.load_servers()
            servers = [s for s in servers if s["ip"] != server_data["ip"]]
            servers.append(server_data)
            if self.repository.save_servers(servers):
                self.metrics.increment("register_success")
                return True
            self.metrics.increment("register_failed")
            return False
        except Exception as e:
            self.metrics.increment("register_error")
            self.logger.error(f"Registration error: {e}")
            return False

    def exclude_server(self, ip: str) -> bool:
        """Исключение сервера по IP"""
        try:
            servers = self.repository.load_servers()
            for s in servers:
                if s["ip"] == ip:
                    s["excluded"] = True
            if self.repository.save_servers(servers):
                self.metrics.increment("exclude_success")
                return True
            self.metrics.increment("exclude_failed")
            return False
        except Exception as e:
            self.metrics.increment("exclude_error")
            self.logger.error(f"Exclusion error: {e}")
            return False

    def include_server(self, ip: str) -> bool:
        """Включение сервера по IP"""
        try:
            servers = self.repository.load_servers()
            for s in servers:
                if s["ip"] == ip:
                    s.pop("excluded", None)
            if self.repository.save_servers(servers):
                self.metrics.increment("include_success")
                return True
            self.metrics.increment("include_failed")
            return False
        except Exception as e:
            self.metrics.increment("include_error")
            self.logger.error(f"Inclusion error: {e}")
            return False

    def get_servers(self, include_excluded: bool = False) -> List[Dict[str, Any]]:
        """Возвращает список серверов"""
        try:
            servers = self.repository.load_servers()
            if not include_excluded:
                servers = [s for s in servers if not s.get("excluded", False)]
            self.metrics.increment("get_servers_success")
            return servers
        except Exception as e:
            self.metrics.increment("get_servers_error")
            self.logger.error(f"Get servers error: {e}")
            return []


class ServerRequestHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов"""

    def __init__(self, manager: ServerManager, metrics: ConnectionMetrics, *args, **kwargs):
        self.manager = manager
        self.metrics = metrics
        self.logger = manager.logger
        super().__init__(*args, **kwargs)

    def handle(self):
        """Основной обработчик запроса с перехватом ошибок"""
        try:
            super().handle()
        except (ConnectionError, ValueError) as e:
            if "closed file" not in str(e):
                self.logger.error(f"Connection error: {e}")

    def _send_response(self, code: int, content: Optional[Dict] = None) -> None:
        """Отправление HTTP-ответа"""
        try:
            self.send_response(code)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            if content is None:
                content = {"status": "ok"}
            self.wfile.write(json.dumps(content).encode())
        except (ConnectionError, BrokenPipeError):
            self.metrics.increment("connection_closed_during_response")

    def do_GET(self) -> None:
        """Обрабатка GET-запросов"""
        try:
            if self.path.startswith("/api/servers/check"):
                try:
                    qs = parse_qs(urlparse(self.path).query)
                    ip = qs.get("ip", [None])[0]
                    port_str = qs.get("port", ["0"])[0]
                    try:
                        port = int(port_str)
                    except ValueError:
                        self._send_response(400, {"error": "Invalid port"})
                        return
                    url = f"http://{ip}:{port}/vnc.html"
                    reachable = False
                    try:
                        req = urllib.request.Request(url, method="GET")
                        with urllib.request.urlopen(req, timeout=1.5) as response:
                            if response.status == 200:
                                reachable = True
                    except Exception as e:
                        self.logger.warning(f"HTTP check failed for {ip}:{port} → {e}")
                        reachable = False
                    self._send_response(200, {"ip": ip, "reachable": reachable})
                except Exception as e:
                    self.logger.error(f"Error in /check handler: {e}")
                    self._send_response(500, {"error": str(e)})
                return

            if self.path.startswith("/api/servers"):
                query = urlparse(self.path).query
                params = parse_qs(query)
                include_excluded = params.get('include_excluded', ['false'])[0].lower() == 'true'
                servers = self.manager.get_servers(include_excluded)
                self._send_response(200, servers)
            else:
                self._send_response(404, {"error": "Not Found"})

        except Exception as e:
            self.logger.error(f"GET request error: {e}")
            self._send_response(500, {"error": str(e)})

    def do_POST(self) -> None:
        """Обрабатка POST-запросов"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = json.loads(self.rfile.read(content_length))

            if self.path == "/api/servers/register":
                success = self.manager.register_server(post_data)
                self._send_response(200 if success else 500)
            elif self.path == "/api/servers/exclude":
                success = self.manager.exclude_server(post_data["ip"])
                self._send_response(200 if success else 500)
            elif self.path == "/api/servers/include":
                success = self.manager.include_server(post_data["ip"])
                self._send_response(200 if success else 500)
            else:
                self._send_response(404, {"error": "Not Found"})
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON: {e}")
            self._send_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            self.logger.error(f"POST request error: {e}")
            self._send_response(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


class ServerHTTPServer(HTTPServer):
    """HTTP сервер с поддержкой метрик и логирования"""

    def __init__(self, manager: ServerManager, metrics: ConnectionMetrics, server_address: tuple, RequestHandlerClass):
        """
        Args:
            manager: Экземпляр ServerManager
            metrics: Экземпляр ConnectionMetrics
            server_address: (host, port) для привязки сервера
            RequestHandlerClass: Класс для обработки запросов
        """
        self.manager = manager
        self.metrics = metrics
        self.logger = manager.logger
        super().__init__(server_address, RequestHandlerClass)

    def finish_request(self, request, client_address) -> None:
        """Создание обработчика запросов с обработкой ошибок"""
        try:
            handler = ServerRequestHandler(
                manager=self.manager,
                metrics=self.metrics,
                request=request,
                client_address=client_address,
                server=self
            )
            handler.handle()
        except Exception as e:
            self.metrics.increment("handler_creation_error")
            self.logger.error(f"Handler creation error: {e}")

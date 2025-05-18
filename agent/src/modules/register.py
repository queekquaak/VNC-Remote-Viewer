import requests
from typing import Dict, Optional, Union


class ServerRegister:
    """Регистратор агента на сервере с логированием ошибок"""

    def __init__(self, logger):
        self.logger = logger

    def register_server(
            self,
            server_api_url: str,
            ip: str,
            username: str,
            websockify_port: Optional[int] = None,
            auth_token: Optional[str] = None
    ) -> Optional[Union[Dict, str]]:
        self.logger.info(
            f"Registering to {server_api_url} - "
            f"User: {username}, "
            f"WS: {websockify_port or 'N/A'}"
        )

        data = {
            'ip': ip,
            'username': username,
            'websockify_port': websockify_port
        }

        headers = {}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        try:
            response = requests.post(server_api_url, json=data, headers=headers, timeout=10)
            response.raise_for_status()

            if not response.text.strip():
                self.logger.info("Server registered successfully (empty response)")
                return {'status': 'success', 'message': 'empty response'}

            try:
                return response.json()
            except ValueError:
                self.logger.warning(f"Non-JSON response: {response.text}")
                return response.text

        except requests.Timeout:
            self.logger.error("Registration timeout")
        except requests.HTTPError as e:
            self.logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        except requests.RequestException as e:
            self.logger.error(f"Network error: {str(e)}")
        except Exception:
            self.logger.exception("Unexpected registration error")

        return None

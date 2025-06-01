import requests
import time
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import json

@dataclass
class StackSpotConfig:
    """Configuração para o cliente StackSpot"""
    base_url: str
    client_id: str
    client_secret: str
    auth_url: str = 'https://idm.stackspot.com/stackspot-freemium/oidc/oauth/token'
    max_retries: int = 30
    retry_interval: int = 5
    request_delay: float = 0.0  # Delay em segundos antes de cada requisição

class StackSpotError(Exception):
    """Exceção base para erros do StackSpot"""
    pass

class AuthenticationError(StackSpotError):
    """Erro de autenticação"""
    pass

class APIError(StackSpotError):
    """Erro na chamada da API"""
    pass

class StackSpotClient:
    """Cliente base para interagir com a API do StackSpot"""
    
    def __init__(self, config: StackSpotConfig):
        self.config = config
        self._token: Optional[str] = None
    
    def authenticate(self) -> bool:
        """Realiza autenticação na API"""
        try:
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret
            }
            
            response = requests.post(
                self.config.auth_url,
                data=auth_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Credenciais inválidas")
            
            response.raise_for_status()
            data = response.json()
            self._token = data.get('access_token')
            
            if not self._token:
                raise AuthenticationError("Token não encontrado na resposta")
                
            return True
            
        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'text'):
                raise APIError(f"Erro na requisição: {e.response.text}")
            raise APIError(f"Erro na requisição: {str(e)}")
        except json.JSONDecodeError:
            raise APIError("Resposta inválida do servidor")
        except Exception as e:
            raise APIError(f"Erro inesperado: {str(e)}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Método auxiliar para fazer requisições HTTP"""
        if not self._token:
            if not self.authenticate():
                raise AuthenticationError("Falha na autenticação")

        # Aplica o delay se configurado
        if self.config.request_delay > 0:
            time.sleep(self.config.request_delay)

        headers = {
            'Authorization': f'Bearer {self._token}',
            'Content-Type': 'application/json',
            'User-Agent': 'insomnia/11.0.1'
        }
        headers.update(kwargs.pop('headers', {}))

        response = requests.request(
            method,
            f"{self.config.base_url}/{endpoint}",
            headers=headers,
            **kwargs
        )

        if response.status_code == 401:
            self._token = None
            if not self.authenticate():
                raise AuthenticationError("Falha na autenticação")
            # Tenta novamente com o novo token
            headers['Authorization'] = f'Bearer {self._token}'
            response = requests.request(
                method,
                f"{self.config.base_url}/{endpoint}",
                headers=headers,
                **kwargs
            )

        return response 
import requests
import time
import os
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import json

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

@dataclass
class StackSpotConfig:
    """
    Configuração para o cliente StackSpot.
    Pode ser instanciada diretamente ou via variáveis de ambiente usando from_env().
    Variáveis suportadas:
      - STACKSPOT_BASE_URL
      - STACKSPOT_CLIENT_ID
      - STACKSPOT_CLIENT_SECRET
      - STACKSPOT_AUTH_URL
      - STACKSPOT_MAX_RETRIES
      - STACKSPOT_RETRY_INTERVAL
      - STACKSPOT_REQUEST_DELAY
    """
    base_url: str
    client_id: str
    client_secret: str
    auth_url: str = 'https://idm.stackspot.com/stackspot-freemium/oidc/oauth/token'
    max_retries: int = 30
    retry_interval: int = 5
    request_delay: float = 0.0  # Delay em segundos antes de cada requisição

    @classmethod
    def from_env(cls, load_dotenv_file: bool = True) -> 'StackSpotConfig':
        """
        Cria uma instância de StackSpotConfig lendo variáveis de ambiente.
        Se load_dotenv_file=True e python-dotenv estiver instalado, carrega variáveis do .env automaticamente.
        """
        if load_dotenv_file and load_dotenv:
            load_dotenv()
        def _get_env(key, default=None, required=False, cast=str):
            value = os.getenv(key, default)
            if required and value is None:
                raise ValueError(f"Variável de ambiente obrigatória não encontrada: {key}")
            if value is not None and cast != str:
                try:
                    value = cast(value)
                except Exception:
                    raise ValueError(f"Não foi possível converter {key} para {cast}")
            return value
        return cls(
            base_url=_get_env('STACKSPOT_BASE_URL', required=True),
            client_id=_get_env('STACKSPOT_CLIENT_ID', required=True),
            client_secret=_get_env('STACKSPOT_CLIENT_SECRET', required=True),
            auth_url=_get_env('STACKSPOT_AUTH_URL', 'https://idm.stackspot.com/stackspot-freemium/oidc/oauth/token'),
            max_retries=_get_env('STACKSPOT_MAX_RETRIES', 30, cast=int),
            retry_interval=_get_env('STACKSPOT_RETRY_INTERVAL', 5, cast=int),
            request_delay=_get_env('STACKSPOT_REQUEST_DELAY', 0.0, cast=float),
        )

class StackSpotError(Exception):
    """Exceção base para erros do StackSpot"""
    pass

class AuthenticationError(StackSpotError):
    """Erro de autenticação"""
    pass

class APIError(StackSpotError):
    """Erro na chamada da API"""
    pass

class ValidationError(StackSpotError, ValueError):
    """Validation error for input or configuration"""
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
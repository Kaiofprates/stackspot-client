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
    """Cliente para interagir com a API do StackSpot"""
    
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
    
    def execute_command(self, 
                       command_path: str, 
                       input_data: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Executa um comando na API"""
        if not self._token:
            if not self.authenticate():
                return None
        
        try:
            payload = {'input_data': input_data}
            
            response = requests.post(
                f"{self.config.base_url}/{command_path}",
                headers={
                    'Authorization': f'Bearer {self._token}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'insomnia/11.0.1'
                },
                json=payload
            )
            
            if response.status_code == 401:
                self._token = None
                if not self.authenticate():
                    return None
                # Tenta novamente com o novo token
                response = requests.post(
                    f"{self.config.base_url}/{command_path}",
                    headers={
                        'Authorization': f'Bearer {self._token}',
                        'Content-Type': 'application/json',
                        'User-Agent': 'insomnia/11.0.1'
                    },
                    json=payload
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Se a resposta for uma string, assume que é o ID de execução
            if isinstance(data, str):
                return data
            
            # Se for um dicionário, procura pelo ID de execução
            execution_id = data.get('executionId')
            if not execution_id:
                raise APIError("ID de execução não encontrado na resposta")
            
            return execution_id
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                raise APIError(f"Erro na requisição: {e.response.text}")
            raise APIError(f"Erro na requisição: {str(e)}")
        except json.JSONDecodeError as e:
            raise APIError("Resposta inválida do servidor")
        except Exception as e:
            raise APIError(f"Erro inesperado: {str(e)}")
    
    def get_execution_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Obtém o resultado de uma execução"""
        if not self._token:
            if not self.authenticate():
                return None
        
        for attempt in range(self.config.max_retries):
            try:
                response = requests.get(
                    f"{self.config.base_url}/v1/quick-commands/callback/{execution_id}",
                    headers={
                        'Authorization': f'Bearer {self._token}',
                        'Content-Type': 'application/json',
                        'User-Agent': 'insomnia/11.0.1'
                    }
                )
                
                if response.status_code == 401:
                    self._token = None
                    if not self.authenticate():
                        return None
                    continue
                
                response.raise_for_status()
                result = response.json()
                
                # Se o resultado for uma string, retorna como resposta
                if isinstance(result, str):
                    return {'answer': result}
                
                # Se não for um dicionário, tenta converter
                if not isinstance(result, dict):
                    if isinstance(result, (list, tuple)):
                        return {'answer': str(result)}
                    return {'answer': str(result)}
                
                # Verifica se tem status direto
                if 'status' in result:
                    if result['status'] == 'COMPLETED':
                        return result
                    elif result['status'] == 'FAILED':
                        error_msg = result.get('error', 'Erro desconhecido')
                        raise APIError(f"Execução falhou: {error_msg}")
                
                # Verifica o progresso
                progress = result.get('progress', {})
                if isinstance(progress, dict):
                    status = progress.get('status')
                    if status == 'COMPLETE':
                        return result
                    elif status == 'FAILED':
                        error_msg = progress.get('error', 'Erro desconhecido')
                        raise APIError(f"Execução falhou: {error_msg}")
                    elif status == 'RUNNING':
                        time.sleep(self.config.retry_interval)
                    else:
                        return result
                
            except requests.exceptions.RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    raise APIError(f"Erro na requisição: {e.response.text}")
                raise APIError(f"Erro na requisição: {str(e)}")
            except json.JSONDecodeError as e:
                raise APIError("Resposta inválida do servidor")
            except Exception as e:
                raise APIError(f"Erro inesperado: {str(e)}")
        
        raise APIError("Tempo limite excedido ao aguardar resultado") 
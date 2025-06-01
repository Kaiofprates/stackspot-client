import json
import time
from typing import Dict, Any, Optional, Union

import requests
from .client import StackSpotClient, APIError

class QuickCommands(StackSpotClient):
    """Cliente para interagir com comandos rápidos do StackSpot"""

    def execute_command(self, 
                       command_path: str, 
                       input_data: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Executa um comando na API"""
        try:
            payload = {'input_data': input_data}
            
            response = self._make_request(
                'POST',
                command_path,
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
        for attempt in range(self.config.max_retries):
            try:
                response = self._make_request(
                    'GET',
                    f"v1/quick-commands/callback/{execution_id}"
                )
                
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
                    if status == 'COMPLETED':
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
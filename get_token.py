import requests
from typing import Optional, Dict, Any
import time

def get_token(
    client_id: str,
    client_secret: str,
    grant_type: str = 'client_credentials'
) -> Optional[Dict[str, Any]]:
    """
    Obtém um token de acesso usando as credenciais fornecidas.
    
    Args:
        client_id (str): ID do cliente
        client_secret (str): Segredo do cliente
        grant_type (str, optional): Tipo de concessão. Padrão é 'client_credentials'
    
    Returns:
        Optional[Dict[str, Any]]: Resposta da API em formato JSON ou None em caso de erro
    """
    url = 'https://idm.stackspot.com/stackspot-freemium/oidc/oauth/token'
    
    # Dados do payload
    payload = {
        'client_id': client_id,
        'grant_type': grant_type,
        'client_secret': client_secret
    }
    
    # Headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        # Fazendo a requisição POST
        response = requests.post(url, data=payload, headers=headers)
        
        # Verificando se a requisição foi bem sucedida
        response.raise_for_status()
        
        # Retornando o JSON da resposta
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None

def analyze_resume(token: str, input_data: str) -> Optional[Dict[str, Any]]:
    """
    Analisa um currículo usando o serviço de análise de currículos.
    
    Args:
        token (str): Token de acesso obtido da função get_token
        input_data (str): Dados do currículo para análise
    
    Returns:
        Optional[Dict[str, Any]]: Resposta da API em formato JSON ou None em caso de erro
    """
    url = 'https://genai-code-buddy-api.stackspot.com/v1/quick-commands/create-execution/resume-analyzer'
    
    # Headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'insomnia/11.0.1'
    }
    
    # Dados do payload
    payload = {
        'input_data': input_data
    }
    
    try:
        # Fazendo a requisição POST	
        response = requests.post(url, headers=headers, json=payload)
        
        # Verificando se a requisição foi bem sucedida
        response.raise_for_status()
        
        # Retornando o JSON da resposta
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None

def get_analysis_result(token: str, execution_id: str, max_retries: int = 12, retry_interval: int = 5) -> Optional[Dict[str, Any]]:
    """
    Obtém o resultado da análise de currículo usando o ID de execução.
    Implementa um sistema de retry que aguarda até que a análise seja concluída.
    
    Args:
        token (str): Token de acesso obtido da função get_token
        execution_id (str): ID da execução retornado pela função analyze_resume
        max_retries (int): Número máximo de tentativas (padrão: 12 = 1 minuto)
        retry_interval (int): Intervalo em segundos entre as tentativas (padrão: 5)
    
    Returns:
        Optional[Dict[str, Any]]: Resposta da API em formato JSON ou None em caso de erro
    """
    url = f'https://genai-code-buddy-api.stackspot.com/v1/quick-commands/callback/{execution_id}'
    
    # Headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'insomnia/11.0.1'
    }
    
    start_time = time.time()
    last_percentage = -1
    
    for attempt in range(max_retries):
        try:
            # Fazendo a requisição GET
            response = requests.get(url, headers=headers)
            
            # Verificando se a requisição foi bem sucedida
            response.raise_for_status()
            
            # Obtendo o resultado
            result = response.json()
            
            # Verificando se o resultado tem a estrutura esperada
            if not isinstance(result, dict):
                print(f"\n❌ Resposta inválida na tentativa {attempt + 1}")
                return None
            
            # Verificando o status da análise
            progress = result.get('progress', {})
            status = progress.get('status')
            percentage = progress.get('execution_percentage', 0)
            
            # Só atualiza o progresso se mudou
            if percentage != last_percentage:
                print(f"\r⏳ Aguardando conclusão da análise... {percentage:.1f}% concluído", end='')
                last_percentage = percentage
            
            if status == 'COMPLETE':
                print(f"\n✅ Análise concluída após {attempt + 1} tentativas")
                return result
            elif status == 'FAILED':
                print(f"\n❌ Análise falhou após {attempt + 1} tentativas")
                return result
            elif status not in ['RUNNING', 'PENDING']:
                print(f"\n❌ Status desconhecido: {status}")
                return result
            
            # Verifica se excedeu o tempo máximo (2 minutos)
            if time.time() - start_time > 120:
                print("\n❌ Tempo máximo de espera excedido (2 minutos)")
                return result
            
            # Aguarda o intervalo definido antes da próxima tentativa
            time.sleep(retry_interval)
                
        except requests.exceptions.RequestException as e:
            print(f"\nErro na requisição (tentativa {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            else:
                return None
    
    print("\n❌ Número máximo de tentativas excedido")
    return None 
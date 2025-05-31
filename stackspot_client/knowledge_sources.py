from typing import Dict, Any, Literal, Optional
from .client import StackSpotClient
import requests
import os
from requests.exceptions import RequestException, Timeout, ProxyError


class KnowledgeSources:
    """Classe para gerenciar fontes de conhecimento no StackSpot"""
    
    def __init__(self, client: StackSpotClient):
        self.client = client
        self.endpoint = "knowledge-sources"

    def create_ks(
        self,
        slug: str,
        name: str,
        description: str,
        type: Literal["api", "snippet", "custom"]
    ) -> Dict[str, Any]:
        """
        Cria uma nova fonte de conhecimento no StackSpot.

        Args:
            slug (str): Identificador único da fonte de conhecimento
            name (str): Nome da fonte de conhecimento
            description (str): Descrição da fonte de conhecimento
            type (Literal["api", "snippet", "custom"]): Tipo da fonte de conhecimento

        Returns:
            Dict[str, Any]: Resposta da API contendo os detalhes da fonte de conhecimento criada

        Raises:
            APIError: Se houver erro na chamada da API
        """
        payload = {
            "slug": slug,
            "name": name,
            "description": description,
            "type": type
        }

        response = self.client._make_request(
            method="POST",
            endpoint=self.endpoint,
            json=payload
        )

        response.raise_for_status()
        return response.json()

    def upload_file(self, file_path: str, ks_slug: str) -> Optional[str]:
        """
        Faz upload de um arquivo para uma fonte de conhecimento.

        Args:
            file_path (str): Caminho do arquivo a ser enviado
            ks_slug (str): Slug da fonte de conhecimento

        Returns:
            Optional[str]: ID do upload do arquivo se bem sucedido, None caso contrário

        Raises:
            FileNotFoundError: Se o arquivo não for encontrado
            RequestException: Se houver erro na requisição
            Timeout: Se a requisição exceder o tempo limite
            ProxyError: Se houver erro com o proxy
        """
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'rb') as file:
                upload_data = self.client._make_request(
                    method="POST",
                    endpoint="file-upload/form",
                    json={
                        "file_name": file_name,
                        "target_id": ks_slug,
                        "target_type": "KNOWLEDGE_SOURCE",
                        "expiration": 600
                    }
                )
                upload_data.raise_for_status()
                upload_data = upload_data.json()
                file_upload_id = upload_data['id']
                files = {
                    'key': (None, upload_data['form']['key']),
                    'x-amz-algorithm': (None, upload_data['form']['x-amz-algorithm']),
                    'x-amz-credential': (None, upload_data['form']['x-amz-credential']),
                    'x-amz-date': (None, upload_data['form']['x-amz-date']),
                    'x-amz-security-token': (None, upload_data['form']['x-amz-security-token']),
                    'policy': (None, upload_data['form']['policy']),
                    'x-amz-signature': (None, upload_data['form']['x-amz-signature']),
                    'file': (file_name, file)
                }
                response = requests.post(upload_data['url'], files=files, timeout=10)
                response.raise_for_status()
                return file_upload_id
        except (FileNotFoundError, RequestException, Timeout, ProxyError) as e:
            print(f"error: {e}")
            return None
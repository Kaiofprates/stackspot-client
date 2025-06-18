from typing import Dict, Any, Literal, Optional
from .client import StackSpotClient, ValidationError
import requests
import os
from requests.exceptions import RequestException, Timeout, ProxyError
from docling.document_converter import DocumentConverter
from rich.console import Console
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn


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
        Uploads a file to a knowledge source. Only supports .json, .yml, .yaml, .md, .txt, .pdf, .zip (zip must contain only supported types). Max size: 10MB.

        Args:
            file_path (str): Path to the file to upload
            ks_slug (str): Knowledge source slug

        Returns:
            Optional[str]: Uploaded file ID if successful, None otherwise

        Raises:
            FileNotFoundError: If the file is not found
            ValidationError: If the file format or size is invalid
            RequestException: If there is a request error
            Timeout: If the request times out
            ProxyError: If there is a proxy error
        """
        SUPPORTED_EXTENSIONS = {'.json', '.yml', '.yaml', '.md', '.txt', '.pdf', '.zip'}
        MAX_SIZE_MB = 10
        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValidationError(f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > MAX_SIZE_MB:
            raise ValidationError(f"File too large: {size_mb:.2f}MB. Maximum allowed is {MAX_SIZE_MB}MB.")
        # If zip, check contents
        if ext == '.zip':
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as z:
                for info in z.infolist():
                    inner_ext = os.path.splitext(info.filename)[1].lower()
                    if inner_ext and inner_ext not in SUPPORTED_EXTENSIONS - {'.zip'}:
                        raise ValidationError(f".zip contains unsupported file: {info.filename} ({inner_ext})")
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
        except (FileNotFoundError, RequestException, Timeout, ProxyError, ValidationError) as e:
            print(f"error: {e}")
            return None

    def upload_file_with_docling(self, file_path: str, ks_slug: str) -> Optional[str]:
        """
        Faz upload de um arquivo para uma fonte de conhecimento, processando o arquivo local com Docling
        e gerando um markdown (.md) antes do upload.

        Args:
            file_path (str): Caminho do arquivo local a ser processado
            ks_slug (str): Slug da fonte de conhecimento

        Returns:
            Optional[str]: ID do upload do arquivo se bem sucedido, None caso contrário
        """
        console = Console()
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                # Extrair o conteúdo markdown do arquivo local usando docling
                task = progress.add_task(
                    "[cyan]Extraindo conteúdo do arquivo, essa operação pode levar alguns minutos...",
                    total=None
                )
                converter = DocumentConverter()
                result = converter.convert(file_path)
                markdown_content = result.document.export_to_markdown()
                progress.update(task, completed=True)

                # Criar um arquivo temporário com o conteúdo markdown
                task = progress.add_task(
                    "[green]Preparando arquivo para upload...",
                    total=None
                )
                temp_file_path = f"temp_{ks_slug}.md"
                with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(markdown_content)
                progress.update(task, completed=True)

                # Usar a função upload_file existente para fazer o upload
                task = progress.add_task(
                    "[yellow]Fazendo upload do arquivo...",
                    total=None
                )
                upload_id = self.upload_file(temp_file_path, ks_slug)
                progress.update(task, completed=True)

                # Remover o arquivo temporário
                task = progress.add_task(
                    "[blue]Limpando arquivos temporários...",
                    total=None
                )
                os.remove(temp_file_path)
                progress.update(task, completed=True)

                console.print("[bold green]✓ Upload concluído com sucesso![/bold green]")
                return upload_id

        except (RequestException, Timeout, ProxyError) as e:
            console.print(f"[bold red]Erro durante o upload: {e}[/bold red]")
            return None
        except Exception as e:
            console.print(f"[bold red]Erro inesperado: {e}[/bold red]")
            return None

    def upload_from_url(self, url: str, ks_slug: str) -> Optional[str]:
        """
        Faz upload do conteúdo markdown extraído de uma URL para uma fonte de conhecimento.

        Args:
            url (str): URL do conteúdo a ser extraído
            ks_slug (str): Slug da fonte de conhecimento

        Returns:
            Optional[str]: ID do upload do arquivo se bem sucedido, None caso contrário

        Raises:
            RequestException: Se houver erro na requisição
            Timeout: Se a requisição exceder o tempo limite
            ProxyError: Se houver erro com o proxy
        """
        console = Console()
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                # Extrair o conteúdo markdown da URL usando docling
                task = progress.add_task(
                    "[cyan]Extraindo conteúdo da URL, essa operação pode levar alguns minutos...", 
                    total=None
                )
                converter = DocumentConverter()
                result = converter.convert(url)
                markdown_content = result.document.export_to_markdown()
                progress.update(task, completed=True)
                
                # Criar um arquivo temporário com o conteúdo markdown
                task = progress.add_task(
                    "[green]Preparando arquivo para upload...", 
                    total=None
                )
                temp_file_path = f"temp_{ks_slug}.md"
                with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(markdown_content)
                progress.update(task, completed=True)

                # Usar a função upload_file existente para fazer o upload
                task = progress.add_task(
                    "[yellow]Fazendo upload do arquivo...", 
                    total=None
                )
                upload_id = self.upload_file(temp_file_path, ks_slug)
                progress.update(task, completed=True)

                # Remover o arquivo temporário
                task = progress.add_task(
                    "[blue]Limpando arquivos temporários...", 
                    total=None
                )
                os.remove(temp_file_path)
                progress.update(task, completed=True)

                console.print("[bold green]✓ Upload concluído com sucesso![/bold green]")
                return upload_id

        except (RequestException, Timeout, ProxyError) as e:
            console.print(f"[bold red]Erro durante o upload: {e}[/bold red]")
            return None

    def delete_all_files(self, ks_slug: str) -> bool:
        """
        Deleta todos os arquivos de uma fonte de conhecimento específica.

        Args:
            ks_slug (str): Slug da fonte de conhecimento

        Returns:
            bool: True se a operação foi bem sucedida, False caso contrário

        Raises:
            RequestException: Se houver erro na requisição
            Timeout: Se a requisição exceder o tempo limite
            ProxyError: Se houver erro com o proxy
        """
        console = Console()
        try:
            response = self.client._make_request(
                method="DELETE",
                endpoint=f"{self.endpoint}/{ks_slug}/objects"
            )
            response.raise_for_status()
            console.print("[bold green]✓ Todos os arquivos foram deletados com sucesso![/bold green]")
            return True
        except (RequestException, Timeout, ProxyError) as e:
            console.print(f"[bold red]Erro ao deletar os arquivos: {e}[/bold red]")
            return False
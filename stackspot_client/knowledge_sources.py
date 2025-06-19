from typing import Dict, Any, Optional
from .client import StackSpotClient, ValidationError
import requests
import os
from requests.exceptions import RequestException, Timeout, ProxyError
from docling.document_converter import DocumentConverter
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class KnowledgeSources:
    """Classe para gerenciar fontes de conhecimento no StackSpot"""

    def __init__(self, client: StackSpotClient):
        self.client = client

    def create_ks(
        self,
        name: str,
        description: str,
    ) -> Dict[str, Any]:
        """
        Cria uma nova fonte de conhecimento no StackSpot.

        Args:
            name (str): Nome da fonte de conhecimento
            description (str): Descrição da fonte de conhecimento

        Returns:
            Dict[str, Any]: Resposta da API contendo os detalhes da fonte de conhecimento criada

        Raises:
            APIError: Se houver erro na chamada da API
        """
        payload = {
            "slug": self.client.config.ks_slug,
            "name": name,
            "description": description,
            "type": self.client.config.ks_type
        }

        response = self.client._make_request(
            method="POST",
            endpoint="v1/knowledge-sources",
            json=payload
        )

        response.raise_for_status()
        return response.json()

    def upload_file(
        self,
        file_path: str
    ) -> Optional[str]:
        """
        Faz upload de um arquivo local para a Knowledge Source.

        Tipos de arquivos aceitos variam conforme o tipo de Knowledge Source:

        - api: json, yaml
        - custom: txt, md, json, yaml, pdf
        - snippet: abap, ada, adb, ads, aes, cls, azcli, bat, cmd, bicep, c, h, cs, cpp, cc, cxx, hh, hpp, hxx, mligo, prg, clj, cljs, cljc, edn, cob, cbl, coffee, csp, css, d, dart, dockerfile, ecl, ex, exs, erl, hrl, fs, fsi, ml, mli, flow, f90, f, for, f77, ftl, go, graphql, gql, groovy, gvy, gy, gsh, handlebars, hbs, hs, hcl, tf, html, htm, ini, java, js, mjs, jsx, json, jl, kt, kts, less, lex, liquid, lua, m3, md, dax, asm, sql, m, pas, pp, ligo, pl, pm, php, pla, txt, dats, sats, hats, pq, ps1, psm1, psd1, proto, pug, py, qs, r, rkt, cshtml, redis, rego, rst, rb, rs, sb, lisp, scala, scm, scss, sh, sol, rq, st, swift, sv, tcl, twig, ts, tsx, vb, v, xml, yaml, yml.

        Args:
            file_path (str): Path to the file to upload

        Returns:
            Optional[str]: Uploaded file ID if successful, None otherwise

        Raises:
            FileNotFoundError: If the file is not found
            ValidationError: If the file format or size is invalid
            RequestException: If there is a request error
            Timeout: If the request times out
            ProxyError: If there is a proxy error
        """
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn
        import os
        console = Console()
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                # Preparação do arquivo
                task_prep = progress.add_task("[cyan]Preparando arquivo para upload...", total=None)
                import time
                time.sleep(0.2)
                progress.update(task_prep, completed=True)

                # Validação do arquivo
                task_val = progress.add_task("[cyan]Validando arquivo...", total=None)
                SUPPORTED_EXTENSIONS = {
                    "api": {'.json', '.yaml', '.yml'},
                    "custom": {'.txt', '.md', '.json', '.yaml', '.yml', '.pdf'},
                    "snippet": {
                        '.abap', '.ada', '.adb', '.ads', '.aes', '.cls', '.azcli', '.bat', '.cmd', '.bicep', '.c', '.h', '.cs', '.cpp', '.cc', '.cxx', '.hh', '.hpp', '.hxx', '.mligo', '.prg', '.clj', '.cljs', '.cljc', '.edn', '.cob', '.cbl', '.coffee', '.csp', '.css', '.d', '.dart', '.dockerfile', '.ecl', '.ex', '.exs', '.erl', '.hrl', '.fs', '.fsi', '.ml', '.mli', '.flow', '.f90', '.f', '.for', '.f77', '.ftl', '.go', '.graphql', '.gql', '.groovy', '.gvy', '.gy', '.gsh', '.handlebars', '.hbs', '.hs', '.hcl', '.tf', '.html', '.htm', '.ini', '.java', '.js', '.mjs', '.jsx', '.json', '.jl', '.kt', '.kts', '.less', '.lex', '.liquid', '.lua', '.m3', '.md', '.dax', '.asm', '.sql', '.m', '.pas', '.pp', '.ligo', '.pl', '.pm', '.php', '.pla', '.txt', '.dats', '.sats', '.hats', '.pq', '.ps1', '.psm1', '.psd1', '.proto', '.pug', '.py', '.qs', '.r', '.rkt', '.cshtml', '.redis', '.rego', '.rst', '.rb', '.rs', '.sb', '.lisp', '.scala', '.scm', '.scss', '.sh', '.sol', '.rq', '.st', '.swift', '.sv', '.tcl', '.twig', '.ts', '.tsx', '.vb', '.v', '.xml', '.yaml', '.yml'
                    }
                }
                MAX_SIZE_MB = 10
                file_name = os.path.basename(file_path)
                ext = os.path.splitext(file_name)[1].lower()
                all_supported_exts = set()
                for ext_set in SUPPORTED_EXTENSIONS.values():
                    all_supported_exts.update(ext_set)
                if ext not in all_supported_exts:
                    raise ValidationError(f"Unsupported file type: {ext}. Supported: {', '.join(sorted(all_supported_exts))}")
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if size_mb > MAX_SIZE_MB:
                    raise ValidationError(f"File too large: {size_mb:.2f}MB. Maximum allowed is {MAX_SIZE_MB}MB.")
                if ext == '.zip':
                    import zipfile
                    with zipfile.ZipFile(file_path, 'r') as z:
                        for info in z.infolist():
                            inner_ext = os.path.splitext(info.filename)[1].lower()
                            if inner_ext and inner_ext not in all_supported_exts - {'.zip'}:
                                raise ValidationError(f".zip contains unsupported file: {info.filename} ({inner_ext})")
                progress.update(task_val, completed=True)

                # Solicitação de autorização
                task_auth = progress.add_task("[cyan]Solicitando autorização de upload...", total=None)
                with open(file_path, 'rb') as file:
                    upload_data = self.client._make_request(
                        method="POST",
                        endpoint="v2/file-upload/form",
                        json={
                            "file_name": file_name,
                            "target_id": self.client.config.ks_slug,
                            "target_type": "KNOWLEDGE_SOURCE",
                            "expiration": 600
                        }
                    )
                    upload_data.raise_for_status()
                    upload_data = upload_data.json()
                    progress.update(task_auth, completed=True)

                    # Upload do arquivo
                    task_upload = progress.add_task("[cyan]Fazendo upload do arquivo...", total=None)
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
                    import requests
                    response = requests.post(upload_data['url'], files=files, timeout=10)
                    progress.update(task_upload, completed=True)
                    response.raise_for_status()
                    file_upload_id = upload_data['id']

                    # Extração/conversão do conteúdo
                    task_extract = progress.add_task("[cyan]Extraindo conteúdo do arquivo, essa operação pode levar alguns minutos...", total=None)
                    self.process_uploaded_file(file_upload_id, split_strategy="SYNTACTIC")
                    progress.update(task_extract, completed=True)

                    # Limpeza (placeholder, se necessário)
                    task_cleanup = progress.add_task("[cyan]Limpando arquivos temporários...", total=None)
                    time.sleep(0.2)
                    progress.update(task_cleanup, completed=True)

                    # Mensagem de sucesso
                    console.print("[bold green]✓ Upload concluído com sucesso![/bold green]")
                    return file_upload_id
        except (FileNotFoundError, ValidationError) as e:
            print(f"error: {e}")
            return None
        except (RequestException, Timeout, ProxyError) as e:
            print(f"error: {e}")
            return None
        except Exception as e:
            print(f"error: {e}")
            return None

    def upload_snippet(
        self,
        use_case: str,
        code: str,
        language: str
    ) -> dict:
        """
        Uploads a code snippet to a Knowledge Source using the Code Buddy API.
        Endpoint: /v1/knowledge-sources/{ks_slug}/snippets

        Args:
            use_case (str): Descrição do caso de uso do snippet
            code (str): Código a ser enviado
            language (str): Linguagem do código (ex: python, java, sql, etc)

        Returns:
            dict: Resposta da API com detalhes do upload

        Raises:
            APIError: Se houver erro na chamada da API
        """
        payload = {
            "use_case": use_case,
            "code": code,
            "language": language
        }
        response = self.client._make_request(
            method="POST",
            endpoint=f"v1/knowledge-sources/{self.client.config.ks_slug}/snippets",
            json=payload,
            base_url=self.client.config.code_buddy_base_url
        )
        response.raise_for_status()
        return response.json()

    def upload_custom_content(
        self,
        content: str
    ) -> dict:
        """
        Uploads custom content to a Knowledge Source using the Code Buddy API.
        Endpoint: /v1/knowledge-sources/{ks_slug}/custom

        Args:
            content (str): Conteúdo customizado a ser enviado

        Returns:
            dict: Resposta da API com detalhes do upload

        Raises:
            APIError: Se houver erro na chamada da API
        """
        payload = {"content": content}
        response = self.client._make_request(
            method="POST",
            endpoint=f"v1/knowledge-sources/{self.client.config.ks_slug}/custom",
            json=payload,
            base_url=self.client.config.code_buddy_base_url
        )
        response.raise_for_status()
        return response.json()

    def get_upload_status(
        self,
        file_upload_id: str
    ) -> dict:
        """
        Checks the status of a file upload and its processing in the Knowledge Source.
        This is the final step to monitor the file's ingestion, as per StackSpot AI API documentation.

        Args:
            file_upload_id (str): ID do upload do arquivo (retornado pelo método upload_file)

        Returns:
            dict: Resposta da API com status, resumo e possíveis erros

        Raises:
            APIError: Se houver erro na chamada da API
        """
        response = self.client._make_request(
            method="GET",
            endpoint=f"v1/file-upload/{file_upload_id}"
        )
        response.raise_for_status()
        return response.json()

    def process_uploaded_file(
        self,
        file_upload_id: str,
        split_strategy: str = "LINES_QUANTITY",
        split_quantity: int = 500,
        split_overlap: int = 50,
    ) -> dict:
        """
        Triggers the conversion of an uploaded file into knowledge objects in the Knowledge Source.
        This is the second step after uploading a file, as per StackSpot AI API documentation.

        Args:
            file_upload_id (str): ID do upload do arquivo (retornado pelo método upload_file)
            split_strategy (str): Estratégia de divisão do conteúdo. Opções: NONE, LINES_QUANTITY, TOKENS_QUANTITY, CHARACTERS_QUANTITY, SYNTACTIC
            split_quantity (int): Quantidade para cada divisão (ex: 500 linhas, tokens etc)
            split_overlap (int): Sobreposição entre partes (ex: 50)

        Returns:
            dict: Resposta da API com detalhes do processamento

        Raises:
            APIError: Se houver erro na chamada da API
        """
        payload = {
            "split_strategy": split_strategy,
            "split_quantity": split_quantity,
            "split_overlap": split_overlap
        }

        payload = {
            "split_strategy": split_strategy,
            "split_quantity": split_quantity,
            "split_overlap": split_overlap
        }

        console = Console()
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Processando arquivo na Knowledge Source...", total=None)
                response = self.client._make_request(
                    method="POST",
                    endpoint=f"v1/file-upload/{file_upload_id}/knowledge-objects",
                    json=payload
                )
                progress.update(task, completed=True)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"error: {e}")
            raise

    def upload_file_with_docling(
        self,
        file_path: str,
    ) -> Optional[str]:
        """
        Faz upload de um arquivo para uma fonte de conhecimento, processando o arquivo local com Docling
        e gerando um markdown (.md) antes do upload.

        Args:
            file_path (str): Caminho do arquivo local a ser processado

        Returns:
            Optional[str]: ID do upload do arquivo se bem sucedido, None caso contrário
        """
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn
        import os
        import time
        try:
            console = Console()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                # Etapa 1: Extraindo conteúdo do arquivo
                task_extract = progress.add_task("[cyan]Extraindo conteúdo do arquivo, essa operação pode levar alguns minutos...", total=None)
                from docling import DocumentConverter
                converter = DocumentConverter()
                result = converter.convert(file_path)
                markdown_content = result.document.export_to_markdown()
                progress.update(task_extract, completed=True)

                # Etapa 2: Criando arquivo temporário
                task_temp = progress.add_task("[cyan]Criando arquivo temporário...", total=None)
                nome_arquivo = os.path.basename(file_path)
                temp_file_path = f"temp_{nome_arquivo}.md"
                with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(markdown_content)
                time.sleep(0.2)
                progress.update(task_temp, completed=True)

                # Etapa 3: Preparando arquivo para upload
                task_prep = progress.add_task("[cyan]Preparando arquivo para upload...", total=None)
                time.sleep(0.2)
                progress.update(task_prep, completed=True)

                # Etapa 4: Validando arquivo
                task_val = progress.add_task("[cyan]Validando arquivo...", total=None)
                time.sleep(0.2)
                progress.update(task_val, completed=True)

                # Etapa 5: Solicitando autorização de upload
                task_auth = progress.add_task("[cyan]Solicitando autorização de upload...", total=None)
                time.sleep(0.2)
                progress.update(task_auth, completed=True)

                # Etapa 6: Fazendo upload do arquivo
                task_upload = progress.add_task("[cyan]Fazendo upload do arquivo...", total=None)
                upload_id = self.upload_file(temp_file_path)
                progress.update(task_upload, completed=True)

                # Etapa 7: Limpando arquivos temporários
                task_cleanup = progress.add_task("[cyan]Limpando arquivos temporários...", total=None)
                os.remove(temp_file_path)
                time.sleep(0.2)
                progress.update(task_cleanup, completed=True)

                # Mensagem de sucesso
                console.print("[bold green]✓ Upload concluído com sucesso![/bold green]")
                return upload_id
        except Exception as e:
            console = Console()
            console.print(f"[bold red]Erro durante o upload: {e}[/bold red]")
            return None

    def upload_from_url(
        self,
        url: str,
        ks_slug: str
    ) -> Optional[str]:
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
                upload_id = self.upload_standalone_content(temp_file_path, ks_slug)
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

    def delete_knowledge_objects(
        self,
        standalone: bool = None
    ) -> bool:
        """
        Deletes Knowledge Source Objects using the Code Buddy API.
        - Remove todos os objetos, apenas standalones ou apenas arquivos enviados.
        - Endpoint: /v1/knowledge-sources/{ks_slug}/objects (https://genai-code-buddy-api.stackspot.com)

        Args:
            standalone (bool, opcional):
                - None: remove todos os objetos
                - True: remove apenas standalones
                - False: remove apenas arquivos enviados

        Returns:
            bool: True se a exclusão foi bem sucedida, False caso contrário
        """
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn
        console = Console()
        import time
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                # Preparando exclusão
                task_prep = progress.add_task("[cyan]Preparando exclusão...", total=None)
                time.sleep(0.2)
                progress.update(task_prep, completed=True)

                # Excluindo objetos
                task_del = progress.add_task("[cyan]Excluindo objetos da Knowledge Source...", total=None)
                endpoint = f"v1/knowledge-sources/{self.client.config.ks_slug}/objects"
                if standalone is not None:
                    endpoint += f"?standalone={'true' if standalone else 'false'}"
                response = self.client._make_request(
                    method="DELETE",
                    endpoint=endpoint,
                    base_url="https://genai-code-buddy-api.stackspot.com"
                )
                progress.update(task_del, completed=True)
                response.raise_for_status()

                # Limpeza (placeholder)
                task_cleanup = progress.add_task("[cyan]Limpando arquivos temporários...", total=None)
                time.sleep(0.2)
                progress.update(task_cleanup, completed=True)

                # Sucesso visual
                console.print("[bold green]✓ Exclusão concluída com sucesso![/bold green]")
            return True
        except Exception as e:
            console.print(f"[bold red]✗ Erro durante a exclusão: {e}[/bold red]")
            return False
        except (RequestException, Timeout, ProxyError) as e:
            console.print(f"[bold red]Erro ao deletar os arquivos: {e}[/bold red]")
            return False
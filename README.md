# StackSpot Client Python

Cliente Python oficial para interagir com a API do StackSpot.

## Instalação

```bash
pip install stackspot-client
```

## Uso Básico

```python
from stackspot_client import StackSpotConfig, StackSpotClient

# Configuração do cliente
config = StackSpotConfig(
    base_url='https://genai-code-buddy-api.stackspot.com',
    auth_url='https://idm.stackspot.com/stackspot-freemium/oidc/oauth/token',
    client_id='seu_client_id',
    client_secret='seu_client_secret'
)

# Criando instância do cliente
client = StackSpotClient(config)

# Executando um comando
execution_id = client.execute_command('seu_comando', {'dados': 'exemplo'})

# Obtendo o resultado
result = client.get_execution_result(execution_id)
print(result)
```

## Recursos

- Autenticação automática
- Tratamento de erros
- Retry automático em caso de falhas
- Suporte a diferentes tipos de respostas

## Documentação

Para mais informações sobre a API do StackSpot, consulte a [documentação oficial](https://docs.stackspot.com).

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes. 
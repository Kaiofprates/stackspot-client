# Exemplo de uso
from stackspot_client.client import StackSpotConfig, StackSpotClient
from stackspot_client.knowledge_sources import KnowledgeSources

# Configurar o cliente
config = StackSpotConfig(
    base_url="https://data-integration-api.stackspot.com/v1",
    client_id="",
    client_secret=""
)

# Criar instância do cliente
client = StackSpotClient(config)

# Criar instância do KnowledgeSources
ks = KnowledgeSources(client)

# Fazer o upload do arquivo
ks = KnowledgeSources(client)
upload_id = ks.upload_from_url("https://arxiv.org/pdf/2408.09869", "my-cli-ks-v3")

if upload_id:
    print(f"Upload realizado com sucesso! ID: {upload_id}")
else:
    print("Erro ao realizar o upload")
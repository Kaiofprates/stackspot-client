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

# Criar uma nova fonte de conhecimento
response = ks.create_ks(
    slug="my-cli-ks-v3",
    name="my-cli-ks-v3",
    description="KS created via CLI using form v2",
    type="snippet"  # ou "snippet" ou "custom"
)

print(response)
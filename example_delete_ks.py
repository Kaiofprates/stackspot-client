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


ks = KnowledgeSources(client)
success = ks.delete_all_files("my-cli-ks-v3")

if success:
    print(f"Upload realizado com sucesso! ID: {success}")
else:
    print("Erro ao realizar o upload")
from stackspot_client import StackSpotConfig, QuickCommands, APIError



class TesteStackSpotAPI:
    """Classe para testar a integração com a API do StackSpot"""

    def __init__(self):
        # Configuração do cliente
        self.config = StackSpotConfig(
            base_url='https://genai-code-buddy-api.stackspot.com',
            auth_url='https://idm.stackspot.com/stackspot-freemium/oidc/oauth/token',
            client_id='',
            client_secret='', 
            request_delay=1.0
        )
        self.quick_commands = QuickCommands(self.config)

    def testar_execucao_comando(self, command_path: str, input_data: dict) -> dict:
        """
        Testa a execução de um comando na API
        
        Args:
            command_path: Caminho do comando a ser executado
            input_data: Dados de entrada para o comando
            
        Returns:
            dict: Resultado da execução do comando
        """
        try:
            # Executa o comando
            execution_id = self.quick_commands.execute_command(command_path, input_data)
            print(f"Comando iniciado com ID: {execution_id}")

            # Obtém o resultado da execução
            result = self.quick_commands.get_execution_result(execution_id)

            if result: 
                print("\n📋 Resultado:")
                print("=" * 50)
                print(result['steps'][0]['step_result']['answer'])
                print("=" * 50)
                
            else:
                print("Nenhum resultado encontrado")
            
            return result

        except APIError as e:
            print(f"Erro na execução do comando: {str(e)}")
            raise

    def testar_comando_simples(self):
        """Testa um comando simples com dados básicos"""
        command_path = "/v1/quick-commands/create-execution/ola-mundo-"
        input_data = {
            "command": "echo",
            "parameters": {
                "message": "Olá, StackSpot!"
            }
        }
        
        return self.testar_execucao_comando(command_path, input_data)

    def testar_comando_complexo(self):
        """Testa um comando mais complexo com múltiplos parâmetros"""
        command_path = "/v1/quick-commands/create-execution/ola-mundo-"
        input_data = {
            "command": "processar-dados",
            "parameters": {
                "arquivo": "dados.csv",
                "formato": "json",
                "opcoes": {
                    "separador": ",",
                    "encoding": "utf-8",
                    "ignorar_cabecalho": True
                }
            }
        }
        
        return self.testar_execucao_comando(command_path, input_data)

def main():
    """Função principal para executar os testes"""
    try:
        # Cria instância da classe de teste
        teste = TesteStackSpotAPI()
        
        # Executa teste com comando simples
        #print("\nTestando comando simples:")
        #resultado_simples = teste.testar_comando_simples()
        
        # Executa teste com comando complexo
        print("\nTestando comando complexo:")
        resultado_complexo = teste.testar_comando_complexo()
        
    except Exception as e:
        print(f"Erro durante os testes: {str(e)}")

if __name__ == "__main__":
    main() 
from stackspot_client import StackSpotConfig, StackSpotError
from resume_analyzer import ResumeAnalyzer

def main():
    # Configuração do cliente
    config = StackSpotConfig(
        base_url='https://genai-code-buddy-api.stackspot.com',
        auth_url='https://idm.stackspot.com/stackspot-freemium/oidc/oauth/token',
        client_id='ff6049b1-1da9-40c3-bba7-51c6d095871a',
        client_secret='HYxaZ7txm6xPItvc34587drgWvh7z8K4s72JGsNHIqAA6Ug5dOYJ7DE188Yq76Mq'
    )
    
    try:
        print("\n=== Configuração ===")
        print(f"URL Base: {config.base_url}")
        print(f"URL Auth: {config.auth_url}")
        print(f"Client ID: {config.client_id[:10]}...")
        
        # Criando instância do analisador de currículos
        analyzer = ResumeAnalyzer(config)
        
        # Exemplo de currículo para teste
        sample_resume = """
        Nome: João Silva
        Experiência: 5 anos como desenvolvedor Python
        Formação: Ciência da Computação
        Habilidades: Python, Django, Flask, SQL
        """
        
        print("\n=== Iniciando Análise de Currículo ===")
        result = analyzer.analyze(sample_resume)
        
        if result:
            print("\n📋 Resultado da Análise:")
            print("=" * 50)
            if isinstance(result, dict) and 'answer' in result:
                print(result['answer'])
            else:
                print(result)
            print("=" * 50)
        else:
            print("❌ Falha na análise do currículo")
            
    except StackSpotError as e:
        print(f"\n❌ Erro: {str(e)}")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        import traceback
        print("\nDetalhes do erro:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 
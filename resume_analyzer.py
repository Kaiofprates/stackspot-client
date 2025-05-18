from typing import Dict, Any, Optional
from stackspot_client import StackSpotClient, StackSpotConfig, StackSpotError

class ResumeAnalyzer:
    """Cliente específico para análise de currículos"""
    
    def __init__(self, config: StackSpotConfig):
        self.client = StackSpotClient(config)
        self.config = config
        self.endpoint = 'v1/quick-commands/create-execution/resume-analyzer'
    
    def analyze(self, resume_text: str) -> Optional[Dict[str, Any]]:
        """Analisa um currículo"""
        try:
            execution_id = self.client.execute_command(
                self.endpoint,
                resume_text
            )
            
            if execution_id:
                return self.client.get_execution_result(execution_id)
            return None
            
        except StackSpotError as e:
            print(f"Erro na análise: {str(e)}")
            return None 
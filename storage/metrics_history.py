"""
Armazenamento de métricas históricas para o Dashboard S10+.

Este módulo implementa o armazenamento e recuperação de dados históricos
para visualização de tendências e gráficos.
"""

from collections import deque
from datetime import datetime

from config.settings import Config

class MetricsHistory:
    """Gerencia o histórico de métricas coletadas."""
    
    def __init__(self, max_size=None):
        """Inicializa o armazenamento de histórico.
        
        Args:
            max_size: Tamanho máximo do histórico (usa Config.HISTORY_SIZE se None)
        """
        self.max_size = max_size or Config.HISTORY_SIZE
        self.history = deque(maxlen=self.max_size)
    
    def add_data_point(self, data):
        """Adiciona um novo ponto de dados ao histórico.
        
        Args:
            data: Dicionário com dados a serem armazenados
        """
        # Adiciona timestamp se não existir
        if "timestamp" not in data:
            from datetime import datetime
            data["timestamp"] = datetime.now().isoformat()
        
        # Adiciona ao histórico
        self.history.append(data)
    
    def get_history(self):
        """Retorna todo o histórico de dados.
        
        Returns:
            Lista com todos os pontos de dados armazenados
        """
        return list(self.history)
    
    def get_metric_history(self, metric_path):
        """Retorna histórico de uma métrica específica.
        
        Args:
            metric_path: Caminho para a métrica (ex: "cpu.usage")
            
        Returns:
            Lista de dicionários com timestamp e valor da métrica
        """
        result = []
        for point in self.history:
            value = self._get_nested_value(point, metric_path)
            if value is not None:
                result.append({
                    "timestamp": point.get("timestamp"),
                    "value": value
                })
        return result
    
    def _get_nested_value(self, data, path):
        """Obtém valor aninhado a partir de um caminho.
        
        Args:
            data: Dicionário com dados
            path: Caminho para o valor (ex: "hardware.cpu.usage")
            
        Returns:
            Valor encontrado ou None se não existir
        """
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current

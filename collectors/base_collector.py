"""
Classe base para todos os coletores de dados.

Esta classe define a interface e funcionalidades comuns para
todos os coletores de informações do sistema.
"""

import time
import logging
from datetime import datetime

from config.settings import Config
from core.utils import run_command, get_timestamp

class BaseCollector:
    """Classe base para todos os coletores de dados."""
    
    def __init__(self):
        """Inicializa o coletor."""
        self.last_collection_time = 0
        self.last_data = None
        self.name = self.__class__.__name__
    
    def collect(self):
        """Coleta dados se o intervalo de coleta foi atingido.
        
        Returns:
            Dados coletados ou dados em cache se o intervalo não foi atingido
        """
        current_time = time.time()
        if (current_time - self.last_collection_time) >= Config.COLLECTION_INTERVAL:
            try:
                logging.debug(f"Coletando dados de {self.name}")
                self.last_data = self._collect_data()
                self.last_collection_time = current_time
            except Exception as e:
                logging.error(f"Erro na coleta de dados de {self.name}: {e}")
                # Retorna dados anteriores ou erro
                if not self.last_data:
                    self.last_data = {
                        "error": str(e),
                        "timestamp": get_timestamp()
                    }
        
        return self.last_data
    
    def _collect_data(self):
        """Método a ser implementado pelas subclasses.
        
        Returns:
            Dicionário com dados coletados
            
        Raises:
            NotImplementedError: Se não for implementado pela subclasse
        """
        raise NotImplementedError("Subclasses devem implementar este método")
    
    def run_command(self, command, timeout=None, shell=False):
        """Executa comando shell com timeout.
        
        Args:
            command: Comando a ser executado (lista ou string)
            timeout: Timeout em segundos (usa Config.COMMAND_TIMEOUT se None)
            shell: Se True, executa comando em shell
            
        Returns:
            String com a saída do comando
        """
        return run_command(command, timeout, shell)

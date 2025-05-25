"""
Configurações centralizadas para o Dashboard S10+.

Este módulo contém todas as configurações do sistema, facilitando
ajustes sem necessidade de modificar o código-fonte.
"""

import os

class Config:
    """Classe de configuração centralizada."""
    
    # Configurações do servidor
    SERVER_PORT = 8080
    SERVER_HOST = "0.0.0.0"
    DEBUG = True
    
    # Caminhos de arquivos
    PID_FILE = os.path.expanduser("~/dashboard.pid")
    LOG_FILE = os.path.expanduser("~/dashboard.log")
    LOG_LEVEL = "INFO"
    
    # Configurações de coleta
    COLLECTION_INTERVAL = 5  # segundos
    HISTORY_SIZE = 60  # pontos de dados para histórico
    
    # Configurações de recursos
    MAX_PROCESSES = 50  # número máximo de processos a monitorar
    
    # Timeouts
    COMMAND_TIMEOUT = 3  # segundos para timeout de comandos
    
    # Diretórios
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATIC_DIR = os.path.join(BASE_DIR, "ui", "static")
    TEMPLATE_DIR = os.path.join(BASE_DIR, "ui", "templates")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    
    # Configurações de interface
    THEME = "dark"  # dark ou light
    REFRESH_INTERVAL = 5000  # milissegundos para atualização automática da UI

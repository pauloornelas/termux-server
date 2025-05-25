"""
Rotas e manipuladores da API para o Dashboard S10+.

Este módulo implementa as rotas da API e os manipuladores de requisições.
"""

import os
import json
import logging
from datetime import datetime

from core.server import BaseHandler
from collectors.system_collector import SystemCollector
from collectors.hardware_collector import HardwareCollector
from collectors.network_collector import NetworkCollector
from collectors.storage_collector import StorageCollector
from collectors.process_collector import ProcessCollector
from collectors.android_collector import AndroidCollector
from storage.metrics_history import MetricsHistory
from config.settings import Config

class ApiHandler(BaseHandler):
    """Manipulador para rotas da API."""
    
    def __init__(self, *args, **kwargs):
        """Inicializa o manipulador da API."""
        # Inicializa coletores
        self.collectors = {
            "system": SystemCollector(),
            "hardware": HardwareCollector(),
            "network": NetworkCollector(),
            "storage": StorageCollector(),
            "process": ProcessCollector(),
            "android": AndroidCollector()
        }
        
        # Inicializa armazenamento de histórico
        self.metrics_history = MetricsHistory()
        
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Processa requisições GET."""
        try:
            if self.path == '/api/status':
                self.handle_status()
            elif self.path.startswith('/api/'):
                self.handle_api_route()
            elif self.path.startswith('/static/'):
                self.handle_static_file()
            else:
                self.handle_static_content()
        except Exception as e:
            self.handle_error(e)
    
    def handle_status(self):
        """Manipula rota /api/status."""
        try:
            data = {}
            
            # Coleta dados de todos os coletores
            for name, collector in self.collectors.items():
                data[name] = collector.collect()
            
            # Armazena dados no histórico
            self.metrics_history.add_data_point(data)
            
            # Adiciona timestamp global
            data["timestamp"] = self.get_timestamp()
            
            # Envia resposta
            self.send_json_response(data)
        except Exception as e:
            self.handle_error(e)
    
    def handle_api_route(self):
        """Manipula rotas específicas da API."""
        # Extrai o nome da rota: /api/route -> route
        route = self.path.split('/')[2]
        
        if route in self.collectors:
            # Rota para coletor específico
            data = {
                route: self.collectors[route].collect(),
                "timestamp": self.get_timestamp()
            }
            self.send_json_response(data)
        elif route == "history":
            # Rota para obter dados históricos
            self.send_json_response(self.metrics_history.get_history())
        elif route == "metric" and len(self.path.split('/')) >= 4:
            # Rota para obter histórico de uma métrica específica
            # Formato: /api/metric/cpu.usage
            metric_path = self.path.split('/')[3]
            self.send_json_response(self.metrics_history.get_metric_history(metric_path))
        else:
            self.send_json_response({"error": "Rota não encontrada"}, 404)
    
    def handle_static_file(self):
        """Manipula requisições para arquivos estáticos."""
        # Extrai o caminho do arquivo: /static/css/style.css -> css/style.css
        file_path = self.path[8:]  # Remove '/static/'
        full_path = os.path.join(Config.STATIC_DIR, file_path)
        
        # Verifica se o arquivo existe
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            self.send_error(404, "Arquivo não encontrado")
            return
        
        # Determina o tipo de conteúdo
        content_type = self._get_content_type(full_path)
        
        # Serve o arquivo
        self.serve_static_file(full_path, content_type)
    
    def handle_static_content(self):
        """Manipula requisições para conteúdo HTML."""
        # Serve o template padrão
        self.send_html_response()
    
    def _get_content_type(self, file_path):
        """Determina o tipo de conteúdo com base na extensão do arquivo."""
        ext = os.path.splitext(file_path)[1].lower()
        
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon'
        }
        
        return content_types.get(ext, 'application/octet-stream')

"""
Servidor HTTP base para o Dashboard S10+.

Este módulo implementa o servidor HTTP base com tratamento de erros aprimorado.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import traceback
import logging
import os
import time
from datetime import datetime

from config.settings import Config

class BaseHandler(BaseHTTPRequestHandler):
    """Manipulador base para todas as requisições HTTP."""
    
    def log_message(self, format, *args):
        """Sobrescreve o log padrão para usar o sistema de logging."""
        if Config.DEBUG:
            logging.info(f"{self.address_string()} - {format % args}")
    
    def send_json_response(self, data, status=200):
        """Envia resposta JSON padronizada.
        
        Args:
            data: Dados a serem enviados como JSON
            status: Código de status HTTP (padrão: 200)
        """
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_html_response(self, content=None, status=200):
        """Envia resposta HTML.
        
        Args:
            content: Conteúdo HTML a ser enviado
            status: Código de status HTTP (padrão: 200)
        """
        self.send_response(status)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        if content:
            self.wfile.write(content.encode('utf-8'))
        else:
            # Se não houver conteúdo específico, carrega o template padrão
            self.serve_default_template()
    
    def serve_default_template(self):
        """Serve o template HTML padrão."""
        template_path = os.path.join(Config.TEMPLATE_DIR, "index.html")
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.wfile.write(content.encode('utf-8'))
        else:
            # Fallback para template embutido
            self.wfile.write(b"<html><body><h1>Dashboard S10+</h1><p>Template não encontrado.</p></body></html>")
    
    def serve_static_file(self, file_path, content_type):
        """Serve um arquivo estático.
        
        Args:
            file_path: Caminho completo para o arquivo
            content_type: Tipo de conteúdo MIME
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            logging.error(f"Erro ao servir arquivo estático {file_path}: {e}")
            self.send_error(404, f"Arquivo não encontrado: {os.path.basename(file_path)}")
    
    def handle_error(self, e):
        """Manipula erros de forma padronizada.
        
        Args:
            e: Exceção capturada
        """
        error_data = {
            "error": str(e),
            "traceback": traceback.format_exc() if Config.DEBUG else None,
            "timestamp": self.get_timestamp()
        }
        logging.error(f"Erro: {str(e)}")
        if Config.DEBUG:
            logging.error(traceback.format_exc())
        self.send_json_response(error_data, 500)
    
    def get_timestamp(self):
        """Retorna timestamp atual em formato ISO."""
        return datetime.now().isoformat()


class DashboardServer:
    """Servidor principal do dashboard."""
    
    def __init__(self, handler_class, port=None):
        """Inicializa o servidor.
        
        Args:
            handler_class: Classe manipuladora de requisições
            port: Porta do servidor (opcional, usa Config.SERVER_PORT se não especificada)
        """
        self.port = port or Config.SERVER_PORT
        self.handler = handler_class
        self.httpd = None
    
    def start(self):
        """Inicia o servidor HTTP."""
        try:
            self.httpd = HTTPServer((Config.SERVER_HOST, self.port), self.handler)
            logging.info(f"Servidor iniciado em {Config.SERVER_HOST}:{self.port}")
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("Servidor interrompido pelo usuário")
        except Exception as e:
            logging.error(f"Erro ao iniciar servidor: {e}")
            raise
        finally:
            if self.httpd:
                self.httpd.server_close()
                logging.info("Servidor encerrado")

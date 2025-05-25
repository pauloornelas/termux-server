"""
Ponto de entrada principal para o Dashboard S10+.

Este script inicia um servidor web que fornece uma interface para
monitoramento de recursos do sistema em um dispositivo Galaxy S10+
rodando Termux.
"""

#!/data/data/com.termux/files/usr/bin/python3

import os
import sys
import signal
import logging
import argparse
from datetime import datetime

# Configuração de logging
from config.settings import Config

def setup_logging():
    """Configura o sistema de logging."""
    log_file = os.path.expanduser(Config.LOG_FILE)
    log_level = getattr(logging, Config.LOG_LEVEL)
    
    logging.basicConfig(
        filename=log_file,
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Adiciona log para console se em modo debug
    if Config.DEBUG:
        console = logging.StreamHandler()
        console.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

def write_pid_file():
    """Escreve o PID atual no arquivo de PID."""
    pid_file = os.path.expanduser(Config.PID_FILE)
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    logging.info(f"PID {os.getpid()} gravado em {pid_file}")

def remove_pid_file():
    """Remove o arquivo de PID."""
    pid_file = os.path.expanduser(Config.PID_FILE)
    if os.path.exists(pid_file):
        os.remove(pid_file)
        logging.info(f"Arquivo PID {pid_file} removido")

def signal_handler(sig, frame):
    """Manipula sinais para encerramento limpo."""
    logging.info(f"Sinal recebido: {sig}")
    remove_pid_file()
    sys.exit(0)

def parse_arguments():
    """Processa argumentos de linha de comando."""
    parser = argparse.ArgumentParser(description='Dashboard para servidor S10+')
    parser.add_argument('--port', type=int, help='Porta do servidor HTTP')
    parser.add_argument('--debug', action='store_true', help='Ativa modo debug')
    return parser.parse_args()

def main():
    """Função principal."""
    # Processa argumentos
    args = parse_arguments()
    
    # Sobrescreve configurações com argumentos
    if args.port:
        Config.SERVER_PORT = args.port
    if args.debug:
        Config.DEBUG = True
    
    # Configura logging
    setup_logging()
    
    # Registra manipuladores de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Escreve arquivo PID
    write_pid_file()
    
    try:
        # Importa e inicia o servidor
        from api.routes import ApiHandler
        from core.server import DashboardServer
        
        logging.info(f"Iniciando Dashboard S10+ na porta {Config.SERVER_PORT}")
        server = DashboardServer(ApiHandler, Config.SERVER_PORT)
        server.start()
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        import traceback
        logging.error(traceback.format_exc())
    finally:
        remove_pid_file()

if __name__ == "__main__":
    main()

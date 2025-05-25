"""
Utilitários gerais para o Dashboard S10+.

Este módulo contém funções utilitárias usadas em todo o sistema.
"""

import subprocess
import logging
import os
import re
import json
from datetime import datetime
from config.settings import Config

def run_command(command, timeout=None, shell=False):
    """Executa comando shell com timeout e tratamento de erros.
    
    Args:
        command: Comando a ser executado (lista ou string)
        timeout: Timeout em segundos (usa Config.COMMAND_TIMEOUT se None)
        shell: Se True, executa comando em shell
        
    Returns:
        String com a saída do comando
        
    Raises:
        TimeoutError: Se o comando exceder o timeout
        subprocess.SubprocessError: Se o comando falhar
    """
    timeout = timeout or Config.COMMAND_TIMEOUT
    
    try:
        # Se command for string e shell=False, converte para lista
        if isinstance(command, str) and not shell:
            command = command.split()
            
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell
        )
        
        if result.returncode != 0:
            logging.warning(f"Comando retornou código {result.returncode}: {command}")
            logging.debug(f"Stderr: {result.stderr}")
            
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        logging.warning(f"Timeout ao executar comando: {command}")
        raise TimeoutError(f"Comando excedeu timeout de {timeout}s: {command}")
    except Exception as e:
        logging.error(f"Erro ao executar comando {command}: {e}")
        raise

def format_bytes(bytes_value, precision=2):
    """Formata bytes para unidades legíveis (KB, MB, GB).
    
    Args:
        bytes_value: Valor em bytes
        precision: Número de casas decimais
        
    Returns:
        String formatada com unidade apropriada
    """
    if bytes_value < 0:
        return "0 B"
        
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    
    # Converte para float se for string
    if isinstance(bytes_value, str):
        try:
            bytes_value = float(bytes_value)
        except ValueError:
            return "0 B"
    
    # Determina a unidade apropriada
    unit_index = 0
    while bytes_value >= 1024 and unit_index < len(units) - 1:
        bytes_value /= 1024
        unit_index += 1
        
    return f"{bytes_value:.{precision}f} {units[unit_index]}"

def safe_parse_json(json_str):
    """Analisa JSON com tratamento de erros.
    
    Args:
        json_str: String JSON a ser analisada
        
    Returns:
        Objeto Python ou None se falhar
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logging.warning(f"Erro ao analisar JSON: {e}")
        return None

def get_timestamp():
    """Retorna timestamp atual em formato ISO."""
    return datetime.now().isoformat()

def extract_value_with_regex(text, pattern, default=None, group=1):
    """Extrai valor usando expressão regular.
    
    Args:
        text: Texto a ser analisado
        pattern: Padrão regex
        default: Valor padrão se não encontrar
        group: Grupo de captura a ser retornado
        
    Returns:
        Valor extraído ou default
    """
    match = re.search(pattern, text)
    if match:
        return match.group(group)
    return default

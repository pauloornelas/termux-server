"""
Coletor de informações do sistema.

Este módulo implementa a coleta de informações básicas do sistema,
como uptime, hostname e versão do Python.
"""

import os
import re
from datetime import datetime

from collectors.base_collector import BaseCollector
from core.utils import get_timestamp

class SystemCollector(BaseCollector):
    """Coleta informações gerais do sistema."""
    
    def _collect_data(self):
        """Coleta dados do sistema.
        
        Returns:
            Dicionário com informações do sistema
        """
        data = {
            "timestamp": get_timestamp(),
            "uptime": self._get_uptime(),
            "hostname": self._get_hostname(),
            "python_version": self._get_python_version(),
            "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_dir": os.getcwd()
        }
        return data
    
    def _get_uptime(self):
        """Obtém o uptime do sistema.
        
        Returns:
            String com o uptime formatado
        """
        try:
            # Primeira tentativa: comando uptime
            return self.run_command(['uptime'])
        except:
            try:
                # Segunda tentativa: ler /proc/uptime
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.read().split()[0])
                    
                # Converter para formato legível
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                
                # Formatar
                parts = []
                if days > 0:
                    parts.append(f"{days} dia{'s' if days != 1 else ''}")
                if hours > 0 or days > 0:
                    parts.append(f"{hours} hora{'s' if hours != 1 else ''}")
                parts.append(f"{minutes} minuto{'s' if minutes != 1 else ''}")
                
                return "up " + ", ".join(parts)
            except:
                return "Desconhecido"
    
    def _get_hostname(self):
        """Obtém o nome do host.
        
        Returns:
            String com o nome do host
        """
        try:
            return self.run_command(['hostname'])
        except:
            import socket
            try:
                return socket.gethostname()
            except:
                return "Desconhecido"
    
    def _get_python_version(self):
        """Obtém a versão do Python.
        
        Returns:
            String com a versão do Python
        """
        try:
            return self.run_command(['python', '--version'])
        except:
            import sys
            return sys.version.split()[0]

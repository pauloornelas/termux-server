"""
Coletor de informações de processos.

Este módulo implementa a coleta de informações sobre processos
em execução no sistema.
"""

import os
import re
from datetime import datetime

from collectors.base_collector import BaseCollector
from core.utils import get_timestamp, format_bytes
from config.settings import Config

class ProcessCollector(BaseCollector):
    """Coleta informações sobre processos em execução."""
    
    def _collect_data(self):
        """Coleta dados de processos.
        
        Returns:
            Dicionário com informações de processos
        """
        data = {
            "timestamp": get_timestamp(),
            "summary": self._get_process_summary(),
            "top_processes": self._get_top_processes()
        }
        
        return data
    
    def _get_process_summary(self):
        """Obtém resumo dos processos em execução.
        
        Returns:
            Dicionário com resumo dos processos
        """
        summary = {
            "total": 0,
            "running": 0,
            "sleeping": 0,
            "stopped": 0,
            "zombie": 0
        }
        
        try:
            # Tenta via ps
            output = self.run_command(['ps', 'aux'])
            
            # Conta total de processos
            lines = output.split('\n')
            if len(lines) > 1:  # Ignora cabeçalho
                summary["total"] = len(lines) - 1
                
                # Conta por estado
                for line in lines[1:]:
                    if not line.strip():
                        continue
                        
                    parts = line.split()
                    if len(parts) >= 8:
                        state = parts[7]
                        if state == 'R':
                            summary["running"] += 1
                        elif state == 'S':
                            summary["sleeping"] += 1
                        elif state == 'T':
                            summary["stopped"] += 1
                        elif state == 'Z':
                            summary["zombie"] += 1
        except Exception:
            # Tenta via /proc
            try:
                if os.path.exists('/proc'):
                    # Conta diretórios numéricos em /proc (PIDs)
                    pids = [d for d in os.listdir('/proc') if d.isdigit()]
                    summary["total"] = len(pids)
                    
                    # Conta por estado
                    for pid in pids:
                        try:
                            status_path = f'/proc/{pid}/status'
                            if os.path.exists(status_path):
                                with open(status_path, 'r') as f:
                                    status_content = f.read()
                                    
                                state_match = re.search(r'State:\s+(\w)', status_content)
                                if state_match:
                                    state = state_match.group(1)
                                    if state == 'R':
                                        summary["running"] += 1
                                    elif state == 'S':
                                        summary["sleeping"] += 1
                                    elif state == 'T':
                                        summary["stopped"] += 1
                                    elif state == 'Z':
                                        summary["zombie"] += 1
                        except Exception:
                            continue
            except Exception:
                pass
                
        return summary
    
    def _get_top_processes(self):
        """Obtém lista dos processos que mais consomem recursos.
        
        Returns:
            Lista de dicionários com informações dos processos
        """
        processes = []
        max_processes = Config.MAX_PROCESSES
        
        try:
            # Tenta via ps
            output = self.run_command(['ps', 'aux', '--sort=-pcpu,-pmem'])
            
            lines = output.split('\n')
            if len(lines) > 1:  # Ignora cabeçalho
                for line in lines[1:max_processes+1]:
                    if not line.strip():
                        continue
                        
                    parts = line.split(None, 10)  # Limita a 11 partes para manter comando completo
                    if len(parts) >= 11:
                        process = {
                            "user": parts[0],
                            "pid": int(parts[1]),
                            "cpu_percent": float(parts[2]),
                            "mem_percent": float(parts[3]),
                            "vsz": format_bytes(int(parts[4]) * 1024),
                            "rss": format_bytes(int(parts[5]) * 1024),
                            "tty": parts[6],
                            "stat": parts[7],
                            "start": parts[8],
                            "time": parts[9],
                            "command": parts[10]
                        }
                        processes.append(process)
        except Exception:
            # Tenta via top
            try:
                output = self.run_command(['top', '-b', '-n', '1'])
                
                lines = output.split('\n')
                process_lines = False
                
                for line in lines:
                    if not line.strip():
                        continue
                        
                    # Identifica início da lista de processos
                    if 'PID' in line and 'USER' in line and 'COMMAND' in line:
                        process_lines = True
                        continue
                        
                    if process_lines and len(processes) < max_processes:
                        parts = line.split()
                        if len(parts) >= 12:
                            try:
                                process = {
                                    "pid": int(parts[0]),
                                    "user": parts[1],
                                    "cpu_percent": float(parts[8]),
                                    "mem_percent": float(parts[9]),
                                    "command": ' '.join(parts[11:])
                                }
                                processes.append(process)
                            except (ValueError, IndexError):
                                continue
            except Exception:
                pass
                
        return processes

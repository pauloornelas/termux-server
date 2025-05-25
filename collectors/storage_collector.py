"""
Coletor de informações de armazenamento.

Este módulo implementa a coleta de informações de armazenamento,
como uso de disco, partições e estatísticas de I/O.
"""

import os
import re
from datetime import datetime

from collectors.base_collector import BaseCollector
from core.utils import get_timestamp, format_bytes

class StorageCollector(BaseCollector):
    """Coleta informações de armazenamento do dispositivo."""
    
    def _collect_data(self):
        """Coleta dados de armazenamento.
        
        Returns:
            Dicionário com informações de armazenamento
        """
        data = {
            "timestamp": get_timestamp(),
            "disk_usage": self._get_disk_usage(),
            "partitions": self._get_partitions()
        }
        
        # Tenta obter estatísticas de I/O
        try:
            io_stats = self._get_io_stats()
            if io_stats:
                data["io_stats"] = io_stats
        except Exception:
            # Ignora silenciosamente se não conseguir obter
            pass
            
        return data
    
    def _get_disk_usage(self):
        """Obtém informações de uso de disco.
        
        Returns:
            Dicionário com informações de uso de disco
        """
        try:
            # Usa df para obter uso do diretório atual
            output = self.run_command(['df', '-h', '.'])
            
            lines = output.split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 5:
                    # Tenta extrair o número da porcentagem
                    percent_str = parts[4].rstrip('%')
                    try:
                        percent_num = float(percent_str)
                    except:
                        percent_num = 0
                        
                    return {
                        "total": parts[1],
                        "used": parts[2],
                        "free": parts[3],
                        "percent": parts[4],
                        "percent_num": percent_num,
                        "mount_point": parts[5] if len(parts) >= 6 else "/"
                    }
            
            raise Exception("Não foi possível analisar a saída do comando 'df'")
        except Exception as e:
            # Tenta método alternativo
            try:
                # Usa df com bytes para cálculos mais precisos
                output = self.run_command(['df', '-B1', '.'])
                
                lines = output.split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        total = int(parts[1])
                        used = int(parts[2])
                        free = int(parts[3])
                        percent = (used / total) * 100 if total > 0 else 0
                        
                        return {
                            "total": format_bytes(total),
                            "used": format_bytes(used),
                            "free": format_bytes(free),
                            "percent": f"{percent:.1f}%",
                            "percent_num": round(percent, 1),
                            "mount_point": parts[5] if len(parts) >= 6 else "/"
                        }
            except Exception:
                pass
                
            # Se tudo falhar
            return {
                "total": "Desconhecido", 
                "used": "Desconhecido", 
                "free": "Desconhecido",
                "percent": "0%", 
                "percent_num": 0
            }
    
    def _get_partitions(self):
        """Obtém informações sobre partições.
        
        Returns:
            Lista de dicionários com informações das partições
        """
        partitions = []
        
        try:
            # Usa df para listar todas as partições
            output = self.run_command(['df', '-h'])
            
            lines = output.split('\n')
            if len(lines) >= 2:
                for line in lines[1:]:  # Pula o cabeçalho
                    if not line.strip():
                        continue
                        
                    parts = line.split()
                    if len(parts) >= 6:
                        # Ignora sistemas de arquivos especiais
                        if parts[0].startswith('/dev/') or parts[0] in ['tmpfs', 'sdcard']:
                            # Tenta extrair o número da porcentagem
                            percent_str = parts[4].rstrip('%')
                            try:
                                percent_num = float(percent_str)
                            except:
                                percent_num = 0
                                
                            partition = {
                                "device": parts[0],
                                "total": parts[1],
                                "used": parts[2],
                                "free": parts[3],
                                "percent": parts[4],
                                "percent_num": percent_num,
                                "mount_point": parts[5]
                            }
                            partitions.append(partition)
        except Exception:
            # Tenta método alternativo via mount
            try:
                mount_output = self.run_command(['mount'])
                
                for line in mount_output.split('\n'):
                    if 'type ' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            device = parts[0]
                            mount_point = parts[2]
                            
                            # Ignora sistemas de arquivos especiais
                            if device.startswith('/dev/') or device in ['tmpfs', 'sdcard']:
                                # Tenta obter uso com df específico para este ponto de montagem
                                try:
                                    df_output = self.run_command(['df', '-h', mount_point])
                                    df_lines = df_output.split('\n')
                                    if len(df_lines) >= 2:
                                        df_parts = df_lines[1].split()
                                        if len(df_parts) >= 5:
                                            partition = {
                                                "device": device,
                                                "total": df_parts[1],
                                                "used": df_parts[2],
                                                "free": df_parts[3],
                                                "percent": df_parts[4],
                                                "percent_num": float(df_parts[4].rstrip('%')),
                                                "mount_point": mount_point
                                            }
                                            partitions.append(partition)
                                except Exception:
                                    # Se não conseguir obter uso, adiciona apenas informações básicas
                                    partition = {
                                        "device": device,
                                        "mount_point": mount_point
                                    }
                                    partitions.append(partition)
            except Exception:
                pass
                
        return partitions
    
    def _get_io_stats(self):
        """Obtém estatísticas de I/O.
        
        Returns:
            Dicionário com estatísticas de I/O ou None se não conseguir obter
        """
        try:
            # Tenta ler /proc/diskstats
            if os.path.exists('/proc/diskstats'):
                with open('/proc/diskstats', 'r') as f:
                    diskstats = f.readlines()
                
                io_stats = {}
                
                for line in diskstats:
                    parts = line.split()
                    if len(parts) >= 14:
                        # Filtra apenas dispositivos reais (ignora partições)
                        device = parts[2]
                        if re.match(r'^(sd[a-z]|mmcblk\d|dm-\d)$', device):
                            io_stats[device] = {
                                "reads": int(parts[3]),
                                "reads_merged": int(parts[4]),
                                "sectors_read": int(parts[5]),
                                "read_time_ms": int(parts[6]),
                                "writes": int(parts[7]),
                                "writes_merged": int(parts[8]),
                                "sectors_written": int(parts[9]),
                                "write_time_ms": int(parts[10]),
                                "io_in_progress": int(parts[11]),
                                "io_time_ms": int(parts[12]),
                                "weighted_io_time_ms": int(parts[13])
                            }
                
                return io_stats if io_stats else None
        except Exception:
            return None

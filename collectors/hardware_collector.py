"""
Coletor de informações de hardware.

Este módulo implementa a coleta de informações de hardware,
como CPU, memória e bateria.
"""

import os
import re
import json
from datetime import datetime

from collectors.base_collector import BaseCollector
from core.utils import get_timestamp, extract_value_with_regex, format_bytes

class HardwareCollector(BaseCollector):
    """Coleta informações de hardware do dispositivo."""
    
    def _collect_data(self):
        """Coleta dados de hardware.
        
        Returns:
            Dicionário com informações de hardware
        """
        data = {
            "timestamp": get_timestamp(),
            "cpu": self._get_cpu_info(),
            "memory": self._get_memory_info(),
            "battery": self._get_battery_info()
        }
        
        # Tenta obter informações de temperatura
        try:
            data["temperature"] = self._get_temperature_info()
        except Exception as e:
            # Ignora silenciosamente se não conseguir obter
            pass
            
        return data
    
    def _get_cpu_info(self):
        """Obtém informações detalhadas da CPU.
        
        Returns:
            Dicionário com informações da CPU
        """
        cpu_info = {
            "usage": self._get_cpu_usage(),
            "cores": self._get_cpu_cores(),
            "frequency": self._get_cpu_frequency()
        }
        return cpu_info
    
    def _get_cpu_usage(self):
        """Obtém o uso atual da CPU.
        
        Returns:
            Porcentagem de uso da CPU ou None se não conseguir obter
        """
        try:
            # Tentar via top
            top_output = self.run_command(['top', '-bn1'], timeout=5)
            
            for line in top_output.split('\n'):
                if '%Cpu' in line or 'CPU:' in line:
                    # Extrair o valor de uso da CPU
                    match = re.search(r'(\d+\.\d+)%(\s+|)us', line)
                    if match:
                        return float(match.group(1))
                    
                    # Outro formato possível
                    match = re.search(r'(\d+\.\d+)%(\s+|)user', line)
                    if match:
                        return float(match.group(1))
                        
                    # Tenta extrair qualquer porcentagem
                    match = re.search(r'(\d+\.\d+)%', line)
                    if match:
                        return float(match.group(1))
        except Exception as e:
            pass
            
        # Se chegou aqui, não conseguiu obter a CPU
        return None
    
    def _get_cpu_cores(self):
        """Obtém informações sobre os cores da CPU.
        
        Returns:
            Dicionário com informações dos cores ou None se não conseguir obter
        """
        try:
            # Tenta ler /proc/cpuinfo
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                
                # Conta o número de processadores
                processors = cpuinfo.count('processor')
                if processors > 0:
                    # Extrai modelo do processador
                    model_name = extract_value_with_regex(cpuinfo, r'model name\s+:\s+(.*)', 'Desconhecido')
                    
                    return {
                        "count": processors,
                        "model": model_name
                    }
        except Exception as e:
            pass
        
        # Tenta via nproc
        try:
            core_count = int(self.run_command(['nproc']).strip())
            return {
                "count": core_count,
                "model": "Desconhecido"
            }
        except Exception as e:
            pass
            
        return None
    
    def _get_cpu_frequency(self):
        """Obtém a frequência atual da CPU.
        
        Returns:
            Frequência em MHz ou None se não conseguir obter
        """
        try:
            # Tenta ler /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
            if os.path.exists('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'):
                with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', 'r') as f:
                    freq = int(f.read().strip())
                    # Converte de KHz para MHz
                    return freq / 1000
        except Exception as e:
            pass
            
        # Tenta via /proc/cpuinfo
        try:
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                
                # Extrai frequência
                freq = extract_value_with_regex(cpuinfo, r'cpu MHz\s+:\s+(\d+\.\d+)', None)
                if freq:
                    return float(freq)
        except Exception as e:
            pass
            
        return None
    
    def _get_memory_info(self):
        """Obtém informações de memória.
        
        Returns:
            Dicionário com informações de memória
        """
        try:
            # Tenta usar o comando free
            output = self.run_command(['free', '-b'])
            
            lines = output.split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 3:
                    total = int(parts[1])
                    used = int(parts[2])
                    percent = (used / total) * 100
                    return {
                        "total": format_bytes(total),
                        "used": format_bytes(used),
                        "percent": round(percent, 2)
                    }
            
            raise Exception("Não foi possível analisar a saída do comando 'free'")
        except Exception as e:
            # Tenta usar /proc/meminfo
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                
                total_match = re.search(r'MemTotal:\s+(\d+)', meminfo)
                free_match = re.search(r'MemFree:\s+(\d+)', meminfo)
                
                if total_match and free_match:
                    total_kb = int(total_match.group(1))
                    free_kb = int(free_match.group(1))
                    used_kb = total_kb - free_kb
                    percent = (used_kb / total_kb) * 100
                    
                    return {
                        "total": format_bytes(total_kb * 1024),
                        "used": format_bytes(used_kb * 1024),
                        "percent": round(percent, 2)
                    }
            except Exception as e:
                pass
                
            # Se tudo falhar
            return {"total": "Desconhecido", "used": "Desconhecido", "percent": 0}
    
    def _get_battery_info(self):
        """Tenta obter informações de bateria.
        
        Returns:
            Dicionário com informações de bateria ou None se não conseguir obter
        """
        try:
            # Tentar via termux-api
            output = self.run_command(['termux-battery-status'])
            
            try:
                # Tentar parse do JSON
                battery_info = json.loads(output)
                return battery_info
            except json.JSONDecodeError:
                # Se falhar, tentar extrair valores manualmente
                battery_info = {}
                
                percentage = extract_value_with_regex(output, r'percentage.*?(\d+)')
                if percentage:
                    battery_info["percentage"] = int(percentage)
                
                status = extract_value_with_regex(output, r'status.*?(\w+)')
                if status:
                    battery_info["status"] = status
                
                temperature = extract_value_with_regex(output, r'temperature.*?(\d+)')
                if temperature:
                    battery_info["temperature"] = float(temperature) / 10
                
                return battery_info
        except Exception as e:
            # Tentar método alternativo: arquivos diretos do sistema
            try:
                battery_info = {}
                
                # Verificar capacidade
                if os.path.exists('/sys/class/power_supply/battery/capacity'):
                    with open('/sys/class/power_supply/battery/capacity', 'r') as f:
                        battery_info["percentage"] = int(f.read().strip())
                
                # Verificar status
                if os.path.exists('/sys/class/power_supply/battery/status'):
                    with open('/sys/class/power_supply/battery/status', 'r') as f:
                        battery_info["status"] = f.read().strip()
                
                # Verificar temperatura
                if os.path.exists('/sys/class/power_supply/battery/temp'):
                    with open('/sys/class/power_supply/battery/temp', 'r') as f:
                        temp = int(f.read().strip())
                        # A maioria dos dispositivos armazena em millicelsius
                        if temp > 1000:
                            temp /= 10
                        battery_info["temperature"] = temp / 10
                
                return battery_info
            except Exception as e:
                return None
    
    def _get_temperature_info(self):
        """Obtém informações de temperatura do sistema.
        
        Returns:
            Dicionário com informações de temperatura ou None se não conseguir obter
        """
        temps = {}
        
        # Tenta ler temperaturas do diretório thermal
        try:
            thermal_dir = '/sys/class/thermal/'
            if os.path.exists(thermal_dir) and os.path.isdir(thermal_dir):
                for zone in os.listdir(thermal_dir):
                    if zone.startswith('thermal_zone'):
                        zone_path = os.path.join(thermal_dir, zone)
                        
                        # Tenta ler o tipo da zona
                        type_path = os.path.join(zone_path, 'type')
                        if os.path.exists(type_path):
                            with open(type_path, 'r') as f:
                                zone_type = f.read().strip()
                        else:
                            zone_type = zone
                        
                        # Tenta ler a temperatura
                        temp_path = os.path.join(zone_path, 'temp')
                        if os.path.exists(temp_path):
                            with open(temp_path, 'r') as f:
                                temp_value = int(f.read().strip())
                                # Converte para Celsius (geralmente em millicelsius)
                                if temp_value > 1000:
                                    temp_value /= 1000
                                temps[zone_type] = round(temp_value, 1)
        except Exception as e:
            pass
            
        return temps if temps else None

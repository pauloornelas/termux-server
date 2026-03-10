"""
Coletor de informações de hardware.

Este módulo implementa a coleta de informações de hardware,
como CPU, memória e temperatura.
A coleta de bateria é delegada ao AndroidCollector para evitar duplicação.
"""

import os
import re
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
            "memory": self._get_memory_info()
        }

        # Tenta obter informações de temperatura
        try:
            temp = self._get_temperature_info()
            if temp:
                data["temperature"] = temp
        except Exception:
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

    # Armazena a última leitura de time_in_state para calcular delta
    _last_time_in_state = None
    _last_time_in_state_time = 0

    def _get_cpu_usage(self):
        """Obtém o uso real da CPU via cpufreq/stats/time_in_state.

        No Termux, /proc/stat e top não funcionam corretamente.
        Usamos time_in_state que mostra quanto tempo cada core passou
        em cada frequência. Tempo na frequência mínima = idle,
        tempo em outras frequências = ativo.

        Returns:
            Porcentagem de uso da CPU (0-100) ou None se não conseguir obter
        """
        # Tentativa 1: time_in_state (uso real do sistema inteiro)
        try:
            usage = self._get_cpu_usage_from_time_in_state()
            if usage is not None:
                return usage
        except Exception:
            pass

        # Tentativa 2: top (funciona em Linux padrão)
        try:
            top_output = self.run_command(['top', '-bn1'], timeout=5)

            for line in top_output.split('\n'):
                if '%cpu' in line.lower():
                    total_match = re.search(r'(\d+)%cpu', line)
                    idle_match = re.search(r'(\d+)%idle', line)
                    if total_match and idle_match:
                        total_cpu = int(total_match.group(1))
                        idle = int(idle_match.group(1))
                        if total_cpu > 0:
                            usage = ((total_cpu - idle) / total_cpu) * 100
                            return round(usage, 1)

                    match = re.search(r'(\d+\.?\d*)\s*%?\s*us', line)
                    if match:
                        return float(match.group(1))
        except Exception:
            pass

        return None

    def _get_cpu_usage_from_time_in_state(self):
        """Calcula uso da CPU comparando duas leituras de time_in_state.

        Cada core tem um arquivo time_in_state com pares (freq, ticks).
        Tempo na frequência mínima = idle, demais = ativo.
        Compara com a leitura anterior para obter o delta.

        Returns:
            Porcentagem de uso (0-100) ou None
        """
        import time

        cpu_base = '/sys/devices/system/cpu'
        if not os.path.exists(cpu_base):
            return None

        current_reading = {}
        num_cores = os.cpu_count() or 8

        for i in range(num_cores):
            tis_path = f'{cpu_base}/cpu{i}/cpufreq/stats/time_in_state'
            min_path = f'{cpu_base}/cpu{i}/cpufreq/cpuinfo_min_freq'

            if not os.path.exists(tis_path):
                continue

            try:
                with open(min_path, 'r') as f:
                    min_freq = f.read().strip()

                idle_ticks = 0
                total_ticks = 0
                with open(tis_path, 'r') as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) == 2:
                            freq, ticks = parts[0], int(parts[1])
                            total_ticks += ticks
                            if freq == min_freq:
                                idle_ticks = ticks

                current_reading[i] = {'idle': idle_ticks, 'total': total_ticks}
            except Exception:
                continue

        if not current_reading:
            return None

        prev = HardwareCollector._last_time_in_state
        HardwareCollector._last_time_in_state = current_reading
        HardwareCollector._last_time_in_state_time = time.time()

        # Primeira leitura: sem delta para comparar
        if prev is None:
            return None

        total_active = 0
        total_delta = 0

        for core_id, cur in current_reading.items():
            if core_id not in prev:
                continue

            idle_delta = cur['idle'] - prev[core_id]['idle']
            total_d = cur['total'] - prev[core_id]['total']

            if total_d > 0:
                active_delta = total_d - idle_delta
                total_active += active_delta
                total_delta += total_d

        if total_delta == 0:
            return 0.0

        usage = (total_active / total_delta) * 100
        return round(min(usage, 100.0), 1)

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
        except Exception:
            pass

        # Tenta via nproc
        try:
            core_count = int(self.run_command(['nproc']).strip())
            return {
                "count": core_count,
                "model": "Desconhecido"
            }
        except Exception:
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
        except Exception:
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
        except Exception:
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
        except Exception:
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
            except Exception:
                pass

            # Se tudo falhar
            return {"total": "Desconhecido", "used": "Desconhecido", "percent": 0}

    def _get_temperature_info(self):
        """Obtém informações de temperatura do sistema.

        Returns:
            Dicionário com informações de temperatura ou None se não conseguir obter
        """
        temps = {}

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
        except Exception:
            pass

        return temps if temps else None

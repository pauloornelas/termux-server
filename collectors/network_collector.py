"""
Coletor de informações de rede.

Este módulo implementa a coleta de informações de rede,
como endereços IP, interfaces e estatísticas de tráfego.
"""

import os
import re
import socket
import subprocess
from datetime import datetime

from collectors.base_collector import BaseCollector
from core.utils import get_timestamp, extract_value_with_regex, format_bytes

class NetworkCollector(BaseCollector):
    """Coleta informações de rede do dispositivo."""
    
    def _collect_data(self):
        """Coleta dados de rede.
        
        Returns:
            Dicionário com informações de rede
        """
        data = {
            "timestamp": get_timestamp(),
            "ip": self._get_ip_address(),
            "interfaces": self._get_network_interfaces(),
            "connections": self._get_active_connections()
        }
        
        # Tenta obter informações de WiFi
        try:
            wifi_info = self._get_wifi_info()
            if wifi_info:
                data["wifi"] = wifi_info
        except Exception as e:
            # Ignora silenciosamente se não conseguir obter
            pass
            
        return data
    
    def _get_ip_address(self):
        """Obtém o endereço IP principal do dispositivo.
        
        Returns:
            String com o endereço IP ou "Desconhecido" se não conseguir obter
        """
        # Lista de métodos para obter o IP, em ordem de prioridade
        ip_methods = [
            self._get_ip_socket,
            self._get_ip_hostname,
            self._get_ip_ifconfig,
            self._get_ip_ip_addr,
            self._get_ip_termux_api
        ]
        
        # Tenta cada método até obter sucesso
        for method in ip_methods:
            try:
                ip = method()
                if ip and ip not in ["127.0.0.1", "localhost"]:
                    return ip
            except Exception:
                continue
                
        return "Desconhecido"
    
    def _get_ip_socket(self):
        """Obtém IP usando socket."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    
    def _get_ip_hostname(self):
        """Obtém IP usando hostname -I."""
        output = self.run_command(['hostname', '-I'])
        if output:
            return output.split()[0]
        return None
    
    def _get_ip_ifconfig(self):
        """Obtém IP usando ifconfig."""
        output = self.run_command(['ifconfig'])
        
        # Procura por endereços IPv4
        ip_matches = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
        for ip in ip_matches:
            if ip != "127.0.0.1":
                return ip
        return None
    
    def _get_ip_ip_addr(self):
        """Obtém IP usando ip addr."""
        output = self.run_command(['ip', 'addr'])
        
        # Procura por endereços IPv4
        ip_matches = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
        for ip in ip_matches:
            if ip != "127.0.0.1":
                return ip
        return None
    
    def _get_ip_termux_api(self):
        """Obtém IP usando termux-api."""
        try:
            output = self.run_command(['termux-wifi-connectioninfo'])
            
            # Procura por IP no JSON retornado
            ip_match = re.search(r'"ip":\s*"(\d+\.\d+\.\d+\.\d+)"', output)
            if ip_match:
                return ip_match.group(1)
        except Exception:
            pass
        return None
    
    def _get_network_interfaces(self):
        """Obtém informações sobre interfaces de rede.
        
        Returns:
            Lista de dicionários com informações das interfaces
        """
        interfaces = []
        
        try:
            # Verifica interfaces disponíveis via /proc/net/dev
            if os.path.exists("/proc/net/dev"):
                with open("/proc/net/dev", "r") as f:
                    lines = f.readlines()[2:]  # Pular cabeçalhos
                    
                for line in lines:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        interface_name = parts[0].strip()
                        if interface_name != "lo":  # Ignora loopback
                            # Extrai estatísticas básicas
                            stats = parts[1].split()
                            if len(stats) >= 16:
                                interface_info = {
                                    "name": interface_name,
                                    "rx_bytes": format_bytes(int(stats[0])),
                                    "tx_bytes": format_bytes(int(stats[8])),
                                    "rx_packets": int(stats[1]),
                                    "tx_packets": int(stats[9])
                                }
                                
                                # Tenta obter IP específico da interface
                                try:
                                    output = self.run_command(['ip', 'addr', 'show', interface_name])
                                    ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
                                    if ip_match:
                                        interface_info["ip"] = ip_match.group(1)
                                except Exception:
                                    pass
                                    
                                interfaces.append(interface_info)
        except Exception as e:
            # Tenta método alternativo via ifconfig
            try:
                output = self.run_command(['ifconfig'])
                
                # Divide a saída por interface
                interface_blocks = re.split(r'\n(?=\w)', output)
                
                for block in interface_blocks:
                    if block.strip():
                        # Extrai nome da interface
                        name_match = re.match(r'^(\w+)', block)
                        if name_match:
                            interface_name = name_match.group(1)
                            if interface_name != "lo":  # Ignora loopback
                                interface_info = {"name": interface_name}
                                
                                # Extrai IP
                                ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', block)
                                if ip_match:
                                    interface_info["ip"] = ip_match.group(1)
                                
                                # Extrai RX/TX bytes
                                rx_bytes = extract_value_with_regex(block, r'RX bytes:(\d+)', None)
                                tx_bytes = extract_value_with_regex(block, r'TX bytes:(\d+)', None)
                                
                                if rx_bytes:
                                    interface_info["rx_bytes"] = format_bytes(int(rx_bytes))
                                if tx_bytes:
                                    interface_info["tx_bytes"] = format_bytes(int(tx_bytes))
                                    
                                interfaces.append(interface_info)
            except Exception:
                pass
                
        return interfaces
    
    def _get_active_connections(self):
        """Obtém conexões de rede ativas.
        
        Returns:
            Dicionário com informações de conexões ativas
        """
        connections = {
            "count": 0,
            "tcp": 0,
            "udp": 0,
            "listening": 0,
            "established": 0
        }
        
        try:
            # Tenta via netstat
            output = self.run_command(['netstat', '-tuln'])
            
            # Conta conexões
            tcp_count = output.count('tcp')
            udp_count = output.count('udp')
            listening_count = output.count('LISTEN')
            established_count = output.count('ESTABLISHED')
            
            connections["count"] = tcp_count + udp_count
            connections["tcp"] = tcp_count
            connections["udp"] = udp_count
            connections["listening"] = listening_count
            connections["established"] = established_count
        except Exception:
            # Tenta via ss
            try:
                output = self.run_command(['ss', '-tuln'])
                
                # Conta conexões
                tcp_count = output.count('tcp')
                udp_count = output.count('udp')
                listening_count = output.count('LISTEN')
                established_count = output.count('ESTAB')
                
                connections["count"] = tcp_count + udp_count
                connections["tcp"] = tcp_count
                connections["udp"] = udp_count
                connections["listening"] = listening_count
                connections["established"] = established_count
            except Exception:
                pass
                
        return connections
    
    def _get_wifi_info(self):
        """Obtém informações sobre a conexão WiFi.
        
        Returns:
            Dicionário com informações de WiFi ou None se não conseguir obter
        """
        wifi_info = {}
        
        # Tenta via termux-api
        try:
            output = self.run_command(['termux-wifi-connectioninfo'])
            
            # Extrai informações básicas
            ssid = extract_value_with_regex(output, r'"ssid":\s*"([^"]+)"')
            if ssid:
                wifi_info["ssid"] = ssid
                
            bssid = extract_value_with_regex(output, r'"bssid":\s*"([^"]+)"')
            if bssid:
                wifi_info["bssid"] = bssid
                
            frequency = extract_value_with_regex(output, r'"frequency":\s*(\d+)')
            if frequency:
                wifi_info["frequency"] = int(frequency)
                
            signal = extract_value_with_regex(output, r'"rssi":\s*(-?\d+)')
            if signal:
                wifi_info["signal_strength"] = int(signal)
                
            link_speed = extract_value_with_regex(output, r'"link_speed":\s*(\d+)')
            if link_speed:
                wifi_info["link_speed"] = f"{link_speed} Mbps"
                
            return wifi_info if wifi_info else None
        except Exception:
            return None

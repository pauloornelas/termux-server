"""
Coletor de informações específicas do Android.

Este módulo implementa a coleta de informações específicas
do sistema Android através do Termux API.
"""

import json
import re
from datetime import datetime

from collectors.base_collector import BaseCollector
from core.utils import get_timestamp, safe_parse_json, extract_value_with_regex

class AndroidCollector(BaseCollector):
    """Coleta informações específicas do sistema Android."""
    
    def _collect_data(self):
        """Coleta dados específicos do Android.
        
        Returns:
            Dicionário com informações do Android
        """
        data = {
            "timestamp": get_timestamp(),
            "device_info": self._get_device_info(),
            "battery": self._get_battery_info()
        }
        
        # Tenta obter informações de sensores
        try:
            sensors = self._get_sensors_info()
            if sensors:
                data["sensors"] = sensors
        except Exception:
            # Ignora silenciosamente se não conseguir obter
            pass
            
        return data
    
    def _get_device_info(self):
        """Obtém informações do dispositivo Android.
        
        Returns:
            Dicionário com informações do dispositivo
        """
        device_info = {}
        
        # Tenta via termux-api
        try:
            output = self.run_command(['termux-info'])
            info = safe_parse_json(output)
            
            if info:
                # Extrai informações relevantes
                if "DEVICE_MANUFACTURER" in info:
                    device_info["manufacturer"] = info["DEVICE_MANUFACTURER"]
                if "DEVICE_MODEL" in info:
                    device_info["model"] = info["DEVICE_MODEL"]
                if "ANDROID_VERSION" in info:
                    device_info["android_version"] = info["ANDROID_VERSION"]
                if "ANDROID_SDK" in info:
                    device_info["android_sdk"] = info["ANDROID_SDK"]
                    
                return device_info
        except Exception:
            pass
            
        # Tenta método alternativo via getprop
        try:
            # Fabricante
            manufacturer = self.run_command(['getprop', 'ro.product.manufacturer'])
            if manufacturer:
                device_info["manufacturer"] = manufacturer
                
            # Modelo
            model = self.run_command(['getprop', 'ro.product.model'])
            if model:
                device_info["model"] = model
                
            # Versão do Android
            android_version = self.run_command(['getprop', 'ro.build.version.release'])
            if android_version:
                device_info["android_version"] = android_version
                
            # SDK do Android
            android_sdk = self.run_command(['getprop', 'ro.build.version.sdk'])
            if android_sdk:
                device_info["android_sdk"] = android_sdk
                
            return device_info
        except Exception:
            # Informações mínimas
            return {"model": "Galaxy S10+"}
    
    def _get_battery_info(self):
        """Obtém informações detalhadas da bateria.
        
        Returns:
            Dicionário com informações da bateria
        """
        try:
            # Tenta via termux-api
            output = self.run_command(['termux-battery-status'])
            battery_info = safe_parse_json(output)
            
            if battery_info:
                return battery_info
                
            # Se não conseguiu parsear JSON, tenta extrair manualmente
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
                
            health = extract_value_with_regex(output, r'health.*?(\w+)')
            if health:
                battery_info["health"] = health
                
            return battery_info
        except Exception:
            # Tenta método alternativo via arquivos do sistema
            try:
                battery_info = {}
                
                # Verificar capacidade
                try:
                    with open('/sys/class/power_supply/battery/capacity', 'r') as f:
                        battery_info["percentage"] = int(f.read().strip())
                except:
                    pass
                
                # Verificar status
                try:
                    with open('/sys/class/power_supply/battery/status', 'r') as f:
                        battery_info["status"] = f.read().strip()
                except:
                    pass
                
                # Verificar temperatura
                try:
                    with open('/sys/class/power_supply/battery/temp', 'r') as f:
                        temp = int(f.read().strip())
                        # A maioria dos dispositivos armazena em millicelsius
                        if temp > 1000:
                            temp /= 10
                        battery_info["temperature"] = temp / 10
                except:
                    pass
                
                # Verificar saúde
                try:
                    with open('/sys/class/power_supply/battery/health', 'r') as f:
                        battery_info["health"] = f.read().strip()
                except:
                    pass
                
                return battery_info
            except Exception:
                return None
    
    def _get_sensors_info(self):
        """Obtém informações dos sensores do dispositivo.
        
        Returns:
            Dicionário com informações dos sensores ou None se não conseguir obter
        """
        try:
            # Tenta via termux-api
            output = self.run_command(['termux-sensor', '-l'])
            sensors_list = safe_parse_json(output)
            
            if sensors_list:
                # Formata a lista de sensores
                sensors = {}
                for sensor in sensors_list:
                    if "name" in sensor:
                        sensor_name = sensor["name"].lower().replace(" ", "_")
                        sensors[sensor_name] = {
                            "type": sensor.get("type", "Unknown"),
                            "vendor": sensor.get("vendor", "Unknown")
                        }
                
                # Tenta obter leituras de alguns sensores comuns
                try:
                    # Acelerômetro
                    if "accelerometer" in sensors:
                        accel_output = self.run_command(['termux-sensor', '-s', 'accelerometer', '-n', '1'])
                        accel_data = safe_parse_json(accel_output)
                        if accel_data and len(accel_data) > 0:
                            sensors["accelerometer"]["values"] = {
                                "x": accel_data[0].get("values", [0, 0, 0])[0],
                                "y": accel_data[0].get("values", [0, 0, 0])[1],
                                "z": accel_data[0].get("values", [0, 0, 0])[2]
                            }
                    
                    # Sensor de luz
                    if "light" in sensors:
                        light_output = self.run_command(['termux-sensor', '-s', 'light', '-n', '1'])
                        light_data = safe_parse_json(light_output)
                        if light_data and len(light_data) > 0:
                            sensors["light"]["value"] = light_data[0].get("values", [0])[0]
                except Exception:
                    pass
                
                return sensors
        except Exception:
            return None

"""
Serviço para normalização de valores recebidos de diferentes fontes.
"""
import re
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class NormalizationService:
    """Serviço para normalização de valores de inventário."""
    
    @staticmethod
    def normalize_device_data(device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza os dados de um dispositivo.
        
        Args:
            device_data: Dados brutos do dispositivo
            
        Returns:
            Dict[str, Any]: Dados normalizados
        """
        if not device_data:
            return {}
            
        normalized = device_data.copy()
        
        # Normaliza campos de identificação
        for field in ['system_uuid', 'motherboard_serial', 'bios_serial', 'chassis_serial']:
            if field in normalized and normalized[field]:
                normalized[field] = str(normalized[field]).strip().upper()
        
        # Normaliza endereços MAC
        if 'mac_address' in normalized and normalized['mac_address']:
            normalized['mac_address'] = NormalizationService.normalize_mac(normalized['mac_address'])
        
        # Normaliza endereços IP
        if 'ip_address' in normalized and normalized['ip_address']:
            normalized['ip_address'] = normalized['ip_address'].strip()
        
        # Normaliza nomes
        if 'name' in normalized and normalized['name']:
            normalized['name'] = normalized['name'].strip()
        
        # Normaliza campos de data/hora
        for field in ['last_seen', 'first_seen', 'collection_timestamp']:
            if field in normalized and normalized[field]:
                normalized[field] = NormalizationService.normalize_datetime(normalized[field])
        
        # Normaliza hardware details se presente
        if 'hardware_details' in normalized and isinstance(normalized['hardware_details'], dict):
            normalized['hardware_details'] = NormalizationService.normalize_hardware_details(
                normalized['hardware_details']
            )
        
        return normalized
    
    @staticmethod
    def normalize_hardware_details(hw_details: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza os detalhes de hardware."""
        if not hw_details:
            return {}
            
        normalized = hw_details.copy()
        
        # Normaliza informações de CPU
        if 'cpu_info' in normalized and isinstance(normalized['cpu_info'], list):
            for cpu in normalized['cpu_info']:
                if not isinstance(cpu, dict):
                    continue
                
                # Normaliza frequência
                if 'speed' in cpu and cpu['speed']:
                    cpu['speed'] = NormalizationService.normalize_frequency(cpu['speed'])
                
                # Normaliza cache
                if 'cache' in cpu and isinstance(cpu['cache'], dict):
                    for level, size in cpu['cache'].items():
                        if isinstance(size, str):
                            cpu['cache'][level] = NormalizationService.normalize_storage_size(size)
        
        # Normaliza informações de memória
        if 'ram_info' in normalized and isinstance(normalized['ram_info'], list):
            for ram in normalized['ram_info']:
                if not isinstance(ram, dict):
                    continue
                
                if 'size' in ram and ram['size']:
                    ram['size'] = NormalizationService.normalize_storage_size(ram['size'])
                
                if 'speed' in ram and ram['speed']:
                    ram['speed'] = NormalizationService.normalize_frequency(ram['speed'])
        
        # Normaliza informações de disco
        if 'disk_info' in normalized and isinstance(normalized['disk_info'], list):
            for disk in normalized['disk_info']:
                if not isinstance(disk, dict):
                    continue
                
                for size_field in ['size', 'used', 'free', 'capacity']:
                    if size_field in disk and disk[size_field]:
                        disk[size_field] = NormalizationService.normalize_storage_size(disk[size_field])
        
        # Normaliza informações de rede
        if 'network_info' in normalized and isinstance(normalized['network_info'], list):
            for net in normalized['network_info']:
                if not isinstance(net, dict):
                    continue
                
                if 'mac_address' in net and net['mac_address']:
                    net['mac_address'] = NormalizationService.normalize_mac(net['mac_address'])
                
                if 'speed' in net and net['speed']:
                    net['speed'] = NormalizationService.normalize_network_speed(net['speed'])
        
        return normalized
    
    @staticmethod
    def normalize_mac(mac: str) -> str:
        """Normaliza um endereço MAC para o formato padrão (00:11:22:33:44:55)."""
        if not mac:
            return mac
            
        # Remove caracteres não hexadecimais e converte para maiúsculas
        mac = ''.join(c for c in mac.upper() if c in '0123456789ABCDEF')
        
        # Insira os dois pontos a cada 2 caracteres
        return ':'.join(mac[i:i+2] for i in range(0, len(mac), 2))
    
    @staticmethod
    def normalize_datetime(dt: Union[str, int, float, datetime]) -> str:
        """
        Normaliza uma data/hora para o formato ISO 8601.
        
        Args:
            dt: Data/hora em qualquer formato suportado
            
        Returns:
            str: Data/hora no formato ISO 8601 (UTC)
        """
        if not dt:
            return None
            
        if isinstance(dt, (int, float)):
            # Assume timestamp Unix (segundos desde a época)
            dt = datetime.utcfromtimestamp(dt)
        elif isinstance(dt, str):
            # Tenta fazer parsing da string
            try:
                # Remove timezone se existir
                if 'T' in dt:
                    dt = dt.split('+')[0].split('.')[0]
                    dt = datetime.fromisoformat(dt)
                else:
                    # Tenta formatos comuns
                    for fmt in [
                        '%Y-%m-%d %H:%M:%S',
                        '%d/%m/%Y %H:%M:%S',
                        '%Y%m%d%H%M%S',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S%z',
                    ]:
                        try:
                            dt = datetime.strptime(dt, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        raise ValueError(f"Formato de data não suportado: {dt}")
            except Exception as e:
                logger.warning(f"Falha ao normalizar data/hora '{dt}': {str(e)}")
                return None
        
        # Converte para UTC e formata como ISO 8601 sem timezone
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    @staticmethod
    def normalize_storage_size(size: Union[str, int, float]) -> int:
        """
        Normaliza um tamanho de armazenamento para bytes.
        
        Exemplos:
            - "1.5 TB" -> 1500000000000
            - "500GB" -> 500000000000
            - "1024" -> 1024 (assume bytes)
        """
        if not size:
            return 0
            
        if isinstance(size, (int, float)):
            return int(size)
            
        # Extrai número e unidade
        match = re.match(r'^\s*(\d+(?:\.\d+)?)\s*([KMGTP]?B?)?\s*$', str(size).upper())
        if not match:
            return 0
            
        value = float(match.group(1))
        unit = match.group(2) or 'B'
        
        # Remove o 'B' se presente (KB, MB, etc.)
        if unit.endswith('B'):
            unit = unit[0] if len(unit) > 1 else 'B'
        
        # Converte para bytes
        units = {
            'B': 1,
            'K': 1024,
            'M': 1024**2,
            'G': 1024**3,
            'T': 1024**4,
            'P': 1024**5
        }
        
        return int(value * units.get(unit.upper(), 1))
    
    @staticmethod
    def normalize_frequency(freq: Union[str, int, float]) -> int:
        """
        Normaliza uma frequência para Hz.
        
        Exemplos:
            - "2.4 GHz" -> 2400000000
            - "800MHz" -> 800000000
            - "1600" -> 1600 (assume Hz)
        """
        if not freq:
            return 0
            
        if isinstance(freq, (int, float)):
            return int(freq)
            
        # Extrai número e unidade
        match = re.match(r'^\s*(\d+(?:\.\d+)?)\s*([KMG]?HZ)?\s*$', str(freq).upper())
        if not match:
            return 0
            
        value = float(match.group(1))
        unit = match.group(2) or 'HZ'
        
        # Remove o 'HZ' se presente
        if unit.endswith('HZ'):
            unit = unit[0] if len(unit) > 2 else 'HZ'
        
        # Converte para Hz
        units = {
            'HZ': 1,
            'K': 1000,
            'M': 1000**2,
            'G': 1000**3
        }
        
        return int(value * units.get(unit.upper(), 1))
    
    @staticmethod
    def normalize_network_speed(speed: Union[str, int]) -> int:
        """
        Normaliza uma velocidade de rede para bps.
        
        Exemplos:
            - "1 Gbps" -> 1000000000
            - "100Mbps" -> 100000000
            - "1000" -> 1000 (assume bps)
        """
        if not speed:
            return 0
            
        if isinstance(speed, (int, float)):
            return int(speed)
            
        # Extrai número e unidade
        match = re.match(r'^\s*(\d+(?:\.\d+)?)\s*([KMG]?BPS?)?\s*$', str(speed).upper())
        if not match:
            return 0
            
        value = float(match.group(1))
        unit = match.group(2) or 'BPS'
        
        # Padroniza a unidade
        if unit == 'B/S':
            unit = 'BPS'
        elif unit.endswith('BPS'):
            unit = unit[0] + 'BPS' if len(unit) > 3 else 'BPS'
        
        # Converte para bps (1 byte = 8 bits)
        units = {
            'BPS': 8,        # bits por segundo
            'KBPS': 8 * 1000,       # kilobits por segundo
            'MBPS': 8 * 1000**2,    # megabits por segundo
            'GBPS': 8 * 1000**3,    # gigabits por segundo
            'B/S': 8,               # bytes por segundo
            'KB/S': 8 * 1024,       # kilobytes por segundo
            'MB/S': 8 * 1024**2,    # megabytes por segundo
            'GB/S': 8 * 1024**3     # gigabytes por segundo
        }
        
        return int(value * units.get(unit.upper(), 1))

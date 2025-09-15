"""
data_normalizer.py
Módulo de normalização de dados para comparação consistente de snapshots.
Implementa as regras essenciais de normalização antes de comparar dados.
"""

import re
from typing import Any, Dict, List, Union
from copy import deepcopy


class DataNormalizer:
    """Classe responsável pela normalização de dados antes da comparação"""
    
    # Campos que devem ser normalizados com lowercase (não case-sensitive)
    CASE_INSENSITIVE_FIELDS = {
        'manufacturer', 'vendor', 'model', 'name', 'description', 
        'os', 'version', 'architecture', 'interface_type',
        'driver_version', 'firmware_version', 'publisher'
    }
    
    # Campos que NÃO devem ser normalizados (case-sensitive)
    CASE_SENSITIVE_FIELDS = {
        'serial', 'serial_number', 'part_number', 'uuid', 'mac_address',
        'device_id', 'vendor_id', 'product_id', 'system_uuid'
    }
    
    # Campos voláteis que devem ser removidos da comparação
    VOLATILE_FIELDS = {
        'last_seen', 'uptime_seconds', 'collection_timestamp',
        'temperature_info', 'free_space', 'used_space', 'free_gb',
        'ram_usage', 'cpu_usage', 'current_reading', 'last_checked'
    }
    
    # Campos de capacidade que devem ser convertidos para bytes
    CAPACITY_FIELDS = {
        'total_gb': 1024**3,
        'total_mb': 1024**2,
        'total_kb': 1024,
        'capacity_gb': 1024**3,
        'capacity_mb': 1024**2,
        'size_gb': 1024**3,
        'size_mb': 1024**2,
        'vram_gb': 1024**3,
        'vram_mb': 1024**2
    }
    
    @classmethod
    def normalize_device_data(cls, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza dados de um dispositivo completo para comparação.
        
        Args:
            device_data: Dados do dispositivo
            
        Returns:
            Dados normalizados
        """
        normalized = deepcopy(device_data)
        
        # 1. Remover campos voláteis
        cls._remove_volatile_fields(normalized)
        
        # 2. Normalizar strings
        cls._normalize_strings(normalized)
        
        # 3. Converter unidades para bytes
        cls._convert_units_to_bytes(normalized)
        
        # 4. Ordenar listas por chaves estáveis
        cls._sort_component_lists(normalized)
        
        return normalized
    
    @classmethod
    def _remove_volatile_fields(cls, data: Union[Dict, List, Any]) -> None:
        """Remove campos voláteis recursivamente"""
        if isinstance(data, dict):
            # Remover campos voláteis do nível atual
            keys_to_remove = []
            for key in data.keys():
                if any(volatile in key.lower() for volatile in cls.VOLATILE_FIELDS):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del data[key]
            
            # Recursão para valores
            for value in data.values():
                cls._remove_volatile_fields(value)
                
        elif isinstance(data, list):
            for item in data:
                cls._remove_volatile_fields(item)
    
    @classmethod
    def _normalize_strings(cls, data: Union[Dict, List, Any]) -> None:
        """Normaliza strings recursivamente"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    # Sempre fazer strip
                    value = value.strip()
                    
                    # Lowercase apenas para campos não case-sensitive
                    if any(field in key.lower() for field in cls.CASE_INSENSITIVE_FIELDS):
                        # Verificar se não é um campo case-sensitive
                        if not any(field in key.lower() for field in cls.CASE_SENSITIVE_FIELDS):
                            value = value.lower()
                    
                    data[key] = value
                else:
                    cls._normalize_strings(value)
                    
        elif isinstance(data, list):
            for item in data:
                cls._normalize_strings(item)
    
    @classmethod
    def _convert_units_to_bytes(cls, data: Union[Dict, List, Any]) -> None:
        """Converte unidades para bytes recursivamente"""
        if isinstance(data, dict):
            conversions = {}
            
            for key, value in data.items():
                # Verificar se precisa converter
                for capacity_field, multiplier in cls.CAPACITY_FIELDS.items():
                    if capacity_field in key.lower() and isinstance(value, (int, float)):
                        # Criar novo campo em bytes
                        base_name = key.lower().replace('_gb', '').replace('_mb', '').replace('_kb', '')
                        new_key = f"{base_name}_bytes"
                        conversions[new_key] = int(value * multiplier)
                        break
                
                # Recursão
                cls._convert_units_to_bytes(value)
            
            # Aplicar conversões
            data.update(conversions)
            
        elif isinstance(data, list):
            for item in data:
                cls._convert_units_to_bytes(item)
    
    @classmethod
    def _sort_component_lists(cls, data: Union[Dict, List, Any]) -> None:
        """Ordena listas de componentes por chaves estáveis"""
        if isinstance(data, dict):
            # Listas de componentes que devem ser ordenadas
            component_lists = [
                'disk_info', 'ram_info', 'network_info', 'usb_devices',
                'installed_software', 'partitions', 'gpu_info'
            ]
            
            for key, value in data.items():
                if key in component_lists and isinstance(value, list):
                    # Ordenar por chaves estáveis
                    data[key] = cls._sort_component_list(value)
                else:
                    cls._sort_component_lists(value)
                    
        elif isinstance(data, list):
            for item in data:
                cls._sort_component_lists(item)
    
    @classmethod
    def _sort_component_list(cls, components: List[Dict]) -> List[Dict]:
        """Ordena uma lista de componentes por chaves estáveis"""
        if not components or not isinstance(components[0], dict):
            return components
        
        # Definir ordem de prioridade para chaves de ordenação
        sort_keys = ['serial_number', 'serial', 'mac_address', 'device_id', 
                    'name', 'model', 'part_number', 'uuid']
        
        def get_sort_key(component):
            # Tentar cada chave de ordenação na ordem de prioridade
            for key in sort_keys:
                if key in component and component[key]:
                    value = component[key]
                    if isinstance(value, str):
                        return value.strip().lower()
                    return str(value)
            
            # Fallback: usar o primeiro valor string encontrado
            for value in component.values():
                if isinstance(value, str) and value.strip():
                    return value.strip().lower()
            
            return ""
        
        try:
            return sorted(components, key=get_sort_key)
        except Exception:
            # Em caso de erro, retornar lista original
            return components
    
    @classmethod
    def normalize_for_comparison(cls, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> tuple:
        """
        Normaliza dois conjuntos de dados para comparação.
        
        Args:
            old_data: Dados antigos
            new_data: Dados novos
            
        Returns:
            Tupla com (dados_antigos_normalizados, dados_novos_normalizados)
        """
        normalized_old = cls.normalize_device_data(old_data)
        normalized_new = cls.normalize_device_data(new_data)
        
        return normalized_old, normalized_new
    
    @classmethod
    def get_comparison_hash(cls, data: Dict[str, Any]) -> str:
        """
        Gera hash para comparação rápida de dados normalizados.
        
        Args:
            data: Dados a serem hashados
            
        Returns:
            Hash SHA256 dos dados normalizados
        """
        import hashlib
        import json
        
        normalized = cls.normalize_device_data(data)
        
        # Converter para JSON ordenado para hash consistente
        json_str = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
        
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def normalize_snapshot_devices(devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Função utilitária para normalizar uma lista de dispositivos de snapshot.
    
    Args:
        devices: Lista de dispositivos
        
    Returns:
        Lista de dispositivos normalizados
    """
    return [DataNormalizer.normalize_device_data(device) for device in devices]


if __name__ == "__main__":
    # Teste básico
    test_device = {
        "name": "  Test Device  ",
        "manufacturer": "  DELL  ",
        "serial_number": "ABC123",
        "total_gb": 500.0,
        "last_seen": "2024-01-01",
        "disk_info": [
            {"serial_number": "SSD456", "model": "  Samsung  "},
            {"serial_number": "HDD123", "model": "  Seagate  "}
        ]
    }
    
    normalized = DataNormalizer.normalize_device_data(test_device)
    print("Dados normalizados:")
    import json
    print(json.dumps(normalized, indent=2, ensure_ascii=False))

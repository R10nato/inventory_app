"""
Sistema de filtragem inteligente de mudanças para reduzir ruído em alertas.
Implementa regras práticas para distinguir mudanças significativas de variações normais.
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class ChangeSignificanceAnalyzer:
    """Analisa a significância de mudanças para evitar alertas desnecessários"""
    
    # Limiares configuráveis
    DISK_FREE_SPACE_THRESHOLD = 0.15  # 15% de mudança no espaço livre
    RAM_USAGE_THRESHOLD = 0.20  # 20% de mudança no uso de RAM
    TEMP_VARIATION_THRESHOLD = 10  # 10°C de variação de temperatura
    
    # Fabricantes de VM conhecidos
    VM_VENDORS = {
        'microsoft corporation': 'Hyper-V',
        'vmware, inc.': 'VMware',
        'innotek gmbh': 'VirtualBox',
        'oracle corporation': 'VirtualBox',
        'qemu': 'QEMU/KVM',
        'xen': 'Xen',
        'parallels software': 'Parallels'
    }
    
    # Modelos que indicam VM
    VM_MODELS = [
        'virtual machine',
        'vmware virtual platform',
        'virtualbox',
        'hyper-v',
        'qemu',
        'xen'
    ]

    def __init__(self):
        self.vm_detection_cache = {}
        # Integrar com serviço de detecção de VM
        try:
            from vm_detection_service import vm_detection_service
            self.vm_service = vm_detection_service
        except ImportError:
            self.vm_service = None
        
        # Integrar com gerenciador de configuração de limiares
        try:
            from change_threshold_config import threshold_config
            self.threshold_config = threshold_config
        except ImportError:
            self.threshold_config = None
    
    def is_virtual_machine(self, device_data: Dict[str, Any]) -> Optional[str]:
        """
        Detecta se o dispositivo é uma VM e retorna o tipo.
        
        Args:
            device_data: Dados do dispositivo
            
        Returns:
            String com o tipo de VM ou None se for físico
        """
        device_id = device_data.get('mac_address', device_data.get('ip_address', 'unknown'))
        
        # Cache para evitar reprocessamento
        if device_id in self.vm_detection_cache:
            return self.vm_detection_cache[device_id]
        
        vm_type = None
        
        # Usar serviço avançado de detecção se disponível
        if self.vm_service:
            try:
                vm_result = self.vm_service.detect_virtualization(device_data)
                vm_type = vm_result.vm_type if vm_result.is_virtual else None
                self.vm_detection_cache[device_id] = vm_type
                return vm_type
            except Exception as e:
                print(f"[VM_DETECTION] Erro no serviço avançado: {e}")
        
        # Fallback para detecção básica
        # Verificar fabricante do sistema
        system_vendor = device_data.get('hardware_details', {}).get('motherboard_info', {}).get('vendor', '').lower()
        if system_vendor in self.VM_VENDORS:
            vm_type = self.VM_VENDORS[system_vendor]
        
        # Verificar modelo do sistema
        system_model = device_data.get('hardware_details', {}).get('motherboard_info', {}).get('model', '').lower()
        for vm_model in self.VM_MODELS:
            if vm_model in system_model:
                vm_type = vm_model.title()
                break
        
        # Verificar BIOS
        bios_vendor = device_data.get('bios_vendor', '').lower()
        if any(vendor in bios_vendor for vendor in self.VM_VENDORS.keys()):
            for vendor, vm_name in self.VM_VENDORS.items():
                if vendor in bios_vendor:
                    vm_type = vm_name
                    break
        
        # Cache do resultado
        self.vm_detection_cache[device_id] = vm_type
        return vm_type
    
    def should_trigger_alert(self, change_type: str, old_data: Dict, new_data: Dict, device_data: Dict = None) -> Dict[str, Any]:
        """
        Determina se uma mudança deve gerar alerta baseado em regras inteligentes.
        
        Args:
            change_type: Tipo da mudança (NEW_DEVICE, REMOVED_DEVICE, UPDATED_DEVICE)
            old_data: Dados antigos
            new_data: Dados novos
            device_data: Dados completos do dispositivo para contexto
            
        Returns:
            Dict com 'should_alert': bool, 'reason': str, 'severity': str
        """
        
        # Sempre alertar para adição/remoção de dispositivos
        if change_type in ['NEW_DEVICE', 'REMOVED_DEVICE']:
            return {
                'should_alert': True,
                'reason': f'Dispositivo {"adicionado" if change_type == "NEW_DEVICE" else "removido"}',
                'severity': 'high' if change_type == 'REMOVED_DEVICE' else 'medium'
            }
        
        # Para mudanças em dispositivos existentes
        if change_type == 'UPDATED_DEVICE':
            return self._analyze_device_changes(old_data, new_data, device_data or {})
        
        return {'should_alert': False, 'reason': 'Tipo de mudança não reconhecido', 'severity': 'low'}
    
    def _analyze_device_changes(self, old_data: Dict, new_data: Dict, device_data: Dict) -> Dict[str, Any]:
        """Analisa mudanças específicas em dispositivos"""
        
        significant_changes = []
        vm_type = self.is_virtual_machine(device_data)
        is_vm = vm_type is not None
        
        # Obter limiares configurados
        thresholds = {}
        if self.threshold_config:
            thresholds = self.threshold_config.get_thresholds_for_device(vm_type)
        
        for field, change_data in new_data.items():
            old_value = change_data.get('old')
            new_value = change_data.get('new')
            
            # Usar configuração de limiares se disponível
            if self.threshold_config:
                if self.threshold_config.should_always_alert(field):
                    significant_changes.append({
                        'field': field,
                        'reason': f'Campo crítico alterado: {field}',
                        'severity': 'high'
                    })
                    continue
                
                if self.threshold_config.should_always_ignore(field):
                    continue
            
            # Usar serviço de VM para supressão específica
            if is_vm and self.vm_service:
                vm_detection = self.vm_service.detect_virtualization(device_data)
                should_suppress, reason = self.vm_service.should_suppress_alert('UPDATED_DEVICE', field, vm_detection)
                if should_suppress:
                    continue
            
            # Mudanças sempre significativas (fallback)
            if self._is_always_significant(field, old_value, new_value):
                significant_changes.append({
                    'field': field,
                    'reason': self._get_significance_reason(field, old_value, new_value),
                    'severity': self._get_change_severity(field, old_value, new_value, is_vm)
                })
                continue
            
            # Mudanças que podem ser ignoradas
            if self._should_ignore_change(field, old_value, new_value, is_vm):
                continue
            
            # Mudanças com limiar
            if self._exceeds_threshold(field, old_value, new_value):
                significant_changes.append({
                    'field': field,
                    'reason': f'Mudança em {field} excedeu limiar configurado',
                    'severity': 'medium'
                })
        
        if significant_changes:
            return {
                'should_alert': True,
                'reason': f'Mudanças significativas detectadas: {", ".join([c["field"] for c in significant_changes])}',
                'severity': max([c['severity'] for c in significant_changes], key=lambda x: ['low', 'medium', 'high', 'critical'].index(x)),
                'vm_context': f' (VM: {vm_type})' if is_vm else ' (Físico)',
                'details': significant_changes
            }
        
        return {
            'should_alert': False,
            'reason': 'Apenas mudanças voláteis ou abaixo do limiar detectadas',
            'severity': 'low'
        }
    
    def _is_always_significant(self, field: str, old_value: Any, new_value: Any) -> bool:
        """Mudanças que sempre devem gerar alerta"""
        
        # Mudanças em identificadores únicos
        significant_fields = [
            'system_uuid', 'motherboard_serial', 'bios_version',
            'hardware.cpu_info', 'hardware.motherboard_info'
        ]
        
        if any(sig_field in field for sig_field in significant_fields):
            return True
        
        # Mudanças em seriais de componentes
        if 'serial' in field.lower() and old_value != new_value:
            return True
        
        # Mudanças em capacidades (aumento/diminuição)
        if self._is_capacity_change(field, old_value, new_value):
            return True
        
        # Mudanças em modelos de hardware
        if 'model' in field.lower() and old_value != new_value:
            return True
        
        return False
    
    def _should_ignore_change(self, field: str, old_value: Any, new_value: Any, is_vm: bool) -> bool:
        """Mudanças que devem ser ignoradas"""
        
        # Campos voláteis que sempre mudam
        volatile_fields = [
            'last_seen', 'uptime_seconds', 'collection_timestamp',
            'temperature_info', 'free_space', 'used_space',
            'ram_usage', 'cpu_usage'
        ]
        
        if any(vol_field in field for vol_field in volatile_fields):
            return True
        
        # Em VMs, ignorar algumas mudanças esperadas
        if is_vm:
            vm_expected_changes = [
                'network_info',  # Interfaces podem mudar em VMs
                'usb_devices'    # USB pode ser volátil em VMs
            ]
            if any(vm_field in field for vm_field in vm_expected_changes):
                return True
        
        return False
    
    def _exceeds_threshold(self, field: str, old_value: Any, new_value: Any) -> bool:
        """Verifica se mudança excede limiar configurado"""
        
        if not isinstance(old_value, (int, float)) or not isinstance(new_value, (int, float)):
            return False
        
        if old_value == 0:  # Evitar divisão por zero
            return new_value != 0
        
        change_ratio = abs(new_value - old_value) / old_value
        
        # Limiares específicos por campo
        if 'disk' in field and 'free' in field:
            return change_ratio > self.DISK_FREE_SPACE_THRESHOLD
        
        if 'ram' in field and 'usage' in field:
            return change_ratio > self.RAM_USAGE_THRESHOLD
        
        if 'temperature' in field:
            return abs(new_value - old_value) > self.TEMP_VARIATION_THRESHOLD
        
        return False
    
    def _is_capacity_change(self, field: str, old_value: Any, new_value: Any) -> bool:
        """Detecta mudanças em capacidades de hardware"""
        
        capacity_indicators = ['capacity', 'size', 'bytes', 'gb', 'mb', 'total']
        
        if not any(indicator in field.lower() for indicator in capacity_indicators):
            return False
        
        # Se são dicionários, verificar mudanças em capacidades internas
        if isinstance(old_value, dict) and isinstance(new_value, dict):
            return self._compare_capacity_dicts(old_value, new_value)
        
        # Se são números, verificar mudança significativa
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            return old_value != new_value
        
        return False
    
    def _compare_capacity_dicts(self, old_dict: Dict, new_dict: Dict) -> bool:
        """Compara dicionários procurando mudanças em capacidades"""
        
        capacity_keys = ['capacity_bytes', 'total_bytes', 'size', 'capacity']
        
        for key in capacity_keys:
            if key in old_dict and key in new_dict:
                if old_dict[key] != new_dict[key]:
                    return True
        
        return False
    
    def _get_significance_reason(self, field: str, old_value: Any, new_value: Any) -> str:
        """Retorna razão específica da significância"""
        
        if 'serial' in field.lower():
            return f'Serial alterado: {old_value} → {new_value}'
        
        if 'model' in field.lower():
            return f'Modelo alterado: {old_value} → {new_value}'
        
        if self._is_capacity_change(field, old_value, new_value):
            return f'Capacidade alterada em {field}'
        
        return f'Mudança significativa em {field}'
    
    def _get_change_severity(self, field: str, old_value: Any, new_value: Any, is_vm: bool) -> str:
        """Determina severidade da mudança"""
        
        # Mudanças críticas
        if field in ['system_uuid', 'motherboard_serial']:
            return 'critical'
        
        # Mudanças importantes
        if 'serial' in field.lower() or 'model' in field.lower():
            return 'high'
        
        # Em VMs, reduzir severidade
        if is_vm and field in ['hardware.network_info', 'hardware.usb_devices']:
            return 'low'
        
        return 'medium'


def filter_changes_intelligently(changes: List[Dict[str, Any]], devices_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Filtra lista de mudanças aplicando regras inteligentes.
    
    Args:
        changes: Lista de mudanças detectadas
        devices_data: Dados completos dos dispositivos para contexto
        
    Returns:
        Lista filtrada de mudanças significativas
    """
    
    analyzer = ChangeSignificanceAnalyzer()
    filtered_changes = []
    
    for change in changes:
        change_type = change.get('type')
        mac_address = change.get('mac_address')
        change_data = change.get('changes', {})
        
        # Obter dados do dispositivo para contexto
        device_data = {}
        if devices_data and mac_address:
            device_data = devices_data.get(mac_address, {})
        
        # Analisar significância
        if change_type == 'UPDATED_DEVICE':
            analysis = analyzer.should_trigger_alert(change_type, {}, change_data, device_data)
        else:
            analysis = analyzer.should_trigger_alert(change_type, {}, {}, device_data)
        
        if analysis['should_alert']:
            # Enriquecer mudança com análise
            enriched_change = change.copy()
            enriched_change['analysis'] = analysis
            enriched_change['vm_type'] = analyzer.is_virtual_machine(device_data)
            filtered_changes.append(enriched_change)
    
    return filtered_changes


# Configurações de limiar ajustáveis
THRESHOLD_CONFIG = {
    'disk_free_space_percent': 15,
    'ram_usage_percent': 20,
    'temperature_celsius': 10,
    'persistent_change_hours': 2,  # Mudança deve persistir por X horas
    'vm_sensitivity_reduction': 0.5  # Reduzir sensibilidade em VMs
}


def update_threshold_config(new_config: Dict[str, Any]):
    """Atualiza configurações de limiar dinamicamente"""
    global THRESHOLD_CONFIG
    THRESHOLD_CONFIG.update(new_config)
    
    # Atualizar instância do analisador
    ChangeSignificanceAnalyzer.DISK_FREE_SPACE_THRESHOLD = new_config.get('disk_free_space_percent', 15) / 100
    ChangeSignificanceAnalyzer.RAM_USAGE_THRESHOLD = new_config.get('ram_usage_percent', 20) / 100
    ChangeSignificanceAnalyzer.TEMP_VARIATION_THRESHOLD = new_config.get('temperature_celsius', 10)

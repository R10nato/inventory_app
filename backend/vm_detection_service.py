"""
Serviço de detecção de máquinas virtuais e ajuste de sensibilidade de alertas.
Implementa lógica específica para reduzir falsos-positivos em ambientes virtualizados.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class VMDetectionResult:
    """Resultado da detecção de VM"""
    is_virtual: bool
    vm_type: str
    confidence: float  # 0.0 a 1.0
    indicators: List[str]
    hypervisor: str = None


class VMDetectionService:
    """Serviço para detectar máquinas virtuais e ajustar comportamento de alertas"""
    
    # Indicadores de virtualização por categoria
    VM_INDICATORS = {
        'bios_vendors': {
            'american megatrends': {'vmware': 0.3, 'virtualbox': 0.2},
            'phoenix technologies': {'vmware': 0.2},
            'seabios': {'qemu': 0.9, 'kvm': 0.9},
            'ovmf': {'qemu': 0.8, 'kvm': 0.8, 'hyper-v': 0.3}
        },
        
        'system_vendors': {
            'microsoft corporation': {'hyper-v': 0.9},
            'vmware, inc.': {'vmware': 0.95},
            'innotek gmbh': {'virtualbox': 0.9},
            'oracle corporation': {'virtualbox': 0.8},
            'qemu': {'qemu': 0.95, 'kvm': 0.9},
            'xen': {'xen': 0.95},
            'parallels software': {'parallels': 0.9},
            'red hat': {'kvm': 0.7}
        },
        
        'system_models': {
            'virtual machine': {'hyper-v': 0.8, 'generic': 0.6},
            'vmware virtual platform': {'vmware': 0.95},
            'vmware7,1': {'vmware': 0.9},
            'virtualbox': {'virtualbox': 0.95},
            'standard pc (i440fx + piix, 1996)': {'qemu': 0.8},
            'standard pc (q35 + ich9, 2009)': {'qemu': 0.8},
            'xen domU': {'xen': 0.9}
        },
        
        'cpu_models': {
            'qemu virtual cpu': {'qemu': 0.9, 'kvm': 0.8},
            'common kvm processor': {'kvm': 0.9},
            'common 32-bit kvm processor': {'kvm': 0.9}
        },
        
        'disk_models': {
            'vmware virtual disk': {'vmware': 0.9},
            'vbox harddisk': {'virtualbox': 0.9},
            'qemu harddisk': {'qemu': 0.9},
            'xvd': {'xen': 0.8},
            'virtio': {'kvm': 0.7, 'qemu': 0.7}
        },
        
        'network_vendors': {
            'vmware': {'vmware': 0.8},
            'oracle': {'virtualbox': 0.6},
            'red hat': {'kvm': 0.6},
            'microsoft': {'hyper-v': 0.5}
        }
    }
    
    # Padrões de MAC address de VMs
    VM_MAC_PATTERNS = {
        r'^00:0c:29:': 'vmware',
        r'^00:1c:14:': 'vmware', 
        r'^00:50:56:': 'vmware',
        r'^08:00:27:': 'virtualbox',
        r'^0a:00:27:': 'virtualbox',
        r'^00:16:3e:': 'xen',
        r'^00:15:5d:': 'hyper-v',
        r'^52:54:00:': 'kvm'
    }
    
    def detect_virtualization(self, device_data: Dict[str, Any]) -> VMDetectionResult:
        """
        Detecta se um dispositivo é uma máquina virtual.
        
        Args:
            device_data: Dados completos do dispositivo
            
        Returns:
            VMDetectionResult com detalhes da detecção
        """
        
        indicators = []
        vm_scores = {}  # vm_type -> confidence score
        
        # Analisar BIOS
        bios_vendor = device_data.get('bios_vendor', '').lower()
        if bios_vendor:
            for vendor, vm_types in self.VM_INDICATORS['bios_vendors'].items():
                if vendor in bios_vendor:
                    for vm_type, score in vm_types.items():
                        vm_scores[vm_type] = vm_scores.get(vm_type, 0) + score
                        indicators.append(f'BIOS vendor: {bios_vendor}')
        
        # Analisar hardware details
        hw_details = device_data.get('hardware_details', {})
        
        # Sistema (motherboard)
        mb_info = hw_details.get('motherboard_info', {})
        if isinstance(mb_info, dict):
            vendor = mb_info.get('vendor', '').lower()
            model = mb_info.get('model', '').lower()
            
            # Verificar vendor
            for vm_vendor, vm_types in self.VM_INDICATORS['system_vendors'].items():
                if vm_vendor in vendor:
                    for vm_type, score in vm_types.items():
                        vm_scores[vm_type] = vm_scores.get(vm_type, 0) + score
                        indicators.append(f'System vendor: {vendor}')
            
            # Verificar model
            for vm_model, vm_types in self.VM_INDICATORS['system_models'].items():
                if vm_model in model:
                    for vm_type, score in vm_types.items():
                        vm_scores[vm_type] = vm_scores.get(vm_type, 0) + score
                        indicators.append(f'System model: {model}')
        
        # CPU
        cpu_info = hw_details.get('cpu_info', {})
        if isinstance(cpu_info, dict):
            cpu_model = cpu_info.get('model', '').lower()
            for vm_cpu, vm_types in self.VM_INDICATORS['cpu_models'].items():
                if vm_cpu in cpu_model:
                    for vm_type, score in vm_types.items():
                        vm_scores[vm_type] = vm_scores.get(vm_type, 0) + score
                        indicators.append(f'CPU model: {cpu_model}')
        
        # Discos
        disk_info = hw_details.get('disk_info', {})
        if isinstance(disk_info, dict):
            drives = disk_info.get('drives', [])
            if isinstance(drives, list):
                for drive in drives:
                    if isinstance(drive, dict):
                        model = drive.get('model', '').lower()
                        for vm_disk, vm_types in self.VM_INDICATORS['disk_models'].items():
                            if vm_disk in model:
                                for vm_type, score in vm_types.items():
                                    vm_scores[vm_type] = vm_scores.get(vm_type, 0) + score
                                    indicators.append(f'Disk model: {model}')
        
        # Rede
        network_info = hw_details.get('network_info', {})
        if isinstance(network_info, dict):
            interfaces = network_info.get('interfaces', [])
            if isinstance(interfaces, list):
                for interface in interfaces:
                    if isinstance(interface, dict):
                        # Verificar MAC address
                        mac = interface.get('mac_address', '')
                        for pattern, vm_type in self.VM_MAC_PATTERNS.items():
                            if re.match(pattern, mac, re.IGNORECASE):
                                vm_scores[vm_type] = vm_scores.get(vm_type, 0) + 0.8
                                indicators.append(f'VM MAC pattern: {mac}')
                        
                        # Verificar vendor
                        vendor = interface.get('vendor', '').lower()
                        for vm_vendor, vm_types in self.VM_INDICATORS['network_vendors'].items():
                            if vm_vendor in vendor:
                                for vm_type, score in vm_types.items():
                                    vm_scores[vm_type] = vm_scores.get(vm_type, 0) + score
                                    indicators.append(f'Network vendor: {vendor}')
        
        # Determinar resultado
        if not vm_scores:
            return VMDetectionResult(
                is_virtual=False,
                vm_type='physical',
                confidence=0.0,
                indicators=[]
            )
        
        # Encontrar VM type com maior score
        best_vm_type = max(vm_scores.keys(), key=lambda k: vm_scores[k])
        confidence = min(vm_scores[best_vm_type], 1.0)  # Cap at 1.0
        
        # Considerar virtual se confidence >= 0.5
        is_virtual = confidence >= 0.5
        
        return VMDetectionResult(
            is_virtual=is_virtual,
            vm_type=best_vm_type if is_virtual else 'physical',
            confidence=confidence,
            indicators=indicators,
            hypervisor=best_vm_type if is_virtual else None
        )
    
    def get_vm_specific_thresholds(self, vm_type: str) -> Dict[str, float]:
        """
        Retorna limiares ajustados para tipos específicos de VM.
        
        Args:
            vm_type: Tipo de VM detectado
            
        Returns:
            Dict com limiares ajustados
        """
        
        base_thresholds = {
            'disk_free_space_threshold': 0.15,
            'ram_usage_threshold': 0.20,
            'temp_variation_threshold': 10,
            'network_change_sensitivity': 1.0,
            'usb_change_sensitivity': 1.0
        }
        
        # Ajustes específicos por tipo de VM
        vm_adjustments = {
            'vmware': {
                'network_change_sensitivity': 0.3,  # Menos sensível a mudanças de rede
                'usb_change_sensitivity': 0.2,     # USB muda frequentemente
                'temp_variation_threshold': 15     # Temperatura menos confiável
            },
            'virtualbox': {
                'network_change_sensitivity': 0.4,
                'usb_change_sensitivity': 0.1,     # USB muito volátil
                'disk_free_space_threshold': 0.25  # Discos dinâmicos
            },
            'hyper-v': {
                'network_change_sensitivity': 0.5,
                'temp_variation_threshold': 20     # Sensores podem não existir
            },
            'kvm': {
                'network_change_sensitivity': 0.4,
                'usb_change_sensitivity': 0.3
            },
            'qemu': {
                'network_change_sensitivity': 0.4,
                'usb_change_sensitivity': 0.3,
                'temp_variation_threshold': 15
            }
        }
        
        # Aplicar ajustes
        adjusted_thresholds = base_thresholds.copy()
        if vm_type in vm_adjustments:
            adjusted_thresholds.update(vm_adjustments[vm_type])
        
        return adjusted_thresholds
    
    def should_suppress_alert(self, change_type: str, field: str, vm_detection: VMDetectionResult) -> Tuple[bool, str]:
        """
        Determina se um alerta deve ser suprimido baseado no contexto de VM.
        
        Args:
            change_type: Tipo da mudança
            field: Campo que mudou
            vm_detection: Resultado da detecção de VM
            
        Returns:
            Tuple (should_suppress, reason)
        """
        
        if not vm_detection.is_virtual:
            return False, "Dispositivo físico - sem supressão"
        
        vm_type = vm_detection.vm_type
        
        # Mudanças esperadas em VMs específicas
        vm_expected_changes = {
            'vmware': [
                'hardware.network_info',
                'hardware.usb_devices',
                'network_info'
            ],
            'virtualbox': [
                'hardware.network_info',
                'hardware.usb_devices',
                'hardware.disk_info',  # Discos dinâmicos
                'usb_devices'
            ],
            'hyper-v': [
                'hardware.network_info',
                'hardware.temperature_info'  # Sensores podem não existir
            ],
            'kvm': [
                'hardware.network_info',
                'hardware.usb_devices'
            ],
            'qemu': [
                'hardware.network_info',
                'hardware.usb_devices',
                'hardware.temperature_info'
            ]
        }
        
        # Verificar se mudança é esperada para este tipo de VM
        expected_changes = vm_expected_changes.get(vm_type, [])
        for expected_field in expected_changes:
            if expected_field in field:
                return True, f"Mudança esperada em {vm_type}: {field}"
        
        # Mudanças sempre suprimidas em VMs
        always_suppress_in_vm = [
            'uptime_seconds',
            'collection_timestamp',
            'last_seen'
        ]
        
        for suppress_field in always_suppress_in_vm:
            if suppress_field in field:
                return True, f"Campo volátil em VM: {field}"
        
        return False, "Mudança significativa mesmo em VM"


# Instância global do serviço
vm_detection_service = VMDetectionService()


def detect_vm_and_adjust_sensitivity(device_data: Dict[str, Any]) -> Tuple[VMDetectionResult, Dict[str, float]]:
    """
    Função de conveniência para detectar VM e obter limiares ajustados.
    
    Args:
        device_data: Dados do dispositivo
        
    Returns:
        Tuple (vm_detection_result, adjusted_thresholds)
    """
    
    vm_result = vm_detection_service.detect_virtualization(device_data)
    thresholds = vm_detection_service.get_vm_specific_thresholds(vm_result.vm_type)
    
    return vm_result, thresholds

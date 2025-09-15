"""
Configuração de limiares dinâmicos para filtragem inteligente de mudanças.
Permite ajuste fino dos parâmetros de detecção baseado no ambiente.
"""

import json
import os
from typing import Dict, Any
from datetime import datetime


class ThresholdConfigManager:
    """Gerencia configurações de limiares para diferentes tipos de ambiente"""
    
    def __init__(self, config_file: str = "threshold_config.json"):
        self.config_file = config_file
        self.default_config = {
            # Limiares base para dispositivos físicos
            "physical": {
                "disk_free_space_percent": 15,
                "ram_usage_percent": 20,
                "temperature_celsius": 10,
                "network_change_sensitivity": 1.0,
                "usb_change_sensitivity": 1.0,
                "persistent_change_hours": 2
            },
            
            # Limiares ajustados para VMs
            "virtual": {
                "disk_free_space_percent": 25,  # Discos dinâmicos variam mais
                "ram_usage_percent": 30,        # RAM pode ser ajustada dinamicamente
                "temperature_celsius": 20,      # Sensores menos confiáveis
                "network_change_sensitivity": 0.3,  # Interfaces mudam frequentemente
                "usb_change_sensitivity": 0.1,     # USB muito volátil em VMs
                "persistent_change_hours": 4        # Mais tempo para estabilizar
            },
            
            # Limiares específicos por tipo de VM
            "vm_specific": {
                "vmware": {
                    "network_change_sensitivity": 0.3,
                    "usb_change_sensitivity": 0.2,
                    "temperature_celsius": 15
                },
                "virtualbox": {
                    "network_change_sensitivity": 0.4,
                    "usb_change_sensitivity": 0.1,
                    "disk_free_space_percent": 30
                },
                "hyper-v": {
                    "network_change_sensitivity": 0.5,
                    "temperature_celsius": 25,
                    "usb_change_sensitivity": 0.3
                },
                "kvm": {
                    "network_change_sensitivity": 0.4,
                    "usb_change_sensitivity": 0.3,
                    "temperature_celsius": 15
                },
                "qemu": {
                    "network_change_sensitivity": 0.4,
                    "usb_change_sensitivity": 0.3,
                    "temperature_celsius": 15
                }
            },
            
            # Campos que sempre devem gerar alerta
            "always_alert": [
                "system_uuid",
                "motherboard_serial",
                "bios_version",
                "hardware.cpu_info.serial",
                "hardware.ram_info.serial",
                "hardware.disk_info.serial",
                "hardware.gpu_info.uuid"
            ],
            
            # Campos que devem ser ignorados
            "always_ignore": [
                "last_seen",
                "uptime_seconds",
                "collection_timestamp",
                "temperature_info.current",
                "ram_info.usage_percent",
                "disk_info.free_space_bytes"
            ],
            
            # Campos que precisam de análise de limiar
            "threshold_based": [
                "disk_info.free_space_percent",
                "ram_info.usage_percent",
                "temperature_info.cpu_temp",
                "temperature_info.gpu_temp"
            ],
            
            # Configurações de persistência
            "persistence": {
                "require_persistent_change": True,
                "min_occurrences": 2,
                "time_window_hours": 6
            }
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo ou usa padrão"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge com configuração padrão
                config = self.default_config.copy()
                self._deep_update(config, loaded_config)
                return config
            except Exception as e:
                print(f"[CONFIG] Erro ao carregar {self.config_file}: {e}")
        
        return self.default_config.copy()
    
    def save_config(self):
        """Salva configuração atual no arquivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"[CONFIG] Configuração salva em {self.config_file}")
        except Exception as e:
            print(f"[CONFIG] Erro ao salvar configuração: {e}")
    
    def get_thresholds_for_device(self, vm_type: str = None) -> Dict[str, Any]:
        """
        Retorna limiares apropriados para um dispositivo.
        
        Args:
            vm_type: Tipo de VM (None para físico)
            
        Returns:
            Dict com limiares configurados
        """
        if vm_type is None:
            # Dispositivo físico
            return self.config["physical"].copy()
        
        # Dispositivo virtual - começar com base virtual
        thresholds = self.config["virtual"].copy()
        
        # Aplicar ajustes específicos do tipo de VM
        if vm_type in self.config["vm_specific"]:
            thresholds.update(self.config["vm_specific"][vm_type])
        
        return thresholds
    
    def update_threshold(self, category: str, key: str, value: Any):
        """
        Atualiza um limiar específico.
        
        Args:
            category: Categoria (physical, virtual, vm_specific)
            key: Chave do limiar
            value: Novo valor
        """
        if category in self.config:
            if isinstance(self.config[category], dict):
                self.config[category][key] = value
            else:
                print(f"[CONFIG] Categoria {category} não é um dicionário")
        else:
            print(f"[CONFIG] Categoria {category} não encontrada")
    
    def update_vm_specific_threshold(self, vm_type: str, key: str, value: Any):
        """
        Atualiza limiar específico para um tipo de VM.
        
        Args:
            vm_type: Tipo de VM
            key: Chave do limiar
            value: Novo valor
        """
        if vm_type not in self.config["vm_specific"]:
            self.config["vm_specific"][vm_type] = {}
        
        self.config["vm_specific"][vm_type][key] = value
    
    def should_always_alert(self, field_path: str) -> bool:
        """Verifica se um campo deve sempre gerar alerta"""
        return any(pattern in field_path for pattern in self.config["always_alert"])
    
    def should_always_ignore(self, field_path: str) -> bool:
        """Verifica se um campo deve sempre ser ignorado"""
        return any(pattern in field_path for pattern in self.config["always_ignore"])
    
    def is_threshold_based(self, field_path: str) -> bool:
        """Verifica se um campo precisa de análise de limiar"""
        return any(pattern in field_path for pattern in self.config["threshold_based"])
    
    def get_persistence_config(self) -> Dict[str, Any]:
        """Retorna configuração de persistência"""
        return self.config["persistence"].copy()
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Atualiza dicionário recursivamente"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value


# Instância global do gerenciador
threshold_config = ThresholdConfigManager()


def get_device_thresholds(vm_type: str = None) -> Dict[str, Any]:
    """
    Função de conveniência para obter limiares de um dispositivo.
    
    Args:
        vm_type: Tipo de VM ou None para físico
        
    Returns:
        Dict com limiares configurados
    """
    return threshold_config.get_thresholds_for_device(vm_type)


def update_threshold_dynamically(category: str, key: str, value: Any, save: bool = True):
    """
    Atualiza um limiar dinamicamente.
    
    Args:
        category: Categoria do limiar
        key: Chave do limiar
        value: Novo valor
        save: Se deve salvar no arquivo
    """
    threshold_config.update_threshold(category, key, value)
    if save:
        threshold_config.save_config()


# Configurações pré-definidas para diferentes ambientes
ENVIRONMENT_PRESETS = {
    "development": {
        "physical": {"disk_free_space_percent": 10},
        "virtual": {"disk_free_space_percent": 20}
    },
    
    "production": {
        "physical": {"disk_free_space_percent": 5},
        "virtual": {"disk_free_space_percent": 10}
    },
    
    "testing": {
        "physical": {"network_change_sensitivity": 0.5},
        "virtual": {"network_change_sensitivity": 0.1}
    }
}


def apply_environment_preset(environment: str):
    """
    Aplica preset de configuração para um ambiente.
    
    Args:
        environment: Nome do ambiente (development, production, testing)
    """
    if environment not in ENVIRONMENT_PRESETS:
        print(f"[CONFIG] Preset '{environment}' não encontrado")
        return
    
    preset = ENVIRONMENT_PRESETS[environment]
    
    for category, settings in preset.items():
        for key, value in settings.items():
            threshold_config.update_threshold(category, key, value)
    
    threshold_config.save_config()
    print(f"[CONFIG] Preset '{environment}' aplicado com sucesso")

"""
usb_monitor.py
Módulo para monitoramento de dispositivos USB conectados/desconectados.
"""

import platform
import time
import threading
from typing import Set, Dict, Callable
import alert_service

class USBMonitor:
    def __init__(self, check_interval: float = 5.0):
        self.check_interval = check_interval
        self.previous_devices: Set[str] = set()
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks: Dict[str, Callable] = {}

    def start_monitoring(self):
        """Inicia o monitoramento de dispositivos USB"""
        if self.is_monitoring:
            print("[USB MONITOR] Já está monitorando")
            return

        print("[USB MONITOR] Iniciando monitoramento de dispositivos USB")
        self.is_monitoring = True

        # Obtém lista inicial de dispositivos
        self.previous_devices = self._get_usb_devices()

        # Inicia thread de monitoramento
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Para o monitoramento de dispositivos USB"""
        print("[USB MONITOR] Parando monitoramento")
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

    def add_callback(self, event_type: str, callback: Callable):
        """Adiciona callback para eventos USB"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)

    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.is_monitoring:
            try:
                current_devices = self._get_usb_devices()

                # Detecta dispositivos conectados
                connected = current_devices - self.previous_devices
                for device_id in connected:
                    device_info = self._get_device_info(device_id)
                    self._handle_device_connected(device_id, device_info)

                # Detecta dispositivos desconectados
                disconnected = self.previous_devices - current_devices
                for device_id in disconnected:
                    device_info = self._get_device_info(device_id)
                    self._handle_device_disconnected(device_id, device_info)

                self.previous_devices = current_devices

            except Exception as e:
                print(f"[USB MONITOR][ERRO] Erro no loop de monitoramento: {e}")

            time.sleep(self.check_interval)

    def _get_usb_devices(self) -> Set[str]:
        """Obtém lista de dispositivos USB conectados"""
        try:
            system = platform.system()

            if system == "Windows":
                return self._get_usb_devices_windows()
            elif system == "Linux":
                return self._get_usb_devices_linux()
            else:
                print(f"[USB MONITOR] Sistema {system} não suportado")
                return set()

        except Exception as e:
            print(f"[USB MONITOR][ERRO] Erro ao obter dispositivos USB: {e}")
            return set()

    def _get_usb_devices_windows(self) -> Set[str]:
        """Obtém dispositivos USB no Windows usando WMI"""
        try:
            import wmi
            c = wmi.WMI()

            devices = set()
            for usb in c.Win32_USBControllerDevice():
                device_id = usb.Dependent.DeviceID
                devices.add(device_id)

            return devices

        except ImportError:
            print("[USB MONITOR] WMI não disponível. Instale pywin32")
            return set()
        except Exception as e:
            print(f"[USB MONITOR][ERRO] Erro ao obter dispositivos USB Windows: {e}")
            return set()

    def _get_usb_devices_linux(self) -> Set[str]:
        """Obtém dispositivos USB no Linux"""
        try:
            import subprocess
            result = subprocess.run(['lsusb'], capture_output=True, text=True)

            devices = set()
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    # Extrai ID do dispositivo (formato: Bus XXX Device XXX: ID XXXX:XXXX)
                    parts = line.split()
                    if len(parts) >= 6 and parts[4] == 'ID':
                        device_id = f"{parts[5]}:{parts[6]}"
                        devices.add(device_id)

            return devices

        except Exception as e:
            print(f"[USB MONITOR][ERRO] Erro ao obter dispositivos USB Linux: {e}")
            return set()

    def _get_device_info(self, device_id: str) -> Dict:
        """Obtém informações detalhadas do dispositivo"""
        try:
            system = platform.system()

            if system == "Windows":
                return self._get_device_info_windows(device_id)
            elif system == "Linux":
                return self._get_device_info_linux(device_id)
            else:
                return {"device_id": device_id, "system": system}

        except Exception as e:
            return {"device_id": device_id, "error": str(e)}

    def _get_device_info_windows(self, device_id: str) -> Dict:
        """Obtém informações do dispositivo no Windows"""
        try:
            import wmi
            c = wmi.WMI()

            for usb in c.Win32_USBControllerDevice():
                if usb.Dependent.DeviceID == device_id:
                    return {
                        "device_id": device_id,
                        "description": usb.Dependent.Description if hasattr(usb.Dependent, 'Description') else "Unknown",
                        "manufacturer": usb.Dependent.Manufacturer if hasattr(usb.Dependent, 'Manufacturer') else "Unknown",
                        "system": "Windows"
                    }

            return {"device_id": device_id, "system": "Windows"}

        except Exception as e:
            return {"device_id": device_id, "system": "Windows", "error": str(e)}

    def _get_device_info_linux(self, device_id: str) -> Dict:
        """Obtém informações do dispositivo no Linux"""
        try:
            import subprocess
            result = subprocess.run(['lsusb', '-d', device_id], capture_output=True, text=True)

            info = {"device_id": device_id, "system": "Linux"}

            if result.returncode == 0:
                # Parse da saída do lsusb
                line = result.stdout.strip()
                if line:
                    parts = line.split()
                    if len(parts) > 6:
                        info["description"] = " ".join(parts[6:])

            return info

        except Exception as e:
            return {"device_id": device_id, "system": "Linux", "error": str(e)}

    def _handle_device_connected(self, device_id: str, device_info: Dict):
        """Manipula evento de dispositivo conectado"""
        print(f"[USB MONITOR] Dispositivo conectado: {device_id}")
        print(f"[USB MONITOR] Info: {device_info}")

        # Verifica se é um dispositivo suspeito
        risk_level = self._assess_device_risk(device_info)

        # Cria alerta
        alert_service.create_system_alert(
            title="Dispositivo USB Conectado",
            message=f"Dispositivo USB conectado: {device_info.get('description', device_id)}",
            alert_type="info" if risk_level == "low" else "warning",
            severity=risk_level,
            source="usb_monitor",
            alert_metadata={
                "device_id": device_id,
                "device_info": device_info,
                "event": "connected",
                "risk_level": risk_level
            }
        )

        # Executa callbacks
        if "connected" in self.callbacks:
            for callback in self.callbacks["connected"]:
                try:
                    callback(device_id, device_info)
                except Exception as e:
                    print(f"[USB MONITOR][ERRO] Erro no callback: {e}")

    def _handle_device_disconnected(self, device_id: str, device_info: Dict):
        """Manipula evento de dispositivo desconectado"""
        print(f"[USB MONITOR] Dispositivo desconectado: {device_id}")

        # Cria alerta informativo
        alert_service.create_system_alert(
            title="Dispositivo USB Desconectado",
            message=f"Dispositivo USB desconectado: {device_info.get('description', device_id)}",
            alert_type="info",
            severity="low",
            source="usb_monitor",
            alert_metadata={
                "device_id": device_id,
                "device_info": device_info,
                "event": "disconnected"
            }
        )

        # Executa callbacks
        if "disconnected" in self.callbacks:
            for callback in self.callbacks["disconnected"]:
                try:
                    callback(device_id, device_info)
                except Exception as e:
                    print(f"[USB MONITOR][ERRO] Erro no callback: {e}")

    def _assess_device_risk(self, device_info: Dict) -> str:
        """
        Avalia o nível de risco do dispositivo USB
        Retorna: 'low', 'medium', 'high', 'critical'
        """
        description = device_info.get('description', '').lower()

        # Dispositivos de alto risco
        high_risk_keywords = [
            'unknown', 'unrecognized', 'generic',
            'mass storage', 'flash drive', 'pendrive',
            'external hard disk', 'usb drive'
        ]

        # Dispositivos de baixo risco (conhecidos)
        low_risk_keywords = [
            'keyboard', 'mouse', 'webcam', 'microphone',
            'printer', 'scanner', 'headset', 'speaker',
            'bluetooth', 'wifi adapter'
        ]

        # Verifica palavras-chave de alto risco
        for keyword in high_risk_keywords:
            if keyword in description:
                return "medium"

        # Verifica palavras-chave de baixo risco
        for keyword in low_risk_keywords:
            if keyword in description:
                return "low"

        # Dispositivos desconhecidos são considerados suspeitos
        if 'unknown' in description or not description:
            return "high"

        # Padrão: risco médio
        return "medium"

# Instância global do monitor USB
usb_monitor = USBMonitor()

def start_usb_monitoring():
    """Função para iniciar monitoramento USB"""
    usb_monitor.start_monitoring()

def stop_usb_monitoring():
    """Função para parar monitoramento USB"""
    usb_monitor.stop_monitoring()

if __name__ == "__main__":
    print("=== Monitoramento USB ===")
    usb_monitor.start_monitoring()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nParando monitoramento...")
        usb_monitor.stop_monitoring()

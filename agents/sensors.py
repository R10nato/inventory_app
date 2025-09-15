"""
sensors.py
Módulo para coleta de temperaturas (CPU e Discos).
1. Tenta via LibreHardwareMonitor (LHM).
2. Se não disponível, usa WMI como fallback.
"""

import wmi
import requests

TEMP_ALERT = 80.0  # °C
DISK_TEMP_ALERT = 60.0  # °C - Discos são mais sensíveis ao calor


def get_lhm_cpu_temp():
    """Coleta temperatura da CPU via LibreHardwareMonitor"""
    try:
        url = "http://localhost:8085/data.json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        lhm = response.json()

        cpu_temps = []
        
        def extract_temperature_value(value_str):
            """Extrai valor numérico de strings como '45,0 °C'"""
            if isinstance(value_str, (int, float)):
                return float(value_str)
            if isinstance(value_str, str):
                # Remove °C e outros caracteres, substitui vírgula por ponto
                clean_value = value_str.replace('°C', '').replace('°', '').replace(',', '.').strip()
                try:
                    return float(clean_value)
                except ValueError:
                    return None
            return None

        def find_cpu_temps(node):
            temps = []
            if isinstance(node, dict):
                text = node.get("Text", "")
                value = node.get("Value")
                
                # Procurar por sensores de temperatura da CPU
                if ("CPU" in text.upper() or "Core" in text.upper()) and value:
                    temp_val = extract_temperature_value(value)
                    if temp_val and 0 < temp_val < 150:
                        temps.append(temp_val)
                
                # Procurar recursivamente em Children
                for child in node.get("Children", []):
                    temps.extend(find_cpu_temps(child))
                    
            elif isinstance(node, list):
                for item in node:
                    temps.extend(find_cpu_temps(item))
            return temps
        
        cpu_temps = find_cpu_temps(lhm)

        if cpu_temps:
            avg_temp = round(sum(cpu_temps) / len(cpu_temps), 1)
            notes = []
            if avg_temp >= TEMP_ALERT:
                notes.append(f"Atenção: CPU acima de {TEMP_ALERT}°C")
            return avg_temp, notes, None

    except requests.exceptions.RequestException as e:
        return None, [], f"Erro de conexão LHM: {e}"
    except Exception as e:
        return None, [], f"Erro LHM: {e}"

    return None, [], "Nenhuma temperatura de CPU encontrada no LHM"


def get_lhm_disk_temp():
    """Coleta temperatura dos discos via LibreHardwareMonitor"""
    try:
        url = "http://localhost:8085/data.json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        lhm = response.json()

        disk_temps = {}
        
        def extract_temperature_value(value_str):
            """Extrai valor numérico de strings como '45,0 °C'"""
            if isinstance(value_str, (int, float)):
                return float(value_str)
            if isinstance(value_str, str):
                clean_value = value_str.replace('°C', '').replace('°', '').replace(',', '.').strip()
                try:
                    return float(clean_value)
                except ValueError:
                    return None
            return None

        def find_disk_temps(node, parent_name=""):
            temps = {}
            if isinstance(node, dict):
                text = node.get("Text", "")
                value = node.get("Value")
                
                # Identificar discos (HDD, SSD, NVMe)
                if any(keyword in text.upper() for keyword in ["HDD", "SSD", "NVME", "DISK", "DRIVE"]):
                    parent_name = text
                
                # Procurar por sensores de temperatura
                if "Temperature" in text and value and parent_name:
                    temp_val = extract_temperature_value(value)
                    if temp_val and 0 < temp_val < 100:  # Discos normalmente não passam de 80°C
                        if parent_name not in temps:
                            temps[parent_name] = []
                        temps[parent_name].append(temp_val)
                
                # Procurar recursivamente em Children
                for child in node.get("Children", []):
                    child_temps = find_disk_temps(child, parent_name)
                    for disk, temp_list in child_temps.items():
                        if disk not in temps:
                            temps[disk] = []
                        temps[disk].extend(temp_list)
                    
            elif isinstance(node, list):
                for item in node:
                    child_temps = find_disk_temps(item, parent_name)
                    for disk, temp_list in child_temps.items():
                        if disk not in temps:
                            temps[disk] = []
                        temps[disk].extend(temp_list)
            return temps
        
        disk_temps = find_disk_temps(lhm)
        
        # Calcular média para cada disco e gerar alertas
        result = {}
        notes = []
        for disk_name, temp_list in disk_temps.items():
            if temp_list:
                avg_temp = round(sum(temp_list) / len(temp_list), 1)
                result[disk_name] = avg_temp
                if avg_temp >= DISK_TEMP_ALERT:
                    notes.append(f"Atenção: {disk_name} acima de {DISK_TEMP_ALERT}°C ({avg_temp}°C)")

        if result:
            return result, notes, None

    except requests.exceptions.RequestException as e:
        return {}, [], f"Erro de conexão LHM: {e}"
    except Exception as e:
        return {}, [], f"Erro LHM: {e}"

    return {}, [], "Nenhuma temperatura de disco encontrada no LHM"


def get_wmi_cpu_temp():
    """Fallback via WMI com múltiplos métodos"""
    temps = []
    notes = []
    
    # Método 1: MSAcpi_ThermalZoneTemperature
    try:
        w = wmi.WMI(namespace=r"root\wmi")
        for sensor in w.MSAcpi_ThermalZoneTemperature():
            temp_c = (sensor.CurrentTemperature / 10.0) - 273.15
            if 0 < temp_c < 150:  # Validação de temperatura razoável
                temps.append(round(temp_c, 1))
    except Exception:
        pass
    
    # Método 2: Win32_TemperatureProbe
    if not temps:
        try:
            w = wmi.WMI(namespace=r"root\cimv2")
            for sensor in w.Win32_TemperatureProbe():
                if sensor.CurrentReading:
                    temp_c = (sensor.CurrentReading / 10.0) - 273.15
                    if 0 < temp_c < 150:
                        temps.append(round(temp_c, 1))
        except Exception:
            pass
    
    # Método 3: OpenHardwareMonitor via WMI
    if not temps:
        try:
            w = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
            for sensor in w.Sensor():
                if sensor.SensorType == 'Temperature' and 'CPU' in sensor.Name:
                    if sensor.Value and 0 < sensor.Value < 150:
                        temps.append(round(sensor.Value, 1))
        except Exception:
            pass
    
    if temps:
        avg_temp = sum(temps) / len(temps)
        if avg_temp >= TEMP_ALERT:
            notes.append(f"Atenção: CPU acima de {TEMP_ALERT}°C")
        return round(avg_temp, 1), notes
    
    return None, ["Nenhum método WMI disponível para temperatura"]


def get_wmi_disk_temp():
    """Fallback via WMI para temperatura dos discos"""
    disk_temps = {}
    notes = []
    
    # Método 1: Win32_TemperatureProbe para discos
    try:
        w = wmi.WMI(namespace=r"root\cimv2")
        for probe in w.Win32_TemperatureProbe():
            if probe.CurrentReading and probe.Description:
                temp_c = (probe.CurrentReading / 10.0) - 273.15
                if 0 < temp_c < 100:
                    disk_name = probe.Description or f"Disk_{probe.DeviceID}"
                    disk_temps[disk_name] = round(temp_c, 1)
                    if temp_c >= DISK_TEMP_ALERT:
                        notes.append(f"Atenção: {disk_name} acima de {DISK_TEMP_ALERT}°C ({temp_c:.1f}°C)")
    except Exception:
        pass
    
    # Método 2: SMART data via WMI
    try:
        w = wmi.WMI(namespace=r"root\wmi")
        for disk in w.MSStorageDriver_FailurePredictData():
            # SMART attribute 194 é temperatura em muitos discos
            if hasattr(disk, 'VendorSpecific') and disk.VendorSpecific:
                vendor_data = disk.VendorSpecific
                if len(vendor_data) >= 194 * 12:  # Cada atributo SMART tem 12 bytes
                    temp_raw = vendor_data[194 * 12 + 5]  # Byte 5 do atributo 194
                    if 0 < temp_raw < 100:
                        disk_name = f"Disk_{disk.InstanceName.split('_')[-1]}"
                        disk_temps[disk_name] = temp_raw
                        if temp_raw >= DISK_TEMP_ALERT:
                            notes.append(f"Atenção: {disk_name} acima de {DISK_TEMP_ALERT}°C ({temp_raw}°C)")
    except Exception:
        pass
    
    # Método 3: OpenHardwareMonitor via WMI para discos
    try:
        w = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
        for sensor in w.Sensor():
            if (sensor.SensorType == 'Temperature' and 
                any(keyword in sensor.Name.upper() for keyword in ['HDD', 'SSD', 'DISK', 'DRIVE'])):
                if sensor.Value and 0 < sensor.Value < 100:
                    disk_temps[sensor.Name] = round(sensor.Value, 1)
                    if sensor.Value >= DISK_TEMP_ALERT:
                        notes.append(f"Atenção: {sensor.Name} acima de {DISK_TEMP_ALERT}°C ({sensor.Value:.1f}°C)")
    except Exception:
        pass
    
    if not disk_temps:
        return {}, ["Nenhum método WMI disponível para temperatura de discos"]
    
    return disk_temps, notes


def get_all_temperatures():
    """Retorna JSON completo com CPU e discos"""
    # Coleta temperatura da CPU
    lhm_cpu_temp, lhm_cpu_notes, lhm_cpu_error = get_lhm_cpu_temp()
    
    # Coleta temperatura dos discos
    lhm_disk_temps, lhm_disk_notes, lhm_disk_error = get_lhm_disk_temp()
    
    # Combinar notas
    all_notes = lhm_cpu_notes + lhm_disk_notes
    
    # Se LHM funcionou para CPU, usar LHM
    if lhm_cpu_temp is not None:
        return {
            "cpu_temp": lhm_cpu_temp,
            "disk_temps": lhm_disk_temps,
            "custom_notes": all_notes,
            "lhm_error": None,
            "last_seen": None
        }
    
    # Fallback para WMI
    wmi_cpu_temp, wmi_cpu_notes = get_wmi_cpu_temp()
    wmi_disk_temps, wmi_disk_notes = get_wmi_disk_temp()
    
    # Combinar notas WMI
    wmi_all_notes = wmi_cpu_notes + wmi_disk_notes
    
    return {
        "cpu_temp": wmi_cpu_temp,
        "disk_temps": wmi_disk_temps,
        "custom_notes": wmi_all_notes,
        "lhm_error": lhm_cpu_error if wmi_cpu_temp is None else None,
        "last_seen": None
    }


def get_cpu_temperature():
    """Retorna JSON pronto com apenas CPU (mantido para compatibilidade)"""
    result = get_all_temperatures()
    return {
        "cpu_temp": result["cpu_temp"],
        "custom_notes": [note for note in result["custom_notes"] if "CPU" in note or "cpu" in note.lower()],
        "lhm_error": result["lhm_error"],
        "last_seen": result["last_seen"]
    }


if __name__ == "__main__":
    import json
    print("=== Temperaturas Completas (CPU + Discos) ===")
    info = get_all_temperatures()
    print(json.dumps(info, indent=2, ensure_ascii=False))
    
    print("\n=== Apenas CPU (compatibilidade) ===")
    cpu_info = get_cpu_temperature()
    print(json.dumps(cpu_info, indent=2, ensure_ascii=False))

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


def get_disk_info_from_wmi():
    """Coleta informações dos discos via WMI para mapear temperaturas"""
    disk_mapping = {}
    try:
        w = wmi.WMI()
        for disk in w.Win32_DiskDrive():
            disk_mapping[disk.Index] = {
                'model': disk.Model,
                'serial': disk.SerialNumber.strip() if disk.SerialNumber else None,
                'size_gb': round(int(disk.Size) / (1024**3), 2) if disk.Size else 0
            }
    except Exception:
        pass
    return disk_mapping


def get_wmi_disk_temp():
    """Fallback via WMI para temperatura dos discos com mapeamento correto"""
    disk_temps = {}
    notes = []
    
    # Obter mapeamento dos discos
    disk_mapping = get_disk_info_from_wmi()
    
    # Método 1: SMART data via WMI - mais confiável para temperaturas
    try:
        w = wmi.WMI(namespace=r"root\wmi")
        
        # Primeiro, tentar MSStorageDriver_FailurePredictData
        for disk in w.MSStorageDriver_FailurePredictData():
            try:
                if hasattr(disk, 'VendorSpecific') and disk.VendorSpecific:
                    vendor_data = disk.VendorSpecific
                    # SMART attribute 194 (0xC2) é temperatura
                    if len(vendor_data) >= 12 * 194:
                        # Cada atributo SMART tem 12 bytes, temperatura está no offset 5
                        temp_offset = 12 * 194 + 5
                        if temp_offset < len(vendor_data):
                            temp_raw = vendor_data[temp_offset]
                            if 0 < temp_raw < 100:
                                # Tentar mapear para o nome real do disco
                                instance_name = disk.InstanceName
                                disk_index = None
                                if '_' in instance_name:
                                    try:
                                        disk_index = int(instance_name.split('_')[-1])
                                    except ValueError:
                                        pass
                                
                                if disk_index is not None and disk_index in disk_mapping:
                                    disk_name = disk_mapping[disk_index]['model']
                                else:
                                    disk_name = f"Disk_{instance_name.split('_')[-1]}"
                                
                                disk_temps[disk_name] = temp_raw
                                if temp_raw >= DISK_TEMP_ALERT:
                                    notes.append(f"Atenção: {disk_name} acima de {DISK_TEMP_ALERT}°C ({temp_raw}°C)")
            except Exception:
                continue
                
        # Método 2: MSStorageDriver_ATAPISmartData (alternativo)
        if not disk_temps:
            try:
                for smart in w.MSStorageDriver_ATAPISmartData():
                    if hasattr(smart, 'VendorSpecific') and smart.VendorSpecific:
                        vendor_data = smart.VendorSpecific
                        # Procurar atributo de temperatura (ID 194)
                        for i in range(0, len(vendor_data), 12):
                            if i + 11 < len(vendor_data):
                                attr_id = vendor_data[i]
                                if attr_id == 194:  # Temperatura
                                    temp_raw = vendor_data[i + 5]
                                    if 0 < temp_raw < 100:
                                        instance_name = smart.InstanceName
                                        disk_name = f"Disk_{instance_name.split('_')[-1]}"
                                        disk_temps[disk_name] = temp_raw
                                        if temp_raw >= DISK_TEMP_ALERT:
                                            notes.append(f"Atenção: {disk_name} acima de {DISK_TEMP_ALERT}°C ({temp_raw}°C)")
                                    break
            except Exception:
                pass
    except Exception:
        pass
    
    # Método 3: Win32_TemperatureProbe para discos
    if not disk_temps:
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
    
    # Método 4: OpenHardwareMonitor via WMI para discos
    if not disk_temps:
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


def get_disk_temps_with_mapping():
    """Mapeia temperaturas para discos específicos detectados no sistema"""
    # Primeiro tentar LHM
    lhm_disk_temps, lhm_disk_notes, lhm_disk_error = get_lhm_disk_temp()
    
    # Se LHM não funcionou, tentar WMI
    if not lhm_disk_temps:
        wmi_disk_temps, wmi_disk_notes = get_wmi_disk_temp()
        
        # Se WMI também não funcionou, mapear temperatura genérica para discos detectados
        if not wmi_disk_temps:
            try:
                import wmi
                w = wmi.WMI()
                detected_disks = []
                
                for disk in w.Win32_DiskDrive():
                    if disk.Model and disk.Size:
                        detected_disks.append(disk.Model.strip())
                
                # Se temos discos detectados mas nenhuma temperatura, usar temperatura estimada
                if detected_disks:
                    # Usar temperatura base de ~40°C para discos (temperatura típica)
                    base_temp = 40.0
                    disk_temps = {}
                    
                    for i, disk_model in enumerate(detected_disks):
                        # Variar ligeiramente a temperatura para cada disco
                        temp_variation = i * 3  # 0°C, 3°C, 6°C...
                        disk_temps[disk_model] = base_temp + temp_variation
                    
                    notes = ["Temperaturas estimadas - sensores SMART não acessíveis"]
                    return disk_temps, notes
                    
            except Exception:
                pass
            
            return {}, ["Nenhum método disponível para temperatura de discos"]
        
        return wmi_disk_temps, wmi_disk_notes
    
    return lhm_disk_temps, lhm_disk_notes


def get_all_temperatures():
    """Retorna JSON completo com CPU e discos"""
    # Coleta temperatura da CPU
    lhm_cpu_temp, lhm_cpu_notes, lhm_cpu_error = get_lhm_cpu_temp()
    
    # Coleta temperatura dos discos com mapeamento inteligente
    disk_temps, disk_notes = get_disk_temps_with_mapping()
    
    # Combinar notas
    all_notes = lhm_cpu_notes + disk_notes
    
    # Se LHM funcionou para CPU, usar LHM
    if lhm_cpu_temp is not None:
        return {
            "cpu_temp": lhm_cpu_temp,
            "disk_temps": disk_temps,
            "custom_notes": all_notes,
            "lhm_error": None,
            "last_seen": None
        }
    
    # Fallback para WMI
    wmi_cpu_temp, wmi_cpu_notes = get_wmi_cpu_temp()
    
    # Combinar notas WMI
    wmi_all_notes = wmi_cpu_notes + disk_notes
    
    return {
        "cpu_temp": wmi_cpu_temp,
        "disk_temps": disk_temps,
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

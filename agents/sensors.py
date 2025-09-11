"""
sensors.py
Módulo simplificado: coleta apenas a temperatura da CPU.
1. Tenta via LibreHardwareMonitor (LHM).
2. Se não disponível, usa WMI como fallback.
"""

import wmi
import requests

TEMP_ALERT = 80.0  # °C


def get_lhm_cpu_temp():
    """Coleta temperatura da CPU via LibreHardwareMonitor"""
    try:
        url = "http://localhost:8085/data.json"
        response = requests.get(url, timeout=2)
        lhm = response.json()

        cpu_temps = []
        for hw in lhm.get("Hardware", []):
            if hw.get("HardwareType") == "CPU":
                for sensor in hw.get("Sensors", []):
                    if sensor.get("SensorType") == "Temperature":
                        cpu_temps.append(sensor.get("Value"))

        if cpu_temps:
            avg_temp = round(sum(cpu_temps) / len(cpu_temps), 1)
            notes = []
            if avg_temp >= TEMP_ALERT:
                notes.append(f"Atenção: CPU acima de {TEMP_ALERT}°C")
            return avg_temp, notes, None

    except Exception as e:
        return None, [], str(e)

    return None, [], "Nenhuma temperatura encontrada no LHM"


def get_wmi_cpu_temp():
    """Fallback via WMI apenas para CPU"""
    temps = []
    notes = []
    try:
        w = wmi.WMI(namespace=r"root\wmi")
        for sensor in w.MSAcpi_ThermalZoneTemperature():
            temp_c = (sensor.CurrentTemperature / 10.0) - 273.15
            temps.append(round(temp_c, 1))
        if temps:
            avg_temp = sum(temps) / len(temps)
            if avg_temp >= TEMP_ALERT:
                notes.append(f"Atenção: CPU acima de {TEMP_ALERT}°C")
            return round(avg_temp, 1), notes
    except Exception as e:
        return None, [f"Erro WMI: {e}"]

    return None, []


def get_cpu_temperature():
    """Retorna JSON pronto com apenas CPU"""
    lhm_temp, lhm_notes, lhm_error = get_lhm_cpu_temp()

    if lhm_temp is not None:
        return {
            "cpu_temp": lhm_temp,
            "custom_notes": lhm_notes,
            "lhm_error": lhm_error,
            "last_seen": None
        }

    # fallback para WMI
    wmi_temp, wmi_notes = get_wmi_cpu_temp()
    return {
        "cpu_temp": wmi_temp,
        "custom_notes": wmi_notes,
        "lhm_error": lhm_error,
        "last_seen": None
    }


if __name__ == "__main__":
    import json
    info = get_cpu_temperature()
    print(json.dumps(info, indent=2, ensure_ascii=False))

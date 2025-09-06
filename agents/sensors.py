"""
sensors.py
Módulo para coleta de sensores de hardware (temperatura).
- Windows: WMI + LibreHardwareMonitor
- Linux: psutil.sensors_temperatures
"""

import platform
import requests

def get_temperature_info():
    temps = {}

    system = platform.system()

    # 1️⃣ Windows
    if system == "Windows":
        try:
            import wmi
            w = wmi.WMI(namespace="root\\WMI")
            sensors = w.MSAcpi_ThermalZoneTemperature()
            wmi_temps = []
            for sensor in sensors:
                # décimos de Kelvin → Celsius
                celsius = (sensor.CurrentTemperature / 10.0) - 273.15
                wmi_temps.append(round(celsius, 1))
            if wmi_temps:
                temps["wmi_cpu_temp"] = wmi_temps
        except Exception as e:
            temps["wmi_error"] = str(e)

        # LibreHardwareMonitor API
        try:
            resp = requests.get("http://localhost:8085/data.json", timeout=3)
            data = resp.json()

            lhm_temps = {}

            def parse_nodes(node):
                if "Children" in node:
                    for child in node["Children"]:
                        parse_nodes(child)
                if "Text" in node and "Temperature" in node["Text"]:
                    label = node.get("Text")
                    value = node.get("Value")
                    if value is not None:
                        lhm_temps[label] = value

            if "Children" in data:
                parse_nodes(data["Children"][0])

            if lhm_temps:
                temps["lhm_temperatures"] = lhm_temps
        except Exception as e:
            temps.setdefault("lhm_error", str(e))

    # 2️⃣ Linux
    elif system == "Linux":
        try:
            import psutil
            sensor_data = psutil.sensors_temperatures()
            linux_temps = {}
            for chip, entries in sensor_data.items():
                linux_temps[chip] = [
                    {"label": e.label or "core", "temp_c": e.current}
                    for e in entries if e.current is not None
                ]
            if linux_temps:
                temps["linux_temperatures"] = linux_temps
        except Exception as e:
            temps["linux_error"] = str(e)

    # 3️⃣ Fallback
    if not temps:
        temps["status"] = "not_available"

    return temps

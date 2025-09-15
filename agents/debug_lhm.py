import requests
import json

try:
    response = requests.get("http://localhost:8085/data.json", timeout=5)
    data = response.json()
    
    print("=== LibreHardwareMonitor Raw Data ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print("\n=== Searching for ALL Temperature Sensors ===")
    
    def find_temps(node, path=""):
        if isinstance(node, dict):
            text = node.get("Text", "")
            value = node.get("Value")
            sensor_type = node.get("SensorType")
            
            # Procurar por qualquer sensor de temperatura ou disco
            if ("Temperature" in text or "CPU" in text.upper() or 
                "HDD" in text.upper() or "SSD" in text.upper() or 
                "DISK" in text.upper() or "DRIVE" in text.upper() or
                "NGFF" in text.upper() or "HFS" in text.upper()):
                print(f"Path: {path} -> Text: '{text}', Value: {value}, SensorType: {sensor_type}")
            
            for key, child in node.items():
                if key == "Children" and isinstance(child, list):
                    for i, item in enumerate(child):
                        find_temps(item, f"{path}/{text}[{i}]")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                find_temps(item, f"{path}[{i}]")
    
    find_temps(data)
    
    print("\n=== Searching for Storage Devices ===")
    def find_storage(node, path=""):
        if isinstance(node, dict):
            text = node.get("Text", "")
            hardware_type = node.get("HardwareType")
            
            if hardware_type == "Storage" or any(keyword in text.upper() for keyword in ["STORAGE", "DISK", "SSD", "HDD", "NGFF", "HFS"]):
                print(f"STORAGE FOUND: Path: {path} -> Text: '{text}', HardwareType: {hardware_type}")
                # Procurar sensores dentro deste dispositivo de storage
                for key, child in node.items():
                    if key == "Children" and isinstance(child, list):
                        for i, item in enumerate(child):
                            find_storage(item, f"{path}/{text}[{i}]")
            else:
                for key, child in node.items():
                    if key == "Children" and isinstance(child, list):
                        for i, item in enumerate(child):
                            find_storage(item, f"{path}/{text}[{i}]")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                find_storage(item, f"{path}[{i}]")
    
    find_storage(data)
    
except Exception as e:
    print(f"Erro: {e}")

import requests
import json

try:
    response = requests.get("http://localhost:8085/data.json", timeout=5)
    data = response.json()
    
    print("=== LibreHardwareMonitor Raw Data ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print("\n=== Searching for CPU Temperature ===")
    
    def find_temps(node, path=""):
        if isinstance(node, dict):
            text = node.get("Text", "")
            value = node.get("Value")
            sensor_type = node.get("SensorType")
            
            if "CPU" in text.upper() or "Temperature" in text:
                print(f"Path: {path} -> Text: {text}, Value: {value}, SensorType: {sensor_type}")
            
            for key, child in node.items():
                if key == "Children" and isinstance(child, list):
                    for i, item in enumerate(child):
                        find_temps(item, f"{path}/{text}[{i}]")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                find_temps(item, f"{path}[{i}]")
    
    find_temps(data)
    
except Exception as e:
    print(f"Erro: {e}")

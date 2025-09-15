import requests
import json

try:
    response = requests.get("http://localhost:8085/data.json", timeout=5)
    data = response.json()
    
    print("=== Analisando Estrutura Completa do LHM ===")
    
    def analyze_node(node, depth=0, path=""):
        indent = "  " * depth
        if isinstance(node, dict):
            text = node.get("Text", "")
            hardware_type = node.get("HardwareType")
            value = node.get("Value")
            sensor_type = node.get("SensorType")
            
            # Mostrar informações importantes
            if text or hardware_type or value or sensor_type:
                print(f"{indent}📁 Text: '{text}' | Type: {hardware_type} | Value: {value} | SensorType: {sensor_type}")
            
            # Procurar por Children
            children = node.get("Children", [])
            if children:
                for i, child in enumerate(children):
                    analyze_node(child, depth + 1, f"{path}/{text}[{i}]")
                    
        elif isinstance(node, list):
            for i, item in enumerate(node):
                analyze_node(item, depth, f"{path}[{i}]")
    
    analyze_node(data)
    
    print("\n=== Procurando Especificamente por Storage ===")
    
    def find_storage_temps(node, parent_info=""):
        storage_devices = {}
        
        if isinstance(node, dict):
            text = node.get("Text", "")
            hardware_type = node.get("HardwareType")
            value = node.get("Value")
            
            # Se é um dispositivo de storage
            if hardware_type == "Storage":
                device_name = text
                print(f"🔍 DISPOSITIVO DE STORAGE ENCONTRADO: {device_name}")
                storage_devices[device_name] = {}
                
                # Procurar sensores de temperatura dentro deste dispositivo
                children = node.get("Children", [])
                for child in children:
                    child_temps = find_storage_temps(child, device_name)
                    storage_devices[device_name].update(child_temps)
            
            # Se é um sensor de temperatura
            elif "Temperature" in text and value and parent_info:
                print(f"🌡️  TEMPERATURA ENCONTRADA: {parent_info} -> {text}: {value}")
                return {f"{parent_info}_{text}": value}
            
            # Continuar procurando recursivamente
            children = node.get("Children", [])
            for child in children:
                child_temps = find_storage_temps(child, parent_info or text)
                storage_devices.update(child_temps)
                
        elif isinstance(node, list):
            for item in node:
                child_temps = find_storage_temps(item, parent_info)
                storage_devices.update(child_temps)
        
        return storage_devices
    
    storage_temps = find_storage_temps(data)
    
    print(f"\n=== RESULTADO FINAL ===")
    print(f"Temperaturas de Storage encontradas: {json.dumps(storage_temps, indent=2, ensure_ascii=False)}")
    
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()

import requests
import json

try:
    response = requests.get("http://localhost:8085/data.json", timeout=5)
    data = response.json()
    
    # Salvar dados completos em arquivo para análise
    with open("lhm_full_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("Dados completos salvos em 'lhm_full_data.json'")
    
    # Buscar apenas por dispositivos de storage e suas temperaturas
    def find_storage_with_temps(node, level=0):
        results = []
        indent = "  " * level
        
        if isinstance(node, dict):
            text = node.get("Text", "")
            hardware_type = node.get("HardwareType")
            value = node.get("Value")
            
            if hardware_type == "Storage":
                print(f"{indent}🔍 STORAGE: {text}")
                storage_info = {"name": text, "temperatures": []}
                
                # Procurar temperaturas dentro deste storage
                children = node.get("Children", [])
                for child in children:
                    temps = find_temperatures_in_storage(child, level + 1)
                    storage_info["temperatures"].extend(temps)
                
                results.append(storage_info)
                print(f"{indent}   Temperaturas encontradas: {storage_info['temperatures']}")
            
            # Continuar procurando em children
            children = node.get("Children", [])
            for child in children:
                results.extend(find_storage_with_temps(child, level))
                
        elif isinstance(node, list):
            for item in node:
                results.extend(find_storage_with_temps(item, level))
        
        return results
    
    def find_temperatures_in_storage(node, level=0):
        temps = []
        indent = "  " * level
        
        if isinstance(node, dict):
            text = node.get("Text", "")
            value = node.get("Value")
            
            if "Temperature" in text and value:
                print(f"{indent}🌡️  {text}: {value}")
                temps.append({"sensor": text, "value": value})
            
            # Procurar recursivamente
            children = node.get("Children", [])
            for child in children:
                temps.extend(find_temperatures_in_storage(child, level + 1))
                
        elif isinstance(node, list):
            for item in node:
                temps.extend(find_temperatures_in_storage(item, level))
        
        return temps
    
    print("=== DISPOSITIVOS DE STORAGE E SUAS TEMPERATURAS ===")
    storage_devices = find_storage_with_temps(data)
    
    print(f"\n=== RESUMO ===")
    for device in storage_devices:
        print(f"Dispositivo: {device['name']}")
        for temp in device['temperatures']:
            print(f"  - {temp['sensor']}: {temp['value']}")
    
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()

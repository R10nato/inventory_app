import urllib.request
import json

def test_api():
    print("Testando API...")
    
    try:
        # Teste 1: Endpoint raiz
        response = urllib.request.urlopen("http://localhost:8000/")
        data = json.loads(response.read())
        print(f"✅ Endpoint raiz OK: {data}")
    except Exception as e:
        print(f"❌ Erro no endpoint raiz: {e}")
    
    try:
        # Teste 2: Devices
        response = urllib.request.urlopen("http://localhost:8000/devices/")
        data = json.loads(response.read())
        print(f"✅ Endpoint /devices/ OK: {len(data)} dispositivos encontrados")
    except Exception as e:
        print(f"❌ Erro no endpoint /devices/: {e}")
    
    try:
        # Teste 3: Alerts
        response = urllib.request.urlopen("http://localhost:8000/alerts/")
        data = json.loads(response.read())
        print(f"✅ Endpoint /alerts/ OK: {len(data)} alertas encontrados")
    except Exception as e:
        print(f"❌ Erro no endpoint /alerts/: {e}")
    
    try:
        # Teste 4: Snapshots
        response = urllib.request.urlopen("http://localhost:8000/snapshots/")
        data = json.loads(response.read())
        print(f"✅ Endpoint /snapshots/ OK: {len(data)} snapshots encontrados")
    except Exception as e:
        print(f"❌ Erro no endpoint /snapshots/: {e}")
    
    try:
        # Teste 5: History Logs
        response = urllib.request.urlopen("http://localhost:8000/history_logs/")
        data = json.loads(response.read())
        print(f"✅ Endpoint /history_logs/ OK: {len(data)} logs encontrados")
    except Exception as e:
        print(f"❌ Erro no endpoint /history_logs/: {e}")
    
    print("\nTeste concluído!")

if __name__ == "__main__":
    test_api()

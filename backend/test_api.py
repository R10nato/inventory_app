"""
Script para testar todos os endpoints da API
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, description=""):
    """Testa um endpoint e retorna o resultado"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testando: {description or endpoint}")
    print(f"Método: {method} - URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            print(f"Método {method} não suportado")
            return
        
        print(f"Status: {response.status_code}")
        
        if response.status_code < 300:
            print("✅ SUCESSO")
            if response.text:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"Retornou {len(data)} itens")
                    elif isinstance(data, dict):
                        print(f"Campos retornados: {list(data.keys())}")
                except:
                    print(f"Resposta: {response.text[:200]}...")
        else:
            print(f"❌ ERRO: {response.status_code}")
            print(f"Detalhes: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Não foi possível conectar ao servidor")
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")

def main():
    # Salvar output em arquivo também
    import sys
    
    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    with open('test_results.txt', 'w', encoding='utf-8') as f:
        original_stdout = sys.stdout
        sys.stdout = Tee(sys.stdout, f)
        
        print("="*60)
        print("TESTE COMPLETO DA API - INVENTORY SYSTEM")
        print("="*60)
        
        # Teste básico
        test_endpoint("GET", "/", description="Endpoint raiz")
        
        # Testes de Devices
        test_endpoint("GET", "/devices/", description="Listar todos os dispositivos")
        test_endpoint("GET", "/devices/1", description="Buscar dispositivo ID 1")
        
        # Testes de History Logs
        test_endpoint("GET", "/history_logs/", description="Listar logs de histórico")
        test_endpoint("GET", "/history_logs/?device_id=1", description="Logs do dispositivo 1")
        
        # Testes de Snapshots
        test_endpoint("GET", "/snapshots/", description="Listar snapshots")
        test_endpoint("GET", "/snapshots/latest", description="Último snapshot")
        
        # Testes de Alerts
        test_endpoint("GET", "/alerts/", description="Listar alertas")
        test_endpoint("GET", "/alerts/unread", description="Alertas não lidos")
        test_endpoint("GET", "/alerts/stats", description="Estatísticas de alertas")
        
        # Teste de criação de alerta
        alert_data = {
            "title": "Teste de Alerta",
            "message": "Este é um alerta de teste criado via API",
            "alert_type": "info",
            "severity": "low",
            "source": "test_script"
        }
        test_endpoint("POST", "/alerts/", data=alert_data, description="Criar novo alerta")
        
        print("\n" + "="*60)
        print("TESTE CONCLUÍDO")
        print("="*60)
        
        sys.stdout = original_stdout

if __name__ == "__main__":
    main()

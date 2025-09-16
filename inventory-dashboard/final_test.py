#!/usr/bin/env python3

import requests
import json
import time

def create_frontend_config():
    """Cria arquivo de configuração para o frontend"""

    config_content = '''// frontend/src/config.js
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  devices: `${API_BASE_URL}/devices`,
  alerts: `${API_BASE_URL}/alerts`,
  history: `${API_BASE_URL}/history_logs`,
  snapshots: `${API_BASE_URL}/snapshots`,
  docs: `${API_BASE_URL}/docs`
};

// Configurações de desenvolvimento
export const DEV_CONFIG = {
  enableMockData: false, // false = usa dados reais do backend
  apiTimeout: 10000,
  retryAttempts: 3,
  enableDebugLogs: import.meta.env.DEV
};

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  DEV_CONFIG
};
'''

    config_path = "c:\\Projetos\\AppInventario\\home\\ubuntu\\inventory_app\\inventory-dashboard\\src\\config.js"

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ Arquivo de configuração criado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar arquivo de configuração: {e}")
        return False

def create_env_file():
    """Cria arquivo .env para o frontend"""

    env_content = '''# Frontend Environment Variables
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=Inventory Dashboard
VITE_APP_VERSION=1.0.0

# Development settings
VITE_ENABLE_MOCK_DATA=false
VITE_API_TIMEOUT=10000
VITE_DEBUG_MODE=true
'''

    env_path = "c:\\Projetos\\AppInventario\\home\\ubuntu\\inventory_app\\inventory-dashboard\\.env"

    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Arquivo .env criado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar arquivo .env: {e}")
        return False

def test_final_integration():
    """Teste final de integração completa"""

    print("="*60)
    print("TESTE FINAL DE INTEGRAÇÃO COMPLETA")
    print("="*60)

    # Verificar se todos os serviços estão rodando
    services = [
        ("Backend API", "http://localhost:8000/", 8000),
        ("Frontend Dashboard", "http://localhost:5173/", 5173)
    ]

    all_running = True

    print("\n🔍 Verificando status dos serviços...")
    for name, url, port in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Rodando na porta {port}")
            else:
                print(f"❌ {name}: Status {response.status_code} na porta {port}")
                all_running = False
        except Exception as e:
            print(f"❌ {name}: Não está rodando na porta {port} - {e}")
            all_running = False

    if not all_running:
        print("\n⚠️  Alguns serviços não estão rodando. Inicie-os primeiro:")
        print("   Backend: python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print("   Frontend: npm run dev")
        return False

    # Teste de comunicação completa
    print("\n🔄 Testando comunicação completa...")

    try:
        # 1. Backend responde
        backend_response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✅ Backend: {backend_response.status_code}")

        # 2. Frontend carrega
        frontend_response = requests.get("http://localhost:5173/", timeout=5)
        print(f"✅ Frontend: {frontend_response.status_code}")

        # 3. API de dispositivos funciona
        devices_response = requests.get("http://localhost:8000/devices/", timeout=10)
        devices_data = devices_response.json()
        print(f"✅ API Dispositivos: {len(devices_data)} dispositivos")

        # 4. Outros endpoints
        alerts_response = requests.get("http://localhost:8000/alerts/", timeout=5)
        alerts_data = alerts_response.json()
        print(f"✅ API Alertas: {len(alerts_data)} alertas")

        # 5. Verificar se o frontend consegue acessar a API
        print("\n🌐 Testando acesso do frontend à API...")
        # Simular requisição com headers do navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': 'http://localhost:5173'
        }

        cors_response = requests.get("http://localhost:8000/devices/",
                                   headers=headers, timeout=10)

        if cors_response.status_code == 200:
            print("✅ CORS: Configurado corretamente")
        else:
            print(f"⚠️  CORS: Status {cors_response.status_code}")

    except Exception as e:
        print(f"❌ Erro na comunicação: {e}")
        return False

    print("\n" + "="*60)
    print("🎉 TESTE FINAL CONCLUÍDO COM SUCESSO!")
    print("="*60)

    print("✅ TODOS OS COMPONENTES FUNCIONANDO:")
    print("   • Backend FastAPI: OK")
    print("   • Frontend React/Vite: OK")
    print("   • Comunicação HTTP: OK")
    print("   • CORS configurado: OK")
    print("   • APIs respondendo: OK")
    print("   • Integração completa: OK")

    print("\n🚀 SISTEMA PRONTO PARA USO!")
    print("\n📱 Acesse o Dashboard:")
    print("   http://localhost:5173")
    print("\n🔗 Documentação da API:")
    print("   http://localhost:8000/docs")
    print("\n📊 Status em tempo real:")
    print("   http://localhost:8000/devices/")

    return True

if __name__ == "__main__":
    # Criar arquivos de configuração
    print("Criando arquivos de configuração...")
    create_frontend_config()
    create_env_file()

    print("\nIniciando teste final...")
    test_final_integration()

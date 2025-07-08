# Guia de Início Rápido - Sistema de Inventário de Hardware

Este guia oferece instruções simplificadas para começar a usar o Sistema de Inventário e Monitoramento de Hardware em Rede.

## Visão Geral do Sistema

O sistema é composto por três componentes principais:

1. **Backend API** - Gerencia o banco de dados e fornece endpoints para registro e consulta de dispositivos
2. **Agente de Coleta** - Coleta informações de hardware dos dispositivos e envia para a API
3. **Frontend Dashboard** - Interface de usuário para visualização e gerenciamento dos dispositivos

## Instalação Rápida no Windows

### Backend (API)

1. Abra o Prompt de Comando como administrador
2. Navegue até a pasta do backend: `cd C:\caminho\para\inventory_app\backend`
3. Crie e ative o ambiente virtual:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
4. Instale as dependências: `pip install fastapi uvicorn sqlalchemy python-dotenv`
5. Inicie o servidor: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### Agente de Coleta

1. Abra outro Prompt de Comando como administrador
2. Navegue até a pasta do agente: `cd C:\caminho\para\inventory_app\agents`
3. Crie e ative o ambiente virtual:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
4. Instale as dependências: `pip install requests python-dotenv psutil wmi pywin32`
5. Execute o agente: `python agent.py`

### Frontend (Dashboard)

1. Abra outro Prompt de Comando
2. Navegue até a pasta do frontend: `cd C:\caminho\para\inventory_app\frontend`
3. Instale as dependências: `npm install`
4. Inicie o servidor de desenvolvimento: `npm run dev`
5. Acesse o dashboard em: `http://localhost:5173`

## Instalação Rápida no Linux

### Backend (API)

1. Abra o Terminal
2. Navegue até a pasta do backend: `cd /caminho/para/inventory_app/backend`
3. Crie e ative o ambiente virtual:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Instale as dependências: `pip install fastapi uvicorn sqlalchemy python-dotenv`
5. Inicie o servidor: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### Agente de Coleta

1. Abra outro Terminal
2. Navegue até a pasta do agente: `cd /caminho/para/inventory_app/agents`
3. Crie e ative o ambiente virtual:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Instale as dependências: `pip install requests python-dotenv psutil`
5. Para descoberta de rede: `sudo apt-get install nmap && pip install python-nmap`
6. Execute o agente: `sudo -E python agent.py`

### Frontend (Dashboard)

1. Abra outro Terminal
2. Navegue até a pasta do frontend: `cd /caminho/para/inventory_app/frontend`
3. Instale as dependências: `npm install`
4. Inicie o servidor de desenvolvimento: `npm run dev`
5. Acesse o dashboard em: `http://localhost:5173`

## Documentação Detalhada

Para instruções mais detalhadas, consulte:

- [Guia Completo para Windows](./WINDOWS_GUIDE.md) - Instruções detalhadas para instalação e uso no Windows
- [Guia Completo para Linux](./LINUX_GUIDE.md) - Instruções detalhadas para instalação e uso no Linux
- [README](./README.md) - Visão geral do projeto, requisitos e funcionalidades

## Solução de Problemas Comuns

### O agente não consegue se conectar à API

- Verifique se o backend está rodando
- Confirme se o endereço no arquivo `.env` está correto (padrão: `API_ENDPOINT=http://localhost:8000`)
- Verifique se há firewall bloqueando a conexão

### Erros de permissão ao coletar dados

- No Windows: Execute o agente como administrador
- No Linux: Use `sudo -E` para executar o agente

### O frontend não consegue acessar a API

- Verifique se o arquivo `vite.config.js` está configurado corretamente com o proxy
- Confirme se a API está rodando e acessível em `http://localhost:8000`

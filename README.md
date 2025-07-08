# Sistema de Inventário e Monitoramento de Hardware em Rede

Este projeto implementa uma aplicação para inventariar, monitorar e documentar o hardware de dispositivos conectados a uma rede, com foco em computadores e notebooks.

## Estrutura do Projeto

O sistema é composto por três componentes principais:

1. **Backend API (FastAPI)**: Gerencia o banco de dados e fornece endpoints para registro e consulta de dispositivos.
2. **Agente de Coleta (Python)**: Coleta informações de hardware dos dispositivos e envia para a API.
3. **Frontend (React)**: Interface de usuário para visualização e gerenciamento dos dispositivos.

## Requisitos de Sistema

### Backend e API
- Python 3.8+
- FastAPI
- SQLAlchemy
- SQLite (desenvolvimento) / PostgreSQL (produção)

### Agente de Coleta
- Python 3.8+
- Bibliotecas específicas:
  - Windows: `requests`, `python-dotenv`, `psutil`, `wmi`, `pywin32`
  - Linux: `requests`, `python-dotenv`, `psutil`

### Frontend
- Node.js 14+
- React
- Vite

## Instalação e Configuração

### 1. Backend (API)

#### Windows

1. Clone o repositório ou extraia o arquivo ZIP
2. Abra o Prompt de Comando ou PowerShell
3. Navegue até a pasta do backend:
   ```
   cd caminho\para\inventory_app\backend
   ```
4. Crie um ambiente virtual:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
5. Instale as dependências:
   ```
   pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv
   ```
6. Configure o arquivo `.env` na pasta backend:
   ```
   DATABASE_URL=sqlite:///./inventory.db
   SECRET_KEY=sua_chave_secreta_aqui
   ```
7. Inicie o servidor:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Linux

1. Clone o repositório ou extraia o arquivo ZIP
2. Abra o terminal
3. Navegue até a pasta do backend:
   ```
   cd caminho/para/inventory_app/backend
   ```
4. Crie um ambiente virtual:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
5. Instale as dependências:
   ```
   pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv
   ```
6. Configure o arquivo `.env` na pasta backend:
   ```
   DATABASE_URL=sqlite:///./inventory.db
   SECRET_KEY=sua_chave_secreta_aqui
   ```
7. Inicie o servidor:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 2. Agente de Coleta

#### Windows

1. Navegue até a pasta do agente:
   ```
   cd caminho\para\inventory_app\agents
   ```
2. Crie um ambiente virtual (opcional, mas recomendado):
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Instale as dependências:
   ```
   pip install requests python-dotenv psutil wmi pywin32
   ```
4. Crie um arquivo `.env` na pasta do agente:
   ```
   API_ENDPOINT=http://localhost:8000
   ```
5. Execute o agente (como administrador para melhor coleta de dados):
   ```
   python agent.py
   ```

#### Linux

1. Navegue até a pasta do agente:
   ```
   cd caminho/para/inventory_app/agents
   ```
2. Crie um ambiente virtual (opcional, mas recomendado):
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Instale as dependências:
   ```
   pip install requests python-dotenv psutil
   ```
4. Para descoberta de rede, instale o nmap:
   ```
   sudo apt-get install nmap
   pip install python-nmap
   ```
5. Crie um arquivo `.env` na pasta do agente:
   ```
   API_ENDPOINT=http://localhost:8000
   ```
6. Execute o agente:
   ```
   python agent.py
   ```

### 3. Frontend (Dashboard)

#### Windows

1. Navegue até a pasta do frontend:
   ```
   cd caminho\para\inventory_app\frontend
   ```
2. Instale as dependências:
   ```
   npm install
   ```
3. Inicie o servidor de desenvolvimento:
   ```
   npm run dev
   ```
4. Acesse o dashboard em `http://localhost:5173`

#### Linux

1. Navegue até a pasta do frontend:
   ```
   cd caminho/para/inventory_app/frontend
   ```
2. Instale as dependências:
   ```
   npm install
   ```
3. Inicie o servidor de desenvolvimento:
   ```
   npm run dev
   ```
4. Acesse o dashboard em `http://localhost:5173`

## Testando o Sistema

### Fluxo de Teste Completo

1. Inicie o backend API
2. Inicie o frontend
3. Execute o agente de coleta
4. Verifique se o dispositivo aparece no dashboard

### Verificação da API

Após iniciar o backend, você pode acessar a documentação interativa da API em:
```
http://localhost:8000/docs
```

Esta interface permite testar todos os endpoints disponíveis.

### Testes do Agente

O agente pode ser executado com diferentes parâmetros:

```python
# Apenas coleta local, sem descoberta de rede
python agent.py --self-only

# Apenas descoberta de rede, sem coleta local
python agent.py --discover-only

# Coleta completa (padrão)
python agent.py
```

## Funcionalidades Implementadas

- ✅ Coleta de informações detalhadas de hardware (CPU, RAM, Disco, GPU, etc.)
- ✅ Registro de dispositivos na API
- ✅ Visualização básica dos dispositivos no dashboard
- ✅ Suporte para Windows e Linux

## Limitações Atuais

- A descoberta de rede requer o nmap instalado
- O banco de dados padrão é SQLite (para produção, recomenda-se PostgreSQL)
- O frontend possui apenas visualização básica, sem edição ou histórico
- A coleta de temperatura e fonte de alimentação é limitada

## Próximos Passos

- Implementar autenticação e controle de acesso
- Adicionar histórico de modificações
- Melhorar a interface do dashboard com visualização detalhada
- Implementar exportação de relatórios
- Migrar para PostgreSQL para ambiente de produção

## Solução de Problemas

### Agente não consegue se conectar à API

- Verifique se o backend está rodando
- Confirme se o endereço no arquivo `.env` está correto
- Verifique se há firewall bloqueando a conexão

### Erro ao instalar dependências no Windows

- Para problemas com `wmi` ou `pywin32`, tente:
  ```
  pip install pywin32
  pip install wmi
  ```

### Descoberta de rede não funciona

- Verifique se o nmap está instalado
- No Linux: `sudo apt-get install nmap`
- No Windows: Baixe e instale do site oficial

## Contato e Suporte

Para dúvidas ou problemas, entre em contato com a equipe de desenvolvimento.

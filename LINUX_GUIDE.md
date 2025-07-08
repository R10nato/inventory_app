# Guia de Instalação e Uso no Linux

Este guia detalhado explica como instalar, configurar e usar o Sistema de Inventário e Monitoramento de Hardware em ambiente Linux.

## Requisitos de Sistema

- Distribuição Linux baseada em Debian/Ubuntu (recomendado) ou outra distribuição moderna
- Python 3.8 ou superior
- Node.js 14 ou superior
- Privilégios de sudo para instalação de pacotes e coleta completa de dados

## 1. Instalação do Backend (API)

### Passo a Passo

1. **Extraia o arquivo ZIP** do projeto em uma pasta de sua preferência.

2. **Abra o Terminal**:
   ```
   Ctrl+Alt+T
   ```

3. **Navegue até a pasta do backend**:
   ```
   cd /caminho/para/inventory_app/backend
   ```

4. **Crie um ambiente virtual Python**:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Instale as dependências**:
   ```
   pip install fastapi uvicorn sqlalchemy python-dotenv
   ```

6. **Crie um arquivo `.env`** na pasta backend:
   ```
   echo "DATABASE_URL=sqlite:///./inventory.db" > .env
   echo "SECRET_KEY=sua_chave_secreta_aqui" >> .env
   ```

7. **Inicie o servidor API**:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

8. **Verifique se a API está funcionando**:
   - Abra um navegador e acesse: `http://localhost:8000/docs`
   - Você deverá ver a documentação interativa da API

## 2. Instalação do Agente de Coleta

### Passo a Passo

1. **Abra um novo Terminal**

2. **Navegue até a pasta do agente**:
   ```
   cd /caminho/para/inventory_app/agents
   ```

3. **Crie um ambiente virtual Python**:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Instale as dependências básicas**:
   ```
   pip install requests python-dotenv psutil
   ```

5. **Instale o nmap para descoberta de rede**:
   ```
   sudo apt-get update
   sudo apt-get install nmap
   pip install python-nmap
   ```
   
   *Nota: Para outras distribuições, use o gerenciador de pacotes apropriado:*
   - Fedora/RHEL: `sudo dnf install nmap`
   - Arch Linux: `sudo pacman -S nmap`

6. **Instale ferramentas adicionais para coleta detalhada** (opcional, mas recomendado):
   ```
   sudo apt-get install lshw dmidecode
   ```

7. **Crie um arquivo `.env`** na pasta do agente:
   ```
   echo "API_ENDPOINT=http://localhost:8000" > .env
   ```

8. **Execute o agente**:
   ```
   python agent.py
   ```
   
   *Nota: Para coleta completa de dados, execute com sudo:*
   ```
   sudo -E python agent.py
   ```
   O parâmetro `-E` preserva as variáveis de ambiente, incluindo o ambiente virtual Python.

9. **Verifique a saída do console** para confirmar que o agente coletou e enviou os dados com sucesso.

## 3. Instalação do Frontend (Dashboard)

### Passo a Passo

1. **Abra um novo Terminal**

2. **Navegue até a pasta do frontend**:
   ```
   cd /caminho/para/inventory_app/frontend
   ```

3. **Instale as dependências**:
   ```
   npm install
   ```
   
   *Nota: Se o Node.js não estiver instalado, instale-o primeiro:*
   ```
   curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

4. **Inicie o servidor de desenvolvimento**:
   ```
   npm run dev
   ```

5. **Acesse o dashboard**:
   - Abra um navegador e acesse: `http://localhost:5173`
   - Você deverá ver a interface do dashboard com os dispositivos registrados

## Testando o Sistema Completo

### Fluxo de Teste Recomendado

1. **Mantenha o backend rodando** em um terminal
2. **Mantenha o frontend rodando** em outro terminal
3. **Execute o agente** em um terceiro terminal (com sudo para coleta completa)
4. **Verifique o dashboard** para confirmar que seu dispositivo aparece na lista

### Verificação de Dados Coletados

1. No dashboard, você deve ver seu computador Linux listado
2. Os dados coletados incluem:
   - Informações de CPU (modelo, núcleos)
   - Memória RAM (total)
   - Discos (tipo, capacidade, espaço livre)
   - Interfaces de rede
   - Informações do sistema operacional

### Teste de Descoberta de Rede

Para testar a descoberta de outros dispositivos na rede:

1. Certifique-se de que o nmap está instalado
2. Execute o agente com o parâmetro de descoberta:
   ```
   sudo -E python agent.py --discover
   ```
3. Verifique o dashboard para ver os dispositivos descobertos

## Solução de Problemas Comuns no Linux

### O agente não consegue se conectar à API

- Verifique se o backend está rodando
- Confirme se o endereço no arquivo `.env` está correto
- Verifique se há firewall bloqueando a conexão:
  ```
  sudo ufw status
  ```
- Se necessário, adicione uma regra ao firewall:
  ```
  sudo ufw allow 8000
  ```

### Erros de permissão ao coletar dados

- Alguns dados de hardware só podem ser coletados com privilégios de root
- Use `sudo -E` para executar o agente com privilégios elevados preservando o ambiente

### Problemas com a descoberta de rede

- Verifique se o nmap está instalado corretamente:
  ```
  nmap --version
  ```
- Certifique-se de que está executando o agente com privilégios de root para scan de rede

### O frontend não consegue acessar a API

- Verifique se o arquivo `vite.config.js` está configurado corretamente com o proxy
- Confirme se a API está rodando e acessível em `http://localhost:8000`

## Configuração para Uso Regular

Para uso regular do sistema no Linux, você pode:

1. **Criar scripts shell** para iniciar cada componente
2. **Configurar o agente como serviço systemd** para execução automática
3. **Configurar o backend como serviço systemd**

### Exemplo de Script Shell para Iniciar o Backend

Crie um arquivo `start_backend.sh` com o seguinte conteúdo:

```bash
#!/bin/bash
cd /caminho/para/inventory_app/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Torne o script executável:
```
chmod +x start_backend.sh
```

### Exemplo de Script Shell para Iniciar o Frontend

Crie um arquivo `start_frontend.sh` com o seguinte conteúdo:

```bash
#!/bin/bash
cd /caminho/para/inventory_app/frontend
npm run dev
```

Torne o script executável:
```
chmod +x start_frontend.sh
```

### Exemplo de Serviço Systemd para o Agente

Crie um arquivo `/etc/systemd/system/inventory-agent.service`:

```
[Unit]
Description=Inventory Hardware Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/caminho/para/inventory_app/agents
ExecStart=/caminho/para/inventory_app/agents/venv/bin/python agent.py
Restart=on-failure
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=inventory-agent

[Install]
WantedBy=multi-user.target
```

Ative e inicie o serviço:
```
sudo systemctl daemon-reload
sudo systemctl enable inventory-agent
sudo systemctl start inventory-agent
```

Verifique o status:
```
sudo systemctl status inventory-agent
```

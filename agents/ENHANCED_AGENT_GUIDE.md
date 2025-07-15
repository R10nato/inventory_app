# Guia de Instalação e Uso do Agente Aprimorado

## Visão Geral

O agente de inventário foi completamente aprimorado para atender aos requisitos solicitados, incluindo:

- Coleta detalhada de hardware e software
- Armazenamento local com sincronização posterior
- Detecção de alterações entre inventários
- Suporte a execução em segundo plano
- Tratamento robusto de erros

## Requisitos

### Windows
- Python 3.6 ou superior
- Bibliotecas: `wmi`, `psutil`, `python-nmap`, `pywin32`, `python-dotenv`
- Nmap instalado (opcional, apenas para descoberta de rede)

### Linux
- Python 3.6 ou superior
- Bibliotecas: `psutil`, `python-nmap`, `python-dotenv`
- Nmap instalado (opcional, apenas para descoberta de rede)

## Instalação

1. **Instalar Python**:
   - Windows: Baixe e instale do [python.org](https://www.python.org/downloads/)
   - Linux: Geralmente já vem instalado, ou use `sudo apt install python3 python3-pip`

2. **Instalar dependências**:
   ```
   pip install wmi psutil python-nmap pywin32 python-dotenv
   ```

3. **Instalar Nmap** (opcional, para descoberta de rede):
   - Windows: Baixe e instale do [nmap.org](https://nmap.org/download.html)
   - Linux: `sudo apt install nmap`

4. **Configurar o arquivo .env**:
   Crie um arquivo `.env` no mesmo diretório do agente com:
   ```
   API_ENDPOINT=http://seu-servidor:8000
   API_TOKEN=seu_token_de_api
   ```

## Modos de Uso

### Uso Básico
```
python agent_enhanced.py
```
Executa coleta local e descoberta de rede.

### Apenas Coleta Local
```
python agent_enhanced.py --self-only
```
Coleta apenas informações da máquina local.

### Apenas Descoberta de Rede
```
python agent_enhanced.py --discover-only
```
Apenas descobre dispositivos na rede.

### Modo Offline
```
python agent_enhanced.py --offline
```
Armazena dados localmente para sincronização posterior.

### Sincronização
```
python agent_enhanced.py --sync
```
Sincroniza dados armazenados localmente com o servidor.

### Rede Específica
```
python agent_enhanced.py --network 192.168.1.0/24
```
Especifica a rede para descoberta.

## Configuração como Serviço Windows

Para executar o agente como um serviço Windows:

1. **Instalar NSSM** (Non-Sucking Service Manager):
   - Baixe do [nssm.cc](https://nssm.cc/download)
   - Extraia para uma pasta (ex: `C:\nssm`)

2. **Criar o serviço**:
   - Abra o Prompt de Comando como Administrador
   - Navegue até a pasta do NSSM: `cd C:\nssm\win64`
   - Execute:
     ```
     nssm install InventoryAgent
     ```
   - Na janela que abrir:
     - **Path**: Caminho para o Python (ex: `C:\Python39\python.exe`)
     - **Startup directory**: Diretório do agente
     - **Arguments**: `agent_enhanced.py --self-only`
     - **Service name**: InventoryAgent

3. **Configurar agendamento**:
   - Na aba "Details", defina:
     - **Startup type**: Automatic
   - Na aba "I/O":
     - **Output (stdout)**: Caminho para arquivo de log (ex: `C:\logs\inventory_agent_out.log`)
     - **Error (stderr)**: Caminho para arquivo de erro (ex: `C:\logs\inventory_agent_err.log`)

4. **Iniciar o serviço**:
   ```
   nssm start InventoryAgent
   ```

## Agendamento com Task Scheduler (Alternativa)

1. Abra o Task Scheduler (Agendador de Tarefas)
2. Crie uma nova tarefa:
   - **Nome**: Inventory Agent
   - **Executar com privilégios mais altos**: Sim
   - **Trigger**: Diário ou Na inicialização
   - **Ação**: Iniciar um programa
     - **Programa/script**: Caminho para o Python
     - **Argumentos**: `caminho\para\agent_enhanced.py --self-only`
     - **Iniciar em**: Diretório do agente

## Informações Coletadas

O agente coleta as seguintes informações:

### Hardware
- **CPU**: Modelo, núcleos físicos/lógicos, frequência
- **RAM**: Total, em uso, slots, módulos
- **Discos**: Tipo (HDD/SSD), capacidade, espaço livre
- **GPU**: Modelo, memória
- **Placa-mãe**: Fabricante, modelo, número de série
- **Rede**: Interfaces, endereços IP/MAC
- **Dispositivos USB**: Dispositivos conectados

### Software
- **Sistema Operacional**: Nome, versão, build
- **Programas Instalados**: Nome, versão, fabricante, data de instalação

## Solução de Problemas

### Erros de Permissão
- Execute como Administrador (Windows) ou root (Linux)
- Verifique permissões de escrita no diretório do agente

### Falhas na Descoberta de Rede
- Verifique se o Nmap está instalado e no PATH
- Verifique configurações de firewall
- Use a opção `--network` para especificar a rede manualmente

### Falhas na Conexão com o Servidor
- Verifique se o servidor está acessível
- Confirme se o API_ENDPOINT no arquivo .env está correto
- Use o modo `--offline` e depois `--sync` quando o servidor estiver disponível

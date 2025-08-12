# Documentação do Agente de Inventário Aprimorado

Este documento detalha as melhorias e novas funcionalidades implementadas no agente de inventário, bem como instruções para sua instalação, execução e solução de problemas.

## 1. Visão Geral das Melhorias

O agente de inventário foi aprimorado para coletar informações de hardware mais detalhadas, incluindo:

- **Temperaturas:** Coleta de temperatura da CPU e, quando possível, de discos.
- **Informações de RAM:** Frequência, tipo e número de slots (requer privilégios de root no Linux).
- **Detalhes da Placa-Mãe:** Fabricante e modelo (requer privilégios de root no Linux).
- **Informações de GPU:** Nome, RAM do adaptador, versão do driver, processador de vídeo, resolução e taxa de atualização do monitor.
- **Dispositivos de Áudio:** Lista de dispositivos de áudio conectados.
- **Dispositivos USB:** Lista de dispositivos USB conectados.
- **Software Instalado:** Lista de softwares instalados com nome, versão, editor e data de instalação (no Windows).

Além disso, o agente agora mapeia os dados coletados para um esquema de backend mais robusto, garantindo compatibilidade e facilidade de integração.

## 2. Instalação e Configuração

### 2.1. Pré-requisitos

Para executar o agente, você precisará:

- Python 3.x instalado.
- `pip` (gerenciador de pacotes Python).
- No Linux, as seguintes ferramentas de linha de comando (instale via `apt` ou `yum`):
    - `psutil` (instalado via pip)
    - `dmidecode` (para informações detalhadas de RAM e placa-mãe)
    - `lspci` (para informações de GPU e áudio)
    - `xrandr` (para resolução de monitor)
    - `aplay` (para dispositivos de áudio alternativos)
    - `lsusb` (para dispositivos USB)
    - `smartmontools` (para temperatura de disco)
    - `nmap` (para descoberta de rede)

### 2.2. Instalação das Dependências Python

Navegue até o diretório `inventory_app/agents/` e instale as dependências:

```bash
pip install psutil wmi python-dotenv requests
```

### 2.3. Instalação de Ferramentas no Linux (se aplicável)

```bash
sudo apt-get update
sudo apt-get install -y pciutils x11-xserver-utils alsa-utils usbutils dmidecode smartmontools nmap
```

### 2.4. Configuração do Endpoint da API

O agente envia os dados coletados para um endpoint de API. Você pode configurar este endpoint através de uma variável de ambiente ou diretamente no código.

Crie um arquivo `.env` no mesmo diretório do agente (`inventory_app/agents/`) com o seguinte conteúdo:

```
API_ENDPOINT=http://seu_endereco_do_backend:8000
API_TOKEN=seu_token_de_autenticacao_opcional
```

Substitua `http://seu_endereco_do_backend:8000` pelo endereço real do seu servidor backend. Se você expôs a porta 8000 do sandbox, o endereço será algo como `https://8000-xxxxxxxxxxxxxxxxxxxxxxxx.manusvm.computer`.

## 3. Execução do Agente

O agente pode ser executado de várias maneiras:

### 3.1. Coleta de Dados da Máquina Local (Recomendado)

Para coletar informações detalhadas da máquina local e enviá-las ao backend, execute o agente com privilégios de root (necessário para algumas informações de hardware no Linux):

```bash
sudo python3 agent_final.py --self-only
```

### 3.2. Coleta de Dados e Descoberta de Rede

Para coletar dados da máquina local e realizar a descoberta de dispositivos na rede:

```bash
sudo python3 agent_final.py
```

Você pode especificar a faixa de rede para a descoberta:

```bash
sudo python3 agent_final.py --network 192.168.1.0/24
```

### 3.3. Apenas Descoberta de Rede

```bash
sudo python3 agent_final.py --discover-only
```

### 3.4. Modo Offline

Para coletar dados e armazená-los localmente sem tentar enviar ao servidor (útil para ambientes sem conectividade):

```bash
sudo python3 agent_final.py --self-only --offline
```

### 3.5. Sincronizar Dados Locais com o Servidor

Para enviar dados coletados anteriormente no modo offline para o servidor:

```bash
sudo python3 agent_final.py --sync
```

## 4. Estrutura do Código

- `agent_final.py`: Contém a lógica principal de coleta de dados, mapeamento e envio.
- `map_to_backend_schema()`: Função responsável por transformar os dados brutos coletados no formato esperado pelo backend.
- `get_linux_details()`: Coleta informações de hardware em sistemas Linux.
- `get_windows_details()`: Coleta informações de hardware em sistemas Windows.

## 5. Solução de Problemas

- **`NameError: name 'map_to_backend_schema' is not defined`**: Certifique-se de que a função `map_to_backend_schema` esteja definida antes de ser chamada na função `main`.
- **Comandos não encontrados (`lspci`, `xrandr`, `dmidecode`, etc.)**: Verifique se as ferramentas listadas na seção de pré-requisitos estão instaladas no seu sistema operacional.
- **Permissão negada**: Certifique-se de executar o agente com `sudo` para permitir a coleta de informações de hardware que exigem privilégios de root.
- **Erro ao enviar dados para o servidor**: Verifique se o servidor backend está em execução e acessível no `API_ENDPOINT` configurado. Verifique também os logs do backend para mensagens de erro.
- **`HTTPConnectionPool(...) Connection refused` ou `502 Bad Gateway`**: O backend pode não estar rodando ou o endereço do `API_ENDPOINT` está incorreto. Verifique se o processo do Uvicorn está ativo e se o URL exposto está correto.

## 6. Próximos Passos

- **Desenvolvimento do Backend**: Implementar a lógica de persistência de dados no backend (banco de dados) para armazenar as informações enviadas pelo agente.
- **Desenvolvimento do Frontend**: Criar uma interface de usuário para visualizar os dados de inventário coletados, incluindo o dashboard e as funcionalidades de pesquisa/edição.

---

**Observação**: Este agente foi testado em um ambiente de sandbox Linux. A coleta de dados no Windows depende da disponibilidade do módulo `wmi` e pode ter requisitos adicionais de permissão ou software. A coleta de temperatura no Windows geralmente requer software de terceiros e não é nativamente suportada por este agente.


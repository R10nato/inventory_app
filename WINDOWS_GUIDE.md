# Guia de Instalação e Uso no Windows

Este guia detalhado explica como instalar, configurar e usar o Sistema de Inventário e Monitoramento de Hardware em ambiente Windows.

## Requisitos de Sistema

- Windows 10 ou superior
- Python 3.8 ou superior
- Node.js 14 ou superior
- Privilégios de administrador (para coleta completa de dados de hardware)

## 1. Instalação do Backend (API)

### Passo a Passo

1. **Extraia o arquivo ZIP** do projeto em uma pasta de sua preferência.

2. **Abra o Prompt de Comando como administrador**:
   - Clique com o botão direito no menu Iniciar
   - Selecione "Prompt de Comando (Admin)" ou "Windows PowerShell (Admin)"

3. **Navegue até a pasta do backend**:
   ```
   cd C:\caminho\para\inventory_app\backend
   ```

4. **Crie um ambiente virtual Python**:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
   
   *Nota: Se o comando acima falhar, talvez seja necessário ajustar a política de execução do PowerShell:*
   ```
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   ```

5. **Instale as dependências**:
   ```
   pip install fastapi uvicorn sqlalchemy python-dotenv
   ```

6. **Crie um arquivo `.env`** na pasta backend com o seguinte conteúdo:
   ```
   DATABASE_URL=sqlite:///./inventory.db
   SECRET_KEY=sua_chave_secreta_aqui
   ```

7. **Inicie o servidor API**:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ou 
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

   ```

8. **Verifique se a API está funcionando**:
   - Abra um navegador e acesse: `http://localhost:8000/docs`
   - Você deverá ver a documentação interativa da API

## 2. Instalação do Agente de Coleta

### Passo a Passo

1. **Abra um novo Prompt de Comando como administrador** (importante para coleta completa de dados)

2. **Navegue até a pasta do agente**:
   ```
   cd C:\caminho\para\inventory_app\agents
   ```

3. **Crie um ambiente virtual Python** (opcional, mas recomendado):
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Instale as dependências específicas para Windows**:
   ```
   pip install requests python-dotenv psutil wmi pywin32
   ```

   *Nota: Se houver problemas com a instalação do `wmi` ou `pywin32`, tente instalá-los separadamente:*
   ```
   pip install pywin32
   pip install wmi
   ```

5. **Crie um arquivo `.env`** na pasta do agente com o seguinte conteúdo:
   ```
   API_ENDPOINT=http://localhost:8000
   ```

6. **Execute o agente**:
   ```
   python agent.py
   ```

7. **Verifique a saída do console** para confirmar que o agente coletou e enviou os dados com sucesso.

## 3. Instalação do Frontend (Dashboard)

### Passo a Passo

1. **Abra um novo Prompt de Comando** (não precisa ser como administrador)

2. **Navegue até a pasta do frontend**:
   ```
   cd C:\caminho\para\inventory_app\frontend
   ```

3. **Instale as dependências**:
   ```
   npm install
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

1. **Mantenha o backend rodando** em um prompt de comando
2. **Mantenha o frontend rodando** em outro prompt de comando
3. **Execute o agente** em um terceiro prompt de comando (como administrador)
4. **Verifique o dashboard** para confirmar que seu dispositivo aparece na lista

### Verificação de Dados Coletados

1. No dashboard, você deve ver seu computador Windows listado
2. Os dados coletados incluem:
   - Informações de CPU (fabricante, modelo, núcleos)
   - Memória RAM (total, slots)
   - Discos (tipo, capacidade, espaço livre)
   - Placa de vídeo (se disponível)
   - Placa-mãe
   - Interfaces de rede

## Solução de Problemas Comuns no Windows

### O agente não consegue se conectar à API

- Verifique se o backend está rodando
- Confirme se o endereço no arquivo `.env` está correto
- Verifique se o Windows Defender ou outro firewall está bloqueando a conexão
- Tente adicionar uma regra de exceção no firewall para a porta 8000

### Erros de permissão ao coletar dados

- Certifique-se de executar o agente como administrador
- Alguns dados de hardware só podem ser coletados com privilégios elevados

### Problemas com a instalação de dependências

- Para o `pywin32`, você pode baixar o instalador diretamente do GitHub se a instalação via pip falhar
- Para o `wmi`, certifique-se de ter o Visual C++ Build Tools instalado

### O frontend não consegue acessar a API

- Verifique se o arquivo `vite.config.js` está configurado corretamente com o proxy
- Confirme se a API está rodando e acessível em `http://localhost:8000`

## Configuração para Uso Regular

Para uso regular do sistema no Windows, você pode:

1. **Criar scripts batch (.bat)** para iniciar cada componente
2. **Configurar o agente como serviço Windows** para execução automática
3. **Configurar o backend como serviço Windows** usando ferramentas como NSSM

### Exemplo de Script Batch para Iniciar o Backend

Crie um arquivo `start_backend.bat` com o seguinte conteúdo:

```batch
@echo off
cd C:\caminho\para\inventory_app\backend
call venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Exemplo de Script Batch para Iniciar o Frontend

Crie um arquivo `start_frontend.bat` com o seguinte conteúdo:

```batch
@echo off
cd C:\caminho\para\inventory_app\frontend
npm run dev
```

### Exemplo de Script Batch para Executar o Agente

Crie um arquivo `run_agent.bat` com o seguinte conteúdo:

```batch
@echo off
cd C:\caminho\para\inventory_app\agents
call venv\Scripts\activate
python agent.py
```

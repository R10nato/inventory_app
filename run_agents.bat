@echo off
:start
echo ========================================
echo  Iniciando Agents - Coleta de Inventario
echo ========================================
echo.

cd /d "C:\Projetos\AppInventario\home\ubuntu\inventory_app\agents"

echo Verificando se o ambiente virtual existe...
if not exist "venv\" (
    echo Criando ambiente virtual...
    python -m venv venv
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Instalando/atualizando dependencias...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo Instalando dependencias basicas...
    pip install wmi requests python-dotenv
)

echo.
echo Executando coleta de sensores...
echo Para executar continuamente, pressione Ctrl+C para parar
echo.

python agent.py

echo.
echo ========================================
echo  Agent parou de executar
echo ========================================
echo.
echo [R] - Reiniciar Agent
echo [Q] - Sair
echo.
set /p choice="Escolha uma opcao: "

if /i "%choice%"=="R" goto start
if /i "%choice%"=="Q" exit /b

goto start

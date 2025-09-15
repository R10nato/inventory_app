@echo off
:start
echo ========================================
echo  Iniciando Backend - Inventory API
echo ========================================
echo.

cd /d "C:\Projetos\AppInventario\home\ubuntu\inventory_app\backend"

echo Verificando se o ambiente virtual existe...
if not exist "venv\" (
    echo Criando ambiente virtual...
    python -m venv venv
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Instalando/atualizando dependencias...
pip install -r requirements.txt

echo.
echo Iniciando servidor FastAPI...
echo Backend rodara em: http://localhost:8000
echo Para parar o servidor, pressione Ctrl+C
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo ========================================
echo  Backend parou de executar
echo ========================================
echo.
echo [R] - Reiniciar Backend
echo [Q] - Sair
echo.
set /p choice="Escolha uma opcao: "

if /i "%choice%"=="R" goto start
if /i "%choice%"=="Q" exit /b

goto start

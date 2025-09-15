@echo off
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

pause

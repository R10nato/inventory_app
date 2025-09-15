@echo off
:start
echo ========================================
echo  Iniciando Frontend - Inventory Dashboard
echo ========================================
echo.

cd C:\Projetos\AppInventario\home\ubuntu\inventory_app\inventory-dashboard

echo Ativando ambiente virtual...
call venv\Scripts\activate

echo.
echo Iniciando servidor de desenvolvimento...
echo Frontend rodara em: http://localhost:5173
echo Para parar o servidor, pressione Ctrl+C
echo.

npm run dev

echo.
echo ========================================
echo  Frontend parou de executar
echo ========================================
echo.
echo [R] - Reiniciar Frontend
echo [Q] - Sair
echo.
set /p choice="Escolha uma opcao: "

if /i "%choice%"=="R" goto start
if /i "%choice%"=="Q" exit /b

goto start

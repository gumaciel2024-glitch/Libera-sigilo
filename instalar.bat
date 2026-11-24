@echo off
setlocal
cd /d "%~dp0"
set "SAJ_INSTALL_STAGE=verificar Python"
echo Instalacao do Liberador SAJ > instalacao.log
py -3 -c "import sys; print(sys.version); print(sys.executable); sys.exit(0 if sys.version_info >= (3, 11) else 1)" >> instalacao.log 2>&1
if errorlevel 1 goto python_erro
py -3 -c "import os; print('Pasta:', os.getcwd()); print('Comprimento do caminho:', len(os.getcwd()))" >> instalacao.log 2>&1
echo Preparando o ambiente Python...
set "SAJ_INSTALL_STAGE=criar ambiente virtual"
py -3 -m venv --without-pip .venv >> instalacao.log 2>&1
if errorlevel 1 goto erro
echo Preparando o pip...
set "SAJ_INSTALL_STAGE=preparar pip com ensurepip"
".venv\Scripts\python.exe" -m ensurepip --upgrade --default-pip >> instalacao.log 2>&1
if errorlevel 1 goto erro
echo Instalando dependencias. Aguarde...
set "SAJ_INSTALL_STAGE=instalar dependencias"
".venv\Scripts\python.exe" -m pip install -r requirements.txt >> instalacao.log 2>&1
if errorlevel 1 goto erro
set "SAJ_INSTALL_STAGE=conferir dependencias"
".venv\Scripts\python.exe" -c "import pyautogui, cv2, numpy, PIL, openpyxl, tkinter; print('Dependencias conferidas.')" >> instalacao.log 2>&1
if errorlevel 1 goto erro
echo.
echo Instalacao concluida. Abra iniciar.bat.
pause
exit /b 0
:python_erro
type instalacao.log
echo.
echo O Python Launcher nao encontrou um Python 3.11 ou superior funcional.
echo Confira a instalacao do Python e do Python Launcher.
pause
exit /b 1
:erro
echo.
type instalacao.log
echo.
echo Falha na etapa: %SAJ_INSTALL_STAGE%.
echo O diagnostico completo foi salvo em instalacao.log nesta pasta.
echo Se a pasta estiver em um caminho longo, extraia uma copia NOVA do ZIP
echo em uma pasta curta, por exemplo C:\SAJ_Sigilo, e tente novamente.
echo Nao copie a pasta .venv de outra instalacao.
echo Se persistir, envie as ultimas linhas de instalacao.log.
pause
exit /b 1

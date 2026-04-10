@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title CaçaVagas — Instalador

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║              CaçaVagas — Instalador                 ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: ── 1. Verificar Python ──────────────────────────────────────────────────────
echo  [1/4] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Python nao encontrado no seu computador.
    echo.
    echo  Abrindo a pagina de download do Python...
    echo  Instale o Python 3.11 e marque a opcao "Add Python to PATH".
    echo  Depois execute este instalador novamente.
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  Python %PY_VER% encontrado. OK

:: ── 2. Instalar dependencias ─────────────────────────────────────────────────
echo.
echo  [2/4] Instalando dependencias (pode demorar alguns minutos)...
echo.
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Falha ao instalar dependencias.
    echo  Verifique sua conexao com a internet e tente novamente.
    pause
    exit /b 1
)
echo.
echo  Dependencias instaladas. OK

:: ── 3. Instalar navegador (para Vagas.com) ───────────────────────────────────
echo.
echo  [3/4] Instalando navegador integrado...
python -m playwright install chromium >nul 2>&1
echo  Navegador instalado. OK

:: ── 4. Configurar dados do usuario ───────────────────────────────────────────
echo.
echo  [4/4] Configurando seus dados...
echo.

if exist ".env" (
    echo  Configuracao ja existe. Deseja atualizar seus dados? (S/N)
    set /p RECONF="  > "
    if /i "!RECONF!" neq "S" goto criar_atalho
)

echo  Informe seus dados abaixo.
echo  Pressione ENTER para pular campos opcionais.
echo.

set /p EMAIL="  Seu e-mail (Gmail): "
set /p CIDADE="  Sua cidade (ex: Rio de Janeiro): "
set /p ESTADO="  Sigla do estado (ex: RJ): "

echo # Automacao de Vagas — configuracoes > .env
echo. >> .env
if not "!EMAIL!"=="" (
    echo EMAIL_REMETENTE=!EMAIL! >> .env
    echo EMAIL_DESTINO=!EMAIL! >> .env
) else (
    echo EMAIL_REMETENTE= >> .env
    echo EMAIL_DESTINO= >> .env
)
echo. >> .env
echo GMAIL_APP_PASSWORD= >> .env
echo. >> .env
if not "!CIDADE!"=="" (
    echo CIDADE=!CIDADE! >> .env
) else (
    echo CIDADE=Sao Paulo >> .env
)
if not "!ESTADO!"=="" (
    echo ESTADO=!ESTADO! >> .env
) else (
    echo ESTADO=SP >> .env
)
echo. >> .env
echo GEMINI_API_KEY= >> .env

echo.
echo  Dados salvos. OK

:criar_atalho
:: ── Criar atalho na area de trabalho ─────────────────────────────────────────
set "DIR_APP=%~dp0"
set "ATALHO=%USERPROFILE%\Desktop\CaçaVagas.bat"
(
    echo @echo off
    echo cd /d "%DIR_APP%"
    echo start "" pythonw app.py
) > "%ATALHO%"

:: ── Conclusao ────────────────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   Pronto! Instalacao concluida.                     ║
echo  ║                                                      ║
echo  ║   Para abrir o app, use o atalho criado             ║
echo  ║   na sua area de trabalho:                           ║
echo  ║                                                      ║
echo  ║      Automacao de Vagas                              ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Pressione qualquer tecla para fechar...
pause >nul

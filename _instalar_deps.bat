@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

:: ── Localizar Python (recém instalado ou já existente) ────────────────────────
:: O instalador do Python atualiza o registro mas não o PATH do processo atual,
:: por isso buscamos nas pastas padrão explicitamente.

set PYTHON=
set PYTHONW=

:: 1. Pasta padrão de instalação por usuário (AppData)
for /d %%d in (
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
) do (
    if "!PYTHON!"=="" (
        if exist "%%~d\python.exe" (
            set "PYTHON=%%~d\python.exe"
            set "PYTHONW=%%~d\pythonw.exe"
        )
    )
)

:: 2. Pasta padrão de instalação para todos os usuários
if "!PYTHON!"=="" (
    for /d %%d in (
        "C:\Program Files\Python313"
        "C:\Program Files\Python312"
        "C:\Program Files\Python311"
        "C:\Program Files\Python310"
        "C:\Python311"
        "C:\Python310"
    ) do (
        if "!PYTHON!"=="" (
            if exist "%%~d\python.exe" (
                set "PYTHON=%%~d\python.exe"
                set "PYTHONW=%%~d\pythonw.exe"
            )
        )
    )
)

:: 3. Tentar pelo PATH (Python já estava instalado antes)
if "!PYTHON!"=="" (
    for /f "tokens=*" %%p in ('where python 2^>nul') do (
        if "!PYTHON!"=="" set "PYTHON=%%p"
    )
    for /f "tokens=*" %%p in ('where pythonw 2^>nul') do (
        if "!PYTHONW!"=="" set "PYTHONW=%%p"
    )
)

if "!PYTHON!"=="" (
    echo [ERRO] Python nao encontrado apos instalacao.
    exit /b 1
)

echo Python encontrado: !PYTHON!

:: ── Instalar dependências ─────────────────────────────────────────────────────
"!PYTHON!" -m pip install --upgrade pip --quiet --no-warn-script-location
"!PYTHON!" -m pip install -r requirements.txt --quiet --no-warn-script-location

if !errorlevel! neq 0 (
    echo [ERRO] Falha ao instalar dependencias pip.
    exit /b 1
)

:: ── Instalar Playwright chromium ──────────────────────────────────────────────
"!PYTHON!" -m playwright install chromium

:: ── Gravar caminho do pythonw em iniciar.bat ──────────────────────────────────
if not "!PYTHONW!"=="" (
    if exist "!PYTHONW!" (
        > iniciar.bat (
            echo @echo off
            echo cd /d "%%~dp0"
            echo start "" "!PYTHONW!" "%%~dp0app.py"
        )
    )
)

echo Instalacao concluida.
exit /b 0

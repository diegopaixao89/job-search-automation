@echo off
REM agendar_windows.bat
REM Cria uma tarefa no Agendador de Tarefas do Windows para rodar o digest diariamente.
REM Execute este arquivo como Administrador.
REM
REM Para alterar o horário, edite a variável HORARIO abaixo.

setlocal

set "HORARIO=08:00"
set "TASK_NAME=CacaVagas-Digest"
set "SCRIPT=%~dp0buscar_e_enviar.py"

REM Verifica se Python está no PATH
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH.
    echo Instale Python 3 e adicione-o ao PATH do sistema.
    pause
    exit /b 1
)

for /f "delims=" %%i in ('where python') do (
    set "PYTHON_EXE=%%i"
    goto :found
)
:found

echo.
echo Configuracao:
echo   Script  : %SCRIPT%
echo   Python  : %PYTHON_EXE%
echo   Horario : diariamente as %HORARIO%
echo   Tarefa  : %TASK_NAME%
echo.

schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_EXE%\" \"%SCRIPT%\"" ^
    /sc daily ^
    /st %HORARIO% ^
    /f ^
    /rl HIGHEST

if %errorlevel% equ 0 (
    echo.
    echo [OK] Tarefa "%TASK_NAME%" criada com sucesso!
    echo      Vai rodar todo dia as %HORARIO%.
    echo.
    echo Para executar agora:
    echo   python "%SCRIPT%"
    echo.
    echo Para ver no Agendador de Tarefas:
    echo   taskschd.msc
) else (
    echo.
    echo [ERRO] Falha ao criar tarefa.
    echo Tente executar este arquivo como Administrador ^(botao direito ^> Executar como administrador^).
)

pause

@echo off
cd /d "%~dp0"

:: Tentar pythonw no PATH
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0app.py"
    exit /b
)

:: Procurar nas pastas padrão de instalação
for %%d in (
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
    "C:\Program Files\Python311"
    "C:\Program Files\Python312"
    "C:\Python311"
) do (
    if exist "%%~d\pythonw.exe" (
        start "" "%%~d\pythonw.exe" "%~dp0app.py"
        exit /b
    )
)

:: Fallback com janela de console (para debug)
python "%~dp0app.py"

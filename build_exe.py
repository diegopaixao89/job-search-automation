"""
build_exe.py — gera AutomacaoVagas.exe via PyInstaller
Execute: python build_exe.py
O exe ficará em dist/AutomacaoVagas/AutomacaoVagas.exe
"""
import subprocess, sys, os, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--windowed",                      # sem janela de console
    "--name", "AutomacaoVagas",
    "--icon", "NONE",
    # pacotes que o PyInstaller não detecta automaticamente
    "--hidden-import", "customtkinter",
    "--hidden-import", "PIL._tkinter_finder",
    "--hidden-import", "langdetect",
    "--hidden-import", "deep_translator",
    "--hidden-import", "playwright",
    "--hidden-import", "bs4",
    "--hidden-import", "requests",
    # inclui a pasta vagas/ como pacote
    "--add-data", f"{ROOT}/vagas{os.pathsep}vagas",
    # inclui recursos do customtkinter (temas, imagens)
    "--collect-data", "customtkinter",
    "--collect-data", "PIL",
    # entry point
    "app.py",
]

print("Gerando exe... isso pode levar 2-5 minutos.")
result = subprocess.run(cmd, cwd=ROOT)

if result.returncode == 0:
    dist = os.path.join(ROOT, "dist", "AutomacaoVagas")
    # copia o .env para junto do exe (necessario para a senha do gmail)
    env_src = os.path.join(ROOT, ".env")
    if os.path.exists(env_src):
        shutil.copy(env_src, dist)
        print(f".env copiado para {dist}")
    print(f"\nEXE gerado em: {dist}\\AutomacaoVagas.exe")
    print("IMPORTANTE: o .env com a senha do Gmail precisa estar na mesma pasta do exe.")
else:
    print("Build falhou. Veja os erros acima.")

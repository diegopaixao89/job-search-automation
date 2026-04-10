; setup.iss — CaçaVagas
; ============================================================
; COMO GERAR O INSTALADOR (só o desenvolvedor faz isso):
;
;   1. Instale o Inno Setup: jrsoftware.org/isdl.php
;   2. Baixe o Python 3.11:
;      https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
;      e coloque na mesma pasta deste arquivo
;   3. Abra este arquivo no Inno Setup e clique em "Compile" (Ctrl+F9)
;   4. O instalador será gerado em:  Output\CacaVagas_Setup.exe
;
; PARA DISTRIBUIR: compartilhe apenas  CacaVagas_Setup.exe
; ============================================================

#define AppName "CaçaVagas"
#define AppVersion "1.0"
#define AppPublisher "Diego Paixão"

[Setup]
AppId={{7C4E8B2A-D3F1-4A9E-B6C5-892D4F3A1E78}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\CacaVagas
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=CacaVagas_Setup
SetupIconFile=icone.ico
UninstallDisplayIcon={app}\icone.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=110
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayName={#AppName}

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[CustomMessages]
ptbr.InstallingPython=Instalando Python 3.11 — aguarde...
ptbr.InstallingDeps=Instalando componentes do app (pode levar alguns minutos)...

[Files]
; Aplicativo
Source: "app.py";             DestDir: "{app}"; Flags: ignoreversion
Source: "config.py";          DestDir: "{app}"; Flags: ignoreversion
Source: "banco.py";           DestDir: "{app}"; Flags: ignoreversion
Source: "matcher.py";         DestDir: "{app}"; Flags: ignoreversion
Source: "curriculo_parser.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "detector_idioma.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "geolocalizador.py";  DestDir: "{app}"; Flags: ignoreversion
Source: "notificador.py";     DestDir: "{app}"; Flags: ignoreversion
Source: "aplicador.py";       DestDir: "{app}"; Flags: ignoreversion
Source: "tradutor.py";        DestDir: "{app}"; Flags: ignoreversion
Source: "main.py";            DestDir: "{app}"; Flags: ignoreversion
Source: "rodar_automatico.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt";   DestDir: "{app}"; Flags: ignoreversion
Source: ".env.exemplo";       DestDir: "{app}"; Flags: ignoreversion
Source: "iniciar.bat";        DestDir: "{app}"; Flags: ignoreversion
Source: "_instalar_deps.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "icone.ico";          DestDir: "{app}"; Flags: ignoreversion
Source: "vagas\__init__.py";  DestDir: "{app}\vagas"; Flags: ignoreversion
Source: "vagas\base.py";      DestDir: "{app}\vagas"; Flags: ignoreversion
Source: "vagas\gupy.py";      DestDir: "{app}\vagas"; Flags: ignoreversion
Source: "vagas\himalayas.py"; DestDir: "{app}\vagas"; Flags: ignoreversion
Source: "vagas\indeed.py";    DestDir: "{app}\vagas"; Flags: ignoreversion
Source: "vagas\infojobs.py";  DestDir: "{app}\vagas"; Flags: ignoreversion
Source: "vagas\linkedin.py";  DestDir: "{app}\vagas"; Flags: ignoreversion
Source: "vagas\programathor.py"; DestDir: "{app}\vagas"; Flags: ignoreversion
Source: "vagas\remotive.py";  DestDir: "{app}\vagas"; Flags: ignoreversion
Source: "vagas\vagas_com.py"; DestDir: "{app}\vagas"; Flags: ignoreversion
Source: "vagas\weworkremotely.py"; DestDir: "{app}\vagas"; Flags: ignoreversion

; Python 3.11 embutido no instalador (baixe e coloque aqui antes de compilar)
Source: "python-3.11.9-amd64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autodesktop}\CaçaVagas"; Filename: "{app}\iniciar.bat"; WorkingDir: "{app}"; IconFilename: "{app}\icone.ico"; Comment: "Abrir CaçaVagas"
Name: "{group}\CaçaVagas";       Filename: "{app}\iniciar.bat"; WorkingDir: "{app}"; IconFilename: "{app}\icone.ico"
Name: "{group}\Desinstalar";              Filename: "{uninstallexe}"

[Run]
; Instala Python 3.11 somente se nenhuma versão >=3.10 estiver presente
Filename: "{tmp}\python-3.11.9-amd64.exe"; \
  Parameters: "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=0"; \
  StatusMsg: "{cm:InstallingPython}"; \
  Flags: waituntilterminated; \
  Check: not IsPythonInstalled

; Instala pip packages + Playwright chromium
Filename: "cmd.exe"; \
  Parameters: "/c ""{app}\_instalar_deps.bat"" > ""{app}\_install.log"" 2>&1"; \
  StatusMsg: "{cm:InstallingDeps}"; \
  Flags: runhidden waituntilterminated

[Code]
{ Verifica se Python 3.10 ou superior já está instalado }
function IsPythonInstalled(): Boolean;
var
  Path: string;
begin
  Result :=
    RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.13\InstallPath', '', Path) or
    RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.13\InstallPath', '', Path) or
    RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', Path) or
    RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', Path) or
    RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', Path) or
    RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', Path) or
    RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', Path) or
    RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', Path);
end;

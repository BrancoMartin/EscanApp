; ============================================================================
;  EscanApp - Instalador de Windows (Inno Setup 6)
;
;  Genera release\EscanAppSetup-<version>.exe
;
;  No compilar este archivo a mano: lo compila scripts\build_release.bat, que
;  ademas construye el frontend y el ejecutable y le pasa la version.
;  Compilacion manual (si hiciera falta):
;      iscc /DAppVersion=1.0.0 installer\EscanApp.iss
; ============================================================================

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

#define AppName        "EscanApp"
#define AppPublisher   "EscanApp"
#define AppExeName     "EscanApp.exe"
#define SourceRoot     ".."

[Setup]
; El AppId identifica al producto y NUNCA cambia entre versiones: es lo que hace
; que instalar la 1.1.0 sobre la 1.0.0 sea una ACTUALIZACION in-place y no una
; segunda copia con su propia entrada en "Agregar o quitar programas".
AppId={{8F3C6B41-2D74-4E9A-9C1F-5A7E0B3D6C82}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
VersionInfoVersion={#AppVersion}

DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=no

; Escribir en Program Files necesita elevacion.
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

LicenseFile=LICENSE.txt
SetupIconFile={#SourceRoot}\icono1.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}

OutputDir={#SourceRoot}\release
OutputBaseFilename=EscanAppSetup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"

[Files]
; Salida de PyInstaller (onedir): el .exe y su carpeta _internal con el frontend,
; los Modelfiles y la base de datos inicial.
Source: "{#SourceRoot}\dist\{#AppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Script que deja el entorno de IA listo (Ollama + los 9 modelos).
Source: "postinstall.ps1"; DestDir: "{app}\setup"; Flags: ignoreversion

; Instalador de Ollama vendorizado: OPCIONAL. Si dejas el archivo en
; installer\vendor\OllamaSetup.exe, el Setup lo incluye y la instalacion de
; Ollama funciona sin internet. Si no esta, se descarga del sitio oficial.
Source: "vendor\OllamaSetup.exe"; DestDir: "{app}\setup"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Aprovisionamiento del entorno de IA.
;
; runasoriginaluser es DELIBERADO: Ollama se instala por-usuario (en
; %LOCALAPPDATA%\Programs\Ollama) y guarda los modelos en el perfil del usuario.
; Si esto corriera elevado, en una PC donde el usuario NO es administrador,
; Ollama y los 9 modelos terminarian en el perfil del administrador y la app
; del usuario no los encontraria. Este script no necesita permisos de admin.
;
; Sin runhidden a proposito: la descarga del modelo tarda varios minutos y el
; usuario tiene que ver que algo esta pasando.
Filename: "powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\setup\postinstall.ps1"" -InstallDir ""{app}"""; \
    StatusMsg: "Preparando los agentes de IA (puede tardar varios minutos)..."; \
    Flags: waituntilterminated runasoriginaluser

; Abrir la app al terminar, tambien como el usuario real y no como administrador:
; si arrancara elevada, escribiria la base de datos en el perfil del admin.
Filename: "{app}\{#AppExeName}"; \
    Description: "Abrir {#AppName}"; \
    Flags: nowait postinstall skipifsilent runasoriginaluser

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Los datos del negocio (productos, ventas) viven fuera de la carpeta de
    // instalacion, asi que el desinstalador NO los borra sin preguntar.
    DataDir := ExpandConstant('{localappdata}\EscanApp');
    if DirExists(DataDir) then
    begin
      if MsgBox('¿Querés eliminar también tus datos (base de datos de productos y ventas)?' + #13#10 + #13#10 +
                DataDir + #13#10 + #13#10 +
                'Elegí "No" si pensás reinstalar EscanApp y querés conservar tu información.',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;

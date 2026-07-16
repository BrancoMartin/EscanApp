@echo off
REM ===========================================================================
REM  EscanApp - Build completo del release.
REM
REM  Doble clic en este archivo y listo: compila el frontend, empaqueta la app
REM  y genera release\EscanAppSetup.exe. No hay que correr ningun otro comando.
REM
REM  Para publicar una version nueva: edita el archivo VERSION y corre esto.
REM ===========================================================================

setlocal

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_release.ps1" %*
set EXITCODE=%ERRORLEVEL%

echo.
if %EXITCODE% neq 0 (
    echo El build FALLO. Revisa los mensajes de arriba.
) else (
    echo Build terminado. El instalador esta en la carpeta release\
)
echo.
pause

exit /b %EXITCODE%

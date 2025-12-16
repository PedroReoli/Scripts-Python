@echo off
chcp 65001 >nul
echo Buscando extensoes...

set "OUTPUT_FILE=extensions_list.txt"
set "USER_PROFILE=%USERPROFILE%"

if not exist "%OUTPUT_FILE%" (
    type nul > "%OUTPUT_FILE%"
)

REM Limpar arquivo anterior
> "%OUTPUT_FILE%" echo.

REM Verificar diretorios de extensoes
set "EXT_DIRS[0]=%USER_PROFILE%\.cursor\extensions"
set "EXT_DIRS[1]=%USER_PROFILE%\.vscode\extensions"
set "EXT_DIRS[2]=%USER_PROFILE%\AppData\Roaming\Cursor\User\extensions"
set "EXT_DIRS[3]=%USER_PROFILE%\AppData\Roaming\Code\User\extensions"

for /L %%i in (0,1,3) do (
    call set "CURRENT_DIR=%%EXT_DIRS[%%i]%%"
    if exist "!CURRENT_DIR!" (
        echo Verificando: !CURRENT_DIR!
        for /d %%d in ("!CURRENT_DIR!\*") do (
            set "EXT_NAME=%%~nxd"
            REM Filtrar extensoes corrompidas (comecam com ponto)
            echo !EXT_NAME! | findstr /R "^\\." >nul
            if errorlevel 1 (
                REM Adicionar ao arquivo
                echo !EXT_NAME! >> "%OUTPUT_FILE%"
            )
        )
    )
)

echo.
echo Lista salva em: %CD%\%OUTPUT_FILE%
echo Concluido!


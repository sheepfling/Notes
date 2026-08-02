@echo off
setlocal

if "%~2"=="" (
    echo Usage: %~nx0 ^<input-directory^> ^<output.tar^>
    exit /b 2
)

set "INPUT_DIR=%~1"
set "OUTPUT_TAR=%~2"
set "TAR=%SystemRoot%\System32\tar.exe"
if not exist "%TAR%" set "TAR=tar.exe"

if not exist "%INPUT_DIR%\." (
    echo Input directory does not exist: "%INPUT_DIR%"
    exit /b 1
)
if exist "%OUTPUT_TAR%" (
    echo Refusing to overwrite existing archive: "%OUTPUT_TAR%"
    exit /b 1
)

"%TAR%" -cf "%OUTPUT_TAR%" -C "%INPUT_DIR%" .
if errorlevel 1 (
    echo tar failed while creating "%OUTPUT_TAR%"
    exit /b 1
)

echo Created "%OUTPUT_TAR%"
exit /b 0

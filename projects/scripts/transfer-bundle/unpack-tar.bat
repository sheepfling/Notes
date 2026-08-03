@echo off
setlocal

if "%~2"=="" (
    echo Usage: %~nx0 ^<input.tar^> ^<new-output-directory^>
    exit /b 2
)

set "INPUT_TAR=%~1"
set "OUTPUT_DIR=%~2"
set "TAR=%SystemRoot%\System32\tar.exe"
if not exist "%TAR%" set "TAR=tar.exe"

if not exist "%INPUT_TAR%" (
    echo Archive does not exist: "%INPUT_TAR%"
    exit /b 1
)
if exist "%OUTPUT_DIR%\." (
    echo Refusing to extract into an existing directory: "%OUTPUT_DIR%"
    exit /b 1
)

"%TAR%" -tf "%INPUT_TAR%" >nul
if errorlevel 1 (
    echo Archive listing failed; refusing to extract.
    exit /b 1
)

mkdir "%OUTPUT_DIR%"
"%TAR%" -xf "%INPUT_TAR%" -C "%OUTPUT_DIR%"
if errorlevel 1 (
    echo tar failed while extracting "%INPUT_TAR%"
    exit /b 1
)

echo Extracted "%INPUT_TAR%" to "%OUTPUT_DIR%"
exit /b 0

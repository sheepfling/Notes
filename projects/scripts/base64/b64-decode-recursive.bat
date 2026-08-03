@echo off
setlocal EnableExtensions EnableDelayedExpansion

if "%~1"=="" (
    echo Usage: %~nx0 ^<directory^>
    exit /b 2
)
set "ROOT_DIR=%~1"
if not exist "%ROOT_DIR%\." (
    echo Directory does not exist: "%ROOT_DIR%"
    exit /b 1
)

set "FAILED=0"
for /r "%ROOT_DIR%" %%F in (*.b64.txt) do (
    set "INPUT_FILE=%%F"
    set "OUTPUT_FILE=!INPUT_FILE:~0,-8!"
    if exist "!OUTPUT_FILE!" (
        echo Skipping existing output: "!OUTPUT_FILE!"
    ) else (
        echo Decoding: "!INPUT_FILE!"
        certutil.exe -decode "!INPUT_FILE!" "!OUTPUT_FILE!" >nul
        if errorlevel 1 (
            echo Failed: "!INPUT_FILE!"
            set "FAILED=1"
            if exist "!OUTPUT_FILE!" del /q "!OUTPUT_FILE!"
        )
    )
)

if "%FAILED%"=="1" exit /b 1
echo Recursive Base64 decoding completed.
exit /b 0

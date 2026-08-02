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
for /r "%ROOT_DIR%" %%F in (*) do (
    set "NAME=%%~nxF"
    if /i not "!NAME:~-8!"==".b64.txt" (
        if exist "%%F.b64.txt" (
            echo Skipping existing output: "%%F.b64.txt"
        ) else (
            echo Encoding: "%%F"
            certutil.exe -encode "%%F" "%%F.b64.txt" >nul
            if errorlevel 1 (
                echo Failed: "%%F"
                set "FAILED=1"
                if exist "%%F.b64.txt" del /q "%%F.b64.txt"
            )
        )
    )
)

if "%FAILED%"=="1" exit /b 1
echo Recursive Base64 encoding completed.
exit /b 0

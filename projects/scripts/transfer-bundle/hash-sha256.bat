@echo off
setlocal

if "%~1"=="" (
    echo Usage: %~nx0 ^<file^>
    exit /b 2
)
if not exist "%~1" (
    echo File does not exist: "%~1"
    exit /b 1
)

certutil.exe -hashfile "%~1" SHA256
if errorlevel 1 (
    echo SHA-256 calculation failed.
    exit /b 1
)
exit /b 0

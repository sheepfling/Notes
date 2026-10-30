@echo off
setlocal

if "%~1"=="" (
    echo Usage: %~nx0 ^<input.tar^>
    exit /b 2
)
if not exist "%~1" (
    echo Archive does not exist: "%~1"
    exit /b 1
)
set "TAR=%SystemRoot%\System32\tar.exe"
if not exist "%TAR%" set "TAR=tar.exe"

"%TAR%" -tf "%~1"
if errorlevel 1 (
    echo Archive verification failed: "%~1"
    exit /b 1
)

echo Archive listing completed successfully.
exit /b 0

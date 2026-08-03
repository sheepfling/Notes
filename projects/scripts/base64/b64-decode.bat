@echo off
setlocal

if "%~1"=="" (
    echo Usage: %~nx0 ^<encoded-file^> [decoded-file]
    exit /b 2
)

set "INPUT_FILE=%~1"
set "OUTPUT_FILE=%~2"
if not exist "%INPUT_FILE%" (
    echo Input file does not exist: "%INPUT_FILE%"
    exit /b 1
)
if not defined OUTPUT_FILE set "OUTPUT_FILE=%INPUT_FILE%.decoded"
if exist "%OUTPUT_FILE%" (
    echo Refusing to overwrite existing output: "%OUTPUT_FILE%"
    exit /b 1
)

certutil.exe -decode "%INPUT_FILE%" "%OUTPUT_FILE%"
if errorlevel 1 (
    echo Base64 decoding failed.
    if exist "%OUTPUT_FILE%" del /q "%OUTPUT_FILE%"
    exit /b 1
)
echo Wrote "%OUTPUT_FILE%"
exit /b 0

@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Legacy line-oriented extractor for the `textball.py` format.
rem Prefer `textball.py` extract when Python is available.
rem This fallback does not preserve every whitespace-only line or long line.

if "%~1"=="" (
    echo Usage: %~nx0 ^<textball-file^> [output-directory]
    exit /b 2
)
set "INPUT_FILE=%~1"
set "OUT_DIR=%~2"
if not defined OUT_DIR set "OUT_DIR=extracted_files"
if not exist "%INPUT_FILE%" (
    echo Input file does not exist: "%INPUT_FILE%"
    exit /b 1
)
if not exist "%OUT_DIR%\." mkdir "%OUT_DIR%"

echo This compatibility extractor is intended for trusted, line-oriented textball files.
echo Extracting "%INPUT_FILE%" to "%OUT_DIR%"
echo For hash-checked extraction, use textball.py when available.

set "HEADER="
set /a LINE_COUNT=0
for /f "usebackq delims=" %%A in ("%INPUT_FILE%") do (
    set "LINE=%%A"
    if not defined HEADER (
        set "HEADER=!LINE!"
        for /f "tokens=1,2,3,4 delims=	" %%B in ("!HEADER!") do (
            set "FILEPATH=%%~B"
            set "NUM_LINES=%%C"
            set "IS_BASE64=%%D"
            set "OUTPUT_PATH=%OUT_DIR%\!FILEPATH!"
        )
        if not defined FILEPATH (
            echo Malformed header.
            exit /b 1
        )
        for %%P in ("!OUTPUT_PATH!") do if not exist "%%~dpP\." mkdir "%%~dpP"
        >"!OUTPUT_PATH!" type nul
        set /a LINE_COUNT=0
    ) else (
        >>"!OUTPUT_PATH!" echo(!LINE!
        set /a LINE_COUNT+=1
        if !LINE_COUNT! geq !NUM_LINES! (
            set "HEADER="
            set "FILEPATH="
            set "NUM_LINES="
            set "IS_BASE64="
        )
    )
)

echo Compatibility extraction completed. Verify important files separately.
exit /b 0

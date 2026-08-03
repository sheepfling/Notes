@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Legacy line-oriented extractor for the `textball.py` format.
rem Prefer `textball.py` extract when Python is available.
rem This fallback does not preserve every whitespace-only line or long line.

if "%~1"=="" (
    echo Usage: %~nx0 ^<textball-file^> [output-directory] [--legacy]
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
set "FIRST_LINE=1"
set "PROCESS_LINE=1"
for /f "usebackq delims=" %%A in ("%INPUT_FILE%") do (
    set "LINE=%%A"
    if "!FIRST_LINE!"=="1" (
        set "FIRST_LINE=0"
        if /i "!LINE!"=="NOTES-TEXTBALL/1" (
            set "PROCESS_LINE=0"
        ) else if /i not "%~3"=="--legacy" (
            echo Unsupported textball format. Pass --legacy only for trusted historical files.
            exit /b 2
        )
    )
    if not "!LINE!"=="NOTES-TEXTBALL/1" if "!FIRST_LINE!"=="0" set "PROCESS_LINE=1"
    if "!PROCESS_LINE!"=="1" if not defined HEADER (
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
        if "!FILEPATH:~0,1!"=="\" (
            echo Absolute paths are not allowed.
            exit /b 1
        )
        if "!FILEPATH:~1,1!"==":" (
            echo Drive-qualified paths are not allowed.
            exit /b 1
        )
        if not "!FILEPATH:..=!"=="!FILEPATH!" (
            echo Parent-directory paths are not allowed.
            exit /b 1
        )
        for %%P in ("!OUTPUT_PATH!") do if not exist "%%~dpP\." mkdir "%%~dpP"
        >"!OUTPUT_PATH!" type nul
        set /a LINE_COUNT=0
    ) else if "!PROCESS_LINE!"=="1" (
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

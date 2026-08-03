@echo off
setlocal

if "%~2"=="" (
    echo Usage: %~nx0 ^<input-directory^> ^<output-prefix^>
    echo Creates ^<output-prefix^>.tar.gz, .tar.gz.b64.txt, .tar.gz.sha256, and .tar.gz.manifest.txt.
    exit /b 2
)

set "INPUT_DIR=%~1"
set "OUTPUT_PREFIX=%~2"
set "ARCHIVE=%OUTPUT_PREFIX%.tar.gz"
set "ENCODED=%ARCHIVE%.b64.txt"
set "HASH_FILE=%ARCHIVE%.sha256"
set "MANIFEST=%ARCHIVE%.manifest.txt"
set "TAR=%SystemRoot%\System32\tar.exe"
if not exist "%TAR%" set "TAR=tar.exe"

if not exist "%INPUT_DIR%\." (
    echo Input directory does not exist: "%INPUT_DIR%"
    exit /b 1
)
for %%F in ("%ARCHIVE%" "%ENCODED%" "%HASH_FILE%" "%MANIFEST%") do if exist "%%~F" (
    echo Refusing to overwrite existing output: "%%~F"
    exit /b 1
)

"%TAR%" -czf "%ARCHIVE%" -C "%INPUT_DIR%" .
if errorlevel 1 (
    echo tar failed while creating "%ARCHIVE%"
    if exist "%ARCHIVE%" del /q "%ARCHIVE%"
    exit /b 1
)

set "ARCHIVE_HASH="
for /f "skip=1 tokens=*" %%H in ('certutil.exe -hashfile "%ARCHIVE%" SHA256') do if not defined ARCHIVE_HASH set "ARCHIVE_HASH=%%H"
if not defined ARCHIVE_HASH (
    echo SHA-256 calculation failed.
    if exist "%ARCHIVE%" del /q "%ARCHIVE%"
    exit /b 1
)
>"%HASH_FILE%" echo %ARCHIVE_HASH%
>"%MANIFEST%" echo NOTES-TRANSFER/1
>>"%MANIFEST%" echo archive=tar.gz
>>"%MANIFEST%" echo encoding=certutil-base64
>>"%MANIFEST%" echo sha256=%ARCHIVE_HASH%

certutil.exe -encode "%ARCHIVE%" "%ENCODED%" >nul
if errorlevel 1 (
    echo Base64 encoding failed.
    if exist "%ARCHIVE%" del /q "%ARCHIVE%"
    if exist "%HASH_FILE%" del /q "%HASH_FILE%"
    if exist "%MANIFEST%" del /q "%MANIFEST%"
    if exist "%ENCODED%" del /q "%ENCODED%"
    exit /b 1
)

echo Created archive: "%ARCHIVE%"
echo Created transfer text: "%ENCODED%"
echo Created SHA-256 record: "%HASH_FILE%"
echo Created transfer manifest: "%MANIFEST%"
exit /b 0

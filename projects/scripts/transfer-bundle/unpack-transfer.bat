@echo off
setlocal EnableExtensions EnableDelayedExpansion

if "%~2"=="" (
    echo Usage: %~nx0 ^<encoded-file.b64.txt^> ^<new-output-directory^> [--legacy]
    exit /b 2
)

set "ENCODED=%~1"
set "OUTPUT_DIR=%~2"
set "ARCHIVE=%ENCODED:~0,-8%"
set "HASH_FILE=%ARCHIVE%.sha256"
set "MANIFEST=%ARCHIVE%.manifest.txt"
set "TAR=%SystemRoot%\System32\tar.exe"
if not exist "%TAR%" set "TAR=tar.exe"

if /i not "%ENCODED:~-8%"==".b64.txt" (
    echo Encoded input must end in .b64.txt: "%ENCODED%"
    exit /b 2
)
if not exist "%ENCODED%" (
    echo Encoded input does not exist: "%ENCODED%"
    exit /b 1
)
if exist "%OUTPUT_DIR%\." (
    echo Refusing to extract into an existing directory: "%OUTPUT_DIR%"
    exit /b 1
)

set "LEGACY=0"
if /i "%~3"=="--legacy" set "LEGACY=1"
if exist "%MANIFEST%" (
    set "MANIFEST_MAGIC="
    set /p "MANIFEST_MAGIC="<"%MANIFEST%"
    if /i not "!MANIFEST_MAGIC!"=="NOTES-TRANSFER/1" (
        echo Unsupported transfer manifest format.
        exit /b 2
    )
    set "MANIFEST_ARCHIVE="
    set "MANIFEST_ENCODING="
    set "MANIFEST_HASH="
    for /f "tokens=1,* delims==" %%A in ('findstr /b "archive= encoding= sha256=" "%MANIFEST%"') do (
        if /i "%%A"=="archive" set "MANIFEST_ARCHIVE=%%B"
        if /i "%%A"=="encoding" set "MANIFEST_ENCODING=%%B"
        if /i "%%A"=="sha256" set "MANIFEST_HASH=%%B"
    )
    if /i not "!MANIFEST_ARCHIVE!"=="tar.gz" (
        echo Transfer manifest archive type is invalid.
        exit /b 2
    )
    if /i not "!MANIFEST_ENCODING!"=="certutil-base64" (
        echo Transfer manifest encoding is invalid.
        exit /b 2
    )
    if not defined MANIFEST_HASH (
        echo Transfer manifest has no SHA-256 value.
        exit /b 2
    )
) else if "!LEGACY!"=="0" (
    echo Transfer manifest is missing. Pass --legacy only for trusted historical bundles.
    exit /b 2
)

set "DECODED_HERE=0"
if not exist "%ARCHIVE%" (
    certutil.exe -decode "%ENCODED%" "%ARCHIVE%" >nul
    if errorlevel 1 (
        echo Base64 decoding failed.
        if exist "%ARCHIVE%" del /q "%ARCHIVE%"
        exit /b 1
    )
    set "DECODED_HERE=1"
) else (
    echo Reusing existing decoded archive: "%ARCHIVE%"
)

set "ACTUAL_HASH="
for /f "skip=1 tokens=*" %%H in ('certutil.exe -hashfile "%ARCHIVE%" SHA256') do if not defined ACTUAL_HASH set "ACTUAL_HASH=%%H"
if not defined ACTUAL_HASH (
    echo SHA-256 calculation failed.
    if "!DECODED_HERE!"=="1" if exist "%ARCHIVE%" del /q "%ARCHIVE%"
    exit /b 1
)

if exist "%HASH_FILE%" (
    set "EXPECTED_HASH="
    set /p "EXPECTED_HASH="<"%HASH_FILE%"
    if /i not "!ACTUAL_HASH!"=="!EXPECTED_HASH!" (
        echo SHA-256 mismatch for "%ARCHIVE%"
        echo Expected: !EXPECTED_HASH!
        echo Actual:   !ACTUAL_HASH!
        if "!DECODED_HERE!"=="1" if exist "%ARCHIVE%" del /q "%ARCHIVE%"
        exit /b 1
    )
    echo SHA-256 verified: !ACTUAL_HASH!
) else (
    echo Warning: no SHA-256 sidecar found; archive authenticity was not fully verified.
    echo SHA-256: !ACTUAL_HASH!
)
if defined MANIFEST_HASH if /i not "!ACTUAL_HASH!"=="!MANIFEST_HASH!" (
    echo SHA-256 mismatch with transfer manifest for "%ARCHIVE%"
    if "!DECODED_HERE!"=="1" if exist "%ARCHIVE%" del /q "%ARCHIVE%"
    exit /b 1
)

"%TAR%" -tzf "%ARCHIVE%" >nul
if errorlevel 1 (
    echo Archive listing failed; refusing to extract.
    if "!DECODED_HERE!"=="1" if exist "%ARCHIVE%" del /q "%ARCHIVE%"
    exit /b 1
)

mkdir "%OUTPUT_DIR%"
"%TAR%" -xzf "%ARCHIVE%" -C "%OUTPUT_DIR%"
if errorlevel 1 (
    echo tar failed while extracting "%ARCHIVE%"
    exit /b 1
)

echo Extracted "%ARCHIVE%" to "%OUTPUT_DIR%"
exit /b 0

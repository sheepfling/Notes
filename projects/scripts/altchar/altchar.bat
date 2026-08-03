@echo off
setlocal EnableExtensions EnableDelayedExpansion

if "%~3"=="" (
    echo Usage: %~nx0 ^<insert^|remove^> ^<input-file^> ^<marker^> [output-file]
    exit /b 2
)
set "ACTION=%~1"
set "INPUT_FILE=%~2"
set "MARKER=%~3"
set "OUTPUT_FILE=%~4"
if not exist "%INPUT_FILE%" (
    echo Input file does not exist: "%INPUT_FILE%"
    exit /b 1
)
if not defined OUTPUT_FILE set "OUTPUT_FILE=%INPUT_FILE%.output"
if exist "%OUTPUT_FILE%" (
    echo Refusing to overwrite existing output: "%OUTPUT_FILE%"
    exit /b 1
)

rem This is a line-oriented fallback and cannot safely handle arbitrary binary data
rem or lines longer than cmd.exe's practical expansion limit.
if /i "%ACTION%"=="insert" goto insert
if /i "%ACTION%"=="remove" goto remove
echo Action must be insert or remove.
exit /b 2

:insert
for /f "usebackq delims=" %%A in ("%INPUT_FILE%") do (
    set "LINE=%%A"
    set "OUT="
    for /l %%I in (0,1,8191) do (
        set "CHAR=!LINE:~%%I,1!"
        if not "!CHAR!"=="" set "OUT=!OUT!!CHAR!!MARKER!"
    )
    >>"%OUTPUT_FILE%" echo(!OUT!
)
goto done

:remove
for /f "usebackq delims=" %%A in ("%INPUT_FILE%") do (
    set "LINE=%%A"
    set "OUT="
    for /l %%I in (0,2,8191) do (
        set "CHAR=!LINE:~%%I,1!"
        if not "!CHAR!"=="" set "OUT=!OUT!!CHAR!"
    )
    >>"%OUTPUT_FILE%" echo(!OUT!
)

:done
echo Wrote "%OUTPUT_FILE%"
exit /b 0

@echo off
setlocal EnableDelayedExpansion
title OncoCare AI - Download Offline Packages
mode con: cols=78 lines=50
color 0B

set "BASEDIR=%~dp0"
set "BASEDIR=%BASEDIR:~0,-1%"
set "OFFLINE_DIR=%BASEDIR%\offline_packages"
set "VENV_DIR=%BASEDIR%\venv"
set "LOGS_DIR=%BASEDIR%\logs"

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
if not exist "%OFFLINE_DIR%" mkdir "%OFFLINE_DIR%"
set "LOGFILE=%LOGS_DIR%\offline_download_%DATE:~-4,4%%DATE:~-7,2%%DATE:~-10,2%.log"

cls
echo.
echo  ================================================================
echo   OncoCare AI  -  OFFLINE PACKAGE DOWNLOADER
echo  ================================================================
echo.
echo  What this does:
echo    Downloads all required Python packages to this folder.
echo    After this is done, OncoCare AI will work WITHOUT internet.
echo    Run this tool ONCE while you have internet access.
echo.
echo  ================================================================
echo.

:: Check internet
echo  Checking internet connection...
ping -n 1 -w 3000 8.8.8.8 >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FAIL]  No internet connection detected.
    echo   This tool requires internet to download packages.
    echo   Please connect to internet and try again.
    echo.
    pause
    exit /b 1
)
echo   [ OK ]  Internet connection confirmed.
echo.

:: Find pip
echo  Finding Python pip...
set "PIP="
if exist "%VENV_DIR%\Scripts\pip.exe" (
    set "PIP=%VENV_DIR%\Scripts\pip.exe"
    echo   [ OK ]  Using virtual environment pip.
) else (
    pip --version >nul 2>&1
    if !errorlevel!==0 (
        set "PIP=pip"
        echo   [ OK ]  Using system pip.
    ) else (
        py -m pip --version >nul 2>&1
        if !errorlevel!==0 (
            set "PIP=py -m pip"
            echo   [ OK ]  Using Python launcher pip.
        ) else (
            echo   [FAIL]  pip not found.
            echo   Please run START_OncoCare_AI.bat first to set up Python.
            echo   Then run this downloader again.
            pause
            exit /b 1
        )
    )
)
echo.

:: Upgrade pip
echo  [Step 1 of 4]  Upgrading pip to latest version...
%PIP% install --upgrade pip --quiet >> "%LOGFILE%" 2>&1
echo   [ OK ]  pip upgraded.
echo.

:: Download core packages
echo  [Step 2 of 4]  Downloading core required packages...
echo  This may take 3 to 8 minutes depending on your connection speed.
echo.

set "PACKAGES=flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil"
set /a TOTAL=0
set /a DONE=0

for %%K in (%PACKAGES%) do set /a TOTAL+=1

for %%K in (%PACKAGES%) do (
    set /a DONE+=1
    echo   [!DONE! of %TOTAL%]  Downloading: %%K
    %PIP% download %%K --dest="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (
        echo              [ OK ]  %%K saved to offline cache
    ) else (
        echo              [WARN]  %%K had a warning - check the log if issues occur
    )
)
echo.

:: Download optional packages
echo  [Step 3 of 4]  Downloading optional enhancement packages...
echo  These are extras - they will be skipped if not available.
echo.
set "OPTIONAL=langchain openai tiktoken"
for %%K in (%OPTIONAL%) do (
    echo   Trying: %%K
    %PIP% download %%K --dest="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (
        echo           [ OK ]  %%K
    ) else (
        echo           [ -- ]  %%K not available or skipped
    )
)
echo.

:: Count and verify
echo  [Step 4 of 4]  Verifying downloads...
set /a WHLCOUNT=0
for %%W in ("%OFFLINE_DIR%\*.whl") do set /a WHLCOUNT+=1
for %%W in ("%OFFLINE_DIR%\*.tar.gz") do set /a WHLCOUNT+=1

echo   [ OK ]  Total packages cached: %WHLCOUNT% files
echo   [ OK ]  Location: %OFFLINE_DIR%
echo.

:: Save manifest
echo  Saving package manifest...
(
echo OncoCare AI - Offline Package Cache Manifest
echo Downloaded: %DATE% %TIME%
echo Total files: %WHLCOUNT%
echo.
echo File list:
dir "%OFFLINE_DIR%\*.whl" /b 2>nul
dir "%OFFLINE_DIR%\*.tar.gz" /b 2>nul
) > "%OFFLINE_DIR%\MANIFEST.txt"
echo   [ OK ]  Manifest saved.
echo.

echo  ================================================================
echo   DOWNLOAD COMPLETE
echo  ================================================================
echo.
echo   OncoCare AI will now work WITHOUT internet connection.
echo   %WHLCOUNT% packages are cached in: offline_packages folder
echo.
echo   How to use offline:
echo     Just run START_OncoCare_AI.bat as normal.
echo     It detects offline mode and installs from the local cache.
echo.
echo  ================================================================
echo.
echo   Log saved to: %LOGFILE%
echo.
pause

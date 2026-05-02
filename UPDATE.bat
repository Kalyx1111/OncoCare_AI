@echo off
setlocal EnableDelayedExpansion
title OncoCare AI - UPDATE
mode con: cols=78 lines=45
color 0A

set "BASEDIR=%~dp0"
set "BASEDIR=%BASEDIR:~0,-1%"
set "VENV_DIR=%BASEDIR%\venv"
set "OFFLINE_DIR=%BASEDIR%\offline_packages"
set "LOGS_DIR=%BASEDIR%\logs"

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
set "LOGFILE=%LOGS_DIR%\update_%DATE:~-4,4%%DATE:~-7,2%%DATE:~-10,2%.log"

cls
echo.
echo  ================================================================
echo   OncoCare AI  -  UPDATE TOOL
echo  ================================================================
echo  Updates Python packages to their latest versions.
echo  Your uploaded files and saved profiles are NOT affected.
echo  ================================================================
echo.

:: Check internet
echo  Checking internet connection...
ping -n 1 -w 2000 8.8.8.8 >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FAIL]  No internet connection.
    echo   Updates require internet. Please connect and try again.
    echo.
    pause
    exit /b 1
)
echo   [ OK ]  Internet connected.
echo.

:: Check venv
if not exist "%VENV_DIR%\Scripts\pip.exe" (
    echo   [FAIL]  Virtual environment not found.
    echo   Please run START_OncoCare_AI.bat first to set it up.
    echo   Then run this update tool again.
    pause
    exit /b 1
)
set "PIP=%VENV_DIR%\Scripts\pip.exe"
echo   [ OK ]  Virtual environment found.
echo.

:: Update menu
echo  ================================================================
echo   What would you like to do?
echo  ================================================================
echo.
echo   1  =  Update all packages to latest versions  (recommended)
echo   2  =  Update packages AND refresh offline cache
echo   3  =  Check which packages have updates available
echo   0  =  Cancel and exit
echo.
set /p "CHOICE=  Enter choice (0-3): "
if "%CHOICE%"=="0" exit /b 0
if "%CHOICE%"=="3" goto :CHECK_OUTDATED
if "%CHOICE%"=="1" goto :DO_UPDATE
if "%CHOICE%"=="2" goto :DO_UPDATE_AND_CACHE
echo   Invalid choice. Exiting.
exit /b 0

:CHECK_OUTDATED
echo.
echo  Checking for outdated packages...
echo  ----------------------------------------------------------------
"%PIP%" list --outdated 2>>"%LOGFILE%"
echo.
echo  Done. Review the list above to see what can be updated.
pause
exit /b 0

:DO_UPDATE
echo.
echo  [Step 1 of 2]  Upgrading pip...
"%PIP%" install --upgrade pip --quiet >> "%LOGFILE%" 2>&1
echo   [ OK ]  pip upgraded.
echo.
echo  [Step 2 of 2]  Upgrading OncoCare AI packages...
for %%K in (flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil) do (
    echo   Upgrading: %%K
    "%PIP%" install --upgrade %%K --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (
        echo            [ OK ]
    ) else (
        echo            [WARN]  See log for details
    )
)
echo.
echo   [ OK ]  All packages updated.
goto :UPDATE_DONE

:DO_UPDATE_AND_CACHE
echo.
echo  [Step 1 of 3]  Upgrading pip...
"%PIP%" install --upgrade pip --quiet >> "%LOGFILE%" 2>&1
echo   [ OK ]  pip upgraded.
echo.
echo  [Step 2 of 3]  Upgrading packages...
for %%K in (flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil) do (
    echo   Upgrading: %%K
    "%PIP%" install --upgrade %%K --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
)
echo   [ OK ]  Packages upgraded.
echo.
echo  [Step 3 of 3]  Refreshing offline cache...
for %%K in (flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil) do (
    "%PIP%" download %%K --dest="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
)
echo   [ OK ]  Offline cache updated.
goto :UPDATE_DONE

:UPDATE_DONE
echo.
echo  ================================================================
echo   Update complete.
echo   Log saved to: %LOGFILE%
echo  ================================================================
echo.
echo  Restart OncoCare AI to use the updated packages.
echo  Run START_OncoCare_AI.bat to restart.
echo.
pause

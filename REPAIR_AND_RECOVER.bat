@echo off
setlocal EnableDelayedExpansion
title OncoCare AI - REPAIR AND RECOVERY
mode con: cols=78 lines=50
color 0C

set "BASEDIR=%~dp0"
set "BASEDIR=%BASEDIR:~0,-1%"
set "VENV_DIR=%BASEDIR%\venv"
set "LOGS_DIR=%BASEDIR%\logs"
set "OFFLINE_DIR=%BASEDIR%\offline_packages"
set "PYTHON_EXE="
set "ONLINE=false"

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
set "LOGFILE=%LOGS_DIR%\repair_%DATE:~-4,4%%DATE:~-7,2%%DATE:~-10,2%.log"

cls
echo.
echo  ================================================================
echo   OncoCare AI  -  REPAIR AND RECOVERY TOOL
echo  ================================================================
echo  This tool fixes the most common problems.
echo  Each step is shown clearly so you know what is happening.
echo  ================================================================
echo.

:: ---------------------------------------------------------------
:: CHECK INTERNET
:: ---------------------------------------------------------------
echo  Checking internet connection...
ping -n 1 -w 2000 8.8.8.8 >nul 2>&1
if %errorlevel%==0 (
    set "ONLINE=true"
    echo   [ OK ]  Internet: ONLINE
) else (
    set "ONLINE=false"
    echo   [ -- ]  Internet: OFFLINE - will use cached packages only
)
echo.

:: ---------------------------------------------------------------
:: FIND PYTHON
:: ---------------------------------------------------------------
echo  Looking for Python...
if exist "%BASEDIR%\python_runtime\python.exe" (
    set "PYTHON_EXE=%BASEDIR%\python_runtime\python.exe"
    echo   [ OK ]  Found local Python in python_runtime folder
    goto :PYTHON_FOUND_REPAIR
)
python --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=python"
    for /f "delims=" %%V in ('python --version 2^>^&1') do echo   [ OK ]  System Python: %%V
    goto :PYTHON_FOUND_REPAIR
)
py --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=py"
    echo   [ OK ]  Python launcher found
    goto :PYTHON_FOUND_REPAIR
)
echo   [FAIL]  Python not found.
echo.
if "%ONLINE%"=="true" (
    echo   Downloading Python installer...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py_setup.exe' -UseBasicParsing" >> "%LOGFILE%" 2>&1
    if exist "%TEMP%\py_setup.exe" (
        echo   When the installer opens, CHECK "Add Python to PATH" then click Install Now.
        start /wait "" "%TEMP%\py_setup.exe"
        set "PYTHON_EXE=python"
    )
) else (
    echo   Please install Python from https://www.python.org/downloads/
    echo   Then run this repair tool again.
    pause
    exit /b 1
)

:PYTHON_FOUND_REPAIR
echo.

:: ---------------------------------------------------------------
:: REPAIR MENU
:: ---------------------------------------------------------------
echo  ================================================================
echo   What would you like to repair?
echo  ================================================================
echo.
echo   1  =  Rebuild virtual environment  (fixes most Python errors)
echo   2  =  Reinstall all packages       (fixes import/module errors)
echo   3  =  Recreate missing folders     (fixes folder not found errors)
echo   4  =  Clear logs and cache files   (cleans up temp files)
echo   5  =  Full factory reset           (rebuilds everything, keeps uploads)
echo   6  =  Fix port conflict            (frees port 5050 if something is using it)
echo   7  =  Run ALL repairs              (full repair - recommended)
echo   0  =  Exit without repairing
echo.
set /p "CHOICE=  Enter your choice (0-7): "

if "%CHOICE%"=="0" exit /b 0
if "%CHOICE%"=="1" goto :DO_VENV
if "%CHOICE%"=="2" goto :DO_PACKAGES
if "%CHOICE%"=="3" goto :DO_FOLDERS
if "%CHOICE%"=="4" goto :DO_LOGS
if "%CHOICE%"=="5" goto :DO_FACTORY
if "%CHOICE%"=="6" goto :DO_PORT
if "%CHOICE%"=="7" goto :DO_ALL
echo   Invalid choice. Please enter a number from 0 to 7.
pause
goto :EOF

:: ---------------------------------------------------------------
:: OPTION 1 - REBUILD VENV
:: ---------------------------------------------------------------
:DO_VENV
echo.
echo  Rebuilding virtual environment...
echo  ----------------------------------------------------------------
call :LOG "Rebuilding venv..."
if exist "%VENV_DIR%" (
    echo   Removing old virtual environment...
    rmdir /s /q "%VENV_DIR%" >> "%LOGFILE%" 2>&1
)
echo   Creating fresh virtual environment...
"%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%LOGFILE%" 2>&1
if %errorlevel%==0 (
    echo   [ OK ]  Virtual environment rebuilt successfully.
    call :LOG "Venv rebuilt OK"
) else (
    echo   [FAIL]  Could not rebuild virtual environment.
    echo   Check log file: %LOGFILE%
    call :LOG "Venv rebuild FAILED"
    start notepad "%LOGFILE%"
)
goto :DONE

:: ---------------------------------------------------------------
:: OPTION 2 - REINSTALL PACKAGES
:: ---------------------------------------------------------------
:DO_PACKAGES
echo.
echo  Reinstalling all Python packages...
echo  ----------------------------------------------------------------
call :LOG "Reinstalling packages..."

if not exist "%VENV_DIR%\Scripts\pip.exe" (
    echo   Virtual environment not found. Rebuilding it first...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%LOGFILE%" 2>&1
)

set "PIP=%VENV_DIR%\Scripts\pip.exe"
"%PIP%" install --upgrade pip --quiet >> "%LOGFILE%" 2>&1

if "%ONLINE%"=="true" (
    echo   Downloading and installing from internet...
    for %%K in (flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil) do (
        echo     Installing %%K ...
        "%PIP%" install %%K --upgrade --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
        if !errorlevel!==0 (
            "%PIP%" download %%K --dest="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
        )
    )
) else (
    echo   Installing from offline cache...
    if exist "%OFFLINE_DIR%\*.whl" (
        "%PIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --no-index --find-links="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    ) else (
        echo   [FAIL]  No offline cache found. Connect to internet and try again.
        goto :DONE
    )
)
echo   [ OK ]  Packages reinstalled.
call :LOG "Packages reinstalled"
goto :DONE

:: ---------------------------------------------------------------
:: OPTION 3 - RECREATE FOLDERS
:: ---------------------------------------------------------------
:DO_FOLDERS
echo.
echo  Recreating missing folders...
echo  ----------------------------------------------------------------
call :LOG "Recreating folders..."
for %%D in (uploads offline_packages logs data static reports_db modules) do (
    if not exist "%BASEDIR%\%%D\" (
        mkdir "%BASEDIR%\%%D" >nul 2>&1
        echo   Created folder: %%D
    ) else (
        echo   [ OK ]  Folder exists: %%D
    )
)
echo   [ OK ]  All folders verified.
call :LOG "Folders OK"
goto :DONE

:: ---------------------------------------------------------------
:: OPTION 4 - CLEAR LOGS
:: ---------------------------------------------------------------
:DO_LOGS
echo.
echo  Clearing log and cache files...
echo  ----------------------------------------------------------------
if exist "%LOGS_DIR%" (
    del /q "%LOGS_DIR%\*.log" >nul 2>&1
    del /q "%LOGS_DIR%\*.txt" >nul 2>&1
    echo   [ OK ]  Log files cleared.
)
if exist "%BASEDIR%\__pycache__" rmdir /s /q "%BASEDIR%\__pycache__" >nul 2>&1
if exist "%BASEDIR%\modules\__pycache__" rmdir /s /q "%BASEDIR%\modules\__pycache__" >nul 2>&1
del /q "%BASEDIR%\*.pyc" >nul 2>&1
echo   [ OK ]  Cache files cleared.
call :LOG "Logs and cache cleared"
goto :DONE

:: ---------------------------------------------------------------
:: OPTION 5 - FACTORY RESET
:: ---------------------------------------------------------------
:DO_FACTORY
echo.
echo  ================================================================
echo   FACTORY RESET
echo   This will rebuild everything from scratch.
echo   Your uploaded files in the uploads folder will NOT be deleted.
echo  ================================================================
echo.
set /p "CONFIRM=  Type YES to confirm factory reset: "
if /i not "%CONFIRM%"=="YES" (
    echo   Cancelled. Nothing was changed.
    goto :DONE
)
call :LOG "FACTORY RESET started"
echo   Removing virtual environment...
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
echo   Clearing logs...
if exist "%LOGS_DIR%" del /q "%LOGS_DIR%\*.*" >nul 2>&1
echo   Clearing Python cache...
if exist "%BASEDIR%\__pycache__" rmdir /s /q "%BASEDIR%\__pycache__"
if exist "%BASEDIR%\modules\__pycache__" rmdir /s /q "%BASEDIR%\modules\__pycache__"
echo   Recreating folders...
for %%D in (uploads offline_packages logs data static reports_db modules) do (
    if not exist "%BASEDIR%\%%D\" mkdir "%BASEDIR%\%%D"
)
echo   Rebuilding virtual environment...
"%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%LOGFILE%" 2>&1
echo   Reinstalling packages...
set "PIP=%VENV_DIR%\Scripts\pip.exe"
if "%ONLINE%"=="true" (
    "%PIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --quiet >> "%LOGFILE%" 2>&1
) else (
    if exist "%OFFLINE_DIR%\*.whl" (
        "%PIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --no-index --find-links="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    )
)
echo   [ OK ]  Factory reset complete.
echo   You can now run START_OncoCare_AI.bat
call :LOG "Factory reset complete"
goto :DONE

:: ---------------------------------------------------------------
:: OPTION 6 - FIX PORT
:: ---------------------------------------------------------------
:DO_PORT
echo.
echo  Fixing port 5050 conflict...
echo  ----------------------------------------------------------------
call :LOG "Fixing port 5050..."
netstat -ano 2>nul | findstr ":5050 " >nul 2>&1
if %errorlevel%==0 (
    echo   Port 5050 is in use. Finding and stopping the process...
    for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":5050 "') do (
        echo   Stopping process ID: %%P
        taskkill /PID %%P /F >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo   [ OK ]  Port 5050 is now free.
    call :LOG "Port 5050 freed"
) else (
    echo   [ OK ]  Port 5050 is already free. Nothing to do.
)
goto :DONE

:: ---------------------------------------------------------------
:: OPTION 7 - ALL REPAIRS
:: ---------------------------------------------------------------
:DO_ALL
echo.
echo  Running all repair steps...
echo  ================================================================
call :LOG "Running all repairs..."
goto :DO_PORT_INLINE

:DO_PORT_INLINE
echo.
echo   Step 1 of 5 - Fixing port...
netstat -ano 2>nul | findstr ":5050 " >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":5050 "') do taskkill /PID %%P /F >nul 2>&1
    timeout /t 1 /nobreak >nul
)
echo   [ OK ]  Port done.

echo.
echo   Step 2 of 5 - Rebuilding virtual environment...
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%" >> "%LOGFILE%" 2>&1
"%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%LOGFILE%" 2>&1
echo   [ OK ]  Virtual environment rebuilt.

echo.
echo   Step 3 of 5 - Installing packages...
set "PIP=%VENV_DIR%\Scripts\pip.exe"
"%PIP%" install --upgrade pip --quiet >> "%LOGFILE%" 2>&1
if "%ONLINE%"=="true" (
    "%PIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
) else (
    if exist "%OFFLINE_DIR%\*.whl" (
        "%PIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --no-index --find-links="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    )
)
echo   [ OK ]  Packages installed.

echo.
echo   Step 4 of 5 - Recreating folders...
for %%D in (uploads offline_packages logs data static reports_db modules) do (
    if not exist "%BASEDIR%\%%D\" mkdir "%BASEDIR%\%%D" >nul 2>&1
)
echo   [ OK ]  Folders done.

echo.
echo   Step 5 of 5 - Clearing old logs...
if exist "%LOGS_DIR%" del /q "%LOGS_DIR%\*.log" >nul 2>&1
if exist "%BASEDIR%\__pycache__" rmdir /s /q "%BASEDIR%\__pycache__" >nul 2>&1
echo   [ OK ]  Logs cleared.
call :LOG "All repairs complete"
goto :DONE

:: ---------------------------------------------------------------
:: DONE
:: ---------------------------------------------------------------
:DONE
echo.
echo  ================================================================
echo   Repair complete.
echo   Log saved to: %LOGFILE%
echo  ================================================================
echo.
echo   What would you like to do next?
echo     S  =  Start OncoCare AI now
echo     D  =  Run Diagnostics to verify everything is OK
echo     X  =  Exit
echo.
set /p "POST=  Choice [S/D/X]: "
if /i "%POST%"=="S" call "%BASEDIR%\START_OncoCare_AI.bat"
if /i "%POST%"=="D" call "%BASEDIR%\DIAGNOSTIC.bat"
exit /b 0

:LOG
echo [%DATE% %TIME%] %~1 >> "%LOGFILE%"
goto :EOF

@echo off
setlocal EnableDelayedExpansion
title OncoCare AI - Launching
mode con: cols=78 lines=50
color 0F

:: Get the folder where this bat file lives
set "BASEDIR=%~dp0"
if "%BASEDIR:~-1%"=="\" set "BASEDIR=%BASEDIR:~0,-1%"

set "VENV_DIR=%BASEDIR%\venv"
set "OFFLINE_DIR=%BASEDIR%\offline_packages"
set "LOGS_DIR=%BASEDIR%\logs"
set "PORT=5050"
set "ONLINE=false"
set "PYTHON_EXE="
set "VPYTHON="
set "VPIP="

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

:: Build log filename without spaces
set "YY=%DATE:~-4%"
set "MM=%DATE:~-7,2%"
set "DD=%DATE:~-10,2%"
set "LOGFILE=%LOGS_DIR%\launch_%YY%%MM%%DD%.log"

call :LOG "===== OncoCare AI Launch Started %DATE% %TIME% ====="
call :LOG "Base folder: %BASEDIR%"

cls
echo.
echo  ================================================================
echo   OncoCare AI  -  Cancer Intelligence Platform  v2.0
echo  ================================================================
echo.
echo  MEDICAL DISCLAIMER: This is an AI Research Tool ONLY.
echo  NOT a medical diagnosis. Always consult your oncologist.
echo.
echo  ================================================================
echo.

:: ================================================================
:: STEP 1  -  CHECK INTERNET
:: ================================================================
echo  [STEP 1/7]  Checking internet connection...
call :LOG "Checking internet"
ping -n 1 -w 2000 8.8.8.8 >nul 2>&1
if %errorlevel%==0 (
    set "ONLINE=true"
    echo              [ OK ]  Online - live AI features available
    call :LOG "Internet: ONLINE"
) else (
    set "ONLINE=false"
    echo              [ -- ]  Offline - offline research mode will be used
    call :LOG "Internet: OFFLINE"
)
echo.

:: ================================================================
:: STEP 2  -  FIND PYTHON
:: ================================================================
echo  [STEP 2/7]  Looking for Python...
call :LOG "Locating Python"

:: Check local runtime first
if exist "%BASEDIR%\python_runtime\python.exe" (
    set "PYTHON_EXE=%BASEDIR%\python_runtime\python.exe"
    echo              [ OK ]  Local Python found in python_runtime folder
    call :LOG "Local Python found"
    goto :PYTHON_OK
)

:: Try system python
python --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=python"
    for /f "tokens=*" %%V in ('python --version 2^>^&1') do (
        echo              [ OK ]  %%V found
        call :LOG "System Python: %%V"
    )
    goto :PYTHON_OK
)

:: Try py launcher
py --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=py"
    for /f "tokens=*" %%V in ('py --version 2^>^&1') do (
        echo              [ OK ]  %%V found via py launcher
        call :LOG "Python launcher: %%V"
    )
    goto :PYTHON_OK
)

:: Search common install paths
set "FOUND_PATH="
for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "C:\Python39\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files\Python310\python.exe"
) do (
    if exist %%D (
        if "!FOUND_PATH!"=="" (
            set "FOUND_PATH=%%~D"
        )
    )
)

if not "!FOUND_PATH!"=="" (
    set "PYTHON_EXE=!FOUND_PATH!"
    echo              [ OK ]  Python found at: !FOUND_PATH!
    call :LOG "Python at: !FOUND_PATH!"
    goto :PYTHON_OK
)

:: Python not found - try to download
echo              [FAIL]  Python not found on this system.
call :LOG "Python NOT found"
echo.
if "%ONLINE%"=="true" (
    echo  Downloading Python installer...
    echo  IMPORTANT: When the installer opens you MUST check the box
    echo  that says  Add Python to PATH  before clicking Install Now.
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py_setup.exe' -UseBasicParsing" >> "%LOGFILE%" 2>&1
    if exist "%TEMP%\py_setup.exe" (
        echo  Opening installer now - follow the steps carefully.
        start /wait "" "%TEMP%\py_setup.exe"
        python --version >nul 2>&1
        if !errorlevel!==0 (
            set "PYTHON_EXE=python"
            echo  Python installed. Continuing...
            goto :PYTHON_OK
        )
    )
    echo.
    echo  Python install did not complete successfully.
    echo  Please install from: https://www.python.org/downloads/
    echo  Check the box Add Python to PATH during install.
    echo  Then run this launcher again.
) else (
    echo  No internet to download Python.
    echo  Please connect to internet and run this launcher again.
)
echo.
pause
exit /b 1

:PYTHON_OK
echo.

:: ================================================================
:: STEP 3  -  VIRTUAL ENVIRONMENT
:: ================================================================
echo  [STEP 3/7]  Setting up virtual environment...
call :LOG "Setting up venv"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo              Creating environment - first run only, please wait...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%LOGFILE%" 2>&1
    if !errorlevel! neq 0 (
        echo.
        echo  [FAIL]  Could not create virtual environment.
        echo  Try running REPAIR_AND_RECOVER.bat
        call :LOG "VENV creation FAILED"
        pause
        exit /b 1
    )
    echo              [ OK ]  Environment created.
    call :LOG "Venv created"
) else (
    echo              [ OK ]  Environment already exists.
    call :LOG "Venv exists"
)

:: Set paths to venv python and pip - no extra quotes
set "VPYTHON=%VENV_DIR%\Scripts\python.exe"
set "VPIP=%VENV_DIR%\Scripts\pip.exe"

echo.

:: ================================================================
:: STEP 4  -  INSTALL PACKAGES
:: ================================================================
echo  [STEP 4/7]  Checking required packages...
call :LOG "Checking packages"

:: Quick check if already installed
"%VPYTHON%" -c "import flask" >nul 2>&1
if %errorlevel%==0 (
    "%VPYTHON%" -c "import fitz" >nul 2>&1
    if !errorlevel!==0 goto :NEED_INSTALL
    echo              [ OK ]  All packages already installed.
    call :LOG "Packages already installed"
    goto :PACKAGES_DONE
)

:NEED_INSTALL
echo              Installing packages - takes 3 to 5 mins on first run...
echo              Please wait and do NOT close this window.
echo.
call :LOG "Installing packages"

:: Upgrade pip first
"%VPYTHON%" -m pip install --upgrade pip --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1

if "%ONLINE%"=="true" (
    echo              Downloading from internet...
    call :LOG "Online install"

    "%VPIP%" install flask --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo                flask ... OK) else (echo                flask ... retrying offline && "%VPIP%" install flask --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1)

    "%VPIP%" install flask-cors --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo                flask-cors ... OK) else (echo                flask-cors ... retrying offline && "%VPIP%" install flask-cors --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1)

    "%VPIP%" install requests --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo                requests ... OK) else (echo                requests ... retrying offline && "%VPIP%" install requests --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1)

    "%VPIP%" install Pillow --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo                Pillow ... OK) else (echo                Pillow ... retrying offline && "%VPIP%" install Pillow --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1)

    "%VPIP%" install PyMuPDF --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo                PyMuPDF ... OK) else (echo                PyMuPDF ... retrying offline && "%VPIP%" install PyMuPDF --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1)

    "%VPIP%" install anthropic --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo                anthropic ... OK) else (echo                anthropic ... retrying offline && "%VPIP%" install anthropic --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1)

    "%VPIP%" install numpy --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo                numpy ... OK) else (echo                numpy ... retrying offline && "%VPIP%" install numpy --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1)

    "%VPIP%" install python-docx --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo                python-docx ... OK) else (echo                python-docx ... retrying offline && "%VPIP%" install python-docx --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1)

    "%VPIP%" install colorama --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo                colorama ... OK) else (echo                colorama ... retrying offline && "%VPIP%" install colorama --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1)

    "%VPIP%" install psutil --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo                psutil ... OK) else (echo                psutil ... retrying offline && "%VPIP%" install psutil --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1)

    :: Save to offline cache in background
    echo.
    echo              Saving packages to offline cache for future use...
    "%VPIP%" download flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --dest="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    echo              [ OK ]  Offline cache updated.

) else (
    echo              No internet - installing from offline cache...
    call :LOG "Offline install"
    if exist "%OFFLINE_DIR%\*.whl" (
        "%VPIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --no-index --find-links="%OFFLINE_DIR%" --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    ) else (
        echo.
        echo  ================================================================
        echo   Offline mode but no cached packages found.
        echo.
        echo   Please connect to internet once and run:
        echo   DOWNLOAD_OFFLINE_PACKAGES.bat
        echo   This saves everything needed for future offline use.
        echo  ================================================================
        echo.
        call :LOG "No offline packages found"
        pause
        exit /b 1
    )
)

:: Verify install worked
"%VPYTHON%" -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ================================================================
    echo   Package installation FAILED.
    echo.
    echo   Opening log file now so you can see what went wrong.
    echo   After reading the log, run REPAIR_AND_RECOVER.bat
    echo  ================================================================
    echo.
    call :LOG "Package check FAILED"
    start notepad "%LOGFILE%"
    pause
    exit /b 1
)

echo.
echo              [ OK ]  All packages ready.
call :LOG "Packages OK"

:PACKAGES_DONE
echo.

:: ================================================================
:: STEP 5  -  CHECK FILES
:: ================================================================
echo  [STEP 5/7]  Checking application files...
call :LOG "Checking files"

set "FILES_OK=true"
if not exist "%BASEDIR%\server.py"         set "FILES_OK=false" & call :LOG "MISSING server.py"
if not exist "%BASEDIR%\static\index.html" set "FILES_OK=false" & call :LOG "MISSING static\index.html"

if "%FILES_OK%"=="false" (
    echo              [FAIL]  Critical files missing.
    echo              Re-extract the ZIP file and try again.
    pause
    exit /b 1
)

for %%D in (uploads offline_packages logs data static reports_db) do (
    if not exist "%BASEDIR%\%%D\" mkdir "%BASEDIR%\%%D" >nul 2>&1
)

echo              [ OK ]  All files present.
echo.

:: ================================================================
:: STEP 6  -  CHECK PORT
:: ================================================================
echo  [STEP 6/7]  Checking port %PORT%...
call :LOG "Checking port %PORT%"

netstat -ano 2>nul | findstr ":%PORT% " >nul 2>&1
if %errorlevel%==0 (
    echo              Port %PORT% is busy - freeing it...
    for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":%PORT% "') do (
        taskkill /PID %%P /F >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo              [ OK ]  Port freed.
    call :LOG "Port freed"
) else (
    echo              [ OK ]  Port %PORT% is available.
)
echo.

:: ================================================================
:: STEP 7  -  START SERVER
:: ================================================================
echo  [STEP 7/7]  Starting server...
call :LOG "Starting server"

if not "%ANTHROPIC_API_KEY%"=="" (
    echo              [ OK ]  API key found - live AI mode active.
) else (
    echo              [ -- ]  No API key - offline research mode.
    echo              Set your key inside the app under Settings.
)

:: Start server in a visible window so user can see it running
start "OncoCare AI Server" cmd /k "echo OncoCare AI Server - Keep This Window Open && echo. && "%VPYTHON%" "%BASEDIR%\server.py" --port %PORT%"

echo.
echo              Waiting for server to start...
call :LOG "Waiting for server"

set "SERVER_UP=false"
for /L %%i in (1,1,25) do (
    timeout /t 1 /nobreak >nul
    curl -s "http://localhost:%PORT%/api/health" >nul 2>&1
    if !errorlevel!==0 (
        set "SERVER_UP=true"
        goto :SERVER_READY
    )
    echo              Waiting... %%i of 25
)

:SERVER_READY
if "%SERVER_UP%"=="true" (
    echo              [ OK ]  Server is running.
    call :LOG "Server confirmed running"
) else (
    echo              [ -- ]  Server taking longer than usual to start.
    echo              Try opening http://localhost:%PORT% manually.
    call :LOG "Server startup timeout - may still be loading"
)

:: ================================================================
:: OPEN BROWSER
:: ================================================================
cls
echo.
echo  ================================================================
echo   OncoCare AI IS RUNNING
echo  ================================================================
echo.
echo   Open this in your browser if it does not open automatically:
echo.
echo      http://localhost:%PORT%
echo.
echo  ----------------------------------------------------------------
echo   Server window: Keep the other CMD window open. Do not close it.
echo   Mode: Online = %ONLINE%
echo   Log:  %LOGFILE%
echo  ----------------------------------------------------------------
echo.
echo  DISCLAIMER: All AI output is for research only.
echo  Not a diagnosis. Consult your oncologist before any decision.
echo.

timeout /t 2 /nobreak >nul
start "" "http://localhost:%PORT%"

echo.
echo  ================================================================
echo   CONTROLS  (type a letter and press Enter)
echo.
echo     V  =  View log in Notepad
echo     D  =  Run Diagnostics
echo     U  =  Update packages
echo     Q  =  Quit and stop server
echo  ================================================================
echo.

:MENU
set /p "CHOICE=  Your choice [V/D/U/Q]: "
if /i "!CHOICE!"=="V" start notepad "%LOGFILE%" & goto :MENU
if /i "!CHOICE!"=="D" call "%BASEDIR%\DIAGNOSTIC.bat" & goto :MENU
if /i "!CHOICE!"=="U" call "%BASEDIR%\UPDATE.bat" & goto :MENU
if /i "!CHOICE!"=="Q" goto :QUIT
echo   Please type V, D, U, or Q then press Enter.
goto :MENU

:QUIT
echo.
echo  Stopping OncoCare AI...
call :LOG "Shutdown"
taskkill /FI "WINDOWTITLE eq OncoCare AI Server*" /F >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":%PORT% "') do (
    taskkill /PID %%P /F >nul 2>&1
)
echo  Done. Goodbye.
call :LOG "Stopped."
timeout /t 2 /nobreak >nul
exit /b 0

:LOG
echo [%DATE% %TIME%] %~1 >> "%LOGFILE%"
goto :EOF
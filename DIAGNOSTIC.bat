@echo off
setlocal EnableDelayedExpansion
title OncoCare AI - DIAGNOSTIC TOOL
mode con: cols=78 lines=55
color 0E

set "BASEDIR=%~dp0"
set "BASEDIR=%BASEDIR:~0,-1%"
set "VENV_DIR=%BASEDIR%\venv"
set "LOGS_DIR=%BASEDIR%\logs"
set "PORT=5050"

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
set "REPORT=%LOGS_DIR%\diagnostic_%DATE:~-4,4%%DATE:~-7,2%%DATE:~-10,2%_%TIME:~0,2%%TIME:~3,2%.txt"
set "REPORT=%REPORT: =0%"

cls
echo.
echo  ================================================================
echo   OncoCare AI  -  FULL DIAGNOSTIC TOOL
echo  ================================================================
echo  Running full system check. This may take about 30 seconds.
echo  A report will be saved to the logs folder.
echo  ================================================================
echo.

echo OncoCare AI - Diagnostic Report > "%REPORT%"
echo Date: %DATE%  Time: %TIME% >> "%REPORT%"
echo ================================================================ >> "%REPORT%"
echo. >> "%REPORT%"

:: ---------------------------------------------------------------
:: 1. SYSTEM INFO
:: ---------------------------------------------------------------
call :SEC "1. SYSTEM INFORMATION"
for /f "skip=1 tokens=*" %%V in ('wmic os get Caption 2^>nul') do (
    if not "%%V"=="" echo    OS: %%V & echo    OS: %%V >> "%REPORT%"
)
for /f "skip=1 tokens=*" %%V in ('wmic computersystem get TotalPhysicalMemory 2^>nul') do (
    if not "%%V"=="" (
        set /a "RAM_MB=%%V / 1048576" 2>nul
        if !RAM_MB! lss 4096 (
            call :WARN "RAM: !RAM_MB! MB  WARNING - 4GB minimum recommended"
        ) else (
            call :OK "RAM: !RAM_MB! MB"
        )
    )
)
for /f "skip=1 tokens=*" %%V in ('wmic logicaldisk where "DeviceID='%BASEDIR:~0,2%'" get FreeSpace 2^>nul') do (
    if not "%%V"=="" (
        set /a "FREE_GB=%%V / 1073741824" 2>nul
        if !FREE_GB! lss 2 (
            call :FAIL "Disk free: !FREE_GB! GB  -- LOW -- need at least 2 GB free"
        ) else (
            call :OK "Disk free: !FREE_GB! GB available"
        )
    )
)

:: ---------------------------------------------------------------
:: 2. INTERNET
:: ---------------------------------------------------------------
call :SEC "2. NETWORK AND INTERNET"
ping -n 1 -w 2000 8.8.8.8 >nul 2>&1
if %errorlevel%==0 (
    call :OK "Internet connection: ONLINE"
) else (
    call :WARN "Internet connection: OFFLINE - some features unavailable"
)
ping -n 1 -w 3000 api.anthropic.com >nul 2>&1
if %errorlevel%==0 (
    call :OK "Anthropic API server: Reachable"
) else (
    call :WARN "Anthropic API server: Not reachable - offline or blocked by firewall"
)
ping -n 1 -w 3000 pypi.org >nul 2>&1
if %errorlevel%==0 (
    call :OK "PyPI package server: Reachable"
) else (
    call :WARN "PyPI: Not reachable - package installs will use offline cache"
)

:: ---------------------------------------------------------------
:: 3. PYTHON
:: ---------------------------------------------------------------
call :SEC "3. PYTHON INSTALLATION"

if exist "%BASEDIR%\python_runtime\python.exe" (
    call :OK "Local Python runtime: FOUND in python_runtime folder"
) else (
    call :WARN "Local Python runtime: Not found - will use system Python"
)

python --version >nul 2>&1
if %errorlevel%==0 (
    for /f "delims=" %%V in ('python --version 2^>^&1') do call :OK "System Python: %%V"
) else (
    py --version >nul 2>&1
    if !errorlevel!==0 (
        for /f "delims=" %%V in ('py --version 2^>^&1') do call :OK "Python launcher: %%V"
    ) else (
        call :FAIL "Python: NOT FOUND - run START_OncoCare_AI.bat to install automatically"
    )
)

if exist "%VENV_DIR%\Scripts\python.exe" (
    for /f "delims=" %%V in ('"%VENV_DIR%\Scripts\python.exe" --version 2^>^&1') do (
        call :OK "Virtual environment Python: %%V"
    )
) else (
    call :FAIL "Virtual environment: NOT CREATED - run START_OncoCare_AI.bat first"
)

:: ---------------------------------------------------------------
:: 4. PACKAGES
:: ---------------------------------------------------------------
call :SEC "4. PYTHON PACKAGES"
if exist "%VENV_DIR%\Scripts\python.exe" (
    set "VP=%VENV_DIR%\Scripts\python.exe"
    for %%M in (flask flask_cors requests PIL fitz anthropic numpy docx colorama psutil) do (
        "!VP!" -c "import %%M" >nul 2>&1
        if !errorlevel!==0 (
            call :OK "  Package %%M: installed"
        ) else (
            call :FAIL "  Package %%M: MISSING - run REPAIR_AND_RECOVER.bat option 2"
        )
    )
) else (
    call :WARN "Cannot check packages - virtual environment not set up yet"
)

:: ---------------------------------------------------------------
:: 5. APPLICATION FILES
:: ---------------------------------------------------------------
call :SEC "5. APPLICATION FILES"
for %%F in (
    "server.py"
    "static\index.html"
    "START_OncoCare_AI.bat"
    "DIAGNOSTIC.bat"
    "REPAIR_AND_RECOVER.bat"
    "DOWNLOAD_OFFLINE_PACKAGES.bat"
    "UPDATE.bat"
    "STOP_SERVER.bat"
    "data\cancer_knowledge.json"
    "modules\knowledge_engine.py"
) do (
    if exist "%BASEDIR%\%%~F" (
        for %%S in ("%BASEDIR%\%%~F") do call :OK "  %%~F  (%%~zS bytes)"
    ) else (
        call :FAIL "  %%~F  -- FILE MISSING"
    )
)

:: ---------------------------------------------------------------
:: 6. DIRECTORIES
:: ---------------------------------------------------------------
call :SEC "6. REQUIRED DIRECTORIES"
for %%D in (uploads offline_packages logs data static reports_db modules) do (
    if exist "%BASEDIR%\%%D\" (
        call :OK "  Folder %%D exists"
    ) else (
        mkdir "%BASEDIR%\%%D" >nul 2>&1
        call :WARN "  Folder %%D was missing - created it now"
    )
)

:: ---------------------------------------------------------------
:: 7. OFFLINE PACKAGES
:: ---------------------------------------------------------------
call :SEC "7. OFFLINE PACKAGE CACHE"
if exist "%BASEDIR%\offline_packages\*.whl" (
    set /a WHL=0
    for %%W in ("%BASEDIR%\offline_packages\*.whl") do set /a WHL+=1
    call :OK "  Offline packages cached: !WHL! files"
) else (
    call :WARN "  No offline packages cached."
    call :WARN "  Run DOWNLOAD_OFFLINE_PACKAGES.bat while online to enable offline use."
)

:: ---------------------------------------------------------------
:: 8. SERVER STATUS
:: ---------------------------------------------------------------
call :SEC "8. SERVER STATUS (port %PORT%)"
netstat -ano 2>nul | findstr ":%PORT% " >nul 2>&1
if %errorlevel%==0 (
    call :OK "  Server is running on port %PORT%"
    curl -s "http://localhost:%PORT%/api/health" >nul 2>&1
    if !errorlevel!==0 (
        call :OK "  Health check passed - server responding"
    ) else (
        call :WARN "  Server port is in use but not responding yet - may still be starting"
    )
) else (
    call :WARN "  Server is NOT running - start it with START_OncoCare_AI.bat"
)

:: ---------------------------------------------------------------
:: 9. API KEY
:: ---------------------------------------------------------------
call :SEC "9. API KEY"
if not "%ANTHROPIC_API_KEY%"=="" (
    call :OK "  ANTHROPIC_API_KEY is set - live AI analysis enabled"
) else (
    call :WARN "  ANTHROPIC_API_KEY not set - running in offline research mode"
    call :INFO "  To enable live AI: enter your key in Settings inside the app"
    call :INFO "  Get a free key at: https://console.anthropic.com"
)

:: ---------------------------------------------------------------
:: 10. RECENT LOG
:: ---------------------------------------------------------------
call :SEC "10. RECENT SERVER LOG"
if exist "%LOGS_DIR%\server.log" (
    echo.
    echo   Last 10 lines of server.log:
    echo   --------------------------------
    powershell -Command "Get-Content '%LOGS_DIR%\server.log' -Tail 10 2>$null | ForEach-Object { Write-Host '   ' $_ }"
) else (
    call :WARN "  No server log found yet (server has not been started)"
)

:: ---------------------------------------------------------------
:: SUMMARY
:: ---------------------------------------------------------------
echo.
echo  ================================================================
echo   DIAGNOSTIC COMPLETE
echo   Full report saved to:
echo   %REPORT%
echo  ================================================================
echo.
echo   OPTIONS:
echo     R  =  Run REPAIR_AND_RECOVER.bat
echo     L  =  Open the full report in Notepad
echo     S  =  Start OncoCare AI now
echo     X  =  Exit diagnostic
echo.

:DIAG_MENU
set /p "DC=  Choice [R/L/S/X]: "
if /i "%DC%"=="R" call "%BASEDIR%\REPAIR_AND_RECOVER.bat" & goto :DIAG_MENU
if /i "%DC%"=="L" start notepad "%REPORT%" & goto :DIAG_MENU
if /i "%DC%"=="S" call "%BASEDIR%\START_OncoCare_AI.bat" & exit /b 0
if /i "%DC%"=="X" exit /b 0
echo   Please type R, L, S, or X then press Enter.
goto :DIAG_MENU

:: ---------------------------------------------------------------
:: HELPER FUNCTIONS
:: ---------------------------------------------------------------
:SEC
echo.
echo   --- %~1 ---
echo. >> "%REPORT%"
echo --- %~1 --- >> "%REPORT%"
goto :EOF

:OK
echo   [ OK ]  %~1
echo [OK] %~1 >> "%REPORT%"
goto :EOF

:WARN
echo   [WARN]  %~1
echo [WARN] %~1 >> "%REPORT%"
goto :EOF

:FAIL
echo   [FAIL]  %~1
echo [FAIL] %~1 >> "%REPORT%"
goto :EOF

:INFO
echo          %~1
echo [INFO] %~1 >> "%REPORT%"
goto :EOF

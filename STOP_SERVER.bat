@echo off
setlocal EnableDelayedExpansion
title OncoCare AI - Stopping Server
color 0C
set "PORT=5050"

echo.
echo  ================================================================
echo   OncoCare AI  -  STOP SERVER
echo  ================================================================
echo.
echo  Stopping the OncoCare AI server on port %PORT%...
echo.

:: Method 1 - kill by window title
echo   Stopping by window title...
taskkill /FI "WINDOWTITLE eq OncoCare AI Server*" /F >nul 2>&1

:: Method 2 - kill by port
echo   Freeing port %PORT%...
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":%PORT% "') do (
    echo   Stopping process: %%P
    taskkill /PID %%P /F >nul 2>&1
)

:: Short wait then confirm
timeout /t 2 /nobreak >nul

netstat -ano 2>nul | findstr ":%PORT% " >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [ OK ]  Server stopped. Port %PORT% is now free.
) else (
    echo.
    echo   [WARN]  Port %PORT% may still be in use.
    echo   Try running REPAIR_AND_RECOVER.bat option 6 to force-free the port.
)

echo.
echo  ================================================================
echo.
timeout /t 3 /nobreak >nul

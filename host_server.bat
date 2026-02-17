@echo off
setlocal EnableDelayedExpansion
title Hyper-RMA Server Host

echo ===================================================
echo     Hyper-RMA Server Initialization
echo ===================================================

:: 1. Check/Request Admin Privileges (Required for Firewall Rule)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Requesting Administrator privileges to configure firewall...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: 2. Configure Windows Firewall
echo [1/2] Configuring Windows Firewall Rule...
netsh advfirewall firewall show rule name="Hyper-RMA-Web" >nul
if %errorlevel% neq 0 (
    netsh advfirewall firewall add rule name="Hyper-RMA-Web" dir=in action=allow protocol=TCP localport=8501 profile=any description="Allow Hyper-RMA Web Interface"
    echo [SUCCESS] Firewall rule added: TCP Port 8501 allowed.
) else (
    echo [INFO] Firewall rule already exists. Skipping.
)

:: 3. Get Local IP Address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4 Address"') do (
    set IP=%%a
)
set IP=!IP:~1!

echo.
echo ===================================================
echo     Server uses IP: !IP!
echo ===================================================
echo.
echo [INSTRUCTION]
echo Please share the following URL with your colleagues:
echo.
echo     http://!IP!:8501
echo.
echo ===================================================
echo [2/2] Starting Hyper-RMA Web Server...
echo (Close this window to stop the server)
echo.

:: 4. Run Streamlit in Server Mode
:: --server.address 0.0.0.0 listens on all interfaces
:: --server.headless true prevents opening browser on server itself (optional)
streamlit run src/main.py --server.address 0.0.0.0 --server.port 8501 --theme.base dark
pause

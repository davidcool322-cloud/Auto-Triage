@echo off
chcp 65001 >nul
title Hyper-RMA Operations Hub

REM === 設定專案根目錄 ===
set PROJECT_ROOT=%~dp0

REM === 啟動虛擬環境 ===
call "%PROJECT_ROOT%.venv\Scripts\activate.bat"

REM === 設定環境變數 ===
set PYTHONPATH=%PROJECT_ROOT%src
set PYTHONIOENCODING=utf-8

REM === 顯示啟動資訊 ===
echo ============================================
echo   Hyper-RMA Operations Hub
echo   Starting Streamlit Server...
echo ============================================
echo.
echo   Local URL:   http://localhost:8501
echo   Network URL: http://%COMPUTERNAME%:8501
echo.
echo   [Ctrl+C] to stop the server
echo ============================================
echo.

REM === 自動開啟瀏覽器 (3 秒後) ===
start /min cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8501"

REM === 啟動 Streamlit (允許網路存取) ===
streamlit run "%PROJECT_ROOT%src\main.py" --server.address 0.0.0.0 --server.port 8501 --server.headless true

pause

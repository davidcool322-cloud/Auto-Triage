@echo off
setlocal EnableDelayedExpansion

title Hyper-RMA Builder

echo ===================================================
echo    Hyper-RMA Portable Package Builder
echo ===================================================

:: 1. Check Python Environment
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

:: 2. Install PyInstaller
echo [1/3] Installing Build Dependencies...
pip install pyinstaller --upgrade
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

:: 3. Run PyInstaller
echo [2/3] Building Executable with PyInstaller...
if exist "dist\Hyper-RMA" (
    echo Cleaning previous build...
    rmdir /s /q "dist\Hyper-RMA"
)
pyinstaller --noconfirm --clean Hyper-RMA.spec
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

:: 4. Copy SAA Tools
echo [3/3] Bundling SAA Tools...
set "SAA_SOURCE=..\SAA"
set "SAA_DEST=dist\Hyper-RMA\SAA"

if exist "%SAA_SOURCE%" (
    echo Found SAA at %SAA_SOURCE%, copying...
    xcopy "%SAA_SOURCE%" "%SAA_DEST%" /E /I /Y /Q
) else (
    echo [WARNING] SAA folder not found at "%SAA_SOURCE%".
    echo Please manually copy the 'SAA' folder into 'dist\Hyper-RMA\' before distribution.
)

echo.
echo ===================================================
echo    Build Success!
echo ===================================================
echo Output Location: %CD%\dist\Hyper-RMA\Hyper-RMA.exe
echo.
echo You can zip the 'dist\Hyper-RMA' folder and share it.
echo.
pause

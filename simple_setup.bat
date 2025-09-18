@echo off
echo 🔧 簡化設置程式
echo ================

REM 刪除有問題的虛擬環境
if exist "vitallens_venv" (
    echo 🗑️ 清除舊環境...
    rmdir /s /q vitallens_venv
    timeout /t 2 /nobreak >nul
)

echo 🐍 建立新的虛擬環境...
python -m venv vitallens_venv
if errorlevel 1 (
    echo ❌ 虛擬環境建立失敗
    pause
    exit /b 1
)

echo ✅ 啟動虛擬環境...
call vitallens_venv\Scripts\activate.bat

echo 📦 升級 pip...
python -m pip install --upgrade pip

echo 🔧 應用 Python 3.13 修復...
python simple_fix.py

echo 📦 安裝基本套件...
pip install python-dotenv gradio numpy matplotlib pandas pillow opencv-python

echo 📦 安裝 VitalLens...
pip install vitallens

echo ✅ 設置完成！
echo 💡 現在可以執行: run_app.bat
echo.
pause

@echo off
echo 🩺 啟動 VitalLens 生命體徵檢測器...

REM 檢查虛擬環境是否存在
if not exist "vitallens_venv\Scripts\activate.bat" (
    echo ❌ 未找到虛擬環境！
    echo 💡 正在自動建立虛擬環境...
    python setup_venv.py
    if errorlevel 1 (
        echo ❌ 虛擬環境建立失敗
        pause
        exit /b 1
    )
)

echo ✅ 啟動虛擬環境...
call vitallens_venv\Scripts\activate.bat

echo 🚀 啟動應用程式...
python app.py

echo.
echo 🔚 應用程式已關閉
pause

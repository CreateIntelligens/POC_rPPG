@echo off
chcp 65001 > nul
echo.
echo ===================================================
echo 🩺 VitalLens 即時生命體徵檢測器 (網路攝影機版本)
echo ===================================================
echo.

REM 檢查虛擬環境是否存在
if not exist "vitallens_venv" (
    echo ❌ 虛擬環境不存在！
    echo 請先執行 setup_venv.py 建立虛擬環境
    echo.
    pause
    exit /b 1
)

REM 啟動虛擬環境
echo 📁 啟動虛擬環境...
call vitallens_venv\Scripts\activate.bat

REM 檢查 Python 是否可用
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python 無法運行！
    echo 請檢查虛擬環境是否正確安裝
    pause
    exit /b 1
)

REM 檢查必要套件
echo 🔍 檢查必要套件...
python -c "import gradio, vitallens, cv2" > nul 2>&1
if errorlevel 1 (
    echo ❌ 缺少必要套件！
    echo 正在安裝...
    pip install -r requirements.txt
)

REM 檢查攝影機
echo 📹 檢查攝影機...
python -c "import cv2; cap = cv2.VideoCapture(0); print('✅ 攝影機可用' if cap.isOpened() else '❌ 攝影機無法使用'); cap.release()" 2>nul

REM 檢查設定檔
if not exist ".env" (
    echo ⚠️  未找到 .env 檔案
    echo 💡 您可以將 config.example.py 重新命名為 .env 並填入 API Key
    echo.
)

echo.
echo 🚀 啟動 VitalLens 即時生命體徵檢測器...
echo 📡 預設網址: http://localhost:7861
echo 💡 請確保攝影機已連接且可用
echo.
echo ⚠️  注意事項:
echo    - 錄影時請保持靜止並面向攝影機
echo    - 確保光線充足且均勻
echo    - 建議錄影時間 15-30 秒
echo.

REM 執行應用程式
python webcam_app.py

REM 如果程式結束，暫停以顯示錯誤訊息
if errorlevel 1 (
    echo.
    echo ❌ 程式執行時發生錯誤
    pause
)

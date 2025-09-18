@echo off
echo 🩺 VitalLens 生命體徵檢測器 - 完整啟動程式
echo 根據官方文件要求進行系統檢查
echo ========================================================

REM 首先檢查系統環境
echo 🔍 步驟 1: 檢查系統環境...
python check_system.py
if errorlevel 1 (
    echo.
    echo ❌ 系統環境檢查失敗！
    echo 💡 請解決上述問題後重新執行
    pause
    exit /b 1
)

echo.
echo ✅ 系統環境檢查通過，繼續啟動...
echo.

REM 檢查虛擬環境
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

echo 🔍 步驟 2: 啟動虛擬環境...
call vitallens_venv\Scripts\activate.bat

echo 🔍 步驟 3: 最終檢查 VitalLens...
python -c "from vitallens import VitalLens, Method; print('✅ VitalLens 導入成功')"
if errorlevel 1 (
    echo ❌ VitalLens 導入失敗
    echo 💡 嘗試重新安裝...
    pip install --upgrade vitallens
)

echo.
echo 🚀 步驟 4: 啟動應用程式...
echo 💡 記住：根據官方文件要求
echo    - 心率: 需要至少 5 秒影片
echo    - 呼吸率: 需要至少 10 秒影片
echo    - 確保人臉清晰可見
echo.

python app.py

echo.
echo 🔚 應用程式已關閉
pause

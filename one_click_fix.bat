@echo off
echo 🚀 VitalLens Python 3.13 一鍵修復程式
echo =========================================

echo 🔍 步驟 1: 檢查虛擬環境...
if not exist "vitallens_venv\Scripts\activate.bat" (
    echo ❌ 虛擬環境不存在，請先執行 python setup_venv.py
    pause
    exit /b 1
)

echo ✅ 啟動虛擬環境...
call vitallens_venv\Scripts\activate.bat

echo 🔍 步驟 2: 檢查 Python 版本...
python -c "import sys; print(f'Python 版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); exit(0 if sys.version_info >= (3, 13) else 1)"
if errorlevel 1 (
    echo ℹ️ Python 版本 < 3.13，可能不需要修復
    echo 💡 但如果遇到 WindowsPath 錯誤，仍可嘗試修復
)

echo 🔧 步驟 3: 應用 importlib.resources 修復...
python fix_importlib_resources.py
if errorlevel 1 (
    echo ⚠️ importlib.resources 修復失敗，繼續嘗試直接修復
)

echo 🔧 步驟 4: 直接修復 VitalLens ssd.py...
python fix_vitallens_ssd.py
if errorlevel 1 (
    echo ❌ ssd.py 修復失敗
    echo 💡 您可以嘗試重新安裝 VitalLens: pip install --force-reinstall vitallens
    pause
    exit /b 1
)

echo 🧪 步驟 5: 測試修復結果...
echo 正在測試 VitalLens 導入...
python -c "from vitallens import VitalLens, Method; print('✅ VitalLens 導入成功！')"
if errorlevel 1 (
    echo ❌ 測試失敗，修復未成功
    echo 💡 可嘗試還原並重新安裝: python fix_vitallens_ssd.py --restore
    pause
    exit /b 1
)

echo.
echo 🎉 修復完成！
echo ✅ VitalLens 現在應該可以正常工作
echo 💡 您現在可以執行: run_app.bat 來啟動應用程式
echo.
pause

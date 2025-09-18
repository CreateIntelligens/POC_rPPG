@echo off
echo 🔧 VitalLens 故障排除工具
echo ========================

echo 請選擇操作:
echo 1. 測試 VitalLens 導入
echo 2. 還原 ssd.py 備份檔案
echo 3. 重新安裝 VitalLens
echo 4. 完全清理並重新安裝
echo 5. 顯示錯誤診斷資訊
echo 0. 退出

set /p choice="請輸入選項 (0-5): "

if "%choice%"=="1" goto test
if "%choice%"=="2" goto restore
if "%choice%"=="3" goto reinstall
if "%choice%"=="4" goto clean_install
if "%choice%"=="5" goto diagnose
if "%choice%"=="0" goto end

echo 無效選項，請重新選擇
pause
goto start

:test
echo 🧪 測試 VitalLens 導入...
call vitallens_venv\Scripts\activate.bat
python -c "from vitallens import VitalLens, Method; print('✅ VitalLens 導入成功')"
if errorlevel 1 (
    echo ❌ 導入失敗
    python -c "import traceback; exec('try:\n from vitallens import VitalLens\nexcept Exception as e:\n traceback.print_exc()')"
)
pause
goto end

:restore
echo 🔄 還原 ssd.py 備份檔案...
call vitallens_venv\Scripts\activate.bat
python fix_vitallens_ssd.py --restore
pause
goto end

:reinstall
echo 📦 重新安裝 VitalLens...
call vitallens_venv\Scripts\activate.bat
echo 正在卸載舊版本...
pip uninstall vitallens -y
echo 正在重新安裝...
pip install vitallens
echo 重新安裝完成！
pause
goto end

:clean_install
echo 🧹 完全清理並重新安裝...
echo 警告: 這將刪除整個虛擬環境！
set /p confirm="確定要繼續嗎? (y/N): "
if /i not "%confirm%"=="y" goto end

echo 刪除虛擬環境...
rmdir /s /q vitallens_venv
echo 重新建立虛擬環境...
python setup_venv.py
echo 完全重新安裝完成！
pause
goto end

:diagnose
echo 🔍 錯誤診斷資訊...
call vitallens_venv\Scripts\activate.bat

echo Python 版本:
python --version

echo VitalLens 版本:
python -c "import vitallens; print(vitallens.__version__)" 2>nul || echo "無法獲取版本"

echo 相關套件版本:
python -c "import importlib; print('importlib:', importlib.__version__ if hasattr(importlib, '__version__') else 'built-in')"
python -c "import sys; print('Python:', sys.version)"

echo 檢查 ssd.py 檔案:
python -c "import os; ssd_path = os.path.join('vitallens_venv', 'Lib', 'site-packages', 'vitallens', 'ssd.py'); print('ssd.py 存在:', os.path.exists(ssd_path)); print('備份存在:', os.path.exists(ssd_path + '.backup'))"

echo 嘗試導入 VitalLens:
python -c "exec('try:\n from vitallens import VitalLens, Method\n print(\"✅ 導入成功\")\nexcept Exception as e:\n print(\"❌ 導入失敗:\", str(e))\n import traceback\n traceback.print_exc()')"

pause
goto end

:end
echo 故障排除完成

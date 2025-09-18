@echo off
echo 🔍 Python 安裝檢查工具
echo =====================

echo 檢查系統中的 Python 安裝...
echo.

echo 🔸 檢查 Python Launcher:
py --list
echo.

echo 🔸 檢查常見的 Python 命令:
echo.

echo python --version:
python --version 2>&1

echo python3 --version:
python3 --version 2>&1

echo py --version:
py --version 2>&1

echo py -3.9 --version:
py -3.9 --version 2>&1

echo py -3.10 --version:
py -3.10 --version 2>&1

echo py -3.11 --version:
py -3.11 --version 2>&1

echo py -3.12 --version:
py -3.12 --version 2>&1

echo.
echo 🔸 VitalLens 兼容性建議:
echo ✅ Python 3.9-3.12: 完美兼容
echo ⚠️ Python 3.13+: 可能有問題
echo ❌ Python 3.8-: 不支援
echo.

echo 💡 如果沒有 Python 3.9，執行: install_python39.bat
pause

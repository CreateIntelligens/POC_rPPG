@echo off
echo 🔧 快速修復 Python 3.13 兼容性問題...

REM 刪除現有的虛擬環境（如果存在問題）
if exist "vitallens_venv" (
    echo 🗑️ 移除現有虛擬環境...
    rmdir /s /q vitallens_venv
)

echo 🐍 重新建立虛擬環境...
python -m venv vitallens_venv

echo ✅ 啟動虛擬環境...
call vitallens_venv\Scripts\activate.bat

echo 📦 升級 pip...
python -m pip install --upgrade pip

echo 🔧 應用 Python 3.13 修復...
python fix_python313.py

echo 📦 安裝套件...
pip install -r requirements.txt

echo ✅ 修復完成！現在可以啟動應用程式了
echo 💡 請執行: run_app.bat

pause

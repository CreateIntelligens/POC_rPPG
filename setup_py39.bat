@echo off
echo 🐍 Python 3.9 虛擬環境快速設置
echo ===============================

REM 檢查是否有 Python 3.9
echo 🔍 檢查 Python 3.9...

REM 嘗試不同的 Python 3.9 命令
python3.9 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python3.9
    goto found_python
)

py -3.9 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py -3.9
    goto found_python
)

python39 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python39
    goto found_python
)

REM 檢查預設 python 是否為 3.9
python --version 2>&1 | findstr "Python 3.9" >nul
if %errorlevel%==0 (
    set PYTHON_CMD=python
    goto found_python
)

REM 未找到 Python 3.9
echo ❌ 未找到 Python 3.9 安裝
echo.
echo 📥 請安裝 Python 3.9:
echo 1. 訪問: https://www.python.org/downloads/release/python-3912/
echo 2. 下載 Windows installer (64-bit)
echo 3. 安裝時勾選 'Add Python to PATH'
echo 4. 或使用 winget: winget install Python.Python.3.9
echo.
pause
exit /b 1

:found_python
echo ✅ 找到 Python 3.9: %PYTHON_CMD%
%PYTHON_CMD% --version

REM 建立虛擬環境
set VENV_NAME=vitallens_py39_venv

if exist "%VENV_NAME%" (
    echo ⚠️ 虛擬環境已存在，是否刪除重建?
    set /p confirm="輸入 y 確認，其他鍵跳過: "
    if /i "%confirm%"=="y" (
        echo 🗑️ 刪除現有環境...
        rmdir /s /q "%VENV_NAME%"
    ) else (
        echo ℹ️ 使用現有環境
        goto install_packages
    )
)

echo 📦 建立 Python 3.9 虛擬環境...
%PYTHON_CMD% -m venv %VENV_NAME%
if %errorlevel% neq 0 (
    echo ❌ 虛擬環境建立失敗
    pause
    exit /b 1
)

:install_packages
echo ✅ 啟動虛擬環境...
call %VENV_NAME%\Scripts\activate.bat

echo 🔄 升級 pip...
python -m pip install --upgrade pip

echo 📥 安裝 VitalLens 相關套件...
pip install python-dotenv
pip install gradio
pip install numpy
pip install opencv-python
pip install matplotlib
pip install pandas
pip install pillow
pip install vitallens

if %errorlevel% neq 0 (
    echo ❌ 套件安裝失敗
    pause
    exit /b 1
)

echo 🧪 測試 VitalLens...
python -c "from vitallens import VitalLens, Method; print('✅ VitalLens 導入成功'); vl = VitalLens(method=Method.POS); print('✅ VitalLens 實例建立成功')"
if %errorlevel% neq 0 (
    echo ❌ VitalLens 測試失敗
    pause
    exit /b 1
)

echo.
echo 🎉 Python 3.9 環境設置完成！
echo ===============================
echo 📋 使用方式:
echo 1. 啟動環境: %VENV_NAME%\Scripts\activate.bat
echo 2. 執行應用: python app.py
echo 3. 或使用: run_app_py39.bat (如果存在)
echo.

REM 建立啟動腳本
echo 📝 建立專用啟動腳本...
echo @echo off > run_app_py39.bat
echo echo 🩺 啟動 VitalLens (Python 3.9 環境) >> run_app_py39.bat
echo echo ===================================== >> run_app_py39.bat
echo call %VENV_NAME%\Scripts\activate.bat >> run_app_py39.bat
echo python app.py >> run_app_py39.bat
echo pause >> run_app_py39.bat

echo ✅ 建立啟動腳本: run_app_py39.bat
echo.
echo 💡 現在您可以執行 run_app_py39.bat 來啟動應用程式
pause

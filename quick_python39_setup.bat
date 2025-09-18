@echo off
echo 🚀 VitalLens Python 3.9 快速設置
echo ==============================

echo 🔍 步驟 1: 檢查 Python 3.9...
py -3.9 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.9 未安裝
    echo.
    echo 💡 自動安裝選項:
    echo 1. winget install Python.Python.3.9
    echo 2. 或執行: install_python39.bat 獲得完整安裝指引
    echo.
    echo 🏪 嘗試使用 Microsoft Store 安裝...
    set PYLAUNCHER_ALLOW_INSTALL=1
    echo 如果彈出 Microsoft Store，請點擊安裝 Python 3.9
    py -3.9 --version
    echo.
    echo 💡 安裝完成後請重新執行此腳本
    pause
    exit /b 1
)

echo ✅ Python 3.9 已安裝
py -3.9 --version

echo.
echo 🔍 步驟 2: 建立虛擬環境...
if exist "venv_py39" (
    echo ⚠️ 虛擬環境已存在，是否重新建立?
    set /p confirm="輸入 y 重建，其他鍵繼續: "
    if /i "%confirm%"=="y" (
        rmdir /s /q "venv_py39"
    ) else (
        goto activate_venv
    )
)

py -3.9 -m venv venv_py39
if %errorlevel% neq 0 (
    echo ❌ 虛擬環境建立失敗
    pause
    exit /b 1
)

:activate_venv
echo ✅ 啟動虛擬環境...
call venv_py39\Scripts\activate.bat

echo.
echo 🔍 步驟 3: 安裝套件...
python -m pip install --upgrade pip

REM 建立 imghdr 兼容模組
echo 🔧 建立 imghdr 兼容模組...
python -c "
import os, site
sp = site.getsitepackages()[0]
with open(os.path.join(sp, 'imghdr.py'), 'w') as f:
    f.write('# imghdr compatibility\ndef what(file, h=None):\n    if hasattr(file, \"read\"):\n        header = file.read(32)\n        file.seek(0)\n    elif isinstance(file, str):\n        try:\n            with open(file, \"rb\") as f2:\n                header = f2.read(32)\n        except:\n            return None\n    else:\n        header = file if isinstance(file, bytes) else b\"\"\n    if header.startswith(b\"\\xff\\xd8\\xff\"): return \"jpeg\"\n    elif header.startswith(b\"\\x89PNG\\r\\n\\x1a\\n\"): return \"png\"\n    elif header.startswith(b\"GIF87a\") or header.startswith(b\"GIF89a\"): return \"gif\"\n    return None\ntest_jpeg = lambda h, f: h.startswith(b\"\\xff\\xd8\\xff\")\ntest_png = lambda h, f: h.startswith(b\"\\x89PNG\\r\\n\\x1a\\n\")\ntest_gif = lambda h, f: h.startswith(b\"GIF87a\") or h.startswith(b\"GIF89a\")\ntests = [(test_jpeg, \"jpeg\"), (test_png, \"png\"), (test_gif, \"gif\")]')
print('✅ imghdr 模組已建立')
"

echo 📦 安裝套件...
pip install python-dotenv gradio numpy opencv-python matplotlib pandas pillow vitallens

echo.
echo 🔍 步驟 4: 測試 VitalLens...
python -c "from vitallens import VitalLens, Method; print('✅ VitalLens 正常'); vl = VitalLens(method=Method.POS); print('✅ 測試通過')"
if %errorlevel% neq 0 (
    echo ❌ VitalLens 測試失敗
    echo 💡 嘗試手動修復或重新安裝
    pause
    exit /b 1
)

echo.
echo 🎉 設置完成！
echo =============
echo 📝 建立啟動腳本...

echo @echo off > start_vitallens.bat
echo echo 🩺 VitalLens (Python 3.9) >> start_vitallens.bat
echo call venv_py39\Scripts\activate.bat >> start_vitallens.bat
echo python app.py >> start_vitallens.bat
echo pause >> start_vitallens.bat

echo ✅ 已建立: start_vitallens.bat
echo.
echo 🚀 使用方式:
echo   雙擊: start_vitallens.bat
echo   或手動: venv_py39\Scripts\activate.bat 然後 python app.py
echo.
pause

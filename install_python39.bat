@echo off
echo 🐍 Python 3.9 安裝助手
echo ====================

echo 🔍 檢查 Python 3.9 是否已安裝...
py -3.9 --version >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Python 3.9 已安裝
    py -3.9 --version
    goto create_venv
)

echo ❌ Python 3.9 未安裝

echo.
echo 📥 Python 3.9 安裝選項：
echo 1. 使用 winget 自動安裝（推薦）
echo 2. 使用 Microsoft Store
echo 3. 手動下載安裝
echo 0. 退出

set /p choice="請選擇安裝方式 (0-3): "

if "%choice%"=="1" goto winget_install
if "%choice%"=="2" goto store_install  
if "%choice%"=="3" goto manual_install
if "%choice%"=="0" goto end

echo 無效選項
pause
goto end

:winget_install
echo 🔄 使用 winget 安裝 Python 3.9...
echo 正在檢查 winget...
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ winget 不可用，請嘗試其他安裝方式
    goto store_install
)

echo 正在安裝 Python 3.9...
winget install Python.Python.3.9
if %errorlevel%==0 (
    echo ✅ Python 3.9 安裝完成
    echo 🔄 重新載入環境變數...
    refreshenv
    goto verify_install
) else (
    echo ❌ winget 安裝失敗，嘗試其他方式
    goto store_install
)

:store_install
echo 🏪 使用 Microsoft Store 安裝...
echo 設定環境變數以允許自動安裝...
set PYLAUNCHER_ALLOW_INSTALL=1
echo 嘗試觸發 Microsoft Store 安裝...
py -3.9 --version
echo.
echo 💡 如果上述命令開啟了 Microsoft Store：
echo    1. 點擊「安裝」按鈕
echo    2. 等待安裝完成
echo    3. 重新執行此腳本
echo.
echo 💡 或者手動開啟 Microsoft Store 搜尋「Python 3.9」
goto manual_install

:manual_install
echo 🌐 手動安裝指引：
echo.
echo 1. 開啟瀏覽器訪問：
echo    https://www.python.org/downloads/release/python-3912/
echo.
echo 2. 下載：Windows installer (64-bit)
echo    檔名通常是：python-3.9.12-amd64.exe
echo.
echo 3. 執行安裝程式時：
echo    ✅ 勾選「Add Python 3.9 to PATH」
echo    ✅ 選擇「Install Now」
echo.
echo 4. 安裝完成後重新執行此腳本
echo.
pause
goto end

:verify_install
echo 🔍 驗證 Python 3.9 安裝...
timeout /t 3 /nobreak >nul
py -3.9 --version
if %errorlevel%==0 (
    echo ✅ Python 3.9 安裝成功！
    goto create_venv
) else (
    echo ❌ Python 3.9 仍不可用
    echo 💡 可能需要：
    echo    1. 重新啟動命令提示字元
    echo    2. 重新啟動電腦
    echo    3. 檢查 PATH 環境變數
    pause
    goto end
)

:create_venv
echo.
echo 🏗️ 建立 Python 3.9 虛擬環境...
if exist "vitallens_py39_venv" (
    echo ⚠️ 虛擬環境已存在，是否重新建立？
    set /p confirm="輸入 y 確認，其他鍵跳過: "
    if /i "%confirm%"=="y" (
        echo 🗑️ 刪除現有環境...
        rmdir /s /q "vitallens_py39_venv"
    ) else (
        goto install_packages
    )
)

echo 📦 建立虛擬環境...
py -3.9 -m venv vitallens_py39_venv
if %errorlevel% neq 0 (
    echo ❌ 虛擬環境建立失敗
    pause
    goto end
)

:install_packages
echo ✅ 啟動虛擬環境...
call vitallens_py39_venv\Scripts\activate.bat

echo 🔄 升級 pip...
python -m pip install --upgrade pip

echo 📥 安裝 imghdr 相容套件...
REM 先安裝相容套件
pip install typing-extensions

echo 📥 安裝 VitalLens 和相關套件...
pip install python-dotenv
pip install gradio
pip install numpy
pip install opencv-python
pip install matplotlib
pip install pandas
pip install pillow

REM 在安裝 VitalLens 前建立 imghdr 相容模組
echo 🔧 建立 imghdr 相容模組...
python -c "
import os
import site
site_packages = site.getsitepackages()[0]
imghdr_path = os.path.join(site_packages, 'imghdr.py')

imghdr_content = '''\"\"\"
imghdr module compatibility for newer Python versions
\"\"\"

def what(file, h=None):
    \"\"\"Detect format of image\"\"\"
    if hasattr(file, 'read'):
        header = file.read(32)
        file.seek(0)
    elif isinstance(file, str):
        try:
            with open(file, 'rb') as f:
                header = f.read(32)
        except:
            return None
    else:
        header = file if isinstance(file, bytes) else b''
    
    if header.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        return 'gif'
    elif header.startswith(b'RIFF') and b'WEBP' in header[:12]:
        return 'webp'
    elif header.startswith(b'BM'):
        return 'bmp'
    
    return None

# Compatibility functions
test_jpeg = lambda h, f: h.startswith(b'\xff\xd8\xff')
test_png = lambda h, f: h.startswith(b'\x89PNG\r\n\x1a\n')
test_gif = lambda h, f: h.startswith(b'GIF87a') or h.startswith(b'GIF89a')

tests = [
    (test_jpeg, 'jpeg'),
    (test_png, 'png'), 
    (test_gif, 'gif'),
]
'''

with open(imghdr_path, 'w', encoding='utf-8') as f:
    f.write(imghdr_content)
print('✅ imghdr 相容模組已建立')
"

echo 📥 現在安裝 VitalLens...
pip install vitallens

echo 🧪 測試 VitalLens...
python -c "from vitallens import VitalLens, Method; print('✅ VitalLens 導入成功'); vl = VitalLens(method=Method.POS); print('✅ VitalLens 實例建立成功')"
if %errorlevel% neq 0 (
    echo ❌ VitalLens 測試失敗
    echo 💡 可能需要額外的修復步驟
    pause
    goto end
)

echo.
echo 🎉 Python 3.9 環境設置完成！
echo ===============================
echo 📝 建立專用啟動腳本...

echo @echo off > run_vitallens_py39.bat
echo echo 🩺 VitalLens Python 3.9 環境 >> run_vitallens_py39.bat
echo echo ========================== >> run_vitallens_py39.bat
echo call vitallens_py39_venv\Scripts\activate.bat >> run_vitallens_py39.bat
echo python app.py >> run_vitallens_py39.bat
echo pause >> run_vitallens_py39.bat

echo ✅ 建立啟動腳本: run_vitallens_py39.bat
echo.
echo 📋 使用方式：
echo 1. 執行應用程式: run_vitallens_py39.bat
echo 2. 手動啟動環境: vitallens_py39_venv\Scripts\activate.bat
echo 3. 然後執行: python app.py
echo.
echo 💡 現在您可以使用 Python 3.9 環境運行 VitalLens 了！

:end
pause

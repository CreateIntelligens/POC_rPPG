#!/usr/bin/env python
"""
VitalLens Gradio 應用程式虛擬環境設置腳本
"""

import subprocess
import sys
import os
import platform

def run_command(command, description):
    """執行命令並顯示進度"""
    print(f"📋 {description}...")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), check=True, capture_output=True, text=True)
        print(f"✅ {description}完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description}失敗: {e}")
        if e.stdout:
            print(f"輸出: {e.stdout}")
        if e.stderr:
            print(f"錯誤: {e.stderr}")
        return False

def create_venv():
    """建立虛擬環境"""
    venv_name = "vitallens_venv"
    
    print(f"🐍 建立虛擬環境: {venv_name}")
    
    if os.path.exists(venv_name):
        print(f"⚠️ 虛擬環境 {venv_name} 已存在")
        response = input("是否要刪除並重新建立? (y/N): ").lower()
        if response == 'y':
            import shutil
            shutil.rmtree(venv_name)
            print(f"🗑️ 已刪除舊的虛擬環境")
        else:
            print("ℹ️ 使用現有虛擬環境")
            return venv_name
    
    # 建立虛擬環境
    if not run_command(f"{sys.executable} -m venv {venv_name}", "建立虛擬環境"):
        return None
    
    return venv_name

def install_packages(venv_name):
    """在虛擬環境中安裝套件"""
    system = platform.system()
    
    if system == "Windows":
        pip_path = os.path.join(venv_name, "Scripts", "pip")
        python_path = os.path.join(venv_name, "Scripts", "python")
    else:
        pip_path = os.path.join(venv_name, "bin", "pip")
        python_path = os.path.join(venv_name, "bin", "python")
    
    # 升級 pip
    if not run_command(f"{python_path} -m pip install --upgrade pip", "升級 pip"):
        return False
    
    # 安裝 requirements
    if not run_command(f"{pip_path} install -r requirements.txt", "安裝必要套件"):
        return False
    
    # Python 3.13+ 兼容性修復
    if sys.version_info >= (3, 13):
        print("🔧 檢測到 Python 3.13+，正在應用兼容性修復...")
        if not run_command(f"{python_path} fix_python313.py", "應用 Python 3.13 兼容性修復"):
            print("⚠️ 兼容性修復失敗，但將繼續安裝")
    
    return True

def create_run_scripts(venv_name):
    """建立執行腳本"""
    system = platform.system()
    
    if system == "Windows":
        # Windows 批次檔
        script_content = f"""@echo off
echo 🩺 啟動 VitalLens 生命體徵檢測器...
call {venv_name}\\Scripts\\activate.bat
python app.py
pause
"""
        with open("run_app.bat", "w", encoding="utf-8") as f:
            f.write(script_content)
        
        print("✅ 已建立 Windows 執行腳本: run_app.bat")
        
    else:
        # Unix/Linux/macOS shell 腳本
        script_content = f"""#!/bin/bash
echo "🩺 啟動 VitalLens 生命體徵檢測器..."
source {venv_name}/bin/activate
python app.py
"""
        with open("run_app.sh", "w", encoding="utf-8") as f:
            f.write(script_content)
        
        # 設定執行權限
        os.chmod("run_app.sh", 0o755)
        
        print("✅ 已建立 Unix 執行腳本: run_app.sh")

def create_activation_guide(venv_name):
    """建立虛擬環境啟動指南"""
    system = platform.system()
    
    guide_content = f"""# VitalLens 虛擬環境使用指南

## 🐍 虛擬環境資訊
- 虛擬環境名稱: {venv_name}
- Python 版本: {sys.version.split()[0]}
- 作業系統: {system}

## 🚀 啟動方式

### 方法一：使用執行腳本（推薦）
"""
    
    if system == "Windows":
        guide_content += """
**Windows:**
```batch
# 雙擊執行或在命令提示字元中執行
run_app.bat
```
"""
    else:
        guide_content += """
**Unix/Linux/macOS:**
```bash
# 在終端機中執行
./run_app.sh
```
"""
    
    guide_content += f"""
### 方法二：手動啟動
"""
    
    if system == "Windows":
        guide_content += f"""
**Windows:**
```batch
# 1. 啟動虛擬環境
{venv_name}\\Scripts\\activate.bat

# 2. 執行應用程式
python app.py

# 3. 關閉虛擬環境（可選）
deactivate
```
"""
    else:
        guide_content += f"""
**Unix/Linux/macOS:**
```bash
# 1. 啟動虛擬環境
source {venv_name}/bin/activate

# 2. 執行應用程式
python app.py

# 3. 關閉虛擬環境（可選）
deactivate
```
"""
    
    guide_content += """
## 📦 套件管理

### 安裝新套件
```bash
# 啟動虛擬環境後
pip install package_name
```

### 查看已安裝套件
```bash
pip list
```

### 更新套件
```bash
pip install --upgrade package_name
```

## 🔧 故障排除

### 問題：找不到模組
- 確認已啟動虛擬環境
- 檢查套件是否正確安裝

### 問題：權限錯誤
- 確認有足夠的檔案權限
- 在 Windows 上可能需要以系統管理員身分執行

### 問題：埠號已被使用
- 修改 config.py 中的 SERVER_PORT
- 或關閉佔用埠號的程式

## 📚 相關文件
- [Python venv 官方文件](https://docs.python.org/3/library/venv.html)
- [VitalLens API 文件](https://github.com/Rouast-Labs/vitallens-python)
- [Gradio 文件](https://gradio.app/docs/)
"""
    
    with open("VENV_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide_content)
    
    print("✅ 已建立虛擬環境使用指南: VENV_GUIDE.md")

def main():
    """主程式"""
    print("🚀 VitalLens 虛擬環境設置程式")
    print("=" * 50)
    
    # 檢查 Python 版本
    if sys.version_info < (3, 7):
        print("❌ 需要 Python 3.7 或更高版本")
        sys.exit(1)
    
    print(f"✅ Python 版本: {sys.version.split()[0]}")
    
    # 建立虛擬環境
    venv_name = create_venv()
    if not venv_name:
        print("❌ 虛擬環境建立失敗")
        sys.exit(1)
    
    # 安裝套件
    if not install_packages(venv_name):
        print("❌ 套件安裝失敗")
        sys.exit(1)
    
    # 建立執行腳本
    create_run_scripts(venv_name)
    
    # 建立使用指南
    create_activation_guide(venv_name)
    
    print("\n🎉 虛擬環境設置完成！")
    print("📋 接下來您可以:")
    
    system = platform.system()
    if system == "Windows":
        print("   1. 雙擊 run_app.bat 啟動應用程式")
        print("   2. 或手動執行: vitallens_venv\\Scripts\\activate.bat 然後 python app.py")
    else:
        print("   1. 執行 ./run_app.sh 啟動應用程式")
        print("   2. 或手動執行: source vitallens_venv/bin/activate 然後 python app.py")
    
    print("   3. 查看 VENV_GUIDE.md 了解詳細使用方式")

if __name__ == "__main__":
    main()

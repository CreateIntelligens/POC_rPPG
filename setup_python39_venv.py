#!/usr/bin/env python
"""
建立 Python 3.9 虛擬環境用於 VitalLens
根據官方文件建議使用 Python 3.9-3.12
"""

import subprocess
import sys
import os
import platform
import shutil
from pathlib import Path

def find_python39():
    """尋找可用的 Python 3.9 安裝"""
    print("🔍 尋找 Python 3.9 安裝...")
    
    # 常見的 Python 3.9 命令
    python_commands = [
        'python3.9',
        'python39',
        'py -3.9',  # Windows Python Launcher
        'python',
    ]
    
    for cmd in python_commands:
        try:
            # 檢查版本
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.strip()
                print(f"   找到: {cmd} -> {version_line}")
                
                # 檢查是否為 Python 3.9.x
                if 'Python 3.9.' in version_line:
                    print(f"✅ 找到 Python 3.9: {cmd}")
                    return cmd
                elif 'Python 3.1' in version_line and cmd in ['python', 'py']:
                    # 如果是 python 或 py 命令，檢查具體版本
                    version_result = subprocess.run([cmd, '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'], 
                                                  capture_output=True, text=True, timeout=5)
                    if version_result.returncode == 0:
                        version = version_result.stdout.strip()
                        if version.startswith('3.9'):
                            print(f"✅ 找到 Python 3.9: {cmd}")
                            return cmd
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            continue
    
    print("❌ 未找到 Python 3.9 安裝")
    return None

def download_python39_info():
    """提供 Python 3.9 下載資訊"""
    print("\n📥 Python 3.9 下載指南:")
    print("=" * 40)
    
    system = platform.system()
    
    if system == "Windows":
        print("🪟 Windows:")
        print("1. 訪問: https://www.python.org/downloads/release/python-3912/")
        print("2. 下載: Windows installer (64-bit)")
        print("3. 安裝時勾選 'Add Python to PATH'")
        print("4. 或使用 winget: winget install Python.Python.3.9")
        
    elif system == "Darwin":  # macOS
        print("🍎 macOS:")
        print("1. 使用 Homebrew: brew install python@3.9")
        print("2. 或訪問: https://www.python.org/downloads/release/python-3912/")
        print("3. 或使用 pyenv: pyenv install 3.9.12")
        
    elif system == "Linux":
        print("🐧 Linux:")
        print("Ubuntu/Debian:")
        print("  sudo apt update")
        print("  sudo apt install python3.9 python3.9-venv python3.9-dev")
        print("CentOS/RHEL:")
        print("  sudo yum install python39 python39-devel")
        print("或使用 pyenv:")
        print("  pyenv install 3.9.12")
    
    print("\n💡 安裝後重新執行此腳本")

def create_python39_venv(python_cmd):
    """建立 Python 3.9 虛擬環境"""
    venv_name = "vitallens_py39_venv"
    
    print(f"\n🐍 建立 Python 3.9 虛擬環境: {venv_name}")
    
    # 如果已存在，詢問是否刪除
    if os.path.exists(venv_name):
        response = input(f"⚠️ 虛擬環境 {venv_name} 已存在，是否刪除並重新建立? (y/N): ").lower()
        if response == 'y':
            print("🗑️ 刪除現有虛擬環境...")
            shutil.rmtree(venv_name)
        else:
            print("ℹ️ 使用現有虛擬環境")
            return venv_name
    
    # 建立虛擬環境
    try:
        print(f"📦 正在建立虛擬環境...")
        subprocess.run([python_cmd, '-m', 'venv', venv_name], check=True)
        print(f"✅ 虛擬環境建立成功: {venv_name}")
        return venv_name
    except subprocess.CalledProcessError as e:
        print(f"❌ 建立虛擬環境失敗: {e}")
        return None

def install_packages(venv_name):
    """在 Python 3.9 虛擬環境中安裝套件"""
    print(f"\n📦 在 Python 3.9 環境中安裝套件...")
    
    system = platform.system()
    if system == "Windows":
        pip_path = os.path.join(venv_name, "Scripts", "pip")
        python_path = os.path.join(venv_name, "Scripts", "python")
    else:
        pip_path = os.path.join(venv_name, "bin", "pip")
        python_path = os.path.join(venv_name, "bin", "python")
    
    try:
        # 升級 pip
        print("🔄 升級 pip...")
        subprocess.run([python_path, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        
        # 安裝套件
        packages = [
            'python-dotenv',
            'gradio',
            'numpy',
            'opencv-python',
            'matplotlib',
            'pandas',
            'pillow',
            'vitallens'
        ]
        
        for package in packages:
            print(f"📥 安裝 {package}...")
            subprocess.run([pip_path, 'install', package], check=True)
        
        print("✅ 所有套件安裝完成!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 套件安裝失敗: {e}")
        return False

def create_run_scripts(venv_name):
    """建立 Python 3.9 環境的啟動腳本"""
    print(f"\n📝 建立啟動腳本...")
    
    system = platform.system()
    
    if system == "Windows":
        # Windows 批次檔
        script_content = f"""@echo off
echo 🩺 啟動 VitalLens (Python 3.9 環境)
echo =====================================

call {venv_name}\\Scripts\\activate.bat
python app.py

echo.
echo 🔚 應用程式已關閉
pause
"""
        script_name = "run_app_py39.bat"
        
    else:
        # Unix shell 腳本
        script_content = f"""#!/bin/bash
echo "🩺 啟動 VitalLens (Python 3.9 環境)"
echo "====================================="

source {venv_name}/bin/activate
python app.py

echo "🔚 應用程式已關閉"
"""
        script_name = "run_app_py39.sh"
    
    try:
        with open(script_name, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        if system != "Windows":
            os.chmod(script_name, 0o755)
        
        print(f"✅ 建立啟動腳本: {script_name}")
        return script_name
        
    except Exception as e:
        print(f"❌ 建立啟動腳本失敗: {e}")
        return None

def test_vitallens(venv_name):
    """測試 VitalLens 是否正常工作"""
    print(f"\n🧪 測試 VitalLens...")
    
    system = platform.system()
    if system == "Windows":
        python_path = os.path.join(venv_name, "Scripts", "python")
    else:
        python_path = os.path.join(venv_name, "bin", "python")
    
    try:
        # 測試導入
        test_script = """
try:
    from vitallens import VitalLens, Method
    print("✅ VitalLens 導入成功")
    
    # 測試建立實例（使用免費方法）
    vl = VitalLens(method=Method.POS)
    print("✅ VitalLens 實例建立成功")
    print("🎉 Python 3.9 環境設置完成！")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
"""
        
        result = subprocess.run([python_path, '-c', test_script], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ 測試失敗:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")
        return False

def main():
    """主程式"""
    print("🐍 VitalLens Python 3.9 虛擬環境設置程式")
    print("根據官方文件建議使用 Python 3.9 以獲得最佳兼容性")
    print("=" * 60)
    
    # 檢查當前 Python 版本
    current_version = sys.version_info
    print(f"當前 Python 版本: {current_version.major}.{current_version.minor}.{current_version.micro}")
    
    # 尋找 Python 3.9
    python39_cmd = find_python39()
    
    if not python39_cmd:
        download_python39_info()
        return False
    
    # 建立虛擬環境
    venv_name = create_python39_venv(python39_cmd)
    if not venv_name:
        return False
    
    # 安裝套件
    if not install_packages(venv_name):
        return False
    
    # 建立啟動腳本
    script_name = create_run_scripts(venv_name)
    if not script_name:
        return False
    
    # 測試 VitalLens
    if not test_vitallens(venv_name):
        print("⚠️ VitalLens 測試失敗，但環境已建立")
        print("💡 您可以手動檢查問題")
    
    # 總結
    print("\n" + "=" * 60)
    print("🎉 Python 3.9 環境設置完成！")
    print("=" * 60)
    
    print(f"\n📋 使用說明:")
    print(f"1. 啟動應用程式: {script_name}")
    print(f"2. 手動啟動虛擬環境:")
    
    if platform.system() == "Windows":
        print(f"   {venv_name}\\Scripts\\activate.bat")
    else:
        print(f"   source {venv_name}/bin/activate")
    
    print(f"3. 虛擬環境位置: {os.path.abspath(venv_name)}")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n❌ 設置失敗")
        input("按 Enter 鍵結束...")
        sys.exit(1)
    else:
        print("\n💡 現在您可以使用 Python 3.9 環境來運行 VitalLens 了！")
        input("按 Enter 鍵結束...")
        sys.exit(0)

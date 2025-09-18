#!/usr/bin/env python
"""
直接修復 VitalLens ssd.py 檔案中的 importlib.resources 問題
"""

import os
import sys
from pathlib import Path
import re

def fix_ssd_file():
    """修復 vitallens/ssd.py 檔案"""
    
    # 找到 ssd.py 檔案
    venv_path = Path("vitallens_venv")
    if os.name == 'nt':
        site_packages = venv_path / "Lib" / "site-packages"
    else:
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = venv_path / "lib" / f"python{python_version}" / "site-packages"
    
    ssd_file = site_packages / "vitallens" / "ssd.py"
    
    if not ssd_file.exists():
        print(f"❌ 找不到 ssd.py 檔案: {ssd_file}")
        return False
    
    print(f"🔍 找到 ssd.py 檔案: {ssd_file}")
    
    # 備份原始檔案
    backup_file = ssd_file.with_suffix('.py.backup')
    if not backup_file.exists():
        try:
            import shutil
            shutil.copy2(ssd_file, backup_file)
            print(f"✅ 已備份原始檔案: {backup_file}")
        except Exception as e:
            print(f"⚠️ 備份失敗: {e}")
    
    # 讀取檔案內容
    try:
        with open(ssd_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 讀取檔案失敗: {e}")
        return False
    
    # 檢查是否需要修復
    if "with files(" in content and "as model_dir:" in content:
        print("🔧 發現需要修復的程式碼...")
        
        # 修復 importlib.resources.files 的使用
        # 將 with files(...) as model_dir: 替換為兼容版本
        
        # 首先添加必要的 import
        if "from importlib.resources import files" in content:
            # 替換 import
            content = content.replace(
                "from importlib.resources import files",
                "from importlib.resources import files, as_file"
            )
        
        # 修復 with files() 使用
        pattern = r"with files\('([^']+)'\) as ([^:]+):"
        
        def replacement(match):
            package_name = match.group(1)
            var_name = match.group(2)
            return f"with as_file(files('{package_name}')) as {var_name}:"
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            try:
                with open(ssd_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print("✅ 成功修復 ssd.py 檔案")
                print("💡 修復內容: 將 with files() 改為 with as_file(files())")
                return True
            except Exception as e:
                print(f"❌ 寫入修復失敗: {e}")
                return False
        else:
            print("ℹ️ 未找到需要修復的程式碼模式")
            return False
    else:
        print("ℹ️ 檔案似乎不需要修復")
        return True

def restore_backup():
    """還原備份檔案"""
    venv_path = Path("vitallens_venv")
    if os.name == 'nt':
        site_packages = venv_path / "Lib" / "site-packages"
    else:
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = venv_path / "lib" / f"python{python_version}" / "site-packages"
    
    ssd_file = site_packages / "vitallens" / "ssd.py"
    backup_file = ssd_file.with_suffix('.py.backup')
    
    if backup_file.exists():
        try:
            import shutil
            shutil.copy2(backup_file, ssd_file)
            print(f"✅ 已還原備份檔案")
            return True
        except Exception as e:
            print(f"❌ 還原備份失敗: {e}")
            return False
    else:
        print("❌ 找不到備份檔案")
        return False

def main():
    """主程式"""
    print("🔧 VitalLens ssd.py 修復程式")
    print("修復 Python 3.13 importlib.resources 兼容性問題")
    print("=" * 55)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--restore', action='store_true', 
                       help='還原備份檔案')
    args = parser.parse_args()
    
    if args.restore:
        return restore_backup()
    else:
        return fix_ssd_file()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 操作完成！")
        if '--restore' not in sys.argv:
            print("💡 現在請重新啟動應用程式測試")
    else:
        print("\n❌ 操作失敗")
    
    sys.exit(0 if success else 1)

#!/usr/bin/env python
"""
修復 Python 3.13 importlib.resources 兼容性問題
解決 VitalLens 中的 'WindowsPath' object does not support the context manager protocol 錯誤
"""

import os
import sys
from pathlib import Path

def patch_importlib_resources():
    """修補 importlib.resources 以支援 Python 3.13"""
    
    # 檢查虛擬環境路徑
    venv_path = Path("vitallens_venv")
    if os.name == 'nt':
        site_packages = venv_path / "Lib" / "site-packages"
    else:
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = venv_path / "lib" / f"python{python_version}" / "site-packages"
    
    if not site_packages.exists():
        print(f"❌ 找不到虛擬環境: {site_packages}")
        return False
    
    # 建立修補檔案
    patch_file = site_packages / "importlib_resources_patch.py"
    
    patch_content = '''"""
importlib.resources 兼容性修補
修復 Python 3.13 中 WindowsPath 不支援 context manager 的問題
"""

import sys
from pathlib import Path
import importlib.resources as resources
from contextlib import contextmanager

# 保存原始的 files 函數
_original_files = resources.files

@contextmanager
def patched_files(package):
    """修補的 files 函數，支援 Python 3.13"""
    try:
        # 嘗試使用原始函數
        path_obj = _original_files(package)
        
        # 如果是 Path 物件且不支援 context manager，轉換為支援的格式
        if isinstance(path_obj, Path):
            # 轉換為字串路徑並使用 as_file
            from importlib.resources import as_file
            with as_file(path_obj) as file_path:
                yield file_path
        else:
            # 如果已經支援 context manager，直接使用
            with path_obj as path:
                yield path
                
    except TypeError as e:
        if "'WindowsPath' object does not support the context manager protocol" in str(e):
            # 回退方案：直接使用路徑
            path_obj = _original_files(package)
            if hasattr(path_obj, '__fspath__'):
                yield Path(path_obj)
            else:
                yield path_obj
        else:
            raise

# 應用修補
if sys.version_info >= (3, 13):
    resources.files = patched_files
    print("✅ 已應用 importlib.resources 修補 (Python 3.13+)")
else:
    print("ℹ️ Python 版本無需修補")
'''
    
    try:
        with open(patch_file, 'w', encoding='utf-8') as f:
            f.write(patch_content)
        print(f"✅ 建立修補檔案: {patch_file}")
        return True
    except Exception as e:
        print(f"❌ 建立修補檔案失敗: {e}")
        return False

def create_init_patch():
    """建立 __init__ 修補檔案來自動載入修補"""
    
    venv_path = Path("vitallens_venv")
    if os.name == 'nt':
        site_packages = venv_path / "Lib" / "site-packages"
    else:
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = venv_path / "lib" / f"python{python_version}" / "site-packages"
    
    # 建立一個 sitecustomize.py 來自動載入修補
    sitecustomize_file = site_packages / "sitecustomize.py"
    
    sitecustomize_content = '''"""
Site customization for VitalLens Python 3.13 compatibility
"""

try:
    # 自動載入 importlib.resources 修補
    import importlib_resources_patch
except ImportError:
    pass  # 如果修補檔案不存在，忽略
'''
    
    try:
        with open(sitecustomize_file, 'w', encoding='utf-8') as f:
            f.write(sitecustomize_content)
        print(f"✅ 建立自動載入檔案: {sitecustomize_file}")
        return True
    except Exception as e:
        print(f"❌ 建立自動載入檔案失敗: {e}")
        return False

def main():
    """主程式"""
    print("🔧 修復 importlib.resources 兼容性問題")
    print("=" * 50)
    
    if sys.version_info >= (3, 13):
        print(f"✅ 檢測到 Python {sys.version_info.major}.{sys.version_info.minor}")
        
        success1 = patch_importlib_resources()
        success2 = create_init_patch()
        
        if success1 and success2:
            print("\n✅ 修補完成！")
            print("💡 請重新啟動應用程式以使修補生效")
            return True
        else:
            print("\n❌ 修補失敗")
            return False
    else:
        print(f"ℹ️ Python {sys.version_info.major}.{sys.version_info.minor} 無需修補")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

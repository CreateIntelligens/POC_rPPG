#!/usr/bin/env python
"""
Python 3.13 兼容性修復腳本
解決 imghdr 模組被移除的問題
"""

import os
import sys
import site

def create_imghdr_shim():
    """創建 imghdr 模組的兼容性墊片"""
    
    # 找到虛擬環境的 site-packages 目錄
    venv_path = "vitallens_venv"
    if os.name == 'nt':  # Windows
        site_packages = os.path.join(venv_path, "Lib", "site-packages")
    else:  # Unix/Linux/macOS
        site_packages = os.path.join(venv_path, "lib", "python" + f"{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
    
    if not os.path.exists(site_packages):
        print(f"❌ 找不到虛擬環境: {site_packages}")
        return False
    
    # 創建 imghdr.py 墊片
    imghdr_path = os.path.join(site_packages, "imghdr.py")
    
    imghdr_content = '''"""
imghdr module compatibility shim for Python 3.13+
This module was removed in Python 3.13, but some packages still depend on it.
"""

import mimetypes
from pathlib import Path

def what(file, h=None):
    """Detect format of image (deprecated, use python-magic or Pillow instead)"""
    if hasattr(file, 'read'):
        # file-like object
        header = file.read(32)
        file.seek(0)
    elif isinstance(file, (str, Path)):
        # file path
        try:
            with open(str(file), 'rb') as f:
                header = f.read(32)
        except:
            return None
    else:
        header = file
    
    # Basic format detection
    if header.startswith(b'\\xff\\xd8\\xff'):
        return 'jpeg'
    elif header.startswith(b'\\x89PNG\\r\\n\\x1a\\n'):
        return 'png'
    elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        return 'gif'
    elif header.startswith(b'RIFF') and b'WEBP' in header[:12]:
        return 'webp'
    elif header.startswith(b'BM'):
        return 'bmp'
    elif header.startswith(b'\\x00\\x00\\x01\\x00'):
        return 'ico'
    
    return None

# For compatibility
test_jpeg = lambda h, f: h.startswith(b'\\xff\\xd8\\xff')
test_png = lambda h, f: h.startswith(b'\\x89PNG\\r\\n\\x1a\\n')
test_gif = lambda h, f: h.startswith(b'GIF87a') or h.startswith(b'GIF89a')
test_webp = lambda h, f: h.startswith(b'RIFF') and b'WEBP' in h[:12]
test_bmp = lambda h, f: h.startswith(b'BM')
test_ico = lambda h, f: h.startswith(b'\\x00\\x00\\x01\\x00')

tests = [
    (test_jpeg, 'jpeg'),
    (test_png, 'png'), 
    (test_gif, 'gif'),
    (test_webp, 'webp'),
    (test_bmp, 'bmp'),
    (test_ico, 'ico'),
]
'''
    
    try:
        with open(imghdr_path, 'w', encoding='utf-8') as f:
            f.write(imghdr_content)
        print(f"✅ 已創建 imghdr 兼容性墊片: {imghdr_path}")
        return True
    except Exception as e:
        print(f"❌ 創建 imghdr 墊片失敗: {e}")
        return False

def main():
    """主程式"""
    print("🔧 Python 3.13 兼容性修復程式")
    print("=" * 40)
    
    if sys.version_info >= (3, 13):
        print(f"✅ 檢測到 Python {sys.version_info.major}.{sys.version_info.minor}")
        print("🔧 正在修復 imghdr 模組兼容性問題...")
        
        if create_imghdr_shim():
            print("✅ 修復完成！")
            return True
        else:
            print("❌ 修復失敗！")
            return False
    else:
        print(f"ℹ️ Python {sys.version_info.major}.{sys.version_info.minor} 不需要修復")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

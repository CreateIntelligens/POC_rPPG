#!/usr/bin/env python
"""
簡化的 Python 3.13 兼容性修復
"""

import os
import sys

def create_simple_imghdr():
    """創建簡化的 imghdr 模組"""
    
    # 確定虛擬環境路徑
    venv_path = os.path.join(".", "vitallens_venv")
    
    if os.name == 'nt':  # Windows
        site_packages = os.path.join(venv_path, "Lib", "site-packages")
    else:  # Unix/Linux/macOS
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = os.path.join(venv_path, "lib", f"python{python_version}", "site-packages")
    
    # 檢查目錄是否存在
    if not os.path.exists(site_packages):
        print(f"❌ 虛擬環境不存在: {site_packages}")
        return False
    
    # 創建 imghdr.py 檔案
    imghdr_file = os.path.join(site_packages, "imghdr.py")
    
    # 簡化的 imghdr 內容
    content = '''"""
Simplified imghdr module for Python 3.13+ compatibility
"""

def what(file, h=None):
    """Simple image format detection"""
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
    
    return None

# Compatibility functions
test_jpeg = lambda h, f: h.startswith(b'\\xff\\xd8\\xff')
test_png = lambda h, f: h.startswith(b'\\x89PNG\\r\\n\\x1a\\n')
test_gif = lambda h, f: h.startswith(b'GIF87a') or h.startswith(b'GIF89a')

tests = [
    (test_jpeg, 'jpeg'),
    (test_png, 'png'), 
    (test_gif, 'gif'),
]
'''

    try:
        with open(imghdr_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 成功創建 imghdr 兼容模組: {imghdr_file}")
        return True
    except Exception as e:
        print(f"❌ 創建失敗: {e}")
        return False

def main():
    print("🔧 簡化 Python 3.13 修復程式")
    print("-" * 30)
    
    if sys.version_info >= (3, 13):
        print("✅ 檢測到 Python 3.13+")
        if create_simple_imghdr():
            print("✅ 修復完成！")
        else:
            print("❌ 修復失敗")
            return False
    else:
        print("ℹ️ Python 版本無需修復")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)

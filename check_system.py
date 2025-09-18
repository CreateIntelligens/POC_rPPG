#!/usr/bin/env python
"""
檢查系統是否符合 VitalLens 官方要求
根據 https://docs.rouast.com/python/ 的要求
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """檢查 Python 版本"""
    print("🐍 檢查 Python 版本...")
    
    version = sys.version_info
    print(f"   當前版本: Python {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 9):
        if version >= (3, 13):
            print("   ⚠️ 您使用 Python 3.13，可能有兼容性問題")
            print("   💡 建議使用 Python 3.9-3.12 以獲得最佳兼容性")
            return "warning"
        else:
            print("   ✅ Python 版本符合要求 (>=3.9)")
            return "ok"
    else:
        print("   ❌ Python 版本過舊，需要 Python 3.9 或更新版本")
        return "error"

def check_ffmpeg():
    """檢查 ffmpeg 是否安裝"""
    print("\n🎬 檢查 FFmpeg...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # 解析版本
            lines = result.stdout.split('\n')
            for line in lines:
                if line.startswith('ffmpeg version'):
                    version = line.split(' ')[2]
                    print(f"   ✅ FFmpeg 已安裝: {version}")
                    return "ok"
        else:
            print("   ❌ FFmpeg 未正確安裝")
            return "error"
    except FileNotFoundError:
        print("   ❌ 找不到 FFmpeg")
        print("   💡 請安裝 FFmpeg 並確保在 PATH 中")
        return "error"
    except subprocess.TimeoutExpired:
        print("   ⚠️ FFmpeg 檢查超時")
        return "warning"
    except Exception as e:
        print(f"   ❌ FFmpeg 檢查失敗: {e}")
        return "error"

def check_visual_cpp():
    """檢查 Windows 上的 Visual C++"""
    if platform.system() != "Windows":
        return "skip"
    
    print("\n🔧 檢查 Microsoft Visual C++...")
    
    # 簡單檢查 - 嘗試導入需要 VC++ 的套件
    try:
        import numpy
        print("   ✅ Visual C++ 編譯環境正常")
        return "ok"
    except ImportError:
        print("   ⚠️ 無法驗證 Visual C++ 安裝")
        print("   💡 如果遇到編譯錯誤，請安裝 Microsoft Visual C++ Redistributable")
        return "warning"

def check_vitallens():
    """檢查 VitalLens 安裝"""
    print("\n🩺 檢查 VitalLens 安裝...")
    
    try:
        import vitallens
        from vitallens import VitalLens, Method
        
        print(f"   ✅ VitalLens 已安裝")
        
        # 檢查可用方法
        available_methods = []
        for method_name in ['VITALLENS', 'POS', 'CHROM', 'G']:
            if hasattr(Method, method_name):
                available_methods.append(method_name)
        
        print(f"   ✅ 可用方法: {', '.join(available_methods)}")
        return "ok"
        
    except ImportError as e:
        print(f"   ❌ VitalLens 未安裝或導入失敗: {e}")
        return "error"

def provide_solutions():
    """提供解決方案"""
    print("\n" + "="*50)
    print("🔧 解決方案建議:")
    print("="*50)
    
    print("\n1. **FFmpeg 安裝**:")
    print("   Windows: 下載 https://ffmpeg.org/download.html")
    print("   macOS: brew install ffmpeg")
    print("   Ubuntu: sudo apt install ffmpeg")
    
    print("\n2. **Python 版本問題**:")
    print("   建議使用 Python 3.9-3.12")
    print("   可以使用 pyenv 或 conda 管理多個 Python 版本")
    
    print("\n3. **Windows Visual C++**:")
    print("   下載安裝 Microsoft Visual C++ Redistributable")
    print("   或安裝 Microsoft Build Tools for Visual Studio")
    
    print("\n4. **VitalLens 安裝**:")
    print("   pip install vitallens")
    print("   如果失敗，嘗試: pip install --upgrade pip 然後重試")

def main():
    print("🔍 VitalLens 系統環境檢查")
    print("依據官方文件要求: https://docs.rouast.com/python/")
    print("="*60)
    
    results = []
    
    # 檢查各項要求
    results.append(("Python 版本", check_python_version()))
    results.append(("FFmpeg", check_ffmpeg()))
    results.append(("Visual C++", check_visual_cpp()))
    results.append(("VitalLens", check_vitallens()))
    
    # 統計結果
    print("\n" + "="*60)
    print("📊 檢查結果總結:")
    print("="*60)
    
    errors = 0
    warnings = 0
    
    for name, status in results:
        if status == "ok":
            print(f"✅ {name}: 正常")
        elif status == "warning":
            print(f"⚠️ {name}: 警告")
            warnings += 1
        elif status == "error":
            print(f"❌ {name}: 錯誤")
            errors += 1
        elif status == "skip":
            print(f"⏭️ {name}: 跳過")
    
    print(f"\n錯誤: {errors}, 警告: {warnings}")
    
    if errors > 0:
        print("\n❌ 有嚴重問題需要解決")
        provide_solutions()
        return False
    elif warnings > 0:
        print("\n⚠️ 有警告但可能仍可運行")
        print("如果遇到問題，請參考解決方案")
        provide_solutions()
        return True
    else:
        print("\n🎉 所有檢查通過！系統符合 VitalLens 要求")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

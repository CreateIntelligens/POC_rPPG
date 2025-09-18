#!/usr/bin/env python
"""
檢查系統中可用的 Python 版本
並提供 VitalLens 兼容性建議
"""

import subprocess
import sys
import platform

def check_python_command(cmd):
    """檢查指定的 Python 命令"""
    try:
        result = subprocess.run([cmd, '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_str = result.stdout.strip()
            
            # 獲取詳細版本資訊
            version_result = subprocess.run([cmd, '-c', 
                'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'], 
                capture_output=True, text=True, timeout=5)
            
            if version_result.returncode == 0:
                version = version_result.stdout.strip()
                return {
                    'command': cmd,
                    'version_str': version_str,
                    'version': version,
                    'major': int(version.split('.')[0]),
                    'minor': int(version.split('.')[1]),
                    'micro': int(version.split('.')[2])
                }
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError, ValueError, IndexError):
        pass
    
    return None

def get_vitallens_compatibility(version_info):
    """評估 VitalLens 兼容性"""
    major, minor = version_info['major'], version_info['minor']
    
    if major != 3:
        return "❌ 不支援", "VitalLens 需要 Python 3.x"
    
    if minor < 9:
        return "❌ 版本過舊", "VitalLens 需要 Python 3.9+"
    
    if minor == 9 or minor == 10 or minor == 11 or minor == 12:
        return "✅ 完美兼容", "推薦版本，官方完全支援"
    
    if minor == 13:
        return "⚠️ 可能有問題", "Python 3.13 有已知兼容性問題"
    
    if minor > 13:
        return "❓ 未知", "版本太新，兼容性未知"
    
    return "❓ 未知", "版本兼容性未知"

def main():
    """主程式"""
    print("🐍 Python 版本檢查工具")
    print("檢查 VitalLens 兼容性")
    print("=" * 50)
    
    # 常見的 Python 命令
    commands = [
        'python',
        'python3',
        'python3.9',
        'python3.10',
        'python3.11',
        'python3.12',
        'python3.13',
        'python39',
        'python310',
        'python311',
        'python312',
        'python313',
        'py -3.9',
        'py -3.10', 
        'py -3.11',
        'py -3.12',
        'py -3.13',
        'py',
    ]
    
    found_versions = []
    
    print("🔍 掃描可用的 Python 版本...")
    
    for cmd in commands:
        version_info = check_python_command(cmd)
        if version_info:
            # 避免重複（相同版本的不同命令）
            if not any(v['version'] == version_info['version'] for v in found_versions):
                found_versions.append(version_info)
    
    if not found_versions:
        print("❌ 未找到任何 Python 安裝")
        return
    
    # 排序版本
    found_versions.sort(key=lambda x: (x['major'], x['minor'], x['micro']))
    
    print(f"\n📋 找到 {len(found_versions)} 個 Python 版本:")
    print("=" * 70)
    print(f"{'命令':<15} {'版本':<12} {'兼容性':<12} {'說明':<25}")
    print("-" * 70)
    
    recommended_versions = []
    
    for version_info in found_versions:
        compatibility, note = get_vitallens_compatibility(version_info)
        
        print(f"{version_info['command']:<15} {version_info['version']:<12} {compatibility:<12} {note:<25}")
        
        # 收集推薦版本
        if "完美兼容" in compatibility:
            recommended_versions.append(version_info)
    
    # 顯示當前版本
    print("\n" + "=" * 70)
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"🔸 當前執行版本: Python {current_version}")
    
    current_compatibility, current_note = get_vitallens_compatibility({
        'major': sys.version_info.major,
        'minor': sys.version_info.minor,
        'micro': sys.version_info.micro
    })
    print(f"🔸 當前版本兼容性: {current_compatibility} - {current_note}")
    
    # 建議
    print("\n💡 建議:")
    print("=" * 30)
    
    if recommended_versions:
        print("✅ 推薦使用以下版本設置 VitalLens:")
        for version_info in recommended_versions:
            print(f"   - {version_info['command']} (Python {version_info['version']})")
        
        print(f"\n📋 設置命令:")
        best_version = recommended_versions[0]
        print(f"   手動建立: {best_version['command']} -m venv vitallens_py39_venv")
        print(f"   或執行腳本: python setup_python39_venv.py")
        
    else:
        print("❌ 未找到推薦的 Python 版本")
        print("💿 請安裝 Python 3.9-3.12:")
        
        system = platform.system()
        if system == "Windows":
            print("   - 官方下載: https://www.python.org/downloads/")
            print("   - winget: winget install Python.Python.3.9")
        elif system == "Darwin":
            print("   - Homebrew: brew install python@3.9")
            print("   - pyenv: pyenv install 3.9.12")
        else:
            print("   - apt: sudo apt install python3.9")
            print("   - pyenv: pyenv install 3.9.12")
    
    # 如果當前版本有問題，提供解決方案
    if current_compatibility.startswith("⚠️") or current_compatibility.startswith("❌"):
        print(f"\n🔧 當前版本({current_version})有問題的解決方案:")
        print("   1. 安裝推薦的 Python 版本")
        print("   2. 使用虛擬環境隔離")
        print("   3. 執行: python setup_py39.bat (Windows)")
        print("   4. 或: python setup_python39_venv.py")

if __name__ == "__main__":
    main()

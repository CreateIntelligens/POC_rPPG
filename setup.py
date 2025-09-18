#!/usr/bin/env python
"""
VitalLens Gradio 應用程式安裝腳本
"""

import subprocess
import sys
import os

def install_requirements():
    """安裝必要套件"""
    print("📦 正在安裝必要套件...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 套件安裝完成")
        return True
    except subprocess.CalledProcessError:
        print("❌ 套件安裝失敗")
        return False

def create_config():
    """建立設定檔"""
    if not os.path.exists("config.py"):
        print("📝 建立設定檔...")
        try:
            # 複製範例設定檔
            with open("config.example.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            with open("config.py", "w", encoding="utf-8") as f:
                f.write(content)
            
            print("✅ 設定檔已建立（config.py）")
            print("💡 您可以編輯 config.py 來自訂設定")
        except Exception as e:
            print(f"⚠️ 設定檔建立失敗: {e}")
    else:
        print("ℹ️ 設定檔已存在")

def main():
    """主程式"""
    print("🚀 VitalLens Gradio 應用程式安裝程式")
    print("=" * 50)
    
    # 安裝套件
    if not install_requirements():
        print("❌ 安裝失敗，請檢查錯誤訊息")
        sys.exit(1)
    
    # 建立設定檔
    create_config()
    
    print("\n✅ 安裝完成！")
    print("📋 使用說明:")
    print("   1. 編輯 config.py 設定您的 API Key（可選）")
    print("   2. 執行 python app.py 或 python run.py 啟動應用程式")
    print("   3. 在瀏覽器中開啟顯示的網址")
    print("\n🔗 相關連結:")
    print("   - VitalLens API: https://www.rouast.com/api/")
    print("   - GitHub 專案: https://github.com/Rouast-Labs/vitallens-python")

if __name__ == "__main__":
    main()

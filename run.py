#!/usr/bin/env python
"""
VitalLens Gradio 應用程式啟動腳本
"""

import os
import sys

def main():
    """主程式入口"""
    print("🩺 啟動 VitalLens 生命體徵檢測器...")
    print("📋 正在檢查相依套件...")
    
    # 檢查是否已安裝必要套件
    try:
        import gradio
        import vitallens
        print("✅ 所有相依套件已安裝")
    except ImportError as e:
        print(f"❌ 缺少必要套件: {e}")
        print("請執行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 載入設定檔（如果存在）
    try:
        import config
        print("✅ 已載入自訂設定檔")
        
        # 設定環境變數
        if hasattr(config, 'DEFAULT_API_KEY') and config.DEFAULT_API_KEY:
            os.environ['VITALLENS_API_KEY'] = config.DEFAULT_API_KEY
        
        if hasattr(config, 'SERVER_PORT'):
            os.environ['GRADIO_SERVER_PORT'] = str(config.SERVER_PORT)
            
    except ImportError:
        print("ℹ️ 未找到設定檔，使用預設設定")
    
    # 啟動應用程式
    print("🚀 正在啟動 Gradio 介面...")
    from app import create_interface
    
    interface = create_interface()
    
    # 取得設定
    port = int(os.environ.get('GRADIO_SERVER_PORT', 7860))
    share = os.environ.get('GRADIO_SHARE', 'False').lower() == 'true'
    
    print(f"🌐 介面將在 http://localhost:{port} 啟動")
    if share:
        print("🔗 將產生公開分享連結")
    
    # 啟動介面
    interface.launch(
        share=share,
        server_name="0.0.0.0",
        server_port=port,
        show_error=True
    )

if __name__ == "__main__":
    main()

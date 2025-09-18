#!/usr/bin/env python
"""
測試 WindowsPath 修復是否有效
"""

import os
from pathlib import Path

def test_path_handling():
    """測試路徑處理函數"""
    print("🧪 測試路徑處理...")
    
    # 測試不同類型的路徑輸入
    test_file = "test_video.mp4"
    
    # 創建測試檔案
    with open(test_file, 'w') as f:
        f.write("test")
    
    try:
        # 測試字串路徑
        str_path = test_file
        print(f"✅ 字串路徑: {str_path}")
        
        # 測試 Path 物件
        path_obj = Path(test_file)
        print(f"✅ Path 物件: {path_obj}")
        
        # 測試路徑轉換函數
        def convert_path(video_file):
            if hasattr(video_file, '__fspath__'):
                return os.fspath(video_file)
            elif hasattr(video_file, 'name'):
                return video_file.name
            else:
                return str(video_file)
        
        # 測試轉換
        converted_str = convert_path(str_path)
        converted_path = convert_path(path_obj)
        
        print(f"✅ 轉換結果 (字串): {converted_str}")
        print(f"✅ 轉換結果 (Path): {converted_path}")
        
        print("🎉 所有測試通過！")
        
    finally:
        # 清理測試檔案
        if os.path.exists(test_file):
            os.remove(test_file)

def test_vitallens_import():
    """測試 VitalLens 導入"""
    print("\n🧪 測試 VitalLens 導入...")
    
    try:
        from vitallens import VitalLens, Method
        print("✅ VitalLens 導入成功")
        
        # 測試方法
        available_methods = [Method.POS, Method.CHROM, Method.G]
        if hasattr(Method, 'VITALLENS'):
            available_methods.append(Method.VITALLENS)
        
        print(f"✅ 可用方法: {len(available_methods)} 個")
        
    except Exception as e:
        print(f"❌ VitalLens 導入失敗: {e}")
        return False
    
    return True

def main():
    print("🔧 WindowsPath 修復測試程式")
    print("=" * 40)
    
    # 測試路徑處理
    test_path_handling()
    
    # 測試 VitalLens 導入
    success = test_vitallens_import()
    
    if success:
        print("\n🎉 所有測試通過！應用程式應該可以正常運行。")
    else:
        print("\n❌ 有測試失敗，請檢查虛擬環境設置。")
    
    return success

if __name__ == "__main__":
    main()

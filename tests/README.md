# VitalLens rPPG 測試套件

這個目錄包含了 VitalLens rPPG 系統的完整測試套件。

## 測試檔案結構

```
tests/
├── __init__.py              # 測試套件初始化
├── conftest.py             # pytest 全局配置和 fixtures
├── test_main.py            # 主要路由和基本功能測試
├── test_video_analysis.py  # 影片分析功能測試
├── test_webcam.py          # 攝影機功能測試
├── test_service.py         # VitalLensService 服務層測試
├── test_integration.py     # 整合測試
└── README.md               # 此檔案
```

## 運行測試

### 基本測試運行
```bash
# 運行所有測試
pytest

# 運行特定測試檔案
pytest tests/test_main.py

# 運行特定測試類別
pytest tests/test_main.py::TestMainRoutes

# 運行特定測試函數
pytest tests/test_main.py::TestMainRoutes::test_index_page
```

### 測試選項
```bash
# 詳細輸出
pytest -v

# 顯示測試覆蓋率 (需要安裝 pytest-cov)
pytest --cov=app

# 運行慢速測試
pytest --run-slow

# 運行整合測試
pytest --run-integration

# 跳過需要攝影機的測試
pytest --skip-webcam

# 並行運行測試 (需要安裝 pytest-xdist)
pytest -n auto
```

## 測試標記

- `@pytest.mark.unit` - 單元測試
- `@pytest.mark.integration` - 整合測試
- `@pytest.mark.slow` - 慢速測試
- `@pytest.mark.webcam` - 需要攝影機的測試
- `@pytest.mark.api` - 需要 API 金鑰的測試

## 測試涵蓋範圍

### 主要功能測試 (`test_main.py`)
- 首頁載入
- 健康檢查端點
- 靜態檔案存取
- 錯誤處理

### 影片分析測試 (`test_video_analysis.py`)
- 影片上傳功能
- 支援的影片格式
- 無效輸入處理
- 分析錯誤處理

### 攝影機測試 (`test_webcam.py`)
- 攝影機錄影啟動/停止
- 參數驗證
- 連接失敗處理
- 狀態查詢

### 服務層測試 (`test_service.py`)
- VitalLensService 功能
- 方法和參數驗證
- VitalLens 實例初始化
- 工具函數

### 整合測試 (`test_integration.py`)
- 完整工作流程
- 錯誤恢復
- 效能測試

## 測試配置

測試使用模擬 (mocking) 來避免：
- 真實的 VitalLens API 調用
- 實際的攝影機存取
- 檔案系統操作

所有測試都在隔離的環境中運行，不會影響實際的系統狀態。

## 注意事項

1. 測試需要安裝 `pytest` 套件
2. 某些測試使用 `unittest.mock` 進行模擬
3. 整合測試可能運行較慢，使用 `--run-integration` 選項執行
4. 如果需要測試攝影機功能，請確保系統有可用的攝影機設備
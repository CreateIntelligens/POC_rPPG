# VitalLens Gradio 生命體徵檢測器

這是一個基於 [VitalLens Python API](https://github.com/Rouast-Labs/vitallens-python) 的 Gradio 網頁應用程式，可以從影片中估算心率、呼吸率等生命體徵。

## 🌟 功能特色

- 🎥 **影片上傳**: 支援多種影片格式（MP4, AVI, MOV, MKV, WebM）
- 🩺 **多種檢測方法**:
  - **VITALLENS**: 最準確，支援心率、呼吸率、脈搏波形、呼吸波形（需要 API Key）
  - **POS**: 免費方法，支援心率和脈搏波形
  - **CHROM**: 免費方法，支援心率和脈搏波形
  - **G**: 免費方法，支援心率和脈搏波形
- 📊 **視覺化結果**: 自動生成波形圖和數據分析
- 🔒 **安全**: API Key 使用密碼輸入框保護
- 🌐 **易用**: 直觀的網頁介面，無需程式設計經驗

## 🚀 快速開始

### 方法一：使用虛擬環境（推薦）

#### 1. 設定 API Key（推薦）
```bash
# 將 env.example 重新命名為 .env
cp env.example .env  # Linux/macOS
copy env.example .env  # Windows

# 編輯 .env 檔案，填入您的 API Key
# VITALLENS_API_KEY=your_actual_api_key_here
```

#### 2. 自動設置虛擬環境
```bash
python setup_venv.py
```

#### 3. 啟動應用程式
**Windows:**
```batch
run_app.bat
```

**macOS/Linux:**
```bash
./run_app.sh
```

### 方法二：直接安裝（全域環境）

#### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

#### 2. 啟動應用程式
```bash
python app.py
```

### 3. 開啟瀏覽器

應用程式啟動後，會顯示本地網址（通常是 `http://localhost:7860`），在瀏覽器中開啟即可使用。

## 📋 使用說明

### 基本步驟

1. **上傳影片**: 點擊「上傳影片檔案」選擇您的影片
2. **選擇方法**: 
   - 如果您有 API Key，建議選擇「VITALLENS」獲得最佳準確度
   - 沒有 API Key 可選擇「POS」、「CHROM」或「G」方法
3. **輸入 API Key**: 僅在使用 VITALLENS 時需要填寫
4. **開始分析**: 點擊「🔍 開始分析」按鈕
5. **查看結果**: 分析完成後會顯示波形圖和詳細數據

### API Key 設定

#### 方法一：使用 .env 檔案（推薦）

1. **複製範例檔案**：
   ```bash
   cp env.example .env  # Linux/macOS
   copy env.example .env  # Windows
   ```

2. **獲取 API Key**：
   - 訪問 [VitalLens API 官網](https://www.rouast.com/api/)
   - 註冊免費帳號
   - 獲取您的專屬 API Key

3. **編輯 .env 檔案**：
   ```env
   # 將 your_api_key_here 替換為您的實際 API Key
   VITALLENS_API_KEY=your_actual_api_key_here
   
   # 可選：自訂其他設定
   DEFAULT_METHOD=VITALLENS (需要 API Key)
   GRADIO_SERVER_PORT=7860
   GRADIO_SHARE=false
   ```

4. **重新啟動應用程式**

#### 方法二：在介面中輸入

如果您不想使用 .env 檔案，也可以直接在網頁介面的 API Key 輸入框中填入。

## 📊 結果說明

### 輸出數據

- **心率 (Heart Rate)**: 每分鐘心跳次數（bpm）
- **呼吸率 (Respiratory Rate)**: 每分鐘呼吸次數（rpm，僅 VITALLENS）
- **PPG 波形**: 光體積描記法信號，反映血液體積變化
- **呼吸波形**: 呼吸模式的時間序列數據（僅 VITALLENS）
- **連續心率**: 整個影片期間的連續心率測量
- **連續呼吸率**: 整個影片期間的連續呼吸率測量（僅 VITALLENS）

### 置信度

每個測量結果都包含置信度評分，幫助您評估結果的可靠性。

## 🔧 技術細節

### 系統要求（根據 [官方文件](https://docs.rouast.com/python/)）

- **Python**: 3.9 或更新版本（建議 3.9-3.12，Python 3.13 可能有兼容性問題）
- **FFmpeg**: 必須安裝並可通過 PATH 存取
- **Windows**: 需要 Microsoft Visual C++

### 支援的影片要求

- **心率檢測**: 至少 **5 秒** 的影片
- **呼吸率檢測**: 至少 **10 秒** 的影片（僅 VITALLENS 支援）
- **連續生命體徵**: **10-30 秒** 或更長的影片
- **人臉要求**: 需要清晰可見的人臉
- **品質要求**: 良好光線條件和穩定拍攝

### 方法比較

| 方法 | 準確度 | 速度 | 需要 API Key | 支援功能 |
|------|--------|------|-------------|----------|
| VITALLENS | ⭐⭐⭐⭐⭐ | 中等 | ✅ | 心率、呼吸率、波形 |
| POS | ⭐⭐⭐⭐ | 快 | ❌ | 心率、脈搏波形 |
| CHROM | ⭐⭐⭐ | 快 | ❌ | 心率、脈搏波形 |
| G | ⭐⭐⭐ | 快 | ❌ | 心率、脈搏波形 |

## ⚠️ 重要聲明

**此工具僅供一般健康參考用途，不可用於醫療診斷。如有任何健康疑慮，請諮詢專業醫師。**

## 🛠️ 開發者資訊

### 專案結構

```
POC_rPPG/
├── app.py              # 主要應用程式
├── requirements.txt    # Python 依賴
├── README.md          # 說明文件
├── env.example        # .env 檔案範例
├── .env               # 環境變數設定檔（使用者建立）
├── config.example.py  # 設定檔範例
├── setup_venv.py      # 虛擬環境設置腳本
├── run.py             # 簡化啟動腳本
├── setup.py           # 安裝腳本
├── run_app.bat        # Windows 執行腳本（自動生成）
├── run_app.sh         # Unix 執行腳本（自動生成）
├── VENV_GUIDE.md      # 虛擬環境使用指南（自動生成）
└── vitallens_venv/    # 虛擬環境目錄（自動生成）
```

### 虛擬環境優點

使用虛擬環境的好處：
- 🔒 **隔離性**: 不會影響系統的 Python 環境
- 📦 **相依性管理**: 每個專案有獨立的套件版本
- 🧹 **易於清理**: 可以完全移除而不影響其他專案
- 🔄 **可重現性**: 確保在不同機器上有相同的環境
- 🛡️ **安全性**: 避免套件衝突和版本問題

### 自訂設定

您可以創建 `config.py` 檔案來自訂預設設定：

```python
# config.py
DEFAULT_API_KEY = "your_default_api_key"
DEFAULT_METHOD = "VITALLENS"
SERVER_PORT = 7860
SHARE_GRADIO = True
```

### 環境變數

透過 `.env` 檔案支援以下環境變數：

#### API 設定
- `VITALLENS_API_KEY`: VitalLens API Key
- `DEFAULT_METHOD`: 預設檢測方法

#### 伺服器設定
- `GRADIO_SERVER_PORT`: 伺服器埠號（預設：7860）
- `GRADIO_SERVER_NAME`: 伺服器地址（預設：0.0.0.0）
- `GRADIO_SHARE`: 是否啟用公開分享（預設：false）

#### 介面設定
- `APP_TITLE`: 應用程式標題
- `APP_THEME`: 介面主題（soft/default/monochrome）

#### 檔案設定
- `MAX_FILE_SIZE_MB`: 最大檔案大小（MB）

#### 進階設定
- `ENABLE_QUEUE`: 是否啟用佇列系統
- `MAX_QUEUE_SIZE`: 最大佇列大小

## 📚 相關資源

- [VitalLens Python API](https://github.com/Rouast-Labs/vitallens-python)
- [VitalLens API 官網](https://www.rouast.com/api/)
- [Gradio 文件](https://gradio.app/docs/)

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 來改善此專案！

## 📄 授權

本專案使用 MIT 授權條款。VitalLens API 有其自己的使用條款，請參考官方網站。

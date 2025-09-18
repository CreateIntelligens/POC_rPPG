# 🚀 VitalLens Gradio 快速設置指南

## 📋 步驟概覽

1. [設定 API Key](#1-設定-api-key)
2. [安裝依賴](#2-安裝依賴)
3. [啟動應用程式](#3-啟動應用程式)

---

## 1. 設定 API Key

### 🔑 獲取 API Key

1. 訪問 [VitalLens API 官網](https://www.rouast.com/api/)
2. 註冊免費帳號
3. 複製您的 API Key

### ⚙️ 設定環境變數

**方法一：使用 .env 檔案（推薦）**

```bash
# 1. 複製範例檔案
cp env.example .env

# 2. 編輯 .env 檔案
# Windows: notepad .env
# macOS: open .env
# Linux: nano .env

# 3. 將 your_api_key_here 替換為您的實際 API Key
VITALLENS_API_KEY=your_actual_api_key_here
```

**方法二：直接在介面輸入**

如果不想使用 .env 檔案，可以在網頁介面的 API Key 欄位中直接輸入。

---

## 2. 安裝依賴

### 🐍 使用虛擬環境（推薦）

```bash
# 自動設置虛擬環境和安裝依賴
python setup_venv.py
```

### 📦 直接安裝

```bash
# 安裝必要套件
pip install -r requirements.txt
```

---

## 3. 啟動應用程式

### 🎯 使用執行腳本

**Windows:**
```batch
# 雙擊執行或在命令提示字元中執行
run_app.bat
```

**macOS/Linux:**
```bash
# 在終端機中執行
./run_app.sh
```

### 🔧 手動啟動

```bash
# 如果使用虛擬環境，先啟動
# Windows: vitallens_venv\Scripts\activate.bat
# macOS/Linux: source vitallens_venv/bin/activate

# 啟動應用程式
python app.py
```

---

## 🌐 使用應用程式

1. **開啟瀏覽器**：訪問顯示的網址（通常是 `http://localhost:7860`）
2. **上傳影片**：支援 MP4, AVI, MOV, MKV, WebM 格式
3. **選擇方法**：
   - 有 API Key → 選擇「VITALLENS」
   - 沒有 API Key → 選擇「POS」、「CHROM」或「G」
4. **開始分析**：點擊「🔍 開始分析」按鈕
5. **查看結果**：分析完成後查看波形圖和詳細數據

---

## 🔧 故障排除

### ❓ 常見問題

**問題：找不到模組**
```bash
# 解決：確認已安裝依賴
pip install -r requirements.txt
```

**問題：API Key 錯誤**
```bash
# 解決：檢查 .env 檔案中的 API Key 是否正確
cat .env  # Linux/macOS
type .env  # Windows
```

**問題：埠號被佔用**
```bash
# 解決：修改 .env 檔案中的埠號
GRADIO_SERVER_PORT=7861
```

**問題：虛擬環境問題**
```bash
# 解決：重新建立虛擬環境
rm -rf vitallens_venv  # Linux/macOS
rmdir /s vitallens_venv  # Windows
python setup_venv.py
```

### 📞 需要幫助？

- 查看 [README.md](README.md) 獲取詳細說明
- 訪問 [VitalLens GitHub](https://github.com/Rouast-Labs/vitallens-python) 查看 API 文件
- 檢查 [Issues](https://github.com/Rouast-Labs/vitallens-python/issues) 查看已知問題

---

## ⚠️ 重要提醒

- 此工具僅供一般健康參考，不可用於醫療診斷
- 保護好您的 API Key，不要在公開場所分享
- 確保影片中有清晰可見的人臉以獲得最佳結果

---

**🎉 享受使用 VitalLens 生命體徵檢測器！**

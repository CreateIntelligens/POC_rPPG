# VitalLens 網路攝影機即時檢測指南

## 🎯 簡介

這是 VitalLens 生命體徵檢測器的網路攝影機版本，可以使用您的電腦攝影機即時錄製影片並分析生命體徵。

## 🚀 快速開始

### Windows 用戶
```bash
# 雙擊執行
run_webcam_app.bat

# 或在命令提示字元中執行
.\run_webcam_app.bat
```

### Linux/macOS 用戶
```bash
# 設定執行權限（僅需執行一次）
chmod +x run_webcam_app.sh

# 執行應用程式
./run_webcam_app.sh
```

### 手動執行
```bash
# 啟動虛擬環境
# Windows:
vitallens_venv\Scripts\activate

# Linux/macOS:
source vitallens_venv/bin/activate

# 執行應用程式
python webcam_app.py
```

## 📱 使用方法

1. **啟動應用程式**
   - 執行上述任一啟動指令
   - 在瀏覽器中開啟 `http://localhost:7861`

2. **設定檢測參數**
   - **檢測方法**: 選擇要使用的演算法
     - `VITALLENS`: 最準確（需要 API Key）
     - `POS`, `CHROM`, `G`: 免費方法
   - **API Key**: 如使用 VITALLENS 方法則必填
   - **錄影時間**: 建議 15-30 秒

3. **開始錄影**
   - 點擊 "🔴 開始錄影" 按鈕
   - 面向攝影機並保持靜止
   - 錄影完成後會自動分析

4. **查看結果**
   - 系統會顯示心率、呼吸率等數值
   - 同時提供波形圖表供參考

## 🔧 設定 API Key

### 方法一：使用 .env 檔案（推薦）
1. 複製 `config.example.py` 並重新命名為 `.env`
2. 編輯 `.env` 檔案：
   ```
   VITALLENS_API_KEY=your_actual_api_key_here
   DEFAULT_METHOD=VITALLENS (需要 API Key)
   GRADIO_SERVER_PORT=7861
   ```
3. 重新啟動應用程式

### 方法二：在介面中輸入
1. 訪問 [VitalLens API 官網](https://www.rouast.com/api/)
2. 註冊免費帳號並獲取 API Key
3. 在應用程式介面的 API Key 欄位中輸入

## 💡 獲得最佳效果的秘訣

### 環境設置
- **光線**: 確保面部有充足且均勻的光線，避免強烈陰影
- **背景**: 選擇簡單、無雜亂的背景
- **距離**: 距離攝影機約 50-100 公分

### 錄影技巧
- **保持靜止**: 盡量減少頭部移動和身體晃動
- **面向攝影機**: 確保臉部正面朝向攝影機
- **避免說話**: 錄影期間避免說話或大幅表情變化
- **移除遮擋物**: 取下眼鏡（如有反光）、帽子等可能遮擋面部的物品

### 時間設定
- **最佳時長**: 15-30 秒通常能得到最穩定的結果
- **最短時間**: 不少於 10 秒
- **最長時間**: 不超過 60 秒（較長時間可能影響準確度）

## ⚠️ 注意事項

### 系統需求
- 支援的作業系統：Windows、macOS、Linux
- Python 3.8 或更高版本
- 網路攝影機（內建或外接）
- 穩定的網路連線（使用 VITALLENS API 時）

### 準確度說明
- 此工具僅供健康監測參考，不可用於醫療診斷
- 結果可能受環境因素影響（光線、移動、攝影機品質等）
- 如有健康疑慮，請諮詢專業醫師

### 隱私保護
- 錄製的影片僅在本機暫存，處理完成後會自動刪除
- 使用 VITALLENS API 時，影片會上傳至 VitalLens 服務進行處理
- 不使用 API 的方法（POS、CHROM、G）完全在本機處理

## 🐛 疑難排解

### 攝影機無法使用
```bash
# 檢查攝影機是否被其他應用程式佔用
# 關閉其他可能使用攝影機的程式（如 Skype、Teams 等）

# 在 Python 中測試攝影機
python -c "import cv2; cap = cv2.VideoCapture(0); print('可用' if cap.isOpened() else '不可用'); cap.release()"
```

### 套件安裝問題
```bash
# 重新安裝必要套件
pip install -r requirements.txt

# 如果 OpenCV 有問題，嘗試重新安裝
pip uninstall opencv-python
pip install opencv-python
```

### API Key 錯誤
- 確認 API Key 是否正確輸入
- 檢查 API Key 是否仍然有效
- 確認網路連線正常

### 埠號衝突
如果 7861 埠被佔用，可以修改 `.env` 檔案：
```
GRADIO_SERVER_PORT=8080
```

## 📞 技術支援

如果遇到其他問題：
1. 檢查 `README.md` 中的完整說明
2. 查看 `SETUP_GUIDE.md` 中的安裝指南
3. 確認所有相依套件都已正確安裝

## 🔄 版本差異

| 功能 | 檔案上傳版本 (app.py) | 網路攝影機版本 (webcam_app.py) |
|------|---------------------|------------------------------|
| 輸入方式 | 上傳影片檔案 | 即時錄製攝影機 |
| 預設埠號 | 7860 | 7861 |
| 檔案預覽 | ✅ | ❌ |
| 即時錄影 | ❌ | ✅ |
| 攝影機控制 | ❌ | ✅ |

兩個版本可以同時運行，使用不同的埠號。

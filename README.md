# VitalLens 生命體徵檢測器

基於 [VitalLens Python API](https://github.com/Rouast-Labs/vitallens-python) 的 Web 應用程式。

## 功能

- 影片上傳分析 (MP4, AVI, MOV, MKV, WebM)
- 即時網路攝影機檢測
- 多種檢測方法: VITALLENS, POS, CHROM, G
- WebSocket 即時狀態更新
- Docker 容器化部署

## 🚀 快速開始（Docker部署）

### 1. 環境準備
```bash
# 檢查 Docker 版本
docker --version
docker-compose --version
```

### 2. 設定環境變數
```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案，設定您的 VitalLens API Key
# VITALLENS_API_KEY=your_api_key_here
```

### 3. 啟動服務
```bash
# 啟動所有服務（包含 HTTPS）
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

### 4. 訪問應用
- **HTTPS**: https://localhost:8894 （推薦）
- **健康檢查**: `curl -k https://localhost:8894/health`

### 5. 停止服務
```bash
# 停止服務
docker-compose down

# 停止並清除資料
docker-compose down -v
```

## 架構
- **app**: FastAPI 應用服務
- **proxy**: Nginx HTTPS 反向代理
- 自動生成 SSL 憑證

##  項目結構

```
POC_rPPG/
├── docker/
│   └── Dockerfile           # Python 應用容器定義
├── nginx/
│   ├── nginx.conf          # Nginx 主配置
│   ├── default.conf        # HTTPS 服務配置
│   └── ssl/                # SSL 憑證目錄（自動生成）
├── data/                   # 資料目錄
│   ├── results/            # 分析結果
│   │   ├── upload/        # 上傳影片分析結果
│   │   └── webcam/        # 攝影機分析結果
│   ├── analysis/          # 其他分析資料
│   └── videos/            # 影片相關資料
├── static/                 # 靜態資源
├── templates/              # HTML 模板
├── docker-compose.yml      # 服務編排配置
├── requirements.txt        # Python 依賴
├── app.py                  # 主應用程式（FastAPI + 攝影機功能）
├── backup/                 # 備份目錄
│   ├── gradio_app.py      # Gradio介面版本（備份參考）
│   └── fastapi_frontend.py # FastAPI開發版本（備份參考）
└── .env                    # 環境變數配置
```

## API 說明

### REST API 端點

#### GET `/`
**主頁面**
- 返回 Web 應用程式主介面
- 包含影片上傳和網路攝影機分析功能

#### GET `/health`
**健康檢查**
- 檢查應用程式運行狀態
- 返回: `{"status": "ok", "timestamp": "YYYYMMDD_HHMMSS"}`

#### POST `/api/process-video`
**影片處理**
- 上傳並分析影片檔案
- **參數**:
  - `video` (file): 影片檔案
  - `methods` (list): 檢測方法列表
  - `method` (str): 單一檢測方法
  - `api_key` (str): VitalLens API 金鑰
  - `source` (str): 來源類型，預設 "upload"
- **返回**: 分析結果 JSON

#### WebSocket `/ws/status`
**狀態廣播**
- 實時接收處理狀態更新
- 消息格式: `{"channel": "upload|webcam", "stage": "...", "message": "..."}`

#### POST `/api/webcam/start`
**啟動網路攝影機錄影**
- **參數**:
  - `method` (str): 檢測方法
  - `api_key` (str): API 金鑰
  - `duration` (int): 錄影時間（秒，5-60）
- **返回**: 錄影狀態

#### POST `/api/webcam/stop`
**停止網路攝影機錄影**
- **返回**: 停止狀態

#### GET `/api/webcam/status`
**查詢錄影狀態**
- **返回**: 當前錄影狀態

### 檢測方法說明

| 方法 | API Key | 說明 |
|------|---------|------|
| VITALLENS | 需要 | 商業級精準檢測，支援雲端處理 |
| POS | 免費 | 光流法檢測，適用於一般場景 |
| CHROM | 免費 | 色度法檢測，適合穩定光照環境 |
| G | 免費 | 綠色通道檢測，計算效率高 |

## 開發

### 本地運行
```bash
pip install -r requirements.txt
cp .env.example .env  # 設定 VITALLENS_API_KEY
uvicorn app:app --reload --host 0.0.0.0 --port 8894
```

### 測試
```bash
pytest tests/
```

## 技術棧

- **Backend**: FastAPI, Uvicorn, OpenCV, NumPy
- **Frontend**: HTML5, JavaScript, WebRTC, WebSocket
- **部署**: Docker, Nginx, SSL
- **測試**: pytest

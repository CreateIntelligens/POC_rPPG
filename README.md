# VitalLens 生命體徵檢測器

基於 [VitalLens Python API](https://github.com/Rouast-Labs/vitallens-python) 的網頁應用程式。

## 功能
- 影片上傳分析（MP4, AVI, MOV, MKV, WebM）
- 即時攝影機檢測
- 多種檢測方法：VITALLENS（需API Key）、POS、CHROM、G
- 自動生成波形圖和數據分析

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

## 使用方法
1. 設定 API Key 到 `.env` 檔案
2. 運行 `docker-compose up -d`
3. 訪問 https://localhost:8894
4. 上傳影片或使用攝影機進行檢測

## 技術棧
- FastAPI + Uvicorn
- OpenCV + NumPy
- Matplotlib
- Docker + Nginx
- VitalLens API

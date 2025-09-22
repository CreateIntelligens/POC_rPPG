# =============================================================================
# Dockerfile - VitalLens 應用程式容器化配置
# 定義如何構建包含所有依賴的 Docker 容器來運行 VitalLens 應用程式
# =============================================================================

# 使用 Python 3.9 slim 映像作為基礎映像
FROM python:3.9-slim

# 設定環境變數
# 確保 Python 輸出不被緩衝，方便日誌查看
ENV PYTHONUNBUFFERED=1
# 防止 Python 生成 .pyc 文件，減少容器大小
ENV PYTHONDONTWRITEBYTECODE=1
# 避免 apt-get 安裝時的互動式提示
ENV DEBIAN_FRONTEND=noninteractive

# 安裝系統依賴
# 這些函式庫是 OpenCV、matplotlib 和其他科學計算函式庫所需的
# 安裝必要的系統套件
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    libgl1 \
    ffmpeg \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 創建應用程式目錄
WORKDIR /app

# 安裝 Python 依賴
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

# 暴露應用程式端口
EXPOSE ${APP_PORT:-8894}

# 預設啟動命令（可以在 docker-compose 中覆蓋）
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${APP_PORT:-8894}"]

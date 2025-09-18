#!/bin/bash

echo
echo "==================================================="
echo "🩺 VitalLens 即時生命體徵檢測器 (網路攝影機版本)"
echo "==================================================="
echo

# 檢查虛擬環境是否存在
if [ ! -d "vitallens_venv" ]; then
    echo "❌ 虛擬環境不存在！"
    echo "請先執行 python setup_venv.py 建立虛擬環境"
    echo
    exit 1
fi

# 啟動虛擬環境
echo "📁 啟動虛擬環境..."
source vitallens_venv/bin/activate

# 檢查 Python 是否可用
if ! python --version > /dev/null 2>&1; then
    echo "❌ Python 無法運行！"
    echo "請檢查虛擬環境是否正確安裝"
    exit 1
fi

# 檢查必要套件
echo "🔍 檢查必要套件..."
if ! python -c "import gradio, vitallens, cv2" > /dev/null 2>&1; then
    echo "❌ 缺少必要套件！"
    echo "正在安裝..."
    pip install -r requirements.txt
fi

# 檢查攝影機
echo "📹 檢查攝影機..."
python -c "import cv2; cap = cv2.VideoCapture(0); print('✅ 攝影機可用' if cap.isOpened() else '❌ 攝影機無法使用'); cap.release()" 2>/dev/null

# 檢查設定檔
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 檔案"
    echo "💡 您可以將 config.example.py 重新命名為 .env 並填入 API Key"
    echo
fi

echo
echo "🚀 啟動 VitalLens 即時生命體徵檢測器..."
echo "📡 預設網址: http://localhost:7861"
echo "💡 請確保攝影機已連接且可用"
echo
echo "⚠️  注意事項:"
echo "   - 錄影時請保持靜止並面向攝影機"
echo "   - 確保光線充足且均勻"
echo "   - 建議錄影時間 15-30 秒"
echo

# 執行應用程式
python webcam_app.py

# 如果程式結束，檢查錯誤
if [ $? -ne 0 ]; then
    echo
    echo "❌ 程式執行時發生錯誤"
fi

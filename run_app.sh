#!/bin/bash
echo "🩺 啟動 VitalLens 生命體徵檢測器..."

# 檢查虛擬環境是否存在
if [ -f "vitallens_venv/bin/activate" ]; then
    echo "✅ 找到虛擬環境，正在啟動..."
    source vitallens_venv/bin/activate
    python app.py
else
    echo "⚠️ 未找到虛擬環境，使用全域 Python 環境"
    echo "💡 建議先執行: python setup_venv.py"
    python app.py
fi

echo "🔚 應用程式已關閉"

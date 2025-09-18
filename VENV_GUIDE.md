# VitalLens 虛擬環境使用指南

## 🐍 虛擬環境資訊
- 虛擬環境名稱: vitallens_venv
- Python 版本: 3.13.2
- 作業系統: Windows

## 🚀 啟動方式

### 方法一：使用執行腳本（推薦）

**Windows:**
```batch
# 雙擊執行或在命令提示字元中執行
run_app.bat
```

### 方法二：手動啟動

**Windows:**
```batch
# 1. 啟動虛擬環境
vitallens_venv\Scripts\activate.bat

# 2. 執行應用程式
python app.py

# 3. 關閉虛擬環境（可選）
deactivate
```

## 📦 套件管理

### 安裝新套件
```bash
# 啟動虛擬環境後
pip install package_name
```

### 查看已安裝套件
```bash
pip list
```

### 更新套件
```bash
pip install --upgrade package_name
```

## 🔧 故障排除

### 問題：找不到模組
- 確認已啟動虛擬環境
- 檢查套件是否正確安裝

### 問題：權限錯誤
- 確認有足夠的檔案權限
- 在 Windows 上可能需要以系統管理員身分執行

### 問題：埠號已被使用
- 修改 config.py 中的 SERVER_PORT
- 或關閉佔用埠號的程式

## 📚 相關文件
- [Python venv 官方文件](https://docs.python.org/3/library/venv.html)
- [VitalLens API 文件](https://github.com/Rouast-Labs/vitallens-python)
- [Gradio 文件](https://gradio.app/docs/)

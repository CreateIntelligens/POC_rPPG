# VitalLens Gradio 應用程式設定檔範例
# 複製此檔案為 config.py 並修改相應設定

# VitalLens API 設定
DEFAULT_API_KEY = ""  # 您的預設 API Key，留空則需要在介面中輸入
DEFAULT_METHOD = "POS (免費)"  # 預設檢測方法

# Gradio 伺服器設定
SERVER_PORT = 7860  # 伺服器埠號
SERVER_NAME = "0.0.0.0"  # 伺服器地址，0.0.0.0 允許外部連接
SHARE_GRADIO = False  # 是否啟用 Gradio 公開分享連結

# 介面設定
THEME = "soft"  # Gradio 主題: "default", "soft", "monochrome" 等
TITLE = "VitalLens 生命體徵檢測器"  # 應用程式標題

# 檔案上傳限制
MAX_FILE_SIZE_MB = 100  # 最大檔案大小（MB）
ALLOWED_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".webm"]  # 允許的檔案格式

# 進階設定
ENABLE_QUEUE = True  # 是否啟用佇列系統（建議在多使用者環境下啟用）
MAX_QUEUE_SIZE = 10  # 最大佇列大小

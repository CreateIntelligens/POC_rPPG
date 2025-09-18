import gradio as gr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import tempfile
import json
from vitallens import VitalLens, Method
import cv2
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

class VitalLensApp:
    def __init__(self):
        self.available_methods = {
            "VITALLENS (需要 API Key)": Method.VITALLENS,
            "POS (免費)": Method.POS,
            "CHROM (免費)": Method.CHROM,
            "G (免費)": Method.G
        }
        
        # 從環境變數獲取設定
        self.default_api_key = os.getenv('VITALLENS_API_KEY', '')
        self.default_method = os.getenv('DEFAULT_METHOD', 'POS (免費)')
        self.server_port = int(os.getenv('GRADIO_SERVER_PORT', 7860))
        self.server_name = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')
        self.share_gradio = os.getenv('GRADIO_SHARE', 'false').lower() == 'true'
        self.app_title = os.getenv('APP_TITLE', 'VitalLens 生命體徵檢測器')
        self.app_theme = os.getenv('APP_THEME', 'soft')
    
    def process_video(self, video_file, method_name, api_key):
        """處理上傳的影片並返回生命體徵估算結果"""
        if video_file is None:
            return None, None, "請先上傳影片檔案"
        
        try:
            # 除錯資訊
            print(f"🔍 除錯資訊:")
            print(f"   影片檔案類型: {type(video_file)}")
            print(f"   影片檔案值: {video_file}")
            # 獲取選擇的方法
            method = self.available_methods[method_name]
            
            # 決定要使用的 API Key：優先使用用戶輸入，其次使用環境變數
            effective_api_key = api_key.strip() if api_key else self.default_api_key
            
            # 如果選擇 VITALLENS 但沒有提供 API Key
            if method == Method.VITALLENS and not effective_api_key:
                return None, None, "使用 VITALLENS 方法需要提供 API Key（請在介面輸入或設定 .env 檔案）"
            
            # 初始化 VitalLens
            if method == Method.VITALLENS:
                vl = VitalLens(method=method, api_key=effective_api_key)
            else:
                vl = VitalLens(method=method)
            
            # 處理影片 - 確保路徑是字串格式並且檔案存在
            if hasattr(video_file, '__fspath__'):
                # 如果是路徑物件，轉換為字串
                video_path = os.fspath(video_file)
            elif hasattr(video_file, 'name'):
                # 如果是檔案物件，獲取名稱
                video_path = video_file.name
            else:
                # 否則直接轉換為字串
                video_path = str(video_file)
            
            print(f"   處理後的路徑: {video_path}")
            
            # 檢查檔案是否存在
            if not os.path.exists(video_path):
                return None, None, f"找不到影片檔案: {video_path}"
            
            # 根據官方文件建議，提供影片長度提示
            print(f"💡 提示: 根據 VitalLens 官方文件:")
            print(f"   - 心率估算需要至少 5 秒的影片")
            print(f"   - 呼吸率估算需要至少 10 秒的影片")
            print(f"   - 連續生命體徵需要更長的影片（10-30 秒）")
            
            print(f"🎥 開始處理影片: {os.path.basename(video_path)}")
            result = vl(video_path)
            print(f"✅ 影片處理完成")
            
            # 格式化結果
            formatted_result = self.format_results(result)
            
            # 生成圖表
            plot_fig = self.create_plots(result)
            
            return plot_fig, formatted_result, "處理完成！"
            
        except Exception as e:
            error_msg = f"處理錯誤: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"   錯誤類型: {type(e).__name__}")
            import traceback
            print(f"   完整錯誤追蹤:")
            traceback.print_exc()
            return None, None, error_msg
    
    def format_results(self, results):
        """格式化結果為易讀的文字"""
        if not results:
            return "沒有檢測到結果"
        
        formatted_text = ""
        
        for i, face_result in enumerate(results):
            formatted_text += f"=== 人臉 {i+1} ===\n\n"
            
            # 人臉信息
            face_info = face_result.get('face', {})
            formatted_text += f"人臉置信度: {face_info.get('note', '未知')}\n\n"
            
            # 生命體徵
            vital_signs = face_result.get('vital_signs', {})
            
            # 心率
            if 'heart_rate' in vital_signs:
                hr = vital_signs['heart_rate']
                formatted_text += f"心率: {hr.get('value', 'N/A')} {hr.get('unit', 'bpm')}\n"
                formatted_text += f"心率置信度: {hr.get('confidence', 'N/A')}\n"
                formatted_text += f"備註: {hr.get('note', '')}\n\n"
            
            # 呼吸率
            if 'respiratory_rate' in vital_signs:
                rr = vital_signs['respiratory_rate']
                formatted_text += f"呼吸率: {rr.get('value', 'N/A')} {rr.get('unit', 'rpm')}\n"
                formatted_text += f"呼吸率置信度: {rr.get('confidence', 'N/A')}\n"
                formatted_text += f"備註: {rr.get('note', '')}\n\n"
            
            # PPG 波形信息
            if 'ppg_waveform' in vital_signs:
                ppg = vital_signs['ppg_waveform']
                ppg_data = ppg.get('data', [])
                if len(ppg_data) > 0:
                    formatted_text += f"PPG 波形: {len(ppg_data)} 個數據點\n"
                    formatted_text += f"PPG 單位: {ppg.get('unit', '')}\n\n"
            
            # 呼吸波形信息
            if 'respiratory_waveform' in vital_signs:
                resp = vital_signs['respiratory_waveform']
                resp_data = resp.get('data', [])
                if len(resp_data) > 0:
                    formatted_text += f"呼吸波形: {len(resp_data)} 個數據點\n"
                    formatted_text += f"呼吸波形單位: {resp.get('unit', '')}\n\n"
            
            # 滾動心率
            if 'rolling_heart_rate' in vital_signs:
                rhr = vital_signs['rolling_heart_rate']
                rhr_data = rhr.get('data', [])
                if len(rhr_data) > 0:
                    formatted_text += f"連續心率: {len(rhr_data)} 個數據點\n"
                    formatted_text += f"平均心率: {np.mean(rhr_data):.1f} {rhr.get('unit', 'bpm')}\n\n"
            
            # 滾動呼吸率
            if 'rolling_respiratory_rate' in vital_signs:
                rrr = vital_signs['rolling_respiratory_rate']
                rrr_data = rrr.get('data', [])
                if len(rrr_data) > 0:
                    formatted_text += f"連續呼吸率: {len(rrr_data)} 個數據點\n"
                    formatted_text += f"平均呼吸率: {np.mean(rrr_data):.1f} {rrr.get('unit', 'rpm')}\n\n"
            
            # 消息
            if 'message' in face_result:
                formatted_text += f"系統消息: {face_result['message']}\n\n"
        
        return formatted_text
    
    def create_plots(self, results):
        """創建結果圖表"""
        if not results:
            return None
        
        # 計算需要的子圖數量
        num_faces = len(results)
        
        # 創建圖表
        fig, axes = plt.subplots(2 * num_faces, 2, figsize=(15, 6 * num_faces))
        
        if num_faces == 1:
            axes = axes.reshape(2, 2)
        
        for i, face_result in enumerate(results):
            vital_signs = face_result.get('vital_signs', {})
            
            # PPG 波形
            if 'ppg_waveform' in vital_signs:
                ppg_data = vital_signs['ppg_waveform'].get('data', [])
                if len(ppg_data) > 0:
                    axes[i*2, 0].plot(ppg_data)
                    axes[i*2, 0].set_title(f'人臉 {i+1} - PPG 波形')
                    axes[i*2, 0].set_xlabel('幀數')
                    axes[i*2, 0].set_ylabel(vital_signs['ppg_waveform'].get('unit', ''))
                    axes[i*2, 0].grid(True)
            
            # 呼吸波形
            if 'respiratory_waveform' in vital_signs:
                resp_data = vital_signs['respiratory_waveform'].get('data', [])
                if len(resp_data) > 0:
                    axes[i*2, 1].plot(resp_data)
                    axes[i*2, 1].set_title(f'人臉 {i+1} - 呼吸波形')
                    axes[i*2, 1].set_xlabel('幀數')
                    axes[i*2, 1].set_ylabel(vital_signs['respiratory_waveform'].get('unit', ''))
                    axes[i*2, 1].grid(True)
            
            # 連續心率
            if 'rolling_heart_rate' in vital_signs:
                rhr_data = vital_signs['rolling_heart_rate'].get('data', [])
                if len(rhr_data) > 0:
                    axes[i*2+1, 0].plot(rhr_data)
                    axes[i*2+1, 0].set_title(f'人臉 {i+1} - 連續心率')
                    axes[i*2+1, 0].set_xlabel('幀數')
                    axes[i*2+1, 0].set_ylabel(vital_signs['rolling_heart_rate'].get('unit', 'bpm'))
                    axes[i*2+1, 0].grid(True)
            
            # 連續呼吸率
            if 'rolling_respiratory_rate' in vital_signs:
                rrr_data = vital_signs['rolling_respiratory_rate'].get('data', [])
                if len(rrr_data) > 0:
                    axes[i*2+1, 1].plot(rrr_data)
                    axes[i*2+1, 1].set_title(f'人臉 {i+1} - 連續呼吸率')
                    axes[i*2+1, 1].set_xlabel('幀數')
                    axes[i*2+1, 1].set_ylabel(vital_signs['rolling_respiratory_rate'].get('unit', 'rpm'))
                    axes[i*2+1, 1].grid(True)
        
        plt.tight_layout()
        return fig

def create_interface():
    app = VitalLensApp()
    
    # 根據環境變數選擇主題
    theme_map = {
        'soft': gr.themes.Soft(),
        'default': gr.themes.Default(),
        'monochrome': gr.themes.Monochrome()
    }
    selected_theme = theme_map.get(app.app_theme.lower(), gr.themes.Soft())
    
    with gr.Blocks(title=app.app_title, theme=selected_theme) as interface:
        gr.Markdown("""
        # 🩺 VitalLens 生命體徵檢測器
        
        上傳影片檔案，使用 VitalLens API 或其他方法來估算心率、呼吸率等生命體徵。
        
        ## 支援的方法：
        - **VITALLENS**: 最準確，支援心率、呼吸率、脈搏波形、呼吸波形（需要 API Key）
        - **POS**: 免費方法，支援心率和脈搏波形
        - **CHROM**: 免費方法，支援心率和脈搏波形  
        - **G**: 免費方法，支援心率和脈搏波形
        
        ⚠️ **免責聲明**: 此工具僅供一般健康參考，不可用於醫療診斷。如有健康疑慮請諮詢醫師。
        """)
        
        with gr.Row():
            with gr.Column():
                # 輸入區域
                video_input = gr.File(
                    label="上傳影片檔案",
                    file_types=[".mp4", ".avi", ".mov", ".mkv", ".webm"],
                    type="filepath"
                )
                
                method_dropdown = gr.Dropdown(
                    choices=list(app.available_methods.keys()),
                    value=app.default_method,
                    label="選擇檢測方法"
                )
                
                # 顯示 API Key 狀態
                api_key_status = "✅ 已從 .env 檔案載入 API Key" if app.default_api_key else "❌ 未設定 API Key"
                
                api_key_input = gr.Textbox(
                    label=f"API Key (使用 VITALLENS 時必填) - {api_key_status}",
                    placeholder="請輸入您的 VitalLens API Key 或設定 .env 檔案",
                    type="password",
                    value=""  # 不顯示實際的 API Key
                )
                
                process_btn = gr.Button("🔍 開始分析", variant="primary", size="lg")
                
                # 狀態訊息
                status_text = gr.Textbox(
                    label="處理狀態",
                    value="等待上傳影片...",
                    interactive=False
                )
            
            with gr.Column():
                # 輸出區域
                result_plots = gr.Plot(
                    label="生命體徵波形圖",
                    show_label=True
                )
                
                result_text = gr.Textbox(
                    label="檢測結果",
                    lines=15,
                    max_lines=20,
                    interactive=False
                )
        
        # 事件處理
        process_btn.click(
            fn=app.process_video,
            inputs=[video_input, method_dropdown, api_key_input],
            outputs=[result_plots, result_text, status_text]
        )
        
        # 範例影片資訊
        gr.Markdown("""
        ## 📋 使用說明：
        
        1. **上傳影片**: 支援常見格式（MP4, AVI, MOV, MKV, WebM）
        2. **影片要求**（依據 [官方文件](https://docs.rouast.com/python/)）:
           - 心率估算: 至少 **5 秒**
           - 呼吸率估算: 至少 **10 秒** (僅 VITALLENS)
           - 連續生命體徵: **10-30 秒** 或更長
           - 需要清晰可見的人臉
        3. **選擇方法**: 
           - 有 API Key → VITALLENS（最準確，支援呼吸率）
           - 沒有 API Key → POS、CHROM 或 G（僅心率）
        4. **輸入 API Key**: 僅在使用 VITALLENS 時需要
        5. **開始分析**: 點擊按鈕處理影片
        
        ## 🔧 API Key 設定：
        
        **方法一：使用 .env 檔案（推薦）**
        1. 將 `env.example` 重新命名為 `.env`
        2. 編輯 `.env` 檔案，填入您的 API Key：`VITALLENS_API_KEY=your_actual_api_key`
        3. 重新啟動應用程式
        
        **方法二：在介面中輸入**
        1. 訪問 [VitalLens API 網站](https://www.rouast.com/api/) 註冊免費帳號
        2. 獲取 API Key 後在下方輸入框中填入
        
        ## 📊 結果說明：
        - **心率**: 每分鐘心跳次數（bpm）
        - **呼吸率**: 每分鐘呼吸次數（rpm）
        - **PPG 波形**: 光體積描記法信號，反映血液體積變化
        - **呼吸波形**: 呼吸模式的時間序列數據
        - **連續數據**: 整個影片期間的連續測量值
        """)
    
    return interface

if __name__ == "__main__":
    # 啟動介面
    interface = create_interface()
    
    # 從環境變數或 VitalLensApp 實例獲取設定
    app_instance = VitalLensApp()
    
    print("🩺 啟動 VitalLens 生命體徵檢測器...")
    print(f"📡 伺服器: {app_instance.server_name}:{app_instance.server_port}")
    if app_instance.default_api_key:
        print("✅ 已載入 API Key（來自 .env 檔案）")
    else:
        print("⚠️ 未設定 API Key，請在介面中輸入或設定 .env 檔案")
    
    interface.launch(
        share=app_instance.share_gradio,
        server_name=app_instance.server_name,
        server_port=app_instance.server_port,
        show_error=True
    )

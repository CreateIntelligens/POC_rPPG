import gradio as gr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import tempfile
import json
import cv2
import time
import threading
from datetime import datetime
from vitallens import VitalLens, Method
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

class WebcamVitalLensApp:
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
        self.server_port = int(os.getenv('GRADIO_SERVER_PORT', 7861))  # 使用不同的預設埠
        self.server_name = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')
        self.share_gradio = os.getenv('GRADIO_SHARE', 'false').lower() == 'true'
        self.app_title = os.getenv('APP_TITLE', 'VitalLens 即時生命體徵檢測器')
        self.app_theme = os.getenv('APP_THEME', 'soft')
        
        # 錄影相關變數
        self.is_recording = False
        self.recorded_frames = []
        self.output_video_path = None
        self.fps = 30
        self.recording_thread = None
        
        # 即時檢測相關變數
        self.is_processing = False
        self.frame_buffer = []
        self.buffer_size = 300  # 約10秒的影片（30fps）
        self.processing_interval = 150  # 每5秒處理一次
        
    def start_recording(self, method_name, api_key, recording_duration):
        """開始錄影並準備處理"""
        if self.is_recording:
            return "錄影中...", None, None, "正在錄影中，請等待完成"
        
        try:
            duration = int(recording_duration) if recording_duration else 10
            if duration < 5 or duration > 60:
                return "錄影準備中", None, None, "錄影時間必須在 5-60 秒之間"
            
            # 重置狀態
            self.recorded_frames = []
            self.is_recording = True
            
            # 建立暫存檔案路徑
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_video_path = os.path.join(tempfile.gettempdir(), f"vitallens_webcam_{timestamp}.mp4")
            
            # 開始錄影執行緒
            self.recording_thread = threading.Thread(
                target=self._record_video_thread,
                args=(duration, method_name, api_key)
            )
            self.recording_thread.start()
            
            return f"開始錄影 {duration} 秒...", None, None, "錄影中，請保持靜止並面向攝影機"
            
        except Exception as e:
            self.is_recording = False
            return "錄影準備中", None, None, f"啟動錯誤: {str(e)}"
    
    def _record_video_thread(self, duration, method_name, api_key):
        """錄影執行緒"""
        try:
            # 初始化攝影機
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.is_recording = False
                return
            
            # 設定攝影機參數
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            frames = []
            start_time = time.time()
            
            while self.is_recording and (time.time() - start_time) < duration:
                ret, frame = cap.read()
                if ret:
                    frames.append(frame.copy())
                time.sleep(1/self.fps)  # 控制幀率
            
            cap.release()
            
            if frames:
                # 儲存影片
                self._save_video(frames)
                
                # 處理影片
                if os.path.exists(self.output_video_path):
                    self._process_recorded_video(method_name, api_key)
            
        except Exception as e:
            print(f"錄影錯誤: {e}")
        finally:
            self.is_recording = False
    
    def _save_video(self, frames):
        """儲存錄製的影片"""
        if not frames:
            return
        
        height, width, layers = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        out = cv2.VideoWriter(self.output_video_path, fourcc, self.fps, (width, height))
        
        for frame in frames:
            out.write(frame)
        
        out.release()
    
    def _process_recorded_video(self, method_name, api_key):
        """處理錄製的影片"""
        try:
            if not os.path.exists(self.output_video_path):
                return
            
            # 使用原有的影片處理邏輯
            plot_fig, formatted_result, status = self.process_video(
                self.output_video_path, method_name, api_key
            )
            
            # 這裡需要更新UI，但由於在子執行緒中，需要特殊處理
            # 暫時將結果儲存，讓主執行緒檢查
            self.last_processing_result = {
                'plot': plot_fig,
                'result': formatted_result,
                'status': status
            }
            
        except Exception as e:
            self.last_processing_result = {
                'plot': None,
                'result': None,
                'status': f"處理錯誤: {str(e)}"
            }
    
    def stop_recording(self):
        """停止錄影"""
        if self.is_recording:
            self.is_recording = False
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2)
            return "錄影已停止", None, None, "錄影已停止，正在處理..."
        return "錄影準備中", None, None, "目前沒有在錄影"
    
    def check_recording_status(self):
        """檢查錄影狀態"""
        if self.is_recording:
            return "錄影中...", None, None, "正在錄影，請保持靜止..."
        elif hasattr(self, 'last_processing_result'):
            # 如果有處理結果，返回它
            result = self.last_processing_result
            delattr(self, 'last_processing_result')  # 清除結果避免重複顯示
            return "錄影完成", result['plot'], result['result'], result['status']
        else:
            return "錄影準備中", None, None, "準備開始錄影..."
    
    def process_video(self, video_file, method_name, api_key):
        """處理影片並返回生命體徵估算結果（與原有的相同）"""
        if video_file is None or not os.path.exists(video_file):
            return None, None, "影片檔案不存在"
        
        try:
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
            
            # 處理影片
            result = vl(video_file)
            
            # 格式化結果
            formatted_result = self.format_results(result)
            
            # 生成圖表
            plot_fig = self.create_plots(result)
            
            return plot_fig, formatted_result, "處理完成！"
            
        except Exception as e:
            return None, None, f"處理錯誤: {str(e)}"
    
    def format_results(self, results):
        """格式化結果為易讀的文字（與原有的相同）"""
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
        """創建結果圖表（與原有的相同）"""
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

def create_webcam_interface():
    app = WebcamVitalLensApp()
    
    # 根據環境變數選擇主題
    theme_map = {
        'soft': gr.themes.Soft(),
        'default': gr.themes.Default(),
        'monochrome': gr.themes.Monochrome()
    }
    selected_theme = theme_map.get(app.app_theme.lower(), gr.themes.Soft())
    
    with gr.Blocks(title=app.app_title, theme=selected_theme) as interface:
        gr.Markdown("""
        # 📹 VitalLens 即時生命體徵檢測器
        
        使用網路攝影機即時錄製影片，並使用 VitalLens API 或其他方法來估算心率、呼吸率等生命體徵。
        
        ## 支援的方法：
        - **VITALLENS**: 最準確，支援心率、呼吸率、脈搏波形、呼吸波形（需要 API Key）
        - **POS**: 免費方法，支援心率和脈搏波形
        - **CHROM**: 免費方法，支援心率和脈搏波形  
        - **G**: 免費方法，支援心率和脈搏波形
        
        ⚠️ **免責聲明**: 此工具僅供一般健康參考，不可用於醫療診斷。如有健康疑慮請諮詢醫師。
        """)
        
        with gr.Row():
            with gr.Column():
                # 控制區域
                gr.Markdown("### 🎥 攝影機控制")
                
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
                    value=""
                )
                
                recording_duration = gr.Slider(
                    minimum=5,
                    maximum=60,
                    value=15,
                    step=5,
                    label="錄影時間（秒）",
                    info="建議 10-30 秒以獲得最佳結果"
                )
                
                with gr.Row():
                    start_btn = gr.Button("🔴 開始錄影", variant="primary", size="lg")
                    stop_btn = gr.Button("⏹️ 停止錄影", variant="secondary", size="lg")
                
                # 狀態訊息
                status_text = gr.Textbox(
                    label="狀態",
                    value="準備開始錄影...",
                    interactive=False
                )
                
                # 即時預覽（可選，需要更複雜的實作）
                webcam_preview = gr.Image(
                    label="網路攝影機預覽",
                    source="webcam",
                    interactive=True,
                    type="numpy"
                )
            
            with gr.Column():
                # 結果區域
                gr.Markdown("### 📊 檢測結果")
                
                result_plots = gr.Plot(
                    label="生命體徵波形圖",
                    show_label=True
                )
                
                result_text = gr.Textbox(
                    label="詳細結果",
                    lines=15,
                    max_lines=20,
                    interactive=False
                )
        
        # 事件處理
        start_btn.click(
            fn=app.start_recording,
            inputs=[method_dropdown, api_key_input, recording_duration],
            outputs=[status_text, result_plots, result_text, status_text]
        )
        
        stop_btn.click(
            fn=app.stop_recording,
            inputs=[],
            outputs=[status_text, result_plots, result_text, status_text]
        )
        
        # 定期檢查狀態（每2秒）
        interface.load(
            fn=app.check_recording_status,
            inputs=[],
            outputs=[status_text, result_plots, result_text, status_text],
            every=2
        )
        
        # 使用說明
        gr.Markdown("""
        ## 📋 使用說明：
        
        1. **選擇檢測方法**: 根據是否有 API Key 選擇合適的方法
        2. **輸入 API Key**: 僅在使用 VITALLENS 時需要（可設定在 .env 檔案中）
        3. **設定錄影時間**: 建議 10-30 秒，太短可能影響準確度
        4. **開始錄影**: 點擊紅色按鈕開始錄影
        5. **保持靜止**: 錄影期間請面向攝影機並保持靜止
        6. **查看結果**: 錄影完成後系統會自動分析並顯示結果
        
        ## 💡 獲得最佳效果的秘訣：
        
        - **良好光線**: 確保面部有充足且均勻的光線
        - **保持靜止**: 盡量減少頭部移動和說話
        - **面向攝影機**: 確保臉部正面朝向攝影機
        - **適當距離**: 距離攝影機約 50-100 公分
        - **避免遮擋**: 確保臉部沒有被眼鏡反光、頭髮或其他物品遮擋
        - **錄影時間**: 15-30 秒通常能得到最穩定的結果
        
        ## 🔧 API Key 設定：
        
        **方法一：使用 .env 檔案（推薦）**
        1. 將 `config.example.py` 重新命名為 `.env`
        2. 編輯 `.env` 檔案，填入：`VITALLENS_API_KEY=your_actual_api_key`
        3. 重新啟動應用程式
        
        **方法二：在介面中輸入**
        1. 訪問 [VitalLens API 網站](https://www.rouast.com/api/)
        2. 註冊免費帳號並獲取 API Key
        3. 在上方輸入框中填入 API Key
        """)
    
    return interface

if __name__ == "__main__":
    # 啟動介面
    interface = create_webcam_interface()
    
    # 從環境變數或實例獲取設定
    app_instance = WebcamVitalLensApp()
    
    print("📹 啟動 VitalLens 即時生命體徵檢測器...")
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

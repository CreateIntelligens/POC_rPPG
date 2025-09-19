# =============================================================================
# app.py - VitalLens 生命體徵檢測器主應用程式
# 基於 FastAPI 的 Web 應用程式，提供生命體徵檢測功能
# 支援影片上傳處理和網路攝影機即時錄影分析
# 依賴 VitalLens 函式庫進行心率和呼吸率檢測
# =============================================================================

import base64
import io
import json
import os
import tempfile
import threading
import time
from datetime import datetime
from typing import Dict, Optional

import cv2
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from vitallens import Method, VitalLens

# Load environment variables from .env if present
load_dotenv()


def _now_ts() -> str:
    """
    生成檔案名稱用的時間戳記。

    Returns:
        str: 格式為 YYYYMMDD_HHMMSS 的時間戳記字串

    Example:
        >>> ts = _now_ts()
        >>> print(ts)
        20250919_163655
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class VitalLensService:
    """
    VitalLens 生命體徵檢測服務核心類別。

    此類別封裝了 VitalLens 處理和網路攝影機錄影的所有狀態和功能，
    提供統一的介面來處理影片分析、網路攝影機控制和結果格式化。

    Attributes:
        available_methods (Dict[str, Method]): 可用的檢測方法映射
        default_api_key (str): 預設的 VitalLens API 金鑰
        default_method (str): 預設的檢測方法
        app_title (str): 應用程式標題

    Note:
        此類別使用執行緒鎖來確保網路攝影機操作的執行緒安全。
        所有網路攝影機相關操作都在背景執行緒中執行。
    """

    def __init__(self) -> None:
        """
        初始化 VitalLensService 實例。

        從環境變數載入配置，設定可用的檢測方法，並初始化網路攝影機錄影狀態。

        Attributes:
            available_methods: 支援的生命體徵檢測方法映射
            default_api_key: 從環境變數 VITALLENS_API_KEY 載入的預設 API 金鑰
            default_method: 從環境變數 DEFAULT_METHOD 載入的預設檢測方法
            app_title: 應用程式標題
            _lock: 執行緒鎖，用於保護網路攝影機操作的執行緒安全
            _is_recording: 網路攝影機是否正在錄影的狀態標記
            _recording_thread: 網路攝影機錄影背景執行緒
            _output_video_path: 錄影輸出影片檔案路徑
            _last_result: 最後一次處理結果
            _status_message: 當前狀態訊息
            _fps: 網路攝影機錄影幀率 (預設 30 FPS)
        """
        self.available_methods: Dict[str, Method] = {
            "VITALLENS (需要 API Key)": Method.VITALLENS,
            "POS (免費)": Method.POS,
            "CHROM (免費)": Method.CHROM,
            "G (免費)": Method.G,
        }

        self.default_api_key: str = os.getenv("VITALLENS_API_KEY", "")
        self.default_method: str = os.getenv("DEFAULT_METHOD", "POS (免費)")
        self.app_title: str = os.getenv("APP_TITLE", "VitalLens 生命體徵檢測器")

        # Webcam recording state
        self._lock = threading.Lock()
        self._is_recording = False
        self._recording_thread: Optional[threading.Thread] = None
        self._output_video_path: Optional[str] = None
        self._last_result: Optional[Dict[str, Optional[str]]] = None
        self._status_message = "準備開始錄影..."
        self._fps = 30

    # ------------------------------------------------------------------
    # Video processing helpers
    # ------------------------------------------------------------------
    def process_video(self, video_path: str, method_name: str, api_key: str) -> Dict[str, Optional[str]]:
        """
        處理影片檔案並返回分析結果。

        使用指定的檢測方法處理影片，提取生命體徵數據，並生成可視化圖表。

        Args:
            video_path (str): 要處理的影片檔案路徑
            method_name (str): 檢測方法名稱 (例如: "POS (免費)", "VITALLENS (需要 API Key)")
            api_key (str): VitalLens API 金鑰 (如果使用 VITALLENS 方法)

        Returns:
            Dict[str, Optional[str]]: 處理結果字典，包含:
                - status: 處理狀態訊息
                - result_text: 格式化的結果文字
                - plot_image: Base64 編碼的圖表圖片 (可選)

        Raises:
            FileNotFoundError: 當影片檔案不存在時
            ValueError: 當檢測方法無效或缺少必要參數時
            RuntimeError: 當處理過程中發生錯誤時

        Example:
            >>> result = service.process_video("video.mp4", "POS (免費)", "")
            >>> print(result["status"])
            處理完成！
        """
        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError(f"找不到影片檔案: {video_path}")

        method = self._resolve_method(method_name)
        effective_api_key = api_key.strip() if api_key else self.default_api_key

        if method == Method.VITALLENS and not effective_api_key:
            raise ValueError("使用 VITALLENS 方法需要提供 API Key")

        try:
            if method == Method.VITALLENS:
                vital_lens = VitalLens(method=method, api_key=effective_api_key)
            else:
                vital_lens = VitalLens(method=method)

            result = vital_lens(video_path)

            # 清理 VitalLens 在根目錄產生的臨時檔案
            self._cleanup_vitallens_temp_files()

            # 保存分析結果JSON到temp目錄
            json_path = self._save_analysis_result(result, video_path)

            # 檢查結果是否為空或無效
            if not result or (isinstance(result, list) and len(result) == 0):
                return {
                    "status": "Processing Failed",
                    "result_text": "Unable to detect valid facial or vital sign data from the video.\n\nPlease confirm:\n- Video contains clearly visible face\n- Adequate lighting\n- Video duration is at least 5 seconds",
                    "plot_image": None,
                }

            formatted_text = self.format_results(result)
            plot_fig = self.create_plots(result)
            plot_image = self.figure_to_base64(plot_fig)

            return {
                "status": "Processing Complete!",
                "result_text": formatted_text,
                "plot_image": plot_image,
            }

        except Exception as exc:  # pylint: disable=broad-except
            import traceback
            error_traceback = traceback.format_exc()
            print(f"詳細錯誤堆棧: {error_traceback}")

            error_message = str(exc)

            # 針對常見錯誤提供更友好的提示
            if "truth value of an array" in error_message:
                error_message = "Video processing encountered data analysis issues. Possible causes:\n- Video too short (recommend at least 10 seconds)\n- Face not clear enough\n- Poor lighting conditions\nPlease record a longer, clearer video"
            elif "Problem probing video" in error_message and "NoneType" in error_message:
                error_message = "Video format compatibility issue. This may occur with certain WebM files.\nTry converting to MP4 format or use a different video file."
            elif "No face detected" in error_message:
                error_message = "No face detected. Please ensure camera is facing the face with adequate lighting"
            elif "API" in error_message and "key" in error_message:
                error_message = "API Key error or quota exceeded. Please check your VitalLens API settings"

            raise RuntimeError(f"處理錯誤: {error_message}") from exc

    def _cleanup_vitallens_temp_files(self):
        """清理 VitalLens 在根目錄產生的臨時檔案"""
        try:
            import glob
            # 清理根目錄中的 vitallens_*.json 檔案
            temp_files = glob.glob("vitallens_*.json")
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    print(f"🗑️ 已清理臨時檔案: {temp_file}")
                except Exception as e:
                    print(f"⚠️ 清理檔案失敗 {temp_file}: {e}")
        except Exception as e:
            print(f"⚠️ 清理過程出錯: {e}")

    def _save_analysis_result(self, result, video_path: str) -> str:
        """統一保存分析結果JSON"""
        timestamp = _now_ts()

        # 根據視頻路徑判斷來源類型和存放目錄
        if "webcam" in video_path:
            prefix = "webcam_analysis"
            result_dir = "data/results/webcam"
        elif "upload" in video_path:
            prefix = "upload_analysis"
            result_dir = "data/results/upload"
        else:
            prefix = "analysis_result"
            result_dir = "data/results/upload"  # 默認放upload

        json_filename = f"{prefix}_{timestamp}.json"
        json_path = os.path.join(result_dir, json_filename)

        # 確保結果目錄存在
        os.makedirs(result_dir, exist_ok=True)

        try:
            # 創建更詳細的JSON結構
            analysis_data = {
                "timestamp": timestamp,
                "video_source": "webcam" if "webcam" in video_path else "upload",
                "video_path": video_path,
                "raw_result": result,
                "summary": {
                    "faces_detected": len(result) if isinstance(result, list) else 0,
                    "processing_status": "success"
                }
            }

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"✅ 分析結果已保存: {json_path}")
            return json_path

        except Exception as e:
            print(f"❌ JSON保存失敗: {e}")
            return ""

    def _resolve_method(self, method_name: str) -> Method:
        if method_name not in self.available_methods:
            raise ValueError(f"未知的檢測方法: {method_name}")
        return self.available_methods[method_name]

    # ------------------------------------------------------------------
    # Webcam helpers
    # ------------------------------------------------------------------
    def start_webcam_recording(self, method_name: str, api_key: str, duration: int) -> Dict[str, str]:
        with self._lock:
            if self._is_recording:
                return {"state": "recording", "message": "正在錄影中，請稍候..."}

            duration = int(duration) if duration else 10
            if duration < 5 or duration > 60:
                raise ValueError("錄影時間必須在 5-60 秒之間")

            self._is_recording = True
            self._status_message = f"開始錄影 {duration} 秒..."
            # 確保影片目錄存在
            os.makedirs("data/videos", exist_ok=True)
            self._output_video_path = os.path.join(
                "data/videos", f"vitallens_webcam_{_now_ts()}.mp4"
            )
            self._recording_thread = threading.Thread(
                target=self._record_webcam_thread,
                args=(duration, method_name, api_key),
                daemon=True,
            )
            self._recording_thread.start()

            return {"state": "recording", "message": self._status_message}

    def stop_webcam_recording(self) -> Dict[str, str]:
        with self._lock:
            if not self._is_recording:
                return {"state": "idle", "message": "目前沒有在錄影"}

            self._is_recording = False
            thread = self._recording_thread

        if thread and thread.is_alive():
            thread.join(timeout=2)

        return {"state": "stopping", "message": "錄影已停止，正在處理..."}

    def check_recording_status(self) -> Dict[str, Optional[str]]:
        with self._lock:
            if self._is_recording:
                return {"state": "recording", "message": "錄影中，請保持靜止..."}

            if self._last_result:
                result = self._last_result
                self._last_result = None
                return {
                    "state": "completed",
                    "message": result.get("status", "處理完成！"),
                    "result_text": result.get("result_text"),
                    "plot_image": result.get("plot_image"),
                }

            return {"state": "idle", "message": self._status_message}

    def _record_webcam_thread(self, duration: int, method_name: str, api_key: str) -> None:
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise RuntimeError("無法開啟網路攝影機")

            # 設定較高解析度並保持比例
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, self._fps)

            # 檢查實際解析度
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"📹 Webcam resolution: {actual_width}x{actual_height}")

            frames = []
            start_time = time.time()

            while True:
                with self._lock:
                    if not self._is_recording:
                        break

                if time.time() - start_time >= duration:
                    break

                success, frame = cap.read()
                if not success:
                    continue
                # 水平翻轉以提供鏡像效果，更符合使用者習慣
                frame = cv2.flip(frame, 1)
                frames.append(frame.copy())
                time.sleep(1 / self._fps)

            cap.release()

            if not frames:
                raise RuntimeError("未捕捉到任何畫面，請檢查攝影機")

            print(f"📽️ Captured {len(frames)} frames")

            if self._output_video_path:
                self._save_video(frames, self._output_video_path)
                print(f"💾 Video saved to: {self._output_video_path}")
                result = self.process_video(self._output_video_path, method_name, api_key)
            else:
                raise RuntimeError("找不到輸出檔案路徑")

            with self._lock:
                self._last_result = result
                self._status_message = "錄影完成"

        except Exception as exc:  # pylint: disable=broad-except
            with self._lock:
                self._last_result = {
                    "status": f"處理錯誤: {exc}",
                    "result_text": None,
                    "plot_image": None,
                }
                self._status_message = f"處理錯誤: {exc}"
        finally:
            with self._lock:
                self._is_recording = False

    def _save_video(self, frames: list[np.ndarray], output_path: str) -> None:
        height, width, _ = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, self._fps, (width, height))
        for frame in frames:
            writer.write(frame)
        writer.release()

    # ------------------------------------------------------------------
    # Result formatting helpers
    # ------------------------------------------------------------------
    def format_results(self, results: Optional[list]) -> str:
        if not results:
            return "No detection results"

        formatted_text = []
        for idx, face_result in enumerate(results, start=1):
            formatted_text.append(f"=== Face {idx} ===\n")

            face_info = face_result.get("face", {})
            formatted_text.append(f"Face Confidence: {face_info.get('note', 'Unknown')}\n\n")

            vital_signs = face_result.get("vital_signs", {})

            if "heart_rate" in vital_signs:
                hr = vital_signs["heart_rate"]
                formatted_text.append(
                    f"Heart Rate: {hr.get('value', 'N/A')} {hr.get('unit', 'bpm')}\n"
                )
                formatted_text.append(f"HR Confidence: {hr.get('confidence', 'N/A')}\n")
                formatted_text.append(f"Note: {hr.get('note', '')}\n\n")

            if "respiratory_rate" in vital_signs:
                rr = vital_signs["respiratory_rate"]
                formatted_text.append(
                    f"Respiratory Rate: {rr.get('value', 'N/A')} {rr.get('unit', 'rpm')}\n"
                )
                formatted_text.append(f"RR Confidence: {rr.get('confidence', 'N/A')}\n")
                formatted_text.append(f"Note: {rr.get('note', '')}\n\n")

            if "ppg_waveform" in vital_signs:
                ppg = vital_signs["ppg_waveform"].get("data", [])
                if ppg is not None and len(ppg) > 0:
                    formatted_text.append(f"PPG Waveform: {len(ppg)} data points\n\n")

            if "respiratory_waveform" in vital_signs:
                resp = vital_signs["respiratory_waveform"].get("data", [])
                if resp is not None and len(resp) > 0:
                    formatted_text.append(f"Respiratory Waveform: {len(resp)} data points\n\n")

            if "rolling_heart_rate" in vital_signs:
                rhr = vital_signs["rolling_heart_rate"].get("data", [])
                if rhr is not None and len(rhr) > 0:
                    formatted_text.append(
                        f"Rolling Heart Rate: {len(rhr)} data points\nAverage HR: {np.mean(rhr):.1f} {vital_signs['rolling_heart_rate'].get('unit', 'bpm')}\n\n"
                    )

            if "rolling_respiratory_rate" in vital_signs:
                rrr = vital_signs["rolling_respiratory_rate"].get("data", [])
                if rrr is not None and len(rrr) > 0:
                    formatted_text.append(
                        f"Rolling Respiratory Rate: {len(rrr)} data points\nAverage RR: {np.mean(rrr):.1f} {vital_signs['rolling_respiratory_rate'].get('unit', 'rpm')}\n\n"
                    )

            if "message" in face_result:
                formatted_text.append(f"System Message: {face_result['message']}\n\n")

        return "".join(formatted_text)

    def create_plots(self, results: Optional[list]):
        if not results:
            return None

        num_faces = len(results)
        fig, axes = plt.subplots(2 * num_faces, 2, figsize=(14, 6 * num_faces))

        if num_faces == 1:
            axes = axes.reshape(2, 2)

        for idx, face_result in enumerate(results):
            vital_signs = face_result.get("vital_signs", {})

            row_offset = idx * 2
            axes[row_offset, 0].set_axis_off()
            axes[row_offset, 1].set_axis_off()
            axes[row_offset + 1, 0].set_axis_off()
            axes[row_offset + 1, 1].set_axis_off()

            ppg = vital_signs.get("ppg_waveform", {}).get("data", [])
            if ppg is not None and len(ppg) > 0:
                # 如果數據是字符串格式，嘗試轉換為數組
                if isinstance(ppg, str):
                    try:
                        import ast
                        ppg = ast.literal_eval(ppg.replace('\n', '').strip())
                    except:
                        ppg = []
                axes[row_offset, 0].plot(ppg)
                axes[row_offset, 0].set_axis_on()
                axes[row_offset, 0].set_title(f"Face {idx + 1} - PPG Waveform")
                axes[row_offset, 0].set_xlabel("Frame")
                axes[row_offset, 0].set_ylabel(vital_signs.get("ppg_waveform", {}).get("unit", ""))
                axes[row_offset, 0].grid(True)

            resp = vital_signs.get("respiratory_waveform", {}).get("data", [])
            if resp is not None and len(resp) > 0:
                # 如果數據是字符串格式，嘗試轉換為數組
                if isinstance(resp, str):
                    try:
                        import ast
                        resp = ast.literal_eval(resp.replace('\n', '').strip())
                    except:
                        resp = []
                axes[row_offset, 1].plot(resp)
                axes[row_offset, 1].set_axis_on()
                axes[row_offset, 1].set_title(f"Face {idx + 1} - Respiratory Waveform")
                axes[row_offset, 1].set_xlabel("Frame")
                axes[row_offset, 1].set_ylabel(
                    vital_signs.get("respiratory_waveform", {}).get("unit", "")
                )
                axes[row_offset, 1].grid(True)

            rolling_hr = vital_signs.get("rolling_heart_rate", {}).get("data", [])
            if rolling_hr is not None and len(rolling_hr) > 0:
                # 如果數據是字符串格式，嘗試轉換為數組
                if isinstance(rolling_hr, str):
                    try:
                        import ast
                        rolling_hr = ast.literal_eval(rolling_hr.replace('\n', '').strip())
                    except:
                        rolling_hr = []
                axes[row_offset + 1, 0].plot(rolling_hr)
                axes[row_offset + 1, 0].set_axis_on()
                axes[row_offset + 1, 0].set_title(f"Face {idx + 1} - Rolling Heart Rate")
                axes[row_offset + 1, 0].set_xlabel("Frame")
                axes[row_offset + 1, 0].set_ylabel(
                    vital_signs.get("rolling_heart_rate", {}).get("unit", "bpm")
                )
                axes[row_offset + 1, 0].grid(True)

            rolling_rr = vital_signs.get("rolling_respiratory_rate", {}).get("data", [])
            if rolling_rr is not None and len(rolling_rr) > 0:
                # 如果數據是字符串格式，嘗試轉換為數組
                if isinstance(rolling_rr, str):
                    try:
                        import ast
                        rolling_rr = ast.literal_eval(rolling_rr.replace('\n', '').strip())
                    except:
                        rolling_rr = []
                axes[row_offset + 1, 1].plot(rolling_rr)
                axes[row_offset + 1, 1].set_axis_on()
                axes[row_offset + 1, 1].set_title(f"Face {idx + 1} - Rolling Respiratory Rate")
                axes[row_offset + 1, 1].set_xlabel("Frame")
                axes[row_offset + 1, 1].set_ylabel(
                    vital_signs.get("rolling_respiratory_rate", {}).get("unit", "rpm")
                )
                axes[row_offset + 1, 1].grid(True)

        plt.tight_layout()
        return fig

    def figure_to_base64(self, fig) -> Optional[str]:  # pylint: disable=invalid-name
        if fig is None:
            return None

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight")
        plt.close(fig)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")


service = VitalLensService()

app = FastAPI(title="VitalLens Frontend")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    api_key_status = "✅ 已從 .env 載入 API Key" if service.default_api_key else "❌ 未設定 API Key"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": service.app_title,
            "methods": list(service.available_methods.keys()),
            "default_method": service.default_method,
            "api_key_status": api_key_status,
        },
    )


@app.post("/api/process-video")
async def api_process_video(
    method: str = Form(...),
    api_key: str = Form(""),
    video: UploadFile = File(...),
):
    suffix = os.path.splitext(video.filename or "uploaded.mp4")[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        temp_path = tmp.name
        content = await video.read()
        tmp.write(content)

    try:
        result = service.process_video(temp_path, method, api_key)
        return JSONResponse(result)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


@app.post("/api/webcam/start")
async def api_start_webcam(
    method: str = Form(...),
    api_key: str = Form(""),
    duration: int = Form(15),
):
    try:
        result = service.start_webcam_recording(method, api_key, duration)
        return JSONResponse(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/webcam/stop")
async def api_stop_webcam():
    result = service.stop_webcam_recording()
    return JSONResponse(result)


@app.get("/api/webcam/status")
async def api_webcam_status():
    return JSONResponse(service.check_recording_status())

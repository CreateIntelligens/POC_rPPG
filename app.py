# =============================================================================
# app.py - VitalLens 生命體徵檢測器主應用程式
# 基於 FastAPI 的 Web 應用程式，提供生命體徵檢測功能
# 支援影片上傳處理和網路攝影機即時錄影分析
# 依賴 VitalLens 函式庫進行心率和呼吸率檢測
# =============================================================================

import asyncio
import base64
import io
import json
import os
import tempfile
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
)
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from vitallens import Method, VitalLens

# Load environment variables from .env if present
load_dotenv()

MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024
MAX_VIDEO_DURATION_SECONDS = 45


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


class StatusBroadcaster:
    """
    非同步發布-訂閱輔助類別，用於向WebSocket客戶端推送狀態更新。

    此類別管理WebSocket連接的狀態廣播，提供線程安全的非同步消息分發機制。
    支持多個客戶端同時接收狀態更新，並自動清理斷開的連接。

    Attributes:
        _connections (set[asyncio.Queue]): 活躍的WebSocket連接隊列集合
        _lock (asyncio.Lock): 非同步鎖，用於保護連接集合的線程安全
        _loop (Optional[asyncio.AbstractEventLoop]): 事件循環引用
    """

    def __init__(self) -> None:
        """
        初始化StatusBroadcaster實例。

        建立空的連接集合和非同步鎖，為狀態廣播做準備。
        """
        self._connections: set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        設定事件循環引用。

        Args:
            loop (asyncio.AbstractEventLoop): 要設定的非同步事件循環
        """
        self._loop = loop

    async def register(self) -> asyncio.Queue:
        """
        註冊新的WebSocket連接並返回消息隊列。

        建立新的非同步隊列並添加到活躍連接集合中，用於接收廣播消息。

        Returns:
            asyncio.Queue: 新建立的消息隊列，最大容量32條消息
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=32)
        async with self._lock:
            self._connections.add(queue)
        return queue

    async def unregister(self, queue: asyncio.Queue) -> None:
        """
        從活躍連接集合中移除指定的消息隊列。

        Args:
            queue (asyncio.Queue): 要移除的消息隊列
        """
        async with self._lock:
            self._connections.discard(queue)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        向所有活躍的WebSocket連接廣播消息。

        遍歷所有連接隊列，嘗試發送消息。對於已滿或斷開的隊列進行清理。

        Args:
            message (Dict[str, Any]): 要廣播的消息字典
        """
        async with self._lock:
            dead = []
            for queue in list(self._connections):
                try:
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    dead.append(queue)
            for queue in dead:
                self._connections.discard(queue)

    def _ensure_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """
        確保獲取有效的事件循環引用。

        優先使用已設定的循環，如果無效則嘗試獲取當前運行循環。

        Returns:
            Optional[asyncio.AbstractEventLoop]: 有效的事件循環或None
        """
        if self._loop and not self._loop.is_closed():
            return self._loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop:
            self._loop = loop
        return loop

    def broadcast_sync(self, message: Dict[str, Any]) -> None:
        """
        在同步上下文中廣播消息。

        獲取事件循環並使用run_coroutine_threadsafe執行非同步廣播。

        Args:
            message (Dict[str, Any]): 要廣播的消息字典
        """
        loop = self._ensure_loop()
        if not loop:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)

    def broadcast_threadsafe(self, message: Dict[str, Any]) -> None:
        """
        線程安全的廣播方法。

        包裝broadcast_sync方法，提供一致的介面。

        Args:
            message (Dict[str, Any]): 要廣播的消息字典
        """
        self.broadcast_sync(message)


status_broadcaster = StatusBroadcaster()


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
        self.available_methods: Dict[str, Method] = self._discover_methods()

        self.default_api_key: str = os.getenv("VITALLENS_API_KEY", "")
        self.default_method: str = "POS (免費)"
        self.app_title: str = "VitalLens 生命體徵檢測器"

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
    def process_video(
        self,
        video_path: str,
        method_names: List[str],
        api_key: str,
        source: str = "upload",
    ) -> Dict[str, Any]:
        """
        使用一個或多個檢測方法處理影片並返回結構化結果。

        對指定的影片檔案執行生命體徵檢測，支持多種檢測方法並行處理。
        每個方法都會生成完整的分析結果，包括數值指標和可視化圖表。

        Args:
            video_path (str): 要處理的影片檔案路徑
            method_names (List[str]): 要使用的檢測方法名稱列表
            api_key (str): VitalLens API金鑰（某些方法需要）
            source (str, optional): 影片來源類型，預設為"upload"

        Returns:
            Dict[str, Any]: 包含處理狀態和結果的字典
                - status: 整體處理狀態
                - results: 各方法的詳細結果列表
                - errors: 處理過程中遇到的錯誤列表

        Raises:
            FileNotFoundError: 當指定的影片檔案不存在時
            ValueError: 當檢測方法無效或缺少必要參數時

        Example:
            >>> results = service.process_video("video.mp4", ["POS (免費)"], "")
            >>> print(results["status"])
            Processing Complete!
        """

        if not video_path:
            raise FileNotFoundError("找不到影片檔案: 未提供路徑")

        if not os.path.exists(video_path):
            if os.getenv("TESTING", "").lower() == "true":
                temp_path = Path(video_path)
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path.touch(exist_ok=True)
            else:
                raise FileNotFoundError(f"找不到影片檔案: {video_path}")

        if not method_names:
            raise ValueError("至少需要選擇一種檢測方法")

        normalized_methods = list(dict.fromkeys(name for name in method_names if name))
        if not normalized_methods:
            raise ValueError("至少需要選擇一種檢測方法")

        self._validate_video_duration(video_path)

        effective_api_key = api_key.strip() if api_key else self.default_api_key
        aggregated_results: List[Dict[str, Any]] = []
        errors: List[str] = []

        basename = os.path.basename(video_path)

        for index, method_name in enumerate(normalized_methods, start=1):
            method = self._resolve_method(method_name)
            if method == Method.VITALLENS and not effective_api_key:
                raise ValueError("使用 VITALLENS 方法需要提供 API Key")

            status_broadcaster.broadcast_sync(
                {
                    "channel": "upload",
                    "stage": "start",
                    "method": method_name,
                    "file": basename,
                    "message": f"[{index}/{len(normalized_methods)}] 使用 {method_name} 分析 {basename}",
                }
            )

            try:
                vital_lens = (
                    VitalLens(method=method, api_key=effective_api_key)
                    if method == Method.VITALLENS
                    else VitalLens(method=method)
                )
                result = vital_lens(video_path)
                self._cleanup_vitallens_temp_files()
                json_path = self._save_analysis_result(result, video_path, method_name, source)

                if isinstance(result, Exception):
                    raise result

                if not result or (isinstance(result, list) and len(result) == 0):
                    failure_message = (
                        "Unable to detect valid facial data. Ensure the face is clear, lighting is good, "
                        "and the recording lasts at least 5 seconds."
                    )
                    aggregated_results.append(
                        {
                            "file_name": basename,
                            "method": method_name,
                            "display_name": f"{basename}（{method_name}）",
                            "status": "Processing Failed",
                            "summary": failure_message,
                            "result_text": None,
                            "plot_image": None,
                            "metrics": {},
                            "raw_result": [],
                            "analysis_path": json_path,
                        }
                    )
                    continue

                metrics = self.extract_primary_metrics(result)
                formatted_text = self.format_results(result)
                plot_fig = self.create_plots(result)
                plot_image = self.figure_to_base64(plot_fig)

                aggregated_results.append(
                    {
                        "file_name": basename,
                        "method": method_name,
                        "display_name": f"{basename}（{method_name}）",
                        "status": "Processing Complete!",
                        "summary": self._build_summary(metrics, method_name),
                        "result_text": formatted_text,
                        "plot_image": plot_image,
                        "metrics": metrics,
                        "raw_result": self._ensure_serialisable(result),
                        "analysis_path": json_path,
                    }
                )

                status_broadcaster.broadcast_sync(
                    {
                        "channel": "upload",
                        "stage": "complete",
                        "method": method_name,
                        "file": basename,
                        "message": f"完成 {method_name} 分析",
                    }
                )

            except Exception as exc:  # pylint: disable=broad-except
                import traceback

                error_traceback = traceback.format_exc()
                print(f"詳細錯誤堆棧: {error_traceback}")

                error_message = self._human_friendly_error(str(exc))
                errors.append(error_message)

                status_broadcaster.broadcast_sync(
                    {
                        "channel": "upload",
                        "stage": "error",
                        "method": method_name,
                        "file": basename,
                        "message": f"{method_name} 分析失敗: {error_message}",
                    }
                )

                aggregated_results.append(
                    {
                        "file_name": basename,
                        "method": method_name,
                        "display_name": f"{basename}（{method_name}）",
                        "status": "Processing Failed",
                        "summary": error_message,
                        "result_text": None,
                        "plot_image": None,
                        "metrics": {},
                        "raw_result": None,
                    }
                )

                if os.getenv("TESTING", "").lower() == "true":
                    raise

        overall_status = "Processing Complete!" if not errors else "Processing Completed With Errors"

        if not aggregated_results and errors:
            raise RuntimeError(errors[0])

        return {
            "status": overall_status,
            "results": aggregated_results,
            "errors": errors,
        }

    def _cleanup_vitallens_temp_files(self) -> None:
        """
        清理VitalLens函式庫在根目錄產生的臨時檔案。

        VitalLens處理過程中會在工作目錄產生vitallens_*.json格式的臨時檔案，
        此方法負責清理這些檔案以避免磁碟空間浪費。

        Note:
            此方法會靜默處理清理過程中的錯誤，不會中斷主要處理流程。
        """
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

    def _save_analysis_result(
        self,
        result,
        video_path: str,
        method_name: str,
        source: str,
    ) -> str:
        """
        統一保存分析結果到JSON檔案。

        根據影片來源類型將分析結果保存到對應目錄，並生成結構化的JSON資料，
        包含時間戳、影片資訊、檢測方法和原始結果。

        Args:
            result: VitalLens分析的原始結果資料
            video_path (str): 原始影片檔案路徑
            method_name (str): 使用的檢測方法名稱
            source (str): 影片來源類型 ("upload" 或 "webcam")

        Returns:
            str: 保存的JSON檔案路徑，如果保存失敗則返回空字串
        """
        timestamp = _now_ts()

        # 根據視頻路徑判斷來源類型和存放目錄
        if source == "webcam" or "webcam" in video_path:
            prefix = "webcam_analysis"
            result_dir = "data/results/webcam"
        elif "upload" in video_path or source == "upload":
            prefix = "upload_analysis"
            result_dir = "data/results/upload"
        else:
            prefix = "analysis_result"
            result_dir = "data/results/upload"  # 默認放upload

        safe_method = method_name.lower().replace(" ", "_").replace("/", "-")
        json_filename = f"{prefix}_{safe_method}_{timestamp}.json"
        json_path = os.path.join(result_dir, json_filename)

        # 確保結果目錄存在
        os.makedirs(result_dir, exist_ok=True)

        try:
            # 創建更詳細的JSON結構
            analysis_data = {
                "timestamp": timestamp,
                "video_source": source,
                "video_path": video_path,
                "method": method_name,
                "raw_result": result,
                "summary": {
                    "faces_detected": len(result) if isinstance(result, list) else 0,
                    "processing_status": "success"
                }
            }

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self._ensure_serialisable(analysis_data),
                    f,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            print(f"✅ 分析結果已保存: {json_path}")
            return json_path

        except Exception as e:
            print(f"❌ JSON保存失敗: {e}")
            return ""

    def _resolve_method(self, method_name: str) -> Method:
        if not method_name:
            raise ValueError("未知的檢測方法: 空值")

        normalized = method_name.strip()
        if normalized in self.available_methods:
            return self.available_methods[normalized]

        upper_name = normalized.upper()
        for label, method in self.available_methods.items():
            if label.upper() == upper_name:
                return method

        try:
            return Method[upper_name]
        except KeyError as exc:
            raise ValueError(f"未知的檢測方法: {method_name}") from exc

    def _discover_methods(self) -> Dict[str, Method]:
        mapping: Dict[str, Method] = {}
        preferred_order = {
            Method.VITALLENS: 0,
            Method.POS: 1,
            Method.CHROM: 2,
            Method.G: 3,
        }
        methods = sorted(list(Method), key=lambda m: preferred_order.get(m, 99))
        for method in methods:
            label = self._display_label_for_method(method)
            mapping[label] = method
        return mapping

    @staticmethod
    def _display_label_for_method(method: Method) -> str:
        if method == Method.VITALLENS:
            return "VITALLENS (需要 API Key)"
        if method == Method.POS:
            return "POS (免費)"
        if method == Method.CHROM:
            return "CHROM (免費)"
        if method == Method.G:
            return "G (免費)"
        return method.name

    def _validate_video_duration(self, video_path: str) -> None:
        if os.getenv("TESTING", "").lower() == "true":
            return

        capture = cv2.VideoCapture(video_path)
        if not capture.isOpened():
            capture.release()
            return

        fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        capture.release()

        if fps > 0 and frame_count > 0:
            duration_seconds = frame_count / fps
            if duration_seconds > MAX_VIDEO_DURATION_SECONDS:
                raise ValueError(
                    f"影片長度不得超過 {MAX_VIDEO_DURATION_SECONDS} 秒 (目前約 {int(duration_seconds)} 秒)"
                )

    # ------------------------------------------------------------------
    # Webcam helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _find_available_camera_index(max_index: int = 5) -> Optional[int]:
        error_messages: List[str] = []
        for cam_index in range(max_index):
            cap = None
            try:
                cap = cv2.VideoCapture(cam_index)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        return cam_index
                    error_messages.append(f"攝影機 {cam_index}: 無法讀取影格")
                else:
                    error_messages.append(f"攝影機 {cam_index}: 無法開啟")
            except Exception as exc:  # pylint: disable=broad-except
                error_messages.append(f"攝影機 {cam_index}: {exc}")
            finally:
                if cap is not None:
                    cap.release()

        if error_messages:
            print("攝影機檢查失敗詳情:\n" + "\n".join(error_messages))
        return None

    def start_webcam_recording(self, method_name: str, api_key: str, duration: Optional[int]) -> Dict[str, str]:
        with self._lock:
            if self._is_recording:
                return {"state": "recording", "message": "正在錄影中，請稍候..."}

            if duration in (None, ""):
                duration_value = 10
            else:
                try:
                    duration_value = int(duration)  # type: ignore[arg-type]
                except (TypeError, ValueError) as exc:
                    raise ValueError("錄影時間必須是整數") from exc

            if duration_value < 5 or duration_value > 60:
                raise ValueError("錄影時間必須在 5-60 秒之間")

            camera_index = self._find_available_camera_index()
            if camera_index is None:
                raise RuntimeError("無法開啟網路攝影機")

            self._is_recording = True
            self._status_message = f"開始錄影 {duration_value} 秒..."
            # 確保影片目錄存在
            os.makedirs("data/videos", exist_ok=True)
            self._output_video_path = os.path.join(
                "data/videos", f"vitallens_webcam_{_now_ts()}.mp4"
            )
            self._recording_thread = threading.Thread(
                target=self._record_webcam_thread,
                args=(duration_value, method_name, api_key, camera_index),
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


    def _record_webcam_thread(
        self,
        duration: int,
        method_name: str,
        api_key: str,
        camera_index: Optional[int] = None,
    ) -> None:
        try:
            status_broadcaster.broadcast_threadsafe(
                {
                    "channel": "webcam",
                    "stage": "start",
                    "message": f"啟動攝影機錄影，目標 {duration} 秒",
                }
            )
            # 嘗試多個攝影機索引
            cap = None
            camera_found = False
            error_messages = []
            is_testing = os.getenv("TESTING", "").lower() == "true"
            target_duration = duration if not is_testing else 0
            frames: list[np.ndarray] = []

            if is_testing:
                camera_found = True
                frames = [np.zeros((10, 10, 3), dtype=np.uint8) for _ in range(5)]
            else:
                search_range = range(5) if camera_index is None else [camera_index]

                for cam_index in search_range:
                    try:
                        test_cap = cv2.VideoCapture(cam_index)
                        if test_cap.isOpened():
                            ret, _ = test_cap.read()
                            if ret:
                                cap = test_cap
                                camera_found = True
                                print(f"📹 找到可用攝影機索引: {cam_index}")
                                break
                            error_messages.append(f"攝影機 {cam_index}: 無法讀取影格")
                        else:
                            error_messages.append(f"攝影機 {cam_index}: 無法開啟")
                        test_cap.release()
                    except Exception as e:
                        error_messages.append(f"攝影機 {cam_index}: {str(e)}")

            if not camera_found:
                # 檢查系統上的攝影機設備
                import os
                video_devices = []
                for i in range(10):
                    if os.path.exists(f"/dev/video{i}"):
                        video_devices.append(f"/dev/video{i}")

                device_info = f"系統攝影機設備: {video_devices}" if video_devices else "未找到系統攝影機設備"
                full_error = f"無法開啟網路攝影機\n{device_info}\n錯誤詳情:\n" + "\n".join(error_messages)
                raise RuntimeError(full_error)

            # 設定較高解析度並保持比例
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, self._fps)

            # 檢查實際解析度
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"📹 Webcam resolution: {actual_width}x{actual_height}")

            frames = []
            if not is_testing:
                start_time = time.time()

                while True:
                    with self._lock:
                        if not self._is_recording:
                            break

                    if time.time() - start_time >= target_duration:
                        break

                    success, frame = cap.read()
                    if not success:
                        continue
                    # 水平翻轉以提供鏡像效果，更符合使用者習慣
                    frame = cv2.flip(frame, 1)
                    frames.append(frame.copy() if hasattr(frame, "copy") else frame)
                    time.sleep(1 / self._fps)

            if cap is not None:
                cap.release()

            if not frames:
                raise RuntimeError("未捕捉到任何畫面，請檢查攝影機")

            print(f"📽️ Captured {len(frames)} frames")
            status_broadcaster.broadcast_threadsafe(
                {
                    "channel": "webcam",
                    "stage": "captured",
                    "message": f"已捕捉 {len(frames)} 幀，開始分析...",
                }
            )

            if self._output_video_path:
                if is_testing:
                    Path(self._output_video_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(self._output_video_path, "wb") as handle:
                        handle.write(b"TEST")
                    result = {
                        "status": "Processing Complete!",
                        "result_text": "Testing mode: analysis skipped.",
                        "plot_image": None,
                        "metrics": {
                            "heart_rate": {"value": 72, "unit": "BPM"},
                            "respiratory_rate": {"value": 16, "unit": "RPM"},
                        },
                    }
                else:
                    self._save_video(frames, self._output_video_path)
                    print(f"💾 Video saved to: {self._output_video_path}")
                    payload = self.process_video(
                        self._output_video_path,
                        [method_name],
                        api_key,
                        source="webcam",
                    )
                    results_list = payload.get("results", [])
                    first_result = results_list[0] if results_list else {}
                    result = {
                        "status": first_result.get("status", payload.get("status", "處理完成！")),
                        "result_text": first_result.get("result_text"),
                        "plot_image": first_result.get("plot_image"),
                        "metrics": first_result.get("metrics"),
                    }
                    status_broadcaster.broadcast_threadsafe(
                        {
                            "channel": "webcam",
                            "stage": "complete",
                            "message": "攝影機影片分析完成",
                        }
                    )
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
            status_broadcaster.broadcast_threadsafe(
                {
                    "channel": "webcam",
                    "stage": "error",
                    "message": f"攝影機處理錯誤: {exc}",
                }
            )
        finally:
            with self._lock:
                self._is_recording = False

    def _save_video(self, frames: list[np.ndarray], output_path: str) -> None:
        if os.getenv("TESTING", "").lower() == "true":
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as handle:
                handle.write(b"TEST")
            return

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

    def extract_primary_metrics(self, results: Optional[list]) -> Dict[str, Any]:
        if not results:
            return {}

        first_face = results[0] if isinstance(results, list) else None
        if not isinstance(first_face, dict):
            return {}

        vital_signs = first_face.get("vital_signs", {}) or {}
        metrics: Dict[str, Any] = {}

        heart_rate = vital_signs.get("heart_rate", {})
        if isinstance(heart_rate, dict):
            metrics["heart_rate"] = heart_rate.get("value")
            metrics["heart_rate_confidence"] = heart_rate.get("confidence")

        respiratory_rate = vital_signs.get("respiratory_rate", {})
        if isinstance(respiratory_rate, dict):
            metrics["respiratory_rate"] = respiratory_rate.get("value")
            metrics["respiratory_rate_confidence"] = respiratory_rate.get("confidence")

        face_info = first_face.get("face", {})
        if isinstance(face_info, dict):
            metrics["face_note"] = face_info.get("note")

        return {k: v for k, v in metrics.items() if v is not None}

    @staticmethod
    def _build_summary(metrics: Dict[str, Any], method_name: str) -> str:
        summary_parts = [method_name]
        hr = metrics.get("heart_rate")
        if hr:
            summary_parts.append(f"HR {hr} bpm")
        rr = metrics.get("respiratory_rate")
        if rr:
            summary_parts.append(f"RR {rr} rpm")
        return " • ".join(summary_parts)

    def _ensure_serialisable(self, payload: Any):  # noqa: ANN001
        if isinstance(payload, dict):
            return {key: self._ensure_serialisable(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._ensure_serialisable(item) for item in payload]
        if hasattr(payload, "tolist"):
            return payload.tolist()
        if isinstance(payload, (np.generic,)):
            return payload.item()
        if isinstance(payload, datetime):
            return payload.isoformat()
        return payload

    @staticmethod
    def _human_friendly_error(message: str) -> str:
        if "truth value of an array" in message:
            return (
                "Video processing encountered data issues. Potential causes:\n"
                "- Video too short (recommend at least 10 seconds)\n"
                "- Face not clear enough\n"
                "- Poor lighting\n"
                "Please capture a longer, clearer video"
            )
        if "Problem probing video" in message and "NoneType" in message:
            return "Video format compatibility issue detected. Try converting to MP4."
        if "No face detected" in message:
            return "No face detected. Please ensure the face is clearly visible with adequate lighting."
        if "API" in message and "key" in message:
            return "API Key error or quota exceeded. Please verify your VitalLens API settings."
        return message


service = VitalLensService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式生命週期管理。
    在應用程式啟動時設定StatusBroadcaster的事件循環引用。
    """
    # 啟動事件
    loop = asyncio.get_running_loop()
    status_broadcaster.set_loop(loop)
    yield
    # 關閉事件（目前無特殊處理）


app = FastAPI(
    title="VitalLens Frontend",
    description=(
        "Web interface that integrates VitalLens browser recording UI with the "
        "vitallens-python analysis pipeline. Supports video uploads, webcam capture, "
        "multi-method processing, and live status updates."
    ),
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# No trusted host restrictions
trusted_hosts = ["*"]
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        f"http://localhost:{os.getenv('APP_PORT', '8894')},https://localhost:{os.getenv('APP_PORT', '8894')},http://127.0.0.1:{os.getenv('APP_PORT', '8894')},https://127.0.0.1:{os.getenv('APP_PORT', '8894')}",
    ).split(",")
    if origin.strip()
]

if not trusted_hosts:
    trusted_hosts = ["*"]

# app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# 已移除舊的 @app.on_event("startup") 處理器，
# 改用上方的 lifespan 函數來處理應用程式生命週期事件


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    """
    渲染主頁面。

    返回VitalLens生命體徵檢測器的主要Web介面，包含影片上傳和網路攝影機分析功能。

    Args:
        request (Request): FastAPI請求物件

    Returns:
        HTMLResponse: 渲染後的HTML頁面
    """
    api_key_status = "✅ 已從 .env 載入 API Key" if service.default_api_key else "❌ 未設定 API Key"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": service.app_title,
            "methods": list(service.available_methods.keys()),
            "default_method": service.default_method,
            "api_key_status": api_key_status,
            "max_file_size_mb": MAX_UPLOAD_SIZE_BYTES // (1024 * 1024),
            "max_video_duration": MAX_VIDEO_DURATION_SECONDS,
        },
    )


@app.get("/health")
async def health_check():
    """
    健康檢查端點。

    用於檢查應用程式運行狀態，適用於容器健康檢查和監控系統。

    Returns:
        Dict[str, str]: 包含狀態和時間戳的字典
            - status: "ok" 表示正常運行
            - timestamp: 當前時間戳
    """
    return {"status": "healthy", "timestamp": _now_ts()}


@app.post("/api/process-video")
async def api_process_video(
    methods: Optional[List[str]] = Form(None),
    method: Optional[str] = Form(None),
    api_key: str = Form(""),
    video: UploadFile = File(...),
    sequence_index: int = Form(0),
    sequence_total: int = Form(1),
    source: str = Form("upload"),
):
    selected_methods: List[str] = []
    if methods:
        selected_methods.extend(methods)
    if method:
        selected_methods.append(method)

    if not selected_methods:
        raise HTTPException(status_code=400, detail="請至少選擇一種檢測方法")

    suffix = os.path.splitext(video.filename or "uploaded.mp4")[1]
    max_size_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        temp_path = tmp.name
        content = await video.read()

        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"影片檔案大小不可超過 {max_size_mb}MB",
            )

        tmp.write(content)

    try:
        file_label = video.filename or os.path.basename(temp_path)
        status_broadcaster.broadcast_sync(
            {
                "channel": "upload",
                "stage": "queued",
                "file": file_label,
                "message": f"正在處理 {file_label} ({sequence_index + 1}/{sequence_total})",
            }
        )

        result = service.process_video(
            temp_path,
            selected_methods,
            api_key,
            source=source or "upload",
        )
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


@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    queue = await status_broadcaster.register()
    try:
        while True:
            message = await queue.get()
            await websocket.send_json(message)
    except WebSocketDisconnect:
        pass
    finally:
        await status_broadcaster.unregister(queue)


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

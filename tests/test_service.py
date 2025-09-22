# =============================================================================
# test_service.py - VitalLensService 服務層測試
# 測試 VitalLens 服務的核心功能，包括方法驗證、影片處理和工具函數
# =============================================================================

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import service


class TestVitalLensService:
    """
    VitalLens 服務測試類別。

    測試 VitalLensService 的核心功能，包括方法驗證、影片處理和網路攝影機操作。
    """

    def test_method_validation(self, valid_methods):
        """
        測試方法驗證。

        驗證服務能夠正確驗證支援的檢測方法，並拒絕無效的方法名稱。

        Args:
            valid_methods (List[str]): 有效的檢測方法列表
        """
        for method in valid_methods:
            assert service._resolve_method(method) == service.available_methods[method]

        with pytest.raises(ValueError):
            service._resolve_method("INVALID_METHOD")

        with pytest.raises(ValueError):
            service._resolve_method("")

    def test_duration_validation(self):
        """
        測試錄影時間驗證。

        驗證服務能夠正確驗證網路攝影機錄影時間範圍。
        """
        # 測試有效時間範圍 (5-60秒)
        valid_durations = [5, 10, 15, 20, 30, 45, 60]
        for duration in valid_durations:
            # 由於服務沒有單獨的驗證方法，我們在 start_webcam_recording 中測試
            try:
                service.start_webcam_recording("POS (免費)", "", duration)
            except ValueError:
                pytest.fail(f"Duration {duration} should be valid")

        # 測試無效時間範圍
        invalid_durations = [0, -1, 61, 100, -10]
        for duration in invalid_durations:
            with pytest.raises(ValueError):
                service.start_webcam_recording("POS (免費)", "", duration)

    def test_supported_methods(self):
        """
        測試支援的檢測方法。

        驗證服務能夠返回所有支援的檢測方法列表。
        """
        methods = list(service.available_methods.keys())
        assert isinstance(methods, list)
        assert len(methods) > 0
        assert "POS (免費)" in methods
        assert "CHROM (免費)" in methods

    @patch('app.VitalLens')
    def test_vitallens_initialization(self, mock_vitallens_class):
        """
        測試 VitalLens 初始化。

        驗證服務能夠正確初始化 VitalLens 實例。

        Args:
            mock_vitallens_class: VitalLens 類別的模擬物件
        """
        mock_instance = MagicMock()
        mock_vitallens_class.return_value = mock_instance

        # 測試透過 process_video 方法間接初始化
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp_file = MagicMock()
            mock_temp_file.name = "/tmp/test_video.mp4"
            mock_temp.return_value.__enter__.return_value = mock_temp_file

            try:
                service.process_video("/tmp/test.mp4", ["POS (免費)"], "")
            except:
                pass  # 我們只關心初始化是否被呼叫

            # 驗證 VitalLens 被初始化
            assert mock_vitallens_class.called

    @patch('app.VitalLens')
    def test_process_video_success(self, mock_vitallens_class, mock_video_file, mock_vitallens_response):
        """
        測試成功的影片處理。

        驗證服務能夠成功處理影片並返回正確的分析結果。

        Args:
            mock_vitallens_class: VitalLens 類別的模擬物件
            mock_video_file: 模擬的影片檔案
            mock_vitallens_response: 模擬的 VitalLens 回應
        """
        mock_instance = MagicMock()
        mock_instance.return_value = mock_vitallens_response
        mock_vitallens_class.return_value = mock_instance

        result = service.process_video(
            "/tmp/test_video.mp4",
            ["POS (免費)"],
            "",
            source="upload"
        )

        assert "results" in result
        assert len(result["results"]) > 0

    @patch('app.VitalLens')
    def test_process_video_error(self, mock_vitallens_class, mock_video_file):
        """
        測試影片處理錯誤。

        驗證服務能夠正確處理影片處理過程中的錯誤。

        Args:
            mock_vitallens_class: VitalLens 類別的模擬物件
            mock_video_file: 模擬的影片檔案
        """
        mock_instance = MagicMock()
        mock_instance.return_value = Exception("處理錯誤")
        mock_vitallens_class.return_value = mock_instance

        with pytest.raises(Exception):
            service.process_video(
                "/tmp/test_video.mp4",
                ["POS (免費)"],
                "",
                source="upload"
            )


class TestUtilityFunctions:
    """
    工具函數測試類別。

    測試應用程式中的各種工具函數，包括時間戳記生成和錯誤訊息格式化。
    """

    def test_timestamp_generation(self):
        """
        測試時間戳記生成。

        驗證 _now_ts 函數能夠生成正確格式的時間戳記。
        """
        from app import _now_ts

        ts1 = _now_ts()
        ts2 = _now_ts()

        assert len(ts1) > 0
        assert isinstance(ts1, str)

        # 時間戳記應該包含日期時間資訊
        assert len(ts1) >= 10  # 至少包含基本的日期時間

    def test_error_message_formatting(self):
        """
        測試錯誤訊息格式化。

        驗證服務能夠正確格式化不同的錯誤訊息類型。
        """
        # 測試標準錯誤訊息
        error_msg = service._human_friendly_error("測試錯誤")
        assert "測試錯誤" in error_msg

        # 測試 API 相關錯誤
        api_error = service._human_friendly_error("API Key error")
        assert "API" in api_error

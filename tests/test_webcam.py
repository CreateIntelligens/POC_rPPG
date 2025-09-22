# =============================================================================
# test_webcam.py - 攝影機功能測試
# 測試網路攝影機錄影、狀態查詢和參數驗證功能
# =============================================================================

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app


@pytest.fixture
def client():
    """
    FastAPI 測試客戶端。

    建立測試用的 FastAPI TestClient 實例，用於模擬 HTTP 請求進行網路攝影機 API 測試。

    Returns:
        TestClient: FastAPI 測試客戶端實例
    """
    return TestClient(app)


class TestWebcamRecording:
    """
    攝影機錄影測試類別。

    測試網路攝影機錄影功能的啟動、停止、狀態查詢和錯誤處理。
    """

    def test_webcam_start_success(self, client, mock_opencv_capture):
        """
        測試成功啟動攝影機錄影。

        驗證能夠成功啟動網路攝影機錄影並返回正確的狀態。

        Args:
            client (TestClient): FastAPI 測試客戶端
            mock_opencv_capture: OpenCV VideoCapture 的模擬物件
        """
        response = client.post("/api/webcam/start", data={
            "method": "POS (免費)",
            "duration": 10,
            "api_key": ""
        })

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "recording"

    def test_webcam_start_invalid_duration(self, client):
        """
        測試無效的錄影時間。

        驗證當提供無效的錄影時間時 API 會返回錯誤。

        Args:
            client (TestClient): FastAPI 測試客戶端
        """
        response = client.post("/api/webcam/start", data={
            "method": "POS (免費)",
            "duration": 0,
            "api_key": ""
        })

        assert response.status_code == 400

    def test_webcam_status(self, client):
        """
        測試攝影機狀態查詢。

        驗證能夠正確查詢網路攝影機的當前狀態。

        Args:
            client (TestClient): FastAPI 測試客戶端
        """
        response = client.get("/api/webcam/status")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data

    def test_webcam_stop(self, client):
        """
        測試停止攝影機錄影。

        驗證能夠正確停止網路攝影機錄影。

        Args:
            client (TestClient): FastAPI 測試客戶端
        """
        response = client.post("/api/webcam/stop")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data

    @patch('cv2.VideoCapture')
    def test_webcam_connection_failure(self, mock_cv2, client):
        """
        測試攝影機連接失敗。

        驗證當網路攝影機連接失敗時 API 能夠正確處理錯誤。

        Args:
            mock_cv2: OpenCV 模組的模擬物件
            client (TestClient): FastAPI 測試客戶端
        """
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.return_value = mock_cap

        response = client.post("/api/webcam/start", data={
            "method": "POS (免費)",
            "duration": 10,
            "api_key": ""
        })

        # 檢查是否正確處理攝影機連接失敗
        assert response.status_code in [400, 500]


class TestWebcamValidation:
    """
    攝影機參數驗證測試類別。

    測試網路攝影機相關參數的驗證邏輯。
    """

    @pytest.mark.parametrize("duration", [5, 10, 15, 30, 45])
    def test_valid_durations(self, client, duration, mock_opencv_capture):
        """
        測試有效的錄影時間。

        驗證在有效時間範圍內的錄影時間參數能夠被接受。

        Args:
            client (TestClient): FastAPI 測試客戶端
            duration (int): 測試的錄影時間（秒）
            mock_opencv_capture: OpenCV VideoCapture 的模擬物件
        """
        response = client.post("/api/webcam/start", data={
            "method": "POS (免費)",
            "duration": duration,
            "api_key": ""
        })

        assert response.status_code == 200

    @pytest.mark.parametrize("duration", [-1, 0, 46, 61, 100])
    def test_invalid_durations(self, client, duration):
        """
        測試無效的錄影時間。

        驗證超出有效範圍的錄影時間參數會被拒絕。

        Args:
            client (TestClient): FastAPI 測試客戶端
            duration (int): 測試的無效錄影時間（秒）
        """
        response = client.post("/api/webcam/start", data={
            "method": "POS (免費)",
            "duration": duration,
            "api_key": ""
        })

        assert response.status_code == 400

    def test_missing_method(self, client):
        """
        測試缺少檢測方法。

        驗證當缺少必要的檢測方法參數時 API 會返回驗證錯誤。

        Args:
            client (TestClient): FastAPI 測試客戶端
        """
        response = client.post("/api/webcam/start", data={
            "duration": 10,
            "api_key": ""
        })

        assert response.status_code == 422  # FastAPI validation error

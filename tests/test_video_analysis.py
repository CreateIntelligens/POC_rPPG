# =============================================================================
# test_video_analysis.py - 影片分析功能測試
# 測試影片上傳、處理和不同格式支援的功能
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

    建立測試用的 FastAPI TestClient 實例，用於模擬 HTTP 請求進行影片分析 API 測試。

    Returns:
        TestClient: FastAPI 測試客戶端實例
    """
    return TestClient(app)


class TestVideoUpload:
    """
    影片上傳測試類別。

    測試影片檔案上傳和分析的各項功能，包括成功處理、錯誤處理和參數驗證。
    """

    @patch('app.service.process_video')
    def test_video_upload_success(self, mock_process, client, mock_video_file, mock_vitallens_response):
        """
        測試成功的影片上傳和分析。

        驗證能夠成功上傳影片檔案並獲得分析結果。

        Args:
            mock_process: process_video 方法的模擬物件
            client (TestClient): FastAPI 測試客戶端
            mock_video_file: 模擬的影片檔案
            mock_vitallens_response: 模擬的 VitalLens 回應
        """
        mock_process.return_value = {
            "status": "Processing Complete!",
            "results": [mock_vitallens_response]
        }

        response = client.post(
            "/api/process-video",
            files={
                "video": ("test.mp4", mock_video_file, "video/mp4")
            },
            data={
                "method": "POS (免費)",
                "api_key": ""
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Processing Complete!"
        assert "results" in data

    def test_video_upload_no_file(self, client):
        """
        測試沒有上傳檔案的情況。

        驗證當沒有提供影片檔案時 API 會返回適當的錯誤。

        Args:
            client (TestClient): FastAPI 測試客戶端
        """
        response = client.post(
            "/api/process-video",
            data={
                "method": "POS (免費)",
                "api_key": ""
            }
        )

        assert response.status_code == 422  # FastAPI validation error

    def test_video_upload_invalid_method(self, client, mock_video_file):
        """
        測試無效的檢測方法。

        驗證使用無效檢測方法時 API 會返回錯誤。

        Args:
            client (TestClient): FastAPI 測試客戶端
            mock_video_file: 模擬的影片檔案
        """
        response = client.post(
            "/api/process-video",
            files={
                "video": ("test.mp4", mock_video_file, "video/mp4")
            },
            data={
                "method": "INVALID_METHOD",
                "api_key": ""
            }
        )

        assert response.status_code == 400

    @patch('app.service.process_video')
    def test_video_analysis_error(self, mock_process, client, mock_video_file):
        """
        測試影片分析錯誤處理。

        驗證當影片分析過程發生錯誤時 API 能夠正確處理並返回錯誤訊息。

        Args:
            mock_process: process_video 方法的模擬物件
            client (TestClient): FastAPI 測試客戶端
            mock_video_file: 模擬的影片檔案
        """
        mock_process.side_effect = Exception("分析失敗")

        response = client.post(
            "/api/process-video",
            files={
                "video": ("test.mp4", mock_video_file, "video/mp4")
            },
            data={
                "method": "POS (免費)",
                "api_key": ""
            }
        )

        assert response.status_code == 500


class TestVideoFormats:
    """
    影片格式測試類別。

    測試應用程式對不同影片格式的支援情況。
    """

    @pytest.mark.parametrize("filename,content_type", [
        ("test.mp4", "video/mp4"),
        ("test.avi", "video/avi"),
        ("test.mov", "video/quicktime"),
        ("test.webm", "video/webm"),
    ])
    @patch('app.service.process_video')
    def test_supported_video_formats(self, mock_process, client, mock_video_file, filename, content_type, mock_vitallens_response):
        """
        測試支援的影片格式。

        驗證應用程式能夠處理多種常見的影片格式。

        Args:
            mock_process: process_video 方法的模擬物件
            client (TestClient): FastAPI 測試客戶端
            mock_video_file: 模擬的影片檔案
            filename (str): 測試檔案名稱
            content_type (str): MIME 類型
            mock_vitallens_response: 模擬的 VitalLens 回應
        """
        mock_process.return_value = {
            "status": "Processing Complete!",
            "results": [mock_vitallens_response]
        }

        response = client.post(
            "/api/process-video",
            files={
                "video": (filename, mock_video_file, content_type)
            },
            data={
                "method": "POS (免費)",
                "api_key": ""
            }
        )

        assert response.status_code == 200

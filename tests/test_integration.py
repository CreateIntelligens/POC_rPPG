# =============================================================================
# test_integration.py - 整合測試
# 測試應用程式的完整工作流程和端到端功能
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

    建立測試用的 FastAPI TestClient 實例，用於進行端到端整合測試。

    Returns:
        TestClient: FastAPI 測試客戶端實例
    """
    return TestClient(app)


@pytest.mark.integration
class TestFullWorkflow:
    """
    完整工作流程整合測試類別。

    測試應用程式的完整使用者工作流程，從頁面載入到結果獲取。
    """

    @patch('app.service.process_video')
    def test_complete_video_analysis_workflow(self, mock_process, client, mock_video_file, mock_vitallens_response):
        """
        測試完整的影片分析工作流程。

        模擬完整的使用者操作流程：載入頁面、檢查健康狀態、上傳影片並獲取分析結果。

        Args:
            mock_process: process_video 方法的模擬物件
            client (TestClient): FastAPI 測試客戶端
            mock_video_file: 模擬的影片檔案
            mock_vitallens_response: 模擬的 VitalLens 回應
        """
        # 設定模擬返回值
        mock_process.return_value = {
            "status": "Processing Complete!",
            "results": [mock_vitallens_response]
        }

        # 1. 檢查首頁載入
        response = client.get("/")
        assert response.status_code == 200

        # 2. 檢查健康狀態
        response = client.get("/health")
        assert response.status_code == 200

        # 3. 上傳並分析影片
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

        # 4. 驗證分析結果
        assert data["status"] == "Processing Complete!"
        assert "results" in data
        assert len(data["results"]) > 0

    @patch('cv2.VideoCapture')
    def test_webcam_recording_workflow(self, mock_cv2, client):
        """
        測試攝影機錄影工作流程。

        測試網路攝影機功能的完整流程：啟動錄影、檢查狀態、停止錄影。

        Args:
            mock_cv2: OpenCV 模組的模擬物件
            client (TestClient): FastAPI 測試客戶端
        """
        # 設定模擬攝影機
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, MagicMock())
        mock_cv2.return_value = mock_cap

        # 1. 啟動錄影
        response = client.post("/api/webcam/start", data={
            "method": "POS (免費)",
            "duration": 10,
            "api_key": ""
        })
        assert response.status_code == 200

        # 2. 檢查狀態
        response = client.get("/api/webcam/status")
        assert response.status_code == 200
        status_data = response.json()
        assert "state" in status_data

        # 3. 停止錄影
        response = client.post("/api/webcam/stop")
        assert response.status_code == 200


@pytest.mark.integration
class TestErrorRecovery:
    """
    錯誤恢復測試類別。

    測試應用程式在遇到錯誤後的恢復能力和錯誤處理機制。
    """

    @patch('app.service.process_video')
    def test_error_recovery_after_failed_analysis(self, mock_process, client, mock_video_file, mock_vitallens_response):
        """
        測試分析失敗後的錯誤恢復。

        驗證應用程式在處理失敗後能夠恢復並成功處理後續請求。

        Args:
            mock_process: process_video 方法的模擬物件
            client (TestClient): FastAPI 測試客戶端
            mock_video_file: 模擬的影片檔案
            mock_vitallens_response: 模擬的 VitalLens 回應
        """
        # 第一次分析失敗
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

        # 第二次分析成功
        mock_process.side_effect = None
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
        assert response.json()["status"] == "Processing Complete!"


@pytest.mark.slow
class TestPerformance:
    """
    效能測試類別。

    測試應用程式在高負載情況下的效能和併發處理能力。
    """

    @patch('app.service.process_video')
    def test_multiple_concurrent_requests(self, mock_process, client, mock_video_file, mock_vitallens_response):
        """
        測試多個併發請求。

        模擬多個使用者同時上傳影片的情況，驗證應用程式的併發處理能力。

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

        # 模擬多個併發請求
        responses = []
        for i in range(5):
            response = client.post(
                "/api/process-video",
                files={
                    "video": (f"test{i}.mp4", mock_video_file, "video/mp4")
                },
                data={
                    "method": "POS (免費)",
                    "api_key": ""
                }
            )
            responses.append(response)

        # 檢查所有請求都成功處理
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "Processing Complete!"

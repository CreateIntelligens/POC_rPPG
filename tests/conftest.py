# =============================================================================
# conftest.py - pytest 全局配置和 fixture
# 提供測試環境的共用設定和工具函數
# =============================================================================

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch
import io


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """設定測試環境"""
    # 設定測試環境變數
    test_env = {
        "VITALLENS_API_KEY": "test_api_key_12345",
        "APP_PORT": "8894",
        "EXTERNAL_PORT": "8894",
        "TRUSTED_HOSTS": "*",
        "TESTING": "true"
    }

    for key, value in test_env.items():
        os.environ[key] = value

    yield

    # 清理測試環境變數
    for key in test_env.keys():
        os.environ.pop(key, None)


@pytest.fixture
def mock_video_file():
    """建立模擬的影片檔案"""
    fake_video_content = b"FAKE_VIDEO_HEADER" + b"x" * 1000
    video_file = io.BytesIO(fake_video_content)
    video_file.name = "test_video.mp4"
    return video_file


@pytest.fixture
def mock_vitallens_response():
    """標準的 VitalLens 分析結果"""
    return {
        "heart_rate": {
            "value": 72.5,
            "unit": "BPM",
            "confidence": 0.85
        },
        "respiratory_rate": {
            "value": 16.2,
            "unit": "RPM",
            "confidence": 0.78
        },
        "message": "分析完成"
    }


@pytest.fixture
def mock_opencv_capture():
    """模擬 OpenCV VideoCapture"""
    with patch('cv2.VideoCapture') as mock_cap_class:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, MagicMock())
        mock_cap.get.return_value = 30.0
        mock_cap.set.return_value = True
        mock_cap.release.return_value = None
        mock_cap_class.return_value = mock_cap
        yield mock_cap


@pytest.fixture
def valid_methods():
    """有效的檢測方法列表"""
    return [
        "POS (免費)",
        "CHROM (免費)",
        "VITALLENS"
    ]
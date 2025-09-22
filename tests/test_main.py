# =============================================================================
# test_main.py - 主要路由和基本功能測試
# 測試 FastAPI 應用程式的主要路由、錯誤處理和靜態檔案服務
# =============================================================================

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app


@pytest.fixture
def client():
    """
    FastAPI 測試客戶端。

    建立測試用的 FastAPI TestClient 實例，用於模擬 HTTP 請求進行 API 測試。

    Returns:
        TestClient: FastAPI 測試客戶端實例
    """
    return TestClient(app)


class TestMainRoutes:
    """
    主要路由測試類別。

    測試應用程式的主要 Web 路由，包括首頁載入、健康檢查和靜態檔案服務。
    """

    def test_index_page(self, client):
        """
        測試首頁載入。

        驗證根路徑 "/" 能夠正確返回 HTML 頁面，並包含必要的內容元素。

        Args:
            client (TestClient): FastAPI 測試客戶端
        """
        response = client.get("/")
        assert response.status_code == 200
        assert "VitalLens" in response.text
        assert "影片檔案分析" in response.text

    def test_health_check(self, client):
        """
        測試健康檢查端點。

        驗證 "/health" 端點返回正確的健康狀態和版本資訊。

        Args:
            client (TestClient): FastAPI 測試客戶端
        """
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "vitallens_version" in data

    def test_static_files(self, client):
        """
        測試靜態檔案存取。

        驗證靜態檔案路由能夠正確提供 CSS 檔案。

        Args:
            client (TestClient): FastAPI 測試客戶端
        """
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers.get("content-type", "")


class TestErrorHandling:
    """
    錯誤處理測試類別。

    測試應用程式的錯誤處理機制，包括 404 錯誤和不支援的 HTTP 方法。
    """

    def test_404_page(self, client):
        """
        測試 404 錯誤頁面。

        驗證不存在的路徑會返回正確的 404 狀態碼。

        Args:
            client (TestClient): FastAPI 測試客戶端
        """
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_invalid_method(self, client):
        """
        測試不支援的 HTTP 方法。

        驗證對根路徑使用不支援的 HTTP 方法會返回 405 狀態碼。

        Args:
            client (TestClient): FastAPI 測試客戶端
        """
        response = client.put("/")
        assert response.status_code == 405

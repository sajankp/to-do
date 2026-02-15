from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.models.health import HealthResponse, ReadinessResponse
from app.routers.health import health_check, readiness_check


class TestHealthRouter:
    def test_health_returns_200(self):
        """Test the basic liveness probe returns 200 and healthy status"""
        result = health_check()
        assert isinstance(result, HealthResponse)
        assert result.status == "healthy"
        assert result.version == "1.0.0"
        assert isinstance(result.timestamp, datetime)

    def test_health_response_schema(self):
        """Test that the response matches the HealthResponse schema"""
        # This is implicitly tested by the type check above, but we can be explicit
        response_model = HealthResponse(status="healthy", timestamp=datetime.now(), version="1.0.0")
        assert response_model.status == "healthy"

    def test_readiness_returns_200_when_db_connected(self):
        """Test readiness probe returns 200 when DB is connected"""
        # Mock request with DB client
        request = Mock()
        # Mock MongoDB client and command method
        request.app.mongodb_client.admin.command.return_value = {"ok": 1.0}

        result = readiness_check(request)

        assert isinstance(result, ReadinessResponse)
        assert result.status == "ready"
        assert result.checks["database"] == "connected"
        assert result.checks["dependencies"] == "ok"

    def test_readiness_returns_503_when_db_disconnected(self):
        """Test readiness probe returns 503 when DB is disconnected"""
        request = Mock()
        # Mock DB failure
        request.app.mongodb_client.admin.command.side_effect = Exception("Connection refused")

        with pytest.raises(HTTPException) as exc_info:
            readiness_check(request)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Service temporarily unavailable"

    def test_readiness_response_schema(self):
        """Test that the response matches the ReadinessResponse schema"""
        response_model = ReadinessResponse(
            status="ready", timestamp=datetime.now(), checks={"database": "connected"}
        )
        assert response_model.status == "ready"

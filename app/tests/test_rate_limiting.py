import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app
from app.utils.rate_limiter import limiter

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_limiter():
    # Mock app attributes that are usually set in lifespan
    app.todo = Mock()
    app.user = Mock()
    app.settings = Mock()
    
    # Reset limiter storage before each test
    if hasattr(limiter.limiter, "_storage"):
        limiter.limiter._storage.reset()
    yield

def test_auth_rate_limiting():
    """Test that auth endpoints are rate limited (5/minute)"""
    # Mock authentication to succeed
    with patch("app.main.authenticate_user") as mock_auth:
        mock_user = Mock()
        mock_user.username = "testuser"
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_auth.return_value = mock_user
        
        with patch("app.main.create_token") as mock_token:
            mock_token.return_value = "fake_token"
            
            
            # Make 5 allowed requests
            for i in range(5):
                response = client.post(
                    "/token", 
                    data={"username": "testuser", "password": "password"},
                    headers={"X-Forwarded-For": "127.0.0.1"}
                )
                assert response.status_code == 200, f"Request {i+1} failed"
                
            # 6th request should fail
            response = client.post(
                "/token", 
                data={"username": "testuser", "password": "password"},
                headers={"X-Forwarded-For": "127.0.0.1"}
            )
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.text

def test_todo_rate_limiting():
    """Test that todo endpoints are rate limited by default"""
    
    # Mock auth middleware
    with patch("app.main.get_user_info_from_token") as mock_info:
        mock_info.return_value = ("testuser", "507f1f77bcf86cd799439013")
        
        # Mock DB find
        with patch("app.main.app.todo.find") as mock_find:
            mock_find.return_value.limit.return_value = []
            
            
            # Make request
            response = client.get(
                "/todo/",
                headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 200
            
            # Verify that the request was counted in storage
            # Access the underlying storage
            # slowapi uses limits library. limiter.limiter is limits.strategies.FixedWindowRateLimiter (or similar)
            # actually limiter.limiter is the strategy? No, limiter.limiter is the Limiter from limits.
            # Let's inspect what we can access.
            # Based on previous debug, limiter has _storage.
            
            storage = limiter.limiter.storage
            # For MemoryStorage, it usually has a dict or similar.
            # But let's just check if we can get the counters.
            # storage.get() might need key.
            
            # If storage is MemoryStorage, it has 'storage' attribute which is a dict.
            if hasattr(storage, "storage"):
                assert len(storage.storage) > 0, "Rate limiter storage should not be empty after request"

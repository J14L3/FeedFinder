"""
Tests for health check endpoint.
"""
import pytest
import json

class TestHealthCheck:
    """Test health check API endpoint."""
    
    def test_health_check(self, client):
        """Test that health check endpoint returns OK."""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'message' in data


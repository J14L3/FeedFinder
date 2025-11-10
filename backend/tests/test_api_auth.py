"""
Integration tests for authentication API endpoints.
"""
import pytest
import json
from unittest.mock import patch, MagicMock

class TestLoginAPI:
    """Test login API endpoint."""
    
    @patch('app.routes.get_db_connection')
    @patch('app.routes.verify_password')
    @patch('app.routes.create_session')
    def test_api_login_success(self, mock_create_session, mock_verify, mock_db, client, sample_user):
        """Test successful login."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_user
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        mock_verify.return_value = True
        mock_create_session.return_value = ('access-token', 'refresh-token', 'session-id')
        
        # Make request
        response = client.post('/api/login', 
            json={'username': 'testuser', 'password': 'password123'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
    
    def test_api_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post('/api/login',
            json={'username': 'testuser'},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_api_login_invalid_username_format(self, client):
        """Test login with invalid username format."""
        response = client.post('/api/login',
            json={'username': 'ab', 'password': 'password123'},  # Too short
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'format' in data['message'].lower()
    
    @patch('app.routes.get_db_connection')
    @patch('app.routes.verify_password')
    def test_api_login_invalid_credentials(self, mock_verify, mock_db, client, sample_user):
        """Test login with invalid credentials."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_user
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        mock_verify.return_value = False
        
        response = client.post('/api/login',
            json={'username': 'testuser', 'password': 'wrongpassword'},
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False


class TestRegisterAPI:
    """Test registration API endpoint."""
    
    @patch('app.routes.get_db_connection')
    @patch('app.routes.hash_password')
    @patch('app.routes.create_session')
    def test_api_register_success(self, mock_create_session, mock_hash, mock_db, client):
        """Test successful registration."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # No existing user
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.side_effect = [
            None,  # First call: check existing user
            {'user_id': 1, 'user_name': 'newuser', 'user_email': 'new@example.com', 'user_role': 'normie'}  # Second call: get new user
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        mock_hash.return_value = 'hashed-password'
        mock_create_session.return_value = ('access-token', 'refresh-token', 'session-id')
        
        response = client.post('/api/register',
            json={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'password123',
                'confirm_password': 'password123'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_api_register_password_mismatch(self, client):
        """Test registration with mismatched passwords."""
        response = client.post('/api/register',
            json={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'password123',
                'confirm_password': 'different'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'match' in data['message'].lower()
    
    def test_api_register_short_password(self, client):
        """Test registration with password too short."""
        response = client.post('/api/register',
            json={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'short',
                'confirm_password': 'short'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert '8' in data['message'] or 'length' in data['message'].lower()


class TestLogoutAPI:
    """Test logout API endpoint."""
    
    @patch('app.routes.get_token_from_request')
    @patch('app.routes.verify_session_token')
    @patch('app.routes.invalidate_session')
    def test_api_logout_success(self, mock_invalidate, mock_verify, mock_get_token, client, mock_session_token):
        """Test successful logout."""
        mock_get_token.return_value = 'valid-token'
        mock_verify.return_value = (True, mock_session_token, None)
        mock_invalidate.return_value = True
        
        response = client.post('/api/logout',
            headers={'Authorization': 'Bearer valid-token'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('app.routes.get_token_from_request')
    def test_api_logout_no_token(self, mock_get_token, client):
        """Test logout without token."""
        mock_get_token.return_value = None
        
        response = client.post('/api/logout',
            content_type='application/json'
        )
        
        assert response.status_code == 401


class TestVerifySessionAPI:
    """Test session verification API endpoint."""
    
    @patch('app.routes.get_token_from_request')
    @patch('app.routes.verify_session_token')
    @patch('app.routes.get_db_connection')
    def test_api_verify_session_success(self, mock_db, mock_verify, mock_get_token, client, mock_session_token, sample_user):
        """Test successful session verification."""
        mock_get_token.return_value = 'valid-token'
        mock_verify.return_value = (True, mock_session_token, None)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'user_role': 'normie'}
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        response = client.get('/api/verify-session',
            headers={'Authorization': 'Bearer valid-token'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data


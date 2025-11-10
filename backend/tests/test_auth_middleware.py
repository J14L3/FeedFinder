"""
Tests for authentication middleware.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, request
from app.auth_middleware import (
    get_token_from_request,
    require_auth,
    optional_auth,
    set_auth_cookies,
    clear_auth_cookies,
    require_admin
)

class TestGetTokenFromRequest:
    """Test token extraction from requests."""
    
    def test_get_token_from_authorization_header(self, app):
        """Test extracting token from Authorization header."""
        with app.test_request_context(headers={'Authorization': 'Bearer test-token'}):
            token = get_token_from_request()
            assert token == 'test-token'
    
    def test_get_token_from_cookie(self, app):
        """Test extracting token from cookie."""
        with app.test_request_context():
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    with app.test_request_context(cookies={'access_token': 'cookie-token'}):
                        token = get_token_from_request()
                        assert token == 'cookie-token'
    
    def test_get_token_priority_header_over_cookie(self, app):
        """Test that Authorization header takes priority over cookie."""
        with app.test_request_context(
            headers={'Authorization': 'Bearer header-token'},
            cookies={'access_token': 'cookie-token'}
        ):
            token = get_token_from_request()
            assert token == 'header-token'
    
    def test_get_token_none_when_missing(self, app):
        """Test that None is returned when no token is present."""
        with app.test_request_context():
            token = get_token_from_request()
            assert token is None


class TestRequireAuth:
    """Test require_auth decorator."""
    
    @patch('app.auth_middleware.verify_session_token')
    @patch('app.auth_middleware.get_user_role_from_db')
    def test_require_auth_valid_token(self, mock_get_role, mock_verify, app):
        """Test that valid token allows access."""
        mock_verify.return_value = (True, {'user_id': 1, 'username': 'test'}, None)
        mock_get_role.return_value = 'normie'
        
        @require_auth
        def protected_route():
            return {'success': True}
        
        with app.test_request_context(headers={'Authorization': 'Bearer valid-token'}):
            result = protected_route()
            assert result['success'] is True
            assert hasattr(request, 'user_id')
            assert request.user_id == 1
    
    @patch('app.auth_middleware.get_token_from_request')
    def test_require_auth_no_token(self, mock_get_token, app):
        """Test that missing token is rejected."""
        mock_get_token.return_value = None
        
        @require_auth
        def protected_route():
            return {'success': True}
        
        with app.test_request_context():
            from flask import jsonify
            response = protected_route()
            assert response[1] == 401  # Status code
    
    @patch('app.auth_middleware.verify_session_token')
    @patch('app.auth_middleware.get_token_from_request')
    def test_require_auth_invalid_token(self, mock_get_token, mock_verify, app):
        """Test that invalid token is rejected."""
        mock_get_token.return_value = 'invalid-token'
        mock_verify.return_value = (False, None, 'Token expired')
        
        @require_auth
        def protected_route():
            return {'success': True}
        
        with app.test_request_context():
            response = protected_route()
            assert response[1] == 401


class TestOptionalAuth:
    """Test optional_auth decorator."""
    
    @patch('app.auth_middleware.verify_session_token')
    @patch('app.auth_middleware.get_user_role_from_db')
    def test_optional_auth_with_valid_token(self, mock_get_role, mock_verify, app):
        """Test that valid token sets user info."""
        mock_verify.return_value = (True, {'user_id': 1, 'username': 'test'}, None)
        mock_get_role.return_value = 'normie'
        
        @optional_auth
        def optional_route():
            return {'user_id': getattr(request, 'user_id', None)}
        
        with app.test_request_context(headers={'Authorization': 'Bearer valid-token'}):
            result = optional_route()
            assert result['user_id'] == 1
    
    @patch('app.auth_middleware.get_token_from_request')
    def test_optional_auth_without_token(self, mock_get_token, app):
        """Test that route works without token."""
        mock_get_token.return_value = None
        
        @optional_auth
        def optional_route():
            return {'user_id': getattr(request, 'user_id', None)}
        
        with app.test_request_context():
            result = optional_route()
            assert result['user_id'] is None


class TestSetAuthCookies:
    """Test setting authentication cookies."""
    
    def test_set_auth_cookies(self, app):
        """Test that cookies are set correctly."""
        from flask import make_response, jsonify
        
        response = make_response(jsonify({'success': True}))
        response = set_auth_cookies(response, 'access-token', 'refresh-token')
        
        cookies = [cookie for cookie in response.headers.getlist('Set-Cookie')]
        assert len(cookies) == 2
        assert any('access_token' in cookie for cookie in cookies)
        assert any('refresh_token' in cookie for cookie in cookies)


class TestClearAuthCookies:
    """Test clearing authentication cookies."""
    
    def test_clear_auth_cookies(self, app):
        """Test that cookies are cleared."""
        from flask import make_response, jsonify
        
        response = make_response(jsonify({'success': True}))
        response = clear_auth_cookies(response)
        
        cookies = [cookie for cookie in response.headers.getlist('Set-Cookie')]
        assert len(cookies) == 2
        assert all('expires=0' in cookie or 'Max-Age=0' in cookie for cookie in cookies)


class TestRequireAdmin:
    """Test require_admin decorator."""
    
    @patch('app.auth_middleware.get_user_role_from_db')
    def test_require_admin_with_admin_role(self, mock_get_role, app):
        """Test that admin role allows access."""
        mock_get_role.return_value = 'admin'
        
        @require_auth
        @require_admin
        def admin_route():
            return {'success': True}
        
        with app.test_request_context():
            # Mock request attributes set by require_auth
            request.user_id = 1
            request.user_role = 'admin'
            
            result = admin_route()
            assert result['success'] is True
    
    @patch('app.auth_middleware.get_user_role_from_db')
    def test_require_admin_with_normal_role(self, mock_get_role, app):
        """Test that non-admin role is rejected."""
        mock_get_role.return_value = 'normie'
        
        @require_auth
        @require_admin
        def admin_route():
            return {'success': True}
        
        with app.test_request_context():
            request.user_id = 1
            request.user_role = 'normie'
            
            response = admin_route()
            assert response[1] == 403  # Forbidden


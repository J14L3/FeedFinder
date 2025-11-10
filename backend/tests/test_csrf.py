"""
Tests for CSRF protection utilities.
"""
import pytest
from flask import session
from app.csrf import generate_csrf_token, validate_csrf_token, require_csrf
from datetime import datetime, timedelta

class TestCSRFToken:
    """Test CSRF token generation and validation."""
    
    def test_generate_csrf_token(self, app, client):
        """Test that CSRF token is generated and stored in session."""
        with app.test_request_context():
            with client.session_transaction() as sess:
                token = generate_csrf_token()
                
                assert token is not None
                assert isinstance(token, str)
                assert len(token) > 20
                assert 'csrf_token' in sess
                assert sess['csrf_token'] == token
                assert 'csrf_token_expiry' in sess
    
    def test_generate_csrf_token_reuses_existing(self, app, client):
        """Test that generate_csrf_token reuses existing token."""
        with app.test_request_context():
            with client.session_transaction() as sess:
                token1 = generate_csrf_token()
                token2 = generate_csrf_token()
                
                assert token1 == token2
    
    def test_validate_csrf_token_valid(self, app, client):
        """Test that valid CSRF token is accepted."""
        with app.test_request_context():
            with client.session_transaction() as sess:
                token = generate_csrf_token()
                assert validate_csrf_token(token) is True
    
    def test_validate_csrf_token_invalid(self, app, client):
        """Test that invalid CSRF token is rejected."""
        with app.test_request_context():
            with client.session_transaction() as sess:
                generate_csrf_token()
                assert validate_csrf_token("invalid-token") is False
    
    def test_validate_csrf_token_missing_session(self, app, client):
        """Test that validation fails when session has no token."""
        with app.test_request_context():
            assert validate_csrf_token("any-token") is False
    
    def test_validate_csrf_token_expired(self, app, client):
        """Test that expired CSRF token is rejected."""
        with app.test_request_context():
            with client.session_transaction() as sess:
                token = generate_csrf_token()
                # Set expiry to past
                sess['csrf_token_expiry'] = (datetime.utcnow() - timedelta(hours=1)).isoformat()
                
                assert validate_csrf_token(token) is False
                # Token should be removed from session
                assert 'csrf_token' not in sess


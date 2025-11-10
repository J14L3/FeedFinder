"""
Pytest configuration and fixtures for backend tests.
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from app import app as flask_app

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def app():
    """Create a test Flask application."""
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key-for-testing-only'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    return flask_app

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.rowcount = 0
    mock_cursor.lastrowid = 1
    return mock_conn, mock_cursor

@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        'user_id': 1,
        'user_name': 'testuser',
        'user_email': 'test@example.com',
        'password_hash': '$argon2id$v=19$m=51200,t=2,p=2$test$test',
        'user_role': 'normie',
        'bio': 'Test bio',
        'is_private': 0,
        'profile_picture': None
    }

@pytest.fixture
def sample_post():
    """Sample post data for testing."""
    return {
        'post_id': 1,
        'user_id': 1,
        'content_text': 'Test post content',
        'media_url': '/uploads/test.jpg',
        'media_type': 'image',
        'privacy': 'public',
        'created_at': '2024-01-01T00:00:00'
    }

@pytest.fixture
def auth_headers():
    """Create authentication headers with a mock token."""
    return {
        'Authorization': 'Bearer test-access-token',
        'Content-Type': 'application/json'
    }

@pytest.fixture
def mock_session_token():
    """Mock session token payload."""
    return {
        'user_id': 1,
        'username': 'testuser',
        'user_role': 'normie',
        'session_id': 'test-session-id',
        'fingerprint': 'test-fingerprint',
        'ip_address': '127.0.0.1',
        'iat': 1000000000,
        'exp': 1000003600,
        'type': 'access_token'
    }


"""
Integration tests for posts API endpoints.
"""
import pytest
import json
from unittest.mock import patch, MagicMock

class TestPublicPostsAPI:
    """Test public posts API endpoint."""
    
    @patch('app.routes.get_db_connection')
    def test_api_public_posts_success(self, mock_db, client):
        """Test fetching public posts."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'post_id': 1,
                'user_id': 1,
                'content_text': 'Test post',
                'media_url': None,
                'media_type': None,
                'privacy': 'public',
                'created_at': '2024-01-01',
                'user_name': 'testuser',
                'user_email': 'test@example.com'
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        response = client.get('/api/posts/public?limit=10')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'items' in data
        assert len(data['items']) == 1
    
    @patch('app.routes.get_db_connection')
    def test_api_public_posts_limit_validation(self, mock_db, client):
        """Test that limit parameter is validated."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        # Test with very large limit (should be capped)
        response = client.get('/api/posts/public?limit=1000')
        assert response.status_code == 200
        
        # Test with invalid limit (should default)
        response = client.get('/api/posts/public?limit=invalid')
        assert response.status_code == 200


class TestSearchPostsAPI:
    """Test search posts API endpoint."""
    
    @patch('app.routes.get_db_connection')
    def test_api_search_posts_success(self, mock_db, client):
        """Test searching posts."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'post_id': 1,
                'user_id': 1,
                'content_text': 'Test post with search term',
                'media_url': None,
                'media_type': None,
                'privacy': 'public',
                'created_at': '2024-01-01',
                'user_name': 'testuser',
                'user_email': 'test@example.com'
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        response = client.get('/api/posts/search?q=search')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'items' in data
    
    def test_api_search_posts_missing_query(self, client):
        """Test search without query parameter."""
        response = client.get('/api/posts/search')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_api_search_posts_query_too_long(self, client):
        """Test search with query too long."""
        long_query = 'a' * 201
        response = client.get(f'/api/posts/search?q={long_query}')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'long' in data['message'].lower()


class TestCreatePostAPI:
    """Test create post API endpoint."""
    
    @patch('app.routes.get_db_connection')
    def test_api_create_post_success(self, mock_db, client):
        """Test creating a post."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        response = client.post('/api/posts',
            json={
                'user_id': 1,
                'content_text': 'New post',
                'media_url': None,
                'privacy': 'public',
                'media_type': 'image'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert 'successfully' in data['message'].lower()


class TestUpdatePostAPI:
    """Test update post API endpoint."""
    
    @patch('app.routes.get_db_connection')
    def test_api_update_post_success(self, mock_db, client):
        """Test updating a post."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1  # One row updated
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        response = client.put('/api/posts/1',
            json={
                'user_id': 1,
                'content_text': 'Updated post',
                'media_url': None,
                'privacy': 'public'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
    
    @patch('app.routes.get_db_connection')
    def test_api_update_post_not_owner(self, mock_db, client):
        """Test updating a post that user doesn't own."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0  # No rows updated
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        response = client.put('/api/posts/1',
            json={
                'user_id': 999,  # Different user
                'content_text': 'Updated post',
                'media_url': None,
                'privacy': 'public'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 404


class TestDeletePostAPI:
    """Test delete post API endpoint."""
    
    @patch('app.routes.get_db_connection')
    def test_api_delete_post_success(self, mock_db, client):
        """Test deleting a post."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1  # One row deleted
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        response = client.delete('/api/posts/1',
            json={'user_id': 1},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
    
    @patch('app.routes.get_db_connection')
    def test_api_delete_post_not_owner(self, mock_db, client):
        """Test deleting a post that user doesn't own."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0  # No rows deleted
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        response = client.delete('/api/posts/1',
            json={'user_id': 999},  # Different user
            content_type='application/json'
        )
        
        assert response.status_code == 404


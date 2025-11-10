"""
Tests for password hashing utilities.
"""
import pytest
from app.hash import hash_password, verify_password

class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a valid hash."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed.startswith('$argon2id$')
        assert len(hashed) > 20  # Argon2 hashes are long
    
    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(hashed, password) is True
    
    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        assert verify_password(hashed, wrong_password) is False
    
    def test_verify_password_empty_password(self):
        """Test that empty password is rejected."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(hashed, "") is False
    
    def test_hash_password_empty_string(self):
        """Test that empty string can be hashed."""
        hashed = hash_password("")
        assert hashed is not None
        assert verify_password(hashed, "") is True


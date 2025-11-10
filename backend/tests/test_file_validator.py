"""
Tests for file validation utilities.
"""
import pytest
from io import BytesIO
from app.file_validator import (
    get_file_extension,
    sanitize_filename,
    verify_file_signature,
    verify_mime_type,
    validate_uploaded_file
)

class TestFileExtension:
    """Test file extension extraction."""
    
    def test_get_file_extension_valid(self):
        """Test extracting valid file extensions."""
        assert get_file_extension("test.jpg") == "jpg"
        assert get_file_extension("test.PNG") == "png"
        assert get_file_extension("test_file.jpeg") == "jpeg"
        assert get_file_extension("test.mp4") == "mp4"
    
    def test_get_file_extension_invalid(self):
        """Test that invalid extensions return None."""
        assert get_file_extension("test.txt") is None
        assert get_file_extension("test.exe") is None
        assert get_file_extension("test") is None
        assert get_file_extension("") is None
    
    def test_get_file_extension_multiple_dots(self):
        """Test handling files with multiple dots."""
        assert get_file_extension("test.file.jpg") == "jpg"
        assert get_file_extension("test.backup.png") == "png"


class TestSanitizeFilename:
    """Test filename sanitization."""
    
    def test_sanitize_filename_valid(self):
        """Test sanitizing valid filenames."""
        assert sanitize_filename("test.jpg") == "test.jpg"
        assert sanitize_filename("test_file-123.png") == "test_file-123.png"
        assert sanitize_filename("My File.jpeg") == "My File.jpeg"
    
    def test_sanitize_filename_path_traversal(self):
        """Test that path traversal attempts are blocked."""
        with pytest.raises(ValueError):
            sanitize_filename("../test.jpg")
        with pytest.raises(ValueError):
            sanitize_filename("../../etc/passwd")
        with pytest.raises(ValueError):
            sanitize_filename("test/../file.jpg")
    
    def test_sanitize_filename_dangerous_chars(self):
        """Test that dangerous characters are rejected."""
        with pytest.raises(ValueError):
            sanitize_filename("test*.jpg")
        with pytest.raises(ValueError):
            sanitize_filename("test?.png")
        with pytest.raises(ValueError):
            sanitize_filename("test<file>.jpg")
    
    def test_sanitize_filename_empty(self):
        """Test that empty filename raises error."""
        with pytest.raises(ValueError):
            sanitize_filename("")
    
    def test_sanitize_filename_null_bytes(self):
        """Test that null bytes are removed."""
        result = sanitize_filename("test\x00.jpg")
        assert "\x00" not in result


class TestFileSignature:
    """Test file signature verification."""
    
    def test_verify_png_signature(self):
        """Test PNG file signature verification."""
        # PNG signature: 89 50 4E 47 0D 0A 1A 0A
        png_header = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A' + b'\x00' * 12
        is_valid, ext = verify_file_signature(png_header, ['png'])
        assert is_valid is True
        assert ext == 'png'
    
    def test_verify_jpeg_signature(self):
        """Test JPEG file signature verification."""
        # JPEG signature: FF D8 FF
        jpeg_header = b'\xFF\xD8\xFF' + b'\x00' * 17
        is_valid, ext = verify_file_signature(jpeg_header, ['jpg'])
        assert is_valid is True
        assert ext == 'jpg'
    
    def test_verify_gif_signature(self):
        """Test GIF file signature verification."""
        # GIF signature: GIF8
        gif_header = b'GIF8' + b'\x00' * 16
        is_valid, ext = verify_file_signature(gif_header, ['gif'])
        assert is_valid is True
        assert ext == 'gif'
    
    def test_verify_invalid_signature(self):
        """Test that invalid signatures are rejected."""
        invalid_header = b'\x00\x01\x02\x03' + b'\x00' * 16
        is_valid, ext = verify_file_signature(invalid_header, ['jpg'])
        assert is_valid is False


class TestMimeType:
    """Test MIME type verification."""
    
    def test_verify_mime_type_valid(self):
        """Test valid MIME type verification."""
        is_valid, mime = verify_mime_type("image/jpeg", "test.jpg")
        assert is_valid is True
        assert mime == "image/jpeg"
    
    def test_verify_mime_type_mismatch(self):
        """Test that mismatched MIME types are rejected."""
        is_valid, mime = verify_mime_type("image/png", "test.jpg")
        assert is_valid is False
    
    def test_verify_mime_type_invalid(self):
        """Test that invalid MIME types are rejected."""
        is_valid, mime = verify_mime_type("application/octet-stream", "test.jpg")
        assert is_valid is False


class TestValidateUploadedFile:
    """Test comprehensive file validation."""
    
    def test_validate_valid_jpeg(self):
        """Test validation of a valid JPEG file."""
        # Create a mock JPEG file
        jpeg_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF' + b'\x00' * 13
        file_obj = BytesIO(jpeg_data)
        file_obj.filename = "test.jpg"
        
        is_valid, error, ext = validate_uploaded_file(
            file_obj, "test.jpg", "image/jpeg"
        )
        assert is_valid is True
        assert error == ""
        assert ext == "jpg"
    
    def test_validate_invalid_extension(self):
        """Test that files with invalid extensions are rejected."""
        file_obj = BytesIO(b'test content')
        file_obj.filename = "test.txt"
        
        is_valid, error, ext = validate_uploaded_file(
            file_obj, "test.txt", "text/plain"
        )
        assert is_valid is False
        assert "extension" in error.lower()
    
    def test_validate_path_traversal(self):
        """Test that path traversal attempts are blocked."""
        file_obj = BytesIO(b'test content')
        
        is_valid, error, ext = validate_uploaded_file(
            file_obj, "../etc/passwd", "image/jpeg"
        )
        assert is_valid is False
        assert "invalid" in error.lower()
    
    def test_validate_signature_mismatch(self):
        """Test that files with mismatched signatures are rejected."""
        # Create a file with .jpg extension but PNG signature
        png_data = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A' + b'\x00' * 12
        file_obj = BytesIO(png_data)
        file_obj.filename = "test.jpg"
        
        is_valid, error, ext = validate_uploaded_file(
            file_obj, "test.jpg", "image/jpeg"
        )
        assert is_valid is False
        assert "signature" in error.lower()


"""
File Validation Module
Provides secure file type verification using MIME types and magic bytes (file signatures).
This ensures uploaded files are actually media files and not malicious files with fake extensions.
"""

import os
import mimetypes
from typing import Tuple, Optional

# Allowed media file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "webm"}

# MIME types mapping for allowed media files
ALLOWED_MIME_TYPES = {
    # Images
    "image/png": ["png"],
    "image/jpeg": ["jpg", "jpeg"],
    "image/gif": ["gif"],
    # Videos
    "video/mp4": ["mp4"],
    "video/quicktime": ["mov"],
    "video/webm": ["webm"],
}

# File signatures (magic bytes) for media files
# Format: (signature_bytes, offset, file_extensions)
FILE_SIGNATURES = [
    # PNG: 89 50 4E 47 0D 0A 1A 0A
    (b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A', 0, ["png"]),
    
    # JPEG: FF D8 FF
    (b'\xFF\xD8\xFF', 0, ["jpg", "jpeg"]),
    
    # GIF: 47 49 46 38 (GIF8)
    (b'GIF8', 0, ["gif"]),
    
    # MP4: ftyp box at offset 4 (ftyp is at bytes 4-8)
    # MP4 files start with various ftyp signatures
    (b'ftyp', 4, ["mp4"]),
    (b'ftypisom', 4, ["mp4"]),
    (b'ftypmp41', 4, ["mp4"]),
    (b'ftypmp42', 4, ["mp4"]),
    
    # QuickTime/MOV: ftyp box at offset 4
    (b'ftypqt', 4, ["mov"]),
    
    # WebM: 1A 45 DF A3 (EBML header)
    (b'\x1A\x45\xDF\xA3', 0, ["webm"]),
]


def get_file_extension(filename: str) -> Optional[str]:
    """
    Safely extract file extension from filename.
    Returns lowercase extension without the dot, or None if invalid.
    """
    if not filename or '.' not in filename:
        return None
    
    # Split and get last part (handles multiple dots)
    parts = filename.rsplit('.', 1)
    if len(parts) != 2:
        return None
    
    ext = parts[1].lower().strip()
    
    # Validate extension is alphanumeric and in allowed list
    if ext and ext.isalnum() and ext in ALLOWED_EXTENSIONS:
        return ext
    
    return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other security issues.
    Returns a safe filename or raises ValueError if invalid.
    """
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    # Remove any path components (prevent path traversal)
    filename = os.path.basename(filename)
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Remove control characters
    filename = ''.join(c for c in filename if ord(c) >= 32 or c in (' ', '-', '_', '.'))
    
    # Limit length
    if len(filename) > 255:
        raise ValueError("Filename too long")
    
    # Check for dangerous patterns
    dangerous_patterns = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for pattern in dangerous_patterns:
        if pattern in filename:
            raise ValueError(f"Filename contains invalid characters: {pattern}")
    
    return filename


def verify_file_signature(file_content: bytes, expected_extensions: list) -> Tuple[bool, Optional[str]]:
    """
    Verify file signature (magic bytes) matches expected file type.
    
    Args:
        file_content: First bytes of the file (at least 20 bytes recommended for videos)
        expected_extensions: List of expected file extensions
    
    Returns:
        Tuple of (is_valid, detected_extension)
    """
    if len(file_content) < 4:
        return False, None
    
    # For video files, we need more bytes
    if any(ext in expected_extensions for ext in ['mp4', 'mov', 'webm']):
        if len(file_content) < 20:
            return False, None
    
    # Check each signature
    for signature, offset, extensions in FILE_SIGNATURES:
        # Check if any of the extensions match what we expect
        if not any(ext in expected_extensions for ext in extensions):
            continue
        
        # Check if signature matches at the specified offset
        if offset + len(signature) <= len(file_content):
            if file_content[offset:offset + len(signature)] == signature:
                # Return the first matching extension
                matching_ext = next((ext for ext in extensions if ext in expected_extensions), None)
                return True, matching_ext
    
    # Special handling for MP4/MOV: check for ftyp box at various positions
    # MP4/MOV files start with a box size (4 bytes) followed by 'ftyp'
    if any(ext in expected_extensions for ext in ['mp4', 'mov']):
        # Check at offset 4 (standard position)
        if len(file_content) >= 8 and file_content[4:8] == b'ftyp':
            # Determine if MP4 or MOV based on brand
            if len(file_content) >= 12:
                brand = file_content[8:12]
                if b'qt' in brand or b'quicktime' in brand.lower():
                    if 'mov' in expected_extensions:
                        return True, 'mov'
                elif b'mp4' in brand or b'isom' in brand or b'mp41' in brand or b'mp42' in brand:
                    if 'mp4' in expected_extensions:
                        return True, 'mp4'
                # Generic ftyp means it could be either, prefer MP4
                if 'mp4' in expected_extensions:
                    return True, 'mp4'
                elif 'mov' in expected_extensions:
                    return True, 'mov'
    
    return False, None


def verify_mime_type(content_type: Optional[str], filename: str) -> Tuple[bool, Optional[str]]:
    """
    Verify MIME type matches the file extension.
    
    Args:
        content_type: MIME type from Content-Type header
        filename: Original filename
    
    Returns:
        Tuple of (is_valid, detected_mime_type)
    """
    # Get extension from filename
    ext = get_file_extension(filename)
    if not ext:
        return False, None
    
    # If no content type provided, try to guess from extension
    if not content_type:
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type:
            content_type = guessed_type
        else:
            return False, None
    
    # Normalize MIME type (remove parameters like charset)
    content_type = content_type.split(';')[0].strip().lower()
    
    # Check if MIME type is allowed and matches extension
    if content_type in ALLOWED_MIME_TYPES:
        allowed_exts = ALLOWED_MIME_TYPES[content_type]
        if ext in allowed_exts:
            return True, content_type
    
    return False, None


def validate_uploaded_file(file, filename: str, content_type: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Comprehensive file validation for uploads.
    Validates extension, MIME type, and file signature.
    
    Args:
        file: File object (must support .read() and .seek())
        filename: Original filename
        content_type: Content-Type header value (optional)
    
    Returns:
        Tuple of (is_valid, error_message, detected_extension)
        If valid, error_message will be empty string and detected_extension will be the verified extension.
    """
    # 1. Sanitize filename
    try:
        sanitized_filename = sanitize_filename(filename)
    except ValueError as e:
        return False, f"Invalid filename: {str(e)}", None
    
    # 2. Validate file extension
    ext = get_file_extension(sanitized_filename)
    if not ext:
        return False, f"Invalid file extension. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}", None
    
    # 3. Verify MIME type
    mime_valid, detected_mime = verify_mime_type(content_type, sanitized_filename)
    if not mime_valid:
        return False, f"MIME type mismatch. File extension suggests {ext}, but Content-Type is invalid or doesn't match.", None
    
    # 4. Read file signature (magic bytes)
    try:
        # Save current position
        current_pos = file.tell()
        
        # Read first 20 bytes for signature verification (needed for video files)
        file.seek(0)
        file_header = file.read(20)
        
        # Restore position
        file.seek(current_pos)
        
        if len(file_header) < 4:
            return False, "File is too small or corrupted", None
        
        # Verify file signature matches extension
        signature_valid, detected_ext = verify_file_signature(file_header, [ext])
        if not signature_valid:
            return False, f"File signature verification failed. File content does not match the declared file type ({ext}). This may be a malicious file.", None
        
        # Double-check detected extension matches
        if detected_ext != ext:
            return False, f"File signature mismatch. Expected {ext}, but detected {detected_ext}", None
        
    except Exception as e:
        return False, f"Error reading file: {str(e)}", None
    
    # All checks passed
    return True, "", ext


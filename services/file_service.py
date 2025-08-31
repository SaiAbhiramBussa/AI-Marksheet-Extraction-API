"""
File Service for handling file validation and processing
"""

import logging
from typing import Dict, Any
from fastapi import UploadFile
import magic

logger = logging.getLogger(__name__)

class FileService:
    """Service for file validation and processing"""
    
    # Maximum file size in bytes (10 MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Supported file types
    SUPPORTED_IMAGE_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png'
    }
    
    SUPPORTED_PDF_TYPES = {
        'application/pdf'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.pdf'
    }
    
    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validate uploaded file for size, type, and format
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Read file content for validation
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Check file size
            if len(content) > self.MAX_FILE_SIZE:
                return {
                    "valid": False,
                    "error": f"File size ({len(content)} bytes) exceeds maximum allowed size ({self.MAX_FILE_SIZE} bytes)"
                }
            
            # Check if file is empty
            if len(content) == 0:
                return {
                    "valid": False,
                    "error": "File is empty"
                }
            
            # Validate file extension
            if not self._validate_extension(file.filename):
                return {
                    "valid": False,
                    "error": f"Unsupported file extension. Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
                }
            
            # Validate MIME type
            mime_validation = self._validate_mime_type(content, file.content_type)
            if not mime_validation["valid"]:
                return mime_validation
            
            # Additional file integrity checks
            integrity_check = self._check_file_integrity(content, file.filename)
            if not integrity_check["valid"]:
                return integrity_check
            
            return {
                "valid": True,
                "file_type": self.get_file_type(file.filename, file.content_type),
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return {
                "valid": False,
                "error": f"File validation failed: {str(e)}"
            }
    
    def _validate_extension(self, filename: str) -> bool:
        """Validate file extension"""
        if not filename:
            return False
        
        extension = '.' + filename.lower().split('.')[-1] if '.' in filename else ''
        return extension in self.SUPPORTED_EXTENSIONS
    
    def _validate_mime_type(self, content: bytes, declared_type: str) -> Dict[str, Any]:
        """Validate MIME type using python-magic"""
        try:
            # Detect actual MIME type
            detected_type = magic.from_buffer(content, mime=True)
            
            # Check if detected type is supported
            all_supported = self.SUPPORTED_IMAGE_TYPES | self.SUPPORTED_PDF_TYPES
            
            if detected_type not in all_supported:
                return {
                    "valid": False,
                    "error": f"Unsupported file type detected: {detected_type}"
                }
            
            # Warn if declared type doesn't match detected type
            if declared_type and declared_type != detected_type:
                logger.warning(f"MIME type mismatch: declared={declared_type}, detected={detected_type}")
            
            return {
                "valid": True,
                "detected_type": detected_type
            }
            
        except Exception as e:
            logger.error(f"MIME type validation error: {str(e)}")
            # Don't fail validation if magic detection fails
            return {"valid": True, "detected_type": declared_type}
    
    def _check_file_integrity(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Check basic file integrity"""
        try:
            file_type = self.get_file_type(filename, None)
            
            if file_type == 'pdf':
                # Check PDF header
                if not content.startswith(b'%PDF-'):
                    return {
                        "valid": False,
                        "error": "Invalid PDF file: missing PDF header"
                    }
            
            elif file_type == 'image':
                # Check common image headers
                valid_headers = [
                    b'\xff\xd8\xff',  # JPEG
                    b'\x89PNG\r\n\x1a\n',  # PNG
                ]
                
                if not any(content.startswith(header) for header in valid_headers):
                    return {
                        "valid": False,
                        "error": "Invalid image file: unrecognized image format"
                    }
            
            return {"valid": True}
            
        except Exception as e:
            logger.error(f"File integrity check error: {str(e)}")
            return {"valid": True}  # Don't fail on integrity check errors
    
    def get_file_type(self, filename: str, content_type: str) -> str:
        """
        Determine file type based on filename and content type
        
        Args:
            filename: Original filename
            content_type: MIME content type
            
        Returns:
            'image' or 'pdf'
        """
        if filename:
            extension = '.' + filename.lower().split('.')[-1] if '.' in filename else ''
            if extension == '.pdf':
                return 'pdf'
            elif extension in {'.jpg', '.jpeg', '.png'}:
                return 'image'
        
        if content_type:
            if content_type in self.SUPPORTED_PDF_TYPES:
                return 'pdf'
            elif content_type in self.SUPPORTED_IMAGE_TYPES:
                return 'image'
        
        # Default fallback based on extension
        if filename and filename.lower().endswith('.pdf'):
            return 'pdf'
        else:
            return 'image'
    
    def get_supported_formats_info(self) -> Dict[str, Any]:
        """Get information about supported formats"""
        return {
            "max_file_size_mb": self.MAX_FILE_SIZE // (1024 * 1024),
            "supported_extensions": list(self.SUPPORTED_EXTENSIONS),
            "supported_image_types": list(self.SUPPORTED_IMAGE_TYPES),
            "supported_pdf_types": list(self.SUPPORTED_PDF_TYPES)
        }

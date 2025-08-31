"""
Unit tests for the Marksheet Extraction API
"""

import pytest
import asyncio
import json
import io
from fastapi.testclient import TestClient
from PIL import Image

from main import app

client = TestClient(app)

class TestMarksheetExtractionAPI:
    """Test class for API endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_supported_formats(self):
        """Test supported formats endpoint"""
        response = client.get("/api/supported-formats")
        assert response.status_code == 200
        data = response.json()
        assert "supported_formats" in data
        assert "max_file_size_mb" in data
        assert "max_batch_files" in data
    
    def test_root_endpoint(self):
        """Test root endpoint serves HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_extract_no_file(self):
        """Test extract endpoint without file"""
        response = client.post("/api/extract")
        assert response.status_code == 422  # Validation error
    
    def test_extract_invalid_file_type(self):
        """Test extract endpoint with invalid file type"""
        # Create a text file
        test_content = b"This is not an image or PDF"
        
        response = client.post(
            "/api/extract",
            files={"file": ("test.txt", io.BytesIO(test_content), "text/plain")}
        )
        assert response.status_code == 400
        assert "validation failed" in response.json()["detail"].lower()
    
    def test_extract_oversized_file(self):
        """Test extract endpoint with oversized file"""
        # Create a large fake image (over 10MB)
        large_content = b"fake_image_data" * (1024 * 1024)  # ~15MB
        
        response = client.post(
            "/api/extract",
            files={"file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")}
        )
        assert response.status_code == 400
        assert "exceeds maximum allowed size" in response.json()["detail"]
    
    def test_extract_empty_file(self):
        """Test extract endpoint with empty file"""
        response = client.post(
            "/api/extract",
            files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def create_test_image(self, width=800, height=600):
        """Create a test image with some text-like content"""
        img = Image.new('RGB', (width, height), color='white')
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    def test_extract_valid_image_no_api_key(self):
        """Test extract endpoint with valid image but no API key"""
        import os
        # Temporarily remove API key if it exists
        original_key = os.environ.get("OPENAI_API_KEY")
        if original_key:
            del os.environ["OPENAI_API_KEY"]
        
        try:
            test_image = self.create_test_image()
            
            response = client.post(
                "/api/extract",
                files={"file": ("test.jpg", io.BytesIO(test_image), "image/jpeg")}
            )
            
            # Should fail due to missing API key
            assert response.status_code == 500
            
        finally:
            # Restore API key if it existed
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key
    
    def test_batch_extract_too_many_files(self):
        """Test batch extract with too many files"""
        test_image = self.create_test_image()
        
        # Create 6 files (exceeds limit of 5)
        files = []
        for i in range(6):
            files.append(("files", (f"test{i}.jpg", io.BytesIO(test_image), "image/jpeg")))
        
        response = client.post("/api/batch-extract", files=files)
        assert response.status_code == 400
        assert "Maximum 5 files allowed" in response.json()["detail"]
    
    def test_batch_extract_no_files(self):
        """Test batch extract without files"""
        response = client.post("/api/batch-extract")
        assert response.status_code == 422  # Validation error

class TestFileService:
    """Test class for file service functionality"""
    
    def test_file_validation_logic(self):
        """Test file validation logic"""
        from services.file_service import FileService
        file_service = FileService()
        
        # Test supported formats info
        info = file_service.get_supported_formats_info()
        assert info["max_file_size_mb"] == 10
        assert ".jpg" in info["supported_extensions"]
        assert ".pdf" in info["supported_extensions"]
        
        # Test file type detection
        assert file_service.get_file_type("test.jpg", "image/jpeg") == "image"
        assert file_service.get_file_type("test.pdf", "application/pdf") == "pdf"

class TestOCRService:
    """Test class for OCR service functionality"""
    
    def test_text_cleaning(self):
        """Test text cleaning functionality"""
        from services.ocr_service import OCRService
        ocr_service = OCRService()
        
        # Test text cleaning
        dirty_text = "\n\n  Line 1  \n\n  Line 2  \n\n"
        cleaned = ocr_service._clean_extracted_text(dirty_text)
        assert cleaned == "Line 1\nLine 2"
        
        # Test empty text
        assert ocr_service._clean_extracted_text("") == ""
        assert ocr_service._clean_extracted_text(None) == ""

class TestConfidenceCalculator:
    """Test class for confidence calculation"""
    
    def test_confidence_calculation(self):
        """Test confidence calculation methods"""
        from utils.confidence_calculator import ConfidenceCalculator
        calc = ConfidenceCalculator()
        
        # Test section confidence
        field_confidences = {"name": 0.9, "roll_no": 0.8}
        expected_fields = ["name", "roll_no", "date_of_birth"]
        
        confidence = calc.calculate_section_confidence(field_confidences, expected_fields)
        assert 0.0 <= confidence <= 1.0
        
        # Test overall confidence
        overall = calc.calculate_overall_confidence(0.8, [0.9, 0.7], 0.85, 0.6, {})
        assert 0.0 <= overall <= 1.0
        
        # Test explanation generation
        explanation = calc.generate_confidence_explanation(0.85, 5, 1000, {"text_clarity": 0.9})
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        
        # Test threshold recommendations
        thresholds = calc.get_confidence_threshold_recommendations()
        assert "high_accuracy_required" in thresholds
        assert "standard_processing" in thresholds

if __name__ == "__main__":
    pytest.main([__file__])

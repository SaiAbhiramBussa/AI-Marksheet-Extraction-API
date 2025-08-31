"""
AI-powered Marksheet Extraction API
FastAPI application for extracting structured data from marksheet images and PDFs
"""

import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

from models.schemas import MarksheetExtractionResponse, ErrorResponse
from services.file_service import FileService
from services.ocr_service import OCRService
from services.llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Marksheet Extraction API",
    description="AI-powered API for extracting structured data from marksheet images and PDFs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
file_service = FileService()
ocr_service = OCRService()
llm_service = LLMService()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the demo frontend page"""
    return FileResponse("static/index.html")

@app.post("/api/extract", response_model=MarksheetExtractionResponse)
async def extract_marksheet(
    file: UploadFile = File(..., description="Marksheet file (JPG/PNG/PDF, max 10MB)")
):
    """
    Extract structured data from marksheet image or PDF
    
    Args:
        file: Uploaded marksheet file (JPG/PNG/PDF format, max 10MB)
        
    Returns:
        Structured marksheet data with confidence scores
        
    Raises:
        HTTPException: For invalid files, processing errors, etc.
    """
    try:
        # Validate file
        file_validation = await file_service.validate_file(file)
        if not file_validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"File validation failed: {file_validation['error']}"
            )
        
        logger.info(f"Processing file: {file.filename}, type: {file.content_type}")
        
        # Read file content
        file_content = await file.read()
        file_type = file_service.get_file_type(file.filename, file.content_type)
        
        # Extract text using OCR
        extracted_text = await ocr_service.extract_text(file_content, file_type)
        if not extracted_text.strip():
            raise HTTPException(
                status_code=422,
                detail="No text could be extracted from the file. Please ensure the image is clear and contains readable text."
            )
        
        logger.info(f"Extracted text length: {len(extracted_text)} characters")
        
        # Process with LLM for structured extraction
        structured_data = await llm_service.extract_marksheet_data(extracted_text, file.filename)
        
        logger.info("Successfully extracted and structured marksheet data")
        return structured_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/batch-extract", response_model=list[MarksheetExtractionResponse])
async def batch_extract_marksheets(
    files: list[UploadFile] = File(..., description="Multiple marksheet files (max 5 files)")
):
    """
    Extract structured data from multiple marksheet files
    
    Args:
        files: List of uploaded marksheet files (max 5 files)
        
    Returns:
        List of structured marksheet data with confidence scores
    """
    if len(files) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 files allowed for batch processing"
        )
    
    results = []
    errors = []
    
    for i, file in enumerate(files):
        try:
            # Process each file individually
            result = await extract_marksheet(file)
            results.append(result)
        except HTTPException as e:
            errors.append(f"File {i+1} ({file.filename}): {e.detail}")
        except Exception as e:
            errors.append(f"File {i+1} ({file.filename}): Unexpected error - {str(e)}")
    
    if errors and not results:
        raise HTTPException(
            status_code=422,
            detail=f"All files failed processing: {'; '.join(errors)}"
        )
    
    return results

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Marksheet Extraction API",
        "version": "1.0.0"
    }

@app.get("/api/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats and size limits"""
    return {
        "supported_formats": ["JPG", "JPEG", "PNG", "PDF"],
        "max_file_size_mb": 10,
        "max_batch_files": 5
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

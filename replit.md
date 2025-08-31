# Overview

AI-powered REST API that extracts structured data from marksheet images and PDFs using OCR technology combined with Google Gemini for intelligent data structuring and validation. The system processes educational documents to extract candidate details, subject marks, overall results, and document metadata with confidence scoring for each extracted field.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## FastAPI Backend Framework
The application uses FastAPI as the primary web framework, chosen for its automatic OpenAPI documentation generation, built-in data validation with Pydantic, and high-performance async support. This enables efficient handling of file uploads and concurrent processing of multiple requests.

## Service-Oriented Architecture
The codebase follows a service-oriented pattern with clear separation of concerns:
- **File Service**: Handles file validation, type detection, and size limits (10MB max)
- **OCR Service**: Manages text extraction using Tesseract for images and PyMuPDF for PDFs
- **LLM Service**: Processes raw OCR text through OpenAI GPT-5 for structured data extraction
- **Confidence Calculator**: Provides reliability metrics for extracted data

## Data Processing Pipeline
The system implements a three-stage processing pipeline:
1. **File Validation**: Checks file type, size, and format compatibility
2. **OCR Extraction**: Converts document content to raw text using appropriate OCR engines
3. **AI Structuring**: Uses GPT-5 to parse and structure the raw text into predefined schemas

## Schema-Driven Data Modeling
Uses Pydantic models for strict data validation and serialization:
- **CandidateDetails**: Personal information and identifiers
- **SubjectMark**: Individual subject performance data
- **OverallResult**: Aggregate academic performance
- **DocumentInfo**: Metadata about the source document
- **ExtractionMetadata**: Processing information and confidence scores

## Frontend Interface
Includes a Bootstrap-based demo interface for interactive testing, featuring drag-and-drop file uploads, real-time validation feedback, and JSON response visualization with copy/download functionality.

## Error Handling and Validation
Implements comprehensive error handling with specific HTTP status codes, input validation at multiple levels, and graceful degradation when extraction confidence is low.

# External Dependencies

## AI/LLM Services
- **Google Gemini API**: Uses Gemini-2.5 model for intelligent text parsing and data structuring
- Requires GEMINI_API_KEY environment variable for authentication

## OCR Technologies
- **Tesseract OCR**: Primary OCR engine for image-based text extraction
- **PyMuPDF (fitz)**: Advanced PDF text extraction and handling
- **PyPDF2**: Fallback PDF processing library

## Image Processing
- **Pillow (PIL)**: Image manipulation and format conversion
- **python-magic**: File type detection and validation

## Web Framework Stack
- **FastAPI**: Core web framework with automatic API documentation
- **Uvicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and serialization

## Frontend Libraries
- **Bootstrap 5**: UI framework for responsive design
- **Font Awesome**: Icon library for enhanced user interface

## Development and Testing
- **Pytest**: Testing framework for unit and integration tests
- **Python-multipart**: File upload handling in FastAPI

## System Dependencies
- **Tesseract OCR**: Must be installed at system level for text extraction functionality
- Supports multiple image formats (JPG, PNG) and PDF documents
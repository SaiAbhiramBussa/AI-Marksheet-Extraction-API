# AI Marksheet Extraction API - Technical Approach

## Executive Summary

This document outlines the technical approach, design decisions, and confidence scoring methodology for the AI-powered marksheet extraction API. The system combines OCR technology with Large Language Models to extract structured data from educational documents with reliability metrics.

## System Architecture

### 1. Service-Oriented Design

The application follows a modular service-oriented architecture with clear separation of concerns:

- **FastAPI Framework**: Chosen for automatic OpenAPI documentation, built-in data validation, and high-performance async support
- **File Service**: Handles validation, type detection, and security checks
- **OCR Service**: Manages text extraction using multiple engines
- **LLM Service**: Processes raw text through AI for structured extraction
- **Confidence Calculator**: Provides reliability metrics for extracted data

### 2. Processing Pipeline

The system implements a three-stage pipeline:

1. **File Validation Stage**
   - MIME type verification using python-magic
   - File size limits (10MB maximum)
   - Format compatibility checks
   - Security header validation

2. **OCR Extraction Stage**
   - **Images**: Tesseract OCR with optimized configuration (`--oem 3 --psm 6 -l eng`)
   - **PDFs**: PyMuPDF for direct text extraction, fallback to PyPDF2
   - **Hybrid Processing**: OCR on PDF pages when direct text extraction fails

3. **AI Structuring Stage**
   - Google Gemini with structured JSON output format
   - Low temperature (0.1) for consistent extraction
   - Field-level confidence scoring through LLM analysis

## OCR Technology Implementation

### Multi-Engine Approach

**Primary Engine - Tesseract:**
- Configured with optimal settings for document processing
- Image preprocessing with PIL for format standardization
- Word-level confidence extraction for quality metrics

**PDF Processing - PyMuPDF:**
- Direct text extraction for searchable PDFs
- High-resolution image rendering (2x zoom) for OCR fallback
- Page-by-page processing with error recovery

### Text Quality Enhancement

- Whitespace normalization and line break handling
- Empty line removal while preserving structure
- Character encoding standardization

## LLM Integration Strategy

### Prompt Engineering

The system uses a structured prompt approach:

1. **System Prompt**: Establishes extraction guidelines and output format requirements
2. **User Prompt**: Provides detailed JSON schema with confidence field specifications
3. **Response Format**: Enforces JSON object output for reliable parsing

### Model Selection

**Google Gemini Selection Rationale:**
- Free API access with generous usage limits
- Superior accuracy for structured data extraction
- JSON mode for consistent output formatting
- Field-level confidence assessment capabilities
- Strong performance on educational document understanding
- Cost-effective solution for production deployment

### Error Handling

- Retry logic with exponential backoff for API rate limits
- Graceful degradation when LLM services are unavailable
- Comprehensive error messages for debugging

## Confidence Scoring Methodology

### Multi-Level Confidence Assessment

**1. Section-Level Confidence**
```python
confidence = base_confidence × (0.7 + 0.3 × completeness_ratio)
```

- **Base Confidence**: Average of individual field confidences
- **Completeness Penalty**: Reduces score for missing expected fields
- **Field Coverage**: Weighted by expected vs. found field count

**2. Overall Confidence Calculation**
```python
overall = weighted_average × (0.8 + 0.2 × quality_adjustment)
```

**Weighting Schema:**
- Candidate Details: 30% (identity verification critical)
- Subject Marks: 40% (primary academic data)
- Overall Result: 20% (summary information)
- Document Metadata: 10% (supplementary information)

**Quality Factors:**
- **Text Clarity**: OCR recognition quality
- **Completeness**: Field extraction coverage
- **Field Coverage**: Expected vs. actual field identification

### Confidence Thresholds

- **High Accuracy (≥0.85)**: Suitable for automated processing
- **Standard Processing (≥0.70)**: General use with minimal review
- **Basic Extraction (≥0.50)**: Preliminary processing acceptable
- **Manual Review (<0.60)**: Human verification recommended

## Design Decisions

### 1. Technology Stack Choices

**FastAPI over Flask/Django:**
- Automatic API documentation generation
- Built-in request validation with Pydantic
- Native async support for concurrent processing
- Type hints integration

**Multiple OCR Engines:**
- Tesseract for images (open-source, highly configurable)
- PyMuPDF for PDFs (better text extraction than PyPDF2)
- Fallback mechanisms ensure robust processing

**Pydantic for Data Validation:**
- Automatic request/response validation
- Type safety and serialization
- Clear error messages for malformed data

### 2. Scalability Considerations

**Async Processing:**
- Non-blocking file uploads
- Concurrent request handling
- Efficient I/O operations

**Stateless Design:**
- No session dependencies
- Horizontal scaling capability
- Independent request processing

**Memory Management:**
- Stream processing for large files
- Temporary file cleanup
- Resource-conscious OCR operations

### 3. Security Implementation

**Input Validation:**
- File type verification beyond extensions
- Magic number checking for format validation
- Size limits to prevent resource exhaustion
- Content sanitization

**Error Handling:**
- No sensitive information in error messages
- Structured error responses with appropriate HTTP codes
- Logging without exposing secrets

## Performance Optimizations

### 1. OCR Efficiency

- Image preprocessing optimization
- Selective OCR application (PDF text extraction first)
- Parallel processing capability for batch operations

### 2. LLM Cost Optimization

- Minimal token usage through structured prompts
- Efficient retry logic with exponential backoff
- Request batching for multiple files

### 3. Response Time Optimization

- Async/await patterns throughout
- Minimal blocking operations
- Efficient JSON serialization

## Error Handling Strategy

### 1. Input Validation Errors (400 series)

- File size exceeded: HTTP 400 with clear size limit message
- Invalid format: HTTP 400 with supported format list
- Empty file: HTTP 400 with descriptive error

### 2. Processing Errors (500 series)

- OCR failure: HTTP 422 with text extraction guidance
- LLM failure: HTTP 500 with general processing error
- System errors: HTTP 500 with generic error message (no sensitive data)

### 3. Rate Limiting and Quotas

- OpenAI rate limit handling with retry logic
- Graceful degradation when API quotas exceeded
- User-friendly error messages for quota issues

## Monitoring and Observability

### Logging Strategy

- Structured logging with appropriate levels
- Request processing time tracking
- Error categorization and counting
- No sensitive data in logs

### Metrics Collection

- Processing time per request
- Confidence score distributions
- Error rates by category
- File format success rates

## Future Enhancements

### 1. Model Improvements

- Fine-tuning for specific marksheet formats
- Multi-language support expansion
- Handwritten text recognition

### 2. Performance Scaling

- Caching for repeated similar documents
- Database storage for processed results
- Background processing queues

### 3. Feature Extensions

- Bounding box extraction for visual verification
- Multi-page document support
- Custom field configuration

## Conclusion

The AI Marksheet Extraction API demonstrates a robust, scalable approach to educational document processing. The combination of proven OCR technology with modern LLM capabilities provides reliable structured data extraction while maintaining transparency through comprehensive confidence scoring.

The service-oriented architecture ensures maintainability and extensibility, while the multi-level confidence assessment provides users with clear reliability metrics for extracted data. The system successfully balances accuracy, performance, and usability for production deployment scenarios.
# AI Marksheet Extraction API

An AI-powered REST API that extracts structured data from marksheet images and PDFs using OCR technology and Google Gemini for intelligent data structuring and validation.

## 🚀 Features

- **Multi-format Support**: Processes JPG, PNG, and PDF files (up to 10MB)
- **OCR Technology**: Advanced text extraction using Tesseract and PyMuPDF
- **AI-Powered Extraction**: Uses Google Gemini for intelligent data structuring
- **Confidence Scoring**: Provides reliability metrics for each extracted field
- **Batch Processing**: Supports processing multiple files simultaneously
- **RESTful API**: FastAPI-based with automatic OpenAPI documentation
- **Demo Interface**: Interactive web interface for testing
- **Concurrent Processing**: Handles multiple requests efficiently

## 📋 Extracted Data

The API extracts the following information from marksheets:

### Candidate Details
- Full name, Father's/Mother's name
- Roll number, Registration number
- Date of birth, Examination year
- Board/University, Institution name

### Academic Information
- Subject-wise marks (subject, max marks, obtained marks, grades)
- Overall result/grade/division
- Total marks, percentage, CGPA

### Document Metadata
- Issue date and place
- Document type
- Processing metadata with confidence scores

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **OCR**: Tesseract, PyMuPDF, PIL
- **AI/LLM**: Google Gemini
- **Data Validation**: Pydantic
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Testing**: Pytest

## 📦 Installation

### Prerequisites

- Python 3.8+
- Tesseract OCR (`sudo apt-get install tesseract-ocr` on Ubuntu)
- Google Gemini API key

### Setup

1. **Clone the repository**
   ```bash
   git clone "https://github.com/SaiAbhiramBussa/AI-Marksheet-Extraction-API.git"
   cd marksheet-extraction-api
   ```

2. **Install Python dependencies**
   ```bash
   pip install fastapi uvicorn python-multipart
   pip install pillow pytesseract PyPDF2 PyMuPDF
   pip install openai python-dotenv pydantic
   pip install python-magic pytest
   ```

3. **Set environment variables**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   export PORT=5000  # Optional, defaults to 5000
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:5000`

## 🔧 API Usage

### Single File Extraction

```bash
curl -X POST "http://localhost:5000/api/extract" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@marksheet.jpg"

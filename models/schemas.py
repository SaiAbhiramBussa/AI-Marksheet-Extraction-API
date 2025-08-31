"""
Pydantic models for API request/response schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SubjectMark(BaseModel):
    """Model for individual subject marks"""
    subject: str = Field(..., description="Subject name")
    max_marks: Optional[float] = Field(None, description="Maximum marks/credits for the subject")
    obtained_marks: Optional[float] = Field(None, description="Obtained marks/credits")
    grade: Optional[str] = Field(None, description="Grade assigned (if present)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this subject data")

class CandidateDetails(BaseModel):
    """Model for candidate personal details"""
    name: Optional[str] = Field(None, description="Candidate's full name")
    father_name: Optional[str] = Field(None, description="Father's name")
    mother_name: Optional[str] = Field(None, description="Mother's name")
    roll_no: Optional[str] = Field(None, description="Roll number")
    registration_no: Optional[str] = Field(None, description="Registration number")
    date_of_birth: Optional[str] = Field(None, description="Date of birth")
    exam_year: Optional[str] = Field(None, description="Examination year")
    board_university: Optional[str] = Field(None, description="Board or University name")
    institution: Optional[str] = Field(None, description="Institution/School/College name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence for candidate details")

class OverallResult(BaseModel):
    """Model for overall examination result"""
    result: Optional[str] = Field(None, description="Overall result (Pass/Fail/etc.)")
    grade: Optional[str] = Field(None, description="Overall grade")
    division: Optional[str] = Field(None, description="Division/Class achieved")
    percentage: Optional[float] = Field(None, description="Overall percentage")
    cgpa: Optional[float] = Field(None, description="CGPA if available")
    total_marks: Optional[float] = Field(None, description="Total marks obtained")
    max_total_marks: Optional[float] = Field(None, description="Maximum total marks")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for overall result")

class DocumentInfo(BaseModel):
    """Model for document metadata"""
    issue_date: Optional[str] = Field(None, description="Issue date of the marksheet")
    issue_place: Optional[str] = Field(None, description="Issue place of the marksheet")
    document_type: Optional[str] = Field(None, description="Type of document (marksheet, certificate, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for document info")

class ExtractionMetadata(BaseModel):
    """Model for extraction process metadata"""
    file_name: str = Field(..., description="Original filename")
    processing_time: float = Field(..., description="Processing time in seconds")
    extraction_method: str = Field(..., description="OCR method used")
    text_length: int = Field(..., description="Length of extracted text")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall extraction confidence")
    confidence_explanation: str = Field(..., description="Explanation of how confidence was calculated")

class MarksheetExtractionResponse(BaseModel):
    """Main response model for marksheet extraction"""
    candidate_details: CandidateDetails
    subjects: List[SubjectMark]
    overall_result: OverallResult
    document_info: DocumentInfo
    metadata: ExtractionMetadata
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_details": {
                    "name": "John Doe",
                    "father_name": "Robert Doe",
                    "mother_name": "Jane Doe",
                    "roll_no": "12345",
                    "registration_no": "REG001",
                    "date_of_birth": "01/01/2000",
                    "exam_year": "2023",
                    "board_university": "State Board",
                    "institution": "ABC School",
                    "confidence": 0.95
                },
                "subjects": [
                    {
                        "subject": "Mathematics",
                        "max_marks": 100,
                        "obtained_marks": 85,
                        "grade": "A",
                        "confidence": 0.98
                    }
                ],
                "overall_result": {
                    "result": "Pass",
                    "grade": "A",
                    "division": "First",
                    "percentage": 85.5,
                    "total_marks": 425,
                    "max_total_marks": 500,
                    "confidence": 0.92
                },
                "document_info": {
                    "issue_date": "15/06/2023",
                    "issue_place": "Mumbai",
                    "document_type": "Mark Sheet",
                    "confidence": 0.87
                },
                "metadata": {
                    "file_name": "marksheet.jpg",
                    "processing_time": 2.5,
                    "extraction_method": "OCR + LLM",
                    "text_length": 1245,
                    "overall_confidence": 0.93,
                    "confidence_explanation": "High confidence based on clear text extraction and complete field identification"
                }
            }
        }

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")

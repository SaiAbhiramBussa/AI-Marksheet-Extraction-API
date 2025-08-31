"""
LLM Service for structured data extraction using Google Gemini
"""

import json
import os
import logging
import time
from typing import Dict, Any
from google import genai
from google.genai import types
from pydantic import BaseModel

from models.schemas import (
    MarksheetExtractionResponse, CandidateDetails, SubjectMark, 
    OverallResult, DocumentInfo, ExtractionMetadata
)
from utils.confidence_calculator import ConfidenceCalculator

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM-based structured data extraction"""
    
    def __init__(self):
        # Using the newest Gemini model series "gemini-2.5-flash" for fast processing
        # gemini-2.5-pro is also available for higher accuracy if needed
        self.model = "gemini-2.5-flash"
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.confidence_calculator = ConfidenceCalculator()
        
    async def extract_marksheet_data(self, extracted_text: str, filename: str) -> MarksheetExtractionResponse:
        """
        Extract structured marksheet data using LLM
        
        Args:
            extracted_text: Raw text extracted from marksheet
            filename: Original filename for metadata
            
        Returns:
            Structured marksheet data with confidence scores
        """
        start_time = time.time()
        
        try:
            # Prepare the extraction prompt
            extraction_prompt = self._create_extraction_prompt(extracted_text)
            
            # Call Gemini API for structured extraction
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=extraction_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=self._get_system_prompt(),
                    response_mime_type="application/json",
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_output_tokens=4000  # Increased for complex JSON structure
                )
            )
            
            # Parse the LLM response
            raw_json = response.text
            logger.info(f"Gemini response text: {raw_json}")
            logger.info(f"Response candidates count: {len(response.candidates) if response.candidates else 0}")
            
            if response.candidates:
                candidate = response.candidates[0]
                logger.info(f"Candidate finish_reason: {candidate.finish_reason}")
                if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                    logger.info(f"Safety ratings: {candidate.safety_ratings}")
            
            if not raw_json:
                # Try to extract from candidates if text is empty
                if response.candidates and response.candidates[0].content:
                    parts = response.candidates[0].content.parts
                    if parts and parts[0].text:
                        raw_json = parts[0].text
                        logger.info(f"Extracted from candidates: {raw_json}")
                    else:
                        # Handle truncated response due to MAX_TOKENS
                        candidate = response.candidates[0]
                        if candidate.finish_reason and candidate.finish_reason.name == 'MAX_TOKENS':
                            logger.warning("Response truncated due to token limit, attempting shorter extraction")
                            return await self._fallback_extraction(extracted_text, filename)
                        else:
                            logger.error("No text found in response parts")
                            raise ValueError("Empty response from Gemini model")
                else:
                    logger.error("No candidates found in response")
                    raise ValueError("Empty response from Gemini model")
            
            llm_output = json.loads(raw_json)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Build structured response with confidence scores
            structured_response = self._build_structured_response(
                llm_output, extracted_text, filename, processing_time
            )
            
            logger.info(f"LLM extraction completed in {processing_time:.2f} seconds")
            return structured_response
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {str(e)}")
            raise Exception(f"Failed to extract structured data: {str(e)}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return """You are an expert at extracting structured data from educational marksheets and transcripts. 
        
Your task is to analyze the provided text and extract information into a well-structured JSON format.

IMPORTANT INSTRUCTIONS:
1. Extract only information that is clearly present in the text
2. Use null for fields that are not found or unclear
3. For confidence scores, consider text clarity, field completeness, and extraction certainty
4. Be especially careful with numbers - ensure marks, grades, and percentages are accurate
5. Normalize date formats to DD/MM/YYYY where possible
6. Identify the board/university and institution names carefully
7. For subjects, extract exact subject names as written
8. Calculate confidence based on how certain you are about each extracted field

Return ONLY valid JSON with no additional text or explanations."""

    def _create_extraction_prompt(self, text: str) -> str:
        """Create the extraction prompt for the LLM"""
        return f"""Extract marksheet data from this text and return it in the following simplified JSON structure:

{{
    "candidate_details": {{
        "name": "Full name of candidate",
        "father_name": "Father's name",
        "mother_name": "Mother's name", 
        "roll_no": "Roll number",
        "registration_no": "Registration number",
        "date_of_birth": "Date of birth (DD/MM/YYYY format)",
        "exam_year": "Examination year",
        "board_university": "Board or University name",
        "institution": "School/College/Institution name"
    }},
    "subjects": [
        {{
            "subject": "Subject name",
            "max_marks": 100.0,
            "obtained_marks": 85.0,
            "grade": "Grade if present"
        }}
    ],
    "overall_result": {{
        "result": "Pass/Fail/etc",
        "grade": "Overall grade",
        "division": "Division/Class",
        "percentage": 85.5,
        "cgpa": 8.5,
        "total_marks": 425.0,
        "max_total_marks": 500.0
    }},
    "document_info": {{
        "issue_date": "DD/MM/YYYY",
        "issue_place": "Issue place",
        "document_type": "Mark Sheet/Certificate/etc"
    }}
}}

IMPORTANT: Use null for fields that are not found or unclear.

MARKSHEET TEXT:
{text}"""

    def _build_structured_response(
        self, 
        llm_output: Dict[Any, Any], 
        original_text: str, 
        filename: str, 
        processing_time: float
    ) -> MarksheetExtractionResponse:
        """Build the final structured response with confidence scores"""
        
        # Extract candidate details
        candidate_data = llm_output.get("candidate_details", {})
        # Calculate confidence algorithmically since we removed field_confidence from LLM response
        candidate_confidence = self.confidence_calculator.calculate_candidate_confidence(candidate_data)
        
        candidate_details = CandidateDetails(
            name=candidate_data.get("name"),
            father_name=candidate_data.get("father_name"),
            mother_name=candidate_data.get("mother_name"),
            roll_no=candidate_data.get("roll_no"),
            registration_no=candidate_data.get("registration_no"),
            date_of_birth=candidate_data.get("date_of_birth"),
            exam_year=candidate_data.get("exam_year"),
            board_university=candidate_data.get("board_university"),
            institution=candidate_data.get("institution"),
            confidence=candidate_confidence
        )
        
        # Extract subjects
        subjects_data = llm_output.get("subjects", [])
        subjects = []
        
        for subject_data in subjects_data:
            # Calculate confidence algorithmically since we removed field_confidence from LLM response
            subject_confidence = self.confidence_calculator.calculate_subject_confidence(subject_data)
            
            subject = SubjectMark(
                subject=subject_data.get("subject"),
                max_marks=subject_data.get("max_marks"),
                obtained_marks=subject_data.get("obtained_marks"),
                grade=subject_data.get("grade"),
                confidence=subject_confidence
            )
            subjects.append(subject)
        
        # Extract overall result
        result_data = llm_output.get("overall_result", {})
        # Calculate confidence algorithmically since we removed field_confidence from LLM response
        result_confidence = self.confidence_calculator.calculate_result_confidence(result_data)
        
        overall_result = OverallResult(
            result=result_data.get("result"),
            grade=result_data.get("grade"),
            division=result_data.get("division"),
            percentage=result_data.get("percentage"),
            cgpa=result_data.get("cgpa"),
            total_marks=result_data.get("total_marks"),
            max_total_marks=result_data.get("max_total_marks"),
            confidence=result_confidence
        )
        
        # Extract document info
        doc_data = llm_output.get("document_info", {})
        # Calculate confidence algorithmically since we removed field_confidence from LLM response
        doc_confidence = self.confidence_calculator.calculate_document_confidence(doc_data)
        
        document_info = DocumentInfo(
            issue_date=doc_data.get("issue_date"),
            issue_place=doc_data.get("issue_place"),
            document_type=doc_data.get("document_type"),
            confidence=doc_confidence
        )
        
        # Calculate overall confidence
        extraction_quality = {"text_clarity": 0.7, "completeness": 0.8, "field_coverage": 0.75}  # Default values
        overall_confidence = self.confidence_calculator.calculate_overall_confidence(
            candidate_confidence,
            [s.confidence for s in subjects],
            result_confidence,
            doc_confidence,
            extraction_quality
        )
        
        # Generate confidence explanation
        confidence_explanation = self.confidence_calculator.generate_confidence_explanation(
            overall_confidence,
            len(subjects),
            len(original_text),
            extraction_quality
        )
        
        # Build metadata
        metadata = ExtractionMetadata(
            file_name=filename,
            processing_time=processing_time,
            extraction_method="OCR + LLM (Gemini-2.5)",
            text_length=len(original_text),
            overall_confidence=overall_confidence,
            confidence_explanation=confidence_explanation
        )
        
        return MarksheetExtractionResponse(
            candidate_details=candidate_details,
            subjects=subjects,
            overall_result=overall_result,
            document_info=document_info,
            metadata=metadata
        )

    async def _fallback_extraction(self, extracted_text: str, filename: str) -> MarksheetExtractionResponse:
        """Fallback extraction with simpler prompt for problematic cases"""
        start_time = time.time()
        
        try:
            # Use a much simpler prompt for basic extraction
            simple_prompt = f"""Extract basic information from this marksheet text and return as JSON:
            
{{
    "candidate_details": {{"name": "student name", "roll_no": "roll number", "exam_year": "year"}},
    "subjects": [{{"subject": "subject name", "obtained_marks": 0, "max_marks": 100}}],
    "overall_result": {{"result": "Pass/Fail", "percentage": 0}},
    "document_info": {{"document_type": "marksheet"}}
}}

Text: {extracted_text[:500]}"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=simple_prompt)])
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=1000  # Much smaller limit
                )
            )
            
            raw_json = response.text
            if not raw_json and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                raw_json = response.candidates[0].content.parts[0].text
            
            if not raw_json:
                raw_json = "{}"
                
            llm_output = json.loads(raw_json)
            
            processing_time = time.time() - start_time
            
            # Build basic response with default confidence scores
            return self._build_basic_response(llm_output, extracted_text, filename, processing_time)
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {str(e)}")
            # Return minimal response if everything fails
            return self._build_minimal_response(extracted_text, filename)
    
    def _build_basic_response(self, llm_output: Dict[Any, Any], original_text: str, filename: str, processing_time: float) -> MarksheetExtractionResponse:
        """Build basic response from simplified extraction"""
        
        # Basic candidate details
        candidate_data = llm_output.get("candidate_details", {})
        candidate_details = CandidateDetails(
            name=candidate_data.get("name"),
            father_name=None,
            mother_name=None,
            roll_no=candidate_data.get("roll_no"),
            registration_no=None,
            date_of_birth=None,
            exam_year=candidate_data.get("exam_year"),
            board_university=None,
            institution=None,
            confidence=0.5  # Medium confidence for basic extraction
        )
        
        # Basic subjects
        subjects_data = llm_output.get("subjects", [])
        subjects = []
        for subject_data in subjects_data:
            subject = SubjectMark(
                subject=subject_data.get("subject"),
                max_marks=subject_data.get("max_marks", 100),
                obtained_marks=subject_data.get("obtained_marks"),
                grade=None,
                confidence=0.5
            )
            subjects.append(subject)
        
        # Basic result
        result_data = llm_output.get("overall_result", {})
        overall_result = OverallResult(
            result=result_data.get("result"),
            grade=None,
            division=None,
            percentage=result_data.get("percentage"),
            cgpa=None,
            total_marks=None,
            max_total_marks=None,
            confidence=0.5
        )
        
        # Basic document info
        doc_data = llm_output.get("document_info", {})
        document_info = DocumentInfo(
            issue_date=None,
            issue_place=None,
            document_type=doc_data.get("document_type", "marksheet"),
            confidence=0.4
        )
        
        # Basic metadata
        metadata = ExtractionMetadata(
            file_name=filename,
            processing_time=processing_time,
            extraction_method="OCR + LLM (Gemini-2.5) - Fallback Mode",
            text_length=len(original_text),
            overall_confidence=0.5,
            confidence_explanation="Basic extraction mode due to processing constraints; moderate confidence; partial data extracted"
        )
        
        return MarksheetExtractionResponse(
            candidate_details=candidate_details,
            subjects=subjects,
            overall_result=overall_result,
            document_info=document_info,
            metadata=metadata
        )
    
    def _build_minimal_response(self, original_text: str, filename: str) -> MarksheetExtractionResponse:
        """Build minimal response when all extraction methods fail"""
        
        # Minimal candidate details
        candidate_details = CandidateDetails(
            name="Could not extract",
            father_name=None,
            mother_name=None,
            roll_no=None,
            registration_no=None,
            date_of_birth=None,
            exam_year=None,
            board_university=None,
            institution=None,
            confidence=0.1
        )
        
        # Empty subjects list
        subjects = []
        
        # Minimal result
        overall_result = OverallResult(
            result="Unknown",
            grade=None,
            division=None,
            percentage=None,
            cgpa=None,
            total_marks=None,
            max_total_marks=None,
            confidence=0.1
        )
        
        # Minimal document info
        document_info = DocumentInfo(
            issue_date=None,
            issue_place=None,
            document_type="marksheet",
            confidence=0.1
        )
        
        # Minimal metadata
        metadata = ExtractionMetadata(
            file_name=filename,
            processing_time=0.1,
            extraction_method="OCR + LLM (Gemini-2.5) - Minimal Mode",
            text_length=len(original_text),
            overall_confidence=0.1,
            confidence_explanation="Minimal extraction due to processing difficulties; low confidence; manual review recommended"
        )
        
        return MarksheetExtractionResponse(
            candidate_details=candidate_details,
            subjects=subjects,
            overall_result=overall_result,
            document_info=document_info,
            metadata=metadata
        )

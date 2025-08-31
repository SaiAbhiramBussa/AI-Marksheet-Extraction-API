"""
Confidence Calculator for determining extraction confidence scores
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ConfidenceCalculator:
    """Calculator for confidence scores in marksheet extraction"""
    
    def calculate_section_confidence(self, field_confidences: Dict[str, float], expected_fields: List[str]) -> float:
        """
        Calculate confidence for a section based on field-level confidences
        
        Args:
            field_confidences: Dictionary of field confidence scores
            expected_fields: List of expected field names
            
        Returns:
            Section confidence score (0-1)
        """
        if not field_confidences or not expected_fields:
            return 0.3  # Low confidence for missing data
        
        # Get confidences for expected fields
        valid_confidences = []
        for field in expected_fields:
            if field in field_confidences and field_confidences[field] is not None:
                valid_confidences.append(field_confidences[field])
        
        if not valid_confidences:
            return 0.2  # Very low confidence if no field confidences
        
        # Calculate weighted average
        base_confidence = sum(valid_confidences) / len(valid_confidences)
        
        # Apply penalty for missing fields
        completeness_ratio = len(valid_confidences) / len(expected_fields)
        adjusted_confidence = base_confidence * (0.7 + 0.3 * completeness_ratio)
        
        return max(0.0, min(1.0, adjusted_confidence))
    
    def calculate_overall_confidence(
        self,
        candidate_confidence: float,
        subject_confidences: List[float],
        result_confidence: float,
        doc_confidence: float,
        extraction_quality: Dict[str, float]
    ) -> float:
        """
        Calculate overall extraction confidence
        
        Args:
            candidate_confidence: Confidence for candidate details
            subject_confidences: List of confidence scores for subjects
            result_confidence: Confidence for overall result
            doc_confidence: Confidence for document info
            extraction_quality: Quality metrics from LLM
            
        Returns:
            Overall confidence score (0-1)
        """
        # Weight different sections based on importance
        weights = {
            'candidate': 0.3,
            'subjects': 0.4,
            'result': 0.2,
            'document': 0.1
        }
        
        # Calculate subject average confidence
        subject_avg = sum(subject_confidences) / len(subject_confidences) if subject_confidences else 0.3
        
        # Calculate weighted average
        weighted_confidence = (
            weights['candidate'] * candidate_confidence +
            weights['subjects'] * subject_avg +
            weights['result'] * result_confidence +
            weights['document'] * doc_confidence
        )
        
        # Apply extraction quality factors
        quality_factors = extraction_quality or {}
        text_clarity = quality_factors.get('text_clarity', 0.7)
        completeness = quality_factors.get('completeness', 0.7)
        field_coverage = quality_factors.get('field_coverage', 0.7)
        
        quality_adjustment = (text_clarity + completeness + field_coverage) / 3
        
        # Final confidence with quality adjustment
        final_confidence = weighted_confidence * (0.8 + 0.2 * quality_adjustment)
        
        return max(0.1, min(1.0, final_confidence))
    
    def generate_confidence_explanation(
        self,
        overall_confidence: float,
        subject_count: int,
        text_length: int,
        extraction_quality: Dict[str, float]
    ) -> str:
        """
        Generate human-readable explanation of confidence score
        
        Args:
            overall_confidence: Overall confidence score
            subject_count: Number of subjects extracted
            text_length: Length of extracted text
            extraction_quality: Quality metrics
            
        Returns:
            Confidence explanation string
        """
        explanations = []
        
        # Base confidence assessment
        if overall_confidence >= 0.9:
            explanations.append("Very high confidence extraction")
        elif overall_confidence >= 0.75:
            explanations.append("High confidence extraction")
        elif overall_confidence >= 0.6:
            explanations.append("Good confidence extraction")
        elif overall_confidence >= 0.4:
            explanations.append("Moderate confidence extraction")
        else:
            explanations.append("Low confidence extraction")
        
        # Text quality factors
        if text_length > 500:
            explanations.append("sufficient text content extracted")
        elif text_length > 200:
            explanations.append("moderate text content extracted")
        else:
            explanations.append("limited text content extracted")
        
        # Subject coverage
        if subject_count >= 5:
            explanations.append("comprehensive subject data found")
        elif subject_count >= 3:
            explanations.append("good subject coverage")
        elif subject_count >= 1:
            explanations.append("basic subject information found")
        else:
            explanations.append("limited subject data available")
        
        # Quality factors
        quality = extraction_quality or {}
        text_clarity = quality.get('text_clarity', 0.7)
        completeness = quality.get('completeness', 0.7)
        
        if text_clarity >= 0.8:
            explanations.append("clear text recognition")
        elif text_clarity >= 0.6:
            explanations.append("good text clarity")
        else:
            explanations.append("some text recognition challenges")
        
        if completeness >= 0.8:
            explanations.append("complete field extraction")
        elif completeness >= 0.6:
            explanations.append("most fields extracted successfully")
        else:
            explanations.append("partial field extraction")
        
        return "; ".join(explanations)
    
    def calculate_candidate_confidence(self, candidate_data: Dict[str, Any]) -> float:
        """Calculate confidence for candidate details section"""
        if not candidate_data:
            return 0.2
        
        # Count non-null fields
        non_null_fields = sum(1 for value in candidate_data.values() if value is not None and str(value).strip())
        total_fields = len(candidate_data)
        
        if total_fields == 0:
            return 0.2
        
        # Base confidence from completeness
        completeness_ratio = non_null_fields / total_fields
        base_confidence = 0.4 + (0.5 * completeness_ratio)
        
        # Boost for key fields
        key_fields = ['name', 'roll_no', 'exam_year']
        key_field_score = sum(1 for field in key_fields if candidate_data.get(field))
        key_boost = (key_field_score / len(key_fields)) * 0.1
        
        return max(0.2, min(1.0, base_confidence + key_boost))
    
    def calculate_subject_confidence(self, subject_data: Dict[str, Any]) -> float:
        """Calculate confidence for a single subject"""
        if not subject_data:
            return 0.2
        
        # Essential fields for a subject
        essential_fields = ['subject', 'obtained_marks']
        has_essential = sum(1 for field in essential_fields if subject_data.get(field) is not None)
        
        if has_essential == 0:
            return 0.1
        
        # Base confidence from essential fields
        base_confidence = 0.3 + (has_essential / len(essential_fields)) * 0.4
        
        # Bonus for having marks and max_marks
        if subject_data.get('obtained_marks') is not None and subject_data.get('max_marks') is not None:
            base_confidence += 0.2
        
        # Bonus for having grade
        if subject_data.get('grade'):
            base_confidence += 0.1
        
        return max(0.1, min(1.0, base_confidence))
    
    def calculate_result_confidence(self, result_data: Dict[str, Any]) -> float:
        """Calculate confidence for overall result section"""
        if not result_data:
            return 0.2
        
        # Count meaningful fields
        meaningful_fields = sum(1 for value in result_data.values() if value is not None and str(value).strip())
        total_fields = len(result_data)
        
        if total_fields == 0:
            return 0.2
        
        base_confidence = 0.3 + (meaningful_fields / total_fields) * 0.4
        
        # Boost for key result indicators
        if result_data.get('result'):
            base_confidence += 0.2
        if result_data.get('percentage') or result_data.get('cgpa'):
            base_confidence += 0.1
        
        return max(0.2, min(1.0, base_confidence))
    
    def calculate_document_confidence(self, doc_data: Dict[str, Any]) -> float:
        """Calculate confidence for document info section"""
        if not doc_data:
            return 0.3
        
        # Count non-null fields
        non_null_fields = sum(1 for value in doc_data.values() if value is not None and str(value).strip())
        total_fields = len(doc_data)
        
        if total_fields == 0:
            return 0.3
        
        # Base confidence (document info is often less reliable)
        base_confidence = 0.4 + (non_null_fields / total_fields) * 0.3
        
        return max(0.3, min(1.0, base_confidence))
    
    def get_confidence_threshold_recommendations(self) -> Dict[str, float]:
        """
        Get recommended confidence thresholds for different use cases
        
        Returns:
            Dictionary of threshold recommendations
        """
        return {
            "high_accuracy_required": 0.85,  # For critical applications
            "standard_processing": 0.70,     # For general use
            "basic_extraction": 0.50,        # For preliminary processing
            "manual_review_below": 0.60      # Below this, recommend manual review
        }

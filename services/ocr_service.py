"""
OCR Service for extracting text from images and PDFs
"""

import logging
import io
import base64
from typing import Tuple
import pytesseract
from PIL import Image
import PyPDF2
import fitz  # PyMuPDF for better PDF handling

logger = logging.getLogger(__name__)

class OCRService:
    """Service for OCR text extraction from images and PDFs"""
    
    def __init__(self):
        # Configure Tesseract for better accuracy
        self.tesseract_config = '--oem 3 --psm 6 -l eng'
        
    async def extract_text(self, file_content: bytes, file_type: str) -> str:
        """
        Extract text from file content using appropriate method
        
        Args:
            file_content: Raw file bytes
            file_type: File type ('image' or 'pdf')
            
        Returns:
            Extracted text string
            
        Raises:
            Exception: If text extraction fails
        """
        try:
            if file_type == 'pdf':
                return await self._extract_text_from_pdf(file_content)
            elif file_type == 'image':
                return await self._extract_text_from_image(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise Exception(f"Text extraction failed: {str(e)}")
    
    async def _extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Extracted text string
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR with optimized settings
            text = pytesseract.image_to_string(
                image, 
                config=self.tesseract_config
            )
            
            # Clean up the text
            cleaned_text = self._clean_extracted_text(text)
            
            logger.info(f"Extracted {len(cleaned_text)} characters from image")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Image OCR failed: {str(e)}")
            raise Exception(f"Failed to extract text from image: {str(e)}")
    
    async def _extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF using PyMuPDF and fallback to PyPDF2
        
        Args:
            pdf_bytes: Raw PDF bytes
            
        Returns:
            Extracted text string
        """
        extracted_text = ""
        
        try:
            # Try PyMuPDF first (better for complex PDFs)
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                page_text = page.get_text()
                
                # If no text extracted, try OCR on the page image
                if not page_text.strip():
                    logger.info(f"No text found on page {page_num + 1}, attempting OCR...")
                    page_text = await self._ocr_pdf_page(page)
                
                extracted_text += page_text + "\n"
            
            pdf_document.close()
            
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {str(e)}, trying PyPDF2...")
            
            # Fallback to PyPDF2
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    extracted_text += page_text + "\n"
                    
            except Exception as e2:
                logger.error(f"Both PDF extraction methods failed: {str(e2)}")
                raise Exception(f"Failed to extract text from PDF: {str(e2)}")
        
        cleaned_text = self._clean_extracted_text(extracted_text)
        logger.info(f"Extracted {len(cleaned_text)} characters from PDF")
        return cleaned_text
    
    async def _ocr_pdf_page(self, page) -> str:
        """
        Perform OCR on a PDF page image
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            Extracted text from page image
        """
        try:
            # Render page as image
            mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image and perform OCR
            image = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            
            return text
            
        except Exception as e:
            logger.error(f"PDF page OCR failed: {str(e)}")
            return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        
        # Remove excessive whitespace and normalize line breaks
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def get_text_confidence(self, file_content: bytes, file_type: str) -> float:
        """
        Get confidence score for OCR extraction
        
        Args:
            file_content: Raw file bytes
            file_type: File type ('image' or 'pdf')
            
        Returns:
            Confidence score between 0 and 1
        """
        try:
            if file_type == 'image':
                image = Image.open(io.BytesIO(file_content))
                
                # Get word-level confidence from Tesseract
                data = pytesseract.image_to_data(
                    image, 
                    output_type=pytesseract.Output.DICT,
                    config=self.tesseract_config
                )
                
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                
                if not confidences:
                    return 0.1  # Very low confidence if no words detected
                
                avg_confidence = sum(confidences) / len(confidences)
                return min(1.0, avg_confidence / 100.0)  # Normalize to 0-1
                
            else:  # PDF
                # For PDFs, confidence is based on whether text was directly extractable
                return 0.9  # High confidence for direct text extraction
                
        except Exception as e:
            logger.error(f"Confidence calculation failed: {str(e)}")
            return 0.5  # Medium confidence as fallback

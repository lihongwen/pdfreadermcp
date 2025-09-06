"""
PDF OCR tool using EasyOCR for scanned document recognition.
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import json

try:
    import pdf2image
except ImportError:
    pdf2image = None

try:
    import easyocr
except ImportError:
    easyocr = None

from PIL import Image
import numpy as np

from ..utils.file_handler import FileHandler
from ..utils.chunker import TextChunker
from ..utils.cache import PDFCache


class PDFOCR:
    """
    PDF OCR tool using EasyOCR for processing scanned documents and images.
    """
    
    def __init__(self):
        """Initialize the PDF OCR tool with cache and OCR engine."""
        self.cache = PDFCache(max_entries=30, max_age_seconds=3600)  # 1 hour cache
        self.file_handler = FileHandler()
        self._ocr_reader = None
    
    def _get_ocr_reader(self, languages: List[str] = ['ch_sim', 'en'], use_gpu: bool = False) -> Any:
        """
        Get or create EasyOCR Reader instance.
        
        Args:
            languages: List of language codes for OCR
            use_gpu: Whether to use GPU acceleration
            
        Returns:
            EasyOCR Reader instance
        """
        if easyocr is None:
            raise ImportError("EasyOCR is not installed. Please install it with: pip install easyocr")
        
        # Create new reader if needed or languages changed
        current_languages = getattr(self._ocr_reader, '_languages', [])
        if self._ocr_reader is None or current_languages != languages:
            try:
                # Initialize EasyOCR Reader with specified languages
                self._ocr_reader = easyocr.Reader(
                    lang_list=languages,
                    gpu=use_gpu
                )
                self._ocr_reader._languages = languages  # Store languages for comparison
            except Exception as e:
                raise RuntimeError(f"Failed to initialize EasyOCR: {str(e)}")
        
        return self._ocr_reader
    
    async def extract_text_ocr(
        self,
        file_path: Union[str, Path],
        pages: Optional[str] = None,
        language: str = "ch_sim,en",
        chunk_size: int = 1000,
        use_gpu: bool = False
    ) -> str:
        """
        Extract text from PDF using OCR with EasyOCR.
        
        Args:
            file_path: Path to PDF file
            pages: Page range string (e.g., "1,3,5-10,-1")
            language: OCR language codes (e.g., "ch_sim,en")
            chunk_size: Maximum size of text chunks
            use_gpu: Whether to use GPU acceleration
            
        Returns:
            JSON string with OCR results and metadata
        """
        if pdf2image is None:
            return self._error_response("pdf2image is not installed. Please install it with: pip install pdf2image")
        
        try:
            # Validate file path
            pdf_path = self.file_handler.validate_pdf_path(file_path)
            
            # Check cache
            cache_key_params = {
                'pages': pages,
                'language': language,
                'chunk_size': chunk_size,
                'use_gpu': use_gpu
            }
            cached_result = self.cache.get(pdf_path, 'ocr_extract', **cache_key_params)
            if cached_result:
                return cached_result
            
            # Perform OCR
            result = await self._perform_ocr_extraction(pdf_path, pages, language, chunk_size, use_gpu)
            
            # Cache the result
            self.cache.set(pdf_path, 'ocr_extract', result, **cache_key_params)
            
            return result
            
        except Exception as e:
            return self._error_response(f"Error performing OCR: {str(e)}")
    
    async def _perform_ocr_extraction(
        self,
        pdf_path: Path,
        pages_str: Optional[str],
        language: str,
        chunk_size: int,
        use_gpu: bool
    ) -> str:
        """Perform OCR extraction from PDF pages."""
        
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(pdf_path, dpi=200, fmt='RGB')
            total_pages = len(images)
            
            # Parse page range
            page_numbers = self.file_handler.parse_page_range(pages_str, total_pages)
            
            if not page_numbers:
                return self._error_response("No valid pages specified")
            
            # Parse language string to list
            languages = [lang.strip() for lang in language.split(',')]
            
            # Get OCR reader
            ocr_reader = self._get_ocr_reader(languages, use_gpu)
            
            # Process each page
            pages_content = []
            
            for page_num in page_numbers:
                if page_num >= total_pages:
                    continue
                
                # Get page image
                page_image = images[page_num]
                
                # Convert PIL Image to numpy array for EasyOCR
                image_array = np.array(page_image)
                
                # Perform OCR
                ocr_results = ocr_reader.readtext(image_array)
                
                # Extract text and confidence scores
                page_text, confidence_info = self._process_ocr_results(ocr_results)
                
                page_data = {
                    'text': page_text,
                    'page_number': page_num + 1,  # Convert to 1-indexed
                    'metadata': {
                        'ocr_language': language,
                        'average_confidence': confidence_info['avg_confidence'],
                        'text_blocks': confidence_info['block_count'],
                        'char_count': len(page_text),
                        'word_count': len(page_text.split())
                    }
                }
                
                pages_content.append(page_data)
            
            # Chunk the extracted text
            chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=100)
            chunks = chunker.chunk_pages(pages_content)
            
            # Prepare result
            result = {
                'success': True,
                'file_path': str(pdf_path),
                'total_pages': total_pages,
                'processed_pages': [p + 1 for p in page_numbers],  # Convert to 1-indexed
                'ocr_language': language,
                'chunks': [
                    {
                        'content': chunk.content,
                        'page_number': chunk.page_number,
                        'chunk_index': chunk.chunk_index,
                        'metadata': chunk.metadata
                    }
                    for chunk in chunks
                ],
                'summary': chunker.get_chunks_summary(chunks),
                'extraction_method': 'easyocr'
            }
            
            # Add OCR-specific summary
            avg_confidence = sum(
                page['metadata']['average_confidence'] 
                for page in pages_content
            ) / len(pages_content) if pages_content else 0
            
            result['ocr_summary'] = {
                'average_confidence': round(avg_confidence, 3),
                'total_text_blocks': sum(
                    page['metadata']['text_blocks'] 
                    for page in pages_content
                )
            }
            
            return self._format_result(result)
            
        except Exception as e:
            return self._error_response(f"OCR processing failed: {str(e)}")
    
    def _process_ocr_results(self, ocr_results: List) -> tuple[str, Dict[str, Any]]:
        """
        Process raw OCR results from EasyOCR.
        
        Args:
            ocr_results: Raw OCR results from EasyOCR
            
        Returns:
            Tuple of (extracted_text, confidence_info)
        """
        if not ocr_results:
            return "", {"avg_confidence": 0.0, "block_count": 0}
        
        text_blocks = []
        confidence_scores = []
        
        # EasyOCR returns results as: [bbox, text, confidence]
        for result in ocr_results:
            if len(result) >= 3:
                bbox = result[0]  # Bounding box coordinates
                text = result[1]  # Recognized text
                confidence = result[2]  # Confidence score
                
                if text.strip():  # Only add non-empty text
                    text_blocks.append(text.strip())
                    confidence_scores.append(confidence)
        
        # Join text blocks with appropriate spacing
        extracted_text = " ".join(text_blocks)
        
        # Calculate confidence metrics
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        confidence_info = {
            "avg_confidence": round(avg_confidence, 3),
            "block_count": len(text_blocks)
        }
        
        return extracted_text, confidence_info
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format result as JSON string."""
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def _error_response(self, message: str) -> str:
        """Format error response."""
        return json.dumps({
            'success': False,
            'error': message,
            'extraction_method': 'easyocr'
        }, ensure_ascii=False, indent=2)
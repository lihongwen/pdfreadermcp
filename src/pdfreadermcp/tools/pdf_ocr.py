"""
PDF OCR tool using PaddleOCR for scanned document recognition.
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
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

from PIL import Image
import numpy as np

from ..utils.file_handler import FileHandler
from ..utils.chunker import TextChunker
from ..utils.cache import PDFCache


class PDFOCR:
    """
    PDF OCR tool using PaddleOCR for processing scanned documents and images.
    """
    
    def __init__(self):
        """Initialize the PDF OCR tool with cache and OCR engine."""
        self.cache = PDFCache(max_entries=30, max_age_seconds=3600)  # 1 hour cache
        self.file_handler = FileHandler()
        self._ocr_engine = None
    
    def _get_ocr_engine(self, language: str = "ch_sim,en") -> Any:
        """
        Get or create PaddleOCR engine instance.
        
        Args:
            language: Language codes for OCR
            
        Returns:
            PaddleOCR instance
        """
        if PaddleOCR is None:
            raise ImportError("PaddleOCR is not installed. Please install it with: pip install paddleocr paddlepaddle")
        
        # Create new engine if needed or language changed
        if self._ocr_engine is None or getattr(self._ocr_engine, '_language', '') != language:
            try:
                # Initialize PaddleOCR with specified language
                self._ocr_engine = PaddleOCR(
                    use_angle_cls=True,  # Enable text angle classification
                    lang=language,       # Language setting
                    show_log=False       # Suppress verbose logging
                )
                self._ocr_engine._language = language  # Store language for comparison
            except Exception as e:
                raise RuntimeError(f"Failed to initialize PaddleOCR: {str(e)}")
        
        return self._ocr_engine
    
    async def extract_text_ocr(
        self,
        file_path: Union[str, Path],
        pages: Optional[str] = None,
        language: str = "ch_sim,en",
        chunk_size: int = 1000
    ) -> str:
        """
        Extract text from PDF using OCR with PaddleOCR.
        
        Args:
            file_path: Path to PDF file
            pages: Page range string (e.g., "1,3,5-10,-1")
            language: OCR language codes (e.g., "ch_sim,en")
            chunk_size: Maximum size of text chunks
            
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
                'chunk_size': chunk_size
            }
            cached_result = self.cache.get(pdf_path, 'ocr_extract', **cache_key_params)
            if cached_result:
                return cached_result
            
            # Perform OCR
            result = await self._perform_ocr_extraction(pdf_path, pages, language, chunk_size)
            
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
        chunk_size: int
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
            
            # Get OCR engine
            ocr_engine = self._get_ocr_engine(language)
            
            # Process each page
            pages_content = []
            
            for page_num in page_numbers:
                if page_num >= total_pages:
                    continue
                
                # Get page image
                page_image = images[page_num]
                
                # Convert PIL Image to numpy array for PaddleOCR
                image_array = np.array(page_image)
                
                # Perform OCR
                ocr_results = ocr_engine.ocr(image_array, cls=True)
                
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
                'extraction_method': 'paddleocr'
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
        Process raw OCR results from PaddleOCR.
        
        Args:
            ocr_results: Raw OCR results from PaddleOCR
            
        Returns:
            Tuple of (extracted_text, confidence_info)
        """
        if not ocr_results or not ocr_results[0]:
            return "", {"avg_confidence": 0.0, "block_count": 0}
        
        text_blocks = []
        confidence_scores = []
        
        for result in ocr_results[0]:  # PaddleOCR returns nested results
            if len(result) >= 2:
                text = result[1][0] if len(result[1]) >= 1 else ""
                confidence = result[1][1] if len(result[1]) >= 2 else 0.0
                
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
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # You can add more preprocessing steps here:
        # - Noise reduction
        # - Contrast enhancement
        # - Deskewing
        # - Binarization
        
        return image
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format result as JSON string."""
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def _error_response(self, message: str) -> str:
        """Format error response."""
        return json.dumps({
            'success': False,
            'error': message,
            'extraction_method': 'paddleocr'
        }, ensure_ascii=False, indent=2)
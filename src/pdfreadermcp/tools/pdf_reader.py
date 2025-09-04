"""
PDF text extraction tool using pdfplumber with intelligent text quality detection.
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import re

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from ..utils.file_handler import FileHandler
from ..utils.chunker import TextChunker, TextChunk
from ..utils.cache import PDFCache


class PDFReader:
    """
    PDF text extraction tool with intelligent text quality detection
    and automatic OCR fallback recommendation.
    """
    
    def __init__(self):
        """Initialize the PDF reader with cache."""
        self.cache = PDFCache(max_entries=50, max_age_seconds=1800)  # 30 minutes
        self.file_handler = FileHandler()
    
    async def extract_text(
        self,
        file_path: Union[str, Path],
        pages: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 100
    ) -> str:
        """
        Extract text from PDF with intelligent chunking and caching.
        
        Args:
            file_path: Path to PDF file
            pages: Page range string (e.g., "1,3,5-10,-1")
            chunk_size: Maximum size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            JSON string with extracted text and metadata
        """
        if pdfplumber is None:
            return self._error_response("pdfplumber is not installed. Please install it with: pip install pdfplumber")
        
        try:
            # Validate file path
            pdf_path = self.file_handler.validate_pdf_path(file_path)
            
            # Check cache
            cache_key_params = {
                'pages': pages,
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap
            }
            cached_result = self.cache.get(pdf_path, 'extract_text', **cache_key_params)
            if cached_result:
                return cached_result
            
            # Extract text from PDF
            result = await self._extract_text_from_pdf(pdf_path, pages, chunk_size, chunk_overlap)
            
            # Cache the result
            self.cache.set(pdf_path, 'extract_text', result, **cache_key_params)
            
            return result
            
        except Exception as e:
            return self._error_response(f"Error processing PDF: {str(e)}")
    
    async def _extract_text_from_pdf(
        self,
        pdf_path: Path,
        pages_str: Optional[str],
        chunk_size: int,
        chunk_overlap: int
    ) -> str:
        """Extract text from PDF pages."""
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            page_numbers = self.file_handler.parse_page_range(pages_str, total_pages)
            
            if not page_numbers:
                return self._error_response("No valid pages specified")
            
            # Extract text from specified pages
            pages_content = []
            ocr_recommended_pages = []
            
            for page_num in page_numbers:
                if page_num >= total_pages:
                    continue
                    
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                
                # Analyze text quality
                quality_info = self._analyze_text_quality(text)
                
                page_data = {
                    'text': text,
                    'page_number': page_num + 1,  # Convert back to 1-indexed for display
                    'metadata': {
                        'quality_score': quality_info['quality_score'],
                        'word_count': quality_info['word_count'],
                        'char_count': len(text),
                        'has_extractable_text': quality_info['has_extractable_text']
                    }
                }
                
                pages_content.append(page_data)
                
                # Recommend OCR for low-quality text
                if not quality_info['has_extractable_text']:
                    ocr_recommended_pages.append(page_num + 1)
            
            # Chunk the text
            chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = chunker.chunk_pages(pages_content)
            
            # Prepare result
            result = {
                'success': True,
                'file_path': str(pdf_path),
                'total_pages': total_pages,
                'processed_pages': [p + 1 for p in page_numbers],  # Convert to 1-indexed
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
                'ocr_recommended_pages': ocr_recommended_pages,
                'extraction_method': 'text_extraction'
            }
            
            # Add OCR recommendation if needed
            if ocr_recommended_pages:
                result['recommendations'] = [
                    f"Pages {', '.join(map(str, ocr_recommended_pages))} contain poor quality or no extractable text.",
                    "Consider using the 'ocr_pdf' tool for better results on these pages."
                ]
            
            return self._format_result(result)
    
    def _analyze_text_quality(self, text: str) -> Dict[str, Any]:
        """
        Analyze the quality of extracted text to determine if OCR is needed.
        
        Args:
            text: Extracted text
            
        Returns:
            Dictionary with quality metrics
        """
        if not text.strip():
            return {
                'quality_score': 0.0,
                'word_count': 0,
                'has_extractable_text': False
            }
        
        # Basic metrics
        word_count = len(text.split())
        char_count = len(text)
        
        # Quality indicators
        # 1. Character to word ratio (should be reasonable for normal text)
        char_word_ratio = char_count / max(word_count, 1)
        
        # 2. Presence of normal sentence structures
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # 3. Ratio of letters to total characters
        letters = re.findall(r'[a-zA-Z]', text)
        letter_ratio = len(letters) / max(char_count, 1)
        
        # 4. Check for garbled text (too many special characters)
        special_chars = re.findall(r'[^\w\s\.,!?\'"()-]', text)
        special_char_ratio = len(special_chars) / max(char_count, 1)
        
        # Calculate quality score (0.0 to 1.0)
        quality_score = 0.0
        
        # Good character to word ratio (typically 4-6 for English text)
        if 3 <= char_word_ratio <= 8:
            quality_score += 0.3
        
        # Reasonable sentence length (5-20 words)
        if 3 <= avg_sentence_length <= 25:
            quality_score += 0.3
        
        # Good letter ratio (should be high for text)
        if letter_ratio >= 0.6:
            quality_score += 0.3
        
        # Low special character ratio
        if special_char_ratio <= 0.1:
            quality_score += 0.1
        
        # Minimum word count threshold
        has_extractable_text = word_count >= 5 and quality_score >= 0.4
        
        return {
            'quality_score': quality_score,
            'word_count': word_count,
            'char_word_ratio': char_word_ratio,
            'avg_sentence_length': avg_sentence_length,
            'letter_ratio': letter_ratio,
            'special_char_ratio': special_char_ratio,
            'has_extractable_text': has_extractable_text
        }
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format result as JSON string."""
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def _error_response(self, message: str) -> str:
        """Format error response."""
        import json
        return json.dumps({
            'success': False,
            'error': message,
            'extraction_method': 'text_extraction'
        }, ensure_ascii=False, indent=2)
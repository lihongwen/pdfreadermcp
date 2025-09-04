"""
Text chunking utilities for processing large PDF content.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    page_number: int
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TextChunker:
    """
    Advanced text chunker that implements recursive character text splitting
    with semantic awareness for PDF content.
    """
    
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def chunk_text(self, text: str, page_number: int = 0, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """
        Split text into chunks using recursive character text splitting.
        
        Args:
            text: Text to chunk
            page_number: Page number this text came from
            metadata: Additional metadata for chunks
            
        Returns:
            List of TextChunk objects
        """
        if not text.strip():
            return []
            
        # Clean the text
        cleaned_text = self._clean_text(text)
        
        # Perform recursive splitting
        chunks = self._split_text_recursive(cleaned_text, self.DEFAULT_SEPARATORS)
        
        # Create TextChunk objects
        text_chunks = []
        start_char = 0
        
        for i, chunk_content in enumerate(chunks):
            end_char = start_char + len(chunk_content)
            
            chunk = TextChunk(
                content=chunk_content.strip(),
                page_number=page_number,
                chunk_index=i,
                start_char=start_char,
                end_char=end_char,
                metadata=metadata.copy() if metadata else {}
            )
            
            text_chunks.append(chunk)
            start_char = end_char - self.chunk_overlap
        
        return text_chunks
    
    def chunk_pages(self, pages_content: List[Dict[str, Any]]) -> List[TextChunk]:
        """
        Chunk content from multiple pages.
        
        Args:
            pages_content: List of dictionaries with 'text', 'page_number', and optional metadata
            
        Returns:
            List of TextChunk objects from all pages
        """
        all_chunks = []
        
        for page_data in pages_content:
            text = page_data.get('text', '')
            page_num = page_data.get('page_number', 0)
            metadata = page_data.get('metadata', {})
            
            page_chunks = self.chunk_text(text, page_num, metadata)
            all_chunks.extend(page_chunks)
        
        return all_chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers patterns (simple heuristics)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)  # Page numbers on separate lines
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively split text using different separators.
        
        Args:
            text: Text to split
            separators: List of separators to try in order
            
        Returns:
            List of text chunks
        """
        final_chunks = []
        
        # Use the first separator that exists in the text
        separator = ""
        for sep in separators:
            if sep in text:
                separator = sep
                break
        
        # Split by the chosen separator
        if separator:
            splits = text.split(separator)
        else:
            splits = [text]
        
        # Process each split
        current_chunk = ""
        for split in splits:
            # If adding this split would exceed chunk size
            if len(current_chunk) + len(split) + len(separator) > self.chunk_size:
                if current_chunk:
                    final_chunks.append(current_chunk)
                    current_chunk = ""
                
                # If single split is too large, recursively split it further
                if len(split) > self.chunk_size and len(separators) > 1:
                    sub_chunks = self._split_text_recursive(split, separators[1:])
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(split)
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += separator
                current_chunk += split
        
        # Don't forget the last chunk
        if current_chunk:
            final_chunks.append(current_chunk)
        
        return final_chunks
    
    def merge_chunks(self, chunks: List[TextChunk]) -> str:
        """
        Merge chunks back into a single text with metadata preserved.
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            Merged text
        """
        return "\n\n".join(chunk.content for chunk in chunks)
    
    def get_chunks_summary(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        Get summary information about chunks.
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            Summary dictionary
        """
        if not chunks:
            return {"total_chunks": 0, "total_chars": 0, "pages": []}
        
        total_chars = sum(len(chunk.content) for chunk in chunks)
        pages = list(set(chunk.page_number for chunk in chunks))
        
        return {
            "total_chunks": len(chunks),
            "total_chars": total_chars,
            "pages": sorted(pages),
            "avg_chunk_size": total_chars // len(chunks) if chunks else 0,
            "chunk_size_config": self.chunk_size,
            "overlap_config": self.chunk_overlap
        }
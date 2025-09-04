"""
File handling utilities for PDF processing.
"""

import re
from pathlib import Path
from typing import List, Optional, Union


class FileHandler:
    """Utility class for file operations and page range parsing."""
    
    @staticmethod
    def validate_pdf_path(file_path: Union[str, Path]) -> Path:
        """
        Validate and convert PDF file path.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Validated Path object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a PDF
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        if not path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {file_path}")
            
        return path
    
    @staticmethod
    def parse_page_range(pages_str: Optional[str], total_pages: int) -> List[int]:
        """
        Parse page range string into list of page numbers.
        
        Args:
            pages_str: Page range string (e.g., "1,3,5-10,-1")
            total_pages: Total number of pages in document
            
        Returns:
            List of 0-indexed page numbers
            
        Examples:
            "1,3,5-10,-1" -> [0, 2, 4, 5, 6, 7, 8, 9, total_pages-1]
            "1-3" -> [0, 1, 2]
            "-1" -> [total_pages-1]
            None -> [0, 1, 2, ..., total_pages-1] (all pages)
        """
        if not pages_str:
            return list(range(total_pages))
        
        page_numbers = []
        ranges = pages_str.split(',')
        
        for range_str in ranges:
            range_str = range_str.strip()
            
            # Handle negative indices (e.g., "-1" for last page)
            if range_str.startswith('-') and range_str[1:].isdigit():
                negative_index = int(range_str)
                if negative_index >= -total_pages:
                    page_numbers.append(total_pages + negative_index)
                continue
            
            # Handle ranges (e.g., "5-10")
            if '-' in range_str and not range_str.startswith('-'):
                try:
                    start, end = range_str.split('-', 1)
                    start_page = int(start) - 1  # Convert to 0-indexed
                    end_page = int(end) - 1      # Convert to 0-indexed
                    
                    # Validate range
                    start_page = max(0, min(start_page, total_pages - 1))
                    end_page = max(0, min(end_page, total_pages - 1))
                    
                    if start_page <= end_page:
                        page_numbers.extend(range(start_page, end_page + 1))
                except ValueError:
                    continue
            
            # Handle single page numbers
            elif range_str.isdigit():
                page_num = int(range_str) - 1  # Convert to 0-indexed
                if 0 <= page_num < total_pages:
                    page_numbers.append(page_num)
        
        # Remove duplicates and sort
        return sorted(list(set(page_numbers)))
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> dict:
        """
        Get basic file information.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file info
        """
        path = Path(file_path)
        
        return {
            "name": path.name,
            "size": path.stat().st_size if path.exists() else 0,
            "modified": path.stat().st_mtime if path.exists() else 0,
            "exists": path.exists()
        }
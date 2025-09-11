"""
PDF operations tool for splitting, extracting, and merging PDF documents.
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import json
from datetime import datetime

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    PdfReader = None
    PdfWriter = None

from ..utils.file_handler import FileHandler
from ..utils.cache import PDFCache


class PDFOperations:
    """
    PDF operations tool for splitting, extracting pages, and merging PDFs.
    """
    
    def __init__(self):
        """Initialize the PDF operations tool."""
        self.file_handler = FileHandler()
        self.cache = PDFCache(max_entries=20, max_age_seconds=1800)  # 30 minutes
    
    async def split_pdf(
        self,
        file_path: Union[str, Path],
        split_ranges: List[str],
        output_dir: Optional[str] = None,
        prefix: Optional[str] = None
    ) -> str:
        """
        Split PDF into multiple files based on page ranges.
        
        Args:
            file_path: Path to source PDF file
            split_ranges: List of page ranges (e.g., ["1-5", "6-10", "11-15"])
            output_dir: Output directory (defaults to source file directory)
            prefix: Output file prefix (defaults to source filename)
            
        Returns:
            JSON string with operation results
        """
        if PdfReader is None or PdfWriter is None:
            return self._error_response("pypdf is not installed. Please install it with: pip install pypdf")
        
        try:
            # Validate source file
            pdf_path = self.file_handler.validate_pdf_path(file_path)
            
            # Set defaults
            if output_dir is None:
                output_dir = pdf_path.parent
            else:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            
            if prefix is None:
                prefix = pdf_path.stem
            
            # Read source PDF
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            # Process each split range
            output_files = []
            for i, range_str in enumerate(split_ranges, 1):
                # Parse page range
                page_numbers = self.file_handler.parse_page_range(range_str, total_pages)
                
                if not page_numbers:
                    continue
                
                # Create output filename
                output_filename = f"{prefix}_split_{i:02d}.pdf"
                output_path = output_dir / output_filename
                
                # Create new PDF with specified pages
                writer = PdfWriter()
                for page_num in page_numbers:
                    if 0 <= page_num < total_pages:
                        writer.add_page(reader.pages[page_num])
                
                # Write to file
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                output_files.append({
                    'filename': output_filename,
                    'path': str(output_path),
                    'pages': [p + 1 for p in page_numbers],  # Convert to 1-indexed
                    'page_count': len(page_numbers),
                    'size': output_path.stat().st_size
                })
            
            result = {
                'success': True,
                'operation': 'split_pdf',
                'source_file': str(pdf_path),
                'total_source_pages': total_pages,
                'output_directory': str(output_dir),
                'output_files': output_files,
                'split_count': len(output_files)
            }
            
            return self._format_result(result)
            
        except Exception as e:
            return self._error_response(f"PDF split failed: {str(e)}")
    
    async def extract_pages(
        self,
        file_path: Union[str, Path],
        pages: str,
        output_file: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Extract specific pages from PDF to a new file.
        
        Args:
            file_path: Path to source PDF file
            pages: Page range (e.g., "1,3,5-7")
            output_file: Output filename (optional, auto-generated if not provided)
            output_dir: Output directory (defaults to source file directory)
            
        Returns:
            JSON string with operation results
        """
        if PdfReader is None or PdfWriter is None:
            return self._error_response("pypdf is not installed. Please install it with: pip install pypdf")
        
        try:
            # Validate source file
            pdf_path = self.file_handler.validate_pdf_path(file_path)
            
            # Set output directory
            if output_dir is None:
                output_dir = pdf_path.parent
            else:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Read source PDF
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            # Parse page range
            page_numbers = self.file_handler.parse_page_range(pages, total_pages)
            
            if not page_numbers:
                return self._error_response("No valid pages specified")
            
            # Generate output filename if not provided
            if output_file is None:
                pages_desc = pages.replace(',', '_').replace('-', 'to')
                output_file = f"{pdf_path.stem}_pages_{pages_desc}.pdf"
            
            output_path = output_dir / output_file
            
            # Create new PDF with specified pages
            writer = PdfWriter()
            for page_num in page_numbers:
                if 0 <= page_num < total_pages:
                    writer.add_page(reader.pages[page_num])
            
            # Write to file
            with open(output_path, 'wb') as file:
                writer.write(file)
            
            result = {
                'success': True,
                'operation': 'extract_pages',
                'source_file': str(pdf_path),
                'total_source_pages': total_pages,
                'extracted_pages': [p + 1 for p in page_numbers],  # Convert to 1-indexed
                'extracted_page_count': len(page_numbers),
                'output_file': str(output_path),
                'output_size': output_path.stat().st_size
            }
            
            return self._format_result(result)
            
        except Exception as e:
            return self._error_response(f"Page extraction failed: {str(e)}")
    
    async def merge_pdfs(
        self,
        file_paths: List[str],
        output_file: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Merge multiple PDF files into a single file.
        
        Args:
            file_paths: List of PDF file paths to merge
            output_file: Output filename (optional, auto-generated if not provided)
            output_dir: Output directory (defaults to first file's directory)
            
        Returns:
            JSON string with operation results
        """
        if PdfReader is None or PdfWriter is None:
            return self._error_response("pypdf is not installed. Please install it with: pip install pypdf")
        
        if not file_paths:
            return self._error_response("No files provided for merging")
        
        try:
            # Validate all input files
            validated_paths = []
            for file_path in file_paths:
                pdf_path = self.file_handler.validate_pdf_path(file_path)
                validated_paths.append(pdf_path)
            
            # Set output directory
            if output_dir is None:
                output_dir = validated_paths[0].parent
            else:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename if not provided
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"merged_{timestamp}.pdf"
            
            output_path = output_dir / output_file
            
            # Merge PDFs
            writer = PdfWriter()
            source_info = []
            total_pages = 0
            
            for pdf_path in validated_paths:
                reader = PdfReader(pdf_path)
                page_count = len(reader.pages)
                
                # Add all pages from this PDF
                for page in reader.pages:
                    writer.add_page(page)
                
                source_info.append({
                    'filename': pdf_path.name,
                    'path': str(pdf_path),
                    'page_count': page_count,
                    'size': pdf_path.stat().st_size
                })
                
                total_pages += page_count
            
            # Write merged PDF
            with open(output_path, 'wb') as file:
                writer.write(file)
            
            result = {
                'success': True,
                'operation': 'merge_pdfs',
                'source_files': source_info,
                'total_source_files': len(validated_paths),
                'total_pages': total_pages,
                'output_file': str(output_path),
                'output_size': output_path.stat().st_size
            }
            
            return self._format_result(result)
            
        except Exception as e:
            return self._error_response(f"PDF merge failed: {str(e)}")
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format result as JSON string."""
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def _error_response(self, message: str) -> str:
        """Format error response."""
        return json.dumps({
            'success': False,
            'error': message
        }, ensure_ascii=False, indent=2)
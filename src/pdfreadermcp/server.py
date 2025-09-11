"""
MCP Server for PDF reading with text extraction.
"""

from typing import Any, List
from mcp.server.fastmcp import FastMCP
from .tools.pdf_reader import PDFReader
from .tools.pdf_operations import PDFOperations

# Create FastMCP app
app = FastMCP("PDF Reader MCP Server")

# Initialize PDF processing tools
pdf_reader = PDFReader()
pdf_operations = PDFOperations()


@app.tool()
async def read_pdf(
    file_path: str,
    pages: str = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 100
) -> str:
    """Extract text from PDF files with intelligent page handling and chunking.
    
    Args:
        file_path: Path to the PDF file
        pages: Page range (e.g., '1,3,5-10,-1' for pages 1, 3, 5 to 10, and last page)
        chunk_size: Maximum size of text chunks
        chunk_overlap: Overlap between chunks to preserve context
        
    Returns:
        JSON string with extracted text and metadata
    """
    try:
        result = await pdf_reader.extract_text(
            file_path=file_path,
            pages=pages,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return result
    except Exception as e:
        import json
        return json.dumps({
            'success': False,
            'error': f'PDF text extraction failed: {str(e)}',
            'extraction_method': 'text_extraction'
        }, ensure_ascii=False, indent=2)


@app.tool()
async def split_pdf(
    file_path: str,
    split_ranges: List[str],
    output_dir: str = None,
    prefix: str = None
) -> str:
    """Split PDF into multiple files based on page ranges.
    
    Args:
        file_path: Path to the source PDF file
        split_ranges: List of page ranges (e.g., ["1-5", "6-10", "11-15"])
        output_dir: Output directory (defaults to source file directory)
        prefix: Output file prefix (defaults to source filename)
        
    Returns:
        JSON string with split operation results and output file information
    """
    try:
        result = await pdf_operations.split_pdf(
            file_path=file_path,
            split_ranges=split_ranges,
            output_dir=output_dir,
            prefix=prefix
        )
        return result
    except Exception as e:
        import json
        return json.dumps({
            'success': False,
            'error': f'PDF split failed: {str(e)}',
            'operation': 'split_pdf'
        }, ensure_ascii=False, indent=2)


@app.tool()
async def extract_pages(
    file_path: str,
    pages: str,
    output_file: str = None,
    output_dir: str = None
) -> str:
    """Extract specific pages from PDF to a new file.
    
    Args:
        file_path: Path to the source PDF file
        pages: Page range (e.g., "1,3,5-7" for pages 1, 3, and 5 to 7)
        output_file: Output filename (optional, auto-generated if not provided)
        output_dir: Output directory (defaults to source file directory)
        
    Returns:
        JSON string with extraction results and output file information
    """
    try:
        result = await pdf_operations.extract_pages(
            file_path=file_path,
            pages=pages,
            output_file=output_file,
            output_dir=output_dir
        )
        return result
    except Exception as e:
        import json
        return json.dumps({
            'success': False,
            'error': f'Page extraction failed: {str(e)}',
            'operation': 'extract_pages'
        }, ensure_ascii=False, indent=2)


@app.tool()
async def merge_pdfs(
    file_paths: List[str],
    output_file: str = None,
    output_dir: str = None
) -> str:
    """Merge multiple PDF files into a single file.
    
    Args:
        file_paths: List of PDF file paths to merge
        output_file: Output filename (optional, auto-generated if not provided)
        output_dir: Output directory (defaults to first file's directory)
        
    Returns:
        JSON string with merge results and output file information
    """
    try:
        result = await pdf_operations.merge_pdfs(
            file_paths=file_paths,
            output_file=output_file,
            output_dir=output_dir
        )
        return result
    except Exception as e:
        import json
        return json.dumps({
            'success': False,
            'error': f'PDF merge failed: {str(e)}',
            'operation': 'merge_pdfs'
        }, ensure_ascii=False, indent=2)


